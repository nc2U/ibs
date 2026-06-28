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
            
        # create 액션의 경우, 선제 검증 필요
        if getattr(view, 'action', None) == 'create':
            required_perm = getattr(view, 'required_permission', None)
            
            # 1. 최상위 프로젝트 생성인 경우 ('project.create')
            if required_perm == 'project.create':
                # 최상위 프로젝트 생성은 프로젝트 컨텍스트 없이 허용
                # (실제 권한 체크는 사용자 기반의 전역 권한 체크가 필요하다면 여기에 추가)
                return True
                
            # 2. 리소스 생성 시 프로젝트 식별자 추출 (하위 프로젝트, 회의록, 업무 등)
            project_slug = (
                view.kwargs.get('project_slug') or 
                request.data.get('project') or 
                request.data.get('parent_slug')
            )
            if not project_slug:
                return False 
            
            from work.models.project import IssueProject
            try:
                if isinstance(project_slug, int) or (isinstance(project_slug, str) and project_slug.isdigit()):
                    project = IssueProject.objects.get(pk=int(project_slug))
                else:
                    project = IssueProject.objects.get(slug=project_slug)
            except IssueProject.DoesNotExist:
                return False

            user_perms = project.get_user_permissions(request.user)
            return required_perm in user_perms

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

        # 공개 프로젝트이고 단순 조회(SAFE_METHODS) 요청인 경우 즉시 허용 (목록/상세 조회 정합성 유지)
        if project.is_public and request.method in permissions.SAFE_METHODS:
            return True

        # 모델의 권한 계산 로직 사용
        user_perms = project.get_user_permissions(request.user)
        
        # View에서 정의한 '필요한 권한 코드'와 비교
        required_perm = getattr(view, 'required_permission', None)
        
        if not required_perm:
            # 설정되지 않았을 경우, 기본적으로 읽기 권한(read)만 허용하거나 접근 막기
            return request.method in permissions.SAFE_METHODS

        return required_perm in user_perms

class MeetingPermission(ProjectPermission):
    def has_object_permission(self, request, view, obj):
        # 1. 기존 프로젝트 접근 권한 체크
        if not super().has_object_permission(request, view, obj):
            return False
            
        # 2. 안전한 메서드(GET, HEAD, OPTIONS)는 통과
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # 3. 수정 및 삭제 관련 로직
        if view.action in ['update', 'partial_update', 'destroy']:
            user = request.user
            project = getattr(obj, 'project', None)
            if not project:
                return False
            
            user_perms = project.get_user_permissions(user)

            # (A) 회의록이 확정(is_confirmed)된 상태인 경우 수정/삭제 제한
            if obj.is_confirmed:
                if user.is_superuser or getattr(user, 'work_manager', False) or 'meeting.edit_confirmed' in user_perms:
                    return True
                return False

            # (B) 일반 상태일 때의 권한 로직
            # 수정 권한 처리
            if view.action in ['update', 'partial_update']:
                if 'meeting.update' in user_perms:
                    return True
                if 'meeting.own_update' in user_perms:
                    if (user == obj.creator) or (user in obj.attendees.all()):
                        return True
                return False

            # 삭제 권한 처리 (일반 상태일 때)
            if view.action == 'destroy':
                return 'meeting.delete' in user_perms
            
        return True
