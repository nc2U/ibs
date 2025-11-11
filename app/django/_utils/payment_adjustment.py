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

from datetime import date
from decimal import Decimal
from typing import Dict, Optional, Any

from _utils.contract_price import get_payment_amount
from payment.models import InstallmentPaymentOrder


def get_effective_contract_date(contract) -> Optional[date]:
    """
    유효한 계약일 반환 (계약일 기준 할인/가산금 계산용)

    Args:
        contract: Contract 인스턴스

    Returns:
        date or None: 유효한 계약일
        - Contract.sup_cont_date와 Contractor.contract_date 중 늦은 날
        - 하나만 있으면 그 날짜 반환
        - 둘 다 없으면 None 반환

    Logic:
        1. contract.sup_cont_date 확인
        2. contract.contractor.contract_date 확인 (related_name이 없으므로 contractor로 접근)
        3. 둘 중 늦은 날짜 반환 (max 사용)
    """
    try:
        # Contract의 공급계약 체결일
        sup_cont_date = getattr(contract, 'sup_cont_date', None)

        # Contractor의 계약일자 (OneToOneField이므로 contractor로 직접 접근)
        contractor_date = None
        if hasattr(contract, 'contractor') and contract.contractor:
            contractor_date = getattr(contract.contractor, 'contract_date', None)

        # 둘 다 없으면 None 반환
        if not sup_cont_date and not contractor_date:
            return None

        # 하나만 있으면 그것을 반환
        if sup_cont_date and not contractor_date:
            return sup_cont_date
        if contractor_date and not sup_cont_date:
            return contractor_date

        # 둘 다 있으면 늦은 날짜 반환
        return max(sup_cont_date, contractor_date)

    except AttributeError:
        # 모델 구조가 예상과 다른 경우
        return None


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


