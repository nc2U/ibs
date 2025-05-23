from django.db.models import Q
from django_filters.rest_framework import FilterSet, DateFilter, CharFilter
from rest_framework import viewsets

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.logging import *
from work.models import IssueProject


class ActivityLogFilter(FilterSet):
    project__search = CharFilter(field_name='project__slug', label='project-search')
    from_act_date = DateFilter(field_name='act_date', lookup_expr='gte', label='From log date')
    to_act_date = DateFilter(field_name='act_date', lookup_expr='lte', label='To log date')
    sort = CharFilter(method='sort_filter')

    class Meta:
        model = ActivityLogEntry
        fields = ('project__slug', 'from_act_date', 'to_act_date', 'user', 'sort')

    def filter_queryset(self, queryset):
        cleaned_data = self.form.cleaned_data
        project_slug = cleaned_data.get('project__slug')  # 먼저 project__slug 필터링 처리

        if project_slug:
            try:
                project = IssueProject.objects.get(slug=project_slug)
                sub_slugs = list(self.get_sub_projects(project).values_list('slug', flat=True))
                queryset = queryset.filter(Q(project__slug=project.slug) |
                                           Q(project__slug__in=sub_slugs))
            except IssueProject.DoesNotExist:
                # 존재하지 않으면 빈 쿼리셋 반환
                return queryset.none()

        # 나머지 필드에 대해 일반 필터링 수행
        for name, value in cleaned_data.items():
            if name != 'project__slug' and value is not None:
                queryset = self.filters[name].filter(queryset, value)

        return queryset

    @staticmethod
    def sort_filter(queryset, name, value):
        if value:
            queryset = queryset.filter(sort__in=value.split(","))
        return queryset

    def get_sub_projects(self, parent):
        sub_projects = []
        children = IssueProject.objects.filter(parent=parent)
        for child in children:
            sub_projects.append(child)
            sub_projects.extend(self.get_sub_projects(child))
        return sub_projects


class ActivityLogEntryViewSet(viewsets.ModelViewSet):
    queryset = ActivityLogEntry.objects.all()
    serializer_class = ActivityLogEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = ActivityLogFilter

    def get_queryset(self):
        user = self.request.user
        work_auth = user.work_manager or user.is_superuser
        projects = user.assigned_projects()
        return self.queryset \
            if work_auth \
            else self.queryset.filter(Q(project__is_public=True) |
                                      Q(project__in=projects))


class IssueLogEntryViewSet(viewsets.ModelViewSet):
    queryset = IssueLogEntry.objects.all()
    serializer_class = IssueLogEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('issue', 'user')

    # def get_queryset(self):
    #     user = self.request.user
    #     work_auth = user.work_manager or user.is_superuser
    #     return self.queryset if work_auth else self.queryset.filter(issue__project__is_public=True)
