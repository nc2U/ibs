from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import serializers

from accounts.models import User, Profile, Todo, DocScrape, PasswordResetToken, PostScrape
from forum.models import Post
from docs.models import Document
from work.models.project import IssueProject


# Accounts --------------------------------------------------------------------------
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('pk', 'username')



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
        required=False,
        allow_blank=True,
        help_text='변경할 필요가 없으면 비워 두십시오.',
        style={'input_type': 'password', 'placeholder': '비밀번호'}
    )
    profile = ProfileInUserSerializer(read_only=True)
    is_hq_financial_officer = serializers.SerializerMethodField(read_only=True)
    is_hq_staff = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('pk', 'email', 'username', 'is_active', 'is_superuser',
                  'is_staff', 'work_manager', 'date_joined', 'password',
                  'profile', 'last_login', 'is_hq_financial_officer', 'is_hq_staff')
        read_only_fields = ('date_joined', 'last_login')

    def get_is_hq_financial_officer(self, obj):
        try:
            return getattr(obj.staff, 'is_hq_financial_officer', False)
        except AttributeError:
            return False

    def get_is_hq_staff(self, obj):
        if obj.is_superuser:
            return True
        return obj.member_set.filter(project__type='1').exists()

    def create(self, validated_data):
        user = User(email=validated_data['email'],
                    username=validated_data['username'])
        password = validated_data['password']
        user.set_password(password)

        try:
            # 회원가입 환영 메일 보내기
            subject = f'[IBS] 워크스페이스 {user.username}님, 회원가입을 환영합니다.'
            message = (
                f'안녕하세요, {user.username}님.\n\n'
                'IBS 워크스페이스 회원가입을 환영합니다.\n\n'
                '회원가입은 정상적으로 완료되었으며, '
                '업무용 시스템 이용을 위해서는 관리자의 승인이 필요합니다.\n'
                '관리자의 승인 후 서비스를 이용하실 수 있습니다.\n\n'
                f'승인이 지연되는 경우 관리자({settings.DEFAULT_FROM_EMAIL})에게 문의해 주시기 바랍니다.'
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            # 관리자에게 회원가입 메일 보내기
            subject = f'[IBS] 워크스페이스 신규 회원가입 알림 ({user.username})'
            message = (
                'IBS 워크스페이스에 신규 회원가입이 접수되었습니다.\n\n'
                f'사용자명 : {user.username}\n'
                f'이메일 : {user.email}\n\n'
                f'승인 페이지: {settings.DOMAIN_HOST}/#/settings/authorization\n'
                '관리자 페이지에서 가입 승인 여부를 확인해 주세요.'
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
        except Exception as e:
            print(f"메일 발송 실패 {e}")

        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():  # 나머지 필드 업데이트
            setattr(instance, attr, value)

        if password:  # 비밀번호가 제공된 경우에만 암호화해서 저장
            instance.set_password(password)
        instance.save()
        return instance


class ProfileSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, allow_empty_file=False, required=False)

    class Meta:
        model = Profile
        fields = ('pk', 'user', 'name', 'birth_date', 'cell_phone', 'image',
                  'auto_watch_created', 'auto_watch_assigned',
                  'meeting_created_notification', 'meeting_confirmed_notification',
                  'like_posts', 'like_comments', 'blame_posts', 'blame_comments')

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        user = instance.user
        new_email = self.initial_data.get('email')
        if new_email and user.email != new_email:
            if User.objects.filter(email=new_email).exists():
                raise serializers.ValidationError({'email': '이미 등록된 이메일입니다.'})
            user.email = new_email

        is_active = self.initial_data.get('is_active')
        if is_active is not None:
            user.is_active = bool(is_active)
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
        return obj.issue_project.type if obj.issue_project else None


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
    forum_name = serializers.SlugField(source='forum', read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'forum', 'forum_name', 'title')


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
