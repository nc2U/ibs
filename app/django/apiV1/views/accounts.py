import base64
import logging

from allauth.account.forms import default_token_generator
from django.conf import settings
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

from accounts.models import User, Profile, DocScrape, PostScrape, Todo, PasswordResetToken, FCMDevice, Notification
from apiV1.permissions.auth_perms import IsOwnerOnly, IsWorkManagerOnly
from work.models.issue import Issue, Tracker, IssueStatus, CodeIssuePriority
from work.models.project import Role, Member, IssueProject
from ..pagination import PageNumberPaginationThreeThousand, PageNumberPaginationFifty
from ..serializers.accounts import UserSerializer, ProfileSerializer, \
    DocScrapeSerializer, PostScrapeSerializer, TodoSerializer, ChangePasswordSerializer, \
    PasswordResetSerializer, PasswordResetTokenSerializer, AdminCreateUserSerializer, \
    FCMDeviceSerializer, NotificationSerializer


# Accounts --------------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPaginationThreeThousand
    permission_classes = (AllowAny,)
    filterset_fields = ('is_staff', 'is_active', 'is_system', 'staff__status')

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if self.action in ('update', 'partial_update', 'destroy'):
            if not (request.user.is_superuser or getattr(request.user, 'work_manager', False)):
                if obj.pk != request.user.pk:
                    self.permission_denied(
                        request,
                        message='다른 사용자의 계정 정보를 수정하거나 삭제할 권한이 없습니다.',
                        code=status.HTTP_403_FORBIDDEN
                    )

    def get_queryset(self):
        user = self.request.user

        # 로그인하지 않은 경우 목록 노출 방지
        if not user or not user.is_authenticated:
            return User.objects.none()

        # 1. 기본값: 일반 계정(is_system=False)만 조회 (명시적 ?is_system=true 또는 all 파라미터 지원)
        is_system_param = self.request.query_params.get('is_system')
        if is_system_param is None:
            queryset = User.objects.filter(is_system=False)
        elif is_system_param.lower() in ('true', '1'):
            queryset = User.objects.filter(is_system=True)
        elif is_system_param.lower() in ('false', '0'):
            queryset = User.objects.filter(is_system=False)
        else:  # 'all' 등
            queryset = User.objects.all()

        # 2. 기본값: 활성 사용자(is_active=True)만 조회 (인사/관리자용 명시적 파라미터 지원)
        is_active_param = self.request.query_params.get('is_active')
        if is_active_param is None:
            queryset = queryset.filter(is_active=True)
        elif is_active_param.lower() in ('true', '1'):
            queryset = queryset.filter(is_active=True)
        elif is_active_param.lower() in ('false', '0'):
            queryset = queryset.filter(is_active=False)
        # 'all'인 경우 filter 생략

        # N+1 쿼리 방지 Eager Loading 적용
        queryset = queryset.select_related(
            'profile',
            'staff__executive__rank',
            'staff__position',
            'staff__grade'
        ).prefetch_related('member_set__project')

        # 슈퍼유저나 work_manager는 전체 사용자 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        if UserSerializer().get_is_hq_staff(user):
            return queryset

        # 1. 사용자의 프로젝트별 user_visible 권한 수준 판별
        user_members = Member.objects.filter(user=user).prefetch_related('roles')

        user_visibility_order = {'ALL': 2, 'PRJ': 1, 'NOP': 0}
        best_user_visible = 'NOP'

        for member in user_members:
            for role in member.roles.all():
                if user_visibility_order.get(role.user_visible, 0) > user_visibility_order.get(best_user_visible, 0):
                    best_user_visible = role.user_visible

        # 비회원 역할 pk=2 참고
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

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return DocScrape.objects.none()
        if user.is_superuser:
            return DocScrape.objects.all()
        return DocScrape.objects.filter(user=user)