def calculate_all_installments_payment_allocation(contract) -> Dict[int, Dict[str, Any]]:
    """
    계약의 모든 회차에 대해 Waterfall 충당 방식으로 납부 할당 계산

    납부 시점마다 누적 계산하여 회차별 완납 여부를 판정합니다.
    등록된 회차부터 충당하고, 남은 금액으로 다음 회차들을 순차 충당합니다.

    Returns:
        dict: {
            installment_id: {
                'installment_order': InstallmentPaymentOrder,
                'promised_amount': int,
                'paid_amount': int,  # Waterfall 충당 후 실제 납부액
                'remaining_amount': int,
                'is_fully_paid': bool,
                'fully_paid_date': date or None,  # 완납일 (충당 시점)
                'due_date': date,
                'is_late': bool,
                'late_days': int,
                'late_payment_amount': int,
                'payment_sources': list  # 충당에 사용된 납부 내역
            }
        }
    """
    from cash.models import ProjectCashBook
    from datetime import date as date_type

    # 모든 회차 조회 (순서대로)
    all_installments = InstallmentPaymentOrder.objects.filter(
        project=contract.project,
        type_sort=contract.unit_type.sort
    ).order_by('pay_code')

    # 모든 납부 내역 조회 (시간순)
    all_payments = ProjectCashBook.objects.payment_records().filter(
        contract=contract
    ).exclude(income__isnull=True).order_by('deal_date', 'id')

    # 회차별 상태 초기화
    installment_status = {}
    for inst in all_installments:
        promised = get_payment_amount(contract, inst)
        installment_status[inst.id] = {
            'installment_order': inst,
            'promised_amount': promised,
            'paid_amount': 0,
            'remaining_amount': promised,
            'is_fully_paid': False,
            'fully_paid_date': None,
            'due_date': inst.extra_due_date or inst.pay_due_date,
            'is_late': False,
            'late_days': 0,
            'late_payment_amount': 0,
            'payment_sources': []
        }

    # 시간순으로 납부 처리 (Waterfall Allocation)
    for payment in all_payments:
        payment_amount = payment.income
        payment_date = payment.deal_date
        target_installment = payment.installment_order

        if not target_installment:
            continue

        remaining_payment = payment_amount

        # 1. 타겟 회차 이전의 미납 회차들 우선 충당 (Waterfall 핵심)
        previous_installments = [inst for inst in all_installments
                                 if inst.pay_code < target_installment.pay_code]

        for prev_inst in previous_installments:
            if remaining_payment <= 0:
                break

            prev_status = installment_status[prev_inst.id]
            if not prev_status['is_fully_paid']:
                allocated = min(remaining_payment, prev_status['remaining_amount'])
                prev_status['paid_amount'] += allocated
                prev_status['remaining_amount'] -= allocated
                remaining_payment -= allocated

                prev_status['payment_sources'].append({
                    'payment_id': payment.id,
                    'payment_date': payment_date,
                    'allocated_amount': allocated,
                    'source_installment': target_installment.pay_name
                })

                # 완납 체크
                if prev_status['remaining_amount'] <= 0:
                    prev_status['is_fully_paid'] = True
                    prev_status['fully_paid_date'] = payment_date

        # 2. 타겟 회차 충당
        if remaining_payment > 0:
            target_status = installment_status[target_installment.id]
            if not target_status['is_fully_paid']:
                allocated = min(remaining_payment, target_status['remaining_amount'])
                target_status['paid_amount'] += allocated
                target_status['remaining_amount'] -= allocated
                remaining_payment -= allocated

                target_status['payment_sources'].append({
                    'payment_id': payment.id,
                    'payment_date': payment_date,
                    'allocated_amount': allocated,
                    'source_installment': target_installment.pay_name
                })

                # 완납 체크
                if target_status['remaining_amount'] <= 0:
                    target_status['is_fully_paid'] = True
                    target_status['fully_paid_date'] = payment_date

        # 3. 남은 금액으로 다음 회차들 순차 충당
        if remaining_payment > 0:
            next_installments = [inst for inst in all_installments
                                 if inst.pay_code > target_installment.pay_code]

            for next_inst in next_installments:
                if remaining_payment <= 0:
                    break

                next_status = installment_status[next_inst.id]
                if not next_status['is_fully_paid']:
                    allocated = min(remaining_payment, next_status['remaining_amount'])
                    next_status['paid_amount'] += allocated
                    next_status['remaining_amount'] -= allocated
                    remaining_payment -= allocated

                    next_status['payment_sources'].append({
                        'payment_id': payment.id,
                        'payment_date': payment_date,
                        'allocated_amount': allocated,
                        'source_installment': target_installment.pay_name
                    })

                    # 완납 체크
                    if next_status['remaining_amount'] <= 0:
                        next_status['is_fully_paid'] = True
                        next_status['fully_paid_date'] = payment_date

    # 3. 각 회차별 지연 여부 및 지연일수 계산
    today = date_type.today()

    for inst_id, status in installment_status.items():
        due_date = status['due_date']

        if not due_date:
            continue

        if status['is_fully_paid'] and status['fully_paid_date']:
            # 완납: 완납일 > 납부기한이면 지연
            if status['fully_paid_date'] > due_date:
                status['is_late'] = True
                status['late_days'] = (status['fully_paid_date'] - due_date).days
                status['late_payment_amount'] = status['promised_amount']
        else:
            # 미완납: 오늘 > 납부기한이면 지연
            if today > due_date:
                status['is_late'] = True
                status['late_days'] = (today - due_date).days
                status['late_payment_amount'] = status['remaining_amount']

    return installment_status


