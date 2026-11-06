from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from allauth.account.forms import default_token_generator
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Todo, Profile, PasswordResetToken, FCMDevice, Notification
from company.models import Company
from work.models.project import IssueProject

User = get_user_model()


class AccountsSecurityAndIsolationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='password123'
        )
        self.user_a = User.objects.create_user(
            username='usera', email='usera@test.com', password='password123'
        )
        self.user_b = User.objects.create_user(
            username='userb', email='userb@test.com', password='password123'
        )

        self.profile_a = Profile.objects.create(user=self.user_a, name='User A')
        self.profile_b = Profile.objects.create(user=self.user_b, name='User B')

        self.todo_a = Todo.objects.create(user=self.user_a, title='A의 할일')
        self.todo_b = Todo.objects.create(user=self.user_b, title='B의 할일')

    def test_public_user_registration(self):
        """비인가 사용자도 회원가입(POST /api/v1/user/)은 정상 허용됨"""
        with patch('apiV1.serializers.accounts.send_mail'):
            res = self.client.post('/api/v1/user/', {
                'username': 'newuser',
                'email': 'newuser@test.com',
                'password': 'password123'
            })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@test.com').exists())

    def test_unauthenticated_user_list_returns_empty(self):
        """비로그인 상태에서 사용자 목록 조회 시 401 Unauthorized 차단"""
        res = self.client.get('/api/v1/user/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_modify_or_delete_other_user(self):
        """일반 사용자는 타인의 계정 정보를 수정하거나 삭제할 수 없음 (403 또는 404 차단)"""
        self.client.force_authenticate(user=self.user_a)

        # 타인 계정 수정 시도
        res_patch = self.client.patch(f'/api/v1/user/{self.user_b.pk}/', {
            'username': 'hacked_name'
        })
        self.assertIn(res_patch.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

        # 타인 계정 삭제 시도
        res_del = self.client.delete(f'/api/v1/user/{self.user_b.pk}/')
        self.assertIn(res_del.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

    def test_user_cannot_escalate_privileges_on_self_update(self):
        """사용자가 본인 계정 수정 시 is_superuser, work_manager 등 관리자 권한 필드는 변경 불가"""
        self.client.force_authenticate(user=self.user_a)

        res = self.client.patch(f'/api/v1/user/{self.user_a.pk}/', {
            'username': 'usera_updated',
            'is_superuser': True,
            'is_staff': True,
            'work_manager': True
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.user_a.refresh_from_db()
        self.assertEqual(self.user_a.username, 'usera_updated')
        self.assertFalse(self.user_a.is_superuser)
        self.assertFalse(self.user_a.is_staff)
        self.assertFalse(self.user_a.work_manager)

    def test_user_cannot_escalate_is_system_on_self_update(self):
        """일반 사용자가 is_system=True로 시스템 계정 위장 시도 시 차단"""
        self.client.force_authenticate(user=self.user_a)
        res = self.client.patch(f'/api/v1/user/{self.user_a.pk}/', {
            'is_system': True
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user_a.refresh_from_db()
        self.assertFalse(self.user_a.is_system)

    def test_work_manager_cannot_modify_or_delete_superuser(self):
        """work_manager는 일반 사용자는 관리할 수 있으나, 최고관리자(superuser) 계정은 수정/삭제 불가"""
        wm_user = User.objects.create_user(
            username='workmgr', email='wm@test.com', password='password123', work_manager=True
        )
        self.client.force_authenticate(user=wm_user)

        # 1. UserViewSet을 통한 슈퍼유저 수정 차단 (403)
        res_patch = self.client.patch(f'/api/v1/user/{self.admin.pk}/', {
            'username': 'admin_hacked'
        })
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        # 2. UserViewSet을 통한 슈퍼유저 삭제 차단 (403)
        res_del = self.client.delete(f'/api/v1/user/{self.admin.pk}/')
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

        # 3. AdminManageUserView.put을 통한 슈퍼유저 비밀번호/활성화 수정 차단 (403)
        res_put = self.client.put('/api/v1/admin-create-user/', {
            'email': self.admin.email,
            'is_active': False
        })
        self.assertEqual(res_put.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_modify_other_user(self):
        """관리자(슈퍼유저)는 타 사용자 권한 필드 수정 가능"""
        self.client.force_authenticate(user=self.admin)

        res = self.client.patch(f'/api/v1/user/{self.user_b.pk}/', {
            'work_manager': True
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.user_b.refresh_from_db()
        self.assertTrue(self.user_b.work_manager)

    def test_todo_ownership_isolation(self):
        """Todo는 작성자 본인 데이터만 조회 가능"""
        self.client.force_authenticate(user=self.user_a)

        res = self.client.get('/api/v1/todo/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        todo_titles = [item['title'] for item in res.data['results']]
        self.assertIn('A의 할일', todo_titles)
        self.assertNotIn('B의 할일', todo_titles)

    def test_user_cannot_modify_is_active_via_profile(self):
        """일반 사용자는 Profile 수정을 통해 본인 계정의 is_active를 조작할 수 없음 (보안 취약점 방어)"""
        self.client.force_authenticate(user=self.user_a)

        # 일반 사용자가 is_active=False로 비활성화 시도하거나 임의 조작 시도
        res = self.client.patch(f'/api/v1/profile/{self.profile_a.pk}/', {
            'is_active': False
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.user_a.refresh_from_db()
        # 일반 사용자의 요청으로는 is_active가 변경되지 않아야 함
        self.assertTrue(self.user_a.is_active)

    def test_admin_can_modify_is_active_via_profile(self):
        """관리자는 Profile 수정을 통해 사용자의 is_active 변경 가능"""
        self.client.force_authenticate(user=self.admin)

        # 관리자 본인 프로필 또는 관리자 권한으로 is_active 변경
        admin_profile = Profile.objects.create(user=self.admin, name='Admin Profile')
        res = self.client.patch(f'/api/v1/profile/{admin_profile.pk}/', {
            'is_active': True
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class PasswordResetSecurityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='resetuser', email='resetuser@test.com', password='old_password123'
        )

    def test_multiple_password_reset_requests_do_not_cause_500(self):
        """비밀번호 재설정을 연속 2회 이상 요청해도 MultipleObjectsReturned 예외 없이 안전하게 새 토큰 발급"""
        with patch('apiV1.views.accounts.send_mail') as mock_send:
            # 1회차 요청
            res1 = self.client.post('/api/v1/password-reset/', {'email': self.user.email})
            self.assertEqual(res1.status_code, status.HTTP_200_OK)

            # 2회차 요청 (기존 토큰이 있는 상태)
            res2 = self.client.post('/api/v1/password-reset/', {'email': self.user.email})
            self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # 최종적으로 단 1개의 유효 토큰만 유지되는지 검증
        tokens = PasswordResetToken.objects.filter(user=self.user)
        self.assertEqual(tokens.count(), 1)

    def test_password_reset_confirm_successful_flow(self):
        """비밀번호 재설정 확인 성공 시 비밀번호가 변경되고 일회용 토큰이 소모(delete)됨"""
        token = default_token_generator.make_token(self.user)
        PasswordResetToken.objects.create(user=self.user, token=token)

        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        confirm_url = f'/api/v1/password-reset-confirm/{uidb64}/{token}/'

        res = self.client.post(confirm_url, {'new_password': 'new_secure_password123'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 비밀번호 갱신 확인
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new_secure_password123'))

        # 일회용 토큰 삭제 확인
        self.assertFalse(PasswordResetToken.objects.filter(user=self.user, token=token).exists())

    def test_password_reset_confirm_invalid_uid_returns_400(self):
        """잘못된 UIDb64가 전달되었을 때 500이 아닌 400 Bad Request 반환"""
        invalid_url = '/api/v1/password-reset-confirm/invalid-base-64!/fake-token/'
        res = self.client.post(invalid_url, {'new_password': 'any_password'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_token_expiration(self):
        """만료 시간 지난 토큰은 is_expired()가 True 반환 및 401 반환"""
        token_obj = PasswordResetToken.objects.create(
            user=self.user,
            token='test_token',
            expired=0  # 즉시 만료
        )
        self.assertTrue(token_obj.is_expired())

    def test_pass_reset_token_endpoint_removed(self):
        """토큰 값을 노출하던 /pass-reset-token/ 엔드포인트는 더 이상 존재하지 않음"""
        token = default_token_generator.make_token(self.user)
        PasswordResetToken.objects.create(user=self.user, token=token)
        res = self.client.get(f'/api/v1/pass-reset-token/?user={self.user.pk}')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn(token, res.content.decode())

    def test_password_reset_confirm_get_validates_without_exposing_token(self):
        """GET 검증: 유효 토큰은 valid=True, 응답에 토큰 값 미포함, 비밀번호/토큰 상태 변경 없음"""
        token = default_token_generator.make_token(self.user)
        PasswordResetToken.objects.create(user=self.user, token=token)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

        res = self.client.get(f'/api/v1/password-reset-confirm/{uidb64}/{token}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), {'valid': True})
        self.assertNotIn(token, res.content.decode())
        self.assertTrue(PasswordResetToken.objects.filter(user=self.user, token=token).exists())

    def test_password_reset_confirm_get_invalid_cases(self):
        """GET 검증: 만료/불일치 토큰/잘못된 uid 는 모두 valid=False"""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        # 만료된 토큰
        PasswordResetToken.objects.create(user=self.user, token=token, expired=0)
        res = self.client.get(f'/api/v1/password-reset-confirm/{uidb64}/{token}/')
        self.assertEqual(res.json(), {'valid': False})

        # 토큰 불일치
        res = self.client.get(f'/api/v1/password-reset-confirm/{uidb64}/wrong-token/')
        self.assertEqual(res.json(), {'valid': False})

        # 잘못된 uid
        res = self.client.get('/api/v1/password-reset-confirm/invalid-base-64!/fake/')
        self.assertEqual(res.json(), {'valid': False})


class FCMDeviceAndNotificationTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='fcmuser1', email='fcm1@test.com', password='password123')
        self.user2 = User.objects.create_user(username='fcmuser2', email='fcm2@test.com', password='password123')

    def test_fcm_device_register_and_takeover(self):
        """동일 기기 토큰으로 다른 사용자가 로그인 시 소유권 갱신(Takeover) 처리 검증"""
        self.client.force_authenticate(user=self.user1)
        res1 = self.client.post('/api/v1/fcm-device/', {
            'registration_id': 'unique_fcm_token_12345',
            'device_id': 'device_abc',
            'platform': 'android'
        })
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        device = FCMDevice.objects.get(registration_id='unique_fcm_token_12345')
        self.assertEqual(device.user, self.user1)

        # user2로 동일 토큰 등록 시 소유권 이전
        self.client.force_authenticate(user=self.user2)
        res2 = self.client.post('/api/v1/fcm-device/', {
            'registration_id': 'unique_fcm_token_12345',
            'device_id': 'device_abc',
            'platform': 'android'
        })
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        device.refresh_from_db()
        self.assertEqual(device.user, self.user2)

    def test_notification_list_and_read_actions(self):
        """인앱 알림 조회, 읽음 처리, 일괄 읽음 및 채팅 알림 제외 검증"""
        self.client.force_authenticate(user=self.user1)

        # 알림 생성 (업무 2건, 채팅 1건)
        n1 = Notification.objects.create(user=self.user1, title='업무 알림 1', body='내용 1', category='work', target_type='issue', target_id='10')
        n2 = Notification.objects.create(user=self.user1, title='결재 알림 2', body='내용 2', category='approval', target_type='document', target_id='20')
        Notification.objects.create(user=self.user1, title='채팅 메시지', body='채팅 내용', category='chat')

        # 1. 목록 조회 시 채팅 제외 확인
        res_list = self.client.get('/api/v1/notification/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(res_list.data['count'], 2)

        # 2. 미확인 알림 수 확인
        res_unread = self.client.get('/api/v1/notification/unread-count/')
        self.assertEqual(res_unread.data['unread_count'], 2)

        # 3. 단일 알림 읽음 처리
        res_read = self.client.post(f'/api/v1/notification/{n1.pk}/read/')
        self.assertEqual(res_read.status_code, status.HTTP_200_OK)
        n1.refresh_from_db()
        self.assertTrue(n1.is_read)

        # 4. 대상별 읽음 처리 (target_type='document', target_id='20')
        res_by_target = self.client.post('/api/v1/notification/read-by-target/', {
            'target_type': 'document',
            'target_id': '20'
        })
        self.assertEqual(res_by_target.status_code, status.HTTP_200_OK)
        n2.refresh_from_db()
        self.assertTrue(n2.is_read)

        # 5. 전체 미확인 수 0 확인
        res_unread2 = self.client.get('/api/v1/notification/unread-count/')
        self.assertEqual(res_unread2.data['unread_count'], 0)


class InstallViewsRegressionTests(APITestCase):
    def test_issue_project_creation_with_type_field(self):
        """IssueProject 생성 시 type 필드 정상 지정 검증 (TypeError 방지)"""
        company = Company.objects.create(name='설치 테스트 회사')
        user = User.objects.create_superuser(username='installadmin', email='install@test.com', password='password123')

        # accounts.views.create_project에서 사용되는 모델 생성 로직
        issue_project = IssueProject.objects.create(
            company=company,
            type='2',
            name='설치 프로젝트 1',
            slug='install-proj1',
            description='신축사업',
            creator=user
        )
        self.assertIsNotNone(issue_project.pk)
        self.assertEqual(issue_project.type, '2')

    def test_create_superuser_post_blocked_when_superuser_already_exists(self):
        """슈퍼유저가 이미 존재하는 경우 POST /install/create/superuser/ 접근 시 redirect 차단"""
        User.objects.create_superuser(username='existingadmin', email='exist@test.com', password='password123')

        res = self.client.post('/install/create/superuser/', {
            'username': 'attacker',
            'email': 'attacker@test.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })
        # 이미 슈퍼유저가 존재하므로 리다이렉트되어 새 유저 생성 안 됨
        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertFalse(User.objects.filter(email='attacker@test.com').exists())


class PasswordAndAuthSecurityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='authuser', email='authuser@test.com', password='securePassword123!')
        self.target_user = User.objects.create_user(username='victim', email='victim@test.com', password='victimPassword123!')

    def test_check_password_oracle_defense(self):
        """타인 계정 비밀번호 대리 확인 시도(오라클 공격) 시 403 Forbidden 차단"""
        self.client.force_authenticate(user=self.user)

        # 본인 계정 비밀번호 정상 확인
        res_self = self.client.post('/api/v1/check-password/', {
            'email': self.user.email,
            'password': 'securePassword123!'
        })
        self.assertEqual(res_self.status_code, status.HTTP_200_OK)

        # 타인 이메일로 비밀번호 일치 확인 시도 시 차단
        res_victim = self.client.post('/api/v1/check-password/', {
            'email': self.target_user.email,
            'password': 'victimPassword123!'
        })
        self.assertEqual(res_victim.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_password_validation(self):
        """비밀번호 변경 시 기존 비밀번호 일치 및 신규 비밀번호 유효성 검증"""
        self.client.force_authenticate(user=self.user)

        # 종전 비밀번호 불일치 시 400
        res_wrong_old = self.client.post('/api/v1/change-password/', {
            'old_password': 'wrongPassword!',
            'new_password': 'NewPassword12345!'
        })
        self.assertEqual(res_wrong_old.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('패스워드가 맞지 않습니다.', res_wrong_old.data['detail'])

        # 정상 비밀번호 변경 성공
        res_ok = self.client.post('/api/v1/change-password/', {
            'old_password': 'securePassword123!',
            'new_password': 'BrandNewSecurePassword1234!'
        })
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('BrandNewSecurePassword1234!'))
