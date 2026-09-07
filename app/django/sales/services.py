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
    mappings = ContractSalesAgent.objects.filter(
        contract__project=period.project,
        contract_date__gte=period.start_date,
        contract_date__lte=period.end_date,
    ).select_related(
        'contract__unit_type',
        'sales_person__team__agency',
        'sales_person__team__parent',
        'team__agency',
        'team__parent',
        'policy',
    )

    # ── 직영 매핑: person_id → {person, team, [(contract, fee, role_type)]} ──
    direct_map: dict[int, dict] = {}
    # ── 외주 매핑: agency_id → {agency, [(contract, fee)]} ──
    agency_map: dict[int, dict] = {}

    for m in mappings:
        is_direct = m.team.agency.is_direct_managed
        policy = _resolve_policy(m, period.project)

        if is_direct:
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
            agency = m.team.agency
            aid = agency.pk
            agency_fee = policy.agency_fee if policy else 0
            if aid not in agency_map:
                agency_map[aid] = {
                    'agency': agency,
                    'contracts': [],
                }
            agency_map[aid]['contracts'].append({
                'contract': m.contract,
                'fee': agency_fee,
            })

    # ── 직영 CommissionPayout 생성/갱신 ──
    direct_person_count = 0
    total_direct_contracts = 0

    for pid, data in direct_map.items():
        person: SalesPerson = data['person']
        c_list = data['contracts']
        comm_sum = sum(c['fee'] for c in c_list)
        c_count = len(c_list)
        total_direct_contracts += c_count

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

    # ── 외주 AgencyPayout 생성/갱신 ──
    agency_count = 0
    total_agency_contracts = 0

    for aid, data in agency_map.items():
        agency = data['agency']
        c_list = data['contracts']
        fee_sum = sum(c['fee'] for c in c_list)
        c_count = len(c_list)
        total_agency_contracts += c_count

        ap, created = AgencyPayout.objects.get_or_create(
            period=period,
            agency=agency,
            defaults={
                'contract_count': c_count,
                'agency_fee_sum': fee_sum,
                'business_number': agency.business_number,
            },
        )
        if not created:
            ap.contract_count = c_count
            ap.agency_fee_sum = fee_sum
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

    total_contracts = total_direct_contracts + total_agency_contracts

    # ── 회차 전체 집계 갱신 ──
    direct_payouts = period.payouts.all()
    period.total_contracts = total_contracts
    period.total_gross_amount = direct_payouts.aggregate(s=Sum('gross_amount'))['s'] or 0
    period.total_tax_amount = direct_payouts.aggregate(s=Sum('total_tax'))['s'] or 0
    period.total_net_amount = direct_payouts.aggregate(s=Sum('net_amount'))['s'] or 0
    period.save()

    agency_payouts = period.agency_payouts.all()
    total_agency_amount = agency_payouts.aggregate(s=Sum('total_amount'))['s'] or 0

    return {
        'direct_person_count': direct_person_count,
        'agency_count': agency_count,
        'total_contracts': total_contracts,
        'total_gross_amount': period.total_gross_amount,
        'total_agency_amount': total_agency_amount,
    }
