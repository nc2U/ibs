from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from company.models import Company
from forum.models import Forum, PostCategory, Post
from work.models.project import IssueProject, Member, Role, Permission

User = get_user_model()


class ForumAppSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 회사 및 사용자 생성
        self.company = Company.objects.create(name='테스트건설')
        self.admin_user = User.objects.create_superuser(
            username='admin_forum', email='admin@test.com', password='password123'
        )
        self.forum_manager = User.objects.create_user(
            username='manager_forum', email='manager@test.com', password='password123'
        )
        self.member_user = User.objects.create_user(
            username='member_forum', email='member@test.com', password='password123'
        )
        self.other_user = User.objects.create_user(
            username='other_forum', email='other@test.com', password='password123'
        )

        # 권한 및 역할 생성
        self.perm_read = Permission.objects.create(module='forum', code='forum.read', name='포럼 읽기')
        self.perm_create = Permission.objects.create(module='forum', code='forum.create', name='포럼 글쓰기')
        self.perm_update = Permission.objects.create(module='forum', code='forum.update', name='포럼 글수정')
        self.perm_delete = Permission.objects.create(module='forum', code='forum.delete', name='포럼 글삭제')
        self.perm_own_update = Permission.objects.create(module='forum', code='forum.own_update', name='본인 글수정')
        self.perm_own_delete = Permission.objects.create(module='forum', code='forum.own_delete', name='본인 글삭제')

        self.role_member = Role.objects.create(name='일반회원', creator=self.admin_user)
        self.role_member.permissions.add(self.perm_read, self.perm_create, self.perm_own_update, self.perm_own_delete)

        # 1. 비공개 프로젝트 워크스페이스
        self.private_project = IssueProject.objects.create(
            company=self.company,
            name='비공개 프로젝트',
            slug='private-proj',
            is_public=False,
            type='2',
            creator=self.admin_user
        )
        # 멤버 등록 (forum_manager, member_user 등록 / other_user는 미등록)
        m1 = Member.objects.create(project=self.private_project, user=self.forum_manager)
        m1.roles.add(self.role_member)
        m2 = Member.objects.create(project=self.private_project, user=self.member_user)
        m2.roles.add(self.role_member)

        # 2. 포럼 생성
        # (1) 일반 포럼
        self.general_forum = Forum.objects.create(
            project=self.private_project,
            name='자유게시판',
            manager_only=False
        )
        self.general_forum.manager.add(self.forum_manager)

        # (2) 관리자 전용 포럼
        self.notice_forum = Forum.objects.create(
            project=self.private_project,
            name='공지게시판 (관리자전용)',
            manager_only=True
        )
        self.notice_forum.manager.add(self.forum_manager)

        # 3. 게시글 생성
        # (A) 일반 게시글
        self.normal_post = Post.objects.create(
            forum=self.general_forum,
            title='일반 글 제목',
            content='일반 글 본문 내용입니다.',
            creator=self.member_user
        )

        # (B) 비밀글
        self.secret_post = Post.objects.create(
            forum=self.general_forum,
            title='비밀 글 제목',
            content='1급 기밀 본문 내용입니다.',
            is_secret=True,
            password='secret_password_123',
            creator=self.member_user
        )

        # (C) 블라인드글
        self.blind_post = Post.objects.create(
            forum=self.general_forum,
            title='블라인드 글 제목',
            content='유해 게시물 본문입니다.',
            is_blind=True,
            creator=self.member_user
        )

    def test_forum_project_isolation(self):
        """비공개 프로젝트 포럼 열람 격리 검증"""
        # 프로젝트 멤버(member_user)는 포럼 목록 조회 가능
        self.client.force_authenticate(user=self.member_user)
        res_member = self.client.get('/api/v1/forum/')
        self.assertEqual(res_member.status_code, status.HTTP_200_OK)
        forum_ids = [item.get('pk') or item.get('id') for item in res_member.data.get('results', res_member.data)]
        self.assertIn(self.general_forum.pk, forum_ids)

        # 프로젝트 비멤버(other_user)는 포럼 목록에서 제외
        self.client.force_authenticate(user=self.other_user)
        res_other = self.client.get('/api/v1/forum/')
        self.assertEqual(res_other.status_code, status.HTTP_200_OK)
        other_forum_ids = [item.get('pk') or item.get('id') for item in res_other.data.get('results', res_other.data)]
        self.assertNotIn(self.general_forum.pk, other_forum_ids)

    def test_manager_only_forum_write_restriction(self):
        """관리자 전용 포럼(manager_only=True) 작성 제한 검증"""
        # 일반 멤버가 공지게시판 작성 시도 시 차단
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'forum': self.notice_forum.pk,
            'title': '일반 멤버의 공지 작성 시도',
            'content': '작성 실패해야 함'
        }
        res_fail = self.client.post('/api/v1/post/', payload, format='json')
        # ForumPermission에서 403 Forbidden 또는 Serializer validate에서 400 Bad Request
        self.assertIn(res_fail.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

        # 포럼 매니저는 정상 작성 (201 Created)
        self.client.force_authenticate(user=self.forum_manager)
        payload_mgr = {
            'forum': self.notice_forum.pk,
            'title': '공지사항 안내',
            'content': '포럼 매니저의 정상 공지'
        }
        res_ok = self.client.post('/api/v1/post/', payload_mgr, format='json')
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)

    def test_secret_post_masking_and_authorization(self):
        """비밀글 본문 마스킹 및 패스워드 은닉 검증"""
        # 1. 제3자(다른 멤버)가 비밀글 조회 시 본문 마스킹
        # another_member를 워크스페이스에 추가
        another_member = User.objects.create_user(
            username='another_m', email='another@test.com', password='password123'
        )
        m = Member.objects.create(project=self.private_project, user=another_member)
        m.roles.add(self.role_member)

        self.client.force_authenticate(user=another_member)
        res_masked = self.client.get(f'/api/v1/post/{self.secret_post.pk}/')
        self.assertEqual(res_masked.status_code, status.HTTP_200_OK)
        self.assertEqual(res_masked.data['content'], '비밀글입니다.')
        # password 필드가 API 응답에 노출되지 않음
        self.assertNotIn('password', res_masked.data)

        # 2. 작성자 본인은 원본 본문 열람 가능
        self.client.force_authenticate(user=self.member_user)
        res_author = self.client.get(f'/api/v1/post/{self.secret_post.pk}/')
        self.assertEqual(res_author.status_code, status.HTTP_200_OK)
        self.assertEqual(res_author.data['content'], '1급 기밀 본문 내용입니다.')

        # 3. 포럼 매니저 및 Superuser도 원본 본문 열람 가능
        self.client.force_authenticate(user=self.forum_manager)
        res_mgr = self.client.get(f'/api/v1/post/{self.secret_post.pk}/')
        self.assertEqual(res_mgr.status_code, status.HTTP_200_OK)
        self.assertEqual(res_mgr.data['content'], '1급 기밀 본문 내용입니다.')

    def test_blind_post_masking(self):
        """블라인드 처리된 게시글 마스킹 검증"""
        # 일반 멤버 조회 시 마스킹
        self.client.force_authenticate(user=self.member_user)
        res_blind = self.client.get(f'/api/v1/post/{self.blind_post.pk}/')
        self.assertEqual(res_blind.status_code, status.HTTP_200_OK)
        self.assertEqual(res_blind.data['content'], '블라인드 처리된 게시물입니다.')

        # 관리자 조회 시 원문 확인 가능
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get(f'/api/v1/post/{self.blind_post.pk}/')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(res_admin.data['content'], '유해 게시물 본문입니다.')

    def test_post_modify_delete_permission(self):
        """게시글 수정/삭제 시 작성자 및 관리자 통제 검증"""
        # 제3자 사용자가 타인의 글 수정 시도 시 403 차단
        another_member = User.objects.create_user(
            username='third_party', email='third@test.com', password='password123'
        )
        m = Member.objects.create(project=self.private_project, user=another_member)
        m.roles.add(self.role_member)

        self.client.force_authenticate(user=another_member)
        res_modify_denied = self.client.patch(
            f'/api/v1/post/{self.normal_post.pk}/', {'title': '해킹된 제목'}
        )
        self.assertEqual(res_modify_denied.status_code, status.HTTP_403_FORBIDDEN)

        # 작성자 본인은 정상 수정 가능 (200 OK)
        self.client.force_authenticate(user=self.member_user)
        res_modify_ok = self.client.patch(
            f'/api/v1/post/{self.normal_post.pk}/', {'title': '작성자가 수정한 제목'}
        )
        self.assertEqual(res_modify_ok.status_code, status.HTTP_200_OK)
        self.normal_post.refresh_from_db()
        self.assertEqual(self.normal_post.title, '작성자가 수정한 제목')
