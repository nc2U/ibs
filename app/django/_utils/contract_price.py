import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum

from payment.models import SalesPriceByGT, DownPayment, InstallmentPaymentOrder, PaymentPerInstallment
from project.models import ProjectIncBudget

logger = logging.getLogger(__name__)


def get_due_date_per_order(contract, order, payment_orders=None):
    """
    :: 회차 별 납부 일자 구하기 (계약일 기준 조정 로직 적용)
    """
    # 1. 기초 데이터 설정
    cont_date = None
    if hasattr(contract, 'contractor') and contract.contractor:
        cont_date = contract.contractor.contract_date
    if not cont_date:
        return None

    # 2. 미래 기준점(ff_date) 찾기
    ff_date = getattr(contract, '_first_future_date', None)

    if ff_date is None:
        # [수정] ff_date 탐색 시에는 '제외 차수' 여부와 상관없이 프로젝트 전체 일정을 참조해야 함
        future_middle = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort,  # 계약 타입 일치
            pay_sort='2',  # 중도금
            pay_due_date__gte=cont_date  # 계약일 이후
        ).order_by('pay_due_date').first()

        if future_middle:
            ff_date = future_middle.pay_due_date
        else:
            # 중도금이 없으면 잔금(3)에서 동일 로직 적용
            future_remain = InstallmentPaymentOrder.objects.filter(
                project=contract.project,
                type_sort=contract.unit_type.sort,
                pay_sort='3',
                pay_due_date__gte=cont_date
            ).order_by('pay_due_date').first()
            ff_date = future_remain.pay_due_date if future_remain else None

        contract._first_future_date = ff_date

    # 3. 현재 회차 정보 파악
    is_dict = isinstance(order, dict)
    pay_code = order.get('pay_code') if is_dict else order.pay_code
    pay_sort = order.get('pay_sort') if is_dict else order.pay_sort

    # 4. 현재 회차의 '원래(Natural)' 기한 계산
    due_date = None
    if is_dict and order.get('due_date'):
        due_date = order.get('due_date')
    else:
        if pay_sort == '1':
            due_date = cont_date
        else:
            # DB 데이터로부터 날짜 도출
            si_date = order.get('days_since_prev') if is_dict else getattr(order, 'days_since_prev', None)
            pd_date = order.get('pay_due_date') if is_dict else getattr(order, 'pay_due_date', None)
            ed_date = order.get('extra_due_date') if is_dict else getattr(order, 'extra_due_date', None)

            if si_date:
                # 상대 날짜 계산 시에도 전체 일정을 참조해야 정확한 누적 합산 가능
                if payment_orders is None:
                    payment_orders = InstallmentPaymentOrder.objects.filter(
                        project=contract.project, type_sort=contract.unit_type.sort)
                pre_si = payment_orders.filter(pay_code__lt=pay_code).aggregate(
                    total=Sum('days_since_prev'))['total'] or 0
                due_date = cont_date + timedelta(days=pre_si + (si_date or 0))

            fixed_date = ed_date or pd_date
            if fixed_date:
                due_date = max(due_date, fixed_date) if due_date else fixed_date

    # 5. 비즈니스 규칙 적용 (최종 조정)
    if pay_sort == '1':
        # 계약금 Ceiling
        if ff_date and due_date and due_date > ff_date:
            due_date = ff_date
    elif pay_sort == '2':
        # 중도금 Catch-up: 원래 기한이 계약일 이전이면 ff_date로 유예.
        if not due_date or due_date <= cont_date:
            due_date = ff_date
    elif pay_sort == '3':
        # 잔금 유예
        if ff_date and due_date and due_date <= cont_date:
            due_date = ff_date

    return due_date


def get_floor_type(contract):
    if not contract or not contract.key_unit: return None
    try:
        return contract.key_unit.houseunit.floor_type
    except AttributeError:
        return None


def get_sales_price_by_gt(contract, houseunit=None):
    if not contract: return None
    if houseunit is None:
        if not contract.key_unit: return None
        try:
            houseunit = contract.key_unit.houseunit
        except AttributeError:
            return None
    if not houseunit or not hasattr(houseunit, 'floor_type'): return None
    try:
        return SalesPriceByGT.objects.get(project=contract.project, order_group=contract.order_group,
                                          unit_type=contract.unit_type, unit_floor_type=houseunit.floor_type)
    except Exception:
        return None


