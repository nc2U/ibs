from django.db.models import Q
from django_filters.rest_framework import FilterSet, DateFilter, CharFilter
from rest_framework import viewsets

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work import CommitSerializer
from apiV1.serializers.work.logging import *
from work.models import IssueProject, Commit


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
                sub_slugs = [p.slug for p in self.get_sub_projects(project)]
                queryset = queryset.filter(Q(project__slug=project.slug) | Q(project__slug__in=sub_slugs))
            except IssueProject.DoesNotExist:
                return queryset.none()  # 존재하지 않으면 빈 쿼리셋 반환

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
    # pagination_class = PageNumberPaginationThreeHundred
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = ActivityLogFilter

    def get_queryset(self):
        """ActivityLogEntry 필터링: 사용자 권한 기반"""
        user = self.request.user
        work_auth = user.work_manager or user.is_superuser
        projects = user.assigned_projects()
        return self.queryset \
            if work_auth \
            else self.queryset.filter(
            Q(project__is_public=True) |
            Q(project__in=projects)).select_related(
            'project', 'issue', 'comment', 'user', 'spent_time')

    # def get_commits(self):
    #     """Commit 데이터 조회: 프로젝트 권한 적용"""
    #     user = self.request.user
    #     work_auth = user.work_manager or user.is_superuser
    #     projects = user.assigned_projects()
    #     queryset = Commit.objects.filter(repo__slug='ibs')
    #     if not work_auth:
    #         queryset = queryset.filter(
    #             Q(issues__project__is_public=True) |
    #             Q(issues__project__in=projects)
    #         )
    #     return queryset.select_related('repo').prefetch_related('issues').distinct().order_by('-date')
    #
    # def list(self, request, *args, **kwargs):
    #     """ActivityLogEntry와 Commit 데이터를 병합하여 반환"""
    #     # ActivityLogEntry 조회
    #     queryset = self.filter_queryset(self.get_queryset())
    #     logs = queryset.order_by('-timestamp')
    #     log_serializer = self.get_serializer(logs, many=True)
    #     log_data = log_serializer.data
    #
    #     # Commit 조회
    #     commits = self.get_commits()
    #     commit_serializer = CommitSerializer(commits, many=True)
    #     commit_data = commit_serializer.data
    #
    #     # 데이터 병합
    #     combined = [
    #         *[{"data": log} for log in log_data],
    #         *[{
    #             "data": {
    #                 "sort": "3",
    #                 "commit_hash": c["commit_hash"],
    #                 "timestamp": c["date"],
    #                 "status_log": c["message"][:30],
    #                 "user": {"username": c["author"]} if c["author"] else None,  # User 매핑
    #                 "project": c["issues"][0]["project"] if c["issues"] else None
    #             }
    #         } for c in commit_data]
    #     ]
    #
    #     # 시간순 정렬
    #     combined = sorted(
    #         combined,
    #         key=lambda x: x["data"]["timestamp"],
    #         reverse=True
    #     )
    #
    #     # 페이지네이션 적용
    #     paginator = self.pagination_class()
    #     page = paginator.paginate_queryset(combined, request)
    #     return paginator.get_paginated_response(page)


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
