from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from company.models import Company
from contract.models import Contract, Contractor, ContractorContact, ContractorAddress, OrderGroup
from items.models import UnitType
from notice.models import (
    SalesBillIssue, MessageSendHistory, RegisteredSenderNumber, MessageTemplate,
    EmailNotice, EmailSendLog
)
from payment.models import InstallmentPaymentOrder
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

        # UnitType 생성 (Project A)
        self.unit_type_a = UnitType.objects.create(
            project=self.project_a,
            sort='1',
            name='84A',
            color='#123456',
            actual_area=84.0,
            supply_area=110.0,
            contract_area=130.0,
            average_price=500000000,
            num_unit=100
        )

        # 계약 및 계약자 데이터 생성 (Project A)
        self.order_group_a = OrderGroup.objects.create(project=self.project_a, order_number=1, sort='1', name='1차')
        self.contract_a = Contract.objects.create(
            project=self.project_a,
            order_group=self.order_group_a,
            unit_type=self.unit_type_a,
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
            cell_phone='010-1234-5678',
            email='hong@test.com'
        )
        self.address_a = ContractorAddress.objects.create(
            contractor=self.contractor_a,
            id_zipcode='06100',
            id_address1='서울시 강남구 테헤란로 1',
            is_current=True
        )

        # InstallmentPaymentOrder 생성
        self.order_1 = InstallmentPaymentOrder.objects.create(
            project=self.project_a,
            pay_sort='1',
            pay_code=1,
            pay_time=1,
            pay_name='1차 계약금',
            pay_due_date='2026-06-30'
        )

        # SalesBillIssue 데이터 생성
        self.bill_a = SalesBillIssue.objects.create(
            project=self.project_a,
            now_payment_order=self.order_1,
            host_name='시행사A',
            host_tel='02-1111-2222',
            bank_account1='국민은행',
            bank_number1='123-456-789',
            bank_host1='시행사A',
            zipcode='06100',
            address1='서울시 강남구',
            title='수납 고지서',
            content='납부 바랍니다.',
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

    @patch('notice.utils.IwinvSMSService.send_kakao_alimtalk')
    def test_send_kakao_history_creation(self, mock_send_kakao):
        """카카오 알림톡 발송 성공 시 MessageSendHistory 기록 생성 검증"""
        mock_send_kakao.return_value = {
            'code': 200,
            'message': '메시지가 발송되었습니다.',
            'success': 1,
            'fail': 0
        }
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'project': self.project_a.pk,
            'company_id': 'TEST_COMP',
            'sender_number': '02-1234-5678',
            'template_code': 'TMPL-001',
            'recipients': [{'phone': '010-1234-5678', 'template_param': ['홍길동']}],
        }
        res = self.client.post('/api/v1/messages/send-kakao/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 발송 기록 확인
        history = MessageSendHistory.objects.filter(message_type='KAKAO', project=self.project_a).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.sender_number, '02-1234-5678')
        self.assertEqual(history.sent_by, self.user_a)
        self.assertEqual(history.recipient_count, 1)
        self.assertTrue('010-1234-5678' in history.recipients or '01012345678' in history.recipients)

    def test_registered_sender_and_template_soft_delete(self):
        """발신번호 및 메시지 템플릿 삭제 시 soft-delete(비활성화) 검증"""
        self.client.force_authenticate(user=self.user_a)
        sender = RegisteredSenderNumber.objects.create(phone_number='02-9999-8888', label='고객센터')
        tmpl = MessageTemplate.objects.create(
            title='테스트 템플릿', message_type='SMS', content='내용', created_by=self.user_a
        )

        # 발신번호 삭제(비활성화)
        res_del_sender = self.client.delete(f'/api/v1/registered-sender-numbers/{sender.pk}/')
        self.assertEqual(res_del_sender.status_code, status.HTTP_204_NO_CONTENT)
        sender.refresh_from_db()
        self.assertFalse(sender.is_active)

        # 메시지 템플릿 삭제(비활성화)
        res_del_tmpl = self.client.delete(f'/api/v1/message-templates/{tmpl.pk}/')
        self.assertEqual(res_del_tmpl.status_code, status.HTTP_204_NO_CONTENT)
        tmpl.refresh_from_db()
        self.assertFalse(tmpl.is_active)

    @patch('notice.tasks.send_mass_email_task.delay')
    def test_email_notice_api_and_scoping(self, mock_email_task):
        """이메일 공지 발송 통계, RLS 격리, custom_recipients 프로젝트 스코핑 검증"""
        # User A는 Project A 대상자 목록 조회 가능
        self.client.force_authenticate(user=self.user_a)
        res_rec = self.client.get(f'/api/v1/email-notices/recipients/?project={self.project_a.pk}')
        self.assertEqual(res_rec.status_code, status.HTTP_200_OK)
        self.assertEqual(res_rec.data['total_contractors'], 1)
        self.assertEqual(res_rec.data['registered_count'], 1)
        self.assertEqual(res_rec.data['recipients'][0]['email'], 'hong@test.com')

        # User B는 Project A 대상자 조회 403 차단
        self.client.force_authenticate(user=self.user_b)
        res_rec_b = self.client.get(f'/api/v1/email-notices/recipients/?project={self.project_a.pk}')
        self.assertEqual(res_rec_b.status_code, status.HTTP_403_FORBIDDEN)

        # 이메일 발송 생성 (User A)
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'project': self.project_a.pk,
            'title': '이메일 공지 테스트',
            'content': '<p>안녕하세요 {{계약자명}}님</p>',
            'custom_recipients': [
                {'contractor_id': self.contractor_a.pk, 'name': '홍길동', 'email': 'hong@test.com'},
                {'contractor_id': 999999, 'name': '외부인', 'email': 'out@test.com'}
            ]
        }
        res_send = self.client.post('/api/v1/email-notices/send-email/', payload, format='json')
        self.assertEqual(res_send.status_code, status.HTTP_201_CREATED)
        notice_id = res_send.data['notice_id']
        mock_email_task.assert_called_once_with(notice_id)

        # EmailNotice 및 EmailSendLog 검증
        notice = EmailNotice.objects.get(pk=notice_id)
        self.assertEqual(notice.project, self.project_a)
        self.assertEqual(notice.sent_by, self.user_a)
        logs = notice.send_logs.all()
        self.assertEqual(logs.count(), 2)

        # 외부 계약자 ID(999999)는 contractor FK에 매핑되지 않아야 함 (프로젝트 격리)
        out_log = logs.filter(recipient_email='out@test.com').first()
        self.assertIsNone(out_log.contractor)

        # list 조회 시 정상 응답 확인
        res_list = self.client.get('/api/v1/email-notices/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        # retrieve 조회 시 send_logs 포함 확인
        res_detail = self.client.get(f'/api/v1/email-notices/{notice_id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertIn('send_logs', res_detail.data)

    def test_post_label_viewset(self):
        """우편 라벨 주소 목록 조회 및 프로젝트 RLS 검증"""
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get(f'/api/v1/post-labels/?project={self.project_a.pk}')
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        labels_a = res_a.data.get('results', res_a.data)
        self.assertEqual(len(labels_a), 1)
        self.assertEqual(labels_a[0]['contractor_name'], '홍길동')
        self.assertEqual(labels_a[0]['effective_address1'], '서울시 강남구 테헤란로 1')

        # User B는 Project A 주소 접근 불가 (403 Forbidden)
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.get(f'/api/v1/post-labels/?project={self.project_a.pk}')
        self.assertEqual(res_b.status_code, status.HTTP_403_FORBIDDEN)

    def test_bill_manage_view_get_and_post(self):
        """BillManageView GET 렌더링(기납입액 계산) 및 POST 저장(creator 바인딩) 검증"""
        client = Client()
        client.force_login(self.admin_user)

        # GET 요청 검증
        url = reverse('ibs:notice:bill') + f'?project={self.project_a.pk}'
        res = client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('total_pay_by_contract', res.context)
        self.assertIn('today', res.context)
        self.assertEqual(res.context['bill_issue'], self.bill_a)

        # POST 요청 (수정 저장) 검증
        post_data = {
            'published_date': '2026-07-01',
            'now_payment_order': self.order_1.pk,
            'now_due_date': '2026-07-15',
            'host_name': '수정시행자',
            'host_tel': '02-7777-8888',
            'bank_account1': '신한은행',
            'bank_number1': '987-654-321',
            'bank_host1': '수정시행자',
            'zipcode': '05500',
            'address1': '서울시 송파구',
            'title': '수정된 고지서 제목',
            'content': '납부 기한 준수 요망',
        }
        res_post = client.post(url, post_data)
        self.assertEqual(res_post.status_code, 302)

        self.bill_a.refresh_from_db()
        self.assertEqual(self.bill_a.host_name, '수정시행자')
        self.assertEqual(self.bill_a.creator, self.admin_user)

    @patch('weasyprint.HTML.write_pdf')
    def test_pdf_export_bill(self, mock_write_pdf):
        """고지서 PDF 내보내기 뷰 응답 및 예외 처리 검증"""
        mock_write_pdf.return_value = b'%PDF-1.4 dummy pdf'

        # 정상 요청
        url_ok = reverse('pdf:bill') + f'?project={self.project_a.pk}&seq={self.contract_a.pk}'
        res_ok = self.client.get(url_ok)
        self.assertEqual(res_ok.status_code, 200)
        self.assertEqual(res_ok['Content-Type'], 'application/pdf')
        self.assertEqual(res_ok.content, b'%PDF-1.4 dummy pdf')

        # seq 미전달 시 400 Bad Request
        url_no_seq = reverse('pdf:bill') + f'?project={self.project_a.pk}'
        res_no_seq = self.client.get(url_no_seq)
        self.assertEqual(res_no_seq.status_code, 400)

        # SalesBillIssue 미존재 프로젝트 시 404 Not Found
        url_no_bill = reverse('pdf:bill') + f'?project=999999&seq={self.contract_a.pk}'
        res_no_bill = self.client.get(url_no_bill)
        self.assertEqual(res_no_bill.status_code, 404)
