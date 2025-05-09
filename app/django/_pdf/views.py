from datetime import date, datetime, timedelta
from itertools import accumulate
# --------------------------------------------------------
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from cash.models import ProjectCashBook
from contract.models import Contract
from notice.models import SalesBillIssue
from payment.models import (InstallmentPaymentOrder, OverDueRule,
                            SpecialPaymentOrder, SpecialDownPay, SpecialOverDueRule)

TODAY = date.today()


def get_contract(cont_id):
    """ ■ 계약 가져오기
    :param cont_id: 계약자 아이디
    :return object(contract: 계약 건):
    """
    return Contract.objects.get(pk=cont_id)


def get_simple_orders(payment_orders, contract, amount, is_past=False):
    """
    :: 약식 납부회차 구하기
    :param payment_orders:
    :param contract:
    :param amount:
    :param is_past: 종전 선납/연체 계산 여부
    :return: dict 형식 납부회차 리스트
    """
    simple_orders = []

    amount_total = 0
    try:
        calc_start = payment_orders.filter(Q(is_prep_discount=True)|Q(is_late_penalty=True)).first().pay_code
    except AttributeError:
        calc_start = 2
    for order in payment_orders:
        if is_past:
            amt = amount['1'] if order.pay_code < 5 else amount['2']
        else:
            amt = amount[order.pay_sort]
        amount_total += amt  # 회차별 약정금 누계
        ord_info = {
            'name': order.alias_name if order.alias_name else order.pay_name,  # 회차별 별칭
            'pay_code': order.pay_code,
            'calc_start': calc_start,
            'due_date': get_due_date_per_order(contract, order, payment_orders),  # 회차별 납부기한
            'amount': amt,  # 회차별 약정금
            'amount_total': amount_total,  # 회차별 약정금 누계
        }
        simple_orders.append(ord_info)

    return simple_orders


def get_due_amount(payment_orders, contract, amount):
    """
    :: 약정금 누계 계산 함수
    :param payment_orders: 전체 납부회차 쿼리셋
    :param contract: contract 객체
    :param amount: {'1': down, '2': middle, '3': remain}
    :return: int 현재 회차까지 납부 약정액 합계
    """
    total_amounts = 0
    # 약정회차 리스트
    due_orders = get_due_orders(contract, payment_orders)
    for order in due_orders:
        total_amounts += amount[order.pay_sort]
    return total_amounts


def is_due(due_date):
    """
    :: 주어진 날짜가 기도래 납부기한에 해당하는지 여부
    :param due_date:
    :return: bool -> 기도래 기한 여부
    """
    return due_date and due_date <= TODAY


def get_due_date_per_order(contract, order, payment_orders):
    """
    :: 회차 별 납부 일자 구하기
    :param contract: 계약자 객체
    :param order: 납부 회차 객체
    :param payment_orders: 납부 회차 컬렉션
    :return str(due_date): 회차 별 약정 납부 일자
    """

    cont_date = contract.contractor.contract_date  # 계약일 (default 납부기한 = 계약일)
    due_date = cont_date

    if type(order) is dict and order.get('pay_code') >= 2:
        due_date = order.get('due_date', None)
    elif order.pay_code >= 2:
        si_date = order.days_since_prev
        pd_date = order.pay_due_date
        ed_date = order.extra_due_date

        due_date = cont_date + timedelta(days=si_date) if si_date else ed_date or pd_date

        if order.pay_code >= 3:
            pre_ords = payment_orders.filter(pay_code__lt=order.pay_code)
            pre_si = pre_ords.aggregate(total=Sum('days_since_prev'))['total']
            si_due = cont_date + timedelta(days=pre_si) if pre_si else cont_date

            due = ed_date or pd_date
            if not due:
                due_date = None
            else:
                due_date = due if due > si_due else si_due

    return due_date


def get_due_orders(contract, payment_orders):
    """
    :: 오늘 날짜 기준 기도래 납부 회차 객체 리스트 구하기
    :param contract: 
    :param payment_orders:
    :return: list -> 납부회차 객체
    """
    return [o for o in payment_orders if is_due(get_due_date_per_order(contract, o, payment_orders))]


