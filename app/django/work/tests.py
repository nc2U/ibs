from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from company.models import Company
from work.models.issue import Issue, Tracker, IssueStatus, CodeIssuePriority
from work.models.project import IssueProject, Role, Member
from work.services.work_services import IssueService

User = get_user_model()


class WorkAppTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.company = Company.objects.create(name='Test Company')

        self.project = IssueProject.objects.create(
            company=self.company,
            name='Test Project',
            slug='test-project',
            creator=self.user
        )

        self.status_open = IssueStatus.objects.create(name='Open', creator=self.user)
        self.status_closed = IssueStatus.objects.create(name='Closed', closed=True, creator=self.user)

        self.tracker = Tracker.objects.create(name='Bug', default_status=self.status_open, creator=self.user)
        self.priority = CodeIssuePriority.objects.create(name='Normal', creator=self.user)

    def test_issue_project_creation(self):
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(IssueProject.objects.count(), 1)

    def test_issue_creation_and_tracking(self):
        issue = Issue.objects.create(
            project=self.project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='Test Issue',
            start_date=timezone.now().date(),
            creator=self.user
        )
        self.assertEqual(issue.subject, 'Test Issue')
        self.assertEqual(Issue.objects.count(), 1)

    def test_issue_service_track_changes(self):
        issue = Issue.objects.create(
            project=self.project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='Original Subject',
            start_date=timezone.now().date(),
            creator=self.user
        )

        issue.subject = 'New Subject'
        IssueService.track_changes(issue)

        self.assertTrue(hasattr(issue, 'old_subject'))
        self.assertEqual(issue.old_subject, 'Original Subject')

    def test_project_all_members_optimization(self):
        role = Role.objects.create(name='Manager', creator=self.user)
        Member.objects.create(user=self.user, project=self.project)
        self.project.members.first().roles.add(role)

        members = self.project.all_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]['user']['username'], 'testuser')
        self.assertEqual(len(members[0]['roles']), 1)
        self.assertEqual(members[0]['roles'][0]['name'], 'Manager')

    def test_project_member_inheritance(self):
        parent_project = IssueProject.objects.create(
            company=self.company,
            name='Parent Project',
            slug='parent-project',
            creator=self.user
        )
        child_project = IssueProject.objects.create(
            company=self.company,
            name='Child Project',
            slug='child-project',
            parent=parent_project,
            is_inherit_members=True,
            creator=self.user
        )

        role = Role.objects.create(name='Manager', creator=self.user)
        Member.objects.create(user=self.user, project=parent_project)
        parent_project.members.first().roles.add(role)

        members = child_project.all_members()
        self.assertEqual(len(members), 1)
        self.assertTrue(members[0]['roles'][0]['inherited'])


from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from work.models.meeting import Meeting, MeetingCategory
from work.models.project import Permission
from work.models.logging import ActivityLogEntry, IssueLogEntry


