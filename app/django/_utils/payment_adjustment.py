"""
Payment Adjustment Utilities

선납 할인 및 연체 가산금 계산을 위한 유틸리티 함수들

핵심 계산 로직:
- 완납 여부: 약정금액 ≤ 실제 납부금액 합계 (get_payment_amount 사용)
- 선납 할인: 완납 시점 기준 일괄 계산
- 연체 가산금: 각 납부건별 연체일수로 개별 계산

계정 구조:
    is_payment=True: 유효한 계약자의 납부만 (111, 811) - 할인/가산 대상
    is_payment=False: 유효 계약자 입금을 제외한 모든 계정
        예: 해지 입금 (112, 812), 환불 (113, 114, 813, 814), 기타 출금 등
"""

from decimal import Decimal
from typing import Dict, Optional, Any


def calculate_daily_interest(principal: int, annual_rate: Decimal, days: int) -> int:
    """
    일할 계산 (연이율 기준)

    Args:
        principal: 원금
        annual_rate: 연이율 (%)
        days: 일수

    Returns:
        int: 일할 계산된 이자/할인/가산금

    Examples:
        >>> calculate_daily_interest(10000000, Decimal('3.0'), 30)
        24657  # 10,000,000 × 3% ÷ 365 × 30일
    """
    if principal <= 0 or annual_rate <= 0 or days <= 0:
        return 0

    return int((annual_rate / Decimal('100') / Decimal('365')) * days * principal)


def calculate_installment_paid_status(
        contract,
        installment_order,
        payments_qs=None
) -> Dict[str, Any]:
    """
    회차별 완납 여부 및 완납일 계산

    Args:
        contract: Contract 인스턴스
        installment_order: InstallmentPaymentOrder 인스턴스
        payments_qs: ProjectCashBook QuerySet (선택, 없으면 자동 조회)

    Returns:
        dict: {
            'is_fully_paid': bool,           # 완납 여부
            'paid_amount': int,              # 실제 납부금액 합계
            'promised_amount': int,          # 약정금액
            'fully_paid_date': date or None, # 완납일 (완납된 경우만)
            'remaining_amount': int,         # 미납금액
            'payment_count': int             # 납부 횟수
        }

    Logic:
        - 약정금액: get_payment_amount(contract, installment_order)로 산출
        - 완납 여부: 약정금액 ≤ 실제 납부금액 합계
        - 완납일: 누적 납부금액이 약정금액 이상이 된 최초 날짜
    """
    from _utils.contract_price import get_payment_amount
    from cash.models import ProjectCashBook

    # 약정금액 계산
    promised_amount = get_payment_amount(contract, installment_order)

    # 납부내역 조회
    if payments_qs is None:
        payments_qs = ProjectCashBook.objects.filter(
            project=contract.project,
            contract=contract,
            installment_order=installment_order,
            project_account_d3__is_payment=True
        ).exclude(
            income__isnull=True
        ).order_by('deal_date', 'id')

    # 실제 납부금액 및 완납일 계산
    paid_amount = 0
    fully_paid_date = None
    payment_count = 0

    for payment in payments_qs:
        if payment.income:
            paid_amount += payment.income
            payment_count += 1

            # 완납일 체크 (누적 납부금액이 약정금액 이상이 된 최초 날짜)
            if fully_paid_date is None and paid_amount >= promised_amount:
                fully_paid_date = payment.deal_date

    # 완납 여부
    is_fully_paid = paid_amount >= promised_amount

    # 미납금액
    remaining_amount = max(0, promised_amount - paid_amount)

    return {
        'is_fully_paid': is_fully_paid,
        'paid_amount': paid_amount,
        'promised_amount': promised_amount,
        'fully_paid_date': fully_paid_date,
        'remaining_amount': remaining_amount,
        'payment_count': payment_count
    }


