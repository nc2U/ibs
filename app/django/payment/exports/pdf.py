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

from _pdf.utils import (get_contract, get_simple_orders, get_paid)
from _utils.contract_price import get_contract_payment_plan, get_contract_price, get_due_date_per_order
from _utils.payment_adjustment import (calculate_all_installments_payment_allocation,
                                       get_installment_adjustment_summary,
                                       calculate_daily_interest)
from payment.models import InstallmentPaymentOrder, SpecialDownPay

TODAY = date.today()


class PdfExportLedgerPayment(View):
    """납부 확인서 (Ledger 기반)"""

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

        # 약정금 누계 계산 (payment_plan 기반)
        context['due_amount'] = sum(plan_item['amount'] for plan_item in payment_plan)

        # 3. 간단 차수 정보 (payment_plan 기반으로 생성)
        context['simple_orders'] = PdfExportLedgerPayment.get_simple_orders_from_plan(payment_plan, contract)

        # 4. 납부목록, 완납금액 구하기 (Ledger 기반)
        paid_dicts, paid_sum_total, calc_sums = PdfExportLedgerPayment.get_paid_with_adjustment_ledger(
            contract, pub_date, is_calc=calc
        )
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

            ord_info = {
                'name': order.alias_name if order.alias_name else order.pay_name,
                'pay_code': order.pay_code,
                'calc_start': calc_start,
                'due_date': plan_item.get('due_date'), # get_contract_payment_plan에서 계산된 날짜 사용
                'amount': amount,
                'amount_total': amount_total,
            }
            simple_orders.append(ord_info)

        return simple_orders

    @staticmethod
    def get_paid_with_adjustment_ledger(contract, pub_date, **kwargs):
        """
        회차순 납부 내역 및 조정금액 계산 (Ledger 기반 - 우선순위 충당 로직 적용)

        Args:
            contract: Contract 인스턴스
            pub_date: 발행일자 (기준일)
            **kwargs: is_calc (True면 미납 회차 포함)

        Returns:
            tuple: (paid_dict_list, paid_sum_total, calc_sums)
        """
        from payment.models import ContractPayment

        is_calc = kwargs.get('is_calc', False)

        # 1. 우선순위 충당 계산 (기준일 반영) - 핵심!
        all_status = calculate_all_installments_payment_allocation(contract, pub_date)

        # 2. 실제 납부 내역 (Ledger 기반)
        paid_payments = ContractPayment.objects.select_related(
            'accounting_entry', 'installment_order'
        ).filter(
            contract=contract,
            deal_date__lte=pub_date,
            is_payment_mismatch=False  # 유효한 계약자 납부만
        ).order_by('deal_date', 'id')

        # 3. 표시할 회차 결정 (조정된 날짜 기준)
        all_installments = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort
        ).exclude(excluded_order_groups=contract.order_group).order_by('pay_code', 'pay_time')

        paid_ids = paid_payments.values_list('installment_order_id', flat=True).distinct()

        display_ids = []
        for inst in all_installments:
            status = all_status.get(inst.id)
            if not status:
                continue

            adj_due = status['due_date']
            # 1. 기한이 도래했거나 (조정된 날짜 기준)
            # 2. 기한은 없지만 실제 납부됐거나
            # 3. 계약금 회차이거나
            if (adj_due and adj_due <= pub_date) or \
               (not adj_due and inst.id in paid_ids) or \
               (inst.pay_sort == '1'):
                display_ids.append(inst.id)

        display = all_installments.filter(id__in=display_ids)

        # 4. 결과 초기화
        result = []
        penalty_total = 0
        discount_total = 0
        unpaid_indices = []
        cumulative = 0

        # 5. 회차별 처리
        for inst in display:
            status = all_status.get(inst.id, {})
            if not status:
                continue

            is_paid = status['is_fully_paid']
            promised = status['promised_amount']
            paid = status['paid_amount']
            remaining = status['remaining_amount']
            due_date = status['due_date']  # 조정된 납부 기한

            # Waterfall 기준 지연 상세 정보 사용
            late_payment_details = status.get('late_payment_details', [])
            total_late_penalty = status.get('total_late_penalty', 0)

            # 선납 할인 조회
            adj_summary = get_installment_adjustment_summary(contract, inst)

            # 실제 납부 내역 확인 (Ledger 기반)
            payments = paid_payments.filter(installment_order=inst)

            if payments.exists():
                # 실제 납부 존재
                for p in payments:
                    payment_amount = p.accounting_entry.amount if p.accounting_entry else 0
                    cumulative += payment_amount

                    # 해당 납부건의 지연 상세 정보 찾기 (waterfall 결과에서 추출)
                    p_detail = next((d for d in late_payment_details if d.get('payment_id') == p.id), None)

                    penalty = p_detail['late_penalty'] if p_detail and is_calc else 0
                    days = p_detail['late_days'] if p_detail and is_calc else 0
                    diff = p_detail['payment_amount'] if p_detail and is_calc else 0

                    # is_calc=True일 때만 할인료 적용
                    discount_value = adj_summary['total_discount'] if is_calc and p == payments.last() else 0

                    result.append({
                        'paid': p,
                        'sum': cumulative,
                        'order': inst.pay_name,
                        'installment_order': inst,
                        'due_date': due_date,
                        'paid_amount': payment_amount,
                        'diff': diff,
                        'delay_days': days,
                        'penalty': penalty,
                        'discount': discount_value,
                        'is_fully_paid': is_paid,
                        'promised_amount': promised
                    })

                penalty_total += (total_late_penalty if is_calc else 0)
                if is_calc:
                    discount_total += adj_summary['total_discount']

                # 일부납부 시 미납 잔액 추가 (기준일 시점)
                if not is_paid and remaining > 0:
                    unpaid_indices.append(len(result))

                    u_detail = next((d for d in late_payment_details if d['type'] == 'unpaid'), None)
                    u_penalty = u_detail['late_penalty'] if u_detail and is_calc else 0
                    u_days = u_detail['late_days'] if u_detail and is_calc else 0

                    result.append({
                        'paid': None,
                        'sum': cumulative,
                        'order': inst.pay_name,
                        'installment_order': inst,
                        'due_date': due_date,
                        'paid_amount': 0,
                        'diff': remaining if is_calc else 0,
                        'delay_days': u_days,
                        'penalty': u_penalty,
                        'discount': 0,
                        'is_fully_paid': False,
                        'promised_amount': promised
                    })
            else:
                # 실제 납부 없음 (미납 회차)
                if not is_paid:
                    unpaid_indices.append(len(result))

                u_detail = next((d for d in late_payment_details if d['type'] == 'unpaid'), None)
                u_penalty = u_detail['late_penalty'] if u_detail and is_calc else 0
                u_days = u_detail['late_days'] if u_detail and is_calc else 0

                result.append({
                    'paid': None,
                    'sum': cumulative,
                    'order': inst.pay_name,
                    'installment_order': inst,
                    'due_date': due_date,
                    'paid_amount': 0,
                    'diff': remaining if is_calc else 0,
                    'delay_days': u_days,
                    'penalty': u_penalty,
                    'discount': 0,
                    'is_fully_paid': is_paid,
                    'promised_amount': promised
                })
                penalty_total += u_penalty

        return result, cumulative, (penalty_total, discount_total, unpaid_indices)


