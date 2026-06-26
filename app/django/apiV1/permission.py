from rest_framework import permissions

from accounts.models import StaffAuth


class IsSuperUserOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsStaffOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        else:
            try:
                return request.user.staffauth.is_staff
            except StaffAuth.DoesNotExist:
                return False


class IsOwnerOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_superuser


class IsSuperUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return request.user.is_superuser


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            if request.user.is_superuser:
                return True
            else:
                try:
                    return request.user.staffauth.is_staff
                except StaffAuth.DoesNotExist:
                    return False


class IsProjectStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            if request.user.is_superuser:
                return True
            else:
                try:
                    return request.user.staffauth.is_staff or request.user.staffauth.is_project_staff
                except StaffAuth.DoesNotExist:
                    return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return obj.user == request.user or request.user.is_superuser


class IsOwnSelfOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return obj == request.user or request.user.is_superuser


class ProjectPermission(permissions.BasePermission):
    """
    프로젝트 slug를 기반으로 사용자의 권한을 체크하는 클래스
    """
    def has_permission(self, request, view):
        # 인증 여부 우선 체크
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 슈퍼유저/관리자 예외 처리
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return True
            
        # create 액션의 경우, 전역 권한 체크 단계에서 선제 검증 필요
        if getattr(view, 'action', None) == 'create':
            # URL kwarg (예: /projects/<project_slug>/issues/) 또는 payload에서 project 추출
            project_slug = view.kwargs.get('project_slug') or request.data.get('project')
            if not project_slug:
                return False  # 프로젝트 정보가 없으면 거부
            
            from work.models.project import IssueProject
            try:
                # Slug 또는 PK로 프로젝트 조회
                if isinstance(project_slug, int) or (isinstance(project_slug, str) and project_slug.isdigit()):
                    project = IssueProject.objects.get(pk=int(project_slug))
                else:
                    project = IssueProject.objects.get(slug=project_slug)
            except IssueProject.DoesNotExist:
                return False

            # 해당 프로젝트에서 이 사용자의 권한 계산
            user_perms = project.get_user_permissions(request.user)
            required_perm = getattr(view, 'required_permission', None)
            return required_perm in user_perms

        # 객체 단위 체크가 아닌 경우(예: list)에는 True를 반환하여 
        # get_queryset 등에서 필터링되도록 처리합니다.
        return True

    def has_object_permission(self, request, view, obj):
        from work.models.project import IssueProject
        # 슈퍼유저/관리자 예외 처리
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return True
            
        # obj가 프로젝트 모델인지 확인 (혹은 프로젝트를 참조하는 모델인지)
        project = obj if isinstance(obj, IssueProject) else getattr(obj, 'project', None)
        
        if not project:
            return False

        # 모델의 권한 계산 로직 사용
        user_perms = project.get_user_permissions(request.user)
        
        # View에서 정의한 '필요한 권한 코드'와 비교
        required_perm = getattr(view, 'required_permission', None)
        
        if not required_perm:
            # 설정되지 않았을 경우, 기본적으로 읽기 권한(read)만 허용하거나 접근 막기
            return request.method in permissions.SAFE_METHODS

        return required_perm in user_perms
