from work.models.project import IssueProject


def get_project_pk_from_request(request, view):
    """요청으로부터 프로젝트 PK(정수)를 안전하게 추출합니다."""
    data = getattr(request, 'data', {}) if hasattr(request, 'data') else {}
    query_params = getattr(request, 'query_params', {}) if hasattr(request, 'query_params') else {}

    pk = (
            view.kwargs.get('project')
            or (data.get('project') if isinstance(data, dict) else None)
            or query_params.get('project')
    )
    if pk is None and (getattr(view, 'basename', None) == 'project' or view.__class__.__name__ == 'ProjectViewSet'):
        pk = getattr(view, 'kwargs', {}).get('pk')

    if pk is not None:
        try:
            return int(pk)
        except (TypeError, ValueError):
            pass

    # building_unit 기반 프로젝트 ID 역추적 (items.HouseUnit 등)
    bldg_pk = (
        (data.get('building_unit') if isinstance(data, dict) else None)
        or query_params.get('building_unit')
    )
    if bldg_pk is not None:
        try:
            from items.models import BuildingUnit
            return BuildingUnit.objects.filter(pk=int(bldg_pk)).values_list('project_id', flat=True).first()
        except Exception:
            pass

    # unit_type 기반 프로젝트 ID 역추적
    ut_pk = (
        (data.get('unit_type') if isinstance(data, dict) else None)
        or query_params.get('unit_type')
    )
    if ut_pk is not None:
        try:
            from items.models import UnitType
            return UnitType.objects.filter(pk=int(ut_pk)).values_list('project_id', flat=True).first()
        except Exception:
            pass

    # contract 기반 프로젝트 ID 역추적
    contract_pk = (
        (data.get('contract') if isinstance(data, dict) else None)
        or query_params.get('contract')
    )
    if contract_pk is not None:
        try:
            from contract.models import Contract
            return Contract.objects.filter(pk=int(contract_pk)).values_list('project_id', flat=True).first()
        except Exception:
            pass

    # house_unit 기반 프로젝트 ID 역추적 (미계약 ContractPrice 등)
    hu_pk = (
        (data.get('house_unit') if isinstance(data, dict) else None)
        or query_params.get('house_unit')
    )
    if hu_pk is not None:
        try:
            from items.models import HouseUnit
            return HouseUnit.objects.filter(pk=int(hu_pk)).values_list('unit_type__project_id', flat=True).first()
        except Exception:
            pass

    # contractor 기반 프로젝트 ID 역추적 (ContractFile, ContractDocument, Address, Contact, ConsultationLogs 등)
    contractor_pk = (
        view.kwargs.get('contractor_id')
        or (data.get('contractor') if isinstance(data, dict) else None)
        or query_params.get('contractor')
    )
    if contractor_pk is not None:
        try:
            from contract.models import Contractor
            c_obj = Contractor.objects.select_related('contract', 'prev_contract').filter(pk=int(contractor_pk)).first()
            if c_obj:
                if c_obj.contract_id and c_obj.contract:
                    return c_obj.contract.project_id
                if c_obj.prev_contract_id and c_obj.prev_contract:
                    return c_obj.prev_contract.project_id
        except Exception:
            pass

    # contract_document 기반 프로젝트 ID 역추적 (ContractDocumentFile 등)
    cd_pk = (
        view.kwargs.get('contract_document_id')
        or (data.get('contract_document') if isinstance(data, dict) else None)
        or query_params.get('contract_document')
    )
    if cd_pk is not None:
        try:
            from contract.models import ContractDocument
            cd_obj = ContractDocument.objects.select_related(
                'contractor__contract', 'contractor__prev_contract'
            ).filter(pk=int(cd_pk)).first()
            if cd_obj and cd_obj.contractor:
                if cd_obj.contractor.contract_id and cd_obj.contractor.contract:
                    return cd_obj.contractor.contract.project_id
                if cd_obj.contractor.prev_contract_id and cd_obj.contractor.prev_contract:
                    return cd_obj.contractor.prev_contract.project_id
        except Exception:
            pass

    # sales.SalesAgency 기반 프로젝트 ID 역추적
    agency_pk = (
        (data.get('agency') if isinstance(data, dict) else None)
        or query_params.get('agency')
    )
    if agency_pk is not None:
        try:
            from sales.models import SalesAgency
            return SalesAgency.objects.filter(pk=int(agency_pk)).values_list('project_id', flat=True).first()
        except Exception:
            pass

    # sales.SalesTeam 기반 프로젝트 ID 역추적
    team_pk = (
        (data.get('team') if isinstance(data, dict) else None)
        or query_params.get('team')
    )
    if team_pk is not None:
        try:
            from sales.models import SalesTeam
            return SalesTeam.objects.filter(pk=int(team_pk)).values_list('agency__project_id', flat=True).first()
        except Exception:
            pass

    # sales.SalesPerson 기반 프로젝트 ID 역추적
    sp_pk = (
        (data.get('sales_person') if isinstance(data, dict) else None)
        or query_params.get('sales_person')
    )
    if sp_pk is not None:
        try:
            from sales.models import SalesPerson
            return SalesPerson.objects.filter(pk=int(sp_pk)).values_list('team__agency__project_id', flat=True).first()
        except Exception:
            pass

    # sales.SettlementPeriod 기반 프로젝트 ID 역추적
    period_pk = (
        (data.get('period') if isinstance(data, dict) else None)
        or query_params.get('period')
    )
    if period_pk is not None:
        try:
            from sales.models import SettlementPeriod
            return SettlementPeriod.objects.filter(pk=int(period_pk)).values_list('project_id', flat=True).first()
        except Exception:
            pass

    return None


