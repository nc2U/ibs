import base64

from allauth.account.forms import default_token_generator
from django.conf import settings
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from accounts.models import User, StaffAuth, Profile, DocScrape, PostScrape, Todo, PasswordResetToken
from apiV1.permissions.auth_perms import IsStaffOrReadOnly, IsOwnerOnly, IsWorkManagerOnly
from ..pagination import PageNumberPaginationThreeThousand, PageNumberPaginationFifty
from ..serializers.accounts import UserSerializer, StaffAuthInUserSerializer, ProfileSerializer, \
    DocScrapeSerializer, PostScrapeSerializer, TodoSerializer, ChangePasswordSerializer, \
    PasswordResetSerializer, PasswordResetTokenSerializer, AdminCreateUserSerializer


# Accounts --------------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPaginationThreeThousand
    permission_classes = (AllowAny,)
    filterset_fields = ('is_staff', 'is_active',)

    def get_queryset(self):
        from django.db.models import Q
        queryset = User.objects.all()
        user = self.request.user

        # 로그인하지 않은 경우 목록 노출 방지
        if not user or not user.is_authenticated:
            return queryset.none()

        # 슈퍼유저나 work_manager는 전체 사용자 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        try:
            if hasattr(user, 'staff_auth') and user.staff_auth.is_hq_staff:
                return queryset
        except AttributeError:
            pass

        # 1. 사용자의 프로젝트별 user_visible 권한 수준 판별
        from work.models.project import Member
        user_members = Member.objects.filter(user=user).prefetch_related('roles')

        user_visibility_order = {'ALL': 2, 'PRJ': 1, 'NOP': 0}
        best_user_visible = 'NOP'

        for member in user_members:
            for role in member.roles.all():
                if user_visibility_order.get(role.user_visible, 0) > user_visibility_order.get(best_user_visible, 0):
                    best_user_visible = role.user_visible

        # 비회원 역할 pk=2 참고
        from work.models.project import Role
        try:
            non_member_role = Role.objects.get(pk=2)
            non_member_user_visible = non_member_role.user_visible
        except Role.DoesNotExist:
            non_member_user_visible = 'NOP'

        if not user_members.exists():
            best_user_visible = non_member_user_visible

        # 2. 수준별 필터링 적용
        if best_user_visible == 'ALL':
            return queryset
        elif best_user_visible == 'PRJ':
            member_project_ids = [m.project_id for m in user_members]
            project_user_ids = Member.objects.filter(
                project_id__in=member_project_ids
            ).values_list('user_id', flat=True)
            return queryset.filter(Q(pk__in=project_user_ids) | Q(pk=user.pk)).distinct()
        elif best_user_visible == 'NOP':
            return queryset.filter(pk=user.pk)

        return queryset.none()