def get_late_fee(project, late_amt, days, is_past=False):
    """
    :: 회차별 지연 가산금 계산 함수
    :param project: 프로젝트
    :param late_amt: 지연금액
    :param days: 지연일수
    :param is_past: 종전 선납/연체 계산 여부
    :return int(floor_fee: 가산금), str(적용 이자율):
    """

    if not is_past:
        rules = OverDueRule.objects.filter(project=project)
    else:
        rules = SpecialOverDueRule.objects.filter(project=project)

    calc_fee = 0
    calc_days = 0

    for rule in rules:
        start = rule.term_start
        end = rule.term_end
        rate = rule.rate_year / 100

        if start is None and end is None:  # 단일 가산율 적용인 경우
            return int(late_amt * days * rate / 365)

        elif start is None and end is not None:  # 선납 률이 규정 되어 있는 경우
            if days <= 0:  # 선납인 경우
                return int(late_amt * days * rate / 365)
            else:
                pass

        elif start is not None and end is not None:  # 특정 기간 동안 연체인 경우

            if start == 1:  # 연체 시작 구간일 경우
                if days <= end:
                    return int(late_amt * days * rate / 365)
                else:
                    calc_fee += late_amt * end * rate / 365
                    calc_days = end
            else:  # 연체 진행 구간일 경우
                if days <= end:
                    return int(calc_fee + (late_amt * (days - calc_days) * rate / 365))
                else:
                    calc_fee += late_amt * (end - calc_days) * rate / 365
                    calc_days = end

        elif start is not None and end is None:  # 특정 기간 이상 연체인 경우
            return int(calc_fee + (late_amt * (days - calc_days) * rate / 365))


