from rest_framework import permissions

from apiV1.permissions._utils import (get_project_pk_from_request, resolve_issue_project,
                                      is_project_locked, is_project_closed)
from apiV1.permissions.work_perms import ProjectPermission


class HqFinancialOfficerPermission(permissions.BasePermission):
    """
    본사 자금 전용 권한 클래스.

    is_hq_financial_officer=True 인 직원과 슈퍼유저만
    모든 액션을 허용하며, 그 외에는 전면 차단합니다.

    사용 대상:
        LedgerCompanyBankAccountViewSet
        CompanyAccountViewSet
        AffiliateViewSet
        CompanyBankTransactionViewSet
        CompanyAccountingEntryViewSet
        CompanyCompositeTransactionViewSet
        CompanyLedgerCalculationViewSet
        CompanyLedgerLastDealDateViewSet

    ViewSet에 required_permission 선언 불필요.
    """

    @staticmethod
    def _is_hq_financial_officer(user) -> bool:
        """슈퍼유저 또는 Staff.is_hq_financial_officer 값을 안전하게 반환합니다."""
        if user.is_superuser:
            return True
        try:
            return bool(getattr(user.staff, 'is_hq_financial_officer', False))
        except AttributeError:
            return False

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return self._is_hq_financial_officer(request.user)

    def has_object_permission(self, request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return self._is_hq_financial_officer(request.user)


class HqProjectModulePermission(permissions.BasePermission):
    """
    본사 업무 프로젝트(IssueProject type='1') 전용 권한 클래스.

    자금/회계(ledger) 는 HqFinancialOfficerPermission이 담당하며, 이 클래스는
    본사 IssueProject에 연결된 문서(docs), 인사관리(hr_work) 등 일반 업무 권한을
    IssueProject.get_user_permissions() 메커니즘을 통해 검사합니다.

    IssueProject.type='1' 은 project.Project 레코드를 갖지 않으므로,
    IssueProject를 직접 조회하여 사용합니다.

    ViewSet 에서 아래와 같이 선언합니다:
        permission_classes = (IsAuthenticated, HqProjectPermission)

        @property
        def required_permission(self):
            return {
                'list': 'hr_work.read',
                'retrieve': 'hr_work.read',
                'create': 'hr_work.create',
                'update': 'hr_work.update',
                'partial_update': 'hr_work.update',
                'destroy': 'hr_work.delete',
            }.get(self.action, 'hr_work.read')

    사용 대상 (예시):
        DepartmentViewSet, JobGradeViewSet, PositionViewSet,
        DutyTitleViewSet, StaffViewSet  (company.py)
        본사 문서 관련 ViewSet (docs.py 중 type='1' 컨텍스트)
    """

    @classmethod
    def _get_all_hq_user_permissions(cls, user):
        """모든 type='1' 본사업무 프로젝트의 권한을 합집합으로 반환"""
        from work.models.project import IssueProject
        all_hq_ips = IssueProject.objects.filter(type='1')

        all_perms = set()
        for hq_ip in all_hq_ips:
            # 각 프로젝트의 권한을 수집
            all_perms.update(set(hq_ip.get_user_permissions(user)))
        return all_perms

    def has_permission(self, request, view) -> bool:
        # 1. 미인증 요청 차단
        if not request.user or not request.user.is_authenticated:
            return False

        issue_project = None
        project_pk = get_project_pk_from_request(request, view)
        if project_pk:
            issue_project = resolve_issue_project(project_pk, request)
            # 1-A. 잠금보관(9) 프로젝트는 슈퍼유저를 포함하여 비즈니스 데이터 접근 전면 차단
            if is_project_locked(issue_project):
                return False

        # 2. 슈퍼유저 전체 허용
        if request.user.is_superuser:
            return True

        # 3. work_manager 전체 허용
        if getattr(request.user, 'work_manager', False):
            return True

        required_perm = getattr(view, 'required_permission', None)

        # 4. required_permission 미선언 ViewSet은 인증만 확인
        if not required_perm:
            return True

        # 5. 본사 IssueProject가 없으면 차단
        if not issue_project:
            return False

        # 6. 닫힘(2) 프로젝트 — 읽기만 허용
        if is_project_closed(issue_project) and request.method not in permissions.SAFE_METHODS:
            return False

        # 7. list/SAFE 메서드 — project 미지정 시 Row-Level Security 에서 필터링
        user_perms = self._get_all_hq_user_permissions(request.user)
        return required_perm in user_perms

    def has_object_permission(self, request, view, obj) -> bool:
        # 1. 미인증 요청 차단
        if not request.user or not request.user.is_authenticated:
            return False

        project_pk = get_project_pk_from_request(request, view)
        issue_project = resolve_issue_project(project_pk, request) if project_pk else None

        # 1-A. 잠금보관(9) 프로젝트는 슈퍼유저를 포함하여 비즈니스 데이터 접근 전면 차단
        if is_project_locked(issue_project):
            return False

        # 3. 슈퍼유저 전체 허용
        if request.user.is_superuser:
            return True

        # 4. work_manager 전체 허용
        if getattr(request.user, 'work_manager', False):
            return True

        # 5. 본사 IssueProject가 없으면 차단
        if not issue_project:
            return False

        # 6. 닫힘(2) — 읽기 전용
        if is_project_closed(issue_project) and request.method not in permissions.SAFE_METHODS:
            return False

        required_perm = getattr(view, 'required_permission', None)
        if not required_perm:
            return request.method in permissions.SAFE_METHODS

        user_perms = self._get_all_hq_user_permissions(request.user)
        return required_perm in user_perms


class IbsModulePermission(ProjectPermission):
    """
    IBS 비즈니스 도메인 Project 모델 (contract/payment/notice/ledger/site/hr_work 등) ViewSet용 권한 클래스.

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

    ※ 본사 자금(ledger) 관련 ViewSet은 HqFinancialOfficerPermission 을 사용합니다.
    * 기타 본사 모듈 관련 ViewSet 은 HqProjectModulePermission 을 사용합니다.
    """

    @staticmethod
    def _resolve_project_issue_project(project_pk, request=None):
        """
        project.Project PK → work.IssueProject 인스턴스를 반환합니다.
        (Project 전용 역추적 로직)
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
        except (Project.DoesNotExist, Project.issue_project.RelatedObjectDoesNotExist, AttributeError):
            issue_project = None

        if request is not None:
            setattr(request, cache_key, issue_project)
        return issue_project
    def has_permission(self, request, view):
        # 1. 미인증 요청 차단
        if not request.user or not request.user.is_authenticated:
            return False

        project_pk = get_project_pk_from_request(request, view)
        issue_project = self._resolve_project_issue_project(project_pk, request) if project_pk else None

        # 1-A. 잠금보관(9) 프로젝트는 슈퍼유저를 포함하여 비즈니스 데이터 접근 전면 차단
        if is_project_locked(issue_project):
            return False

        # 2. 슈퍼유저 전체 허용
        if request.user.is_superuser:
            return True

        # 3. work_manager 허용
        if getattr(request.user, 'work_manager', False):
            return True

        required_perm = getattr(view, 'required_permission', None)

        # 4. required_permission 미선언 ViewSet은 기존 동작(인증만 확인) 유지
        if not required_perm:
            return True

        # 5. list 또는 안전 메서드 + project 미지정 → Row-Level Security 에서 필터링
        action = getattr(view, 'action', None)
        if not project_pk:
            if action == 'list' or request.method in permissions.SAFE_METHODS:
                return True
            return False

        # 6. IssueProject 역추적 (앞에서 이미 resolve 했다면 캐시됨)
        if not issue_project:
            return False

        # 7. 닫힘(2) 프로젝트 — 읽기만 허용
        if is_project_closed(issue_project) and request.method not in permissions.SAFE_METHODS:
            return False

        # 8. 권한 코드 검사
        user_perms = set(issue_project.get_user_permissions(request.user))
        return required_perm in user_perms

    def has_object_permission(self, request, view, obj):
        # obj 에서 project.Project PK를 추출합니다.
        project_pk = getattr(obj, 'project_id', None)
        if project_pk is None:
            project_rel = getattr(obj, 'project', None)
            if project_rel is not None:
                project_pk = getattr(project_rel, 'pk', None)

        if project_pk is not None:
            project_pk = int(project_pk) if not isinstance(project_pk, int) else project_pk

        issue_project = self._resolve_project_issue_project(project_pk, request)

        # 1-A. 잠금보관(9) 프로젝트는 슈퍼유저를 포함하여 비즈니스 데이터 접근 전면 차단
        if is_project_locked(issue_project):
            return False

        # 2. 슈퍼유저 전체 허용
        if request.user.is_superuser:
            return True

        # 3. work_manager 허용
        if getattr(request.user, 'work_manager', False):
            return True

        required_perm = getattr(view, 'required_permission', None)

        if not issue_project:
            return False

        # 잠금보관 → 전면 차단
        # 닫힘 → 읽기 전용
        if is_project_closed(issue_project) and request.method not in permissions.SAFE_METHODS:
            return False

        user_perms = set(issue_project.get_user_permissions(request.user))

        if not required_perm:
            return request.method in permissions.SAFE_METHODS

        return required_perm in user_perms