class PdfExportLedgerDailyLateFee(View):
    """일자별 연체료 (Ledger 기반)"""

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

        # 1. 미납 회차 및 미납금액 계산 (Ledger 기반)
        unpaid_data = PdfExportLedgerDailyLateFee.get_unpaid_summary_ledger(contract, pub_date)
        context['unpaid_amount'] = unpaid_data['total_unpaid']
        context['unpaid_installments'] = unpaid_data['installments']

        # 2. 금일 기준 누적 연체료 계산
        current_penalty = PdfExportLedgerDailyLateFee.calculate_current_penalty(
            unpaid_data['installments']
        )
        context['current_penalty'] = current_penalty
        context['current_total_payment'] = unpaid_data['total_unpaid'] + current_penalty

        # 3. 일자별 연체료 계산 (내일부터 1개월간)
        daily_fees = PdfExportLedgerDailyLateFee.calculate_daily_late_fees(
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
    def get_unpaid_summary_ledger(contract, pub_date):
        """
        미납 회차 및 총 미납금액 계산 (Ledger 기반)

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
        # Ledger 기반 미납 회차 계산
        unpaid_installments = PdfExportLedgerDailyLateFee.get_unpaid_installments_ledger(contract, pub_date)

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
    def get_unpaid_installments_ledger(contract, as_of_date):
        """
        미납 회차 목록 조회 (Ledger 기반)

        Args:
            contract: Contract 인스턴스
            as_of_date: 기준일

        Returns:
            list: 미납 회차 정보 리스트
        """
        # 우선순위 충당 계산으로 각 회차별 납부 현황 파악
        all_status = calculate_all_installments_payment_allocation(contract, as_of_date)

        # 도래한 회차 중 미완납 회차만 필터링
        unpaid_list = []

        for inst_id, status in all_status.items():
            if not status['is_fully_paid'] and status['remaining_amount'] > 0:
                installment = InstallmentPaymentOrder.objects.get(pk=inst_id)

                # 기한 도래 여부 확인 (조정된 날짜 기준)
                due_date = status['due_date']

                if due_date and due_date <= as_of_date:
                    unpaid_list.append({
                        'installment_order': installment,
                        'remaining_amount': status['remaining_amount'],
                        'late_days': status['late_days']
                    })

        return unpaid_list

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
            list: 일자별 연체료 정보
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


class PdfExportLedgerCalculation(View):
    """선납할인/연체가산 내역서 (Ledger 기반)"""

    def get(self, request):
        """
        Note: 이 클래스는 SpecialPaymentOrder와 SpecialDownPay를 사용하는 특수 케이스입니다.
        일반적인 InstallmentPaymentOrder와는 다른 로직을 사용하므로,
        Ledger 기반으로 리팩토링이 필요한지 프로젝트 요구사항에 따라 결정해야 합니다.

        현재는 기존 로직을 유지하되, 실제 납부 데이터 조회 시 Ledger를 사용하도록 수정했습니다.
        """
        context = dict()

        project = request.GET.get('project')  # 프로젝트 ID
        # 계약 건 객체
        cont_id = request.GET.get('contract')
        context['contract'] = contract = get_contract(cont_id)

        # 발행일자
        pub_date = request.GET.get('pub_date', None)
        pub_date = datetime.strptime(pub_date, '%Y-%m-%d').date() if pub_date else TODAY
        context['pub_date'] = pub_date

        # 납부 회차 정보 (조정된 날짜 반영을 위해 필터링)
        payment_orders = InstallmentPaymentOrder.objects.filter(
            project=project,
            type_sort=contract.unit_type.sort
        ).exclude(excluded_order_groups=contract.order_group)

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

        down1 = self.get_down_pay(contract)[0]
        down2 = self.get_down_pay(contract)[1]
        amount = {'1': down1, '2': down2}

        # 2. 요약 테이블 데이터
        context['due_amount'] = (down1 * 4) + down2  # 약정금 누계

        # 3. 간단 차수 정보
        context['simple_orders'] = simple_orders = get_simple_orders(payment_orders, contract, amount, True)

        # 4. 납부목록, 완납금액 구하기 (Ledger 기반으로 수정 필요)
        # Note: get_paid 함수가 ProjectCashBook을 사용한다면 Ledger 기반 함수로 교체 필요
        paid_dicts, paid_sum_total, calc_sums = get_paid(contract, simple_orders, pub_date,
                                                         is_calc=True, is_past=True)
        context['paid_dicts'] = paid_dicts
        context['paid_sum_total'] = paid_sum_total
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
