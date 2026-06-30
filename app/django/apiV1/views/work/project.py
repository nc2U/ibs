from django.db.models import Q
from django_filters.rest_framework import FilterSet, BooleanFilter, CharFilter
from rest_framework import viewsets, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apiV1.pagination import PageNumberPaginationTwenty, PageNumberPaginationOneHundred
from apiV1.permissions.auth_perms import IsWorkManagerReadOnly
from apiV1.permissions.work_perms import ProjectPermission
from apiV1.serializers.work import IssueProjectSerializer, IssueProjectListSerializer, \
    ModuleSerializer, RoleSerializer, PermissionSerializer, MemberSerializer, VersionSerializer
from work.models import IssueProject, Module, Role, Permission, Member, Version


# Work --------------------------------------------------------------------------
class IssueProjectFilter(FilterSet):
    status__exclude = CharFilter(field_name='status', exclude=True, label='사용여부-제외')
    parent__isnull = BooleanFilter(field_name='parent', lookup_expr='isnull', label='최상위 프로젝트')
    project = CharFilter(field_name='slug', lookup_expr='exact', label='프로젝트')
    project__exclude = CharFilter(field_name='slug', exclude=True, label='프로젝트-제외')
    is_public__exclude = BooleanFilter(field_name='is_public', exclude=True, label='공개여부-제외')
    name = CharFilter(field_name='name', lookup_expr='icontains', label='이름')
    description = CharFilter(field_name='description', lookup_expr='icontains', label='설명')

    class Meta:
        model = IssueProject
        fields = ('company', 'sort', 'status', 'parent__slug', 'project',
                  'is_public', 'name', 'members__user', 'description')


