"""
sales/services.py
-----------------
수수료 정산 자동 계산 서비스 모듈.

직영 대행사 (is_direct_managed=True)
    계약에 배정된 담당자(SalesPerson)의 duty에 따라 상담사/팀장/본부장에게
    계층별로 수수료를 분배하여 CommissionPayout + PayoutContractDetail 생성.

    duty 별 지급 규칙:
      '1' (상담사) : 상담사=agent_fee, 소속 팀장=leader_fee, 소속 본부장=director_fee
      '2' (팀장)   : 팀장=(agent_fee + leader_fee), 소속 본부장=director_fee
      '3','4' (본부장/총괄): 본부장=(agent_fee + leader_fee + director_fee)

외주 대행사 (is_direct_managed=False)
    시행사는 대행사에게만 정산 (agency_fee × 건수, VAT 10% 별도 표시).
    AgencyPayout + AgencyPayoutContractDetail 생성.
"""
from __future__ import annotations

from django.db.models import Sum

from sales.models import (
    CommissionClawback,
    CommissionPayout,
    CommissionPolicy,
    ContractSalesAgent,
    AgencyPayout,
    AgencyPayoutContractDetail,
    PayoutContractDetail,
    SalesPerson,
    SettlementPeriod,
)


# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────

def _resolve_policy(mapping: ContractSalesAgent, project) -> CommissionPolicy | None:
    """
    계약 매핑에 명시된 정책 우선 사용.
    없으면 유니트 타입→ 전체 공통 순으로 활성 정책 탐색.
    """
    if mapping.policy_id:
        return mapping.policy

    unit_type = getattr(mapping.contract, 'unit_type', None)
    return (
        CommissionPolicy.objects.filter(
            project=project, unit_type=unit_type, is_active=True
        ).first()
        or CommissionPolicy.objects.filter(
            project=project, unit_type__isnull=True, is_active=True
        ).first()
    )


def _find_leader(team) -> SalesPerson | None:
    """팀 내 재직 중인 팀장(duty='2') 첫 번째 반환"""
    return (
        SalesPerson.objects.filter(team=team, duty='2', status='1')
        .order_by('name')
        .first()
    )


def _find_director(team) -> SalesPerson | None:
    """
    상위 조직(parent_team) 내 재직 중인 본부장(duty='3' or '4') 탐색.
    상위 조직이 없으면 현재 팀에서도 탐색.
    """
    parent = getattr(team, 'parent', None)
    search_team = parent if parent else team
    return (
        SalesPerson.objects.filter(
            team=search_team, duty__in=('3', '4'), status='1'
        )
        .order_by('duty', 'name')
        .first()
    )


def _build_direct_targets(
    person: SalesPerson,
    team,
    policy: CommissionPolicy,
) -> list[tuple[SalesPerson, int, str]]:
    """
    직영 체제 수수료 수령자 목록 반환.
    반환형: [(SalesPerson, 금액, role_type), ...]
    """
    duty = person.duty
    targets: list[tuple[SalesPerson | None, int, str]] = []

    if duty == '1':  # 상담사가 담당자
        leader = _find_leader(team)
        director = _find_director(team)
        targets = [
            (person, policy.agent_fee, 'agent'),
            (leader, policy.leader_fee, 'leader'),
            (director, policy.director_fee, 'director'),
        ]
    elif duty == '2':  # 팀장이 직접 담당
        director = _find_director(team)
        targets = [
            (person, policy.agent_fee + policy.leader_fee, 'leader'),
            (director, policy.director_fee, 'director'),
        ]
    elif duty in ('3', '4'):  # 본부장/총괄이 직접 담당
        targets = [
            (person, policy.agent_fee + policy.leader_fee + policy.director_fee, 'director'),
        ]
    else:  # 지원/기타 → 상담사 기준 처리
        leader = _find_leader(team)
        director = _find_director(team)
        targets = [
            (person, policy.agent_fee, 'agent'),
            (leader, policy.leader_fee, 'leader'),
            (director, policy.director_fee, 'director'),
        ]

    return [(p, fee, role) for p, fee, role in targets if p is not None and fee > 0]


# ─────────────────────────────────────────────
# 퍼블릭 서비스 함수
# ─────────────────────────────────────────────

