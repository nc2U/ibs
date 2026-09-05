from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Todo, Profile

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

        self.todo_a = Todo.objects.create(user=self.user_a, title='A의 할일')
        self.todo_b = Todo.objects.create(user=self.user_b, title='B의 할일')

    def test_public_user_registration(self):
        """비인가 사용자도 회원가입(POST /api/v1/user/)은 정상 허용됨"""
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