def get_contract_price(contract, houseunit=None, is_set=False):
    if not contract: return 0, 0, 0, 0
    if not is_set:
        try:
            cp = contract.contractprice
            return (cp.price or 0, cp.price_build or 0, cp.price_land or 0, cp.price_tax or 0)
        except AttributeError:
            pass
    try:
        sales_price = get_sales_price_by_gt(contract, houseunit)
        if sales_price: return (sales_price.price or 0, sales_price.price_build or 0,
                                sales_price.price_land or 0, sales_price.price_tax or 0)
    except Exception:
        pass
    try:
        budget = ProjectIncBudget.objects.get(project=contract.project, order_group=contract.order_group,
                                              unit_type=contract.unit_type)
        if budget and budget.average_price: return budget.average_price, 0, 0, 0
    except Exception:
        pass
    try:
        if contract.unit_type and contract.unit_type.average_price: return contract.unit_type.average_price, 0, 0, 0
    except AttributeError:
        pass
    return 0, 0, 0, 0


def get_fixed_payment_amount(installment_order):
    return installment_order.pay_amt if installment_order and installment_order.pay_amt else None


def get_down_payment(contract, installment_order):
    if not contract or not installment_order or installment_order.pay_sort != '1': return None
    fixed = get_fixed_payment_amount(installment_order)
    if fixed is not None: return fixed
    try:
        sales_price = get_sales_price_by_gt(contract)
        if sales_price: return PaymentPerInstallment.objects.get(sales_price=sales_price,
                                                                 pay_order=installment_order).amount
    except Exception:
        pass
    if getattr(installment_order, 'calculation_method', 'auto') != 'ratio':
        try:
            down = DownPayment.objects.get(project=contract.project, order_group=contract.order_group,
                                           unit_type=contract.unit_type)
            if down.payment_amount: return down.payment_amount
        except Exception:
            pass
    try:
        price = get_contract_price(contract)[0]
        if not price: return None
        ratio = installment_order.pay_ratio if installment_order.pay_ratio is not None else Decimal('10.0')
        return int(price * (ratio / 100))
    except Exception:
        pass
    return None


def get_total_paid_down_payments(contract):
    if not contract: return 0
    try:
        orders = InstallmentPaymentOrder.objects.filter(project=contract.project, type_sort=contract.unit_type.sort,
                                                        pay_sort='1').exclude(
            excluded_order_groups=contract.order_group)
        return sum(filter(None, [get_down_payment(contract, o) for o in orders]))
    except Exception:
        return 0


def get_down_payment_settlement(contract, installment_order):
    if not contract or not installment_order or not installment_order.pay_ratio: return 0
    price = get_contract_price(contract)[0]
    if not price: return 0
    return int(price * (installment_order.pay_ratio / 100)) - get_total_paid_down_payments(contract)


def calculate_remain_payment(contract, remain_installment_order):
    if not contract or not remain_installment_order: return 0
    price = get_contract_price(contract)[0]
    if not price: return 0
    try:
        others = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort).exclude(pay_sort='3').exclude(
            id=remain_installment_order.id).exclude(excluded_order_groups=contract.order_group)
        total_other_payments = 0
        for installment in others:
            total_other_payments += get_payment_amount(contract, installment)
        return max(0, price - total_other_payments)
    except Exception:
        return 0


def get_payment_amount(contract, installment_order):
    if not contract or not installment_order: return 0
    sort = installment_order.pay_sort
    if sort == '1': return get_down_payment(contract, installment_order) or 0
    if sort == '4': return get_down_payment_settlement(contract, installment_order)
    fixed = get_fixed_payment_amount(installment_order)
    if fixed is not None: return fixed
    price = get_contract_price(contract)[0]
    if not price: return 0
    if sort == '2':
        ratio = installment_order.pay_ratio if installment_order.pay_ratio is not None else Decimal('10.0')
        return int(price * (ratio / 100))
    if sort == '3': return calculate_remain_payment(contract, installment_order)
    if sort not in ['1', '2', '3', '4']:
        if installment_order.pay_ratio: return int(price * (installment_order.pay_ratio / 100))
        try:
            sp = get_sales_price_by_gt(contract)
            if sp: return PaymentPerInstallment.objects.get(sales_price=sp, pay_order=installment_order).amount
        except Exception:
            pass
    return 0