class WorkMeetingAndSecurityAPITests(APITestCase):
    """
    회의(Meeting) 및 업무(Issue) 백엔드 보안 & 데이터 무결성 통합 테스트:
    1. 회의-업무 연동: 회의 생성, 회의에 연결된 업무 목록 및 완료 상태(closed) 반영 검증
    2. 비공개 워크스페이스 격리 (Row-Level Security): 비멤버에게 비공개 프로젝트 회의/업무 노출 차단 (403/404) 및 슈퍼유저 열람 검증
    3. 회의 확정 생애주기 제약: 준비('1') 상태 확정 시도 시 400 차단, 종료('2') 상태 확정 성공 및 일반 멤버의 확정 회의 수정 403 차단
    4. 회의 외부 참석자(other_attendees) 및 회의 장소(location) API 입출력 무결성 검증
    5. 활동 및 변경 이력 추적: 회의/업무 등록 시 ActivityLogEntry 생성 및 업무 필드 변경 시 IssueLogEntry 기록 검증
    """

    def setUp(self):
        # 1. 메일 발송 태스크 모킹 (테스트 격리)
        self.patcher_meeting_mail = patch('work.services.work_services.MeetingService.send_meeting_mail')
        self.patcher_issue_mail = patch('work.services.work_services.IssueService.send_issue_mail')
        self.mock_meeting_mail = self.patcher_meeting_mail.start()
        self.mock_issue_mail = self.patcher_issue_mail.start()

        # 2. 사용자 계정 생성
        self.admin_user = User.objects.create_superuser(
            username='work_admin', email='admin@example.com', password='password123'
        )
        self.manager_user = User.objects.create_user(
            username='project_manager', email='manager@example.com', password='password123'
        )
        self.staff_user = User.objects.create_user(
            username='project_staff', email='staff@example.com', password='password123'
        )
        self.outsider_user = User.objects.create_user(
            username='outsider', email='outsider@example.com', password='password123'
        )

        # 3. 회사 및 워크스페이스 생성
        self.company = Company.objects.create(name='(주)대영아이비에스')

        self.public_project = IssueProject.objects.create(
            company=self.company,
            name='공개 워크스페이스',
            slug='public-ws',
            is_public=True,
            creator=self.admin_user
        )
        self.private_project = IssueProject.objects.create(
            company=self.company,
            name='비공개 워크스페이스',
            slug='private-ws',
            is_public=False,
            creator=self.admin_user
        )

        # 4. 업무 상태, 유형, 우선순위
        self.status_open = IssueStatus.objects.create(name='진행', creator=self.admin_user)
        self.status_closed = IssueStatus.objects.create(name='완료', closed=True, creator=self.admin_user)
        self.tracker = Tracker.objects.create(name='업무', default_status=self.status_open, creator=self.admin_user)
        self.priority = CodeIssuePriority.objects.create(name='보통', creator=self.admin_user)

        # 5. 권한 생성
        self.perm_meeting_read, _ = Permission.objects.get_or_create(
            code='meeting.read', defaults={'name': '회의 조회', 'module': 'meeting'}
        )
        self.perm_meeting_create, _ = Permission.objects.get_or_create(
            code='meeting.create', defaults={'name': '회의 등록', 'module': 'meeting'}
        )
        self.perm_meeting_update, _ = Permission.objects.get_or_create(
            code='meeting.update', defaults={'name': '회의 수정', 'module': 'meeting'}
        )
        self.perm_meeting_delete, _ = Permission.objects.get_or_create(
            code='meeting.delete', defaults={'name': '회의 삭제', 'module': 'meeting'}
        )
        self.perm_meeting_confirm, _ = Permission.objects.get_or_create(
            code='meeting.confirm', defaults={'name': '회의 확정', 'module': 'meeting'}
        )
        self.perm_meeting_edit_conf, _ = Permission.objects.get_or_create(
            code='meeting.edit_confirmed', defaults={'name': '확정 회의 수정', 'module': 'meeting'}
        )

        self.perm_issue_read, _ = Permission.objects.get_or_create(
            code='issue.read', defaults={'name': '업무 조회', 'module': 'issue'}
        )
        self.perm_issue_create, _ = Permission.objects.get_or_create(
            code='issue.create', defaults={'name': '업무 등록', 'module': 'issue'}
        )
        self.perm_issue_update, _ = Permission.objects.get_or_create(
            code='issue.update', defaults={'name': '업무 수정', 'module': 'issue'}
        )

        # 6. 역할 및 권한 매핑
        self.role_manager = Role.objects.create(name='관리자 역할', creator=self.admin_user, issue_visible='ALL')
        self.role_manager.permissions.set([
            self.perm_meeting_read, self.perm_meeting_create, self.perm_meeting_update,
            self.perm_meeting_delete, self.perm_meeting_confirm, self.perm_meeting_edit_conf,
            self.perm_issue_read, self.perm_issue_create, self.perm_issue_update
        ])

        self.role_staff = Role.objects.create(name='팀원 역할', creator=self.admin_user, issue_visible='PUB')
        self.role_staff.permissions.set([
            self.perm_meeting_read, self.perm_meeting_create, self.perm_meeting_update,
            self.perm_issue_read, self.perm_issue_create, self.perm_issue_update
        ])

        Role.objects.get_or_create(pk=2, defaults={'name': '비회원', 'creator': self.admin_user, 'issue_visible': 'PUB'})

        # 7. 비공개 워크스페이스에 매니저 및 사원 등록
        m_manager = Member.objects.create(user=self.manager_user, project=self.private_project)
        m_manager.roles.add(self.role_manager)

        m_staff = Member.objects.create(user=self.staff_user, project=self.private_project)
        m_staff.roles.add(self.role_staff)

    def tearDown(self):
        self.patcher_meeting_mail.stop()
        self.patcher_issue_mail.stop()

    def test_meeting_issues_linkage_and_status(self):
        """1. 회의 생성 후 Issue.meeting 연결 및 회의 상세 API에서 issues 리스트와 완료 상태가 올바르게 반환되는지 검증"""
        # 회의 생성
        meeting = Meeting.objects.create(
            project=self.private_project,
            title='2026년도 상반기 사업계획 회의',
            agenda='1. 예산 배정\n2. 인력 운영안',
            action_items='1. 예산서 초안 작성 (담당: 사원)\n2. 운영안 승인 요청 (담당: 매니저)',
            status='1',
            creator=self.manager_user
        )

        # 회의와 연계된 업무(Issue) 2건 생성
        issue1 = Issue.objects.create(
            project=self.private_project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='1. 예산서 초안 작성',
            meeting=meeting,
            start_date=timezone.now().date(),
            assigned_to=self.staff_user,
            creator=self.manager_user
        )
        issue2 = Issue.objects.create(
            project=self.private_project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='2. 운영안 승인 요청',
            meeting=meeting,
            start_date=timezone.now().date(),
            assigned_to=self.manager_user,
            creator=self.manager_user
        )

        # 사원 계정으로 회의 상세 조회 API 호출
        self.client.force_authenticate(user=self.staff_user)
        url = f'/api/v1/meeting/{meeting.pk}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        issues_data = response.data.get('issues', [])
        self.assertEqual(len(issues_data), 2)

        subjects = [item['subject'] for item in issues_data]
        self.assertIn('1. 예산서 초안 작성', subjects)
        self.assertIn('2. 운영안 승인 요청', subjects)

        # 첫 번째 업무의 초기 상태는 진행(closed is None)
        target_issue_data = next(item for item in issues_data if item['pk'] == issue1.pk)
        self.assertEqual(target_issue_data['status'], '진행')
        self.assertIsNone(target_issue_data['closed'])

        # 업무 1을 완료로 변경 처리
        issue1.status = self.status_closed
        issue1.closed = timezone.now()
        issue1.save()

        # 회의 상세 재조회 시 완료 상태가 즉시 반영되는지 검증
        response_after = self.client.get(url)
        self.assertEqual(response_after.status_code, status.HTTP_200_OK)
        issues_after = response_after.data.get('issues', [])
        updated_issue_data = next(item for item in issues_after if item['pk'] == issue1.pk)
        self.assertEqual(updated_issue_data['status'], '완료')
        self.assertIsNotNone(updated_issue_data['closed'])

    def test_private_workspace_security_isolation(self):
        """2. 비공개 워크스페이스의 회의/업무가 비멤버에게 완벽히 은닉(403/404)되고 슈퍼유저에게만 허용되는지 Row-Level Security 검증"""
        # 비공개 워크스페이스의 회의 및 이슈
        private_meeting = Meeting.objects.create(
            project=self.private_project,
            title='기밀 경영전략 회의',
            agenda='대외비 안건',
            creator=self.manager_user
        )
        private_issue = Issue.objects.create(
            project=self.private_project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='기밀 전략 수립',
            start_date=timezone.now().date(),
            creator=self.manager_user
        )

        # 공개 워크스페이스의 회의 및 이슈
        public_meeting = Meeting.objects.create(
            project=self.public_project,
            title='전사 공지 회의',
            agenda='공개 안건',
            creator=self.admin_user
        )
        public_issue = Issue.objects.create(
            project=self.public_project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='공개 업무 진행',
            start_date=timezone.now().date(),
            creator=self.admin_user
        )

        # [A] 비멤버 일반 사원(outsider_user)의 조회 시도
        self.client.force_authenticate(user=self.outsider_user)

        # 1) 회의 목록 조회: 비공개 회의는 목록에서 격리되어 보이지 않아야 함
        res_meetings = self.client.get('/api/v1/meeting/')
        self.assertEqual(res_meetings.status_code, status.HTTP_200_OK)
        meeting_results = res_meetings.data.get('results', res_meetings.data)
        meeting_pks = [m['pk'] for m in meeting_results]
        self.assertNotIn(private_meeting.pk, meeting_pks)
        self.assertIn(public_meeting.pk, meeting_pks)

        # 2) 비공개 회의 단건 조회: 404 (존재 자체 은닉)
        res_private_meeting = self.client.get(f'/api/v1/meeting/{private_meeting.pk}/')
        self.assertIn(res_private_meeting.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

        # 3) 비공개 워크스페이스에 회의 무단 생성 시도: 403 Forbidden
        res_create_meeting = self.client.post('/api/v1/meeting/', {
            'project': self.private_project.pk,
            'title': '비인가 회의 생성 시도',
            'agenda': '침입'
        })
        self.assertEqual(res_create_meeting.status_code, status.HTTP_403_FORBIDDEN)

        # 4) 업무 목록 조회: 비공개 업무는 목록에서 격리
        res_issues = self.client.get('/api/v1/issue/')
        self.assertEqual(res_issues.status_code, status.HTTP_200_OK)
        issue_results = res_issues.data.get('results', res_issues.data)
        issue_pks = [i['pk'] for i in issue_results]
        self.assertNotIn(private_issue.pk, issue_pks)
        self.assertIn(public_issue.pk, issue_pks)

        # 5) 비공개 업무 단건 조회: 404
        res_private_issue = self.client.get(f'/api/v1/issue/{private_issue.pk}/')
        self.assertIn(res_private_issue.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

        # [B] 슈퍼유저(admin_user)의 조회: 모든 회의/업무에 접근 가능해야 함
        self.client.force_authenticate(user=self.admin_user)

        res_admin_meeting = self.client.get(f'/api/v1/meeting/{private_meeting.pk}/')
        self.assertEqual(res_admin_meeting.status_code, status.HTTP_200_OK)
        self.assertEqual(res_admin_meeting.data['title'], '기밀 경영전략 회의')

        res_admin_issue = self.client.get(f'/api/v1/issue/{private_issue.pk}/')
        self.assertEqual(res_admin_issue.status_code, status.HTTP_200_OK)
        self.assertEqual(res_admin_issue.data['subject'], '기밀 전략 수립')

    def test_meeting_confirm_lifecycle_restrictions(self):
        """3. 회의 확정 생애주기: 준비('1') 상태 확정 불가(400), 종료('2') 상태 확정 성공 및 일반 멤버의 확정 회의 수정 차단(403)"""
        meeting = Meeting.objects.create(
            project=self.private_project,
            title='주간 공정 회의',
            status='1',  # 준비 상태
            creator=self.manager_user
        )

        # 1) 확정 권한이 없는 일반 사원(staff_user)이 confirm 시도: 403 차단
        self.client.force_authenticate(user=self.staff_user)
        res_unauthorized = self.client.post(f'/api/v1/meeting/{meeting.pk}/confirm/')
        self.assertEqual(res_unauthorized.status_code, status.HTTP_403_FORBIDDEN)

        # 2) 매니저(manager_user)가 준비('1') 상태에서 확정 시도: 400 Bad Request
        self.client.force_authenticate(user=self.manager_user)
        res_invalid_status = self.client.post(f'/api/v1/meeting/{meeting.pk}/confirm/')
        self.assertEqual(res_invalid_status.status_code, status.HTTP_400_BAD_REQUEST)
        meeting.refresh_from_db()
        self.assertFalse(meeting.is_confirmed)

        # 3) 회의 상태를 종료('2')로 변경 후 확정 시도: 성공 (200 OK)
        meeting.status = '2'
        meeting.save()

        res_confirm = self.client.post(f'/api/v1/meeting/{meeting.pk}/confirm/')
        self.assertEqual(res_confirm.status_code, status.HTTP_200_OK)
        self.assertTrue(res_confirm.data['is_confirmed'])

        meeting.refresh_from_db()
        self.assertTrue(meeting.is_confirmed)

        # 4) 확정된 회의를 'meeting.edit_confirmed' 권한이 없는 일반 사원이 수정 시도: 403 Forbidden
        self.client.force_authenticate(user=self.staff_user)
        res_edit_confirmed = self.client.patch(f'/api/v1/meeting/{meeting.pk}/', {
            'title': '확정된 회의 무단 수정 시도'
        })
        self.assertEqual(res_edit_confirmed.status_code, status.HTTP_403_FORBIDDEN)

        # 5) 'meeting.edit_confirmed' 권한을 가진 매니저는 수정 가능: 200 OK
        self.client.force_authenticate(user=self.manager_user)
        res_edit_manager = self.client.patch(f'/api/v1/meeting/{meeting.pk}/', {
            'title': '주간 공정 회의 (최종 검토 완료)'
        })
        self.assertEqual(res_edit_manager.status_code, status.HTTP_200_OK)
        meeting.refresh_from_db()
        self.assertEqual(meeting.title, '주간 공정 회의 (최종 검토 완료)')

        # 6) confirm 엔드포인트 재호출 시 토글(확정 해제) 동작 검증
        res_unconfirm = self.client.post(f'/api/v1/meeting/{meeting.pk}/confirm/')
        self.assertEqual(res_unconfirm.status_code, status.HTTP_200_OK)
        self.assertFalse(res_unconfirm.data['is_confirmed'])
        meeting.refresh_from_db()
        self.assertFalse(meeting.is_confirmed)

    def test_meeting_external_attendees_and_location(self):
        """4. 외부 참석자(other_attendees) 및 회의 장소(location) API 입출력 무결성 검증"""
        self.client.force_authenticate(user=self.manager_user)

        payload = {
            'project': self.private_project.pk,
            'title': '시공사/감리단 합동 대책회의',
            'location': '현장 상황실 2층 대회의실 & Zoom 화상 회의',
            'other_attendees': '홍길동 수석감리원 (○○엔지니어링), 이순신 현장소장 (△△건설)',
            'agenda': '기초 파일 항타 공법 변경 심의',
            'status': '1',
        }

        # 회의 생성 API
        res_create = self.client.post('/api/v1/meeting/', payload)
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        created_pk = res_create.data['pk']

        # 응답 데이터 검증
        self.assertEqual(res_create.data['location'], payload['location'])
        self.assertEqual(res_create.data['other_attendees'], payload['other_attendees'])

        # DB 인스턴스 검증
        meeting = Meeting.objects.get(pk=created_pk)
        self.assertEqual(meeting.location, payload['location'])
        self.assertEqual(meeting.other_attendees, payload['other_attendees'])

        # 단건 조회 API 검증
        res_get = self.client.get(f'/api/v1/meeting/{created_pk}/')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data['location'], payload['location'])
        self.assertEqual(res_get.data['other_attendees'], payload['other_attendees'])

    def test_issue_and_meeting_activity_logging(self):
        """5. 회의 및 업무 등록 시 ActivityLogEntry 생성 및 업무 수정 시 IssueLogEntry diff 기록 검증"""
        # 1) 회의 생성 시 활동 로그(sort='3') 자동 생성 확인
        meeting = Meeting.objects.create(
            project=self.private_project,
            title='품질 안전 점검 회의',
            agenda='주간 안전 점검 결과 보고',
            creator=self.manager_user
        )
        meeting_activity = ActivityLogEntry.objects.filter(sort='3', target_id=meeting.pk).first()
        self.assertIsNotNone(meeting_activity)
        self.assertIn('품질 안전 점검 회의', meeting_activity.title)
        self.assertEqual(meeting_activity.creator, self.manager_user)

        # 2) 업무 생성 시 활동 로그(sort='1') 자동 생성 확인
        issue = Issue.objects.create(
            project=self.private_project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='비계 설치 구간 안전망 보강',
            start_date=timezone.now().date(),
            creator=self.staff_user
        )
        issue_activity = ActivityLogEntry.objects.filter(sort='1', target_id=issue.pk).first()
        self.assertIsNotNone(issue_activity)
        self.assertIn('비계 설치 구간 안전망 보강', issue_activity.title)
        self.assertEqual(issue_activity.creator, self.staff_user)

        # 3) 업무 수정 시 IssueService 변경 추적 및 IssueLogEntry 생성 검증
        issue.subject = '비계 설치 구간 안전망 보강 (완료 보고)'
        issue.done_ratio = 100
        IssueService.track_changes(issue)
        issue.save()

        # signals post_save에서 IssueService.log_and_notify 호출됨
        IssueService.log_and_notify(issue, False, self.staff_user)

        issue_log = IssueLogEntry.objects.filter(issue=issue).first()
        self.assertIsNotNone(issue_log)
        self.assertEqual(issue_log.action, 'Updated')
        self.assertIn('비계 설치 구간 안전망 보강 (완료 보고)', issue_log.details)

