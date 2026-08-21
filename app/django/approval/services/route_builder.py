from django.db.models import Q
from company.models import StaffAssignment, Staff, Department
from ..models import DocumentType


def extract_amount_from_content(content: dict | None) -> float | None:
    """기안 문서 내용에서 금액 성격의 필드 값을 자동 추출"""
    if not content or not isinstance(content, dict):
        return None
    for key in ('amount', 'estimated_amount', 'total_amount', 'price', 'cost', 'expense_amount', 'payment_amount'):
        val = content.get(key)
        if val is not None and val != '':
            try:
                clean_val = str(val).replace(',', '').replace(' ', '').replace('원', '')
                return float(clean_val)
            except (ValueError, TypeError):
                continue
    return None


def _get_department_manager(dept: Department, added_user_ids: set):
    """
    부서의 책임자를 다각도로 탐색:
    1. Department.manager 지정 직원
    2. 해당 부서의 직책(Duty) 보유 StaffAssignment (팀장, 본부장, 실장, 부서장 등)
    """
    # 1. Department.manager 명시된 경우
    if dept.manager and dept.manager.user and dept.manager.user.id not in added_user_ids:
        manager_staff = dept.manager
        # 해당 부서에서의 보직 또는 주보직에서 직책 추출
        dept_assignment = manager_staff.assignments.filter(department=dept).first()
        duty = dept_assignment.duty if dept_assignment and dept_assignment.duty else manager_staff.duty
        return manager_staff.user, duty

    # 2. StaffAssignment에서 해당 부서의 직책 보유자 탐색 (재직 직원 한정)
    dept_assignments = StaffAssignment.objects.filter(
        department=dept,
        duty__isnull=False,
        staff__status='1',
    ).select_related('staff__user', 'duty')

    for a in dept_assignments:
        if a.staff and a.staff.user and a.staff.user.id not in added_user_ids:
            return a.staff.user, a.duty

    return None, None


def _get_company_ceos(company, added_user_ids: set):
    """
    회사의 대표이사(CEO) 사용자 목록을 다각도로 조회:
    1. StaffAssignment (duty.code='CEO' 또는 duty.name에 '대표이사'/'대표' 포함)
    2. Executive (임원 등기 정보에서 represent_type이 sole, joint, each인 경우)
    3. Company.ceo 대표자명과 일치하는 재직 Staff
    """
    ceo_users = []
    seen_ids = set(added_user_ids)

    # 1. StaffAssignment 기준
    ceo_assignments = StaffAssignment.objects.filter(
        Q(duty__code__iexact='CEO') | Q(duty__name__icontains='대표이사') | Q(duty__name__icontains='대표'),
        company=company,
        staff__status='1',
    ).select_related('staff__user')

    for a in ceo_assignments:
        if a.staff and a.staff.user and a.staff.user.id not in seen_ids:
            ceo_users.append(a.staff.user)
            seen_ids.add(a.staff.user.id)

    # 2. Executive 등기 임원 기준
    executives = company.executives.filter(
        represent_type__in=['sole', 'joint', 'each'],
        staff__status='1',
    ).select_related('staff__user')

    for ex in executives:
        if ex.staff and ex.staff.user and ex.staff.user.id not in seen_ids:
            ceo_users.append(ex.staff.user)
            seen_ids.add(ex.staff.user.id)

    # 3. Company.ceo 이름 일치 기준 (fallback)
    if not ceo_users and company and company.ceo:
        matched_staffs = Staff.objects.filter(
            company=company,
            name=company.ceo.strip(),
            status='1',
        ).select_related('user')
        for s in matched_staffs:
            if s.user and s.user.id not in seen_ids:
                ceo_users.append(s.user)
                seen_ids.add(s.user.id)

    return ceo_users


