from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from company.models import Company
from contract.models import Contract, Contractor, ContractorContact, OrderGroup
from notice.models import SalesBillIssue, MessageSendHistory
from project.models import Project
from work.models.project import IssueProject, Member, Role, Permission

User = get_user_model()


class NoticeAppSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 회사 및 사용자 생성
        self.company = Company.objects.create(name='테스트건설')
        self.admin_user = User.objects.create_superuser(
            username='admin_notice', email='admin@test.com', password='password123'
        )
        self.user_a = User.objects.create_user(
            username='user_proj_a', email='usera@test.com', password='password123'
        )
        self.user_b = User.objects.create_user(
            username='user_proj_b', email='userb@test.com', password='password123'
        )

        # 권한 및 역할 생성
        self.perm_read = Permission.objects.create(module='notice', code='notice.read', name='공지 읽기')
        self.perm_create = Permission.objects.create(module='notice', code='notice.create', name='공지 생성')
        self.role_staff = Role.objects.create(name='직원', creator=self.admin_user)
        self.role_staff.permissions.add(self.perm_read, self.perm_create)

        # 워크스페이스 및 프로젝트 A 생성
        self.issue_proj_a = IssueProject.objects.create(
            company=self.company, name='워크스페이스 A', slug='workspace-a', type='2', creator=self.admin_user
        )
        self.project_a = Project.objects.create(
            issue_project=self.issue_proj_a,
            name='프로젝트 A',
            kind='1',
            start_year=2026,
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24
        )
        member_a = Member.objects.create(project=self.issue_proj_a, user=self.user_a)
        member_a.roles.add(self.role_staff)

        # 워크스페이스 및 프로젝트 B 생성
        self.issue_proj_b = IssueProject.objects.create(
            company=self.company, name='워크스페이스 B', slug='workspace-b', type='2', creator=self.admin_user
        )
        self.project_b = Project.objects.create(
            issue_project=self.issue_proj_b,
            name='프로젝트 B',
            kind='1',
            start_year=2026,
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24
        )
        member_b = Member.objects.create(project=self.issue_proj_b, user=self.user_b)
        member_b.roles.add(self.role_staff)

        # 계약 및 계약자 데이터 생성 (Project A)
        self.order_group_a = OrderGroup.objects.create(project=self.project_a, order_number=1, sort='1', name='1차')
        self.contract_a = Contract.objects.create(
            project=self.project_a,
            order_group=self.order_group_a,
            serial_number='A-001',
            is_active=True,
            creator=self.admin_user
        )
        self.contractor_a = Contractor.objects.create(
            contract=self.contract_a,
            name='홍길동',
            is_active=True,
            creator=self.admin_user
        )
        self.contact_a = ContractorContact.objects.create(
            contractor=self.contractor_a,
            cell_phone='010-1234-5678'
        )

        # SalesBillIssue 데이터 생성
        self.bill_a = SalesBillIssue.objects.create(
            project=self.project_a,
            creator=self.admin_user
        )
        self.bill_b = SalesBillIssue.objects.create(
            project=self.project_b,
            creator=self.admin_user
        )

        now = timezone.now()
        # 발송 이력 데이터 생성
        self.history_a = MessageSendHistory.objects.create(
            project=self.project_a,
            sent_by=self.user_a,
            sent_at=now,
            sender_number='02-1234-5678',
            message_content='프로젝트 A 공지',
            recipients=['010-1234-5678'],
            recipient_count=1
        )
        self.history_b = MessageSendHistory.objects.create(
            project=self.project_b,
            sent_by=self.user_b,
            sent_at=now,
            sender_number='02-1234-5678',
            message_content='프로젝트 B 공지',
            recipients=['010-9876-5432'],
            recipient_count=1
        )
        self.history_user_b_unbound = MessageSendHistory.objects.create(
            project=None,
            sent_by=self.user_b,
            sent_at=now,
            sender_number='02-1234-5678',
            message_content='개별 발송 건',
            recipients=['010-0000-0000'],
            recipient_count=1
        )

    def test_bill_issue_unauthenticated_blocked(self):
        """미인증 사용자 BillIssue 접근 401 차단"""
        res = self.client.get('/api/v1/sales-bill-issue/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bill_issue_row_level_security(self):
        """프로젝트 멤버십 기반 BillIssue 조회 격리 검증"""
        # User A는 Project A의 BillIssue만 조회 가능
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get('/api/v1/sales-bill-issue/')
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        ids_a = [item.get('pk') or item.get('id') for item in res_a.data.get('results', res_a.data)]
        self.assertIn(self.bill_a.pk, ids_a)
        self.assertNotIn(self.bill_b.pk, ids_a)

        # Superuser는 전체 BillIssue 조회 가능
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get('/api/v1/sales-bill-issue/')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        ids_admin = [item.get('pk') or item.get('id') for item in res_admin.data.get('results', res_admin.data)]
        self.assertIn(self.bill_a.pk, ids_admin)
        self.assertIn(self.bill_b.pk, ids_admin)

    def test_recipient_groups_project_authorization(self):
        """수신자 그룹 연락처 조회 시 비인가 프로젝트 403 차단 검증"""
        # User B가 Project A 연락처 조회 시도 시 403 Forbidden
        self.client.force_authenticate(user=self.user_b)
        res_forbidden = self.client.get(f'/api/v1/messages/recipient-groups/?project={self.project_a.pk}&group_type=all')
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # User A는 Project A 연락처 정상 조회 (200 OK)
        self.client.force_authenticate(user=self.user_a)
        res_ok = self.client.get(f'/api/v1/messages/recipient-groups/?project={self.project_a.pk}&group_type=all')
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data['count'], 1)
        self.assertIn('010-1234-5678', res_ok.data['phone_numbers'])

    def test_send_message_unauthorized_project_blocked(self):
        """타 프로젝트로 메시지 발송 시도 시 403 차단 검증"""
        self.client.force_authenticate(user=self.user_b)
        payload = {
            'project': self.project_a.pk,
            'sender_number': '02-1234-5678',
            'message': '비인가 발송 시도',
            'recipients': ['010-1234-5678']
        }
        res_sms = self.client.post('/api/v1/messages/send-sms/', payload, format='json')
        self.assertEqual(res_sms.status_code, status.HTTP_403_FORBIDDEN)

        res_kakao = self.client.post('/api/v1/messages/send-kakao/', payload, format='json')
        self.assertEqual(res_kakao.status_code, status.HTTP_403_FORBIDDEN)

    def test_message_send_history_isolation(self):
        """메시지 발송 기록 프로젝트 및 작성자 격리 검증"""
        # User A는 Project A의 발송 기록만 조회
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get('/api/v1/message-send-history/')
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        history_ids_a = [item.get('pk') or item.get('id') for item in res_a.data.get('results', res_a.data)]
        self.assertIn(self.history_a.pk, history_ids_a)
        self.assertNotIn(self.history_b.pk, history_ids_a)
        self.assertNotIn(self.history_user_b_unbound.pk, history_ids_a)

        # User B는 Project B 발송 기록과 본인이 보낸 개별 발송 건 조회
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.get('/api/v1/message-send-history/')
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)
        history_ids_b = [item.get('pk') or item.get('id') for item in res_b.data.get('results', res_b.data)]
        self.assertNotIn(self.history_a.pk, history_ids_b)
        self.assertIn(self.history_b.pk, history_ids_b)
        self.assertIn(self.history_user_b_unbound.pk, history_ids_b)

        # Superuser는 모든 발송 기록 조회
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get('/api/v1/message-send-history/')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        history_ids_admin = [item.get('pk') or item.get('id') for item in res_admin.data.get('results', res_admin.data)]
        self.assertIn(self.history_a.pk, history_ids_admin)
        self.assertIn(self.history_b.pk, history_ids_admin)
        self.assertIn(self.history_user_b_unbound.pk, history_ids_admin)
