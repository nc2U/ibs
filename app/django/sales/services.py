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
    시행사는 대행사에게 전체 수수료 일괄 정산
    (agent_fee + leader_fee + director_fee + agency_fee) × 건수, VAT 10% 별도 표시.
    대행사가 소속 영업 인력에게 내부 재정산하는 구조.
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
) -> tuple[list[tuple[SalesPerson, int, str]], int]:
    """
    직영 체제 수수료 수령자 목록 및 귀속 이익(미지급 fee) 계산.

    버블업(Bubble-Up) 규칙:
      - 팀장 없음 + 본부장 있음  → 본부장이 leader_fee + director_fee 합산 수령
      - 팀장 있음 + 본부장 없음  → 팀장은 leader_fee만 수령, director_fee → 귀속
      - 팀장 없음 + 본부장 없음  → leader_fee + director_fee 전액 → 귀속
      * 귀속(unallocated_fee): 직영 대행사에는 표시만, 외주는 합산 지급 대상

    Returns:
        targets: [(SalesPerson, fee, role_type), ...]
        unallocated_fee: 팀장/본부장 부재로 귀속된 fee 합계 (양수)
    """
    duty = person.duty
    leader = _find_leader(team)
    director = _find_director(team)
    targets: list[tuple[SalesPerson, int, str]] = []
    unallocated_fee = 0

    if duty == '1':  # 상담사가 담당자
        targets.append((person, policy.agent_fee, 'agent'))

        if leader and director:
            # 정상 구조: 팀장 + 본부장 모두 존재
            targets.append((leader, policy.leader_fee, 'leader'))
            targets.append((director, policy.director_fee, 'director'))
        elif not leader and director:
            # 팀장 없음 → 본부장이 leader_fee + director_fee 합산 수령
            targets.append((director, policy.leader_fee + policy.director_fee, 'director'))
        elif leader and not director:
            # 본부장 없음 → 팀장은 leader_fee만, director_fee → 귀속
            targets.append((leader, policy.leader_fee, 'leader'))
            unallocated_fee += policy.director_fee
        else:
            # 팀장도 본부장도 없음 → 전액 귀속
            unallocated_fee += policy.leader_fee + policy.director_fee

    elif duty == '2':  # 팀장이 직접 담당
        if director:
            targets.append((person, policy.agent_fee + policy.leader_fee, 'leader'))
            targets.append((director, policy.director_fee, 'director'))
        else:
            # 본부장 없음 → 팀장이 agent+leader 수령, director_fee → 귀속
            targets.append((person, policy.agent_fee + policy.leader_fee, 'leader'))
            unallocated_fee += policy.director_fee

    elif duty in ('3', '4'):  # 본부장/총괄이 직접 담당
        targets.append((person, policy.agent_fee + policy.leader_fee + policy.director_fee, 'director'))

    else:  # 지원/기타 → 상담사 기준 처리
        targets.append((person, policy.agent_fee, 'agent'))
        if leader and director:
            targets.append((leader, policy.leader_fee, 'leader'))
            targets.append((director, policy.director_fee, 'director'))
        elif not leader and director:
            targets.append((director, policy.leader_fee + policy.director_fee, 'director'))
        elif leader and not director:
            targets.append((leader, policy.leader_fee, 'leader'))
            unallocated_fee += policy.director_fee
        else:
            unallocated_fee += policy.leader_fee + policy.director_fee

    valid_targets = [(p, fee, role) for p, fee, role in targets if p is not None and fee > 0]
    return valid_targets, unallocated_fee


