import base64

from allauth.account.forms import default_token_generator
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ..pagination import *
from ..permission import *
from ..serializers.accounts import *


# Accounts --------------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPaginationThreeThousand
    permission_classes = (permissions.AllowAny,)
    filterset_fields = ('is_staff', 'is_active',)


class StaffAuthViewSet(viewsets.ModelViewSet):
    queryset = StaffAuth.objects.all()
    serializer_class = StaffAuthInUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocScrapeViewSet(viewsets.ModelViewSet):
    queryset = DocScrape.objects.all()
    serializer_class = DocScrapeSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user',)
    search_fields = ('title', 'post__title', 'post__content')


class PostScrapeViewSet(viewsets.ModelViewSet):
    queryset = PostScrape.objects.all()
    serializer_class = PostScrapeSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user',)
    search_fields = ('title', 'post__title', 'post__content')


class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsOwnerOnly)
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
    permission_classes = (permissions.IsAuthenticated,)

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
    permission_classes = (permissions.AllowAny,)

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

            reset_link = f'{scheme}://{curr_host}/cms/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

            # Send the password reset email
            subject = f'[IBS] {user.username}님 계정 비밀번호 초기화 링크 안내드립니다.'
            message = f'비밀번호를 재설정 하기 위해서 다음 링크를 클릭 하세요: \n{reset_link}\n\n이 링크는 발송 후 10분 후에 만료됩니다.'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            return Response({'detail': '비밀번호 재설정을 위한 이메일을 발송했습니다.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """비밀번호 재설정 링크를 통해서 비밀번호를 재설정하는 API"""
    permission_classes = (permissions.AllowAny,)

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
                # authenticated_user = authenticate(username=user.username, password=new_password)
                # login(request, authenticated_user)

                return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'This token was expired'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)


class PasswordResetTokenViewSet(viewsets.ModelViewSet):
    queryset = PasswordResetToken.objects.all()
    serializer_class = PasswordResetTokenSerializer
    permission_classes = (permissions.AllowAny,)
    filterset_fields = ('user', 'token')


class AdminCreateUserView(APIView):
    """비밀번호 분실 시 재설정 링크를 요청하는 API"""
    permission_classes = (permissions.IsAdminUser,)

    @staticmethod
    def post(request, *args, **kwargs):
        serializer = AdminCreateUserSerializer(data=request.data)
        if serializer.is_valid():
            # Find the user with the given email
            email = serializer.validated_data.get('email')
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')
            mail_sending = serializer.validated_data.get('mail_sending')
            send_option = serializer.validated_data.get('send_option')
            expired = serializer.validated_data.get('expired')
            print("Serializer is valid:", serializer.validated_data)

            try:
                User.objects.get(email=email)
                print(f"User with email {email} already exists.")
                return Response({'detail': '입력한 이메일로 등록된 사용자가 이미 존재합니다.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                print(f"No user found with email {email}. Proceeding with user creation.")

            # 1. 관리자가 입력한 계정 정보(임의 패스워드 포함)로 계정 생성
            user = User(email=email, username=username)
            user.set_password(password)
            user.save()

            # 2. 기본 스태프 권한 및 프로필 등록
            StaffAuth.objects.create(user=user, company_id=1, is_project_staff=True)
            Profile.objects.create(user=user)

            if mail_sending is not None:
                scheme = 'http' if settings.DEBUG else 'https'
                curr_host = request.get_host()

                if send_option == '1':
                    # Generate a password reset token
                    token = default_token_generator.make_token(user)
                    try:
                        token_db = PasswordResetToken.objects.get(user=user)
                        token_db.token = token
                    except PasswordResetToken.DoesNotExist:
                        token_db = PasswordResetToken(user=user, token=token, expired=expired*3600)
                    token_db.save()

                    # Create a password reset link
                    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                    reset_link = f'{scheme}://{curr_host}/cms/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

                    # Send the password reset email
                    subject = f'[IBS] {user.username}님 새 계정이 생성 되었습니다.'
                    message = f'''[IBS]를 시작하기 위해 다음 링크를 클릭하여 비밀번호를 설정 하세요.: \n{reset_link}\n\n이 링크는 발송 후 {expired}시간 후에 만료됩니다. 만료되기 전에 패스워드를 설정하지 않은 경우 관리자에게 문의하십시오.'''
                else:
                    # Send the password reset email
                    subject = f'[IBS] {user.username}님 새 계정이 생성 되었습니다.'
                    message = f'''[IBS]를 시작하기 위해 다음 사용자 정보를 이용해 로그인 하세요.: \n\n메일주소 : {email}\n비밀번호 : {password}\n\nURL 주소 : {scheme}://{curr_host}\n\n로그인 및 각 메뉴에 대한 접근 권한은 관리자에게 문의하십시오.'''

                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                except Exception as e:
                    return Response({'detail': '이메일 발송 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({'detail': '새 계정을 생성하고 비밀번호 설정을 위한 이메일을 발송했습니다.'}, status=status.HTTP_200_OK)

            return Response({ 'detail': '새 계정을 생성하였습니다.' }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
