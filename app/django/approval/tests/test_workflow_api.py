import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Profile
from approval.models import (
    DocCategory,
    DocumentType,
    ApprovalDocument,
    ApprovalStep,
    ApprovalAction,
    ApprovalDelegation,
    ApprovalAttachment,
)
from company.models import Company, Department, Staff, StaffAssignment, DutyTitle, Position

User = get_user_model()


class ApprovalWorkflowAPITestCase(APITestCase):
    """
    전자결재 시스템 백엔드 통합 API 테스트 케이스:
    - 기안 / 임시저장
    - 상신(Submit) 및 결재선 동적 생성
    - 권한 제어 (비인가자/순번 외 결재자 403/404 차단)
    - 단계별 승인 및 최종 승인 (자동 채번 검증)
    - 반려(Reject) 및 사유 기록
    - 기안 회수(Cancel) 허용 및 차단 조건
    - 대결(Delegation) 처리 검증
    - 보안등급(Security Level)별 열람 제어
    """

    def setUp(self):
        # 1. 회사 및 직급/직책 생성
        self.company = Company.objects.create(
            name='(주)대영아이비에스',
            tax_number='123-45-67890',
            ceo='홍대표',
            org_number='123456-1234567',
            is_default=True,
        )
        self.pos_staff = Position.objects.create(company=self.company, name='사원')
        self.pos_leader = Position.objects.create(company=self.company, name='팀장')
        self.pos_ceo = Position.objects.create(company=self.company, name='대표이사')

        self.duty_team_leader = DutyTitle.objects.create(company=self.company, name='팀장', code='TL')
        self.duty_ceo = DutyTitle.objects.create(company=self.company, name='대표이사', code='CEO')

        # 2. 부서 생성
        self.dept_dev = Department.objects.create(company=self.company, name='개발팀', level=1)
        self.dept_hr = Department.objects.create(company=self.company, name='인사팀', level=1)

        # 3. 사용자 및 직원/보직 설정
        # 1) 기안자 (개발팀 사원)
        self.user_drafter = User.objects.create_user(username='drafter', email='drafter@example.com', password='password123')
        Profile.objects.create(user=self.user_drafter, name='김기안')
        self.staff_drafter = Staff.objects.create(
            company=self.company, user=self.user_drafter, name='김기안',
            position=self.pos_staff, id_number='900101-1234567', personal_phone='010-1111-2222',
            date_join='2025-01-01', status='1'
        )
        self.assign_drafter = StaffAssignment.objects.create(
            staff=self.staff_drafter, company=self.company, department=self.dept_dev,
            is_primary=True
        )

        # 2) 1차 결재자 (개발팀 팀장)
        self.user_leader = User.objects.create_user(username='leader', email='leader@example.com', password='password123')
        Profile.objects.create(user=self.user_leader, name='박팀장')
        self.staff_leader = Staff.objects.create(
            company=self.company, user=self.user_leader, name='박팀장',
            position=self.pos_leader, id_number='850101-1234567', personal_phone='010-2222-3333',
            date_join='2023-01-01', status='1'
        )
        self.dept_dev.manager = self.staff_leader
        self.dept_dev.save()
        self.assign_leader = StaffAssignment.objects.create(
            staff=self.staff_leader, company=self.company, department=self.dept_dev,
            duty=self.duty_team_leader, is_primary=True
        )

        # 3) 최종 결재자 (대표이사)
        self.user_ceo = User.objects.create_user(username='ceo', email='ceo@example.com', password='password123')
        Profile.objects.create(user=self.user_ceo, name='홍대표')
        self.staff_ceo = Staff.objects.create(
            company=self.company, user=self.user_ceo, name='홍대표',
            position=self.pos_ceo, id_number='750101-1234567', personal_phone='010-3333-4444',
            date_join='2020-01-01', status='1'
        )
        self.assign_ceo = StaffAssignment.objects.create(
            staff=self.staff_ceo, company=self.company, department=self.dept_dev,
            duty=self.duty_ceo, is_primary=True
        )

        # 4) 대결자 (부재중인 박팀장 대신 결재할 대결자)
        self.user_delegate = User.objects.create_user(username='delegate', email='delegate@example.com', password='password123')
        Profile.objects.create(user=self.user_delegate, name='최대결')
        self.staff_delegate = Staff.objects.create(
            company=self.company, user=self.user_delegate, name='최대결',
            position=self.pos_leader, id_number='880101-1234567', personal_phone='010-4444-5555',
            date_join='2024-01-01', status='1'
        )
        self.assign_delegate = StaffAssignment.objects.create(
            staff=self.staff_delegate, company=self.company, department=self.dept_dev,
            is_primary=True
        )

        # 5) 타 부서 비인가자 (인사팀 사원)
        self.user_outsider = User.objects.create_user(username='outsider', email='outsider@example.com', password='password123')
        Profile.objects.create(user=self.user_outsider, name='이타부서')
        self.staff_outsider = Staff.objects.create(
            company=self.company, user=self.user_outsider, name='이타부서',
            position=self.pos_staff, id_number='950101-2234567', personal_phone='010-5555-6666',
            date_join='2025-06-01', status='1'
        )
        self.assign_outsider = StaffAssignment.objects.create(
            staff=self.staff_outsider, company=self.company, department=self.dept_hr,
            is_primary=True
        )

        # 4. 문서 유형 설정
        self.category = DocCategory.objects.create(name='일반품의', code='COMMON')
        self.doc_type = DocumentType.objects.create(
            category=self.category,
            name='업무품의서',
            code='BIZ',
            route_type=DocumentType.ROUTE_ORGANIZATION,
            default_security_level=ApprovalDocument.SECURITY_DEPT,
        )

    # ─────────────────────────────────────────────────────────────
    # 1. 기안 작성 및 임시저장 테스트
    # ─────────────────────────────────────────────────────────────
    def test_create_draft_document(self):
        """기안자가 임시저장 상태로 문서를 생성할 수 있는지 검증"""
        self.client.force_authenticate(user=self.user_drafter)
        payload = {
            'doc_type': self.doc_type.id,
            'title': '2026 상반기 서버 증설의 건',
            'content': {'amount': 5000000, 'purpose': '트래픽 증가 대비'},
            'drafter_assignment': self.assign_drafter.id,
            'security_level': ApprovalDocument.SECURITY_DEPT,
        }
        response = self.client.post('/api/v1/approval-document/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], ApprovalDocument.STATUS_DRAFT)
        self.assertIsNone(response.data['doc_number'])  # 임시저장 상태에서는 문서번호 미채번

    def test_update_and_destroy_restricted_to_drafter_and_draft_status(self):
        """[T-4 / C-2] 결재 문서는 기안자 본인이면서 DRAFT 또는 REJECTED 상태일 때만 수정/삭제 가능하며, 타인 또는 PENDING 상태에서는 403 차단 검증"""
        # 1. 기안자의 임시저장 문서 생성
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='임시저장 문서',
            content={'amount': 1000000},
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_DRAFT,
        )

        # 2. 타인(user_outsider)이 임시저장 문서 수정/삭제 시도 -> 403 Forbidden 또는 404 Not Found (RLS 차단)
        self.client.force_authenticate(user=self.user_outsider)
        res_patch_other = self.client.patch(f'/api/v1/approval-document/{doc.id}/', {'title': '타인 수정 시도'}, format='json')
        self.assertIn(res_patch_other.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        res_del_other = self.client.delete(f'/api/v1/approval-document/{doc.id}/')
        self.assertIn(res_del_other.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])


        # 3. 문서가 결재 진행 중(STATUS_PENDING)으로 변경된 경우 기안자 본인이어도 수정/삭제 시도 -> 400 Bad Request
        doc.status = ApprovalDocument.STATUS_PENDING
        doc.save()

        self.client.force_authenticate(user=self.user_drafter)
        res_patch_pending = self.client.patch(f'/api/v1/approval-document/{doc.id}/', {'title': '진행중 수정 시도'}, format='json')
        self.assertEqual(res_patch_pending.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('임시저장 또는 반려 상태의 문서만', str(res_patch_pending.data))

        res_del_pending = self.client.delete(f'/api/v1/approval-document/{doc.id}/')
        self.assertEqual(res_del_pending.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('임시저장 또는 반려 상태의 문서만', str(res_del_pending.data))


        # 4. 반려(STATUS_REJECTED) 상태로 변경 시 기안자 본인의 수정 허용 (200 OK)
        doc.status = ApprovalDocument.STATUS_REJECTED
        doc.save()

        res_patch_rejected = self.client.patch(f'/api/v1/approval-document/{doc.id}/', {'title': '반려 후 재작성 제목'}, format='json')
        self.assertEqual(res_patch_rejected.status_code, status.HTTP_200_OK)
        doc.refresh_from_db()
        self.assertEqual(doc.title, '반려 후 재작성 제목')


    def test_create_draft_document_with_file_multipart(self):
        """파일 첨부와 함께 multipart/form-data로 기안 시 content JSON이 유실 없이 dict로 보존되고 첨부파일이 등록되는지 검증"""
        self.client.force_authenticate(user=self.user_drafter)
        mock_file = SimpleUploadedFile(
            'test_spec.pdf',
            b'%PDF-1.4 mock content for test',
            content_type='application/pdf'
        )
        content_dict = {
            'amount': 2500000,
            'purpose': '개발용 장비 구매',
            'items': [{'name': '모니터', 'qty': 2, 'price': 1250000}],
        }
        payload = {
            'doc_type': self.doc_type.id,
            'title': '개발 장비 구매 신청',
            'content': json.dumps(content_dict),
            'drafter_assignment': self.assign_drafter.id,
            'security_level': ApprovalDocument.SECURITY_DEPT,
            'files': [mock_file],
        }
        response = self.client.post('/api/v1/approval-document/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        doc_id = response.data['id']
        doc = ApprovalDocument.objects.get(id=doc_id)

        # 🌟 핵심 검증 1: multipart 요청임에도 content JSON이 dict 구조로 완벽히 보존되었는지 검증
        self.assertIsInstance(doc.content, dict)
        self.assertEqual(doc.content.get('amount'), 2500000)
        self.assertEqual(doc.content.get('purpose'), '개발용 장비 구매')
        self.assertEqual(len(doc.content.get('items', [])), 1)

        # 🌟 핵심 검증 2: ApprovalAttachment 레코드가 문서에 정상 생성 및 링크되었는지 검증
        self.assertEqual(doc.attachments.count(), 1)
        attachment = doc.attachments.first()
        self.assertEqual(attachment.creator, self.user_drafter)
        self.assertEqual(attachment.file_name, 'test_spec.pdf')

    # ─────────────────────────────────────────────────────────────
    # 2. 상신 및 결재 단계 생성 테스트
    # ─────────────────────────────────────────────────────────────
    @patch('approval.tasks.notify_approvers_task.delay')
    def test_submit_document_generates_approval_steps(self, mock_notify):
        """임시저장 문서를 상신하면 조직도 기반으로 결재선이 자동 구성되는지 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='테스트 상신 문서',
            content={'amount': 1000000},
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_DRAFT,
        )

        self.client.force_authenticate(user=self.user_drafter)
        response = self.client.post(f'/api/v1/approval-document/{doc.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        doc.refresh_from_db()
        self.assertEqual(doc.status, ApprovalDocument.STATUS_PENDING)
        self.assertEqual(doc.current_step, 1)
        self.assertTrue(bool(doc.content_hash))  # 해시 생성 검증
        self.assertGreaterEqual(doc.steps.count(), 1)
        self.assertTrue(mock_notify.called)

    @patch('approval.tasks.generate_approval_pdf_task.delay')
    def test_submit_document_by_ceo_auto_approves_instantly(self, mock_pdf):
        """대표이사 본인이 기안 및 상신 시 즉시 최종 승인(STATUS_APPROVED) 및 채번 완료되는지 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='대표이사 직접 기안 문서',
            content={'purpose': '전사 경영 방침 지시'},
            drafter=self.user_ceo,
            drafter_assignment=self.assign_ceo,
            status=ApprovalDocument.STATUS_DRAFT,
        )

        self.client.force_authenticate(user=self.user_ceo)
        response = self.client.post(f'/api/v1/approval-document/{doc.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        doc.refresh_from_db()
        self.assertEqual(doc.status, ApprovalDocument.STATUS_APPROVED)
        self.assertIsNotNone(doc.doc_number)  # 즉시 정식 문서번호 채번 완료
        self.assertEqual(doc.steps.count(), 1)  # 승인된 1단계 기록 생성
        self.assertEqual(doc.steps.first().status, ApprovalStep.STATUS_APPROVED)
        self.assertEqual(doc.steps.first().role_label, '대표이사 승인')

    def test_submit_by_non_drafter_forbidden(self):
        """기안자가 아닌 타인이 상신 API를 호출하면 차단(403 또는 404)되는지 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='타인 상신 시도',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_DRAFT,
        )
        self.client.force_authenticate(user=self.user_outsider)
        response = self.client.post(f'/api/v1/approval-document/{doc.id}/submit/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    # ─────────────────────────────────────────────────────────────
    # 3. 단계별 승인 및 최종 승인(채번) 테스트
    # ─────────────────────────────────────────────────────────────
    @patch('approval.tasks.generate_approval_pdf_task.delay')
    @patch('approval.tasks.notify_drafter_task.delay')
    @patch('approval.tasks.notify_approvers_task.delay')
    def test_full_approval_lifecycle_and_doc_numbering(self, mock_notify_app, mock_notify_draft, mock_pdf):
        """1차 결재자 승인 -> 최종 결재자 승인 -> 최종 완료 및 자동 채번 생성 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='최종 승인 검증 품의서',
            content={'amount': 300000},
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )
        step1 = ApprovalStep.objects.create(document=doc, step_order=1, role_label='개발팀 팀장')
        step1.approvers.add(self.user_leader)
        step2 = ApprovalStep.objects.create(document=doc, step_order=2, role_label='대표이사 최종 승인')
        step2.approvers.add(self.user_ceo)

        # 1. 비인가자(대표이사)가 1단계에서 먼저 승인 시도 -> 403 차단
        self.client.force_authenticate(user=self.user_ceo)
        res_fail = self.client.post(f'/api/v1/approval-document/{doc.id}/act/', {'action': 'approved', 'comment': '월권 결재 시도'})
        self.assertEqual(res_fail.status_code, status.HTTP_403_FORBIDDEN)

        # 2. 1차 결재자(팀장) 정상 승인
        self.client.force_authenticate(user=self.user_leader)
        res_step1 = self.client.post(f'/api/v1/approval-document/{doc.id}/act/', {'action': 'approved', 'comment': '1차 승인합니다.'})
        self.assertEqual(res_step1.status_code, status.HTTP_200_OK)

        doc.refresh_from_db()
        self.assertEqual(doc.current_step, 2)
        self.assertEqual(doc.status, ApprovalDocument.STATUS_PENDING)

        # 3. 1차 결재자가 중복 승인 시도 -> 403 차단 (2단계 권한 없음)
        res_dup = self.client.post(f'/api/v1/approval-document/{doc.id}/act/', {'action': 'approved'})
        self.assertEqual(res_dup.status_code, status.HTTP_403_FORBIDDEN)

        # 4. 최종 결재자(대표이사) 최종 승인
        self.client.force_authenticate(user=self.user_ceo)
        res_step2 = self.client.post(f'/api/v1/approval-document/{doc.id}/act/', {'action': 'approved', 'comment': '최종 승인 완료'})
        self.assertEqual(res_step2.status_code, status.HTTP_200_OK)

        doc.refresh_from_db()
        self.assertEqual(doc.status, ApprovalDocument.STATUS_APPROVED)
        self.assertIsNotNone(doc.completed_at)
        self.assertIsNotNone(doc.doc_number)
        self.assertTrue(doc.doc_number.startswith('BIZ-'))

    # ─────────────────────────────────────────────────────────────
    # 4. 반려(Reject) 테스트
    # ─────────────────────────────────────────────────────────────
    @patch('approval.tasks.notify_drafter_task.delay')
    def test_reject_document_stops_workflow(self, mock_notify):
        """결재자가 반려 처리 시 결재선이 즉시 중단되고 상태가 반려로 변경되는지 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='반려 테스트 품의서',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )
        step1 = ApprovalStep.objects.create(document=doc, step_order=1, role_label='개발팀 팀장')
        step1.approvers.add(self.user_leader)

        self.client.force_authenticate(user=self.user_leader)
        response = self.client.post(f'/api/v1/approval-document/{doc.id}/act/', {
            'action': 'rejected',
            'comment': '예산 초과로 인한 반려'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        doc.refresh_from_db()
        self.assertEqual(doc.status, ApprovalDocument.STATUS_REJECTED)
        action_record = ApprovalAction.objects.filter(step=step1, action='rejected').first()
        self.assertIsNotNone(action_record)
        self.assertEqual(action_record.comment, '예산 초과로 인한 반려')

    # ─────────────────────────────────────────────────────────────
    # 5. 상신 회수(Cancel) 테스트
    # ─────────────────────────────────────────────────────────────
    @patch('approval.tasks.notify_cancel_task.delay')
    def test_cancel_document_before_approval(self, mock_cancel_task):
        """1차 결재 승인 전 기안자가 정상 회수(임시저장 복귀)할 수 있는지 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='회수 테스트 문서 1',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )
        step1 = ApprovalStep.objects.create(document=doc, step_order=1, role_label='개발팀 팀장')
        step1.approvers.add(self.user_leader)

        self.client.force_authenticate(user=self.user_drafter)
        res_cancel = self.client.post(f'/api/v1/approval-document/{doc.id}/cancel/')
        self.assertEqual(res_cancel.status_code, status.HTTP_200_OK)

        doc.refresh_from_db()
        self.assertEqual(doc.status, ApprovalDocument.STATUS_DRAFT)
        self.assertEqual(doc.steps.count(), 0)

    def test_cancel_document_after_approval_blocked(self):
        """1차 결재자가 이미 승인을 완료한 문서는 회수할 수 없도록 400 차단되는지 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='회수 테스트 문서 2',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )
        step1 = ApprovalStep.objects.create(document=doc, step_order=1, role_label='개발팀 팀장')
        step1.approvers.add(self.user_leader)
        ApprovalAction.objects.create(step=step1, approver=self.user_leader, action=ApprovalAction.ACTION_APPROVED)

        self.client.force_authenticate(user=self.user_drafter)
        res_cancel_fail = self.client.post(f'/api/v1/approval-document/{doc.id}/cancel/')
        self.assertEqual(res_cancel_fail.status_code, status.HTTP_400_BAD_REQUEST)

    # ─────────────────────────────────────────────────────────────
    # 6. 결재 권한 위임 (대결, Delegation) 테스트
    # ─────────────────────────────────────────────────────────────
    def test_approval_by_delegated_user(self):
        """위임 기간 내 대결자가 원 결재자를 대신하여 승인할 수 있는지 검증"""
        today = timezone.localdate()
        ApprovalDelegation.objects.create(
            delegator=self.user_leader,
            delegatee=self.user_delegate,
            start_date=today,
            end_date=today,
            is_active=True,
            reason='출장으로 인한 결재 권한 위임',
        )

        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='대결 테스트 문서',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )
        step1 = ApprovalStep.objects.create(document=doc, step_order=1, role_label='개발팀 팀장')
        step1.approvers.add(self.user_leader)

        # 대결자(user_delegate)로 로그인하여 승인
        self.client.force_authenticate(user=self.user_delegate)
        response = self.client.post(f'/api/v1/approval-document/{doc.id}/act/', {
            'action': 'approved',
            'comment': '팀장 출장으로 대리 결재합니다.'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        action = ApprovalAction.objects.filter(step=step1).first()
        self.assertTrue(action.is_delegated)
        self.assertEqual(action.delegated_from, self.user_leader)
        self.assertEqual(action.approver, self.user_delegate)

    # ─────────────────────────────────────────────────────────────
    # 7. 보안등급(Security Level) 접근 권한 테스트
    # ─────────────────────────────────────────────────────────────
    def test_security_level_visibility_control(self):
        """1등급(비공개) 문서는 타 부서원에게 조회 목록에서 배제되는지 검증"""
        secret_doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='1급 비밀 문서',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            security_level=ApprovalDocument.SECURITY_SECRET,
            status=ApprovalDocument.STATUS_APPROVED,
        )

        # 1. 타 부서원(outsider) 목록 조회 시 1등급 문서 미노출
        self.client.force_authenticate(user=self.user_outsider)
        response = self.client.get('/api/v1/approval-document/')
        doc_ids = [d['id'] for d in response.data.get('results', response.data)]
        self.assertNotIn(secret_doc.id, doc_ids)

        # 2. 타 부서원이 상세 URL로 직접 접근 시 403 또는 404 차단
        res_detail = self.client.get(f'/api/v1/approval-document/{secret_doc.id}/')
        self.assertIn(res_detail.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_security_level_dept_and_public_visibility(self):
        """2등급(부서공개) 문서의 동일부서/타부서 열람 격리 및 3등급(전사공개) 문서의 전사 열람 허용 검증"""
        # 1. 2등급(부서공개) 승인 완료 문서
        dept_doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='개발팀 2등급 부서공개 문서',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,  # 개발팀(dept_dev)
            security_level=ApprovalDocument.SECURITY_DEPT,
            status=ApprovalDocument.STATUS_APPROVED,
        )

        # 2. 3등급(전사공개) 승인 완료 문서
        public_doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='전사 공지 3등급 공개 문서',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            security_level=ApprovalDocument.SECURITY_PUBLIC,
            status=ApprovalDocument.STATUS_APPROVED,
        )

        # ── 개발팀 소속 동료(user_delegate) 시점 ──
        # 기안자나 결재자가 아니지만 개발팀 소속이므로 2등급, 3등급 모두 열람 가능
        self.client.force_authenticate(user=self.user_delegate)
        res_team = self.client.get('/api/v1/approval-document/')
        team_doc_ids = [d['id'] for d in res_team.data.get('results', res_team.data)]
        self.assertIn(dept_doc.id, team_doc_ids)
        self.assertIn(public_doc.id, team_doc_ids)

        # ── 인사팀 타 부서원(user_outsider) 시점 ──
        # 2등급 문서는 목록에 미노출, 3등급 문서는 목록에 노출
        self.client.force_authenticate(user=self.user_outsider)
        res_outsider = self.client.get('/api/v1/approval-document/')
        outsider_doc_ids = [d['id'] for d in res_outsider.data.get('results', res_outsider.data)]
        self.assertNotIn(dept_doc.id, outsider_doc_ids)
        self.assertIn(public_doc.id, outsider_doc_ids)

        # 타 부서원이 2등급 문서 상세 URL 직접 접근 -> 차단
        res_dept_detail = self.client.get(f'/api/v1/approval-document/{dept_doc.id}/')
        self.assertIn(res_dept_detail.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # 타 부서원이 3등급 문서 상세 URL 직접 접근 -> 성공
        res_public_detail = self.client.get(f'/api/v1/approval-document/{public_doc.id}/')
        self.assertEqual(res_public_detail.status_code, status.HTTP_200_OK)

    def test_confidential_document_accessible_by_assigned_observer(self):
        """1등급(비공개) 비밀 문서라도 '참조자(Observer)'로 지정된 직원은 정상 열람할 수 있는지 검증"""
        confidential_doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            title='극비 전략 기획서',
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            security_level=ApprovalDocument.SECURITY_SECRET,
            status=ApprovalDocument.STATUS_APPROVED,
        )
        # 타 부서원(user_outsider)을 참조자로 등록
        confidential_doc.observers.add(self.user_outsider)

        # user_outsider로 조회 시 목록에 노출되고 상세 조회가 허용되어야 함
        self.client.force_authenticate(user=self.user_outsider)
        res_list = self.client.get('/api/v1/approval-document/')
        doc_ids = [d['id'] for d in res_list.data.get('results', res_list.data)]
        self.assertIn(confidential_doc.id, doc_ids)

        res_detail = self.client.get(f'/api/v1/approval-document/{confidential_doc.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['title'], '극비 전략 기획서')

    def test_approval_delegation_creation_defaults_to_request_user(self):
        """대결(위임) 등록 시 delegator_id가 누락되어도 슈퍼유저 및 일반 유저 모두 요청 유저로 정상 생성되는지 검증"""
        # 1. 슈퍼유저 생성
        admin_user = User.objects.create_superuser(
            username='admin_boss', email='admin@example.com', password='password123'
        )

        # 2. 슈퍼유저가 본인의 대결 등록 (delegator_id 미전달)
        self.client.force_authenticate(user=admin_user)
        payload = {
            'delegatee_id': self.user_leader.id,
            'start_date': '2026-10-12',
            'end_date': '2026-10-19',
            'reason': '출장으로 인한 대결 위임',
            'is_active': True,
        }
        res_admin = self.client.post('/api/v1/approval-delegation/', payload)
        self.assertEqual(res_admin.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_admin.data['delegator']['id'], admin_user.id)
        self.assertEqual(res_admin.data['delegatee']['id'], self.user_leader.id)

        # 3. 일반 사용자(user_leader)가 본인의 대결 등록 (delegator_id 미전달)
        self.client.force_authenticate(user=self.user_leader)
        payload_leader = {
            'delegatee_id': self.user_drafter.id,
            'start_date': '2026-10-20',
            'end_date': '2026-10-25',
            'reason': '휴가',
            'is_active': True,
        }
        res_leader = self.client.post('/api/v1/approval-delegation/', payload_leader)
        self.assertEqual(res_leader.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_leader.data['delegator']['id'], self.user_leader.id)
        self.assertEqual(res_leader.data['delegatee']['id'], self.user_drafter.id)


    def test_file_cleanup_on_document_delete(self):
        """ApprovalDocument 삭제 시 attachment 및 pdf_file 파일이 스토리지에서 자동 삭제되는지 검증"""
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage

        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            title='파일 정리 테스트 품의',
            status=ApprovalDocument.STATUS_DRAFT,
        )
        doc.attachment.save('test_att.txt', ContentFile(b'sample attachment content'))
        doc.pdf_file.save('test_pdf.pdf', ContentFile(b'%PDF-1.4 sample pdf'))
        doc.save()

        att_path = doc.attachment.name
        pdf_path = doc.pdf_file.name

        self.assertTrue(default_storage.exists(att_path))
        self.assertTrue(default_storage.exists(pdf_path))

        # 문서 삭제 시 파일도 함께 삭제되는지 검증
        with self.captureOnCommitCallbacks(execute=True):
            doc.delete()

        self.assertFalse(default_storage.exists(att_path))
        self.assertFalse(default_storage.exists(pdf_path))

    @patch('approval.tasks.generate_approval_pdf_task.delay')
    def test_ceo_direct_submit_auto_finalizes(self, mock_pdf_task):
        """대표이사 직접 기안 후 submit 호출 시 단독 승인으로 즉시 approved 상태 및 채번 완료 검증"""
        self.client.force_authenticate(user=self.user_ceo)
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            drafter=self.user_ceo,
            drafter_assignment=self.assign_ceo,
            title='대표이사 직접 기안 결재',
            status=ApprovalDocument.STATUS_DRAFT,
        )

        res = self.client.post(f'/api/v1/approval-document/{doc.id}/submit/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        doc.refresh_from_db()
        self.assertEqual(doc.status, ApprovalDocument.STATUS_APPROVED)
        self.assertIsNotNone(doc.completed_at)
        self.assertIsNotNone(doc.doc_number)
        self.assertTrue(len(doc.doc_number) > 0)
        self.assertEqual(doc.steps.count(), 1)
        self.assertEqual(doc.steps.first().status, ApprovalStep.STATUS_APPROVED)

    def test_and_condition_delegation_approval_completes(self):
        """[T-AND] AND(전원 합의) 조건 결재 단계에서 대결자가 원결재자를 대신해 승인 시, 모든 필수 결재자의 승인이 완료되면 단계 및 문서가 정상 승인되는지 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            title='AND 조건 결재 대결 테스트',
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )
        step = ApprovalStep.objects.create(
            document=doc,
            step_order=1,
            role_label='팀장 및 대표이사 합의',
            condition=ApprovalStep.CONDITION_AND,
            status=ApprovalStep.STATUS_PENDING,
        )
        step.approvers.set([self.user_leader, self.user_ceo])

        # leader -> delegate 위임 등록
        today = timezone.localdate()
        ApprovalDelegation.objects.create(
            delegator=self.user_leader,
            delegatee=self.user_delegate,
            start_date=today,
            end_date=today,
            is_active=True,
            reason='출장 대결',
        )

        # 1. 대결자(user_delegate)가 leader 대신 승인
        self.client.force_authenticate(user=self.user_delegate)
        res1 = self.client.post(f'/api/v1/approval-document/{doc.id}/act/', {
            'action': 'approved',
            'comment': '팀장 대결 승인',
        })
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # 아직 ceo 승인이 남았으므로 step 및 doc는 pending 상태 유지
        step.refresh_from_db()
        doc.refresh_from_db()
        self.assertEqual(step.status, ApprovalStep.STATUS_PENDING)
        self.assertEqual(doc.status, ApprovalDocument.STATUS_PENDING)

        # 2. 대표이사(user_ceo) 승인
        self.client.force_authenticate(user=self.user_ceo)
        with patch('approval.tasks.generate_approval_pdf_task.delay'):
            res2 = self.client.post(f'/api/v1/approval-document/{doc.id}/act/', {
                'action': 'approved',
                'comment': '대표이사 최종 승인',
            })
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # AND 조건이 모두 충족되어 step과 doc가 STATUS_APPROVED로 완료되었는지 검증
        step.refresh_from_db()
        doc.refresh_from_db()
        self.assertEqual(step.status, ApprovalStep.STATUS_APPROVED)
        self.assertEqual(doc.status, ApprovalDocument.STATUS_APPROVED)
        self.assertIsNotNone(doc.completed_at)
        self.assertIsNotNone(doc.doc_number)

    def test_double_action_prevention_with_delegation(self):
        """[T-DOUBLE] 원결재자와 대결자 간의 상호 중복 결재(Double Approval) 완벽 차단 검증"""
        today = timezone.localdate()
        ApprovalDelegation.objects.create(
            delegator=self.user_leader,
            delegatee=self.user_delegate,
            start_date=today,
            end_date=today,
            is_active=True,
            reason='대결',
        )

        # 케이스 1: 대결자 승인 후 원결재자 또는 대결자 재승인 차단
        doc1 = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            title='중복 결재 차단 1',
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )
        step1 = ApprovalStep.objects.create(
            document=doc1,
            step_order=1,
            role_label='팀장 승인',
            condition=ApprovalStep.CONDITION_OR,
            status=ApprovalStep.STATUS_PENDING,
        )
        step1.approvers.set([self.user_leader])

        # 대결자 승인
        self.client.force_authenticate(user=self.user_delegate)
        res = self.client.post(f'/api/v1/approval-document/{doc1.id}/act/', {'action': 'approved'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 대결자가 다시 승인 시도 -> 차단 (문서 상태를 pending으로 유지한 다단계 상황 가정하여 검증하기 위해 강제 pending)
        doc1.status = ApprovalDocument.STATUS_PENDING
        doc1.save(update_fields=['status'])
        res_dup_delegate = self.client.post(f'/api/v1/approval-document/{doc1.id}/act/', {'action': 'approved'})
        self.assertEqual(res_dup_delegate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('이미 승인 또는 반려 처리하셨습니다', res_dup_delegate.data['detail'])

        # 원결재자(user_leader)가 직접 승인 시도 -> 차단
        self.client.force_authenticate(user=self.user_leader)
        res_dup_leader = self.client.post(f'/api/v1/approval-document/{doc1.id}/act/', {'action': 'approved'})
        self.assertEqual(res_dup_leader.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('이미 승인 또는 반려 처리하셨습니다', res_dup_leader.data['detail'])

        # 케이스 2: 원결재자가 먼저 승인한 후 대결자가 대리 승인 시도 -> 차단
        doc2 = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            title='중복 결재 차단 2',
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
        )
        step2 = ApprovalStep.objects.create(
            document=doc2,
            step_order=1,
            role_label='팀장 승인',
            condition=ApprovalStep.CONDITION_OR,
            status=ApprovalStep.STATUS_PENDING,
        )
        step2.approvers.set([self.user_leader])

        # 원결재자 직접 승인
        self.client.force_authenticate(user=self.user_leader)
        res_leader_ok = self.client.post(f'/api/v1/approval-document/{doc2.id}/act/', {'action': 'approved'})
        self.assertEqual(res_leader_ok.status_code, status.HTTP_200_OK)

        # 대결자가 대리 승인 시도 -> 차단
        doc2.status = ApprovalDocument.STATUS_PENDING
        doc2.save(update_fields=['status'])
        self.client.force_authenticate(user=self.user_delegate)
        res_delegate_blocked = self.client.post(f'/api/v1/approval-document/{doc2.id}/act/', {'action': 'approved'})
        self.assertEqual(res_delegate_blocked.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('이미 승인 또는 반려 처리하셨습니다', res_delegate_blocked.data['detail'])

    def test_attachment_access_and_modification_guards(self):
        """[T-ATT] 결재 첨부파일 접근 제어(BOLA 방지) 및 기안자/문서상태 기반 추가·삭제 방어 검증"""
        # 1. 1등급(비공개) 문서 생성
        conf_doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type,
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            title='비공개 특수 품의서',
            security_level=ApprovalDocument.SECURITY_SECRET,
            status=ApprovalDocument.STATUS_DRAFT,
        )

        # 2. 기안자가 첨부파일 업로드 성공
        self.client.force_authenticate(user=self.user_drafter)
        upload_file = SimpleUploadedFile('secret_plan.pdf', b'Confidential Plan Content', content_type='application/pdf')
        res_upload = self.client.post(
            '/api/v1/approval-attachment/',
            {'document': conf_doc.id, 'file': upload_file},
            format='multipart'
        )
        self.assertEqual(res_upload.status_code, status.HTTP_201_CREATED)
        attachment_id = res_upload.data['id']

        # 3. 비인가자(user_outsider)의 BOLA 공격 차단: 목록 및 상세 조회 차단
        self.client.force_authenticate(user=self.user_outsider)
        res_list = self.client.get('/api/v1/approval-attachment/')
        att_ids = [att['id'] for att in res_list.data.get('results', res_list.data)]
        self.assertNotIn(attachment_id, att_ids)

        res_detail = self.client.get(f'/api/v1/approval-attachment/{attachment_id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_404_NOT_FOUND)

        # 4. 타인이 첨부파일 업로드 시도 시 403 차단
        other_file = SimpleUploadedFile('hack.pdf', b'hack content', content_type='application/pdf')
        res_unauth_upload = self.client.post(
            '/api/v1/approval-attachment/',
            {'document': conf_doc.id, 'file': other_file},
            format='multipart'
        )
        self.assertEqual(res_unauth_upload.status_code, status.HTTP_403_FORBIDDEN)

        # 5. 문서가 PENDING(진행 중) 상태일 때 첨부파일 삭제 및 추가 차단 검증
        conf_doc.status = ApprovalDocument.STATUS_PENDING
        conf_doc.save(update_fields=['status'])

        self.client.force_authenticate(user=self.user_drafter)
        # 삭제 시도 -> 400 차단
        res_del = self.client.delete(f'/api/v1/approval-attachment/{attachment_id}/')
        self.assertEqual(res_del.status_code, status.HTTP_400_BAD_REQUEST)

        # 추가 시도 -> 400 차단
        new_file = SimpleUploadedFile('new.pdf', b'new content', content_type='application/pdf')
        res_add = self.client.post(
            '/api/v1/approval-attachment/',
            {'document': conf_doc.id, 'file': new_file},
            format='multipart'
        )
        self.assertEqual(res_add.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delegation_self_delegation_and_delegatee_modification_blocked(self):
        """[T-DEL] 자기 자신에게 위임 불가 검증 및 수임자(대결자)의 임의 수정/삭제 403 차단 검증"""
        # 1. 자기 자신에게 위임 시도 (400 차단)
        self.client.force_authenticate(user=self.user_leader)
        today = timezone.localdate()
        res_self = self.client.post('/api/v1/approval-delegation/', {
            'delegatee_id': self.user_leader.id,
            'start_date': str(today),
            'end_date': str(today),
            'reason': '셀프 위임 시도',
        })
        self.assertEqual(res_self.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('delegatee', res_self.data)

        # 2. 정상 위임 등록 (user_leader -> user_delegate)
        res_create = self.client.post('/api/v1/approval-delegation/', {
            'delegatee_id': self.user_delegate.id,
            'start_date': str(today),
            'end_date': str(today),
            'reason': '정상 위임',
            'is_active': True,
        })
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        del_id = res_create.data['id']

        # 3. 수임자(user_delegate)가 해당 위임 건을 수정(PATCH)하려 할 때 403 차단
        self.client.force_authenticate(user=self.user_delegate)
        res_patch = self.client.patch(f'/api/v1/approval-delegation/{del_id}/', {
            'reason': '수임자가 위임 사유 임의 변경',
        })
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        # 4. 수임자(user_delegate)가 해당 위임 건을 삭제(DELETE)하려 할 때 403 차단
        res_delete = self.client.delete(f'/api/v1/approval-delegation/{del_id}/')
        self.assertEqual(res_delete.status_code, status.HTTP_403_FORBIDDEN)

        # 5. 위임자 본인(user_leader)은 정상적으로 삭제 가능 (204 No Content)
        self.client.force_authenticate(user=self.user_leader)
        res_del_ok = self.client.delete(f'/api/v1/approval-delegation/{del_id}/')
        self.assertEqual(res_del_ok.status_code, status.HTTP_204_NO_CONTENT)
