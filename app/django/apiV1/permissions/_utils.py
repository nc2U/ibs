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