class IssueProjectViewSet(viewsets.ModelViewSet):
    queryset = IssueProject.objects.all()
    serializer_class = IssueProjectSerializer
    lookup_field = 'slug'
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    pagination_class = PageNumberPaginationTwenty
    filterset_class = IssueProjectFilter

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, slug=None):
        project = self.get_object()
        # 상태 전환 로직 (예: '1' -> '9', '9' -> '1')
        project.status = '9' if project.status == '1' else '1'
        project.save()
        return Response({'status': project.status})

    @action(detail=True, methods=['post'])
    def toggle_public(self, request, slug=None):
        project = self.get_object()
        project.is_public = not project.is_public
        project.save()
        return Response({'is_public': project.is_public})

    @action(detail=True, methods=['post'])
    def update_members(self, request, slug=None):
        project = self.get_object()
        users = request.data.get('users', [])
        roles = request.data.get('roles', [])
        del_mem = request.data.get('del_mem')

        if users:
            for user_id in users:
                member, _ = Member.objects.get_or_create(user_id=user_id, project=project)
                if roles:
                    member.roles.set(roles)
                member.save()
            return Response({'status': 'members updated'})
        elif del_mem is not None:
            Member.objects.filter(pk=del_mem, project=project).delete()
            return Response({'status': 'member deleted'})

        return Response({'status': 'no action taken'}, status=400)

    @property
    def required_permission(self):
        mapping = {  # 매핑 로직 정의
            'create': 'project.create',
            'update': 'project.update',
            'partial_update': 'project.update',
            'toggle_status': 'project.close',
            'toggle_public': 'project.public',
            'update_members': 'project.member',
            'destroy': 'project.delete'
        }
        # 정의되지 않은 액션에 대해 기본 권한 반환
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # 1. 슈퍼유저나 work_manager는 전체 프로젝트 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:  # 2. 비공개 프로젝트는 멤버인 경우만, 공개 프로젝트는 모두 조회 가능
            base_qs = queryset.filter(Q(is_public=True) | Q(members__user=user)).distinct()

        # 3. Prefetch 최적화 추가 (N+1 문제 해결)
        base_qs = base_qs.prefetch_related(
            'members__user', 'members__roles',
            'trackers', 'versions', 'categories__assigned_to',
            'allowed_roles'
        )

        # 4. 액션에 따른 추가 필드 로드 최적화
        if self.action == 'list':
            return base_qs.select_related('company', 'module', 'creator')
        # For detail view, we can add non-recursive annotations as a hint
        return base_qs.select_related('company', 'module', 'creator', 'parent', 'default_version')

    def get_serializer_class(self):
        if self.action == 'list':
            return IssueProjectListSerializer
        return IssueProjectSerializer

    def perform_create(self, serializer):
        parent_slug = self.request.data.get('parent_slug')
        if parent_slug:
            # 하위 프로젝트 생성 권한 체크
            try:
                parent_project = IssueProject.objects.get(slug=parent_slug)
            except IssueProject.DoesNotExist:
                raise serializers.ValidationError({"parent_slug": "부모 프로젝트를 찾을 수 없습니다."})
            user_perms = parent_project.get_user_permissions(self.request.user)
            if 'project.create_sub' not in user_perms:
                raise serializers.PermissionDenied("하위 프로젝트를 생성할 권한이 없습니다.")
            serializer.save(creator=self.request.user, parent=parent_project)
        else:
            # 일반 프로젝트 생성
            serializer.save(creator=self.request.user)


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)

    @property
    def required_permission(self):
        mapping = {  # 매핑 로직 정의
            'create': 'project.module',
            'update': 'project.module',
            'partial_update': 'project.module',
            'destroy': 'project.module'
        }
        # 정의되지 않은 액션에 대해 기본 권한 반환
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().select_related('project')

        # 1. 슈퍼유저나 work_manager는 전체 모듈 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        # 2. 접근 가능한 프로젝트의 모듈만 조회
        # - 공개 프로젝트 OR 사용자가 멤버인 프로젝트
        return queryset.filter(
            Q(project__is_public=True) | Q(project__members__user=user)
        ).distinct()


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().select_related('creator')
    serializer_class = RoleSerializer
    permission_classes = (permissions.IsAuthenticated, IsWorkManagerReadOnly)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationOneHundred


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    filterset_fields = ('user',)

    @property
    def required_permission(self):
        mapping = {  # 매핑 로직 정의
            'create': 'project.member',
            'update': 'project.member',
            'partial_update': 'project.member',
            'destroy': 'project.member'
        }
        # 정의되지 않은 액션에 대해 기본 권한 반환
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().select_related('project', 'user')

        # 1. 슈퍼유저나 work_manager는 전체 멤버 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset.prefetch_related('roles')

        # 2. 사용자의 프로젝트별 user_visible 권한 수준 판별
        from work.models.project import Member as ProjectMember
        user_members = ProjectMember.objects.filter(user=user).prefetch_related('roles')

        user_visibility_order = {'ALL': 2, 'PRJ': 1, 'NOP': 0}
        best_user_visible = 'NOP'

        for member in user_members:
            for role in member.roles.all():
                if user_visibility_order.get(role.user_visible, 0) > user_visibility_order.get(best_user_visible, 0):
                    best_user_visible = role.user_visible

        from work.models.project import Role
        try:
            non_member_role = Role.objects.get(pk=2)
            non_member_user_visible = non_member_role.user_visible
        except Role.DoesNotExist:
            non_member_user_visible = 'NOP'

        if not user_members.exists():
            best_user_visible = non_member_user_visible

        # 3. 수준별 필터링 적용
        member_project_ids = [m.project_id for m in user_members]

        if best_user_visible == 'ALL':
            return queryset.filter(
                Q(project__is_public=True) | Q(project_id__in=member_project_ids)
            ).distinct().prefetch_related('roles')
        elif best_user_visible == 'PRJ':
            return queryset.filter(project_id__in=member_project_ids).distinct().prefetch_related('roles')
        elif best_user_visible == 'NOP':
            return queryset.filter(user=user).prefetch_related('roles')

        return queryset.none()


class VersionFilter(FilterSet):
    status__exclude = CharFilter(field_name='status', exclude=True, label='상태-제외')

    class Meta:
        model = Version
        fields = ('project__slug', 'status')


class VersionViewSet(viewsets.ModelViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    filterset_class = VersionFilter
    search_fields = ('name', 'description')

    def get_queryset(self):
        user = self.request.user
        queryset = Version.objects.all()

        # 1. 슈퍼유저나 work_manager는 전체 버전 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 접근 가능한 프로젝트의 버전만 조회
            base_qs = queryset.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()

        # 3. 성능 최적화
        return base_qs.select_related('project').prefetch_related('issues__tracker', 'issues__project')

    @property
    def required_permission(self):
        mapping = {  # 매핑 로직 정의
            'create': 'project.version',
            'update': 'project.version',
            'partial_update': 'project.version',
            'destroy': 'project.version'
        }
        # 정의되지 않은 액션에 대해 기본 권한 반환
        return mapping.get(self.action, None)
