from django.db.models import Q
from django_filters.rest_framework import FilterSet, BooleanFilter, CharFilter, NumberFilter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.issue import *


class IssueFilter(FilterSet):
    status__exclude = CharFilter(field_name='status', exclude=True, label='사용여부-제외')
    project__exclude = CharFilter(field_name='project__slug', exclude=True, label='프로젝트-제외')
    project__search = CharFilter(field_name='project__slug', label='프로젝트-검색')
    tracker__exclude = CharFilter(field_name='tracker', exclude=True, label='유형-제외')
    creator__exclude = CharFilter(field_name='creator', exclude=True, label='작성자-제외')
    assigned_to__exclude = CharFilter(field_name='assigned_to', exclude=True, label='담당자-제외')
    assigned_to__isnull = BooleanFilter(field_name='assigned_to', lookup_expr='isnull', label='담당자-유무')
    fixed_version__exclude = CharFilter(field_name='fixed_version', exclude=True, label='목표단계-제외')
    fixed_version__isnull = BooleanFilter(field_name='fixed_version', lookup_expr='isnull', label='목표단계-유무')

    id = NumberFilter(field_name='id', lookup_expr='exact', label='ID-일치')
    id__gte = NumberFilter(field_name='id', lookup_expr='gte', label='ID-이상')
    id__lte = NumberFilter(field_name='id', lookup_expr='lte', label='ID-이하')
    id__between = CharFilter(method='filter_id_between', label='ID-범위 (예: 10,20)')
    id__any = CharFilter(method='filter_id_any', label='ID-모두보기')

    parent__subject = CharFilter(field_name='parent__subject', lookup_expr='icontains', label='상위업무-제목')
    parent__isnull = BooleanFilter(field_name='parent', lookup_expr='isnull', label='상위업무-유무')
    parent_issue = NumberFilter(method='filter_parent_issue', label='상위업무-검색')
    parent = NumberFilter(method='filter_parent', label='하위업무-검색')
    follows_issue = NumberFilter(method='filter_follows', label='선행업무-검색')
    precedes_issue = NumberFilter(method='filter_precedes', label='후속업무-검색')

    class Meta:
        model = Issue
        fields = ('project__slug', 'status__closed', 'status', 'tracker', 'creator', 'assigned_to',
                  'fixed_version', 'id', 'id__gte', 'id__lte', 'id__between', 'id__any',
                  'parent', 'parent_issue', 'precedes_issue', 'follows_issue',)

    @staticmethod
    def filter_id_between(queryset, name, value):
        try:
            start, end = map(int, value.split(','))
            return queryset.filter(id__range=(start, end))
        except (ValueError, AttributeError):
            return queryset

    @staticmethod
    def filter_id_any(queryset, name, value):
        return queryset

    @staticmethod
    def filter_parent_issue(queryset, name, value):
        try:
            parent = Issue.objects.get(pk=value).parent
            return queryset.filter(pk=parent.pk) if parent else queryset.none()
        except Issue.DoesNotExist:
            return queryset.none()

    @staticmethod
    def filter_parent(queryset, name, value):
        return queryset.filter(parent=value)

    @staticmethod
    def filter_precedes(queryset, name, value):
        # 내가 선행하는 업무들 (내가 source이므로, 대상 target_id들을 찾음)
        pks = IssueRelation.objects.filter(source_id=value).values_list('target_id', flat=True)
        return queryset.filter(pk__in=pks)

    @staticmethod
    def filter_follows(queryset, name, value):
        # 내가 후속하는 업무들 (내가 target이므로, 대상 source_id들을 찾음)
        pks = IssueRelation.objects.filter(target_id=value).values_list('source_id', flat=True)
        return queryset.filter(pk__in=pks)

    def filter_queryset(self, queryset):
        for name, value in self.form.cleaned_data.items():
            if name == 'project__slug' and value:
                try:
                    project = IssueProject.objects.get(slug=value)
                    all_projects = list(IssueProject.objects.all())
                    sub_projects_slugs = []

                    def collect_children(parent_obj):
                        for p in all_projects:
                            if p.parent_id == parent_obj.id:
                                sub_projects_slugs.append(p.slug)
                                collect_children(p)

                    collect_children(project)
                    slugs = [project.slug] + sub_projects_slugs
                    queryset = queryset.filter(project__slug__in=slugs)
                except IssueProject.DoesNotExist:
                    pass
            elif value is not None and name != 'project__slug':
                queryset = self.filters[name].filter(queryset, value)

        return queryset


