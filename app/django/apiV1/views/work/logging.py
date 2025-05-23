from django_filters.rest_framework import FilterSet, BooleanFilter, DateFilter, CharFilter
from rest_framework import viewsets
from rest_framework.views import APIView

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.logging import *


class ActivityLogFilter(FilterSet):
    project__search = CharFilter(field_name='project__slug', label='project-search')
    from_act_date = DateFilter(field_name='act_date', lookup_expr='gte', label='From log date')
    to_act_date = DateFilter(field_name='act_date', lookup_expr='lte', label='To log date')
    sort = CharFilter(method='sort_filter')

    class Meta:
        model = ActivityLogEntry
        fields = ('project__slug', 'from_act_date', 'to_act_date', 'user', 'sort')

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
