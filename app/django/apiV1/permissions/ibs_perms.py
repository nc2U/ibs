from rest_framework import permissions

from apiV1.permissions.work_perms import ProjectPermission


class IbsModulePermission(ProjectPermission):
    """
    IBS 비즈니스 도메인(contract/payment/notice/ledger/site/hr_work 등) ViewSet용 권한 클래스.

    기존 work 시스템의 ProjectPermission과 달리, IBS 도메인 ViewSet은
    IssueProject slug가 아닌 project.Project PK(정수)로 프로젝트를 식별합니다.
    project.Project → work.IssueProject (OneToOneField) 역추적을 통해
    동일한 IssueProject.get_user_permissions() 메커니즘을 재사용합니다.

    ViewSet에서 아래 두 가지를 선언하면 동작합니다:
        permission_classes = (IsAuthenticated, IbsModulePermission)

        @property
        def required_permission(self):
            return {
                'list': 'contract.read',
                'retrieve': 'contract.read',
                'create': 'contract.create',
                ...
            }.get(self.action, 'contract.read')
    """

    @staticmethod
    def _get_project_pk(request, view):
        """
        요청에서 project.Project PK를 추출합니다.
        우선순위: URL kwargs → request.data → query_params
        """
        pk = (
            view.kwargs.get('project')
            or request.data.get('project')
            or request.query_params.get('project')
        )
        if pk is None:
            return None
        try:
            return int(pk)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _resolve_issue_project(project_pk, request=None):
        """
        project.Project PK → work.IssueProject 인스턴스를 반환합니다.
        결과를 request에 캐싱하여 동일 요청 내 중복 쿼리를 방지합니다.
        """
        if project_pk is None:
            return None

        # 요청 캐시 확인
        cache_key = f'_ibs_issue_project_{project_pk}'
        if request and hasattr(request, cache_key):
            return getattr(request, cache_key)

        from project.models import Project
        try:
            issue_project = (
                Project.objects
                .select_related('issue_project')
                .get(pk=project_pk)
                .issue_project
            )
        except (Project.DoesNotExist, Project.issue_project.RelatedObjectDoesNotExist,
                AttributeError):
            issue_project = None

        if request is not None:
            setattr(request, cache_key, issue_project)
        return issue_project

    def has_permission(self, request, view):
        # 1. 미인증 요청 차단
        if not request.user or not request.user.is_authenticated:
            return False

        project_pk = self._get_project_pk(request, view)
        if project_pk:
            issue_project = self._resolve_issue_project(project_pk, request)
            # 1-A. 잠금보관(9) 프로젝트는 슈퍼유저를 포함하여 비즈니스 데이터 접근 전면 차단
            if issue_project and issue_project.status == '9':
                return False

        # 2. 슈퍼유저 전체 허용
        if request.user.is_superuser:
            return True

        required_perm = getattr(view, 'required_permission', None)

        # 3. required_permission 미선언 ViewSet은 기존 동작(인증만 확인) 유지
        if not required_perm:
            return True

        # 4. list 또는 안전 메서드 + project 미지정 → Row-Level Security에서 필터링
        action = getattr(view, 'action', None)
        if not project_pk:
            if action == 'list' or request.method in permissions.SAFE_METHODS:
                return True
            return False

        # 5. IssueProject 역추적 (앞에서 이미 resolve 했다면 캐시됨)
        issue_project = self._resolve_issue_project(project_pk, request)
        if not issue_project:
            return False

        # 6. 본사 프로젝트(type='1')의 자금(ledger) 관련 요청 검증 (은밀한 플래그 체크)
        if issue_project.type == '1' and 'ledger' in required_perm:
            try:
                if not getattr(request.user.staff, 'is_hq_financial_officer', False):
                    return False
            except AttributeError:
                return False
        # 본사 자금이 아닌 일반 요청인 경우 work_manager 허용
        elif getattr(request.user, 'work_manager', False):
            return True

        # 7. 닫힘(2) 프로젝트 — 읽기만 허용
        if issue_project.status == '2' and request.method not in permissions.SAFE_METHODS:
            return False

        # 8. 권한 코드 검사
        user_perms = set(issue_project.get_user_permissions(request.user))
        return required_perm in user_perms


    def has_object_permission(self, request, view, obj):
        # obj에서 project.Project PK를 추출합니다.
        project_pk = getattr(obj, 'project_id', None) or getattr(obj, 'project', None)
        if project_pk is not None:
            project_pk_int = int(project_pk) if not isinstance(project_pk, int) else project_pk
            issue_project = self._resolve_issue_project(project_pk_int, request)
            # 1-A. 잠금보관(9) 프로젝트는 슈퍼유저를 포함하여 비즈니스 데이터 접근 전면 차단
            if issue_project and issue_project.status == '9':
                return False

        # 2. 슈퍼유저 전체 허용
        if request.user.is_superuser:
            return True

        required_perm = getattr(view, 'required_permission', None)

        if project_pk is None:
            return False

        issue_project = self._resolve_issue_project(
            int(project_pk) if not isinstance(project_pk, int) else project_pk,
            request
        )
        if not issue_project:
            return False

        # 본사 프로젝트(type='1')의 자금(ledger) 관련 요청 검증 (은밀한 플래그 체크)
        if required_perm and issue_project.type == '1' and 'ledger' in required_perm:
            try:
                if not getattr(request.user.staff, 'is_hq_financial_officer', False):
                    return False
            except AttributeError:
                return False
        # 본사 자금이 아닌 일반 요청인 경우 work_manager 허용
        elif getattr(request.user, 'work_manager', False):
            return True

        # 잠금보관 → 전면 차단
        if issue_project.status == '9':
            return False

        # 닫힘 → 읽기 전용
        if issue_project.status == '2' and request.method not in permissions.SAFE_METHODS:
            return False

        user_perms = set(issue_project.get_user_permissions(request.user))

        if not required_perm:
            return request.method in permissions.SAFE_METHODS

        return required_perm in user_perms