def resolve_issue_project(project_pk, request=None):
    """
    project_pk를 받아 IssueProject를 조회합니다.
    """
    if project_pk is None:
        return None

    # 요청 캐시 확인
    cache_key = f'_resolved_issue_project_{project_pk}'
    if request and hasattr(request, cache_key):
        return getattr(request, cache_key)

    try:
        issue_project = IssueProject.objects.get(pk=project_pk)
    except IssueProject.DoesNotExist:
        issue_project = None

    if request is not None:
        setattr(request, cache_key, issue_project)
    return issue_project


def is_project_locked(issue_project):
    """워크스페이스가 잠금보관(status='9') 상태인지 확인합니다."""
    return issue_project and issue_project.status == '9'


def is_project_closed(issue_project):
    """워크스페이스가 닫힘(status='2') 상태인지 확인합니다."""
    return issue_project and issue_project.status == '2'


def get_project_ids_with_permission(user, required_perm: str):
    """
    [H-7] 사용자가 특정 required_perm을 실제로 보유한 IBS 프로젝트 ID 목록을 반환합니다.

    단순 소속(member) 여부가 아닌 IssueProject.get_user_permissions()를 통해
    required_perm 보유 여부를 검증합니다.

    Args:
        user: request.user
        required_perm: 'sales.read', 'sales.policy', 'contract.read' 등

    Returns:
        list[int]: 해당 권한을 보유한 project.Project PK 목록
    """
    if not user or not user.is_authenticated:
        return []

    from work.models.project import IssueProject as _IssueProject
    # 소속 IssueProject 중 IBS project가 연결된 것만 조회
    candidate_ips = _IssueProject.objects.filter(
        members__user=user,
        project__isnull=False,
    ).select_related('project')

    allowed_ids = []
    for ip in candidate_ips:
        perms = set(ip.get_user_permissions(user))
        if required_perm in perms:
            allowed_ids.append(ip.project.id)
    return allowed_ids


def get_company_ids_with_permission(user, required_perm: str = None):
    """
    사용자가 접근 권한을 보유한 회사(Company) PK 목록을 반환합니다.
    1. 슈퍼유저 / work_manager: 전체 회사 ID 반환
    2. 소속 Staff (직접 연결 또는 이메일 매칭): 해당 회사 ID
    3. 본사 워크스페이스(IssueProject type='1') 멤버십 및 required_perm 보유 회사 ID
    """
    if not user or not user.is_authenticated:
        return []

    from company.models import Company, Staff
    if user.is_superuser or getattr(user, 'work_manager', False):
        return list(Company.objects.values_list('id', flat=True))

    from django.db.models import Q
    from work.models.project import IssueProject

    allowed_company_ids = set()

    # 1. Staff 소속 (직접 외래키 또는 이메일 일치)
    if hasattr(user, 'staff') and user.staff and user.staff.company_id:
        allowed_company_ids.add(user.staff.company_id)
    for cid in Staff.objects.filter(
        Q(user=user) | Q(email=user.email),
        company__isnull=False
    ).values_list('company_id', flat=True):
        allowed_company_ids.add(cid)

    # 2. 본사 워크스페이스(type='1') 멤버십 및 권한 검증
    hq_ips = IssueProject.objects.filter(
        type='1',
        members__user=user,
        company__isnull=False
    ).select_related('company')

    for ip in hq_ips:
        if required_perm:
            perms = set(ip.get_user_permissions(user))
            if required_perm in perms:
                allowed_company_ids.add(ip.company_id)
        else:
            allowed_company_ids.add(ip.company_id)

    return list(allowed_company_ids)


