"""
간단한 지연납부 계산 로직

핵심 원리:
1. 지연납부금액 = 약정금액 - 납부기일까지 납부액
2. 지연일수 = 납부기일부터 실제납부일까지 (납부시마다 재계산)
"""

from datetime import date
from django.db.models import Sum
from cash.models import ProjectCashBook


def calculate_simple_late_payment(contract, installment, as_of_date=None):
    """
    간단한 지연납부 정보 계산

    Args:
        contract: Contract 인스턴스
        installment: InstallmentPaymentOrder 인스턴스
        as_of_date: 기준일 (None이면 오늘)

    Returns:
        {
            'promised_amount': 약정금액,
            'due_date': 납부기일,
            'paid_on_time': 납부기일까지 납부액,
            'late_payment_amount': 지연납부금액,
            'late_days': 지연일수,
            'is_fully_paid': 완납여부,
            'total_paid': 총납부액
        }
    """
    if as_of_date is None:
        as_of_date = date.today()

    # 1. 기본 정보
    # 약정금액 계산 (pay_amt가 있으면 그대로, 없으면 pay_ratio로 계산)
    try:
        if installment.pay_amt:
            promised_amount = installment.pay_amt
        elif installment.pay_ratio:
            from _utils.contract_price import get_payment_amount
            total_payment = get_payment_amount(contract, installment)
            promised_amount = int(total_payment * installment.pay_ratio / 100)
        else:
            promised_amount = 0
    except (TypeError, ValueError, AttributeError):
        promised_amount = 0

    due_date = installment.pay_due_date

    # 납부기일이 None인 경우에도 전체 납부액은 계산
    if not due_date:
        # 전체 납부액 계산
        total_paid_result = ProjectCashBook.objects.filter(
            contract=contract,
            installment_order=installment,
            project_account_d3__is_payment=True
        ).aggregate(total=Sum('income'))['total']
        total_paid = total_paid_result or 0

        is_fully_paid = total_paid >= promised_amount

        return {
            'promised_amount': promised_amount,
            'due_date': None,
            'paid_on_time': total_paid,  # 납부기일이 없으면 전체 납부액
            'late_payment_amount': 0,    # 납부기일이 없으면 지연 없음
            'late_days': 0,
            'is_fully_paid': is_fully_paid,
            'total_paid': total_paid
        }

    # 2. 납부기일까지 납부된 금액
    paid_on_time_result = ProjectCashBook.objects.filter(
        contract=contract,
        installment_order=installment,
        deal_date__lte=due_date,
        project_account_d3__is_payment=True
    ).aggregate(total=Sum('income'))['total']
    paid_on_time = paid_on_time_result or 0

    # 3. 지연납부금액 = 약정금액 - 납부기일까지 납부액
    late_payment_amount = max(0, promised_amount - paid_on_time)

    # 4. 전체 납부액
    total_paid_result = ProjectCashBook.objects.filter(
        contract=contract,
        installment_order=installment,
        project_account_d3__is_payment=True
    ).aggregate(total=Sum('income'))['total']
    total_paid = total_paid_result or 0

    is_fully_paid = total_paid >= promised_amount

    # 5. 지연일수 계산
    late_days = 0

    if late_payment_amount > 0:  # 지연납부가 있는 경우만
        if is_fully_paid:
            # 완납된 경우: 납부기일 → 완납일
            late_days = _calculate_late_days_to_completion(contract, installment, due_date)
        else:
            # 미완납: 납부기일 → 기준일(오늘)
            if as_of_date > due_date:
                late_days = (as_of_date - due_date).days

    return {
        'promised_amount': promised_amount,
        'due_date': due_date,
        'paid_on_time': paid_on_time,
        'late_payment_amount': late_payment_amount,
        'late_days': late_days,
        'is_fully_paid': is_fully_paid,
        'total_paid': total_paid
    }


def _calculate_late_days_to_completion(contract, installment, due_date):
    """
    완납까지의 지연일수 계산
    납부기일부터 실제 완납일까지
    """
    # 약정금액 계산 (main 함수와 동일한 로직)
    try:
        if installment.pay_amt:
            promised_amount = installment.pay_amt
        elif installment.pay_ratio:
            from _utils.contract_price import get_payment_amount
            total_payment = get_payment_amount(contract, installment)
            promised_amount = int(total_payment * installment.pay_ratio / 100)
        else:
            promised_amount = 0
    except (TypeError, ValueError, AttributeError):
        promised_amount = 0

    if promised_amount <= 0:
        return 0

    cumulative_paid = 0

    payments = ProjectCashBook.objects.filter(
        contract=contract,
        installment_order=installment,
        project_account_d3__is_payment=True
    ).order_by('deal_date')

    for payment in payments:
        cumulative_paid += payment.income or 0
        if cumulative_paid >= promised_amount:
            # 이 납부로 완납됨
            if payment.deal_date > due_date:
                return (payment.deal_date - due_date).days
            else:
                return 0  # 납부기일 내 완납

    return 0  # 완납되지 않음


def calculate_late_penalty(contract, installment, late_payment_amount, late_days):
    """
    간단한 연체료 계산

    Args:
        contract: Contract 인스턴스
        installment: InstallmentPaymentOrder 인스턴스
        late_payment_amount: 지연납부금액
        late_days: 지연일수

    Returns:
        연체료 금액
    """
    if late_days <= 0 or late_payment_amount <= 0:
        return 0

    if not installment.is_late_penalty or not installment.late_penalty_ratio:
        return 0

    # 일단위 연체료 계산
    from decimal import Decimal
    daily_rate = Decimal(str(installment.late_penalty_ratio)) / 100 / 365
    penalty = late_payment_amount * daily_rate * late_days

    return int(penalty)