def validate_org_health(project) -> dict:
    """
    직영 영업 조직 무결성 검사.
    에러를 발생시키지 않고 문제 항목 목록을 반환한다.
    severity: 'error' (계약 정산 누락), 'warning' (fee 귀속 발생)
    """
    from django.db.models import Q
    from django.utils import timezone
    from sales.models import SalesAgency, SalesTeam, SalesPerson, CommissionPolicy
    from items.models import UnitType

    items = []
    direct_agencies = SalesAgency.objects.filter(
        project=project, is_direct_managed=True, is_active=True
    )

    for agency in direct_agencies:
        # 하위 팀이 없는 최하위 팀(leaf team)만 검사
        leaf_teams = SalesTeam.objects.filter(
            agency=agency, is_active=True, sub_teams__isnull=True
        )
        for team in leaf_teams:
            has_counselors = SalesPerson.objects.filter(team=team, duty='1', status='1').exists()
            if not has_counselors:
                continue  # 상담사 없는 팀은 검사 불필요

            has_leader = SalesPerson.objects.filter(team=team, duty='2', status='1').exists()
            search_team = team.parent if team.parent else team
            has_director = SalesPerson.objects.filter(
                team=search_team, duty__in=('3', '4'), status='1'
            ).exists()

            if not has_leader and not has_director:
                items.append({
                    'type': 'NO_LEADER_NO_DIRECTOR',
                    'severity': 'warning',
                    'agency': agency.name,
                    'team': str(team),
                    'message': (
                        f'[{agency.name}] {team.name} 팀에 팀장·본부장이 모두 없습니다. '
                        f'leader_fee + director_fee가 대행사에 귀속됩니다.'
                    ),
                })
            elif not has_leader:
                items.append({
                    'type': 'NO_LEADER',
                    'severity': 'warning',
                    'agency': agency.name,
                    'team': str(team),
                    'message': (
                        f'[{agency.name}] {team.name} 팀에 팀장이 없습니다. '
                        f'본부장이 leader_fee + director_fee를 합산 수령합니다.'
                    ),
                })
            elif not has_director:
                items.append({
                    'type': 'NO_DIRECTOR',
                    'severity': 'warning',
                    'agency': agency.name,
                    'team': str(team),
                    'message': (
                        f'[{agency.name}] {team.name} 팀의 상위 본부에 본부장이 없습니다. '
                        f'director_fee가 대행사에 귀속됩니다.'
                    ),
                })

    # 수수료 정책 미등록 타입 확인
    from django.utils import timezone as tz
    from django.db.models import Q as Q2
    today = tz.localdate()
    for ut in UnitType.objects.filter(project=project):
        has_policy = CommissionPolicy.objects.filter(
            project=project, is_active=True, start_date__lte=today
        ).filter(Q2(unit_type=ut) | Q2(unit_type__isnull=True)).exists()
        if not has_policy:
            items.append({
                'type': 'NO_POLICY',
                'severity': 'error',
                'unit_type': ut.name,
                'message': (
                    f'[{ut.name}] 타입에 적용 가능한 활성 수수료 정책이 없습니다. '
                    f'해당 타입 계약 건은 정산에서 제외됩니다.'
                ),
            })

    errors = [i for i in items if i['severity'] == 'error']
    return {
        'is_healthy': len(errors) == 0,
        'error_count': len(errors),
        'warning_count': len(items) - len(errors),
        'items': items,
    }


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

    # ── 직영 매핑: person_id → {person, [(contract, fee, role_type)]} ──
    direct_map: dict[int, dict] = {}
    # ── 대행사 매핑: agency_id → {agency, is_direct, [(contract, fee)], unallocated_fee} ──
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
                    'unallocated_fee': 0,
                }
            agency_map[aid]['contracts'].append({
                'contract': m.contract,
                'fee': unit_total_fee,
            })

            # 직영 운영인력 계층별 타깃 (bubble-up 로직 적용)
            if policy:
                targets, unallocated = _build_direct_targets(m.sales_person, m.team, policy)
                # 귀속 fee를 직영 대행사에 누적
                agency_map[aid]['unallocated_fee'] += unallocated
            else:
                targets = []

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
            # 외주 대행사가 소속 영업 인력에게 재정산하므로,
            # 시행사는 (agent_fee + leader_fee + director_fee + agency_fee) 전액을 대행사에 일괄 지급.
            agency_contract_count += 1
            aid = agency.pk
            # 전체 수수료 합산 = 정책 상 모든 fee 항목 합계
            total_policy_fee = (
                (policy.agent_fee + policy.leader_fee + policy.director_fee + policy.agency_fee)
                if policy else 0
            )
            if aid not in agency_map:
                agency_map[aid] = {
                    'agency': agency,
                    'is_direct': False,
                    'contracts': [],
                    'unallocated_fee': 0,
                }
            agency_map[aid]['contracts'].append({
                'contract': m.contract,
                'fee': total_policy_fee,
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
        unallocated = data.get('unallocated_fee', 0)

        note_parts = [
            '[직영 대행 청구] 운영인력 인센티브 + 대행사 몫 포함 (VAT 10% 별도 가산)'
            if is_direct else '[외주 대행 정산]'
        ]
        if unallocated > 0:
            note_parts.append(f'귀속 이익 {unallocated:,}원 포함 (팀장/본부장 부재로 미지급)')
        note_text = ' | '.join(note_parts)

        ap, created = AgencyPayout.objects.get_or_create(
            period=period,
            agency=agency,
            defaults={
                'contract_count': c_count,
                'agency_fee_sum': fee_sum,
                'unallocated_fee': unallocated,
                'business_number': agency.business_number,
                'note': note_text,
            },
        )
        if not created:
            ap.contract_count = c_count
            ap.agency_fee_sum = fee_sum
            ap.unallocated_fee = unallocated
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

    # ── 조직 건강 상태 검사 (경고 수집) ──
    org_health = validate_org_health(period.project)

    agency_payouts = period.agency_payouts.all()
    total_agency_amount = agency_payouts.aggregate(s=Sum('total_amount'))['s'] or 0
    total_unallocated_fee = sum(data.get('unallocated_fee', 0) for data in agency_map.values())

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
        # 귀속 이익: 팀장/본부장 부재로 미지급된 fee 합계 (직영 대행사 귀속, 표시 전용)
        'total_unallocated_fee': total_unallocated_fee,
        # 조직 건강 상태 경고 목록
        'org_warnings': org_health['items'],
        'org_is_healthy': org_health['is_healthy'],
    }
