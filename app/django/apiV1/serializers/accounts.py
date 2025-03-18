from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import serializers

from accounts.models import User, StaffAuth, Profile, Todo, DocScrape, PasswordResetToken, PostScrape
from board.models import Post
from docs.models import Document
from work.models import IssueProject


# Accounts --------------------------------------------------------------------------
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('pk', 'username')


class StaffAuthInUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAuth
        fields = ('pk', 'user', 'company', 'is_staff', 'is_project_staff',
                  'allowed_projects', 'assigned_project', 'contract', 'payment', 'notice',
                  'project_cash', 'project_docs', 'project', 'project_site', 'company_cash',
                  'company_docs', 'human_resource', 'company_settings', 'auth_manage')

    @transaction.atomic
    def create(self, validated_data):
        # 1. 권한정보 테이블 입력
        many_to_many = {'allowed_projects': validated_data.pop('allowed_projects')}
        instance = StaffAuth.objects.create(**validated_data)

        # Save many-to-many relationships after the instance is created.
        for field_name, value in many_to_many.items():
            field = getattr(instance, field_name)
            field.set(value)

        # 2. 프로필 정보가 있는지 확인 후 없으면 기본 프로필 생성
        try:
            Profile.objects.get(user=validated_data['user'])
        except Profile.DoesNotExist:
            empty_profile = Profile(user=instance.user)
            empty_profile.save()

        try:
            # 3. 멤버 승인 및 권한 부여 확인 메일 보내기
            subject = f'[IBS] {instance.user.username}님 회원가입이 관리자에게 승인 되었습니다.'
            message = (f'이 메일은 [IBS]회원가입에 대해 관리자에게 승인 후 발송되는 메일입니다. \n\n'
                       f'가입 시 등록한 이메일 계정으로 로그인 후 이용하시기 바랍니다.')
            send_mail(subject, message, settings.EMAIL_DEFAULT_SENDER, [instance.user.email])
        except ConnectionRefusedError:
            pass

        return instance


class ProfileInUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('pk', 'name', 'birth_date', 'cell_phone')


class IssueProjectInUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueProject
        fields = ('pk', 'slug', 'name')


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text='변경할 필요가 없으면 비워 두십시오.',
        style={'input_type': 'password', 'placeholder': '비밀번호'}
    )
    staffauth = StaffAuthInUserSerializer(read_only=True)
    profile = ProfileInUserSerializer(read_only=True)
    assigned_projects = IssueProjectInUserSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('pk', 'email', 'username', 'is_active', 'is_superuser',
                  'is_staff', 'work_manager', 'date_joined', 'password',
                  'staffauth', 'profile', 'assigned_projects', 'last_login')
        read_only_fields = ('date_joined', 'last_login')

    def create(self, validated_data):
        user = User(email=validated_data['email'],
                    username=validated_data['username'])
        password = validated_data['password']
        user.set_password(password)

        try:
            # 회원가입 환영 메일 보내기
            subject = f'[IBS] {user.username}님 회원가입을 환영합니다.'
            message = (f'이 메일은 [IBS]회원가입에 따라 발송되는 메일입니다. \n\n'
                       f'이 사이트는 업무용 시스템으로 회원가입 후 사이트 이용을 위해서는 관리자의 승인이 필요합니다. \n'
                       f'관리자의 승인을 기다리거나 관리자({settings.EMAIL_DEFAULT_SENDER})에게 승인을 요청할 수 있습니다.')
            send_mail(subject, message, settings.EMAIL_DEFAULT_SENDER, [user.email])

            # 관리자에게 회원가입 메일 보내기
            subject = f'[IBS] 신규회원 가입 1건 ({user.username}님)이 있습니다.'
            message = (f'[IBS] 시스템 - {user.username}님이 신규 회원가입을 하였습니다.\n\n'
                       f'사용자 이  름 : {user.username}\n'
                       f'사용자 이메일 : {user.email}\n')
            send_mail(subject, message, settings.EMAIL_DEFAULT_SENDER, [settings.EMAIL_DEFAULT_SENDER])
        except ConnectionRefusedError:
            pass

        user.save()
        return user

    def update(self, instance, validated_data):
        instance.__dict__.update(validated_data)
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class ProfileSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, allow_empty_file=False, required=False)

    class Meta:
        model = Profile
        fields = ('pk', 'user', 'name', 'birth_date', 'cell_phone', 'image',
                  'like_posts', 'like_comments', 'blame_posts', 'blame_comments')

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        instance.save()

        user = instance.user
        email = user.email
        new_email = self.initial_data.get('email')
        if new_email and email != new_email:
            if User.objects.filter(email=new_email).exists():
                raise serializers.ValidationError({'email': '이미 등록된 이메일입니다.'})
            user.email = new_email
        is_active = self.initial_data.get('is_active')
        if is_active is not None:
            user.is_active = False
        user.save()

        return instance


class DocsInScrapeSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField(read_only=True)
    proj_sort = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = ('pk', 'doc_type', 'type_name', 'issue_project', 'proj_sort', 'title')

    @staticmethod
    def get_type_name(obj):
        return obj.doc_type.get_type_display()

    @staticmethod
    def get_proj_sort(obj):
        return obj.issue_project.sort if obj.issue_project else None


class DocScrapeSerializer(serializers.ModelSerializer):
    docs = DocsInScrapeSerializer(read_only=True)

    class Meta:
        model = DocScrape
        fields = ('pk', 'user', 'docs', 'title', 'created')

    def create(self, validated_data):
        docs = self.initial_data.get('docs')
        user = validated_data.get('user')
        scrape = DocScrape(docs_id=docs, user=user)
        scrape.save()
        return scrape


class PostInScrapeSerializer(serializers.ModelSerializer):
    board_name = serializers.SlugField(source='board', read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'board', 'board_name', 'title')


class PostScrapeSerializer(serializers.ModelSerializer):
    post = PostInScrapeSerializer(read_only=True)

    class Meta:
        model = PostScrape
        fields = ('pk', 'user', 'post', 'title', 'created')

    def create(self, validated_data):
        post = self.initial_data.get('post')
        user = validated_data.get('user')
        scrape = PostScrape(post_id=post, user=user)
        scrape.save()
        return scrape


class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('pk', 'user', 'title', 'completed', 'soft_deleted')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, write_only=True, required=True)
    new_password = serializers.CharField(max_length=128, write_only=True, required=True)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordResetToken
        fields = ('pk', 'user', 'token', 'updated', 'is_expired')


class AdminCreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    mail_sending = serializers.BooleanField()
    send_option = serializers.CharField()
    expired = serializers.IntegerField()
