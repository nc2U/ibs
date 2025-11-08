from datetime import date, datetime
from itertools import accumulate

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from _pdf.utils import (get_contract, get_simple_orders, get_due_date_per_order,
                        get_late_fee, is_due, get_paid)
from _utils.contract_price import get_contract_payment_plan, get_contract_price
from cash.models import ProjectCashBook
from payment.models import InstallmentPaymentOrder, SpecialPaymentOrder, SpecialDownPay

TODAY = date.today()


class PdfExportPayments(View):
    """납부 확인서"""

    @staticmethod
    def get(request):
        context = dict()

        project = request.GET.get('project')  # 프로젝트 ID
        # 계약 건 객체
        cont_id = request.GET.get('contract')
        context['contract'] = contract = get_contract(cont_id)
        context['is_calc'] = calc = True if request.GET.get('is_calc') else False  # 1 = 일반용(할인가산 포함) / '' = 확인용

        # 발행일자
        pub_date = request.GET.get('pub_date', None)
        pub_date = datetime.strptime(pub_date, '%Y-%m-%d').date() if pub_date else TODAY
        context['pub_date'] = pub_date

        try:
            unit = contract.key_unit.houseunit
        except ObjectDoesNotExist:
            unit = None

        # 동호수
        context['unit'] = unit

        # 1. 이 계약 건 분양가격
        price, price_build, price_land, price_tax = get_contract_price(contract)

        context['price'] = price if unit else '동호 지정 후 고지'  # 이 건 분양가격
        context['price_build'] = price_build if unit else '-'  # 이 건 건물가
        context['price_land'] = price_land if unit else '-'  # 이 건 대지가
        context['price_tax'] = price_tax if unit else '-'  # 이 건 부가세

        # 2. 정확한 결제 계획 가져오기 (get_contract_payment_plan 사용)
        payment_plan = get_contract_payment_plan(contract)

        # Create amount dictionary from a payment plan for backward compatibility with existing functions
        amount_by_sort = {}
        for plan_item in payment_plan:
            pay_sort = plan_item['installment_order'].pay_sort
            if pay_sort not in amount_by_sort:
                amount_by_sort[pay_sort] = 0
            amount_by_sort[pay_sort] += plan_item['amount']

        # 약정금 누계 계산 (payment_plan 기반)
        context['due_amount'] = sum(plan_item['amount'] for plan_item in payment_plan)

        # 3. 간단 차수 정보 (payment_plan 기반으로 생성)
        context['simple_orders'] = simple_orders = PdfExportPayments.get_simple_orders_from_plan(payment_plan, contract)

        # 4. 납부목록, 완납금액 구하기 (payment_plan 기반)
        paid_dicts, paid_sum_total, calc_sums = PdfExportPayments.get_paid_with_adjustment(contract,
                                                                                           pub_date,
                                                                                           is_calc=calc)
        context['paid_dicts'] = paid_dicts
        context['paid_sum_total'] = paid_sum_total
        context['calc_sums'] = calc_sums
        # ----------------------------------------------------------------

        html_string = render_to_string('pdf/payments_by_contractor.html', context)

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        filename = request.GET.get('filename', 'payments_contractor')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response

    @staticmethod
    def get_simple_orders_from_plan(payment_plan, contract):
        """
        Create simple orders data structure from payment plan
        """
        simple_orders = []
        amount_total = 0

        try:
            calc_start = next((plan['installment_order'].pay_code for plan in payment_plan
                               if
                               plan['installment_order'].is_prep_discount or plan['installment_order'].is_late_penalty),
                              2)
        except StopIteration:
            calc_start = 2

        for plan_item in payment_plan:
            order = plan_item['installment_order']
            amount = plan_item['amount']
            amount_total += amount

            # Get payment_orders QuerySet for due date calculation
            payment_orders = InstallmentPaymentOrder.objects.filter(project=contract.project)

            ord_info = {
                'name': order.alias_name if order.alias_name else order.pay_name,
                'pay_code': order.pay_code,
                'calc_start': calc_start,
                'due_date': get_due_date_per_order(contract, order, payment_orders),
                'amount': amount,
                'amount_total': amount_total,
            }
            simple_orders.append(ord_info)

        return simple_orders

    @staticmethod
    def get_paid_with_adjustment(contract, pub_date, **kwargs):
        """
        payment_adjustment.py를 활용한 납부 내역 및 조정금액 계산

        get_paid_from_plan의 대체 함수로, _utils/payment_adjustment.py의
        표준화된 로직을 사용하여 선납 할인 및 연체 가산금을 계산합니다.

        Args:
            contract: Contract 인스턴스
            pub_date: 발행일자 (기준일)
            **kwargs:
                - is_calc: True면 미납 회차 포함, False면 실제 납부만

        Returns:
            tuple: (paid_dict_list, paid_sum_total, calc_sums)
            - paid_dict_list: 납부 및 미납 상세 내역
            - paid_sum_total: 총 납부액
            - calc_sums: (총 가산금, 총 할인금, 미납 회차 인덱스)
        """
        from _utils.payment_adjustment import (
            get_unpaid_installments,
            get_installment_adjustment_summary
        )
        from itertools import accumulate

        is_calc = kwargs.get('is_calc', False)

        # 1. 실제 납부내역 조회
        paid_list = (
            ProjectCashBook.objects
            .payment_records()
            .filter(
                contract=contract,
                deal_date__lte=pub_date
            )
            .order_by('deal_date', 'id')
        )

        # 2. 납부 누적 금액 계산
        pay_list = [p.income for p in paid_list]
        paid_sum_list = list(accumulate(pay_list))

        # 3. 결과 데이터 구조 초기화
        paid_dict_list = []
        penalty_sum = 0
        discount_sum = 0
        ord_i_list = []  # 미납 회차 인덱스

        # 4. 실제 납부 내역 처리
        for i, (payment, cumulative) in enumerate(zip(paid_list, paid_sum_list)):
            # 회차 정보 가져오기
            installment_order = payment.installment_order
            order_name = installment_order.pay_name if installment_order else None

            # 연체 가산금 계산 (payment_adjustment 사용)
            from _utils.payment_adjustment import calculate_late_penalty
            penalty_info = calculate_late_penalty(payment)

            penalty_amount = penalty_info['penalty_amount'] if penalty_info else 0
            late_days = penalty_info['late_days'] if penalty_info else 0
            penalty_sum += penalty_amount

            paid_dict = {
                'paid': payment,
                'sum': cumulative,
                'order': order_name,
                'diff': 0,  # 실제 납부는 미납금액 0
                'delay_days': late_days,
                'penalty': penalty_amount,
                'discount': 0  # 선납 할인은 회차 완납 시점에만 적용
            }
            paid_dict_list.append(paid_dict)

        # 5. 미납 회차 처리 (is_calc=True일 때만)
        if is_calc:
            unpaid_installments = get_unpaid_installments(contract, pub_date)

            for unpaid_info in unpaid_installments:
                installment = unpaid_info['installment_order']

                # 회차별 조정금액 계산
                adjustment_summary = get_installment_adjustment_summary(contract, installment)

                # 선납 할인 (완납된 경우에만)
                discount_amount = adjustment_summary['total_discount']
                discount_sum += discount_amount

                # 연체 가산금 (미납 회차)
                penalty_amount = 0
                if unpaid_info['is_overdue'] and installment.is_late_penalty:
                    # 미납금액에 대한 연체료 계산
                    penalty_rate = installment.late_penalty_ratio
                    if penalty_rate and penalty_rate > 0:
                        from _utils.payment_adjustment import calculate_daily_interest
                        from decimal import Decimal
                        penalty_amount = calculate_daily_interest(
                            unpaid_info['remaining_amount'],
                            Decimal(str(penalty_rate)),
                            unpaid_info['late_days']
                        )
                        penalty_sum += penalty_amount

                # 미납 회차 정보 저장
                ord_i_list.append(len(paid_dict_list))

                paid_dict = {
                    'paid': {
                        'name': installment.pay_name,
                        'pay_code': installment.pay_code,
                        'due_date': installment.pay_due_date
                    },
                    'sum': 0,  # 미납이므로 0
                    'order': installment.pay_name,
                    'diff': unpaid_info['remaining_amount'],  # 미납금액
                    'delay_days': unpaid_info['late_days'],  # 연체일수
                    'penalty': penalty_amount,
                    'discount': discount_amount
                }
                paid_dict_list.append(paid_dict)

        # 6. 총 납부액
        paid_sum_total = sum(pay_list) if pay_list else 0

        # 7. 결과 반환
        calc_sums = (penalty_sum, discount_sum, ord_i_list)

        return paid_dict_list, paid_sum_total, calc_sums


