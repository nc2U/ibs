from datetime import datetime

from django.core.cache import cache
from django.db import connection
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
                project_ids = [project.pk] + [p.get('pk') for p in self.get_sub_projects(project)]
                queryset = queryset.filter(project__id__in=project_ids)
            except IssueProject.DoesNotExist:
                return queryset.none()

        # 명시적 필터링
        if cleaned_data.get('from_act_date'):
            queryset = queryset.filter(act_date__gte=cleaned_data['from_act_date'])
        if cleaned_data.get('to_act_date'):
            queryset = queryset.filter(act_date__lte=cleaned_data['to_act_date'])
        if cleaned_data.get('user'):
            queryset = queryset.filter(user=cleaned_data['user'])
        if cleaned_data.get('sort'):
            queryset = self.sort_filter(queryset, 'sort', cleaned_data['sort'])

        return queryset

    @staticmethod
    def sort_filter(queryset, name, value):
        valid_sorts = {'1', '2', '3'}  # 프로젝트별 유효 정렬 값
        sort_values = [v for v in value.split(",") if v in valid_sorts]
        if sort_values:
            queryset = queryset.filter(sort__in=sort_values)
        return queryset

    @staticmethod
    def get_sub_projects(parent):
        """캐싱된 하위 프로젝트 목록 반환"""
        cache_key = f"sub_projects_{parent.slug}"
        sub_projects = cache.get(cache_key)
        if sub_projects is None:
            sub_projects = []
            # CTE로 재귀 쿼리 최적화
            with connection.cursor() as cursor:
                cursor.execute("""
                               WITH RECURSIVE project_tree AS (SELECT id, slug
                                                               FROM work_issueproject
                                                               WHERE id = %s
                                                               UNION
                                                               SELECT p.id, p.slug
                                                               FROM work_issueproject p
                                                                        INNER JOIN project_tree pt ON p.parent_id = pt.id)
                               SELECT id, slug
                               FROM project_tree
                               """, [parent.id])
                sub_projects = [{'pk': row[0], 'slug': row[1]} for row in cursor.fetchall()]
            cache.set(cache_key, sub_projects, timeout=3600)
        return sub_projects


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
                    project_ids = [project.pk] + [p.get('pk') for p in ActivityLogFilter.get_sub_projects(project)]
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
            'pk', 'sort', 'project__id', 'project__name', 'project__slug', 'issue__id',
            'issue__tracker', 'issue__status__name', 'issue__status__closed', 'issue__subject',
            'issue__description', 'status_log', 'comment__id', 'comment__content', 'spent_time__id',
            'spent_time__hours', 'act_date', 'timestamp', 'user__id', 'user__username')

        # Commit 조회
        commits = self.get_commits().values(
            'repo__id', 'repo__slug', 'commit_hash', 'message', 'date', 'author')

        # 데이터 병합 (제너레이터)
        from heapq import merge
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
                'tracker': log['issue__tracker'],
                'status': {'name': log['issue__status__name'], 'closed': log['issue__status__closed']},
                'subject': log['issue__subject'],
                'description': log['issue__description'],
            },
            'status_log': log['status_log'],
            'comment': {
                'pk': log['comment__id'],
                'content': log['comment__content'],
            },
            'spent_time': {'pk': log['spent_time__id'], 'hours': log['spent_time__hours']},
            'change_set': None,
            'act_date': log['act_date'],
            'timestamp': log['timestamp'],
            'user': {'pk': log['user__id'], 'username': log['user__username']},
        } for log in logs)
        commit_iter = ({
            'pk': 0,
            'sort': '3',
            'project': None,
            'issue': None,
            'status_log': None,  # c['message'][:30],
            'comment': None,
            'spent_time': None,
            'change_set': {
                'repo': {'pk': c['repo__id'], 'slug': c['repo__slug']},
                'sha': c['commit_hash'],
                'message': c['message'],
            },
            'act_date': c['date'],  # datetime.fromtimestamp(c['date']).date(),
            'timestamp': c['date'],
            'user': {'pk': 0, 'username': c['author']},
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