def calculate_prepayment_discount(
        contract,
        installment_order,
        payments_qs=None
) -> Optional[Dict[str, Any]]:
    """
    선납 할인 계산 (완납 시점 기준 일괄)

    Args:
        contract: Contract 인스턴스
        installment_order: InstallmentPaymentOrder 인스턴스
        payments_qs: ProjectCashBook QuerySet (선택)

    Returns:
        dict or None: {
            'discount_amount': int,      # 할인 금액
            'discount_days': int,        # 선납 일수
            'discount_rate': Decimal,    # 할인율 (연이율 %)
            'base_amount': int,          # 기준 금액 (약정금액)
            'fully_paid_date': date,     # 완납일
            'due_date': date,            # 약정일
            'prep_ref_date': date        # 선납 기준일 (있는 경우)
        } or None (할인 대상이 아닌 경우)

    Logic:
        1. installment_order.is_prep_discount = True 확인
        2. 완납 여부 및 완납일 확인
        3. 완납일 < 약정일 확인
        4. 할인 계산: (약정일 - 완납일) × (할인율/365) × 약정금액

    Examples:
        >>> # 약정금액 10,000,000원, 약정일 2025-12-31, 완납일 2025-12-01, 할인율 3%
        >>> # (31일 - 1일) = 30일 선납
        >>> # 할인금액 = 10,000,000 × 3% ÷ 365 × 30 = 24,657원
    """
    # 1. 선납 할인 적용 여부 확인
    if not installment_order or not installment_order.is_prep_discount:
        return None

    # 2. 할인율 확인
    discount_rate = installment_order.prep_discount_ratio
    if not discount_rate or discount_rate <= 0:
        return None

    # 3. 완납 상태 확인
    paid_status = calculate_installment_paid_status(contract, installment_order, payments_qs)

    if not paid_status['is_fully_paid'] or not paid_status['fully_paid_date']:
        return None

    fully_paid_date = paid_status['fully_paid_date']

    # 4. 약정일/선납 기준일 결정
    # prep_ref_date가 있으면 우선, 없으면 pay_due_date 사용
    due_date = installment_order.prep_ref_date or installment_order.pay_due_date

    if not due_date:
        return None

    # 5. 선납 여부 확인 (완납일 < 약정일)
    if fully_paid_date >= due_date:
        return None

    # 6. 선납 일수 계산
    discount_days = (due_date - fully_paid_date).days

    # 7. 할인 금액 계산
    base_amount = paid_status['promised_amount']
    discount_amount = calculate_daily_interest(base_amount, discount_rate, discount_days)

    return {
        'discount_amount': discount_amount,
        'discount_days': discount_days,
        'discount_rate': discount_rate,
        'base_amount': base_amount,
        'fully_paid_date': fully_paid_date,
        'due_date': due_date,
        'prep_ref_date': installment_order.prep_ref_date
    }


def calculate_late_penalty(payment) -> Optional[Dict[str, Any]]:
    """
    개별 납부건의 연체 가산금 계산 (각 납부건별 연체일수)

    Args:
        payment: ProjectCashBook 인스턴스

    Returns:
        dict or None: {
            'penalty_amount': int,       # 가산 금액
            'late_days': int,            # 연체 일수
            'penalty_rate': Decimal,     # 가산율 (연이율 %)
            'payment_amount': int,       # 납부 금액
            'payment_date': date,        # 납부일
            'due_date': date,            # 약정일
            'extra_due_date': date       # 연체 기준일 (있는 경우)
        } or None (가산 대상이 아닌 경우)

    Logic:
        1. installment_order.is_late_penalty = True 확인
        2. 납부일 > 약정일 확인
        3. 가산금 계산: (납부일 - 약정일) × (가산율/365) × 납부금액

    Examples:
        >>> # 납부금액 5,000,000원, 약정일 2025-01-31, 납부일 2025-03-01, 가산율 10%
        >>> # (3월1일 - 1월31일) = 29일 연체
        >>> # 가산금 = 5,000,000 × 10% ÷ 365 × 29 = 39,726원
    """
    # 1. 연체 가산 적용 여부 확인
    if not payment or not payment.installment_order:
        return None

    installment_order = payment.installment_order

    if not installment_order.is_late_penalty:
        return None

    # 2. 가산율 확인
    penalty_rate = installment_order.late_penalty_ratio
    if not penalty_rate or penalty_rate <= 0:
        return None

    # 3. 납부일 및 납부금액 확인
    if not payment.deal_date or not payment.income or payment.income <= 0:
        return None

    payment_date = payment.deal_date
    payment_amount = payment.income

    # 4. 약정일/연체 기준일 결정
    # extra_due_date가 있으면 우선, 없으면 pay_due_date 사용
    due_date = installment_order.extra_due_date or installment_order.pay_due_date

    if not due_date:
        return None

    # 5. 연체 여부 확인 (납부일 > 약정일)
    if payment_date <= due_date:
        return None

    # 6. 연체 일수 계산
    late_days = (payment_date - due_date).days

    # 7. 가산금 계산
    penalty_amount = calculate_daily_interest(payment_amount, penalty_rate, late_days)

    return {
        'penalty_amount': penalty_amount,
        'late_days': late_days,
        'penalty_rate': penalty_rate,
        'payment_amount': payment_amount,
        'payment_date': payment_date,
        'due_date': due_date,
        'extra_due_date': installment_order.extra_due_date
    }


