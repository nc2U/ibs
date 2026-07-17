from rest_framework import permissions


class ProjectPermission(permissions.BasePermission):
    """
    프로젝트 slug를 기반으로 사용자의 권한을 체크하는 클래스
    """

    @staticmethod
    def get_project_slug(view, *sources):
        slug = view.kwargs.get('slug')
        if slug:
            return slug

        for source in sources:
            if isinstance(source, dict):
                slug = (source.get('project')
                        or source.get('issue_project')
                        or source.get('parent_slug'))
                if slug:
                    return slug

                # 이슈 ID를 기반으로 프로젝트 역추적
                issue_id = source.get('issue') or source.get('source') or source.get('parent')
                if issue_id:
                    from work.models.issue import Issue
                    try:
                        issue = Issue.objects.select_related('project').get(pk=issue_id)
                        return issue.project.pk
                    except (Issue.DoesNotExist, ValueError, TypeError):
                        pass
        return None

    def find_project(self, project_slug):
        from work.models.project import IssueProject

        if isinstance(project_slug, int):
            return IssueProject.objects.filter(pk=project_slug).first()

        if isinstance(project_slug, str) and project_slug.isdigit():
            return IssueProject.objects.filter(pk=int(project_slug)).first()

        return IssueProject.objects.filter(slug=project_slug).first()

    def extract_project(self, obj):
        from work.models.project import IssueProject

        if isinstance(obj, IssueProject):
            return obj
        if hasattr(obj, 'project'):
            return obj.project
        if hasattr(obj, 'issue_project'):
            return obj.issue_project
        if hasattr(obj, 'source') and hasattr(obj.source, 'project'):
            return obj.source.project
        if hasattr(obj, 'issue') and hasattr(obj.issue, 'project'):
            return obj.issue.project
        if hasattr(obj, 'meeting') and hasattr(obj.meeting, 'project'):
            return obj.meeting.project
        if hasattr(obj, 'news') and hasattr(obj.news, 'project'):
            return obj.news.project
        # 게시판(Forum) 및 게시물 관련 프로젝트 매핑
        if hasattr(obj, 'forum') and hasattr(obj.forum, 'project'):
            return obj.forum.project
        if hasattr(obj, 'post') and hasattr(obj.post, 'forum') and hasattr(obj.post.forum, 'project'):
            return obj.post.forum.project
        return None

    def has_permission(self, request, view):
        # 인증 여부 우선 체크
        if not request.user or not request.user.is_authenticated:
            return False

        # 슈퍼유저/관리자 예외 처리
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return True

        action = getattr(view, 'action', None)
        # create 액션의 경우, 선제 검증 필요
        if action == 'create':
            required_perm = getattr(view, 'required_permission', None)

            # 1. 최상위 프로젝트 생성인 경우 ('project.create')
            if required_perm == 'project.create':
                from work.models.project import Member
                return Member.objects.filter(
                    user=request.user,
                    roles__permissions__code='project.create'
                ).exists()

            # 검색양식 저장의 경우 익명(pk=1) 및 일반사용자 권한(pk=2 등)을 기본 허용하므로 프로젝트 검사 전 우선 판별
            if required_perm == 'project.save_query':
                from work.models.project import Role
                user_perms = set(
                    Role.objects.filter(
                        projects__members__user=request.user
                    ).filter(
                        permissions__code__in=['project.save_query', 'project.pub_query']
                    ).values_list('permissions__code', flat=True)
                )
                try:
                    # pk=1 (익명) 및 pk=2 (일반사용자) 기본 권한 합산
                    default_roles = Role.objects.prefetch_related('permissions').filter(pk__in=[1, 2])
                    for role in default_roles:
                        user_perms.update(role.permissions.values_list('code', flat=True))
                except Exception:
                    pass
                if 'project.save_query' in user_perms:
                    return True

            # 2. 리소스 생성 시 프로젝트 식별자 추출 (하위 프로젝트, 회의록, 업무 등)
            project_slug = self.get_project_slug(view, request.data, request.query_params)

            if not project_slug:
                return False

            project = self.find_project(project_slug)

            if not project:
                return False

            user_perms = project.get_user_permissions(request.user)

            if not required_perm:
                return False
            return required_perm in user_perms

        # list 액션에 대한 선제 검증
        if action == 'list':
            project_slug = self.get_project_slug(view, request.query_params)

            if project_slug:
                project = self.find_project(project_slug)

                if not project:
                    return False

                if project.is_public:
                    return True

                user_perms = project.get_user_permissions(request.user)
                required_perm = getattr(view, 'required_permission', 'issue.read')
                if not required_perm:
                    return False
                return required_perm in user_perms

        return True

    def has_object_permission(self, request, view, obj):
        # 슈퍼유저/관리자 예외 처리
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return True

        # obj가 프로젝트 모델인지 확인 (혹은 프로젝트를 참조하는 모델인지 지능형 추적)
        project = self.extract_project(obj)

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

        if required_perm in user_perms:
            return True

        # own_ 권한 확인 (작성자 본인 검증 등 세부 로직은 하위 Permission 클래스에서 처리)
        parts = required_perm.split('.')
        if len(parts) == 2:
            domain, action = parts
            if action in ['update', 'delete', 'private']:
                if f"{domain}.own_{action}" in user_perms:
                    return True

            # comment_update -> comment_own_update 등 복합 액션 처리
            if '_' in action:
                prefix, suffix = action.rsplit('_', 1)
                if suffix in ['update', 'delete']:
                    if f"{domain}.{prefix}_own_{suffix}" in user_perms:
                        return True

        return False


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
                    # 개선: filter().exists()를 사용해 M2M 전체 인메모리 로드 방지
                    if (user == obj.creator) or obj.attendees.filter(pk=user.pk).exists():
                        return True
                return False

            # 삭제 권한 처리 (일반 상태일 때)
            if view.action == 'destroy':
                return 'meeting.delete' in user_perms

        return True