def get_paid(contract: Contract, simple_orders, pub_date, **kwargs):
    """
    :: ■ 기 납부금액 구하기
    :param contract: 계약정보
    :param simple_orders: 회차정보
    :param pub_date: 발행일자
    :param kwargs: is_calc => True - 일반용 / False - 확인용 / is_past => 변경 약정에 의한 가산금 산출 여부
    :return list(paid_list: { 납부 건 딕셔너리 }), int(paid_sum_total: 납부 총액):
    """

    calc_start_pay_code = simple_orders[0].get('calc_start')  # 연체/가산 적용 시작 회차 코드
    paid_list = ProjectCashBook.objects.filter(
        income__isnull=False,
        project_account_d3__in=(1, 4),  # 분(부)담금 or 분양수입금
        contract=contract,
        deal_date__lte=pub_date
    ).order_by('deal_date', 'id')  # 해당 계약 건 납부 데이터

    is_past = True if kwargs.get('is_past') else False
    paid_list = paid_list.filter(installment_order__pay_sort='1') if is_past else paid_list

    pay_list = [p.income for p in paid_list]  # 입금액 추출 리스트
    paid_sum_list = list(accumulate(pay_list))  # 입금액 리스트를 시간 순 누계액 리스트로 변경

    zip_pay_list = list(zip(paid_list, paid_sum_list))

    def get_date(item):
        return item[0].deal_date if isinstance(item, tuple) else item['due_date']

    # 선납/할인 적용 시작 회차부터 현재 납부 의무 회차까지
    calc_orders = [item for item in simple_orders
                   if item.get('pay_code', 0) >= calc_start_pay_code
                   and is_due(get_due_date_per_order(contract, item, simple_orders))]

    calc_orders = calc_orders if kwargs.get('is_calc', None) else []  # 일반용일 경우에만 적용

    combined = zip_pay_list + calc_orders
    sorted_combined = sorted(combined, key=get_date)

    ord_list = []  # 완납 회차 별칭 리스트
    ord_i_list = []  # 납부 내역 중 약정회차 순차 삽입 index 리스트
    paid_dict_list = []  # 메인 데이타 딕셔너리 리스트
    first_date = None  # 첫 번째 납입 일자

    curr_paid_total = 0  # 납부 금액 합계
    curr_pay_code = 0  # 현재 약정 코드
    is_first_pre = True
    curr_amt_total = 0  # 약정 금액 합계
    penalty_sum = 0  # 가산금 합계
    discount_sum = 0  # 할인금 합계

    for i, paid in enumerate(sorted_combined):  # 입금액 리스트를 순회
        if i == 0:
            try:
                first_date = paid[0].deal_date
            except KeyError:
                pass

        try:  # 이전 / 다음 회차 납부일 or 약정일
            pre_date = sorted_combined[i - 1][0].deal_date \
                if isinstance(sorted_combined[i - 1], tuple) \
                else sorted_combined[i - 1].get('due_date', None)
            next_date = sorted_combined[i + 1][0].deal_date \
                if isinstance(sorted_combined[i + 1], tuple) \
                else sorted_combined[i + 1].get('due_date', None)
        except IndexError:  # 마지막은 발행일
            pre_date = first_date
            next_date = pub_date

        if is_past and contract.sup_cont_date:
            next_date = next_date if contract.sup_cont_date >= next_date else contract.sup_cont_date

        if isinstance(paid, tuple):
            curr_paid_total = paid[1]  # 납부 금액 누계 추출 기록

            # 약정액누계 보다 납부액 누계가 큰(<=)인 회차 별칭 리스트
            paid_ords = [o for o in list(filter(lambda o: o['amount_total'] <= curr_paid_total, simple_orders))]

            # 당회 완납이면 회차 별칭 추출
            paid_pay_code = paid_ords[-1]['pay_code'] if paid_ords else 0
            paid_ord_name = paid_ords[-1]['name'] if paid_ords else None

            # ord_list 요소와 중복이 아니면 완납회차 별칭 추출
            paid_ord_name = paid_ord_name if paid_ord_name not in ord_list else None
            ord_list.append(paid_ord_name)  # 납부회차 별칭 리스트 추가

            if curr_amt_total == 0 and paid_pay_code >= calc_start_pay_code:
                curr_amt_total = paid_ords[-1]['amount_total'] if paid_ords else None

            if curr_paid_total > curr_amt_total:  # 선납 시 (납부 총액 > 약정 총액)
                # --------------------------------
                if is_first_pre:  # calc 약정 개시 전이면
                    # 약정 총액 - 납부 총액 (선납금 추출)
                    diff = curr_amt_total - curr_paid_total \
                        if paid_pay_code and paid_pay_code >= calc_start_pay_code else 0
                    diff = diff if paid[0].deal_date > contract.contractor.contract_date else 0
                    if paid_pay_code >= calc_start_pay_code:
                        is_first_pre = False  # 최초 선납의 경우에만 계산하기 위해 이후 False로 변경
                else:
                    diff = -paid[0].income
                # --------------------------------

                try:
                    code = calc_start_pay_code if curr_pay_code == 0 else curr_pay_code + 1
                    next_due_date = [o['due_date'] for o in simple_orders if o.get('pay_code', 0) == code][0]
                except IndexError:
                    next_due_date = simple_orders[-1]['due_date']

                prepay_days = (paid[0].deal_date - next_due_date).days

                buffer_days = 30
                diff = diff if prepay_days < -buffer_days else 0  # 납부기한 30일 이내 납부는 선납 적용하지 않음

                delay_days = (paid[0].deal_date - pre_date).days \
                    if ord_i_list and ord_i_list[0] < i else 0
            else:  # 미납 시 (약정 총액 > 납부 총액)
                # 납부 총액 - 약정 총액(미납금 추출)
                diff = curr_amt_total - curr_paid_total
                if paid_pay_code >= calc_start_pay_code:
                    is_first_pre = True  # 미납이 발생된 경우 최초 선납 초기화
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
        else:  # 약정 데이터 삽입
            ord_i_list.append(i)  # 연체 적용 약정회차 기록 배열
            curr_pay_code = paid['pay_code'] if paid else 0
            curr_amt_total = paid['amount_total']  # 현재 약정금 합계

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

    paid_sum_total = paid_list.aggregate(Sum('income'))['income__sum']  # 완납 총금액
    paid_sum_total = paid_sum_total if paid_sum_total else 0
    calc_sums = (penalty_sum, discount_sum, ord_i_list)

    return paid_dict_list, paid_sum_total, calc_sums


