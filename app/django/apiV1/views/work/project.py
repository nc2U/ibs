from django.db.models import Q
from django_filters.rest_framework import FilterSet, BooleanFilter, CharFilter
from rest_framework import viewsets

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.project import *


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

    @property
    def required_permission(self):
        mapping = {  # 매핑 로직 정의
            'create': 'project.create',
            'update': 'project.update',
            'partial_update': 'project.update',
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

        # 3. 액션에 따른 추가 필드 로드 최적화
        if self.action == 'list':
            return base_qs.select_related('company', 'module', 'creator')
        # For detail view, we can add non-recursive annotations as a hint
        return base_qs.select_related('company', 'module', 'creator', 'parent', 'default_version')

    def get_serializer_class(self):
        if self.action == 'list':
            return IssueProjectListSerializer
        return IssueProjectSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationOneHundred


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    filterset_fields = ('user',)
