from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import Profile
from approval.models import DocCategory, DocumentType, ApprovalDocument, ApprovalStep
from approval.services import finalize_approval, cancel_leave_approval
from company.models import (
    Company, Department, Staff, StaffAssignment, DutyTitle, Position,
    StaffLeaveQuota, StaffLeaveUsage
)

User = get_user_model()


class LeaveApprovalIntegrationTestCase(APITestCase):
    """
    전자결재(휴가 신청서) ↔ 근태/연차 관리 자동 차감 연동 테스트
    """

    def setUp(self):
        # 1. 회사 생성
        self.company = Company.objects.create(
            name='(주)대영아이비에스',
            tax_number='123-45-67890',
            ceo='홍대표',
            org_number='123456-1234567',
            is_default=True,
        )
        self.pos_staff = Position.objects.create(company=self.company, name='사원')
        self.pos_ceo = Position.objects.create(company=self.company, name='대표이사')
        self.duty_ceo = DutyTitle.objects.create(company=self.company, name='대표이사', code='CEO')
        self.dept = Department.objects.create(company=self.company, name='개발본부', level=1)

        # 2. 기안자 사용자 및 Staff 생성
        self.user_drafter = User.objects.create_user(
            username='leave_drafter', email='drafter@example.com', password='password123'
        )
        Profile.objects.create(user=self.user_drafter, name='김휴가')
        self.staff_drafter = Staff.objects.create(
            company=self.company,
            user=self.user_drafter,
            name='김휴가',
            id_number='900101-1234567',
            personal_phone='010-1234-5678',
            position=self.pos_staff,
            date_join=date(2025, 1, 1),
            status='1',
        )
        self.assign_drafter = StaffAssignment.objects.create(
            company=self.company,
            staff=self.staff_drafter,
            department=self.dept,
            is_primary=True,
        )

        # 3. 2026년도 연차 15일 부여
        self.quota = StaffLeaveQuota.objects.create(
            company=self.company,
            staff=self.staff_drafter,
            year=2026,
            granted_days=Decimal('15.00'),
            carry_over_days=Decimal('0.00'),
            reward_days=Decimal('0.00'),
            valid_start=date(2026, 1, 1),
            valid_end=date(2026, 12, 31),
        )

        # 4. 결재 카테고리 및 휴가 결재 문서 유형 생성
        self.cat_hr = DocCategory.objects.create(name='인사/근태', code='HR')
        self.doc_type_leave = DocumentType.objects.create(
            category=self.cat_hr,
            name='휴가 신청서',
            code='HR_LEAVE',
            route_type=DocumentType.ROUTE_ORGANIZATION,
            form_template_key='LEAVE',
        )

    def test_leave_approval_creates_leave_usage_and_deducts_quota(self):
        """연차 3일 신청 후 최종 승인 시 StaffLeaveUsage 생성 및 잔여 연차 차감 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type_leave,
            title='2026년 하계 휴가 신청서',
            content={
                'leave_type': 'ANNUAL',
                'start_date': '2026-07-10',
                'end_date': '2026-07-12',
                'days_count': 3.0,
                'reason': '하계 휴가',
            },
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
        )

        # 최종 승인 실행
        finalize_approval(doc)

        # 1. StaffLeaveUsage 인스턴스 자동 생성 확인
        usage = StaffLeaveUsage.objects.filter(approval_doc=doc).first()
        self.assertIsNotNone(usage)
        self.assertEqual(usage.staff, self.staff_drafter)
        self.assertEqual(usage.leave_type, 'annual')
        self.assertEqual(usage.start_date, date(2026, 7, 10))
        self.assertEqual(usage.end_date, date(2026, 7, 12))
        self.assertEqual(usage.deduction_days, Decimal('3.00'))
        self.assertFalse(usage.is_cancelled)

        # 2. StaffLeaveQuota 연차 잔여 일수 실시간 차감 검증 (15 - 3 = 12)
        self.assertEqual(self.quota.used_days, Decimal('3.00'))
        self.assertEqual(self.quota.remaining_days, Decimal('12.00'))

    def test_half_day_leave_deduction(self):
        """오전 반차(0.5일) 신청 후 최종 승인 시 정확히 0.5일 차감 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type_leave,
            title='병원 진료 반차 신청',
            content={
                'leave_type': 'HALF_AM',
                'start_date': '2026-05-15',
                'reason': '건강검진',
            },
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
        )

        finalize_approval(doc)

        usage = StaffLeaveUsage.objects.filter(approval_doc=doc).first()
        self.assertIsNotNone(usage)
        self.assertEqual(usage.leave_type, 'half_am')
        self.assertEqual(usage.deduction_days, Decimal('0.50'))
        self.assertEqual(self.quota.remaining_days, Decimal('14.50'))

    def test_condolence_leave_no_deduction(self):
        """경조사 휴가(SPECIAL) 승인 시 무차감(0.00일) 처리 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type_leave,
            title='경조사 휴가 신청',
            content={
                'leave_type': 'SPECIAL',
                'start_date': '2026-06-01',
                'end_date': '2026-06-03',
                'reason': '가족 경조사',
            },
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
        )

        finalize_approval(doc)

        usage = StaffLeaveUsage.objects.filter(approval_doc=doc).first()
        self.assertIsNotNone(usage)
        self.assertEqual(usage.leave_type, 'condolence')
        self.assertEqual(usage.deduction_days, Decimal('0.00'))
        self.assertEqual(self.quota.remaining_days, Decimal('15.00'))

    def test_cancel_leave_restores_quota(self):
        """승인 후 취소(cancel_leave_approval) 시 is_cancelled=True 및 연차 일수 전액 원상 복구 검증"""
        doc = ApprovalDocument.objects.create(
            doc_type=self.doc_type_leave,
            title='개인 사정 휴가 신청',
            content={
                'leave_type': 'ANNUAL',
                'start_date': '2026-08-01',
                'end_date': '2026-08-02',
                'days_count': 2.0,
                'reason': '개인 일정',
            },
            drafter=self.user_drafter,
            drafter_assignment=self.assign_drafter,
            status=ApprovalDocument.STATUS_PENDING,
        )

        finalize_approval(doc)
        self.assertEqual(self.quota.remaining_days, Decimal('13.00'))

        # 취소 실행
        cancel_leave_approval(doc)

        usage = StaffLeaveUsage.objects.filter(approval_doc=doc).first()
        self.assertTrue(usage.is_cancelled)

        # 연차 잔여 일수 원상 복구 확인 (15.00)
        self.assertEqual(self.quota.used_days, Decimal('0.00'))
        self.assertEqual(self.quota.remaining_days, Decimal('15.00'))
