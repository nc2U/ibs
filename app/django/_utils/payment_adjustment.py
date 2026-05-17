"""
Payment Adjustment Utilities

선납 할인 및 연체 가산금 계산을 위한 유틸리티 함수들
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Optional, Any, List

from django.db.models import Sum, Q, F

from _utils.contract_price import get_payment_amount, get_due_date_per_order
from payment.models import InstallmentPaymentOrder, ContractPayment


def get_effective_contract_date(contract) -> Optional[date]:
    """유효한 계약일 반환"""
    try:
        sup_cont_date = getattr(contract, 'sup_cont_date', None)
        contractor_date = None
        if hasattr(contract, 'contractor') and contract.contractor:
            contractor_date = getattr(contract.contractor, 'contract_date', None)

        if not sup_cont_date and not contractor_date:
            return None
        if sup_cont_date and not contractor_date:
            return sup_cont_date
        if contractor_date and not sup_cont_date:
            return contractor_date
        return max(sup_cont_date, contractor_date)
    except AttributeError:
        return None


def calculate_daily_interest(principal: int, annual_rate: Decimal, days: int) -> int:
    """일할 계산 (연이율 기준)"""
    if principal <= 0 or annual_rate <= 0 or days <= 0:
        return 0
    return int((annual_rate / Decimal('100') / Decimal('365')) * days * principal)


def calculate_all_installments_payment_allocation(contract, as_of_date: Optional[date] = None) -> Dict[int, Dict[str, Any]]:
    """계약의 모든 회차에 대해 Waterfall 충당 방식으로 납부 할당 계산 (조정된 날짜 반영)"""
    if as_of_date is None:
        as_of_date = date.today()

    all_installments = InstallmentPaymentOrder.objects.filter(
        project=contract.project,
        type_sort=contract.unit_type.sort
    ).exclude(excluded_order_groups=contract.order_group).order_by('pay_code', 'pay_time')

    all_payments = ContractPayment.objects.valid_payments().filter(
        contract=contract,
        deal_date__lte=as_of_date
    ).order_by('deal_date', 'id').select_related('accounting_entry')

    installment_status = {}
    for inst in all_installments:
        promised = get_payment_amount(contract, inst)
        due_date = get_due_date_per_order(contract, inst, all_installments)
        installment_status[inst.id] = {
            'installment_order': inst,
            'promised_amount': promised,
            'paid_amount': 0,
            'remaining_amount': promised,
            'is_fully_paid': False,
            'fully_paid_date': None,
            'due_date': due_date,
            'is_late': False,
            'late_days': 0,
            'late_payment_amount': 0,
            'late_payment_details': [],
            'total_late_penalty': 0,
            'payment_sources': []
        }

    for payment in all_payments:
        payment_amount = payment.accounting_entry.amount
        payment_date = payment.deal_date
        remaining_payment = payment_amount

        for inst in all_installments:
            if remaining_payment <= 0: break
            status = installment_status[inst.id]
            if not status['is_fully_paid']:
                allocated = min(remaining_payment, status['remaining_amount'])
                status['paid_amount'] += allocated
                status['remaining_amount'] -= allocated
                remaining_payment -= allocated
                status['payment_sources'].append({
                    'payment_id': payment.id,
                    'payment_date': payment_date,
                    'allocated_amount': allocated,
                })
                if status['remaining_amount'] <= 0:
                    status['is_fully_paid'] = True
                    status['fully_paid_date'] = payment_date

    # 지연 가산금 계산
    for inst_id, status in installment_status.items():
        due_date = status['due_date']
        inst = status['installment_order']
        if not due_date or not inst.is_late_penalty or not inst.late_penalty_ratio: continue

        total_penalty = 0
        details = []
        max_days = 0

        for source in status['payment_sources']:
            if source['payment_date'] > due_date:
                days = (source['payment_date'] - due_date).days
                penalty = calculate_daily_interest(source['allocated_amount'], inst.late_penalty_ratio, days)
                details.append({
                    'payment_id': source['payment_id'],
                    'payment_date': source['payment_date'],
                    'payment_amount': source['allocated_amount'],
                    'late_days': days,
                    'late_penalty': penalty,
                    'type': 'paid_late'
                })
                total_penalty += penalty
                max_days = max(max_days, days)
                status['is_late'] = True

        if not status['is_fully_paid'] and status['remaining_amount'] > 0:
            if as_of_date > due_date:
                days = (as_of_date - due_date).days
                penalty = calculate_daily_interest(status['remaining_amount'], inst.late_penalty_ratio, days)
                details.append({
                    'payment_date': None,
                    'payment_amount': status['remaining_amount'],
                    'late_days': days,
                    'late_penalty': penalty,
                    'type': 'unpaid'
                })
                total_penalty += penalty
                max_days = max(max_days, days)
                status['is_late'] = True

        status['late_days'] = max_days
        status['late_payment_amount'] = total_penalty
        status['late_payment_details'] = details
        status['total_late_penalty'] = total_penalty

    return installment_status


def get_installment_adjustment_summary(contract, installment_order, as_of_date: Optional[date] = None) -> Dict[str, Any]:
    """회차별 선납 할인 및 연체 가산금 종합 정보"""
    all_status = calculate_all_installments_payment_allocation(contract, as_of_date)
    status = all_status.get(installment_order.id, {})
    return {
        'total_penalty': status.get('total_late_penalty', 0),
        'total_discount': 0, # TODO: 선납 할인 로직 통합 필요 시 추가
        'is_fully_paid': status.get('is_fully_paid', False),
        'late_days': status.get('late_days', 0),
        'remaining_amount': status.get('remaining_amount', 0)
    }


def aggregate_installment_adjustments(contract, payment_orders, now_due_order, pub_date) -> Dict[str, Any]:
    """분할 납부를 회차별로 집계하여 할인/가산금 계산 (고지서용)"""
    all_status = calculate_all_installments_payment_allocation(contract, pub_date)
    display_installments = payment_orders.filter(
        Q(pay_code__lte=now_due_order)
    ).order_by('pay_code', 'pay_time')

    total_late_fee, total_discount, details = 0, 0, []

    for inst in display_installments:
        status = all_status.get(inst.id, {})
        if not status: continue
        
        # 조정된 날짜가 발행일 이후인 경우 미납 계산 제외 (Catch-up 반영)
        due_date = status['due_date']
        if due_date and due_date > pub_date: continue

        penalty = status.get('total_late_penalty', 0)
        adj = get_installment_adjustment_summary(contract, inst, pub_date)
        
        details.append({
            'installment': inst,
            'order_name': inst.pay_name,
            'is_fully_paid': status['is_fully_paid'],
            'late_days': status['late_days'],
            'penalty_amount': penalty,
            'discount_amount': adj['total_discount'],
            'late_amount': status['late_payment_amount'] if penalty > 0 else 0,
        })
        total_late_fee += penalty
        total_discount += adj['total_discount']

    return {
        'total_late_fee': total_late_fee,
        'total_discount': total_discount,
        'installment_details': details,
        'penalty_count': sum(1 for d in details if d['penalty_amount'] > 0),
        'discount_count': sum(1 for d in details if d['discount_amount'] > 0)
    }


def calculate_effective_late_metrics(late_payment_details):
    """분할 납부 시 가중 평균 지연 지표 계산"""
    late_only = [d for d in late_payment_details if d.get('type') == 'paid_late']
    if not late_only: return None, None
    total_amount = sum(d.get('payment_amount', 0) for d in late_only)
    if total_amount == 0: return None, None
    weighted_days_sum = sum(d.get('payment_amount', 0) * d.get('late_days', 0) for d in late_only)
    return total_amount, round(weighted_days_sum / total_amount)


def get_first_due_date_after_contract(contract, current_date=None) -> Optional[date]:
    """계약일 이후 첫 번째 도래 회차 납부기한 (유틸리티)"""
    if current_date is None: current_date = date.today()
    contract_date = get_effective_contract_date(contract)
    if not contract_date: return None
    from _utils.contract_price import get_due_date_per_order
    all_insts = InstallmentPaymentOrder.objects.filter(project=contract.project, type_sort=contract.unit_type.sort).exclude(excluded_order_groups=contract.order_group).order_by('pay_code')
    for inst in all_insts:
        due = get_due_date_per_order(contract, inst, all_insts)
        if due and due > contract_date: return due
    return None
