from django.db.models import Q
from django_filters.rest_framework import FilterSet, BooleanFilter, DateFilter, CharFilter
from rest_framework import viewsets
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
    fixed_version__exclude = CharFilter(field_name='fixed_version', exclude=True, label='목표버전-제외')
    fixed_version__isnull = BooleanFilter(field_name='fixed_version', lookup_expr='isnull', label='목표버전-유무')
    parent__subject = CharFilter(field_name='parent__subject', lookup_expr='icontains', label='상위업무-제목')
    parent__isnull = BooleanFilter(field_name='parent', lookup_expr='isnull', label='상위업무-유무')

    class Meta:
        model = Issue
        fields = ('project__slug', 'status__closed', 'status', 'tracker', 'creator',
                  'assigned_to', 'fixed_version', 'parent')

    def filter_queryset(self, queryset):
        for name, value in self.form.cleaned_data.items():
            if name == 'project__slug':
                try:
                    project = IssueProject.objects.get(slug=value)
                    subs = self.get_sub_projects(project)
                    # Include activity log entries related to the specified project and its subprojects
                    queryset = queryset.filter(
                        Q(project__slug=project.slug) | Q(project__slug__in=[sub.slug for sub in subs]))
                except IssueProject.DoesNotExist:
                    pass
            elif value is not None:
                # Apply other filters
                queryset = self.filters[name].filter(queryset, value)

        return queryset

    def get_sub_projects(self, parent):
        sub_projects = []
        children = IssueProject.objects.filter(parent=parent)
        for child in children:
            sub_projects.append(child)
            sub_projects.extend(self.get_sub_projects(child))
        return sub_projects


class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    filterset_class = IssueFilter

    def get_queryset(self):
        user = self.request.user
        work_auth = user.work_manager or user.is_superuser
        projects = user.assigned_projects()

        queryset = self.queryset.filter(project__in=projects)

        return queryset if work_auth else self.queryset \
            .filter(is_private=False) \
            .filter(project__is_public=True)

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
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('issue',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class IssueFileViewSet(viewsets.ModelViewSet):
    queryset = IssueFile.objects.all()
    serializer_class = IssueFileSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IssueCommentViewSet(viewsets.ModelViewSet):
    queryset = IssueComment.objects.all()
    serializer_class = IssueCommentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TimeEntryFilter(FilterSet):
    project__search = CharFilter(field_name='project__slug', label='프로젝트-검색')
    project__exclude = CharFilter(field_name='project__slug', exclude=True, label='프로젝트-제외')
    from_spent_on = DateFilter(field_name='spent_on', lookup_expr='gte', label='작업일자부터')
    to_spent_on = DateFilter(field_name='spent_on', lookup_expr='lte', label='작업일자부터')
    user__exclude = CharFilter(field_name='user', exclude=True, label='사용자-제외')
    issue__fixed_version__exclude = CharFilter(field_name='issue__fixed_version', exclude=True, label='목표버전-제외')

    class Meta:
        model = TimeEntry
        fields = ('project__slug', 'spent_on', 'issue', 'user', 'activity', 'hours',
                  'issue__tracker', 'issue__parent', 'issue__fixed_version', 'issue__category')

    def filter_queryset(self, queryset):

        for name, value in self.form.cleaned_data.items():
            if name == 'project__slug':
                try:
                    project = IssueProject.objects.get(slug=value)
                    subs = self.get_sub_projects(project)
                    queryset = queryset.filter(
                        Q(project__slug=project.slug) | Q(project__slug__in=[sub.slug for sub in subs]))
                except IssueProject.DoesNotExist:
                    pass
            elif value is not None:
                # Apply other filters
                queryset = self.filters[name].filter(queryset, value)

        return queryset

    def get_sub_projects(self, parent):
        sub_projects = []
        children = IssueProject.objects.filter(parent=parent)
        for child in children:
            sub_projects.append(child)
            sub_projects.extend(self.get_sub_projects(child))
        return sub_projects


class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    filterset_class = TimeEntryFilter
    search_fields = ('issue__subject', 'comment')

    def get_queryset(self):
        user = self.request.user
        work_auth = user.work_manager or user.is_superuser
        projects = user.assigned_projects()
        return self.queryset \
            if work_auth \
            else self.queryset.filter(Q(issue__project__is_public=True) |
                                      Q(issue__project__in=projects))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TrackerViewSet(viewsets.ModelViewSet):
    queryset = Tracker.objects.all()
    serializer_class = TrackerSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('projects',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IssueCategoryViewSet(viewsets.ModelViewSet):
    queryset = IssueCategory.objects.all()
    serializer_class = IssueCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
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
        serializer.save(user=self.request.user)


class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = (permissions.IsAuthenticated,)


class CodeActivityViewSet(viewsets.ModelViewSet):
    queryset = CodeActivity.objects.all()
    serializer_class = CodeActivitySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CodeIssuePriorityViewSet(viewsets.ModelViewSet):
    queryset = CodeIssuePriority.objects.all()
    serializer_class = CodeIssuePrioritySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