class PdfExportDailyLateFee(View):
    """일자별 연체료"""

    @staticmethod
    def get(request):
        context = dict()

        # 계약 건 객체
        cont_id = request.GET.get('contract')
        context['contract'] = contract = get_contract(cont_id)

        # 발행일자
        pub_date = request.GET.get('pub_date', None)
        pub_date = datetime.strptime(pub_date, '%Y-%m-%d').date() if pub_date else TODAY
        context['pub_date'] = pub_date

        try:
            unit = contract.key_unit.houseunit
        except ObjectDoesNotExist:
            unit = None

        # 동호수
        context['unit'] = unit

        # # 1. 이 계약 건 분양가격
        # price, price_build, price_land, price_tax = get_contract_price(contract)
        #
        # context['price'] = price if unit else '동호 지정 후 고지'  # 이 건 분양가격
        # context['price_build'] = price_build if unit else '-'  # 이 건 건물가
        # context['price_land'] = price_land if unit else '-'  # 이 건 대지가
        # context['price_tax'] = price_tax if unit else '-'  # 이 건 부가세

        # ----------------------------------------------------------------

        html_string = render_to_string('pdf/daily_late_fee.html', context)

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        filename = request.GET.get('filename', 'daily_late_fee')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response


class PdfExportCalculation(View):
    """선납할인/연체가산 내역서"""

    def get(self, request):
        context = dict()

        project = request.GET.get('project')  # 프로젝트 ID
        # 계약 건 객체
        cont_id = request.GET.get('contract')
        context['contract'] = contract = get_contract(cont_id)

        # 발행일자
        pub_date = request.GET.get('pub_date', None)
        pub_date = datetime.strptime(pub_date, '%Y-%m-%d').date() if pub_date else TODAY
        context['pub_date'] = pub_date

        payment_orders = SpecialPaymentOrder.objects.filter(project=project)  # 전체 납부회차 컬렉션

        try:
            unit = contract.key_unit.houseunit
        except ObjectDoesNotExist:
            unit = None

        # 동호수
        context['unit'] = unit

        # 1. 이 계약 건 분양가격 (계약금, 중도금, 잔금 약정액)
        price, price_build, price_land, price_tax = get_contract_price(contract)

        context['price'] = price if unit else '동호 지정 후 고지'  # 이 건 분양가격
        context['price_build'] = price_build if unit else '-'  # 이 건 건물가
        context['price_land'] = price_land if unit else '-'  # 이 건 대지가
        context['price_tax'] = price_tax if unit else '-'  # 이 건 부가세

        down1 = self.get_down_pay(contract)[0]  # cont_price.down_pay  # 계약금
        down2 = self.get_down_pay(contract)[1]  # cont_price.down_pay  # 계약금
        amount = {'1': down1, '2': down2}

        # 2. 요약 테이블 데이터
        context['due_amount'] = (down1 * 4) + down2  # 약정금 누계

        # 3. 간단 차수 정보
        context['simple_orders'] = simple_orders = get_simple_orders(payment_orders, contract, amount, True)

        # 4. 납부목록, 완납금액 구하기 ------------------------------------------
        paid_dicts, paid_sum_total, calc_sums = get_paid(contract, simple_orders, pub_date,
                                                         is_calc=True, is_past=True)
        context['paid_dicts'] = paid_dicts
        context['paid_sum_total'] = paid_sum_total  # paid_list.aggregate(Sum('income'))['income__sum']  # 기 납부총액
        context['calc_sums'] = calc_sums
        # ----------------------------------------------------------------

        html_string = render_to_string('pdf/calculation_by_contractor.html', context)

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        filename = request.GET.get('filename', 'calculation_contractor')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response

    @staticmethod
    def get_down_pay(contract):
        try:
            down = SpecialDownPay.objects.get(order_group=contract.order_group, unit_type=contract.unit_type)
            return down.payment_amount, down.payment_remain
        except SpecialDownPay.DoesNotExist:
            # 특수 계약금 데이터가 없는 경우 기본값 반환
            return 0, 0