class PdfExportBill(View):
    """고지서 리스트"""

    def get(self, request):
        """
        :: PDF 파일 생성 함수
        :parma request:
        :return:
        """
        project = request.GET.get('project')  # 프로젝트 ID
        pub_date = datetime.strptime(request.GET.get('date'), '%Y-%m-%d').date()
        bill_info = SalesBillIssue.objects.get(project=project)
        np = True if request.GET.get('np') else False
        nl = True if request.GET.get('nl') else False

        context = {
            'pub_date': pub_date,
            'bill_info': bill_info
        }  # 전체 데이터 딕셔너리
        payment_orders = InstallmentPaymentOrder.objects.filter(project=project)  # 전체 납부회차 리스트
        now_due_order = bill_info.now_payment_order.pay_code if bill_info.now_payment_order else 2  # 당회 납부 회차

        contractor_list = request.GET.get('seq').split('-')  # 계약 건 ID 리스트

        # 해당 계약건에 대한 데이터 정리 --------------------------------------- start

        context['data_list'] = (self.get_bill_data(cont_id, payment_orders, now_due_order, pub_date, np, nl) \
                                for cont_id in contractor_list)

        # 해당 계약건에 대한 데이터 정리 --------------------------------------- end

        html_string = render_to_string('pdf/bill_control.html', context)
        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="payment_bill({len(contractor_list)}).pdf"'
            return response

    def get_bill_data(self, cont_id, payment_orders, now_due_order, pub_date, np, nl):
        """
        :: 계약 건 당 전달 데이터 생성 함수
        :param cont_id: 계약자 아이디
        :param payment_orders: 전체 납부 회차
        :param now_due_order: 금회 납부 회차
        :param pub_date: 발행일
        :param np: no price 가격 미표시 여부
        :param nl: no late 연체 미표시 여부
        :return dict(bill_data: 계약 건당 데이터):
        """
        bill_data = {}  # 현재 계약 정보 딕셔너리

        # 계약 건 객체
        bill_data['contract'] = contract = get_contract(cont_id)

        try:
            unit = contract.key_unit.houseunit
        except ObjectDoesNotExist:
            unit = None

        # 동호수
        bill_data['unit'] = unit

        # 이 계약 건 분양가 (계약금, 중도금, 잔금 약정액)
        try:
            cont_price = contract.contractprice
            price = cont_price.price
            price_build = cont_price.price_build
            price_land = cont_price.price_land
            price_tax = cont_price.price_tax

            down = cont_price.down_pay
            middle = cont_price.middle_pay
            remain = cont_price.remain_pay
        except ObjectDoesNotExist:
            price = 0
            price_build = 0
            price_land = 0
            price_tax = 0

            down = 0
            middle = 0
            remain = 0

        bill_data['price'] = price if unit else '동호 지정 후 고지'  # 이 건 분양가격
        bill_data['price_build'] = price_build if unit else '-'  # 이 건 건물가
        bill_data['price_land'] = price_land if unit else '-'  # 이 건 대지가
        bill_data['price_tax'] = price_tax if unit else '-'  # 이 건 부가세

        amount = {'1': down, '2': middle, '3': remain}

        # 납부목록, 완납금액 구하기 ------------------------------------------
        paid_list, paid_sum_total = self.get_paid(contract)
        # --------------------------------------------------------------

        # 해당 계약 건의 회차별 관련 정보
        orders_info = self.get_orders_info(payment_orders, amount, paid_sum_total)

        # 완납 회차
        paid_code = self.get_paid_code(orders_info, paid_sum_total)

        # ■ 계약 내용 -----------------------------------------------------
        bill_data['cont_content'] = self.get_cont_content(contract, unit)

        # ■ 납부대금 안내 ----------------------------------------------
        bill_data['this_pay_info'] = self.get_this_pay_info(contract,
                                                            orders_info,
                                                            payment_orders,
                                                            now_due_order,
                                                            paid_code)

        # 납부대금 합계
        bill_data['this_pay_sum'] = {
            'amount_sum': sum([pi["amount"] for pi in bill_data['this_pay_info']]),
            'unpaid_sum': sum([pi["unpaid"] for pi in bill_data['this_pay_info']]),
            'penalty_sum': sum([pi["penalty"] for pi in bill_data['this_pay_info']]),
            'amount_total': sum([pi["sum_amount"] for pi in bill_data['this_pay_info']]),
        }

        # ■ 납부방법 안내 ------------------------------------------------
        pm_cost_sum = sum([pm['pm_cost_sum'] for pm in orders_info])
        bill_data['pay_method'] = (bill_data['this_pay_sum']['amount_total'], pm_cost_sum)

        # ■ 납부약정 및 납입내역 -------------------------------------------
        # 기 도래한 약정 회차 내역
        bill_data['due_orders'] = self.get_due_orders(contract, orders_info,
                                                      payment_orders, now_due_order,
                                                      paid_code, pub_date, is_late_fee=False)

        # 미 도래한 약정 회차 내역
        bill_data['remain_orders'] = self.get_remain_orders(contract, orders_info,
                                                            payment_orders, now_due_order)

        bill_data['paid_sum_total'] = paid_sum_total  # 기 납부 총액
        # 연체료 합계
        bill_data['late_fee_sum'] = self.get_due_orders(contract, orders_info,
                                                        payment_orders, now_due_order,
                                                        paid_code, pub_date, is_late_fee=True)

        # 표시 정보 제한 여부
        bill_data['no_price'] = np
        bill_data['no_late'] = nl

        # 공백 개수 구하기
        unpaid_count = len(bill_data['this_pay_info'])
        rem_count = len(bill_data['remain_orders'])

        bill_data['blank_line'] = self.get_blank_line(unpaid_count,
                                                      pm_cost_sum,
                                                      payment_orders.count())

        # --------------------------------------------------------------
        return bill_data

    @staticmethod
    def get_paid(contract):
        """
        :: ■ 기 납부금액 구하기
        :param contract: 계약정보
        :param pub_date: 발행일
        :return list(paid_list: 납부 건 리스트), int(paid_sum_total: 납부 총액):
        """
        paid_list = ProjectCashBook.objects.filter(
            income__isnull=False,
            project_account_d3__in=(1, 4),  # 분(부)담금 or 분양수입금
            contract=contract,
        ).order_by('deal_date', 'id')  # 해당 계약 건 납부 데이터

        paid_sum_total = paid_list.aggregate(Sum('income'))['income__sum']  # 완납 총금액
        paid_sum_total = paid_sum_total if paid_sum_total else 0
        return paid_list, paid_sum_total

    @staticmethod
    def get_orders_info(payment_orders, amount, paid_sum_total):
        """
        :: 회차별 부가정보
        :param payment_orders: 회차 정보
        :param amount: {'1': down_pay, '2': middle_pay, '3': remain_pay}
        :param paid_sum_total: 기 납부 총액
        :return list(dict(order_info_list)): 회차별 부가정보 딕셔너리 리스트
        """
        order_info_list = []
        sum_pay_amount = 0  # 회당 납부 약정액 누계
        pm_cost_sum = 0  # PM 용역비 합계

        # 지연가산금 관련 계산 시작 회차 ----------------------------------------------
        try:
            calc_start_code = payment_orders.filter(Q(is_prep_discount=True)|Q(is_late_penalty=True))[0].pay_code
        except IndexError:
            calc_start_code = 2

        for order in payment_orders:
            info = {'order': order}
            pay_amount = amount[order.pay_sort]  # 회당 납부 약정액
            info['pay_amount'] = pay_amount  # 회당 납부 약정액
            sum_pay_amount += pay_amount  # 회당 납부 약정액 누계
            info['sum_pay_amount'] = sum_pay_amount  # 회당 납부 약정액 누계
            unpaid = sum_pay_amount - paid_sum_total  # 약정액 누계 - 총 납부액
            unpaid = unpaid if unpaid > 0 else 0  # 음수(초과 납부 시)는 0 으로 설정
            info['unpaid_amount'] = unpaid if unpaid < pay_amount else pay_amount  # 미납액
            pm_cost_sum += pay_amount if order.pay_sort == '7' else 0  # PM 용역비 합계
            info['pm_cost_sum'] = pm_cost_sum  # PM 용역비 합계

            order_info_list.append(info)

        return order_info_list

    @staticmethod
    def get_cont_content(contract, unit):
        """
        :: ■ 계약 내용
        :param contract: 계약정보
        :param unit: 동호수 정보
        :return dict(contractor: 계약자명, cont_date: 계약일, cont_no: 계약번호, cont_type: 평형):
        """
        contractor = contract.contractor.name
        cont_date = contract.contractor.contract_date
        cont_no = contract.key_unit.houseunit if unit else contract.serial_number
        cont_type = contract.unit_type or contract.key_unit.unit_type

        return {
            'contractor': contractor,
            'cont_date': cont_date,
            'cont_no': cont_no,
            'cont_type': cont_type,
        }

    @staticmethod
    def get_paid_code(orders_info, paid_sum_total):
        """
        :: 완납 회차 구하기
        :param orders_info: 전체 납부 회차
        :param paid_sum_total: 납부 총액
        :return 완납회차 객체:
        """
        try:
            paid_code = [c['order'].pay_code for c in orders_info if paid_sum_total >= c['sum_pay_amount']][-1]
        except IndexError:  # paid_sum_total 이 1회차에 미치지 못하는 경우 == 계약금 부족 시
            paid_code = 0

        return paid_code

    @staticmethod
    def get_this_pay_info(contract,
                          orders_info, payment_orders,
                          now_due_order, paid_code):
        """
        :: ■ 납부대금 안내
        :param contract: 계약 정보
        :param orders_info: 회차별 부가정보
        :param payment_orders: 회차 정보
        :param now_due_order: 당회 납부 회차
        :param paid_code: 완납 회차
        :return list(dict(order: 납부회차, due_date: 납부기한, amount: 약정금액, unpaid: 미납금액, penalty: 연체가산금, sum_amount: 납부금액)):
        """
        payment_list = []
        unpaid_orders = payment_orders.filter(pay_code__gt=paid_code,
                                              pay_code__lte=now_due_order)  # 최종 기납부회차 이후부터 납부지정회차 까지 회차그룹
        for order in unpaid_orders:
            ord_info = list(filter(lambda o: o['order'] == order, orders_info))[0]

            amount = ord_info['pay_amount']
            unpaid = ord_info['unpaid_amount']
            penalty = 0

            payment_dict = {
                'order': order,
                'due_date': get_due_date_per_order(contract, order, unpaid_orders),
                'amount': amount,
                'unpaid': unpaid,
                'penalty': penalty,
                'sum_amount': unpaid + penalty
            }
            payment_list.append(payment_dict)

        return payment_list

    def get_due_orders(self, contract, orders_info,
                       payment_orders, now_due_order,
                       paid_code, pub_date, is_late_fee=False):
        """
        :: ■ 납부약정 및 납입내역 - 납입내역
        :param contract: 계약 건
        :param orders_info: 납부 회차별 부가정보
        :param payment_orders: 전체 납부회차
        :param now_due_order: 금회 납부 회차
        :param paid_code: 완납회차
        :param pub_date: 발행일자
        :param is_late_fee: 연체료 발행여부
        :return list(paid_list: 왼납 회차 목록):
        """

        # 해당 계약 건 전체 납부 목록 -> [(income, deal_date), ...]
        paid_list = [(p.income, p.deal_date) for p in self.get_paid(contract)[0]]
        paid_date = paid_list[0][1] if len(paid_list) > 0 else None

        # 전체 리턴 데이터 목록
        paid_amt_list = []
        due_orders = payment_orders.filter(pay_code__lte=now_due_order)  # 금 회차까지 납부 회차

        excess = 0  # 회차별 초과 납부분
        paid_amt_sum = 0  # 실 수납액 누계

        late_fee_sum = 0

        try:
            calc_start_code = payment_orders.filter(Q(is_prep_discount=True)|Q(is_late_penalty=True))[0].pay_code
        except IndexError:
            calc_start_code = 2

        for order in due_orders:
            due_date = get_due_date_per_order(contract, order, due_orders)  # 납부기한
            ord_info = list(filter(lambda o: o['order'] == order, orders_info))[0]  # 금 회차 orders_info
            amount = ord_info['pay_amount']  # 금 회차 납부 약정액

            paid_amt = 0  # 금회 납부금액

            while True:  # 납입회차별 납입금 구하기
                try:
                    paid = paid_list.pop(0)  # (income, deal_date) <- 첫번째 요소(가장 빠른 납부일자)
                    paid_amt += paid[0]  # 납부액 += income (loop 동안 income 을 모두 더함)
                    paid_date = paid[1]  # 납부일 = deal_date(loop 마지막 납부건 납부일)
                    is_over_amt = (excess + paid_amt) >= amount  # (전회 초과 납부분 + 납부액) >= 약정액
                    # 현재 회차 == 금회 직전 회차 (이 경우 루프 마지막까지 순회하기 위해서 루프탈출 조건에서 제외)

                    is_last_ord = order.pay_code + 1 == now_due_order
                    if is_over_amt and not is_last_ord:  # loop 탈출 조건
                        excess += (paid_amt + excess - amount)  # 금회 초과 납부분 += (금회 납부액 + 전회 초과납부분 - 약정액)
                        break
                except IndexError:  # .pop(0) 에러 시 탈출
                    break

            paid_date = paid_date if paid_amt else ''  # 납부 금액이 있을 때만 납부일 저장

            if paid_date:  # 당 회차 완납인 경우(지연 납부일 계산)
                unpaid_amt = 0  # 당회 납부 지연 시 납부 전 지연금 계산
                unpaid_days = 0  # 당회 납부 지연 시 납부 전 지연금 지연일 계산

                paid_amt_sum += paid_amt  # 당 회차 납부액 누계

                # 납부코드 2 회차 이상 and 납부 금액 and 납부 날짜 > 약정 날짜
                if order.pay_code >= calc_start_code and paid_amt and paid_date > due_date:
                    sum_p_amt = ord_info['sum_pay_amount']  # 금 회차 납부 약정액
                    sum_p_paid = paid_amt_sum - paid_amt
                    unpaid_amt = sum_p_amt - sum_p_paid if sum_p_amt - sum_p_paid > 0 else 0
                    if unpaid_amt > 0:
                        # unpaid_days = (datetime.strptime(paid_date, '%Y-%m-%d').date() - due_date).days
                        unpaid_days = (paid_date - due_date).days
            else:  # 당 회차 미납인 경우
                # 납부 지연금
                unpaid_amt = ord_info['unpaid_amount'] if order.pay_code >= calc_start_code else 0

                if unpaid_amt == 0 or (order.pay_code == 1 and paid_code >= 1):  # 지연금 없거나 1회차 일때 완납코드가 1 이상이면,
                    unpaid_days = 0
                else:
                    try:
                        unpaid_days = (pub_date - due_date).days if pub_date >= due_date else 0
                    except AttributeError:
                        unpaid_days = 0

            project = contract.project
            late_fee_sum += get_late_fee(project, unpaid_amt, unpaid_days)

            paid_dict = dict()
            paid_dict['order'] = order.pay_name
            paid_dict['due_date'] = due_date
            paid_dict['amount'] = amount
            paid_dict['paid_date'] = paid_date
            paid_dict['paid_amt'] = paid_amt

            paid_dict['unpaid_amt'] = unpaid_amt
            paid_dict['unpaid_days'] = unpaid_days
            paid_dict['unpaid_result'] = get_late_fee(project, unpaid_amt, unpaid_days)

            paid_dict['note'] = f'(+)' if unpaid_days else ''
            paid_amt_list.append(paid_dict)

        if is_late_fee:
            return late_fee_sum
        else:
            return paid_amt_list

    @staticmethod
    def get_blank_line(unpaid_count, pm, total_orders_count):
        """
        :: 공백 라인 개수 구하기
        :param unpaid_count: 미납내역 개수
        :param pm: pm 용역비 적용여부
        :param total_orders_count: 전체 납부회차 개수
        :return str(. * 공백라인 수):
        """
        num = unpaid_count + 1 if pm else unpaid_count
        blank_line = (14 - (num + total_orders_count))
        return '.' * blank_line

    @staticmethod
    def get_remain_orders(contract, orders_info, payment_orders, now_due_order):
        """
        :: ■ 납부약정 및 납입내역 - 잔여회차
        :param contract: 계약 건
        :param orders_info: 납부 회차별 부가정보
        :param payment_orders: 전체 납부 회차
        :param now_due_order: 금회 납부 회차
        :return list(dict(remain_amt_list)): 잔여 회차(dict) 목록:
        """
        remain_amt_list = []
        remain_orders = payment_orders.filter(pay_code__gt=now_due_order)

        for order in remain_orders:
            ord_info = list(filter(lambda o: o['order'] == order, orders_info))[0]
            amount = ord_info['pay_amount']

            paid_dict = {
                'order': order.pay_name,
                'due_date': get_due_date_per_order(contract, order, remain_orders),
                'amount': amount,
                'paid_date': '',
                'paid_amt': 0,
                # 'delayed_amt': 0,
                'penalty_days': 0,
                'panalty_amt': 0,
            }
            remain_amt_list.append(paid_dict)

        return remain_amt_list


