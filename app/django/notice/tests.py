"""
Notice 앱 테스트

PdfExportBill 클래스의 할인/연체료 계산 로직 테스트 포함
"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from notice.exports.pdf import PdfExportBill
from payment.exports.pdf import PdfExportPayments
from _utils.payment_adjustment import calculate_all_installments_payment_allocation, get_installment_adjustment_summary
from _utils.simple_late_payment import calculate_late_penalty, calculate_simple_late_payment
from contract.models import Contract
from payment.models import InstallmentPaymentOrder
from project.models import Project
from company.models import ProjectBudget
from cash.models import ProjectCashBook, SalesPriceByGT
from items.models import UnitType


User = get_user_model()


class PdfExportBillTestCase(TestCase):
    """PdfExportBill 할인/연체료 계산 테스트"""

    @classmethod
    def setUpTestData(cls):
        """테스트 데이터 생성"""
        # 사용자
        cls.user = User.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='testpass123'
        )

        # 프로젝트
        cls.project = Project.objects.create(
            name='테스트 프로젝트',
            kind='apt',
            start_year=2024,
            local1='서울',
            local2='강남구',
            creator=cls.user,
            modifier=cls.user
        )

        # 예산
        cls.budget = ProjectBudget.objects.create(
            project=cls.project,
            basis_calc='area',
            creator=cls.user,
            modifier=cls.user
        )

        # 유닛 타입
        cls.unit_type = UnitType.objects.create(
            project=cls.project,
            sort=1,
            name='84A',
            color='#000000',
            average_price=100000,
            creator=cls.user,
            modifier=cls.user
        )

        # 분양가
        cls.sales_price = SalesPriceByGT.objects.create(
            project=cls.project,
            unit_type=cls.unit_type,
            unit_floor_type=1,
            price=500000000,  # 5억
            creator=cls.user,
            modifier=cls.user
        )

        # 계약 (2024-08-15 계약)
        cls.contract = Contract.objects.create(
            project=cls.project,
            unit_type=cls.unit_type,
            contractor='홍길동',
            contract_date=date(2024, 8, 15),
            succession=None,
            is_active=True,
            creator=cls.user,
            modifier=cls.user
        )

        # 납부 회차 설정
        cls.installments = []

        # 1차 계약금 (계약 시 납부, 납부기한 없음)
        inst1 = InstallmentPaymentOrder.objects.create(
            project=cls.project,
            type_sort=1,
            pay_code=1,
            pay_name='1차 계약금',
            pay_time=1,
            pay_ratio=Decimal('10.00'),
            pay_due_date=None,
            is_late_penalty=False,
            late_penalty_ratio=None,
            is_prep_discount=False,
            prep_discount_ratio=None,
            creator=cls.user,
            modifier=cls.user
        )
        cls.installments.append(inst1)

        # 2차 중도금 (2024-11-30 납부기한, 연체율 10%, 선납할인 3%)
        inst2 = InstallmentPaymentOrder.objects.create(
            project=cls.project,
            type_sort=1,
            pay_code=2,
            pay_name='2차 중도금',
            pay_time=2,
            pay_ratio=Decimal('10.00'),
            pay_due_date=date(2024, 11, 30),
            extra_due_date=date(2024, 11, 30),
            is_late_penalty=True,
            late_penalty_ratio=Decimal('10.00'),
            is_prep_discount=True,
            prep_discount_ratio=Decimal('3.00'),
            prep_ref_date=date(2024, 11, 20),  # 10일 선납 시 할인
            creator=cls.user,
            modifier=cls.user
        )
        cls.installments.append(inst2)

        # 3차 중도금 (2025-02-28 납부기한, 연체율 10%)
        inst3 = InstallmentPaymentOrder.objects.create(
            project=cls.project,
            type_sort=1,
            pay_code=3,
            pay_name='3차 중도금',
            pay_time=3,
            pay_ratio=Decimal('10.00'),
            pay_due_date=date(2025, 2, 28),
            extra_due_date=date(2025, 2, 28),
            is_late_penalty=True,
            late_penalty_ratio=Decimal('10.00'),
            is_prep_discount=False,
            prep_discount_ratio=None,
            creator=cls.user,
            modifier=cls.user
        )
        cls.installments.append(inst3)

    def test_calculate_late_penalty_function(self):
        """simple_late_payment.calculate_late_penalty() 함수 테스트"""
        inst = self.installments[1]  # 2차 중도금 (연체율 10%)

        # 5천만원, 15일 연체
        late_amount = 50000000
        late_days = 15

        penalty = calculate_late_penalty(self.contract, inst, late_amount, late_days)

        # 기대값: 50,000,000 * (10 / 100 / 365) * 15 = 205,479원 (int 변환)
        expected = int(late_amount * Decimal('0.1') / Decimal('365') * late_days)

        self.assertEqual(penalty, expected)
        self.assertGreater(penalty, 0)

    def test_waterfall_allocation(self):
        """Waterfall allocation 기본 동작 테스트"""
        # 1차 계약금: 5천만원 (2024-08-15 납부)
        ProjectCashBook.objects.create(
            project=self.project,
            contract=self.contract,
            installment_order=self.installments[0],
            deal_date=date(2024, 8, 15),
            income=50000000,
            project_account_d3_id=1,  # is_payment=True 가정
            creator=self.user,
            modifier=self.user
        )

        # Waterfall 계산
        all_status = calculate_all_installments_payment_allocation(self.contract)

        # 1차 계약금이 완납 처리되었는지 확인
        inst1_status = all_status.get(self.installments[0].id)
        self.assertIsNotNone(inst1_status)
        self.assertTrue(inst1_status['is_fully_paid'])
        self.assertEqual(inst1_status['paid_amount'], 50000000)

    def test_prepayment_discount_calculation(self):
        """선납 할인 계산 테스트"""
        # 2차 중도금: 5천만원 (2024-11-15 납부 - 15일 선납)
        ProjectCashBook.objects.create(
            project=self.project,
            contract=self.contract,
            installment_order=self.installments[1],
            deal_date=date(2024, 11, 15),  # 납부기한(11-30)보다 15일 빠름
            income=50000000,
            project_account_d3_id=1,
            creator=self.user,
            modifier=self.user
        )

        # 할인 계산
        adj = get_installment_adjustment_summary(self.contract, self.installments[1])

        # 선납할인이 계산되었는지 확인
        discount = adj.get('total_discount', 0)
        self.assertGreater(discount, 0)

        # 대략적인 할인액 검증 (50,000,000 * 3% / 365 * 10일 정도)
        # prep_ref_date가 11-20이고, 납부일이 11-15이므로 차이 없음 -> 납부기한 11-30까지 15일
        # 실제 계산은 payment_adjustment.calculate_prepayment_discount 참조

    def test_late_penalty_calculation(self):
        """연체료 계산 테스트"""
        # 2차 중도금: 5천만원 (2024-12-15 납부 - 15일 연체)
        ProjectCashBook.objects.create(
            project=self.project,
            contract=self.contract,
            installment_order=self.installments[1],
            deal_date=date(2024, 12, 15),  # 납부기한(11-30)보다 15일 늦음
            income=50000000,
            project_account_d3_id=1,
            creator=self.user,
            modifier=self.user
        )

        # Waterfall 계산
        all_status = calculate_all_installments_payment_allocation(self.contract)
        inst2_status = all_status.get(self.installments[1].id)

        # 지연일수 확인
        self.assertGreater(inst2_status.get('late_days', 0), 0)

        # 연체료 계산
        late_days = inst2_status['late_days']
        late_amount = inst2_status['late_payment_amount']

        penalty = calculate_late_penalty(
            self.contract,
            self.installments[1],
            late_amount,
            late_days
        )

        self.assertGreater(penalty, 0)

    def test_pdf_export_bill_calculation(self):
        """PdfExportBill.calculate_late_fees_standardized() 테스트"""
        # 2차 중도금 연체 납부
        ProjectCashBook.objects.create(
            project=self.project,
            contract=self.contract,
            installment_order=self.installments[1],
            deal_date=date(2024, 12, 15),
            income=50000000,
            project_account_d3_id=1,
            creator=self.user,
            modifier=self.user
        )

        pub_date = date(2024, 12, 20)
        payment_orders = InstallmentPaymentOrder.objects.filter(project=self.project)
        now_due_order = 2

        # PdfExportBill 계산
        result = PdfExportBill.calculate_late_fees_standardized(
            self.contract,
            payment_orders,
            now_due_order,
            pub_date
        )

        # 결과 검증
        self.assertIn('total_late_fee', result)
        self.assertIn('total_discount', result)
        self.assertIn('installment_details', result)
        self.assertIn('penalty_count', result)
        self.assertIn('discount_count', result)

        # 연체료가 계산되었는지 확인
        self.assertGreater(result['total_late_fee'], 0)

    def test_both_pdf_classes_produce_same_results(self):
        """PdfExportBill과 PdfExportPayments가 동일한 결과 산출하는지 검증"""
        # 시나리오: 1차 정상납부, 2차 연체납부
        ProjectCashBook.objects.create(
            project=self.project,
            contract=self.contract,
            installment_order=self.installments[0],
            deal_date=date(2024, 8, 15),
            income=50000000,
            project_account_d3_id=1,
            creator=self.user,
            modifier=self.user
        )

        ProjectCashBook.objects.create(
            project=self.project,
            contract=self.contract,
            installment_order=self.installments[1],
            deal_date=date(2024, 12, 15),
            income=50000000,
            project_account_d3_id=1,
            creator=self.user,
            modifier=self.user
        )

        pub_date = date(2024, 12, 20)
        payment_orders = InstallmentPaymentOrder.objects.filter(project=self.project)
        now_due_order = 3

        # PdfExportBill 계산
        bill_result = PdfExportBill.calculate_late_fees_standardized(
            self.contract,
            payment_orders,
            now_due_order,
            pub_date
        )

        # PdfExportPayments 계산 (get_paid_with_adjustment)
        payments_result, _, (penalty_total, discount_total, _) = PdfExportPayments.get_paid_with_adjustment(
            self.contract,
            pub_date,
            is_calc=False
        )

        # 총 연체료 비교
        self.assertEqual(
            bill_result['total_late_fee'],
            penalty_total,
            msg=f"연체료 불일치: Bill={bill_result['total_late_fee']}, Payments={penalty_total}"
        )

        # 총 할인액 비교
        self.assertEqual(
            bill_result['total_discount'],
            discount_total,
            msg=f"할인액 불일치: Bill={bill_result['total_discount']}, Payments={discount_total}"
        )

    def test_prepayment_discount_scenario(self):
        """선납 할인 시나리오 테스트"""
        # 2차 중도금을 납부기한보다 먼저 납부
        ProjectCashBook.objects.create(
            project=self.project,
            contract=self.contract,
            installment_order=self.installments[1],
            deal_date=date(2024, 11, 10),  # 납부기한(11-30)보다 20일 빠름
            income=50000000,
            project_account_d3_id=1,
            creator=self.user,
            modifier=self.user
        )

        pub_date = date(2024, 11, 15)
        payment_orders = InstallmentPaymentOrder.objects.filter(project=self.project)
        now_due_order = 2

        # PdfExportBill 계산
        result = PdfExportBill.calculate_late_fees_standardized(
            self.contract,
            payment_orders,
            now_due_order,
            pub_date
        )

        # 할인이 계산되었는지 확인
        self.assertGreater(result['total_discount'], 0)
        self.assertEqual(result['discount_count'], 1)

        # 연체료는 없어야 함
        self.assertEqual(result['total_late_fee'], 0)

    def test_partial_payment_penalty(self):
        """부분 납부 시 연체료 계산 테스트"""
        # 2차 중도금의 절반만 납부
        ProjectCashBook.objects.create(
            project=self.project,
            contract=self.contract,
            installment_order=self.installments[1],
            deal_date=date(2024, 12, 15),  # 15일 연체
            income=25000000,  # 절반만 납부
            project_account_d3_id=1,
            creator=self.user,
            modifier=self.user
        )

        pub_date = date(2024, 12, 20)

        # Waterfall 계산
        all_status = calculate_all_installments_payment_allocation(self.contract)
        inst2_status = all_status.get(self.installments[1].id)

        # 미완납 상태 확인
        self.assertFalse(inst2_status['is_fully_paid'])

        # 지연 납부액 확인 (남은 금액)
        self.assertEqual(inst2_status['remaining_amount'], 25000000)

        # 연체료 계산
        payment_orders = InstallmentPaymentOrder.objects.filter(project=self.project)
        result = PdfExportBill.calculate_late_fees_standardized(
            self.contract,
            payment_orders,
            2,
            pub_date
        )

        # 연체료가 남은 금액 기준으로 계산되었는지 확인
        self.assertGreater(result['total_late_fee'], 0)


class SimpleLatePaymentTestCase(TestCase):
    """simple_late_payment 모듈 단위 테스트"""

    def test_calculate_simple_late_payment_no_due_date(self):
        """납부기한이 없는 회차(계약금) 테스트"""
        # TODO: 실제 모델 생성 및 테스트 구현
        pass

    def test_calculate_simple_late_payment_pre_contract(self):
        """계약일 이전 회차 테스트"""
        # TODO: 계약일 이전 회차의 납부기한 계산 로직 테스트
        pass

    def test_calculate_late_penalty_zero_conditions(self):
        """연체료가 0이 되는 조건 테스트"""
        # late_days <= 0
        # late_payment_amount <= 0
        # is_late_penalty = False
        # late_penalty_ratio = None
        pass
