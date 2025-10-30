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
        paid_dicts, paid_sum_total, calc_sums = PdfExportPayments.get_paid_from_plan(contract, simple_orders, pub_date,
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
    def get_paid_from_plan(contract, simple_orders, pub_date, **kwargs):
        """
        Calculate paid amounts using payment plan data structure
        """
        calc_start_pay_code = simple_orders[0].get('calc_start')
        paid_list = ProjectCashBook.objects.filter(
            income__isnull=False,
            project_account_d3__is_payment=True,
            contract=contract,
            deal_date__lte=pub_date
        ).order_by('deal_date', 'id')

        is_past = True if kwargs.get('is_past') else False
        paid_list = paid_list.filter(installment_order__pay_sort='1') if is_past else paid_list

        pay_list = [p.income for p in paid_list]
        paid_sum_list = list(accumulate(pay_list))

        zip_pay_list = list(zip(paid_list, paid_sum_list))

        def get_date(item):
            return item[0].deal_date if isinstance(item, tuple) else item['due_date']

        calc_orders = [item for item in simple_orders
                       if item.get('pay_code', 0) >= calc_start_pay_code
                       and is_due(get_due_date_per_order(contract, item, simple_orders))]

        calc_orders = calc_orders if kwargs.get('is_calc', None) else []

        combined = zip_pay_list + calc_orders
        sorted_combined = sorted(combined, key=get_date)

        ord_list = []
        ord_i_list = []
        paid_dict_list = []
        first_date = None

        curr_paid_total = 0
        curr_pay_code = 0
        is_first_pre = True
        curr_amt_total = 0
        penalty_sum = 0
        discount_sum = 0

        for i, paid in enumerate(sorted_combined):
            if i == 0:
                try:
                    first_date = paid[0].deal_date
                except (KeyError, AttributeError):
                    pass

            try:
                pre_date = sorted_combined[i - 1][0].deal_date \
                    if isinstance(sorted_combined[i - 1], tuple) \
                    else sorted_combined[i - 1].get('due_date', None)
                next_date = sorted_combined[i + 1][0].deal_date \
                    if isinstance(sorted_combined[i + 1], tuple) \
                    else sorted_combined[i + 1].get('due_date', None)
            except IndexError:
                pre_date = first_date
                next_date = pub_date

            if is_past and contract.sup_cont_date:
                next_date = next_date if contract.sup_cont_date >= next_date else contract.sup_cont_date

            if isinstance(paid, tuple):
                curr_paid_total = paid[1]

                paid_ords = [o for o in list(filter(lambda o: o['amount_total'] <= curr_paid_total, simple_orders))]

                paid_pay_code = paid_ords[-1]['pay_code'] if paid_ords else 0
                paid_ord_name = paid_ords[-1]['name'] if paid_ords else None

                paid_ord_name = paid_ord_name if paid_ord_name not in ord_list else None
                ord_list.append(paid_ord_name)

                if curr_amt_total == 0 and paid_pay_code >= calc_start_pay_code:
                    curr_amt_total = paid_ords[-1]['amount_total'] if paid_ords else None

                if curr_paid_total > curr_amt_total:
                    if is_first_pre:
                        diff = curr_amt_total - curr_paid_total \
                            if paid_pay_code and paid_pay_code >= calc_start_pay_code else 0
                        diff = diff if paid[0].deal_date > contract.contractor.contract_date else 0
                        if paid_pay_code >= calc_start_pay_code:
                            is_first_pre = False
                    else:
                        diff = -paid[0].income

                    try:
                        code = calc_start_pay_code if curr_pay_code == 0 else curr_pay_code + 1
                        next_due_date = [o['due_date'] for o in simple_orders if o.get('pay_code', 0) == code][0]
                    except IndexError:
                        next_due_date = simple_orders[-1]['due_date']

                    prepay_days = (paid[0].deal_date - next_due_date).days

                    buffer_days = 30
                    diff = diff if prepay_days < -buffer_days else 0

                    delay_days = (paid[0].deal_date - pre_date).days \
                        if ord_i_list and ord_i_list[0] < i else 0
                else:
                    diff = curr_amt_total - curr_paid_total
                    if paid_pay_code >= calc_start_pay_code:
                        is_first_pre = True
                    prepay_days = (pre_date - paid[0].deal_date).days \
                        if ord_i_list and ord_i_list[0] < i and diff else 0
                    delay_days = (next_date - paid[0].deal_date).days \
                        if ord_i_list and ord_i_list[0] < i and diff else 0

                days = prepay_days if diff < 0 else delay_days
                days = days if diff else 0

                calc = get_late_fee(contract.project, diff, days, is_past)

                penalty = calc if diff > 0 else 0
                discount = calc if diff < 0 else 0

                penalty_sum += penalty
                discount_sum += discount
                paid_dict = {'paid': paid[0], 'sum': curr_paid_total, 'order': paid_ord_name, 'diff': diff,
                             'delay_days': days,
                             'penalty': penalty,
                             'discount': discount}
                paid_dict_list.append(paid_dict)
            else:
                ord_i_list.append(i)
                curr_pay_code = paid['pay_code'] if paid else 0
                curr_amt_total = paid['amount_total']

                diff = curr_amt_total - curr_paid_total if is_first_pre else 0
                is_first_pre = True

                days = (next_date - paid['due_date']).days if diff else 0
                days = days if diff > 0 else days * -1

                calc = get_late_fee(contract.project, diff, days, is_past)

                penalty = calc if diff > 0 else 0
                discount = calc if diff < 0 else 0

                penalty_sum += penalty
                discount_sum += discount
                paid_dict = {
                    'paid': paid,
                    'sum': 0,
                    'order': paid['name'],
                    'diff': diff,
                    'delay_days': days,
                    'penalty': penalty,
                    'discount': discount,
                }
                paid_dict_list.append(paid_dict)

        paid_sum_total = paid_list.aggregate(Sum('income'))['income__sum']
        paid_sum_total = paid_sum_total if paid_sum_total else 0
        calc_sums = (penalty_sum, discount_sum, ord_i_list)

        return paid_dict_list, paid_sum_total, calc_sums


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