class StaffAuthViewSet(viewsets.ModelViewSet):
    queryset = StaffAuth.objects.all()
    serializer_class = StaffAuthInUserSerializer
    permission_classes = (IsAuthenticated, IsStaffOrReadOnly)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated, IsOwnerOnly)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocScrapeViewSet(viewsets.ModelViewSet):
    queryset = DocScrape.objects.all()
    serializer_class = DocScrapeSerializer
    permission_classes = (IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user',)
    search_fields = ('title', 'post__title', 'post__content')


class PostScrapeViewSet(viewsets.ModelViewSet):
    queryset = PostScrape.objects.all()
    serializer_class = PostScrapeSerializer
    permission_classes = (IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user',)
    search_fields = ('title', 'post__title', 'post__content')


class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user', 'soft_deleted')
    search_fields = ('title',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CheckPasswordView(APIView):
    """비밀번호가 맞는지 체크하는 API"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        password = request.data.get('password', None)

        if not password:
            return Response({'detail': 'Password not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=request.data.get('email'), password=password)

        if user is not None:
            # Password is correct
            return Response({'detail': 'Password correct.'}, status=status.HTTP_200_OK)
        else:
            # Password is correct
            return Response({'detail': 'Password incorrect.'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """종전 비밀번호를 확인 한 후 비밀번호를 변경하는 API"""
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            # Check if the old password is correct
            old_password = serializer.validated_data.get('old_password')
            if not check_password(old_password, request.user.password):
                return Response({'detail': '패스워드를 맞지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # Update the password
            new_password = serializer.validated_data.get('new_password')
            request.user.set_password(new_password)
            request.user.save()

            # Update the user's session to prevent the user from being logged out
            update_session_auth_hash(request, request.user)

            return Response({'detail': '패스워드가 변경되었습니다.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """비밀번호 분실 시 재설정 링크를 요청하는 API"""
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Find the user with the given email
            email = serializer.validated_data.get('email')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'detail': '입력한 이메일로 등록된 사용자가 존재하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate a password reset token
            token = default_token_generator.make_token(user)
            try:
                token_db = PasswordResetToken.objects.get(user=user)
                token_db.token = token
            except PasswordResetToken.DoesNotExist:
                token_db = PasswordResetToken(user=user, token=token)
            token_db.save()

            # Create a password reset link
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            scheme = 'http' if settings.DEBUG else 'https'
            curr_host = request.get_host()

            reset_link = f'{scheme}://{curr_host}/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

            # Send the password reset email
            subject = f'[IBS] {user.username}님 계정 비밀번호 초기화 링크 안내드립니다.'
            message = f'비밀번호를 재설정 하기 위해서 다음 링크를 클릭 하세요: \n{reset_link}\n\n이 링크는 발송 후 10분 후에 만료됩니다.'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            return Response({'detail': '비밀번호 재설정을 위한 이메일을 발송했습니다.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """비밀번호 재설정 링크를 통해서 비밀번호를 재설정하는 API"""
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        while len(user_id) % 4 != 0:
            user_id += '='
        user_id = base64.b64decode(user_id, validate=True).decode('utf-8')
        token = kwargs.get('token')

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            token_db = PasswordResetToken.objects.get(user=user)
            if not token_db.is_expired():
                # Token is valid, perform password reset
                new_password = request.data.get('new_password')
                user.set_password(new_password)
                user.save()

                # # Log the user in with the new password
                # authenticated_user = authenticate (username=user.username, password=new_password)
                # login(request, authenticated_user)

                return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'This token was expired'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)


class PasswordResetTokenViewSet(viewsets.ModelViewSet):
    queryset = PasswordResetToken.objects.all()
    serializer_class = PasswordResetTokenSerializer
    permission_classes = (AllowAny,)
    filterset_fields = ('user', 'token')


class AdminManageUserView(APIView):
    """비밀번호 분실 시 재설정 링크를 요청하는 API"""
    permission_classes = (IsAuthenticated, IsWorkManagerOnly)

    @staticmethod
    def post(request, *args, **kwargs):
        serializer = AdminCreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 이미 존재하는 이메일 체크
        email = serializer.validated_data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'detail': '이미 등록된 이메일입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 트랜잭션을 사용하여 원자적 처리
        try:
            with transaction.atomic():
                # 1. 사용자 생성
                user = User(email=email, username=serializer.validated_data.get('username'))
                user.set_password(serializer.validated_data.get('password'))
                user.save()

                # 2. 기본 스태프 권한 및 프로필 등록
                StaffAuth.objects.create(user=user, is_pjt_staff=True)
                Profile.objects.create(user=user)

                # 3. 메일 발송 로직 (mail_sending이 True인 경우)

                # Find the user with the given email
                mail_sending = serializer.validated_data.get('mail_sending')

                if mail_sending is not None:
                    scheme = 'http' if settings.DEBUG else 'https'
                    curr_host = request.get_host()

                    send_option = serializer.validated_data.get('send_option')

                    if send_option == '1':
                        # Generate a password reset token
                        token = default_token_generator.make_token(user)
                        expired = serializer.validated_data.get('expired')
                        try:
                            token_db = PasswordResetToken.objects.get(user=user)
                            token_db.token = token
                        except PasswordResetToken.DoesNotExist:
                            token_db = PasswordResetToken(user=user, token=token, expired=expired * 3600)
                        token_db.save()

                        # Create a password reset link
                        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                        reset_link = f'{scheme}://{curr_host}/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

                        # Send the password reset email
                        subject = f'[IBS] 워크스페이스 {user.username}님 새 계정이 생성 되었습니다.'
                        message = f'''[IBS] 워크스페이스를 시작하기 위해 다음 링크를 클릭하여 비밀번호를 설정 하세요.: \n{reset_link}\n\n이 링크는 발송 후 {expired}시간 후에 만료됩니다. 만료되기 전에 패스워드를 설정하지 않은 경우 관리자에게 문의하십시오.'''
                    else:
                        # Send the password reset email
                        subject = f'[IBS] 워크스페이스 {user.username}님 새 계정이 생성 되었습니다.'
                        message = f'''[IBS] 워크스페이스를 시작하기 위해 다음 사용자 정보를 이용해 로그인 하세요.: \n\n메일주소 : {email}\n비밀번호 : {password}\n\nURL 주소 : {scheme}://{curr_host}\n\n로그인 및 각 메뉴에 대한 접근 권한은 관리자에게 문의하십시오.'''

                    try:
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                    except Exception as e:
                        print(f"관리자 유저 생성 메일 발송 실패: {e}")
                        return Response(
                            {'pk': user.pk, 'detail': '새 계정이 생성되었으나 알림 이메일 발송에는 실패했습니다. 비밀번호를 수동으로 전달하십시오.'},
                            status=status.HTTP_201_CREATED)

                    return Response({'pk': user.pk, 'detail': '새 계정을 생성하고 비밀번호 설정을 위한 이메일을 발송했습니다.'},
                                    status=status.HTTP_201_CREATED)

            return Response({'pk': user.pk, 'detail': '새 계정을 생성하였습니다.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': f'사용자 생성 중 오류 발생: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def put(request, *args, **kwargs):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': '사용자를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 1. 권한 관련 필드 업데이트 (명시적 존재 확인)
        # 요청 데이터에 해당 필드가 있을 때만 업데이트합니다.
        for field in ['is_active', 'is_staff', 'work_manager']:
            if field in request.data:
                setattr(user, field, request.data[field])

        # 2. 비밀번호 변경 (비밀번호 정보가 명시적으로 들어올 때만)
        password = request.data.get('password')
        mail_sending = request.data.get('mail_sending', False)
        send_option = request.data.get('send_option', '1')  # '1': 리셋 링크, '2': 새 비밀번호 정보

        # 비밀번호 직접 변경 로직 (send_option '2'일 때)
        if password and send_option == '2':
            user.set_password(password)

        # 3. 데이터 저장 및 메일 발송 (트랜잭션으로 원자적 처리)
        try:
            with transaction.atomic():
                user.save()

                # 메일 발송이 필요한 경우
                if mail_sending:
                    scheme = 'http' if settings.DEBUG else 'https'
                    curr_host = request.get_host()
                    email = user.email

                    expired = request.data.get('expired', 24)
                    if not str(expired).isdigit():
                        expired = 24
                    else:
                        expired = int(expired)

                    if send_option == '1':
                        # Generate a password reset token
                        token = default_token_generator.make_token(user)
                        try:
                            token_db = PasswordResetToken.objects.get(user=user)
                            token_db.token = token
                        except PasswordResetToken.DoesNotExist:
                            token_db = PasswordResetToken(user=user, token=token, expired=expired * 3600)
                        token_db.save()

                        # Create a password reset link
                        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                        reset_link = f'{scheme}://{curr_host}/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

                        # Send the password reset email
                        subject = f'[IBS] 워크스페이스 {user.username}님 계정 비밀번호 초기화 안내.'
                        message = f'''[IBS] 워크스페이스 계정의 비밀번호를 재설정하기 위해 다음 링크를 클릭하세요.: \n{reset_link}\n\n이 링크는 발송 후 {expired}시간 후에 만료됩니다. 만료되기 전에 패스워드를 재설정하지 않은 경우 관리자에게 문의하십시오.'''
                    else:
                        # Send the password reset email with new password
                        subject = f'[IBS] 워크스페이스 {user.username}님 계정 비밀번호가 변경되었습니다.'
                        message = f'''[IBS] 워크스페이스 계정의 비밀번호가 관리자에 의해 변경되었습니다. 다음 정보로 로그인 하세요.: \n\n메일주소 : {email}\n비밀번호 : {password}\n\nURL 주소 : {scheme}://{curr_host}'''

                    try:
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                    except Exception as e:
                        print(f"비밀번호 재설정 메일 발송 실패: {e}")
                        return Response({'detail': '비밀번호 처리가 완료되었으나 알림 이메일 발송에 실패했습니다.'}, status=status.HTTP_200_OK)

                    return Response({'detail': '비밀번호 재설정 처리 및 알림 이메일을 발송했습니다.'}, status=status.HTTP_200_OK)
        except Exception as e:
            # 트랜잭션 내에서 에러 발생 시 롤백됨
            return Response({'detail': f'처리 중 오류 발생: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': '사용자 정보 변경 처리가 완료되었습니다.'}, status=status.HTTP_200_OK)