def get_contract_payment_plan(contract):
    if not contract: return []
    cached = contract.get_cached_payment_plan()
    if cached is not None: return cached
    try:
        sp = get_sales_price_by_gt(contract)
        manuals = {p.pay_order_id: p.amount for p in
                   PaymentPerInstallment.objects.filter(sales_price=sp).select_related('pay_order')} if sp else {}
        installments = InstallmentPaymentOrder.objects.filter(project=contract.project,
                                                              type_sort=contract.unit_type.sort).exclude(
            excluded_order_groups=contract.order_group).order_by('pay_code', 'pay_time')
        plan = []
        for inst in installments:
            due = get_due_date_per_order(contract, inst, installments)
            amt = manuals.get(inst.id) if inst.id in manuals else get_payment_amount(contract, inst)
            plan.append({'installment_order': inst, 'amount': amt, 'due_date': due,
                         'source': 'payment_per_installment' if inst.id in manuals else 'calculated'})
        contract.set_cached_payment_plan(plan)
        return plan
    except Exception:
        logger.exception('get_contract_payment_plan 계산 실패 (contract_pk=%s)', getattr(contract, 'pk', None))
        contract.set_cached_payment_plan([])
        return []


def get_project_payment_summary(project, order_group=None, unit_type=None):
    if not project: return {'installment_summaries': [], 'grand_total': 0, 'total_contracts': 0}
    try:
        contracts_q = project.contract_set.filter(activation=True).select_related('contractprice', 'order_group',
                                                                                  'unit_type',
                                                                                  'key_unit__houseunit__floor_type')
        if order_group: contracts_q = contracts_q.filter(order_group=order_group)
        if unit_type: contracts_q = contracts_q.filter(unit_type=unit_type)
        contracts = list(contracts_q)
        if not contracts: return {'installment_summaries': [], 'grand_total': 0, 'total_contracts': 0}
        inst_q = InstallmentPaymentOrder.objects.filter(project=project)
        if order_group: inst_q = inst_q.exclude(excluded_order_groups=order_group)
        if unit_type: inst_q = inst_q.filter(type_sort=unit_type.sort)
        insts = list(inst_q.order_by('pay_code', 'pay_time'))
        summaries = {i.id: {'installment_order': i, 'total_amount': 0, 'contract_count': 0,
                            'source_breakdown': {'calculated': 0, 'payment_per_installment': 0}} for i in insts}
        total, processed = 0, 0
        for c in contracts:
            try:
                plan = get_contract_payment_plan(c)
                has_pay = False
                for p in plan:
                    iid, amt, src = p['installment_order'].id, p['amount'], p['source']
                    if iid in summaries:
                        summaries[iid]['total_amount'] += amt
                        summaries[iid]['source_breakdown'][src] += amt
                        total += amt
                        has_pay = True
                if has_pay:
                    processed += 1
                    for p in plan:
                        if p['installment_order'].id in summaries: summaries[p['installment_order'].id][
                            'contract_count'] += 1; break
            except Exception:
                continue
        res = []
        for s in summaries.values():
            s['average_amount'] = s['total_amount'] // s['contract_count'] if s['contract_count'] > 0 else 0
            if s['total_amount'] > 0: res.append(s)
        res.sort(key=lambda x: (x['installment_order'].pay_code, x['installment_order'].pay_time))
        return {'installment_summaries': res, 'grand_total': total, 'total_contracts': processed}
    except Exception:
        return {'installment_summaries': [], 'grand_total': 0, 'total_contracts': 0}


def get_multiple_projects_payment_summary(projects, order_group=None, unit_type=None):
    if not projects: return {'installment_summaries': [], 'grand_total': 0, 'total_contracts': 0}
    combined, total_g, total_c = {}, 0, 0
    for p in projects:
        try:
            s = get_project_payment_summary(p, order_group, unit_type)
            total_c += s['total_contracts'];
            total_g += s['grand_total']
            for item in s['installment_summaries']:
                iid = item['installment_order'].id
                if iid not in combined: combined[iid] = {'installment_order': item['installment_order'],
                                                         'total_amount': 0, 'contract_count': 0,
                                                         'source_breakdown': {'calculated': 0,
                                                                              'payment_per_installment': 0}}
                combined[iid]['total_amount'] += item['total_amount']
                combined[iid]['contract_count'] += item['contract_count']
                combined[iid]['source_breakdown']['calculated'] += item['source_breakdown']['calculated']
                combined[iid]['source_breakdown']['payment_per_installment'] += item['source_breakdown'][
                    'payment_per_installment']
        except Exception:
            continue
    res = []
    for s in combined.values():
        s['average_amount'] = s['total_amount'] // s['contract_count'] if s['contract_count'] > 0 else 0
        res.append(s)
    res.sort(key=lambda x: (x['installment_order'].pay_code, x['installment_order'].pay_time))
    return {'installment_summaries': res, 'grand_total': total_g, 'total_contracts': total_c}
