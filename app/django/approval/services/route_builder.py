from company.models import StaffAssignment, Staff, Department
from ..models import DocumentType


def build_dynamic_approval_route(doc_type: DocumentType, drafter_user, drafter_assignment: StaffAssignment = None):
    """
    기안자의 보직(소속 부서)과 문서 유형의 전결 규정에 따라 결재 단계 목록을 동적으로 생성합니다.

    반환 형식:
    [
        {
            'step_order': 1,
            'role_label': '경영지원팀 팀장',
            'approver_ids': [user_id, ...],
            'approvers': [User, ...],
            'condition': 'AND' | 'OR',
        },
        ...
    ]
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
        ).select_related('company', 'department', 'position', 'duty').first()

        if not assignment:
            # 주보직이 없는 경우 아무 보직이나 1개 조회
            assignment = StaffAssignment.objects.filter(
                staff__user=drafter_user
            ).select_related('company', 'department', 'position', 'duty').first()

    steps = []
    step_order = 1
    reached_final = False
    added_user_ids = {drafter_user.id} if drafter_user else set()

    company = assignment.company if assignment else None

    # (1) 부서 트리 상향 순회 (직속 부서장 → 상위 부서장 → ...)
    if assignment and assignment.department:
        current_dept = assignment.department
        while current_dept:
            manager_staff = current_dept.manager

            # 부서 책임자가 존재하고, 기안자 본인이 아니며, 아직 결재선에 추가되지 않은 경우
            if manager_staff and manager_staff.user and manager_staff.user.id not in added_user_ids:
                manager_user = manager_staff.user
                added_user_ids.add(manager_user.id)

                duty_str = manager_staff.duty.name if manager_staff.duty else '책임자'
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
                if doc_type.final_approval_duty and manager_staff.duty_id == doc_type.final_approval_duty_id:
                    reached_final = True
                    break

                # 전결 규정 체크: 부서 레벨 전결 (예: 1레벨(본부) 부서장까지만 승인)
                if doc_type.final_dept_level and current_dept.level <= doc_type.final_dept_level:
                    reached_final = True
                    break

            current_dept = current_dept.upper_depart

    # (2) 대표이사 최종 결재 단계 (전결 규정에 도달하지 않은 경우)
    if not reached_final and company:
        # 대표이사 보직을 가진 재직 직원 조회
        ceo_assignments = StaffAssignment.objects.filter(
            company=company,
            duty__name='대표이사',
            staff__status='1',
        ).select_related('staff__user')

        ceo_users = [
            a.staff.user for a in ceo_assignments
            if a.staff.user and a.staff.user.id not in added_user_ids
        ]

        # fallback: Staff 모델에서 직접 duty__name='대표이사' 조회
        if not ceo_users:
            ceo_staffs = Staff.objects.filter(
                company=company,
                duty__name='대표이사',
                status='1',
            ).select_related('user')
            ceo_users = [
                s.user for s in ceo_staffs
                if s.user and s.user.id not in added_user_ids
            ]

        if ceo_users:
            is_joint = any(a.represent_type == 'joint' for a in ceo_assignments)
            # 공동대표인 경우 AND(전원 승인), 단독/각자대표인 경우 OR(1인 승인)
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
