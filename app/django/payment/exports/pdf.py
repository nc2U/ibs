from datetime import date, datetime
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from _pdf.utils import (get_contract, get_simple_orders, get_due_date_per_order, get_paid)
from _utils.contract_price import get_contract_payment_plan, get_contract_price
from _utils.payment_adjustment import (calculate_all_installments_payment_allocation,
                                       get_installment_adjustment_summary,
                                       calculate_daily_interest, get_unpaid_installments,
                                       calculate_segmented_late_penalty)
from cash.models import ProjectCashBook
from payment.models import InstallmentPaymentOrder, SpecialPaymentOrder, SpecialDownPay

TODAY = date.today()


class PdfExportPayments(View):
    """납부 확인서"""

    @staticmethod
    def get(request):
        context = dict()

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
        context['simple_orders'] = PdfExportPayments.get_simple_orders_from_plan(payment_plan, contract)

        # 4. 납부목록, 완납금액 구하기 (payment_plan 기반)
        paid_dicts, paid_sum_total, calc_sums = PdfExportPayments.get_paid_with_adjustment(contract, pub_date, is_calc=calc)
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
        Create simple orders data structure from the payment plan
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
        회차순 납부 내역 및 조정금액 계산 (우선순위 충당 로직 적용)

        2차 중도금으로 등록된 납부가 1,2차를 모두 충족하면 1,2차 모두 완납 처리됩니다.

        Args:
            contract: Contract 인스턴스
            pub_date: 발행일자 (기준일)
            **kwargs: is_calc (True면 미납 회차 포함)

        Returns:
            tuple: (paid_dict_list, paid_sum_total, calc_sums)
        """

        is_calc = kwargs.get('is_calc', False)

        # 1. 우선순위 충당 계산 - 핵심!
        all_status = calculate_all_installments_payment_allocation(contract)

        # 2. 실제 납부 내역
        paid_payments = ProjectCashBook.objects.payment_records().filter(
            contract=contract,
            deal_date__lte=pub_date
        ).order_by('deal_date', 'id')

        # 3. 표시할 회차 (모든 도래한 회차 + 실제 납부된 회차)
        all_installments = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort
        ).order_by('pay_code', 'pay_time')

        # 도래한 회차 + 계약금(납부기한 없는 회차)
        paid_ids = paid_payments.values_list('installment_order_id', flat=True).distinct()

        # 도래한 회차 또는 납부기한 없는 납부된 회차
        display = all_installments.filter(
            models.Q(pay_due_date__lte=pub_date) |  # pay_due_date 기준 도래
            models.Q(pay_due_date__isnull=True, extra_due_date__lte=pub_date) |  # extra_due_date 기준 도래
            models.Q(pay_due_date__isnull=True, extra_due_date__isnull=True, id__in=paid_ids)  # 계약금
        )

        # 4. 결과 초기화
        result = []
        penalty_total = 0
        discount_total = 0
        unpaid_indices = []
        cumulative = 0

        # 6. 회차별 처리
        for inst in display:
            status = all_status.get(inst.id, {})
            if not status:
                continue

            is_paid = status['is_fully_paid']
            paid_date = status['fully_paid_date']
            promised = status['promised_amount']
            paid = status['paid_amount']
            remaining = status['remaining_amount']

            # Waterfall 기준 지연일수 사용 (이미 계산됨)
            days = status.get('late_days', 0)
            late_amount = status.get('late_payment_amount', 0)

            # 조정금액
            adj = get_installment_adjustment_summary(contract, inst)

            # 연체료 계산 (납부 건별 정확한 계산)
            if not inst.is_late_penalty or not inst.late_penalty_ratio:
                penalty = 0
            else:
                # calculate_segmented_late_penalty 사용: 각 납부 건의 실제 지연일수 반영
                segmented = calculate_segmented_late_penalty(contract, inst, pub_date)
                penalty = segmented['total_penalty']
                # 참고: segmented['segments']에 납부 건별 상세 내역 포함

            # 실제 납부 내역 확인
            payments = paid_payments.filter(installment_order=inst)

            if payments.exists():
                # 실제 납부 존재
                # 미납금액: 지연 완납이면 지연금액, 정상 완납이면 0, 미완납이면 잔액
                if is_paid and days > 0:
                    diff_amount = late_amount  # 지연 완납
                elif is_paid:
                    diff_amount = 0  # 정상 완납
                else:
                    diff_amount = remaining  # 미완납

                # is_late_penalty가 False면 표시값 0으로
                if not inst.is_late_penalty or not inst.late_penalty_ratio:
                    display_days = 0
                    display_diff = 0
                    display_penalty = 0
                else:
                    display_days = days
                    display_diff = diff_amount
                    display_penalty = penalty

                # 분할납부별 지연 정보 매핑
                payment_penalty_map = {}
                if 'late_payment_details' in status:
                    for detail in status['late_payment_details']:
                        # payment_date와 payment_amount로 매핑
                        key = (detail['payment_date'], detail['payment_amount'])
                        payment_penalty_map[key] = {
                            'penalty': detail.get('late_penalty', 0),
                            'late_days': detail.get('late_days', 0),
                            'type': detail.get('type', 'paid_late')
                        }

                total_penalty_added = 0
                for p in payments:
                    cumulative += (p.income or 0)

                    # 해당 payment의 개별 지연 정보 찾기
                    payment_key = (p.deal_date, p.income)
                    individual_penalty_info = payment_penalty_map.get(payment_key, {})

                    individual_penalty = individual_penalty_info.get('penalty', 0)
                    individual_days = individual_penalty_info.get('late_days', 0)

                    # is_late_penalty가 False면 표시값 0으로
                    if not inst.is_late_penalty or not inst.late_penalty_ratio:
                        individual_penalty = 0
                        individual_days = 0
                        individual_diff = 0
                    else:
                        # 지연금액: 해당 payment의 실제 금액만
                        if individual_days > 0:
                            individual_diff = p.income or 0
                        else:
                            individual_diff = 0

                    result.append({
                        'paid': p,
                        'sum': cumulative,
                        'order': inst.pay_name,
                        'installment_order': inst,
                        'paid_amount': p.income,
                        'diff': individual_diff,  # 개별 payment의 지연금액
                        'delay_days': individual_days,  # 개별 지연일수
                        'penalty': individual_penalty,  # 개별 지연가산금
                        'discount': adj['total_discount'] if len(payments) == 1 else 0,  # 할인은 마지막에만
                        'is_fully_paid': is_paid,
                        'promised_amount': promised
                    })

                    total_penalty_added += individual_penalty

                penalty_total += total_penalty_added
                discount_total += adj['total_discount']
            else:
                # 실제 납부 없음
                if not is_paid:  # 미납 시
                    unpaid_indices.append(len(result))

                # 미납금액 결정
                # 1. 지연 완납: 지연 납부된 금액 (연체료 계산 기준)
                # 2. 정상 완납: 0
                # 3. 미완납: 약정금액 전체
                if is_paid and days > 0:
                    diff_amount = late_amount  # 지연 완납
                elif is_paid:
                    diff_amount = 0  # 정상 완납
                else:
                    diff_amount = promised  # 미완납

                # is_late_penalty가 False면 표시값 0으로
                if not inst.is_late_penalty or not inst.late_penalty_ratio:
                    display_days = 0
                    display_diff = 0
                    display_penalty = 0
                else:
                    display_days = days
                    display_diff = diff_amount
                    display_penalty = penalty

                result.append({
                    'paid': None,
                    'sum': cumulative,
                    'order': inst.pay_name,
                    'installment_order': inst,
                    'paid_amount': 0,  # 실납부액 0원
                    'diff': display_diff,  # 표시용
                    'delay_days': display_days,  # 표시용
                    'penalty': display_penalty,  # 표시용
                    'discount': 0,
                    'is_fully_paid': is_paid,
                    'promised_amount': promised
                })
                penalty_total += display_penalty

        return result, cumulative, (penalty_total, discount_total, unpaid_indices)


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