class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = (permissions.IsAuthenticated, IssuePermission)
    pagination_class = PageNumberPaginationTwenty
    filterset_class = IssueFilter

    @property
    def required_permission(self):
        mapping = {
            'list': 'issue.read',
            'retrieve': 'issue.read',
            'create': 'issue.create',
            'update': 'issue.update',
            'partial_update': 'issue.update',
            'destroy': 'issue.delete',
            'toggle_private': 'issue.public'
        }
        return mapping.get(self.action, None)

    @action(detail=True, methods=['post'])
    def toggle_private(self, request, pk=None):
        issue = self.get_object()
        issue.is_private = not issue.is_private
        issue.save()
        return Response({'is_private': issue.is_private})

    def get_queryset(self):
        user = self.request.user

        # 기본 쿼리셋에 관계형 필드를 미리 로딩하여 N+1 문제 방지
        # + 프로젝트 상태가 '1'(사용)인 업무만 조회하도록 제한 (전역 조건)
        queryset = self.queryset.filter(project__status='1').select_related(
            'project', 'status', 'creator', 'assigned_to', 'tracker', 'fixed_version'
        )

        # 관리자는 모든 사용 중인 프로젝트의 업무에 접근 가능
        if getattr(user, 'work_manager', False) or user.is_superuser:
            return queryset

        # 사용자가 멤버로 속한 프로젝트 ID 목록
        member_project_ids = user.member_project_ids()

        # 접근 가능 범위 정의 (프로젝트 상태 '1'은 위에서 이미 필터링됨)
        # 1. 멤버인 프로젝트의 모든 업무
        # 2. 공개 프로젝트의 업무
        # 3. 비공개 업무라도 사용자가 작성자(creator)이거나 담당자(assigned_to)인 경우
        return queryset.filter(
            Q(project__id__in=member_project_ids) |
            Q(project__is_public=True) |
            Q(creator=user) |
            Q(assigned_to=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updater=self.request.user)


class IssueCountByMemberView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    # filterset_fields = ('projects',)

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.query_params.get('user', None)

        # Count issues assigned to the user
        issues_in_charge = Issue.objects.filter(assigned_to=user)
        open_charged = issues_in_charge.filter(closed__isnull=True).count()
        closed_charged = issues_in_charge.filter(closed__isnull=False).count()
        all_charged = open_charged + closed_charged

        # Count issues created by the user
        issues_in_created = Issue.objects.filter(creator=user)
        open_created = issues_in_created.filter(closed__isnull=True).count()
        closed_created = issues_in_created.filter(closed__isnull=False).count()
        all_created = open_created + closed_created

        summary_data = {
            'open_charged': open_charged,
            'closed_charged': closed_charged,
            'all_charged': all_charged,
            'open_created': open_created,
            'closed_created': closed_created,
            'all_created': all_created
        }

        serializer = IssueCountByMemberSerializer(summary_data)
        return Response(serializer.data)


class IssueRelationViewSet(viewsets.ModelViewSet):
    queryset = IssueRelation.objects.all()
    serializer_class = IssueRelationSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('source',)

    @property
    def required_permission(self):
        mapping = {
            'create': 'issue.rel_manage',
            'update': 'issue.rel_manage',
            'partial_update': 'issue.rel_manage',
            'destroy': 'issue.rel_manage'
        }
        return mapping.get(self.action, None)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(creator=self.request.user)


class IssueFileViewSet(viewsets.ModelViewSet):
    queryset = IssueFile.objects.all()
    serializer_class = IssueFileSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    @property
    def required_permission(self):
        mapping = {
            'create': 'issue.update',
            'update': 'issue.update',
            'partial_update': 'issue.update',
            'destroy': 'issue.update'
        }
        return mapping.get(self.action, None)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class IssueCommentViewSet(viewsets.ModelViewSet):
    queryset = IssueComment.objects.all()
    serializer_class = IssueCommentSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class TrackerViewSet(viewsets.ModelViewSet):
    queryset = Tracker.objects.all()
    serializer_class = TrackerSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('projects',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class IssueCategoryViewSet(viewsets.ModelViewSet):
    queryset = IssueCategory.objects.all()
    serializer_class = IssueCategorySerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    filterset_fields = ('project__slug',)


class IssueCountByTrackerViewSet(viewsets.ModelViewSet):
    queryset = Tracker.objects.all()
    serializer_class = IssueCountByTrackerSerializer
    filterset_fields = ('projects',)

    def get_serializer_context(self):
        # Pass the request object as context to the serializer
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class IssueStatusViewSet(viewsets.ModelViewSet):
    queryset = IssueStatus.objects.all()
    serializer_class = IssueStatusSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = (permissions.IsAuthenticated,)


class CodeIssuePriorityViewSet(viewsets.ModelViewSet):
    queryset = CodeIssuePriority.objects.all()
    serializer_class = CodeIssuePrioritySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
