from datetime import date, timedelta
from itertools import accumulate

from django.db.models import Sum, Q

from cash.models import ProjectCashBook
from contract.models import Contract
from payment.models import OverDueRule, SpecialOverDueRule

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
        calc_start = payment_orders.filter(Q(is_prep_discount=True) | Q(is_late_penalty=True)).first().pay_code
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
    return None


def get_paid(contract: Contract, simple_orders, pub_date, **kwargs):
    """
    :: ■ 기 납부금액 구하기
    :param contract: 계약정보
    :param simple_orders: 회차정보
    :param pub_date: 발행일자
    :param kwargs: is_calc => True - 일반용 / False - 확인용 / is_past => 변경 약정에 의한 가산금 산출 여부
    :return list(paid_list: { 납부 건 딕셔너리 }), int(paid_sum_total: 납부 총액):
    """

    calc_start_pay_code = simple_orders[0].get('calc_start') if simple_orders else 2  # 연체/가산 적용 시작 회차 코드
    paid_list = ProjectCashBook.objects.filter(
        income__isnull=False,
        project_account_d3__is_payment=True,  # 분(부)담금 or 분양수입금
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