def calculate_segmented_late_penalty(contract, installment, as_of_date=None) -> Dict[str, Any]:
    """
    부분 납부 시 구간별 연체료 계산 (분할 계산 방식)

    미완납 상태에서 부분 납부가 여러 번 발생할 경우, 각 구간별로 미납금액 × 일수를 계산합니다.

    Args:
        contract: Contract 인스턴스
        installment: InstallmentPaymentOrder 인스턴스
        as_of_date: 기준일 (None이면 오늘)

    Returns:
        dict: {
            'segments': [
                {
                    'period_start': date,      # 구간 시작일
                    'period_end': date,        # 구간 종료일
                    'days': int,               # 구간 일수
                    'unpaid_amount': int,      # 구간 미납액
                    'penalty': int             # 구간 연체료
                },
                ...
            ],
            'total_penalty': int,              # 총 연체료
            'is_fully_paid': bool,             # 완납 여부
            'promised_amount': int,            # 약정금액
            'total_paid': int                  # 총 납부액
        }

    Examples:
        >>> # 50M 약정, 납부기한 2024-06-14
        >>> # 2024-10-15: 30M 납부 → 구간1: 50M × 123일
        >>> # 2024-12-20: 20M 납부 → 구간2: 20M × 66일
        >>> # 총 연체료: 구간1 + 구간2
    """
    from cash.models import ProjectCashBook
    from datetime import date as date_type

    if as_of_date is None:
        as_of_date = date_type.today()

    # 연체 가산 설정 확인
    if not installment.is_late_penalty or not installment.late_penalty_ratio:
        return {
            'segments': [],
            'total_penalty': 0,
            'is_fully_paid': False,
            'promised_amount': 0,
            'total_paid': 0
        }

    # 약정금액 및 납부기한
    promised = get_payment_amount(contract, installment)
    due_date = installment.extra_due_date or installment.pay_due_date

    if not due_date:
        return {
            'segments': [],
            'total_penalty': 0,
            'is_fully_paid': False,
            'promised_amount': promised,
            'total_paid': 0
        }

    penalty_rate = installment.late_penalty_ratio

    # 해당 회차로 등록된 납부 내역 조회 (시간순)
    payments = ProjectCashBook.objects.payment_records().filter(
        contract=contract,
        installment_order=installment
    ).exclude(income__isnull=True).order_by('deal_date')

    segments = []
    cumulative_paid = 0
    prev_date = due_date

    # 각 납부 시점마다 구간 계산
    for payment in payments:
        # 이전 구간의 미납금
        unpaid = promised - cumulative_paid

        # 구간 일수
        days = (payment.deal_date - prev_date).days

        # 구간 연체료 계산
        if days > 0 and unpaid > 0 and payment.deal_date > due_date:
            penalty = calculate_daily_interest(unpaid, penalty_rate, days)
            segments.append({
                'period_start': prev_date,
                'period_end': payment.deal_date,
                'days': days,
                'unpaid_amount': unpaid,
                'penalty': penalty
            })

        cumulative_paid += payment.income or 0
        prev_date = payment.deal_date

    # 아직 미완납이면 현재(발행일)까지 구간 추가
    is_fully_paid = cumulative_paid >= promised

    if not is_fully_paid:
        unpaid = promised - cumulative_paid
        days = (as_of_date - prev_date).days

        if days > 0 and unpaid > 0:
            penalty = calculate_daily_interest(unpaid, penalty_rate, days)
            segments.append({
                'period_start': prev_date,
                'period_end': as_of_date,
                'days': days,
                'unpaid_amount': unpaid,
                'penalty': penalty
            })

    return {
        'segments': segments,
        'total_penalty': sum(seg['penalty'] for seg in segments),
        'is_fully_paid': is_fully_paid,
        'promised_amount': promised,
        'total_paid': cumulative_paid
    }


