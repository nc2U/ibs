from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django_filters.rest_framework import FilterSet, DateFilter, CharFilter
from rest_framework import viewsets

from apiV1.pagination import PageNumberPaginationThreeHundred, PageNumberPaginationFifty
from apiV1.permissions.auth_perms import permissions
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
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = ActivityLogFilter

    def get_queryset(self):
        """ActivityLogEntry 필터링: 사용자 권한 및 issue_visible 격리 적용"""
        user = self.request.user
        queryset = self.queryset

        # 1. 슈퍼유저/work_manager는 전체 활동 조회
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset.select_related('project', 'creator', 'issue', 'comment', 'meeting', 'news', 'document',
                                           'post')

        # 2. 일반 유저는 본인이 소속되었거나 공개 프로젝트의 활동만 조회 가능
        user_members = Member.objects.filter(user=user).prefetch_related('roles')

        member_all_pids = []
        member_pub_pids = []
        member_pri_pids = []
        member_all_project_ids = []

        for m in user_members:
            member_all_project_ids.append(m.project_id)
            roles = m.roles.all()
            best_issue_visible = 'NOP'
            visibility_order = {'ALL': 3, 'PUB': 2, 'PRI': 1, 'NOP': 0}
            for role in roles:
                if visibility_order.get(role.issue_visible, 0) > visibility_order.get(best_issue_visible, 0):
                    best_issue_visible = role.issue_visible

            if best_issue_visible == 'ALL':
                member_all_pids.append(m.project_id)
            elif best_issue_visible == 'PUB':
                member_pub_pids.append(m.project_id)
            elif best_issue_visible == 'PRI':
                member_pri_pids.append(m.project_id)

        base_filter = Q(project__is_public=True) | Q(project_id__in=member_all_project_ids)

        # 업무 및 의견 로그에 대한 issue_visible 필터 적용
        issue_filter = Q()

        if member_all_pids:
            issue_filter |= Q(project_id__in=member_all_pids)

        if member_pub_pids:
            issue_filter |= Q(
                project_id__in=member_pub_pids,
                issue__isnull=False
            ) & (
                                    Q(issue__is_private=False) |
                                    Q(issue__assigned_to=user) |
                                    Q(issue__creator=user)
                            )

        if member_pri_pids:
            issue_filter |= Q(
                project_id__in=member_pri_pids,
                issue__isnull=False
            ) & (
                                    Q(issue__assigned_to=user) |
                                    Q(issue__creator=user)
                            )

        try:
            non_member_role = Role.objects.get(pk=2)
            non_member_issue_visible = non_member_role.issue_visible
        except Role.DoesNotExist:
            non_member_issue_visible = 'PUB'

        public_pids = IssueProject.objects.filter(is_public=True).exclude(pk__in=member_all_project_ids).values_list(
            'pk', flat=True)
        if public_pids:
            if non_member_issue_visible == 'ALL':
                issue_filter |= Q(project_id__in=public_pids)
            elif non_member_issue_visible == 'PUB':
                issue_filter |= Q(
                    project_id__in=public_pids,
                    issue__isnull=False
                ) & (
                                        Q(issue__is_private=False) |
                                        Q(issue__assigned_to=user) |
                                        Q(issue__creator=user)
                                )
            elif non_member_issue_visible == 'PRI':
                issue_filter |= Q(
                    project_id__in=public_pids,
                    issue__isnull=False
                ) & (
                                        Q(issue__assigned_to=user) |
                                        Q(issue__creator=user)
                                )

        final_qs = queryset.filter(base_filter).filter(
            ~Q(sort__in=['1', '2']) | issue_filter
        )

        return final_qs.select_related('project', 'creator', 'issue', 'comment', 'meeting', 'news', 'document', 'post')


class IssueLogEntryViewSet(viewsets.ModelViewSet):
    queryset = IssueLogEntry.objects.all()
    serializer_class = IssueLogEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('issue', 'creator')

    def get_queryset(self):
        """IssueLogEntry 필터링: 해당 사용자가 접근 권한이 있는 업무의 로그만 조회 가능"""
        user = self.request.user
        queryset = self.queryset.select_related('issue__project', 'comment', 'creator')

        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        user_members = Member.objects.filter(user=user).prefetch_related('roles__permissions')

        member_all_pids = []
        member_pub_pids = []
        member_pri_pids = []
        member_all_project_ids = []
        private_comment_read_pids = []

        for m in user_members:
            member_all_project_ids.append(m.project_id)
            roles = m.roles.all()
            best_issue_visible = 'NOP'
            visibility_order = {'ALL': 3, 'PUB': 2, 'PRI': 1, 'NOP': 0}
            has_private_comment_read = False
            for role in roles:
                if visibility_order.get(role.issue_visible, 0) > visibility_order.get(best_issue_visible, 0):
                    best_issue_visible = role.issue_visible
                for perm in role.permissions.all():
                    if perm.code == 'issue.private_comment_read':
                        has_private_comment_read = True

            if best_issue_visible == 'ALL':
                member_all_pids.append(m.project_id)
            elif best_issue_visible == 'PUB':
                member_pub_pids.append(m.project_id)
            elif best_issue_visible == 'PRI':
                member_pri_pids.append(m.project_id)

            if has_private_comment_read:
                private_comment_read_pids.append(m.project_id)

        allowed_issues_filter = Q()

        if member_all_pids:
            allowed_issues_filter |= Q(issue__project_id__in=member_all_pids)

        if member_pub_pids:
            allowed_issues_filter |= Q(
                issue__project_id__in=member_pub_pids
            ) & (
                                             Q(issue__is_private=False) |
                                             Q(issue__assigned_to=user) |
                                             Q(issue__creator=user)
                                     )

        if member_pri_pids:
            allowed_issues_filter |= Q(
                issue__project_id__in=member_pri_pids
            ) & (
                                             Q(issue__assigned_to=user) |
                                             Q(issue__creator=user)
                                     )

        try:
            non_member_role = Role.objects.get(pk=2)
            non_member_issue_visible = non_member_role.issue_visible
        except Role.DoesNotExist:
            non_member_issue_visible = 'PUB'

        public_pids = IssueProject.objects.filter(is_public=True).exclude(pk__in=member_all_project_ids).values_list(
            'pk', flat=True)
        if public_pids:
            if non_member_issue_visible == 'ALL':
                allowed_issues_filter |= Q(issue__project_id__in=public_pids)
            elif non_member_issue_visible == 'PUB':
                allowed_issues_filter |= Q(
                    issue__project_id__in=public_pids
                ) & (
                                                 Q(issue__is_private=False) |
                                                 Q(issue__assigned_to=user) |
                                                 Q(issue__creator=user)
                                         )
            elif non_member_issue_visible == 'PRI':
                allowed_issues_filter |= Q(
                    issue__project_id__in=public_pids
                ) & (
                                                 Q(issue__assigned_to=user) |
                                                 Q(issue__creator=user)
                                         )

        # 4. 비공개 댓글 열람 가드 조건 빌드 (Method D)
        comment_visibility_filter = (Q(comment__isnull=True)
                                     | Q(comment__is_private=False)
                                     | Q(comment__creator=user))
        if private_comment_read_pids:
            comment_visibility_filter |= Q(issue__project_id__in=private_comment_read_pids)

        return queryset.filter(allowed_issues_filter).filter(comment_visibility_filter)