def get_installment_adjustment_summary(
        contract,
        installment_order
) -> Dict[str, Any]:
    """
    회차별 선납 할인 및 연체 가산금 종합 정보

    Args:
        contract: Contract 인스턴스
        installment_order: InstallmentPaymentOrder 인스턴스

    Returns:
        dict: {
            'installment_order': InstallmentPaymentOrder,
            'promised_amount': int,               # 약정금액
            'paid_amount': int,                   # 실제 납부금액
            'is_fully_paid': bool,                # 완납 여부
            'fully_paid_date': date or None,      # 완납일
            'prepayment_discount': dict or None,  # 선납 할인 정보
            'late_penalties': list,               # 각 납부건별 연체 정보
            'total_discount': int,                # 총 할인 금액
            'total_penalty': int,                 # 총 가산 금액
            'net_adjustment': int,                # 순 조정 금액 (할인 - 가산금)
            'payment_count': int                  # 납부 횟수
        }

    Logic:
        1. 완납 상태 조회
        2. 선납 할인 계산 (완납 시점 기준 일괄)
        3. 각 납부건별 연체 가산금 계산
        4. 종합 집계
    """
    from cash.models import ProjectCashBook

    # 납부내역 조회
    payments_qs = ProjectCashBook.objects.filter(
        project=contract.project,
        contract=contract,
        installment_order=installment_order,
        project_account_d3__is_payment=True
    ).exclude(
        income__isnull=True
    ).order_by('deal_date', 'id')

    # 1. 완납 상태 조회
    paid_status = calculate_installment_paid_status(contract, installment_order, payments_qs)

    # 2. 선납 할인 계산
    prepayment_discount = calculate_prepayment_discount(contract, installment_order, payments_qs)
    total_discount = prepayment_discount['discount_amount'] if prepayment_discount else 0

    # 3. 각 납부건별 연체 가산금 계산
    late_penalties = []
    total_penalty = 0

    for payment in payments_qs:
        penalty_info = calculate_late_penalty(payment)
        if penalty_info:
            late_penalties.append({
                'payment_id': payment.id,
                'payment_date': payment.deal_date,
                **penalty_info
            })
            total_penalty += penalty_info['penalty_amount']

    # 4. 순 조정 금액 (할인 - 가산금)
    net_adjustment = total_discount - total_penalty

    return {
        'installment_order': installment_order,
        'promised_amount': paid_status['promised_amount'],
        'paid_amount': paid_status['paid_amount'],
        'is_fully_paid': paid_status['is_fully_paid'],
        'fully_paid_date': paid_status['fully_paid_date'],
        'prepayment_discount': prepayment_discount,
        'late_penalties': late_penalties,
        'total_discount': total_discount,
        'total_penalty': total_penalty,
        'net_adjustment': net_adjustment,
        'payment_count': paid_status['payment_count']
    }


