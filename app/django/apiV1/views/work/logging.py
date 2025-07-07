from heapq import merge

from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django_filters.rest_framework import FilterSet, DateFilter, CharFilter
from rest_framework import viewsets

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.logging import *
from work.models import IssueProject, Commit


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
        fields = ('project__slug', 'project__search', 'from_act_date', 'to_act_date', 'user', 'sort')

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
        valid_sorts = {'1', '2', '3', '4', '5', '6', '7', '8', '9'}
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
        if work_auth:
            return self.queryset
        return self.queryset.filter(
            Q(project__is_public=True) |
            Q(project__in=projects)).select_related('project', 'user')

    def get_commits(self):
        user = self.request.user

        work_auth = user.work_manager or user.is_superuser
        projects = user.assigned_projects().values_list('id', flat=True)

        # 필터 파라미터 가져오기
        # fields = ('sort', 'project__slug', 'from_act_date', 'to_act_date')
        query_params = self.request.query_params
        sort = query_params.get('sort')
        project_slug = query_params.get('project__slug')
        from_date = query_params.get('from_act_date')
        to_date = query_params.get('to_act_date')

        # 기본 쿼리셋
        if not sort or '3' in sort:
            queryset = Commit.objects.all()

            if not work_auth:
                queryset = queryset.filter(
                    Q(repo__project__is_public=True) |
                    Q(repo__project__in=projects))

            # project__slug → IssueProject id 목록
            if project_slug:
                try:
                    project = IssueProject.objects.get(slug=project_slug)
                    project_ids = [project.pk] + [pk for pk in get_sub_project_ids(project)]
                    queryset = queryset.filter(repo__project__id__in=project_ids)
                except IssueProject.DoesNotExist:
                    return Commit.objects.none()

            if from_date:
                queryset = queryset.filter(date__gte=from_date)
            if to_date:
                queryset = queryset.filter(date__lte=to_date)

            return queryset.select_related('repo').order_by('-date')
        else:
            return Commit.objects.none()

    def list(self, request, *args, **kwargs):
        """ActivityLogEntry와 Commit 데이터를 병합하여 반환"""

        # ActivityLogEntry 조회
        logs = self.filter_queryset(self.get_queryset()).values(
            'pk', 'sort', 'project__id', 'project__name', 'project__slug',
            'issue__id', 'issue__tracker__name', 'issue__status__name',
            'issue__status__closed', 'issue__subject', 'issue__description',
            'status_log', 'comment__id', 'comment__content', 'news__title',
            'news__summary', 'news__author', 'spent_time__id',
            'spent_time__hours', 'act_date', 'timestamp', 'user__id', 'user__username')

        # Commit 조회
        commits = self.get_commits().values(
            'repo__id', 'repo__slug', 'repo__project__name',
            'repo__project__slug', 'commit_hash', 'message', 'date', 'author')

        # 데이터 병합 (제너레이터)
        log_iter = ({
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
            'spent_time': {'pk': log['spent_time__id'], 'hours': log['spent_time__hours']},
            'change_set': None,
            'act_date': log['act_date'],
            'timestamp': log['timestamp'],
            'user': {'pk': log['user__id'], 'username': log['user__username']},
        } for log in logs)
        commit_iter = ({
            'pk': 0,
            'sort': '3',
            'project': {'name': c['repo__project__name'], 'slug': c['repo__project__slug']},
            'issue': None,
            'status_log': None,  # c['message'][:30],
            'comment': None,
            'spent_time': None,
            'change_set': {
                'repo': {'pk': c['repo__id'], 'slug': c['repo__slug']},
                'sha': c['commit_hash'],
                'message': c['message'],
            },
            'act_date': c['date'].date(),  # datetime.fromtimestamp(c['date']).date(),
            'timestamp': c['date'],
            'user': {'pk': f"commit:{c['commit_hash'][:8]}", 'username': c['author']},
        } for c in commits)

        combined = list(merge(log_iter, commit_iter, key=lambda x: x['timestamp'], reverse=True))

        # 페이지네이션
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(combined, request)
        return paginator.get_paginated_response(page)


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
