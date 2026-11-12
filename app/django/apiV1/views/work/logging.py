from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django_filters.rest_framework import FilterSet, DateFilter, CharFilter
from rest_framework import viewsets

from apiV1.pagination import PageNumberPaginationThreeHundred, PageNumberPaginationFifty
from apiV1.permissions.auth_perms import permissions, IsWorkManagerReadOnly
from apiV1.serializers.work import IssueLogEntrySerializer
from apiV1.serializers.work.logging import ActivityLogEntrySerializer
from work.models.logging import ActivityLogEntry, IssueLogEntry
from work.models.project import IssueProject, Role, Member


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

    @staticmethod
    def filter_by_project_with_sub(queryset, name, value):
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
        valid_sorts = {'1', '2', '3', '4', '5', '6'}
        sort_values = [v for v in value.split(",") if v in valid_sorts]
        if sort_values:
            queryset = queryset.filter(sort__in=sort_values)
        return queryset


class ActivityLogEntryViewSet(viewsets.ModelViewSet):
    queryset = ActivityLogEntry.objects.all()
    serializer_class = ActivityLogEntrySerializer
    permission_classes = (IsWorkManagerReadOnly,)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = ActivityLogFilter

    def get_queryset(self):
        """ActivityLogEntry 필터링: 사용자 권한 및 issue_visible 격리 적용"""
        user = self.request.user
        queryset = self.queryset.exclude(project__status='9')

        # 1. 슈퍼유저/work_manager는 전체 활동 조회
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset.select_related('project', 'creator')

        # 2. 일반 유저는 본인이 소속되었거나 공개 프로젝트의 활동만 조회 가능
        member_all_project_ids = list(
            Member.objects.filter(user=user).values_list('project_id', flat=True)
        )
        base_filter = Q(project__is_public=True) | Q(project_id__in=member_all_project_ids)

        # 3. 업무(sort='1') 및 의견(sort='2') 로그에 대한 비공개/가시성 접근 제한
        from apiV1.views.work.issue import build_issue_queryset
        accessible_issue_ids = build_issue_queryset(user).values_list('pk', flat=True)

        final_qs = queryset.filter(base_filter).filter(
            ~Q(sort__in=['1', '2']) |
            (Q(sort='1') & Q(target_id__in=accessible_issue_ids)) |
            (Q(sort='2') & Q(parent_id__in=accessible_issue_ids))
        )

        return final_qs.select_related('project', 'creator')


class IssueLogEntryViewSet(viewsets.ModelViewSet):
    queryset = IssueLogEntry.objects.order_by('id')
    serializer_class = IssueLogEntrySerializer
    permission_classes = (IsWorkManagerReadOnly,)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('issue', 'creator')

    def get_queryset(self):
        """IssueLogEntry 필터링: 해당 사용자가 접근 권한이 있는 업무의 로그만 조회 가능"""
        user = self.request.user
        queryset = self.queryset.exclude(issue__project__status='9').select_related('issue__project', 'comment', 'creator')

        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        from apiV1.views.work.issue import build_issue_queryset
        accessible_issues = build_issue_queryset(user)

        user_members = Member.objects.filter(user=user).prefetch_related('roles__permissions')
        private_comment_read_pids = [
            m.project_id
            for m in user_members
            if any(
                perm.code == 'issue.private_comment_read'
                for role in m.roles.all()
                for perm in role.permissions.all()
            )
        ]

        # 비공개 댓글 열람 가드 조건 빌드 (Method D)
        comment_visibility_filter = (Q(comment__isnull=True)
                                     | Q(comment__is_private=False)
                                     | Q(comment__creator=user))
        if private_comment_read_pids:
            comment_visibility_filter |= Q(issue__project_id__in=private_comment_read_pids)

        return queryset.filter(issue__in=accessible_issues).filter(comment_visibility_filter).distinct()