def calculate_installment_paid_status_with_priority(
        contract,
        installment_order,
        payments_qs=None
) -> Dict[str, Any]:
    """
    우선순위 납부 충당을 고려한 회차별 완납 여부 계산

    새로운 방식: 전체 납부 충당을 계산한 후 해당 회차 정보 반환
    """
    # 전체 회차의 납부 충당 계산
    all_status = calculate_all_installments_payment_allocation(contract)

    # 해당 회차의 상태 반환
    installment_status = all_status.get(installment_order.id, {})

    return {
        'is_fully_paid': installment_status.get('is_fully_paid', False),
        'paid_amount': installment_status.get('paid_amount', 0),
        'promised_amount': installment_status.get('promised_amount', 0),
        'fully_paid_date': installment_status.get('fully_paid_date', None),
        'remaining_amount': installment_status.get('remaining_amount', 0),
        'payment_count': len(installment_status.get('payment_sources', [])),
        'late_days': installment_status.get('late_days', 0)
    }


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
    from cash.models import ProjectCashBook

    # 약정금액 계산
    promised_amount = get_payment_amount(contract, installment_order)

    # 납부내역 조회 (payment_records() 사용으로 최적화)
    if payments_qs is None:
        payments_qs = ProjectCashBook.objects.payment_records().filter(
            contract=contract,
            installment_order=installment_order
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

    # 4. 계약일 확인 (계약일 이후 회차만 할인 대상)
    contract_date = get_effective_contract_date(contract)

    # 5. 약정일/선납 기준일 결정
    # prep_ref_date가 있으면 우선, 없으면 pay_due_date 사용
    due_date = installment_order.prep_ref_date or installment_order.pay_due_date

    if not due_date:
        return None

    # 6. 계약일 이후 회차인지 확인 (계약일이 있는 경우만)
    if contract_date and due_date < contract_date:
        return None

    # 7. 선납 여부 확인 (완납일 < 약정일)
    if fully_paid_date >= due_date:
        return None

    # 8. 선납 일수 계산
    discount_days = (due_date - fully_paid_date).days

    # 9. 할인 금액 계산
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


def get_first_due_date_after_contract(contract, current_date=None) -> Optional[date]:
    """
    계약일 이후 첫 번째 도래 회차의 납부기한일 반환

    Args:
        contract: Contract 인스턴스
        current_date: 기준일 (None이면 오늘 날짜 사용)

    Returns:
        date or None: 계약일 이후 첫 번째 도래 회차의 납부기한일

    Logic:
        1. 계약일 이후 모든 회차 조회
        2. 현재일 기준 도래한 회차들 중 가장 빠른 납부기한일 반환
    """

    if current_date is None:
        current_date = date.today()

    # 계약일 확인
    contract_date = get_effective_contract_date(contract)
    if not contract_date:
        return None

    # 계약일 이후 도래한 회차들 조회
    installments = InstallmentPaymentOrder.objects.filter(
        project=contract.project,
        pay_due_date__gte=contract_date,  # 계약일 이후
        pay_due_date__lte=current_date  # 현재일까지 도래
    ).order_by('pay_due_date')

    # 첫 번째 도래 회차의 납부기한일 반환
    first_installment = installments.first()
    return first_installment.pay_due_date if first_installment else None


def calculate_late_penalty(payment) -> Optional[Dict[str, Any]]:
    """
    개별 납부건의 연체 가산금 계산 (계약일 이후 첫 도래 회차 기준 연체일수)

    Args:
        payment: ProjectCashBook 인스턴스

    Returns:
        dict or None: {
            'penalty_amount': int,       # 가산 금액
            'late_days': int,            # 연체 일수 (계약일 이후 첫 도래 회차 기준)
            'penalty_rate': Decimal,     # 가산율 (연이율 %)
            'payment_amount': int,       # 납부 금액
            'payment_date': date,        # 납부일
            'due_date': date,            # 약정일
            'extra_due_date': date,      # 연체 기준일 (있는 경우)
            'first_due_date': date       # 계약일 이후 첫 도래 회차 기준일
        } or None (가산 대상이 아닌 경우)

    Logic:
        1. installment_order.is_late_penalty = True 확인
        2. 계약일 이후 회차인지 확인
        3. 계약일 이후 첫 도래 회차 기준일로 연체일수 계산
        4. 가산금 계산: (현재일 - 첫도래기준일) × (가산율/365) × 납부금액

    Examples:
        >>> # 계약일: 2024-08-15, 첫 도래: 2024-09-30
        >>> # 납부금액 5,000,000원, 현재일 2024-11-15, 가산율 10%
        >>> # 연체일수 = (11월15일 - 9월30일) = 46일
        >>> # 가산금 = 5,000,000 × 10% ÷ 365 × 46 = 62,945원
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

    # 4. 계약일 확인 (계약일 이후 회차만 가산금 대상)
    try:
        contract = payment.contract
        contract_date = get_effective_contract_date(contract)
    except AttributeError:
        # payment에서 contract를 찾을 수 없는 경우
        contract_date = None

    # 5. 약정일/연체 기준일 결정
    # extra_due_date가 있으면 우선, 없으면 pay_due_date 사용
    due_date = installment_order.extra_due_date or installment_order.pay_due_date

    if not due_date:
        return None

    # 6. 계약일 이후 회차인지 확인 (계약일이 있는 경우만)
    if contract_date and due_date < contract_date:
        return None

    # 7. 계약일 이후 첫 번째 도래 회차 기준일 확인
    first_due_date = get_first_due_date_after_contract(contract, payment_date)
    if not first_due_date:
        return None

    # 8. 연체 기준일 계산: max(계약일 후 첫 도래 회차 납부기한, 당회차 납부기한)
    base_due_date = max(first_due_date, due_date)

    # 9. 연체 여부 확인 (기준일 이후인지)
    if payment_date <= base_due_date:
        return None

    # 10. 연체 일수 계산 (기준일부터)
    late_days = (payment_date - base_due_date).days

    # 10. 가산금 계산
    penalty_amount = calculate_daily_interest(payment_amount, penalty_rate, late_days)

    return {
        'penalty_amount': penalty_amount,
        'late_days': late_days,
        'penalty_rate': penalty_rate,
        'payment_amount': payment_amount,
        'payment_date': payment_date,
        'due_date': due_date,
        'extra_due_date': installment_order.extra_due_date,
        'first_due_date': first_due_date,
        'base_due_date': base_due_date
    }


def calculate_late_penalty_for_all_unpaid(contract, current_date=None) -> list:
    """
    기한 도과 시점부터 모든 미납 회차에 대한 연체 가산금 계산

    Args:
        contract: Contract 인스턴스
        current_date: 기준일 (None이면 오늘 날짜 사용)

    Returns:
        list: 미납 회차별 연체 가산금 정보
        [
            {
                'installment_order': InstallmentPaymentOrder,
                'remaining_amount': int,     # 미납 금액
                'penalty_amount': int,       # 연체 가산금
                'late_days': int,           # 연체일수 (통일된 기준)
                'penalty_rate': Decimal,     # 가산율
                'due_date': date,           # 회차별 납부기한
                'first_due_date': date      # 연체 계산 기준일
            },
            ...
        ]

    Logic:
        1. 계약일 이후 첫 번째 도래 회차의 납부기한일을 연체 기준일로 설정
        2. 기준일 이후 모든 미납 회차에 대해 연체 가산금 계산
        3. 모든 회차가 동일한 연체일수 적용 (기준일부터 현재일까지)
        4. 각 회차별 미납금액에 개별적으로 가산금 적용

    Examples:
        >>> # 계약일: 2024-08-15, 4차 중도금 기한: 2024-11-30, 현재일: 2024-12-15
        >>> # 미납회차: 4차(500만), 5차(300만), 6차(200만)
        >>> # 연체일수: 15일 (모든 회차 동일)
        >>> # 4차 가산금: 500만 × 10% ÷ 365 × 15
        >>> # 5차 가산금: 300만 × 10% ÷ 365 × 15
        >>> # 6차 가산금: 200만 × 10% ÷ 365 × 15
    """

    if current_date is None:
        current_date = date.today()

    # 1. 계약일 확인
    contract_date = get_effective_contract_date(contract)
    if not contract_date:
        return []

    # 2. 계약일 이후 첫 번째 도래 회차의 납부기한일 확인
    first_due_date = get_first_due_date_after_contract(contract, current_date)

    # 계약일 이후 도래 회차가 없는 경우, 계약일을 연체 기준일로 사용
    if not first_due_date:
        # 계약일 이전 미납 회차가 있는지 확인
        pre_contract_installments = InstallmentPaymentOrder.objects.filter(
            project=contract.project,
            type_sort=contract.unit_type.sort,
            pay_due_date__lt=contract_date  # 계약일 이전
        ).exists()

        if not pre_contract_installments:
            return []

        # 계약일을 연체 기준일로 설정
        first_due_date = contract_date

    # 3. 연체 여부 확인 (현재일이 연체 기준일을 넘었는지)
    if current_date <= first_due_date:
        return []

    # 4. 연체일수 계산 (모든 회차에 동일 적용)
    late_days = (current_date - first_due_date).days

    # 5. 모든 회차 조회 (계약일 이전/이후 모두 포함)
    all_installments = InstallmentPaymentOrder.objects.filter(
        project=contract.project,
        type_sort=contract.unit_type.sort  # 계약 타입에 맞는 모든 회차
    ).order_by('pay_code')

    late_penalties = []

    for installment in all_installments:
        # 연체 가산 설정 확인
        if not installment.is_late_penalty:
            continue

        # 가산율 확인
        penalty_rate = installment.late_penalty_ratio
        if not penalty_rate or penalty_rate <= 0:
            continue

        # 완납 상태 확인
        paid_status = calculate_installment_paid_status(contract, installment)

        # 미완납인 경우만 연체 가산금 적용
        if not paid_status['is_fully_paid'] and paid_status['remaining_amount'] > 0:
            remaining_amount = paid_status['remaining_amount']

            # 연체 가산금 계산
            penalty_amount = calculate_daily_interest(remaining_amount, penalty_rate, late_days)

            late_penalties.append({
                'installment_order': installment,
                'remaining_amount': remaining_amount,
                'penalty_amount': penalty_amount,
                'late_days': late_days,
                'penalty_rate': penalty_rate,
                'due_date': installment.pay_due_date,
                'first_due_date': first_due_date,
                'is_before_contract': installment.pay_due_date < contract_date if contract_date else False
            })

    return late_penalties


def calculate_completed_installment_penalty(
        contract,
        installment_order,
        payments_qs=None
) -> Optional[Dict[str, Any]]:
    """
    완납된 회차의 연체 가산금 계산 (완납일 기준)

    Args:
        contract: Contract 인스턴스
        installment_order: InstallmentPaymentOrder 인스턴스
        payments_qs: ProjectCashBook QuerySet (선택)

    Returns:
        dict or None: {
            'penalty_amount': int,       # 가산 금액
            'late_days': int,            # 연체 일수 (완납일 기준)
            'penalty_rate': Decimal,     # 가산율 (연이율 %)
            'payment_amount': int,       # 약정금액
            'fully_paid_date': date,     # 완납일
            'due_date': date,            # 약정일
            'base_due_date': date        # 연체 기준일
        } or None (연체 대상이 아닌 경우)

    Logic:
        완납된 회차의 경우 실제 완납일을 기준으로 연체일수를 계산
        연체일수 = 완납일 - max(계약일 후 첫 도래 회차 기준일, 당회차 납부기일)
    """
    # 1. 완납 상태 확인
    paid_status = calculate_installment_paid_status(contract, installment_order, payments_qs)

    if not paid_status['is_fully_paid'] or not paid_status['fully_paid_date']:
        return None

    # 2. 연체 가산 적용 여부 확인
    if not installment_order.is_late_penalty:
        return None

    # 3. 가산율 확인
    penalty_rate = installment_order.late_penalty_ratio
    if not penalty_rate or penalty_rate <= 0:
        return None

    fully_paid_date = paid_status['fully_paid_date']

    # 4. 계약일 확인 (계약일 이후 회차만 가산금 대상)
    contract_date = get_effective_contract_date(contract)

    # 5. 약정일/연체 기준일 결정
    due_date = installment_order.extra_due_date or installment_order.pay_due_date

    if not due_date:
        return None

    # 6. 계약일 이후 회차인지 확인 (계약일이 있는 경우만)
    if contract_date and due_date < contract_date:
        return None

    # 7. 계약일 이후 첫 번째 도래 회차 기준일 확인
    first_due_date = get_first_due_date_after_contract(contract, fully_paid_date)
    if not first_due_date:
        return None

    # 8. 연체 기준일 계산: max(계약일 후 첫 도래 회차 납부기한, 당회차 납부기한)
    base_due_date = max(first_due_date, due_date)

    # 9. 연체 여부 확인 (완납일이 기준일 이후인지)
    if fully_paid_date <= base_due_date:
        return None

    # 10. 연체 일수 계산 (완납일 기준)
    late_days = (fully_paid_date - base_due_date).days

    # 11. 가산금 계산
    penalty_amount = calculate_daily_interest(paid_status['promised_amount'], penalty_rate, late_days)

    return {
        'penalty_amount': penalty_amount,
        'late_days': late_days,
        'penalty_rate': penalty_rate,
        'payment_amount': paid_status['promised_amount'],
        'fully_paid_date': fully_paid_date,
        'due_date': due_date,
        'base_due_date': base_due_date
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

    # 납부내역 조회 (payment_records() 사용으로 최적화)
    payments_qs = ProjectCashBook.objects.payment_records().filter(
        contract=contract,
        installment_order=installment_order
    ).exclude(
        income__isnull=True
    ).order_by('deal_date', 'id')

    # 1. 완납 상태 조회
    paid_status = calculate_installment_paid_status(contract, installment_order, payments_qs)

    # 2. 선납 할인 계산
    prepayment_discount = calculate_prepayment_discount(contract, installment_order, payments_qs)
    total_discount = prepayment_discount['discount_amount'] if prepayment_discount else 0

    # 3. 연체 가산금 계산
    late_penalties = []
    total_penalty = 0

    if paid_status['is_fully_paid']:
        # 완납된 회차: 완납일 기준 연체료 계산
        completed_penalty_info = calculate_completed_installment_penalty(contract, installment_order, payments_qs)

        if completed_penalty_info:
            late_penalties.append({
                'payment_id': 'completed',
                'payment_date': completed_penalty_info['fully_paid_date'],
                **completed_penalty_info
            })
            total_penalty = completed_penalty_info['penalty_amount']
    else:
        # 미완납 회차: 각 납부건별 연체료 계산
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
    fully_paid_count = 0

    for installment in installments:
        summary = get_installment_adjustment_summary(contract, installment)
        installment_summaries.append(summary)

        total_promised_amount += summary['promised_amount']
        total_paid_amount += summary['paid_amount']
        total_discount += summary['total_discount']

        if summary['is_fully_paid']:
            fully_paid_count += 1

    # 새로운 연체 가산금 계산 (모든 미납 회차에 대해 통일된 기준)
    all_unpaid_penalties = calculate_late_penalty_for_all_unpaid(contract)
    total_penalty = sum(penalty['penalty_amount'] for penalty in all_unpaid_penalties)

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
        'total_installment_count': installments.count(),
        'all_unpaid_penalties': all_unpaid_penalties  # 새로운 연체 정보 추가
    }


def get_due_installments(contract, pub_date):
    """
    기도래 회차 목록 반환 (pub_date 기준, 계약일 이후 회차만)

    Args:
        contract: Contract 인스턴스
        pub_date: 기준일 (date 객체)

    Returns:
        QuerySet: 기도래 납부 회차 목록 (pay_due_date <= pub_date AND pay_due_date >= contract_date)

    Logic:
        - pay_due_date가 pub_date 이전인 회차만 반환
        - 계약일 이후 회차만 반환 (계약일이 있는 경우)
        - pay_code 순으로 정렬
    """

    # 기본 조건: pay_due_date <= pub_date
    queryset = InstallmentPaymentOrder.objects.filter(
        project=contract.project,
        pay_due_date__lte=pub_date
    )

    # 계약일 이후 회차만 필터링 (계약일이 있는 경우)
    contract_date = get_effective_contract_date(contract)
    if contract_date:
        queryset = queryset.filter(pay_due_date__gte=contract_date)

    return queryset.order_by('pay_code')


def get_unpaid_installments(contract, pub_date):
    """
    미납 회차 목록 반환 (pub_date 기준, 기도래 + 미완납, 계약일 무관)

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
                'late_days': int,  # 연체일수 (첫 도래 회차 기준일 이후부터 계산)
                'is_overdue': bool,  # 연체 여부
                'first_due_date': date  # 연체 기준일
            },
            ...
        ]

    Logic:
        1. 기도래 회차 중 미완납 회차만 추출 (계약일 이전 회차도 포함)
        2. 각 회차별 납부 상태 및 미납금액 계산
        3. 연체일수 계산: 계약일 이후 첫 도래 회차 기준일 이후부터만 계산
           - 첫 도래 회차 기준일 이전인 경우 연체일수 = 0
    """

    # 계약일 확인
    contract_date = get_effective_contract_date(contract)

    # 계약일 이후 첫 도래 회차 기준일 확인 (연체일수 계산용)
    first_due_date = get_first_due_date_after_contract(contract, pub_date)

    # 계약일 이후 도래 회차가 없는 경우 계약일을 기준일로 사용
    if not first_due_date and contract_date:
        first_due_date = contract_date

    # 모든 기도래 회차 조회 (계약일 필터링 없이)
    due_installments = InstallmentPaymentOrder.objects.filter(
        project=contract.project,
        pay_due_date__lte=pub_date
    ).order_by('pay_code')

    unpaid_list = []

    for installment in due_installments:
        # 완납 상태 확인
        paid_status = calculate_installment_paid_status(contract, installment)

        # 미완납인 경우만 포함
        if not paid_status['is_fully_paid']:
            due_date = installment.pay_due_date

            # 연체일수 계산 로직
            if contract_date and due_date and due_date < contract_date:
                # 계약일 이전 회차: 첫 도래 회차 기준일 사용
                if first_due_date and pub_date > first_due_date:
                    late_days = (pub_date - first_due_date).days
                else:
                    late_days = 0
            else:
                # 계약일 이후 회차 또는 계약일 없음: 자신의 납부기일 기준
                if due_date and pub_date > due_date:
                    late_days = (pub_date - due_date).days
                else:
                    late_days = 0

            unpaid_list.append({
                'installment_order': installment,
                'promised_amount': paid_status['promised_amount'],
                'paid_amount': paid_status['paid_amount'],
                'remaining_amount': paid_status['remaining_amount'],
                'due_date': due_date,
                'late_days': late_days,
                'is_overdue': late_days > 0,
                'first_due_date': first_due_date
            })

    return unpaid_list