class PostScrapeViewSet(viewsets.ModelViewSet):
    queryset = PostScrape.objects.all()
    serializer_class = PostScrapeSerializer
    permission_classes = (IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user',)
    search_fields = ('title', 'post__title', 'post__content')

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return PostScrape.objects.none()
        if user.is_superuser:
            return PostScrape.objects.all()
        return PostScrape.objects.filter(user=user)


class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (IsAuthenticated, IsOwnerOnly)
    filterset_fields = ('user', 'soft_deleted')
    search_fields = ('title',)

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Todo.objects.none()
        qs = Todo.objects.select_related('issue', 'issue__project')
        if user.is_superuser:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def convert_to_issue(self, request, pk=None):
        todo = self.get_object()
        if todo.issue_id is not None:
            return Response({'error': '이미 업무로 전환된 할일입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        project_id = request.data.get('project')
        if not project_id:
            return Response({'error': '업무를 등록할 워크스페이스를 선택해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            issue_project = IssueProject.objects.select_related('module').get(pk=project_id)
        except IssueProject.DoesNotExist:
            return Response({'error': '유효하지 않은 워크스페이스입니다.'}, status=status.HTTP_404_NOT_FOUND)

        if issue_project.status != '1':
            return Response({'error': '활성 상태인 워크스페이스에만 업무를 등록할 수 있습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(issue_project, 'module') and not issue_project.module.issue:
            return Response({'error': '해당 워크스페이스는 업무 모듈이 비활성화되어 있습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 권한 확인: 사용자가 해당 워크스페이스의 멤버(상속 포함)이거나 슈퍼유저/work_manager인지 확인
        user = request.user
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            is_member = any(m['user']['pk'] == user.pk for m in issue_project.all_members())
            if not is_member and not issue_project.is_public:
                return Response({'error': '해당 워크스페이스에 접근 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        # Tracker 결정: request.data.get('tracker') or 워크스페이스 허용 trackers 중 첫 번째 or 기본 tracker
        tracker_id = request.data.get('tracker')
        tracker = None
        if tracker_id:
            tracker = Tracker.objects.filter(pk=tracker_id).first()
        if not tracker:
            tracker = issue_project.trackers.first() or Tracker.objects.first()

        if not tracker:
            return Response({'error': '사용 가능한 업무 유형(Tracker)이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # Status 결정: request.data.get('status') or tracker.default_status or 첫 번째 미종료 status
        status_id = request.data.get('status')
        issue_status = None
        if status_id:
            issue_status = IssueStatus.objects.filter(pk=status_id).first()
        if not issue_status:
            issue_status = getattr(tracker, 'default_status', None) or IssueStatus.objects.filter(closed=False).first()

        if not issue_status:
            return Response({'error': '사용 가능한 업무 상태(Status)가 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # Priority 결정: request.data.get('priority') or 기본 priority or 첫 번째 priority
        priority_id = request.data.get('priority')
        priority = None
        if priority_id:
            priority = CodeIssuePriority.objects.filter(pk=priority_id).first()
        if not priority:
            priority = CodeIssuePriority.objects.filter(default=True).first() or CodeIssuePriority.objects.first()

        subject = request.data.get('subject') or todo.title

        with transaction.atomic():
            issue = Issue.objects.create(
                project=issue_project,
                tracker=tracker,
                status=issue_status,
                priority=priority,
                subject=subject,
                description=request.data.get('description', ''),
                assigned_to=user,
                start_date=timezone.now().date(),
                creator=user,
                updater=user,
            )
            todo.completed = True
            todo.issue = issue
            todo.save(update_fields=['completed', 'issue', 'updated'])

        return Response({
            'todo': TodoSerializer(todo).data,
            'issue': {
                'pk': issue.pk,
                'project_id': issue_project.pk,
                'project_slug': issue_project.slug,
                'project_name': issue_project.name,
                'subject': issue.subject,
            }
        }, status=status.HTTP_201_CREATED)


class CheckPasswordView(APIView):
    """비밀번호가 맞는지 체크하는 API"""
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request, *args, **kwargs):
        password = request.data.get('password', None)

        if not password:
            return Response({'detail': 'Password not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=request.data.get('email'), password=password)

        if user is not None:
            # Password is correct
            return Response({'detail': 'Password correct.'}, status=status.HTTP_200_OK)
        else:
            # Password is incorrect
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

            # Generate a password reset token (이전 미사용 토큰 정리 후 단일 발급)
            token = default_token_generator.make_token(user)
            PasswordResetToken.objects.filter(user=user).delete()
            token_db = PasswordResetToken.objects.create(user=user, token=token)

            # Create a password reset link
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            scheme = 'http' if settings.DEBUG else 'https'
            curr_host = request.get_host()

            reset_link = f'{scheme}://{curr_host}/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

            # Send the password reset email
            subject = f'[IBS] 워크스페이스 :: 비밀번호 재설정 안내'
            message = (f"""
안녕하세요, {user.username}님.

비밀번호 재설정을 요청하셨습니다.

아래 링크를 클릭하여 새로운 비밀번호를 설정해 주세요.

{reset_link}

※ 이 링크는 발송 후 10분 동안만 유효하며, 한 번 사용하면 다시 사용할 수 없습니다.

본인이 요청하지 않은 경우에는 이 메일을 무시하시면 됩니다.
감사합니다.

IBS 워크스페이스""")
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            return Response({'detail': '비밀번호 재설정을 위한 이메일을 발송했습니다.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """비밀번호 재설정 링크를 통해서 비밀번호를 재설정하는 API"""
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request, *args, **kwargs):
        try:
            user_id = force_str(urlsafe_base64_decode(kwargs.get('user_id')))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        token = kwargs.get('token')
        if default_token_generator.check_token(user, token):
            token_db = PasswordResetToken.objects.filter(user=user, token=token).order_by('-created').first()
            if token_db and not token_db.is_expired():
                # Token is valid, perform password reset
                new_password = request.data.get('new_password')
                user.set_password(new_password)
                user.save()
                token_db.delete()  # 일회용 토큰 소모

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
                username = serializer.validated_data.get('username')
                password = serializer.validated_data.get('password')
                user = User(email=email, username=username)
                user.set_password(password)
                user.save()

                # 2. 기본 프로필 등록
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
                        PasswordResetToken.objects.filter(user=user).delete()
                        token_db = PasswordResetToken.objects.create(user=user, token=token, expired=expired * 3600)

                        # Create a password reset link
                        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                        reset_link = f'{scheme}://{curr_host}/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

                        # Send the password reset email
                        subject = f'[IBS] 워크스페이스 :: 새 계정 생성 안내'
                        message = f'''
안녕하세요, {user.username}님.

IBS 워크스페이스 계정이 생성되었습니다.

아래 링크를 클릭하여 비밀번호를 설정한 후 서비스를 이용해 주세요.

{reset_link}

※ 이 링크는 발송 후 {expired}시간 동안만 유효합니다.
만료되기 전에 비밀번호를 설정하지 못한 경우 관리자에게 문의하시기 바랍니다.

감사합니다.

IBS 워크스페이스
'''
                    else:
                        # Send the password reset email
                        subject = f'[IBS] 워크스페이스 :: 새 계정 생성 안내'
                        message = f'''
안녕하세요, {user.username}님.

IBS 워크스페이스 계정이 생성되었습니다.

아래 계정 정보로 로그인하실 수 있습니다.

메일주소 : {email}
초기 비밀번호 : {password}

접속 주소 : {scheme}://{curr_host}

로그인 후 보안을 위해 비밀번호를 변경하시기를 권장합니다.
메뉴 접근 권한에 관한 사항은 관리자에게 문의하시기 바랍니다.

감사합니다.

IBS 워크스페이스'''

                    try:
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                    except Exception as e:
                        logger.error(f"관리자 유저 생성 메일 발송 실패: {e}")
                        return Response(
                            {'pk': user.pk, 'detail': '새 계정이 생성되었으나 알림 이메일 발송에는 실패했습니다. 비밀번호를 수동으로 전달하십시오.'},
                            status=status.HTTP_201_CREATED)

                    return Response({'pk': user.pk, 'detail': '새 계정을 생성하고 비밀번호 설정을 위한 이메일을 발송했습니다.'},
                                    status=status.HTTP_201_CREATED)

            return Response({'pk': user.pk, 'detail': '새 계정을 생성하였습니다.'}, status=status.HTTP_201_CREATED)
        except Exception:
            return Response({'detail': f'사용자 생성 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                        PasswordResetToken.objects.filter(user=user).delete()
                        token_db = PasswordResetToken.objects.create(user=user, token=token, expired=expired * 3600)

                        # Create a password reset link
                        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                        reset_link = f'{scheme}://{curr_host}/#/accounts/pass-reset/?uidb64={uidb64}&token={token}'

                        # Send the password reset email
                        subject = f'[IBS] 워크스페이스 :: {user.username}님 계정 비밀번호 초기화 안내'
                        message = f'''
안녕하세요.

관리자에 의해 IBS 워크스페이스 계정의 비밀번호가 초기화되었습니다.

계속해서 서비스를 이용하려면 아래 링크를 클릭하여 새로운 비밀번호를 설정해 주세요.

{reset_link}

이 링크는 발송 시점부터 {expired}시간 동안만 유효합니다.
유효기간 내에 비밀번호를 설정하지 않으면 링크가 만료되며, 다시 발급받아야 합니다.
필요한 경우 관리자에게 문의하시기 바랍니다.

감사합니다.

※ 본인이 요청하거나 관리자에게 안내받은 내용이 아니라면 즉시 관리자에게 문의하시기 바랍니다.'''
                    else:
                        # Send the password reset email with new password
                        subject = f'[IBS] 워크스페이스 :: {user.username}님 계정 비밀번호 변경 안내'
                        message = f'''
안녕하세요.

관리자에 의해 IBS 워크스페이스 계정의 비밀번호가 변경되었습니다.

아래 계정 정보로 로그인하실 수 있습니다.

메일주소 : {email}
임시 비밀번호 : {password}

로그인 주소
{scheme}://{curr_host}

로그인 후에는 보안을 위해 비밀번호를 변경하시기를 권장합니다.

감사합니다.'''

                    try:
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                    except Exception as e:
                        logger.error(f"비밀번호 재설정 메일 발송 실패: {e}")
                        return Response({'detail': '비밀번호 처리가 완료되었으나 알림 이메일 발송에 실패했습니다.'}, status=status.HTTP_200_OK)

                    return Response({'detail': '비밀번호 재설정 처리 및 알림 이메일을 발송했습니다.'}, status=status.HTTP_200_OK)
        except Exception:
            # 트랜잭션 내에서 에러 발생 시 롤백됨
            return Response({'detail': f'처리 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': '사용자 정보 변경 처리가 완료되었습니다.'}, status=status.HTTP_200_OK)


class FCMDeviceViewSet(viewsets.ModelViewSet):
    """모바일 FCM 기기 등록 및 토큰 관리"""
    queryset = FCMDevice.objects.all()
    serializer_class = FCMDeviceSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        return FCMDevice.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        registration_id = request.data.get('registration_id')
        if not registration_id:
            return Response({'detail': 'registration_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        device_id = request.data.get('device_id', '')
        platform = request.data.get('platform', 'android')

        # 기존 다른 사용자에게 등록된 동일 토큰이 있다면 현재 사용자로 소유권 업데이트
        device, created = FCMDevice.objects.update_or_create(
            registration_id=registration_id,
            defaults={
                'user': request.user,
                'device_id': device_id,
                'platform': platform,
                'is_active': True,
            }
        )
        serializer = self.get_serializer(device)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """사용자 인앱 알림 목록 및 읽음 처리 (채팅 알림은 알림 센터에서 제외)"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPaginationFifty

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).exclude(category='chat')

    @action(detail=True, methods=['post'], url_path='read')
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'status': 'read', 'id': notification.pk})

    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_as_read(self, request):
        updated_count = Notification.objects.filter(user=request.user, is_read=False).exclude(category='chat').update(
            is_read=True)
        return Response({'status': 'all_read', 'updated_count': updated_count})

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).exclude(category='chat').count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['post'], url_path='read-by-target')
    def mark_read_by_target(self, request):
        """특정 대상(업무/회의록/문서 등)에 해당하는 미확인 알림을 일괄 읽음 처리"""
        target_type = request.data.get('target_type')
        target_id = str(request.data.get('target_id') or '')
        if not target_type or not target_id:
            return Response({'detail': 'target_type and target_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = Notification.objects.filter(
            user=request.user,
            target_type=target_type,
            target_id=target_id,
            is_read=False,
        ).update(is_read=True)
        return Response({'status': 'ok', 'updated_count': updated_count})