class IssuePermission(ProjectPermission):
    def has_permission(self, request, view):
        # 1. 부모 클래스(ProjectPermission)의 기본 생성 검사 수행
        if not super().has_permission(request, view):
            return False

        # 2. 신규 생성 시의 업무 도메인 특화 검사
        if view.action == 'create':
            project_slug = self.get_project_slug(view, request.data)
            project = None

            # 부모(parent)가 있다면 역추적하여 프로젝트 가져오기 우선 시도
            parent_id = request.data.get('parent')
            if parent_id and not project_slug:
                from work.models.issue import Issue
                try:
                    parent_issue = Issue.objects.select_related('project').get(pk=parent_id)
                    project = parent_issue.project
                except Issue.DoesNotExist:
                    return False
            elif project_slug:
                project = self.find_project(project_slug)

            if not project:
                return False

            # [잠금보관 프로젝트 제한] 아카이브 - 관리자 포함 모든 사용자 제한
            if project.status == '9':
                return False

            # [닫힘 프로젝트 제한] 읽기 전용 - 관리자 포함 모든 사용자 제한
            if project.status == '2':
                return False

            # 슈퍼유저/관리자 예외 처리 (생성 시)
            if request.user.is_superuser or getattr(request.user, 'work_manager', False):
                return True

            user_perms = project.get_user_permissions(request.user)

            # (A) issue.create 혹은 issue.copy 권한 보유 여부 확인 (이전 캡슐화 완료)
            if 'issue.create' not in user_perms and 'issue.copy' not in user_perms:
                return False

            # (B) 비공개 업무 생성 권한 체크 (Method D)
            # issue_visible='ALL' OR issue.private OR (issue.own_private AND is_own) OR is_own(creator/assignee)
            is_private_req = request.data.get('is_private', False)
            if isinstance(is_private_req, str):
                is_private_req = is_private_req.lower() in ['true', '1']
            else:
                is_private_req = bool(is_private_req)
            if is_private_req:
                if 'issue.private' not in user_perms and 'issue.own_private' not in user_perms:
                    return False

            # (C) 하위 업무로 생성하는 경우, sub_manage 권한이 추가로 필요한지 확인
            if parent_id:
                return 'issue.sub_manage' in user_perms

        return True

    def has_object_permission(self, request, view, obj):
        # 1. 기존 프로젝트 접근 권한 체크
        if not super().has_object_permission(request, view, obj):
            return False

        # 슈퍼유저/관리자
        user = request.user
        is_admin = user.is_superuser or getattr(user, 'work_manager', False)

        # 2. issue_visible에 의한 개별 업무 읽기 권한(SAFE_METHODS) 검사
        if request.method in permissions.SAFE_METHODS:
            project = getattr(obj, 'project', None)
            if not project:
                return False

            # [잠금보관 프로젝트 제한]
            if project and project.status == '9':
                return False

            if is_admin:
                return True

            user_perms = project.get_user_permissions(user)
            role_attrs = project.get_user_role_attributes(user)
            issue_visible = role_attrs.get('issue_visible', 'NOP')
            is_own = (obj.creator == user or obj.assigned_to == user)

            # 비공개 업무 열람 권한 체크 (Method D)
            # issue_visible='ALL' OR issue.private OR (issue.own_private AND is_own) OR is_own(creator/assignee)
            if obj.is_private:
                can_read_private = (
                        issue_visible == 'ALL'
                        or 'issue.private' in user_perms
                        or ('issue.own_private' in user_perms and is_own)
                        or is_own
                )
                if not can_read_private:
                    return False

            # 일반 업무 가시성 체크
            if issue_visible == 'ALL':
                pass  # 모두 허용
            elif issue_visible == 'PUB':
                pass  # 공개 업무는 허용, 비공개는 위에서 처리됨
            elif issue_visible in ('PRI', 'NOP'):
                if not is_own:
                    return False

            return True

        # 3. 수정 및 삭제 관련 로직
        if view.action in ['update', 'partial_update', 'destroy', 'toggle_private']:
            project = getattr(obj, 'project', None)
            if not project:
                return False

            # 일반 관리자 예외 처리
            if is_admin:
                return True

            user_perms = project.get_user_permissions(user)

            # (A) 수정 권한 처리
            if view.action in ['update', 'partial_update']:
                # 하위 업무 수정 혹은 상위 관계 수정 시
                is_sub = (obj.parent_id is not None) or ('parent' in request.data) or ('del_child' in request.data)
                if is_sub:
                    return 'issue.sub_manage' in user_perms

                # 기본 수정 권한 확인
                is_own = (obj.creator == user) or (obj.assigned_to == user)
                has_update = 'issue.update' in user_perms
                has_own_update = 'issue.own_update' in user_perms and is_own
                if not (has_update or has_own_update):
                    return False

                # is_private 변경 시 추가 쓰기 권한 검사 (Method D)
                is_private_req = request.data.get('is_private', None)
                if is_private_req is not None:
                    if isinstance(is_private_req, str):
                        is_private_req = is_private_req.lower() in ['true', '1']
                    else:
                        is_private_req = bool(is_private_req)
                    if is_private_req != obj.is_private:
                        has_write_private = (
                                'issue.private' in user_perms
                                or ('issue.own_private' in user_perms and is_own)
                        )
                        if not has_write_private:
                            return False
                return True

            # (B) 삭제 권한 처리
            if view.action == 'destroy':
                if obj.parent_id is not None:
                    return 'issue.sub_manage' in user_perms
                return 'issue.delete' in user_perms

            # (C) 공개/비공개 토글 권한 처리
            if view.action == 'toggle_private':
                if 'issue.private' in user_perms:
                    return True
                if 'issue.own_private' in user_perms:
                    if (obj.creator == user) or (obj.assigned_to == user):
                        return True
                return False

        return True


