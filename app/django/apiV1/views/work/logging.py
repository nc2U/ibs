from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django_filters.rest_framework import FilterSet, DateFilter, CharFilter
from rest_framework import viewsets

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.logging import *
from work.models import IssueProject


def get_sub_project_ids(parent):
    cache_key = f"filter:sub_projects:{parent.id}"
    project_ids = cache.get(cache_key)
    if project_ids is None:
        table_name = IssueProject._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    WITH RECURSIVE project_tree AS (
                        SELECT id FROM {table_name} WHERE id = %s
                        UNION
                        SELECT p.id
                        FROM {table_name} p
                        JOIN project_tree pt ON p.parent_id = pt.id
                    )
                    SELECT id FROM project_tree
                """, [parent.id])
            project_ids = [row[0] for row in cursor.fetchall()]
        cache.set(cache_key, project_ids, timeout=3600)
    return project_ids


class ActivityLogFilter(FilterSet):
    project__slug = CharFilter(method='filter_by_project_with_sub', label='프로젝트+하위')
    project__search = CharFilter(method='filter_by_project_only', label='프로젝트만')
    from_act_date = DateFilter(field_name='act_date', lookup_expr='gte', label='시작 로그일자')
    to_act_date = DateFilter(field_name='act_date', lookup_expr='lte', label='기한 로그일자')
    sort = CharFilter(method='filter_by_sort_code')

    class Meta:
        model = ActivityLogEntry
        fields = ('project__slug', 'project__search', 'from_act_date', 'to_act_date', 'creator', 'sort')

    def filter_by_project_with_sub(self, queryset, name, value):
        try:
            project = IssueProject.objects.get(slug=value)
            project_ids = [project.pk] + get_sub_project_ids(project)
            return queryset.filter(project__id__in=project_ids)
        except IssueProject.DoesNotExist:
            return queryset.none()

    @staticmethod
    def filter_by_project_only(queryset, name, value):
        return queryset.filter(project__slug=value)

    @staticmethod
    def filter_by_sort_code(queryset, name, value):
        valid_sorts = {'1', '2', '4', '5', '8', '9'}
        sort_values = [v for v in value.split(",") if v in valid_sorts]
        if sort_values:
            queryset = queryset.filter(sort__in=sort_values)
        return queryset


class ActivityLogEntryViewSet(viewsets.ModelViewSet):
    queryset = ActivityLogEntry.objects.all()
    serializer_class = ActivityLogEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = ActivityLogFilter

    def get_queryset(self):
        """ActivityLogEntry 필터링: 사용자 권한 기반"""
        user = self.request.user
        work_auth = user.work_manager or user.is_superuser
        projects = user.assigned_projects().values_list('pk', flat=True)
        queryset = self.queryset
        if not work_auth:
            queryset = queryset.filter(
                Q(project__is_public=True) |
                Q(project__in=projects))
        return queryset.select_related('project', 'creator', 'issue', 'comment', 'news', 'spent_time')

    def list(self, request, *args, **kwargs):
        """ActivityLogEntry 데이터를 반환"""

        # ActivityLogEntry 조회
        logs = self.filter_queryset(self.get_queryset()).values(
            'pk', 'sort', 'project__id', 'project__name', 'project__slug',
            'issue__id', 'issue__tracker__name', 'issue__status__name',
            'issue__status__closed', 'issue__subject', 'issue__description',
            'status_log', 'comment__id', 'comment__content', 'news__title',
            'news__summary', 'spent_time__hours', 'spent_time__comment',
            'act_date', 'timestamp', 'creator__id', 'creator__username')

        # 데이터 변환 (제너레이터)
        log_data = [{
            'pk': log['pk'],
            'sort': log['sort'],
            'project': {
                'pk': log['project__id'],
                'name': log['project__name'],
                'slug': log['project__slug'],
            },
            'issue': {
                'pk': log['issue__id'],
                'tracker': log['issue__tracker__name'],
                'status': {'name': log['issue__status__name'], 'closed': log['issue__status__closed']},
                'subject': log['issue__subject'],
                'description': log['issue__description'],
            },
            'status_log': log['status_log'],
            'comment': {
                'pk': log['comment__id'],
                'content': log['comment__content'],
            },
            'news': {'title': log['news__title'], 'summary': log['news__summary']},
            'spent_time': {'hours': log['spent_time__hours'], 'comment': log['spent_time__comment']},
            'act_date': log['act_date'],
            'timestamp': log['timestamp'],
            'creator': {'pk': log['creator__id'], 'username': log['creator__username']},
        } for log in logs]

        # 페이지네이션
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(log_data, request)
        return paginator.get_paginated_response(page)


class IssueLogEntryViewSet(viewsets.ModelViewSet):
    queryset = IssueLogEntry.objects.all()
    serializer_class = IssueLogEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('issue', 'creator')

    # def get_queryset(self):
    #     user = self.request.user
    #     work_auth = user.work_manager or user.is_superuser
    #     return self.queryset if work_auth else self.queryset.filter(issue__project__is_public=True)
