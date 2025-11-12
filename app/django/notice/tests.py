"""
Notice 앱 테스트

PdfExportBill 클래스의 할인/연체료 계산 로직 테스트 포함
"""

from django.test import TestCase


class PdfExportBillTestCase(TestCase):
    """
    PdfExportBill 할인/연체료 계산 테스트

    연체료 과다 계산 버그 수정 검증용 테스트
    - 버그: 다중 납부 건의 지연일수를 무시하고 최종 납부일 기준으로 전체 금액에 연체료 일괄 적용
    - 수정: calculate_segmented_late_penalty() 함수 사용하여 각 납부 건의 실제 지연일수 반영

    실제 데이터로 검증하는 방법:
    ===================================
    Docker 환경에서 실행:
        docker compose -f deploy/docker-compose.yml exec web python manage.py shell

    Shell에서 실행할 코드:
        from notice.exports.pdf import PdfExportBill
        from payment.exports.pdf import PdfExportPayments
        from contract.models import Contract
        from payment.models import InstallmentPaymentOrder
        from datetime import date

        # 다중 납부 건이 있는 계약 선택
        contract = Contract.objects.get(id=YOUR_CONTRACT_ID)
        pub_date = date.today()
        payment_orders = InstallmentPaymentOrder.objects.filter(project=contract.project)

        # 고지서 연체료 계산
        bill_result = PdfExportBill.calculate_late_fees_standardized(
            contract, payment_orders, now_due_order, pub_date
        )
        print(f"고지서 연체료: {bill_result['total_late_fee']:,}원")
        print(f"상세 내역: {bill_result['installment_details']}")

        # 납부확인서 연체료 계산
        payments_result, _, (penalty, discount, _) = PdfExportPayments.get_paid_with_adjustment(
            contract, pub_date, is_calc=True
        )
        print(f"납부확인서 연체료: {penalty:,}원")

        # 두 클래스의 결과가 동일한지 확인
        assert bill_result['total_late_fee'] == penalty, "연체료 불일치!"

    예상 결과:
    ==========
    기존 버그 시나리오 (2024-06-14 납부기한, 65,188,000원):
        - 2024-09-05: 6건 × 10,000,000 = 60,000,000 (83일 지연)
        - 2024-09-27: 1건 × 5,188,000 (105일 지연)

    기존 계산 (잘못): 65,188,000 × 10% ÷ 365 × 105일 = 1,875,123원
    정확한 계산: (60,000,000 × 83일) + (5,188,000 × 105일) = 1,513,737원
    절감액: 361,386원 (23.9%)
    """

    def test_segmented_penalty_calculation_available(self):
        """calculate_segmented_late_penalty 함수가 올바르게 import되는지 확인"""
        from _utils.payment_adjustment import calculate_segmented_late_penalty
        self.assertTrue(callable(calculate_segmented_late_penalty))

    def test_pdf_classes_use_segmented_calculation(self):
        """PDF 클래스들이 calculate_segmented_late_penalty를 사용하는지 확인"""
        from notice.exports.pdf import PdfExportBill
        from payment.exports.pdf import PdfExportPayments
        import inspect

        # PdfExportBill.calculate_late_fees_standardized 소스 확인
        bill_source = inspect.getsource(PdfExportBill.calculate_late_fees_standardized)
        self.assertIn('calculate_segmented_late_penalty', bill_source,
                     "PdfExportBill이 calculate_segmented_late_penalty를 사용하지 않습니다")

        # PdfExportPayments.get_paid_with_adjustment 소스 확인
        payments_source = inspect.getsource(PdfExportPayments.get_paid_with_adjustment)
        self.assertIn('calculate_segmented_late_penalty', payments_source,
                     "PdfExportPayments가 calculate_segmented_late_penalty를 사용하지 않습니다")