def build_dynamic_approval_route(doc_type: DocumentType, drafter_user, drafter_assignment: StaffAssignment = None, content: dict = None):
    """
    기안자의 보직(소속 부서), 문서 유형의 전결 규정 및 금액별 조건부 정책(ApprovalPolicyRule)에 따라
    결재 단계 목록을 동적으로 생성합니다.
    대표이사가 특정 팀/부서의 장을 겸직하는 경우에도 중복 없이 1단계에 정상 할당됩니다.
    """
    # 1. 고정 템플릿 방식인 경우
    if doc_type.route_type == DocumentType.ROUTE_TEMPLATE:
        templates = doc_type.route_templates.order_by('step_order').prefetch_related('approvers')
        return [
            {
                'step_order': tmpl.step_order,
                'role_label': tmpl.role_label,
                'approvers': list(tmpl.approvers.all()),
                'approver_ids': list(tmpl.approvers.values_list('id', flat=True)),
                'condition': tmpl.condition,
            }
            for tmpl in templates
        ]

    # 2. 조직도 기반 자동 결재선 생성 방식
    # 기안 보직 확인
    assignment = drafter_assignment
    if not assignment and drafter_user:
        assignment = StaffAssignment.objects.filter(
            staff__user=drafter_user, is_primary=True
        ).select_related('company', 'department', 'staff__position', 'duty').first()

        if not assignment:
            assignment = StaffAssignment.objects.filter(
                staff__user=drafter_user
            ).select_related('company', 'department', 'staff__position', 'duty').first()

    steps = []
    step_order = 1
    reached_final = False
    added_user_ids = {drafter_user.id} if drafter_user else set()

    from company.models import Company
    company = assignment.company if assignment else Company.objects.filter(is_default=True).first()

    # 조건부 전결 정책(ApprovalPolicyRule) 적용 검사
    amount = extract_amount_from_content(content)
    effective_final_duty = doc_type.final_approval_duty
    effective_final_level = doc_type.final_dept_level

    policy_rules = doc_type.policy_rules.all()
    if policy_rules.exists() and amount is not None:
        for rule in policy_rules:
            if rule.is_matched(amount):
                if rule.final_approval_duty:
                    effective_final_duty = rule.final_approval_duty
                if rule.final_dept_level:
                    effective_final_level = rule.final_dept_level
                break

    # (1) 부서 트리 상향 순회 (직속 부서장 → 상위 부서장 → ...)
    if assignment and assignment.department:
        current_dept = assignment.department
        while current_dept:
            manager_user, manager_duty = _get_department_manager(current_dept, added_user_ids)

            # 부서 책임자가 존재하고 기안자 본인이 아닌 경우
            if manager_user and manager_user.id not in added_user_ids:
                added_user_ids.add(manager_user.id)

                duty_str = manager_duty.name if manager_duty else '책임자'
                role_label = f'{current_dept.name} {duty_str}'

                steps.append({
                    'step_order': step_order,
                    'role_label': role_label,
                    'approvers': [manager_user],
                    'approver_ids': [manager_user.id],
                    'condition': 'AND',
                })
                step_order += 1

                # 전결 규정 체크: 직책 전결 (예: 팀장 전결, 본부장 전결)
                if effective_final_duty and manager_duty and manager_duty.id == effective_final_duty.id:
                    reached_final = True
                    break

                # 전결 규정 체크: 부서 레벨 전결 (예: 1레벨(본부) 부서장까지만 승인)
                if effective_final_level and current_dept.level <= effective_final_level:
                    reached_final = True
                    break

            current_dept = current_dept.upper_depart

    # (2) 대표이사 최종 결재 단계 (전결 규정에 도달하지 않았거나 아직 대표이사가 결재선에 포함되지 않은 경우)
    if not reached_final and company:
        ceo_users = _get_company_ceos(company, added_user_ids)

        if ceo_users:
            # 공동대표 여부 검사
            is_joint = any(
                hasattr(u, 'staff') and hasattr(u.staff, 'executive') and
                u.staff.executive and u.staff.executive.represent_type == 'joint'
                for u in ceo_users
            )
            condition = 'AND' if (is_joint and len(ceo_users) > 1) else 'OR'
            label = '공동대표 최종 승인' if is_joint and len(ceo_users) > 1 else '대표이사 최종 승인'

            steps.append({
                'step_order': step_order,
                'role_label': label,
                'approvers': ceo_users,
                'approver_ids': [u.id for u in ceo_users],
                'condition': condition,
            })

    return steps