class IssueRelationPermission(ProjectPermission):
    def has_permission(self, request, view):
        # 1. 부모 클래스(ProjectPermission)의 기본 생성 검사 수행
        if not super().has_permission(request, view):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # 1. 기존 프로젝트 접근 권한 체크
        if not super().has_object_permission(request, view, obj):
            return False

        project = self.extract_project(obj)
        if not project:
            return False

        # 슈퍼유저/관리자 예외 처리
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return True

        user_perms = project.get_user_permissions(request.user)
        required_perm = getattr(view, 'required_permission', None)

        if not required_perm:
            return False

        return required_perm in user_perms


class IssueCommentPermission(ProjectPermission):
    def has_object_permission(self, request, view, obj):
        # 1. 기본 프로젝트 레벨 권한 선제 검증
        if not super().has_object_permission(request, view, obj):
            return False

        project = None
        if hasattr(obj, 'issue') and hasattr(obj.issue, 'project'):
            project = obj.issue.project

        if not project:
            return False

        # 슈퍼유저 / 업무 관리자는 모든 검증을 통과
        user = request.user
        if user.is_superuser or getattr(user, 'work_manager', False):
            return True

        user_perms = project.get_user_permissions(user)

        # [비공개 댓글 가드] 작성자가 아니고 비공개 댓글 보기 권한이 없으면 접근 전면 차단
        if obj.is_private and obj.creator != user:
            if 'issue.private_comment_read' not in user_perms:
                return False

        # 2. 안전한 메서드(GET, HEAD, OPTIONS)는 통과
        if request.method in permissions.SAFE_METHODS:
            return True

        # 3. 수정 및 삭제 관련 로직
        if view.action in ['update', 'partial_update', 'destroy']:
            # (A) 댓글 수정 권한 처리
            if view.action in ['update', 'partial_update']:
                # 1) is_private 변경 시도 검증
                if 'is_private' in request.data:
                    req_private = request.data.get('is_private')
                    if isinstance(req_private, str):
                        req_private = req_private.lower() in ['true', '1']

                    if req_private != obj.is_private:
                        # 이미 관리자에 의해 잠긴 댓글(is_blocked=True)인 경우 권한 소유자만 설정 변경 가능
                        if obj.is_blocked and 'issue.private_comment_set' not in user_perms:
                            return False

                        is_own_comment = (obj.creator == user)
                        has_set_perm = 'issue.private_comment_set' in user_perms
                        if not (is_own_comment or has_set_perm):
                            return False

                # 2) 댓글 내용 수정 권한 검증
                if 'issue.comment_update' in user_perms:
                    return True
                if 'issue.comment_own_update' in user_perms:
                    if obj.creator == user:
                        return True
                return False

            # (B) 댓글 삭제 권한 처리
            if view.action == 'destroy':
                if 'issue.comment_update' in user_perms:
                    return True
                if 'issue.comment_own_update' in user_perms:
                    if obj.creator == user:
                        return True
                return False

        return True


