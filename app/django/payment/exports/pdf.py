"""
Payment PDF Export Views

납부 관련 PDF 내보내기 뷰들
"""
from datetime import datetime

from _pdf.mixins import PdfExportMixin, ContractPdfMixin, PaymentPdfMixin, DateUtilMixin
from _utils.contract_price import get_contract_payment_plan, get_contract_price
from payment.models import InstallmentPaymentOrder, SpecialPaymentOrder, SpecialDownPay


class PdfExportPayments(PdfExportMixin, ContractPdfMixin, PaymentPdfMixin, DateUtilMixin):
    """납부내역서 PDF 내보내기"""

    def get(self, request):
        # 요청 파라미터 추출
        project_id = request.GET.get('project')
        cont_id = request.GET.get('contract')
        pub_date = self.parse_date(request.GET.get('pub_date'))
        is_calc = bool(request.GET.get('is_calc'))

        # 기본 컨텍스트 생성
        context = self.get_base_context(pub_date=pub_date, is_calc=is_calc)

        # 계약 정보
        contract = self.get_contract(cont_id)
        context['contract'] = contract

        # 동호수 정보
        unit = self.get_contract_unit(contract)
        context['unit'] = unit

        # 가격 정보
        price, price_build, price_land, price_tax = get_contract_price(contract)
        context.update({
            'price': price if unit else '동호 지정 후 고지',
            'price_build': price_build if unit else '-',
            'price_land': price_land if unit else '-',
            'price_tax': price_tax if unit else '-'
        })

        # 정확한 결제 계획 가져오기
        payment_plan = get_contract_payment_plan(contract)

        # 약정금 누계 계산
        context['due_amount'] = sum(plan_item['amount'] for plan_item in payment_plan)

        # 간단 차수 정보 생성
        context['simple_orders'] = self.get_simple_orders_from_plan(payment_plan, contract)

        # 납부목록, 완납금액 구하기
        paid_dicts, paid_sum_total, calc_sums = self.get_paid_from_plan(
            contract, context['simple_orders'], pub_date, is_calc=is_calc
        )

        context.update({
            'paid_dicts': paid_dicts,
            'paid_sum_total': paid_sum_total,
            'calc_sums': calc_sums
        })

        # PDF 생성 및 응답
        filename = 'payments_contractor'
        return self.create_pdf_response('pdf/payments_by_contractor.html', context, filename)

    def get_simple_orders_from_plan(self, payment_plan, contract):
        """payment plan에서 간단 차수 정보 생성"""
        simple_orders = []
        amount_total = 0

        # 계산 시작 회차 찾기
        try:
            calc_start = next(
                (plan['installment_order'].pay_code for plan in payment_plan
                 if plan['installment_order'].is_prep_discount or plan['installment_order'].is_late_penalty),
                2
            )
        except StopIteration:
            calc_start = 2

        for plan_item in payment_plan:
            order = plan_item['installment_order']
            amount = plan_item['amount']
            amount_total += amount

            # 납부회차 정보 가져오기
            payment_orders = InstallmentPaymentOrder.objects.filter(project=contract.project)

            ord_info = {
                'name': order.alias_name if order.alias_name else order.pay_name,
                'pay_code': order.pay_code,
                'calc_start': calc_start,
                'due_date': self._get_due_date_per_order(contract, order, payment_orders),
                'amount': amount,
                'amount_total': amount_total,
            }
            simple_orders.append(ord_info)

        return simple_orders

    def get_paid_from_plan(self, contract, simple_orders, pub_date, **kwargs):
        """payment plan 기반 납부 금액 계산"""
        from _pdf.views import get_paid  # 원본 함수 재사용
        return get_paid(contract, simple_orders, pub_date, **kwargs)

    def _get_due_date_per_order(self, contract, order, payment_orders):
        """회차별 납부 기한 계산"""
        from _pdf.views import get_due_date_per_order
        return get_due_date_per_order(contract, order, payment_orders)


class PdfExportCalculation(PdfExportMixin, ContractPdfMixin, PaymentPdfMixin, DateUtilMixin):
    """정산서 PDF 내보내기"""

    def get(self, request):
        # 요청 파라미터 추출
        project_id = request.GET.get('project')
        cont_id = request.GET.get('contract')
        pub_date = self.parse_date(request.GET.get('pub_date'))

        # 기본 컨텍스트 생성
        context = self.get_base_context(pub_date=pub_date)

        # 계약 정보
        contract = self.get_contract(cont_id)
        context['contract'] = contract

        # 동호수 정보
        unit = self.get_contract_unit(contract)
        context['unit'] = unit

        # 가격 정보
        price, price_build, price_land, price_tax = get_contract_price(contract)
        context.update({
            'price': price if unit else '동호 지정 후 고지',
            'price_build': price_build if unit else '-',
            'price_land': price_land if unit else '-',
            'price_tax': price_tax if unit else '-'
        })

        # 특수 계약금 정보
        down1, down2 = self.get_down_pay(contract)
        amount = {'1': down1, '2': down2}

        # 약정금 누계
        context['due_amount'] = (down1 * 4) + down2

        # 특수 납부회차 정보
        payment_orders = SpecialPaymentOrder.objects.filter(project=project_id)
        context['simple_orders'] = self.get_simple_orders(payment_orders, contract, amount, True)

        # 납부목록, 완납금액 구하기
        from _pdf.views import get_paid
        paid_dicts, paid_sum_total, calc_sums = get_paid(
            contract, context['simple_orders'], pub_date, is_calc=True, is_past=True
        )

        context.update({
            'paid_dicts': paid_dicts,
            'paid_sum_total': paid_sum_total,
            'calc_sums': calc_sums
        })

        # PDF 생성 및 응답
        filename = 'calculation_contractor'
        return self.create_pdf_response('pdf/calculation_by_contractor.html', context, filename)

    def get_down_pay(self, contract):
        """특수 계약금 정보 조회"""
        try:
            down = SpecialDownPay.objects.get(
                order_group=contract.order_group,
                unit_type=contract.unit_type
            )
            return down.payment_amount, down.payment_remain
        except SpecialDownPay.DoesNotExist:
            return 0, 0

    def get_simple_orders(self, payment_orders, contract, amount, is_past):
        """간단 차수 정보 생성 (특수)"""
        from _pdf.views import get_simple_orders
        return get_simple_orders(payment_orders, contract, amount, is_past)