class PdfExportPayments(View):

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

        payment_orders = InstallmentPaymentOrder.objects.filter(project=project)  # 전체 납부회차 컬렉션

        try:
            unit = contract.key_unit.houseunit
        except ObjectDoesNotExist:
            unit = None

        # 동호수
        context['unit'] = unit

        # 1. 이 계약 건 분양가격 (계약금, 중도금, 잔금 약정액)
        try:
            cont_price = contract.contractprice  # 공급가격
            price = cont_price.price
            price_build = cont_price.price_build
            price_land = cont_price.price_land
            price_tax = cont_price.price_tax

            down = cont_price.down_pay  # 계약금
            middle = cont_price.middle_pay  # 중도금
            remain = cont_price.remain_pay  # 잔금
        except ObjectDoesNotExist:
            price = 0
            price_build = 0
            price_land = 0
            price_tax = 0

            down = 0  # 계약금
            middle = 0  # 중도금
            remain = 0  # 잔금
        context['price'] = price if unit else '동호 지정 후 고지'  # 이 건 분양가격
        context['price_build'] = price_build if unit else '-'  # 이 건 건물가
        context['price_land'] = price_land if unit else '-'  # 이 건 대지가
        context['price_tax'] = price_tax if unit else '-'  # 이 건 부가세

        amount = {'1': down, '2': middle, '3': remain}

        # 2. 요약 테이블 데이터
        context['due_amount'] = get_due_amount(payment_orders, contract, amount)  # 약정금 누계

        # 3. 간단 차수 정보
        context['simple_orders'] = simple_orders = get_simple_orders(payment_orders, contract, amount)

        # 4. 납부목록, 완납금액 구하기 ------------------------------------------
        paid_dicts, paid_sum_total, calc_sums = get_paid(contract, simple_orders, pub_date, is_calc=calc)
        context['paid_dicts'] = paid_dicts
        context['paid_sum_total'] = paid_sum_total  # paid_list.aggregate(Sum('income'))['income__sum']  # 기 납부총액
        context['calc_sums'] = calc_sums
        # ----------------------------------------------------------------

        html_string = render_to_string('pdf/payments_by_contractor.html', context)

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="payments_contractor.pdf"'
            return response


class PdfExportCalculation(View):

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
        try:
            cont_price = contract.contractprice  # 공급가격
            price = cont_price.price
            price_build = cont_price.price_build
            price_land = cont_price.price_land
            price_tax = cont_price.price_tax
        except ObjectDoesNotExist:
            price = 0
            price_build = 0
            price_land = 0
            price_tax = 0
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
        context['paid_sum_total'] = paid_sum_total  # pad_list.aggregate(Sum('income'))['income__sum']  # 기 납부총액
        context['calc_sums'] = calc_sums
        # ----------------------------------------------------------------

        html_string = render_to_string('pdf/calculation_by_contractor.html', context)

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="calculation_contractor.pdf"'
            return response

    @staticmethod
    def get_down_pay(contract):
        down = SpecialDownPay.objects.get(order_group=contract.order_group, unit_type=contract.unit_type)
        return down.payment_amount, down.payment_remain