class NewsPermission(ProjectPermission):
    pass


class DocumentPermission(ProjectPermission):
    def has_object_permission(self, request, view, obj):
        # 1. 기본 프로젝트 레벨 권한 검증
        if not super().has_object_permission(request, view, obj):
            return False

        # 2. 조회 요청은 통과
        if request.method in permissions.SAFE_METHODS:
            return True

        # 3. 연관된 문서(docs)가 기밀 상태인 경우 소유자 및 관리자만 수정/삭제 허용
        docs = getattr(obj, 'docs', None)
        if docs and docs.is_secret:
            user = request.user
            is_admin = user.is_superuser or getattr(user, 'work_manager', False)
            if not is_admin and docs.creator != user:
                return False

        return True


class ForumPermission(ProjectPermission):
    def has_object_permission(self, request, view, obj):
        # 1. 기본 프로젝트 레벨 권한 검증
        if not super().has_object_permission(request, view, obj):
            return False

        project = self.extract_project(obj)
        if not project:
            return False

        user = request.user
        user_perms = project.get_user_permissions(user)

        # 2. 조회(SAFE_METHODS) 요청 시 forum.read 권한 엄격히 대조 (레드마인 모델 준수)
        # 추천/신고(Like/Blame) 뷰셋들의 PATCH/PUT 액션 또한 'forum.read' 권한으로 판별
        is_like_blame_view = 'like' in view.__class__.__name__.lower() or 'blame' in view.__class__.__name__.lower()
        if request.method in permissions.SAFE_METHODS or is_like_blame_view:
            required_perm = getattr(view, 'required_permission', 'forum.read') or 'forum.read'
            return required_perm in user_perms

        # 3. 수정 권한 제어
        if view.action in ['update', 'partial_update']:
            if 'forum.update' in user_perms:
                return True
            if 'forum.own_update' in user_perms:
                # 본인의 글(Post/Comment/첨부물)인지 확인
                creator = getattr(obj, 'creator', None) or getattr(obj, 'author', None)
                if creator == user:
                    return True
            return False

        # 4. 삭제 권한 제어
        if view.action == 'destroy':
            if 'forum.delete' in user_perms:
                return True
            if 'forum.own_delete' in user_perms:
                # 본인의 글(Post/Comment/첨부물)인지 확인
                creator = getattr(obj, 'creator', None) or getattr(obj, 'author', None)
                if creator == user:
                    return True
            return False

        return True


class QueryPermission(ProjectPermission):
    def has_object_permission(self, request, view, obj):
        # 1. 기본 프로젝트 레벨 접근 허용 여부 체크
        if not super().has_object_permission(request, view, obj):
            return False

        user = request.user
        if user.is_superuser or getattr(user, 'work_manager', False):
            return True

        # 2. 조회 권한 분기
        if request.method in permissions.SAFE_METHODS:
            # 개인 검색양식은 작성자 본인만 조회 가능
            if not obj.is_public and obj.user != user:
                return False
            return True

        # 3. 쓰기(수정/삭제) 권한 분기
        project = self.extract_project(obj)
        if project:
            user_perms = set(project.get_user_permissions(user))
        else:
            # 프로젝트가 없는 경우 (글로벌 쿼리 등), 회원이 속한 프로젝트들의 권한 및 회원 기본 역할 권한 합산
            from work.models.project import Role
            user_perms = set(
                Role.objects.filter(
                    projects__members__user=user
                ).filter(
                    permissions__code__in=['project.save_query', 'project.pub_query']
                ).values_list('permissions__code', flat=True)
            )
            try:
                role2 = Role.objects.prefetch_related('permissions').get(pk=2)
                user_perms.update(role2.permissions.values_list('code', flat=True))
            except Role.DoesNotExist:
                pass

        # 공용 검색양식 제어 시도하는 경우 -> 'project.pub_query' 권한 필수
        if obj.is_public:
            return 'project.pub_query' in user_perms

        # 개인 검색양식을 수정/삭제하려는 경우 -> 본인이어야 하고 'project.save_query' 권한 필요
        return obj.user == user and 'project.save_query' in user_perms