def get_contract_adjustment_summary(contract) -> Dict[str, Any]:
    """
    계약별 전체 회차의 선납 할인 및 연체 가산금 종합 정보

    Args:
        contract: Contract 인스턴스

    Returns:
        dict: {
            'contract': Contract,
            'installments': list,              # 각 회차별 조정 정보
            'total_promised_amount': int,      # 총 약정금액
            'total_paid_amount': int,          # 총 납부금액
            'total_discount': int,             # 총 할인 금액
            'total_penalty': int,              # 총 가산 금액
            'net_adjustment': int,             # 순 조정 금액
            'fully_paid_count': int,           # 완납 회차 수
            'total_installment_count': int     # 전체 회차 수
        }
    """
    from payment.models import InstallmentPaymentOrder

    # 해당 계약의 모든 회차 조회
    installments = InstallmentPaymentOrder.objects.filter(
        project=contract.project,
        type_sort=contract.unit_type.sort
    ).order_by('pay_code', 'pay_time')

    # 각 회차별 조정 정보 수집
    installment_summaries = []
    total_promised_amount = 0
    total_paid_amount = 0
    total_discount = 0
    total_penalty = 0
    fully_paid_count = 0

    for installment in installments:
        summary = get_installment_adjustment_summary(contract, installment)
        installment_summaries.append(summary)

        total_promised_amount += summary['promised_amount']
        total_paid_amount += summary['paid_amount']
        total_discount += summary['total_discount']
        total_penalty += summary['total_penalty']

        if summary['is_fully_paid']:
            fully_paid_count += 1

    # 순 조정 금액
    net_adjustment = total_discount - total_penalty

    return {
        'contract': contract,
        'installments': installment_summaries,
        'total_promised_amount': total_promised_amount,
        'total_paid_amount': total_paid_amount,
        'total_discount': total_discount,
        'total_penalty': total_penalty,
        'net_adjustment': net_adjustment,
        'fully_paid_count': fully_paid_count,
        'total_installment_count': installments.count()
    }


def get_due_installments(contract, pub_date):
    """
    기도래 회차 목록 반환 (pub_date 기준)

    Args:
        contract: Contract 인스턴스
        pub_date: 기준일 (date 객체)

    Returns:
        QuerySet: 기도래 납부 회차 목록 (pay_due_date <= pub_date)

    Logic:
        - pay_due_date가 pub_date 이전인 회차만 반환
        - pay_code 순으로 정렬
    """
    from payment.models import InstallmentPaymentOrder

    return InstallmentPaymentOrder.objects.filter(
        project=contract.project,
        pay_due_date__lte=pub_date
    ).order_by('pay_code')


def get_unpaid_installments(contract, pub_date):
    """
    미납 회차 목록 반환 (pub_date 기준, 기도래 + 미완납)

    Args:
        contract: Contract 인스턴스
        pub_date: 기준일 (date 객체)

    Returns:
        list: 미납 회차 정보 리스트
        [
            {
                'installment_order': InstallmentPaymentOrder,
                'promised_amount': int,
                'paid_amount': int,
                'remaining_amount': int,
                'due_date': date,
                'late_days': int,  # 연체일수 (pub_date - due_date)
                'is_overdue': bool  # 연체 여부
            },
            ...
        ]

    Logic:
        1. 기도래 회차 중 미완납 회차만 추출
        2. 각 회차별 납부 상태 및 미납금액 계산
        3. 연체일수 계산 (pub_date - due_date)
    """
    from datetime import date

    due_installments = get_due_installments(contract, pub_date)
    unpaid_list = []

    for installment in due_installments:
        # 완납 상태 확인
        paid_status = calculate_installment_paid_status(contract, installment)

        # 미완납인 경우만 포함
        if not paid_status['is_fully_paid']:
            due_date = installment.pay_due_date
            late_days = (pub_date - due_date).days if due_date else 0

            unpaid_list.append({
                'installment_order': installment,
                'promised_amount': paid_status['promised_amount'],
                'paid_amount': paid_status['paid_amount'],
                'remaining_amount': paid_status['remaining_amount'],
                'due_date': due_date,
                'late_days': late_days,
                'is_overdue': late_days > 0
            })

    return unpaid_list
