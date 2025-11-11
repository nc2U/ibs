from datetime import date, datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from _pdf.utils import (get_contract, get_simple_orders, get_due_date_per_order,
                        get_paid)
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
        회차순 납부 내역 및 조정금액 계산

        모든 기도래 회차를 순서대로 나열하고, 각 회차별로 납부 상태를 표시합니다.

        Args:
            contract: Contract 인스턴스
            pub_date: 발행일자 (기준일)
            **kwargs:
                - is_calc: True면 미납 회차 포함, False면 실제 납부만

        Returns:
            tuple: (paid_dict_list, paid_sum_total, calc_sums)
            - paid_dict_list: 회차순 납부 상세 내역
            - paid_sum_total: 총 납부액
            - calc_sums: (총 가산금, 총 할인금, 미납 회차 인덱스)
        """
        from _utils.payment_adjustment import (
            get_installment_adjustment_summary,
            calculate_installment_paid_status_with_priority
        )
        from payment.models import InstallmentPaymentOrder
        from itertools import accumulate
        from django.db import models

        is_calc = kwargs.get('is_calc', False)

        # 1. 실제 납부 내역 조회
        paid_payments = (
            ProjectCashBook.objects
            .payment_records()
            .filter(
                contract=contract,
                deal_date__lte=pub_date
            )
            .order_by('deal_date', 'id')
        )

        # 2. 모든 회차 조회 (납부내역이 있거나 기도래한 회차)
        all_installments = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort
        ).order_by('pay_code', 'pay_time')

        # 납부 내역이 있는 회차들 확인
        paid_installment_ids = paid_payments.values_list('installment_order_id', flat=True).distinct()

        # 표시할 회차: 기도래 OR 납부내역이 있는 회차
        display_installments = all_installments.filter(
            models.Q(pay_due_date__lte=pub_date) |
            models.Q(id__in=paid_installment_ids)
        )

        # 3. 결과 데이터 구조 초기화
        paid_dict_list = []
        penalty_sum = 0
        discount_sum = 0
        ord_i_list = []  # 미납 회차 인덱스
        cumulative_paid = 0

        # 4. 각 회차별 처리 (순서대로) - 간단한 로직 사용
        for installment in display_installments:
            from _utils.simple_late_payment import calculate_simple_late_payment, calculate_late_penalty

            # 간단한 지연납부 정보 계산
            late_info = calculate_simple_late_payment(contract, installment)

            # 회차별 조정금액 계산
            adjustment_summary = get_installment_adjustment_summary(contract, installment)

            if late_info['is_fully_paid']:
                # === 완납된 회차 ===
                late_days = late_info['late_days']
                late_payment_amount = late_info['late_payment_amount']

                # 연체료 계산
                penalty_amount = calculate_late_penalty(
                    contract, installment, late_payment_amount, late_days
                )

                # 해당 회차의 실제 납부 내역들 가져오기
                installment_payments = paid_payments.filter(installment_order=installment)

                # 실제 납부 내역이 있는 경우
                if installment_payments.exists():
                    for payment in installment_payments:
                        payment_income = payment.income or 0
                        cumulative_paid += payment_income

                        paid_dict = {
                            'paid': payment,
                            'sum': cumulative_paid,
                            'order': installment.pay_name,
                            'installment_order': installment,
                            'paid_amount': late_payment_amount if late_payment_amount > 0 else payment_income,
                            'diff': 0,  # 완납된 회차이므로 미납액 0
                            'delay_days': late_days,
                            'penalty': penalty_amount,
                            'discount': adjustment_summary['total_discount'],
                            'is_fully_paid': True,
                            'promised_amount': late_info['promised_amount'],
                            'is_late_payment': late_payment_amount > 0
                        }
                        paid_dict_list.append(paid_dict)
                else:
                    # 후납 충당으로만 완납된 회차 (실제 납부 없음)
                    if late_payment_amount > 0:  # 지연납부가 있는 경우만
                        cumulative_paid += late_info['promised_amount']

                        paid_dict = {
                            'paid': {
                                'name': f"{installment.pay_name} (후납충당)",
                                'deal_date': date.today(),  # 임시
                                'income': late_payment_amount
                            },
                            'sum': cumulative_paid,
                            'order': f"{installment.pay_name} (후납충당)",
                            'installment_order': installment,
                            'paid_amount': late_payment_amount,
                            'diff': 0,
                            'delay_days': late_days,
                            'penalty': penalty_amount,
                            'discount': adjustment_summary['total_discount'],
                            'is_fully_paid': True,
                            'promised_amount': late_info['promised_amount'],
                            'is_late_payment': True,
                            'is_allocated': True
                        }
                        paid_dict_list.append(paid_dict)

                # 가산금/할인금 누계
                penalty_sum += penalty_amount
                discount_sum += adjustment_summary['total_discount']

            else:
                # === 미납 회차 ===
                if is_calc:  # is_calc=True일 때만 미납 회차 표시
                    ord_i_list.append(len(paid_dict_list))

                    # 간단한 미납 정보 계산
                    late_days = late_info['late_days']
                    remaining_amount = late_info['promised_amount'] - late_info['total_paid']

                    # 해당 회차의 부분 납부가 있었는지 확인
                    installment_payments = paid_payments.filter(installment_order=installment)
                    actual_paid = late_info['total_paid']

                    if actual_paid > 0:
                        cumulative_paid += actual_paid

                    # 연체료 계산
                    penalty_amount = calculate_late_penalty(
                        contract, installment, remaining_amount, late_days
                    )

                    paid_dict = {
                        'paid': {
                            'name': installment.pay_name,
                            'pay_code': installment.pay_code,
                            'due_date': installment.pay_due_date,
                            'income': actual_paid  # 부분 납부 금액
                        },
                        'sum': cumulative_paid,
                        'order': installment.pay_name,
                        'installment_order': installment,
                        'paid_amount': actual_paid,
                        'diff': remaining_amount,  # 미납금액
                        'delay_days': late_days,
                        'penalty': penalty_amount,
                        'discount': 0,  # 미납 회차는 할인 없음
                        'is_fully_paid': False,
                        'promised_amount': late_info['promised_amount']
                    }
                    paid_dict_list.append(paid_dict)

                    penalty_sum += penalty_amount

        # 5. 총 납부액
        paid_sum_total = cumulative_paid

        # 6. 결과 반환
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

        # 1. 미납 회차 및 미납금액 계산
        unpaid_data = PdfExportDailyLateFee.get_unpaid_summary(contract, pub_date)
        context['unpaid_amount'] = unpaid_data['total_unpaid']
        context['unpaid_installments'] = unpaid_data['installments']

        # 2. 금일 기준 누적 연체료 계산
        current_penalty = PdfExportDailyLateFee.calculate_current_penalty(
            unpaid_data['installments']
        )
        context['current_penalty'] = current_penalty
        context['current_total_payment'] = unpaid_data['total_unpaid'] + current_penalty

        # 3. 일자별 연체료 계산 (내일부터 1개월간)
        daily_fees = PdfExportDailyLateFee.calculate_daily_late_fees(
            unpaid_data['total_unpaid'],
            unpaid_data['penalty_rate'],
            pub_date,
            current_penalty
        )
        context['daily_fees'] = daily_fees

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

    @staticmethod
    def get_unpaid_summary(contract, pub_date):
        """
        미납 회차 및 총 미납금액 계산

        Args:
            contract: Contract 인스턴스
            pub_date: 기준일

        Returns:
            dict: {
                'total_unpaid': int,           # 총 미납금액
                'installments': list,          # 미납 회차 상세 정보
                'penalty_rate': Decimal        # 연체료율 (가장 높은 값)
            }
        """
        from _utils.payment_adjustment import get_unpaid_installments
        from decimal import Decimal

        unpaid_installments = get_unpaid_installments(contract, pub_date)

        total_unpaid = 0
        installment_details = []
        max_penalty_rate = Decimal('0')

        for unpaid_info in unpaid_installments:
            installment = unpaid_info['installment_order']
            remaining = unpaid_info['remaining_amount']
            total_unpaid += remaining

            # 연체료율 중 최대값 찾기
            if installment.is_late_penalty and installment.late_penalty_ratio:
                penalty_rate = Decimal(str(installment.late_penalty_ratio))
                if penalty_rate > max_penalty_rate:
                    max_penalty_rate = penalty_rate

            installment_details.append({
                'order_name': installment.pay_name,
                'due_date': installment.pay_due_date,
                'remaining_amount': remaining,
                'late_days': unpaid_info['late_days'],
                'penalty_rate': installment.late_penalty_ratio if installment.is_late_penalty else None
            })

        return {
            'total_unpaid': total_unpaid,
            'installments': installment_details,
            'penalty_rate': max_penalty_rate
        }

    @staticmethod
    def calculate_current_penalty(installment_details):
        """
        금일 기준 누적 연체료 계산

        Args:
            installment_details: 미납 회차 상세 정보 리스트

        Returns:
            int: 금일 기준 총 누적 연체료
        """
        from _utils.payment_adjustment import calculate_daily_interest
        from decimal import Decimal

        total_penalty = 0

        for inst in installment_details:
            if inst['penalty_rate'] and inst['late_days'] > 0:
                penalty = calculate_daily_interest(
                    inst['remaining_amount'],
                    Decimal(str(inst['penalty_rate'])),
                    inst['late_days']
                )
                total_penalty += penalty

        return total_penalty

    @staticmethod
    def calculate_daily_late_fees(unpaid_amount, annual_rate, start_date, current_penalty=0):
        """
        일자별 연체료 계산 (내일부터 1개월간)

        Args:
            unpaid_amount: 미납금액
            annual_rate: 연이율 (%)
            start_date: 시작일 (금일)
            current_penalty: 금일 기준 누적 연체료

        Returns:
            list: [{
                'date': date,              # 날짜
                'days': int,               # 경과 일수
                'penalty_rate': str,       # 연체율 (표시용)
                'daily_penalty': int,      # 당일 연체료
                'cumulative_penalty': int, # 누적 연체료
                'total_payment': int       # 납부금액 (미납금액 + 누적연체료)
            }, ...]
        """
        from _utils.payment_adjustment import calculate_daily_interest
        from datetime import timedelta

        if unpaid_amount <= 0 or annual_rate <= 0:
            return []

        daily_fees = []
        cumulative_penalty = current_penalty  # 금일 기준 누적 연체료부터 시작

        # 내일부터 1개월(30일) 동안의 일자별 계산
        for day in range(1, 31):
            current_date = start_date + timedelta(days=day)

            # 당일 연체료 계산
            daily_penalty = calculate_daily_interest(
                unpaid_amount,
                annual_rate,
                1  # 1일
            )

            cumulative_penalty += daily_penalty
            total_payment = unpaid_amount + cumulative_penalty

            daily_fees.append({
                'date': current_date,
                'days': day,
                'penalty_rate': f"{annual_rate}%",
                'daily_penalty': daily_penalty,
                'cumulative_penalty': cumulative_penalty,
                'total_payment': total_payment
            })

        return daily_fees


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