def generate_period_payouts(period: SettlementPeriod) -> dict:
    """
    정산 회차(period)에 해당하는 기간 내 계약 매핑을 조회하고,
    직영/외주 분기에 따라 CommissionPayout 또는 AgencyPayout을 자동 생성/갱신한다.

    Returns:
        {
            'direct_person_count': int,  # 직영 정산 인원 수
            'agency_count':        int,  # 외주 대행사 수
            'total_contracts':     int,  # 총 계약 건수
            'total_gross_amount':  int,  # 직영 총 지급액
            'total_agency_amount': int,  # 외주 총 지급액 (VAT 포함)
        }
    """
    # ── 이중 정산 방지: 이미 다른 정산 회차에 포함된 계약건 제외 ──
    other_settled_contract_ids = set(
        PayoutContractDetail.objects.filter(
            payout__period__project=period.project,
        ).exclude(payout__period=period).values_list('contract_id', flat=True)
    ) | set(
        AgencyPayoutContractDetail.objects.filter(
            payout__period__project=period.project,
        ).exclude(payout__period=period).values_list('contract_id', flat=True)
    )

    # ── 정산 대상 계약 수집 ──
    # 1. 회차 마감일(end_date) 이전의 계약 (과거 미정산 소급건 포함)
    # 2. 관리자가 '정산 승인(is_settlement_approved=True)' 처리한 건만 포함 (서류 미비/분납 중인 보류건 자동 제외)
    # 3. 이미 다른 회차에 배정/정산 완료된 건은 절대 제외 (이중 정산 방지)
    mappings = ContractSalesAgent.objects.filter(
        contract__project=period.project,
        contract_date__lte=period.end_date,
        is_settlement_approved=True,
    ).select_related(
        'contract__unit_type',
        'agency',
        'sales_person__team__agency',
        'sales_person__team__parent',
        'team__agency',
        'team__parent',
        'policy',
    )

    if other_settled_contract_ids:
        mappings = mappings.exclude(contract_id__in=other_settled_contract_ids)

    # ── 재계산 시 기존 회차의 Payout 및 상세 내역 초기화 ──
    period.payouts.all().delete()
    period.agency_payouts.all().delete()

    # ── 직영 매핑: person_id → {person, team, [(contract, fee, role_type)]} ──
    direct_map: dict[int, dict] = {}
    # ── 대행사 매핑: agency_id → {agency, is_direct, [(contract, fee)]} ──
    agency_map: dict[int, dict] = {}

    # 실제 계약 건수 (cascade 중복 제외한 원천 계약 수)
    direct_contract_count = 0
    agency_contract_count = 0
    direct_agency_fee_total = 0  # 직영 대행사 차지(agency_fee) 합계
    direct_supply_price = 0      # 직영 계약 총 분양수수료 공급가액 (인력 수수료 + 대행사 차지)

    for m in mappings:
        agency = m.agency or (m.team.agency if m.team else None)
        if not agency:
            continue
        is_direct = agency.is_direct_managed
        policy = _resolve_policy(m, period.project)

        if is_direct and m.sales_person:
            direct_contract_count += 1
            agency_fee = policy.agency_fee if policy else 0
            direct_agency_fee_total += agency_fee

            # 계약 건당 총 공급가액 (인력 수수료 + 대행사 수수료)
            unit_total_fee = (
                (policy.agent_fee + policy.leader_fee + policy.director_fee + policy.agency_fee)
                if policy else 0
            )
            direct_supply_price += unit_total_fee

            # 직영 대행사 청구 집계용
            aid = agency.pk
            if aid not in agency_map:
                agency_map[aid] = {
                    'agency': agency,
                    'is_direct': True,
                    'contracts': [],
                }
            agency_map[aid]['contracts'].append({
                'contract': m.contract,
                'fee': unit_total_fee,
            })

            # 직영 운영인력 계층별 타깃
            targets = _build_direct_targets(m.sales_person, m.team, policy) if policy else []
            for person, fee, role in targets:
                pid = person.pk
                if pid not in direct_map:
                    direct_map[pid] = {
                        'person': person,
                        'contracts': [],
                    }
                direct_map[pid]['contracts'].append({
                    'contract': m.contract,
                    'fee': fee,
                    'role_type': role,
                })
        else:
            # 외주: 대행사 단위 집계
            agency_contract_count += 1
            aid = agency.pk
            agency_fee = policy.agency_fee if policy else 0
            if aid not in agency_map:
                agency_map[aid] = {
                    'agency': agency,
                    'is_direct': False,
                    'contracts': [],
                }
            agency_map[aid]['contracts'].append({
                'contract': m.contract,
                'fee': agency_fee,
            })

    # ── 직영 CommissionPayout 생성/갱신 ──
    direct_person_count = 0

    for pid, data in direct_map.items():
        person: SalesPerson = data['person']
        c_list = data['contracts']
        comm_sum = sum(c['fee'] for c in c_list)
        c_count = len(c_list)

        # 미상계 환수금
        clawbacks = CommissionClawback.objects.filter(
            sales_person=person, is_settled=False
        )
        clawback_sum = clawbacks.aggregate(total=Sum('amount'))['total'] or 0

        payout, created = CommissionPayout.objects.get_or_create(
            period=period,
            sales_person=person,
            defaults={
                'contract_count': c_count,
                'commission_amount': comm_sum,
                'deduction_amount': clawback_sum,
                'bank_name': person.bank_name,
                'account_number': person.account_number,
                'account_holder': person.account_holder,
            },
        )
        if not created:
            payout.contract_count = c_count
            payout.commission_amount = comm_sum
            payout.deduction_amount = clawback_sum
            payout.save()

        payout.contract_details.all().delete()
        PayoutContractDetail.objects.bulk_create([
            PayoutContractDetail(
                payout=payout,
                contract=c['contract'],
                role_type=c['role_type'],
                unit_fee=c['fee'],
            )
            for c in c_list
        ])

        if clawback_sum > 0:
            clawbacks.update(is_settled=True, settled_payout=payout)

        direct_person_count += 1

    # ── 대행사 AgencyPayout 생성/갱신 (직영 청구 + 외주 정산) ──
    agency_count = 0

    for aid, data in agency_map.items():
        agency = data['agency']
        is_direct = data.get('is_direct', False)
        c_list = data['contracts']
        fee_sum = sum(c['fee'] for c in c_list)
        c_count = len(c_list)

        note_text = (
            f'[직영 대행 청구] 운영인력 인센티브 + 대행사 몫 포함 (VAT 10% 별도 가산)'
            if is_direct else '[외주 대행 정산]'
        )

        ap, created = AgencyPayout.objects.get_or_create(
            period=period,
            agency=agency,
            defaults={
                'contract_count': c_count,
                'agency_fee_sum': fee_sum,
                'business_number': agency.business_number,
                'note': note_text,
            },
        )
        if not created:
            ap.contract_count = c_count
            ap.agency_fee_sum = fee_sum
            if not ap.note:
                ap.note = note_text
            ap.save()  # calculate_vat() called in save()

        ap.contract_details.all().delete()
        AgencyPayoutContractDetail.objects.bulk_create([
            AgencyPayoutContractDetail(
                payout=ap,
                contract=c['contract'],
                unit_fee=c['fee'],
            )
            for c in c_list
        ])

        agency_count += 1

    # 실제 원천 계약 건수 (cascade 중복 제외)
    total_contracts = direct_contract_count + agency_contract_count

    # ── 회차 전체 집계 갱신 ──
    direct_payouts = period.payouts.all()
    period.total_contracts = total_contracts
    period.total_gross_amount = direct_payouts.aggregate(s=Sum('gross_amount'))['s'] or 0
    period.total_tax_amount = direct_payouts.aggregate(s=Sum('total_tax'))['s'] or 0
    period.total_net_amount = direct_payouts.aggregate(s=Sum('net_amount'))['s'] or 0

    # 대행사 몫 및 시행사 청구 금액 (직영 + 외주)
    external_supply_price = sum(
        sum(c['fee'] for c in data['contracts'])
        for data in agency_map.values()
        if not data.get('is_direct', False)
    )
    period.agency_fee_total = direct_agency_fee_total
    period.billing_supply_price = direct_supply_price + external_supply_price
    period.billing_vat = int(period.billing_supply_price * 0.1 // 10 * 10)
    period.billing_total_amount = period.billing_supply_price + period.billing_vat
    period.save()

    agency_payouts = period.agency_payouts.all()
    total_agency_amount = agency_payouts.aggregate(s=Sum('total_amount'))['s'] or 0

    return {
        'direct_person_count': direct_person_count,
        'agency_count': agency_count,
        'total_contracts': total_contracts,
        'total_gross_amount': period.total_gross_amount,
        'total_agency_amount': total_agency_amount,
        'agency_fee_total': period.agency_fee_total,
        'billing_supply_price': period.billing_supply_price,
        'billing_vat': period.billing_vat,
        'billing_total_amount': period.billing_total_amount,
    }
