from django.db.models import Q, F
from django_filters.rest_framework import FilterSet, BooleanFilter, CharFilter, NumberFilter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apiV1.pagination import PageNumberPaginationTwenty
from apiV1.permissions.auth_perms import permissions
from apiV1.permissions.work_perms import ProjectPermission, IssuePermission, IssueCommentPermission, \
    IssueRelationPermission
from apiV1.serializers.work import (IssueCountByMemberSerializer, IssueRelationSerializer, IssueFileSerializer,
                                    IssueCommentSerializer, TrackerSerializer, IssueCategorySerializer,
                                    IssueCountByTrackerSerializer, IssueStatusSerializer, WorkflowSerializer,
                                    CodeIssuePrioritySerializer)
from apiV1.serializers.work.issue import IssueSerializer
from work.models import Issue, IssueRelation, IssueProject, IssueFile, IssueComment, Tracker, \
    IssueCategory, IssueStatus, Workflow, CodeIssuePriority
from work.models.project import Member, Role
from work.models.logging import IssueLogEntry


class IssueFilter(FilterSet):
    status__exclude = CharFilter(field_name='status', exclude=True, label='사용여부-제외')
    project__exclude = CharFilter(field_name='project__slug', exclude=True, label='프로젝트-제외')
    project__search = CharFilter(field_name='project__slug', label='프로젝트-검색')
    sub_project = NumberFilter(method='dummy_filter', label='하위프로젝트-일치')
    sub_project__exclude = NumberFilter(method='dummy_filter', label='하위프로젝트-제외')
    sub_project__isnull = CharFilter(method='dummy_filter', label='하위프로젝트-유무')
    tracker__exclude = CharFilter(field_name='tracker', exclude=True, label='유형-제외')
    priority__exclude = CharFilter(field_name='priority', exclude=True, label='우선순위-제외')
    category__exclude = CharFilter(field_name='category', exclude=True, label='범주-제외')
    category__isnull = BooleanFilter(field_name='category', lookup_expr='isnull', label='범주-유무')
    watcher = NumberFilter(field_name='watchers', lookup_expr='exact', label='업무관람자-일치')
    watcher__exclude = NumberFilter(field_name='watchers', exclude=True, label='업무관람자-제외')
    creator__exclude = CharFilter(field_name='creator', exclude=True, label='작성자-제외')
    assigned_to__exclude = CharFilter(field_name='assigned_to', exclude=True, label='담당자-제외')
    assigned_to__isnull = BooleanFilter(field_name='assigned_to', lookup_expr='isnull', label='담당자-유무')
    fixed_version__exclude = CharFilter(field_name='fixed_version', exclude=True, label='목표단계-제외')
    fixed_version__isnull = BooleanFilter(field_name='fixed_version', lookup_expr='isnull', label='목표단계-유무')
    updater = NumberFilter(method='filter_updater', label='수정자')
    updater__exclude = NumberFilter(method='filter_updater_exclude', label='수정자-제외')
    last_updater = NumberFilter(field_name='updater', lookup_expr='exact', label='최근수정자-일치')
    last_updater__exclude = NumberFilter(field_name='updater', exclude=True, label='최근수정자-제외')
    subject = CharFilter(field_name='subject', lookup_expr='icontains', label='제목')
    subject__exclude = CharFilter(field_name='subject', lookup_expr='icontains', exclude=True, label='제목-제외')
    description = CharFilter(field_name='description', lookup_expr='icontains', label='설명')
    description__exclude = CharFilter(field_name='description', lookup_expr='icontains', exclude=True, label='설명-제외')
    comment = CharFilter(field_name='comments__content', lookup_expr='icontains', label='댓글')
    comment__exclude = CharFilter(field_name='comments__content', lookup_expr='icontains', exclude=True, label='댓글-제외')
    any_searchable = CharFilter(method='filter_any_searchable', label='전체내용-검색')
    any_searchable__exclude = CharFilter(method='filter_any_searchable_exclude', label='전체내용-제외')
    file = CharFilter(field_name='files__file_name', lookup_expr='icontains', label='파일명')
    file__exclude = CharFilter(field_name='files__file_name', lookup_expr='icontains', exclude=True, label='파일명-제외')
    file_desc = CharFilter(field_name='files__description', lookup_expr='icontains', label='파일설명')
    file_desc__exclude = CharFilter(field_name='files__description', lookup_expr='icontains', exclude=True,
                                    label='파일설명-제외')
    creator_role = CharFilter(method='filter_creator_role', label='등록자역할')
    creator_role__exclude = CharFilter(method='filter_creator_role_exclude', label='등록자역할-제외')
    assignee_role = CharFilter(method='filter_assignee_role', label='담당자역할')
    assignee_role__exclude = CharFilter(method='filter_assignee_role_exclude', label='담당자역할-제외')

    version_date = CharFilter(method='filter_version_date', label='목표단계완료일자-일치')
    version_date__gte = CharFilter(method='filter_version_date_gte', label='목표단계완료일자-이후')
    version_date__lte = CharFilter(method='filter_version_date_lte', label='목표단계완료일자-이전')
    version_date__between = CharFilter(method='filter_version_date_between', label='목표단계완료일자-범위')
    version_date__isnull = BooleanFilter(field_name='fixed_version__effective_date', lookup_expr='isnull',
                                         label='목표단계완료일자-유무')

    version_status = CharFilter(field_name='fixed_version__status', lookup_expr='exact', label='목표단계상태-일치')
    version_status__exclude = CharFilter(field_name='fixed_version__status', exclude=True, label='목표단계상태-제외')

    project_status = CharFilter(field_name='project__status', lookup_expr='exact', label='프로젝트상태-일치')
    project_status__exclude = CharFilter(field_name='project__status', exclude=True, label='프로젝트상태-제외')

    created = CharFilter(method='filter_created_date', label='등록일-일치')
    created__gte = CharFilter(method='filter_created_gte', label='등록일-이후')
    created__lte = CharFilter(method='filter_created_lte', label='등록일-이전')
    created__between = CharFilter(method='filter_created_between', label='등록일-범위')

    updated = CharFilter(method='filter_updated_date', label='변경일-일치')
    updated__gte = CharFilter(method='filter_updated_gte', label='변경일-이후')
    updated__lte = CharFilter(method='filter_updated_lte', label='변경일-이전')
    updated__between = CharFilter(method='filter_updated_between', label='변경일-범위')

    start_date = CharFilter(method='filter_start_date', label='시작일자-일치')
    start_date__gte = CharFilter(method='filter_start_date_gte', label='시작일자-이후')
    start_date__lte = CharFilter(method='filter_start_date_lte', label='시작일자-이전')
    start_date__between = CharFilter(method='filter_start_date_between', label='시작일자-범위')

    due_date = CharFilter(method='filter_due_date', label='완료기한-일치')
    due_date__gte = CharFilter(method='filter_due_date_gte', label='완료기한-이후')
    due_date__lte = CharFilter(method='filter_due_date_lte', label='완료기한-이전')
    due_date__between = CharFilter(method='filter_due_date_between', label='완료기한-범위')
    due_date__isnull = BooleanFilter(field_name='due_date', lookup_expr='isnull', label='완료기한-유무')

    id = NumberFilter(field_name='id', lookup_expr='exact', label='ID-일치')
    id__gte = NumberFilter(field_name='id', lookup_expr='gte', label='ID-이상')
    id__lte = NumberFilter(field_name='id', lookup_expr='lte', label='ID-이하')
    id__between = CharFilter(method='filter_id_between', label='ID-범위 (예: 10,20)')
    id__any = CharFilter(method='filter_id_any', label='ID-모두보기')

    done_ratio = NumberFilter(field_name='done_ratio', lookup_expr='exact', label='진척도-일치')
    done_ratio__gte = NumberFilter(field_name='done_ratio', lookup_expr='gte', label='진척도-이상')
    done_ratio__lte = NumberFilter(field_name='done_ratio', lookup_expr='lte', label='진척도-이하')
    done_ratio__between = CharFilter(method='filter_done_ratio_between', label='진척도-범위 (예: 10,20)')
    done_ratio__isnull = BooleanFilter(field_name='done_ratio', lookup_expr='isnull', label='진척도-유무')

    parent_issue = NumberFilter(field_name='parent', lookup_expr='exact', label='상위업무-일치')
    parent_issue__exclude = NumberFilter(field_name='parent', exclude=True, label='상위업무-제외')
    parent_issue__contains = CharFilter(field_name='parent__subject', lookup_expr='icontains', label='상위업무-제목포함')
    parent_issue__isnull = BooleanFilter(field_name='parent', lookup_expr='isnull', label='상위업무-유무')

    parent = NumberFilter(method='filter_sub_issue', label='하위업무-일치')
    parent__exclude = NumberFilter(method='filter_sub_issue_exclude', label='하위업무-제외')
    parent__contains = CharFilter(field_name='issue_set__subject', lookup_expr='icontains', label='하위업무-제목포함')
    parent__isnull = BooleanFilter(field_name='issue_set', lookup_expr='isnull', label='하위업무-유무')
    follows_issue = NumberFilter(method='filter_follows', label='선행업무-검색')
    follows_issue__exclude = NumberFilter(method='filter_follows_exclude', label='선행업무-제외')
    follows_issue__isnull = BooleanFilter(field_name='incoming_relation', lookup_expr='isnull', label='선행업무-유무')
    precedes_issue = NumberFilter(method='filter_precedes', label='후속업무-검색')
    precedes_issue__exclude = NumberFilter(method='filter_precedes_exclude', label='후속업무-제외')
    precedes_issue__isnull = BooleanFilter(field_name='outgoing_relations', lookup_expr='isnull', label='후속업무-유무')

    project__my_project = BooleanFilter(method='filter_my_project', label='내 프로젝트 업무 여부')

    def filter_my_project(self, queryset, name, value):
        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            if user.is_superuser or getattr(user, 'work_manager', False):
                return queryset
            if value:
                return queryset.filter(project__members__user=user)
            else:
                return queryset.exclude(project__members__user=user)
        return queryset

    class Meta:
        model = Issue
        fields = ('project__slug', 'sub_project', 'sub_project__exclude', 'sub_project__isnull', 'status__closed',
                  'status', 'tracker', 'priority', 'category', 'category__exclude', 'category__isnull',
                  'creator', 'assigned_to', 'fixed_version', 'id', 'id__gte', 'id__lte', 'id__between', 'id__any',
                  'done_ratio', 'done_ratio__gte', 'done_ratio__lte', 'done_ratio__between', 'done_ratio__isnull',
                  'parent', 'parent__exclude', 'parent__contains', 'parent__isnull',
                  'parent_issue', 'parent_issue__exclude', 'parent_issue__contains', 'parent_issue__isnull',
                  'precedes_issue', 'precedes_issue__exclude', 'precedes_issue__isnull', 'follows_issue',
                  'follows_issue__exclude', 'follows_issue__isnull', 'project__my_project', 'is_private',
                  'watcher', 'watcher__exclude', 'updater', 'updater__exclude', 'last_updater', 'last_updater__exclude',
                  'subject', 'subject__exclude', 'description', 'description__exclude', 'comment', 'comment__exclude',
                  'any_searchable', 'any_searchable__exclude',
                  'file', 'file__exclude', 'file_desc', 'file_desc__exclude',
                  'creator_role', 'creator_role__exclude', 'assignee_role', 'assignee_role__exclude',
                  'version_date', 'version_date__gte', 'version_date__lte', 'version_date__between',
                  'version_date__isnull',
                  'version_status', 'version_status__exclude',
                  'project_status', 'project_status__exclude',
                  'created', 'created__gte', 'created__lte', 'created__between',
                  'updated', 'updated__gte', 'updated__lte', 'updated__between',
                  'start_date', 'start_date__gte', 'start_date__lte', 'start_date__between',
                  'due_date', 'due_date__gte', 'due_date__lte', 'due_date__between', 'due_date__isnull')

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
    def filter_done_ratio_between(queryset, name, value):
        try:
            start, end = map(int, value.split(','))
            return queryset.filter(done_ratio__range=(start, end))
        except (ValueError, AttributeError):
            return queryset
        return queryset

    @staticmethod
    def filter_sub_issue(queryset, name, value):
        return queryset.filter(issue_set=value).distinct()

    @staticmethod
    def filter_sub_issue_exclude(queryset, name, value):
        return queryset.exclude(issue_set=value).distinct()

    @staticmethod
    def filter_precedes(queryset, name, value):
        # 내가 선행하는 업무들 (내가 source이므로, 대상 target_id들을 찾음)
        pks = IssueRelation.objects.filter(source_id=value).values_list('target_id', flat=True)
        return queryset.filter(pk__in=pks)

    @staticmethod
    def filter_precedes_exclude(queryset, name, value):
        pks = IssueRelation.objects.filter(source_id=value).values_list('target_id', flat=True)
        return queryset.exclude(pk__in=pks)

    @staticmethod
    def filter_follows(queryset, name, value):
        # 내가 후속하는 업무들 (내가 target이므로, 대상 source_id들을 찾음)
        pks = IssueRelation.objects.filter(target_id=value).values_list('source_id', flat=True)
        return queryset.filter(pk__in=pks)

    @staticmethod
    def filter_follows_exclude(queryset, name, value):
        pks = IssueRelation.objects.filter(target_id=value).values_list('source_id', flat=True)
        return queryset.exclude(pk__in=pks)

    @staticmethod
    def filter_updater(queryset, name, value):
        if value:
            # 수정(Updated) 혹은 댓글(Comment)을 작성한 사람
            pks = IssueLogEntry.objects.filter(
                creator_id=value,
                action__in=['Updated', 'Comment']
            ).values_list('issue_id', flat=True)
            return queryset.filter(pk__in=pks)
        return queryset

    @staticmethod
    def filter_updater_exclude(queryset, name, value):
        if value:
            pks = IssueLogEntry.objects.filter(
                creator_id=value,
                action__in=['Updated', 'Comment']
            ).values_list('issue_id', flat=True)
            return queryset.exclude(pk__in=pks)
        return queryset

    @staticmethod
    def filter_any_searchable(queryset, name, value):
        if value:
            return queryset.filter(
                Q(subject__icontains=value) |
                Q(description__icontains=value) |
                Q(comments__content__icontains=value)
            ).distinct()
        return queryset

    @staticmethod
    def filter_any_searchable_exclude(queryset, name, value):
        if value:
            return queryset.exclude(
                Q(subject__icontains=value) |
                Q(description__icontains=value) |
                Q(comments__content__icontains=value)
            ).distinct()
        return queryset

    @staticmethod
    def filter_created_date(queryset, name, value):
        return queryset.filter(created__date=value)

    @staticmethod
    def filter_created_gte(queryset, name, value):
        return queryset.filter(created__date__gte=value)

    @staticmethod
    def filter_created_lte(queryset, name, value):
        return queryset.filter(created__date__lte=value)

    @staticmethod
    def filter_created_between(queryset, name, value):
        try:
            start, end = value.split(',')
            q = queryset
            if start:
                q = q.filter(created__date__gte=start)
            if end:
                q = q.filter(created__date__lte=end)
            return q
        except ValueError:
            return queryset

    @staticmethod
    def filter_updated_date(queryset, name, value):
        return queryset.filter(updated__date=value)

    @staticmethod
    def filter_updated_gte(queryset, name, value):
        return queryset.filter(updated__date__gte=value)

    @staticmethod
    def filter_updated_lte(queryset, name, value):
        return queryset.filter(updated__date__lte=value)

    @staticmethod
    def filter_updated_between(queryset, name, value):
        try:
            start, end = value.split(',')
            q = queryset
            if start:
                q = q.filter(updated__date__gte=start)
            if end:
                q = q.filter(updated__date__lte=end)
            return q
        except ValueError:
            return queryset

    @staticmethod
    def filter_start_date(queryset, name, value):
        return queryset.filter(start_date=value)

    @staticmethod
    def filter_start_date_gte(queryset, name, value):
        return queryset.filter(start_date__gte=value)

    @staticmethod
    def filter_start_date_lte(queryset, name, value):
        return queryset.filter(start_date__lte=value)

    @staticmethod
    def filter_start_date_between(queryset, name, value):
        try:
            start, end = value.split(',')
            q = queryset
            if start:
                q = q.filter(start_date__gte=start)
            if end:
                q = q.filter(start_date__lte=end)
            return q
        except ValueError:
            return queryset

    @staticmethod
    def filter_due_date(queryset, name, value):
        return queryset.filter(due_date=value)

    @staticmethod
    def filter_due_date_gte(queryset, name, value):
        return queryset.filter(due_date__gte=value)

    @staticmethod
    def filter_due_date_lte(queryset, name, value):
        return queryset.filter(due_date__lte=value)

    @staticmethod
    def filter_due_date_between(queryset, name, value):
        try:
            start, end = value.split(',')
            q = queryset
            if start:
                q = q.filter(due_date__gte=start)
            if end:
                q = q.filter(due_date__lte=end)
            return q
        except ValueError:
            return queryset

    @staticmethod
    def filter_creator_role(queryset, name, value):
        if value:
            return queryset.filter(
                project__members__user=F('creator'),
                project__members__roles=value
            ).distinct()
        return queryset

    @staticmethod
    def filter_creator_role_exclude(queryset, name, value):
        if value:
            matching_ids = queryset.filter(
                project__members__user=F('creator'),
                project__members__roles=value
            ).values_list('id', flat=True)
            return queryset.exclude(id__in=matching_ids)
        return queryset

    @staticmethod
    def filter_assignee_role(queryset, name, value):
        if value:
            return queryset.filter(
                project__members__user=F('assigned_to'),
                project__members__roles=value
            ).distinct()
        return queryset

    @staticmethod
    def filter_assignee_role_exclude(queryset, name, value):
        if value:
            matching_ids = queryset.filter(
                project__members__user=F('assigned_to'),
                project__members__roles=value
            ).values_list('id', flat=True)
            return queryset.exclude(id__in=matching_ids)
        return queryset

    @staticmethod
    def filter_version_date(queryset, name, value):
        return queryset.filter(fixed_version__effective_date=value)

    @staticmethod
    def filter_version_date_gte(queryset, name, value):
        return queryset.filter(fixed_version__effective_date__gte=value)

    @staticmethod
    def filter_version_date_lte(queryset, name, value):
        return queryset.filter(fixed_version__effective_date__lte=value)

    @staticmethod
    def filter_version_date_between(queryset, name, value):
        try:
            start, end = value.split(',')
            q = queryset
            if start:
                q = q.filter(fixed_version__effective_date__gte=start)
            if end:
                q = q.filter(fixed_version__effective_date__lte=end)
            return q
        except ValueError:
            return queryset

    @staticmethod
    def dummy_filter(queryset, name, value):
        return queryset

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

                    sub_project_val = self.form.cleaned_data.get('sub_project')
                    sub_project_exclude_val = self.form.cleaned_data.get('sub_project__exclude')
                    sub_project_isnull_val = self.form.cleaned_data.get('sub_project__isnull')

                    if sub_project_isnull_val == '1':  # 없음 (Only main project)
                        queryset = queryset.filter(project__slug=project.slug)
                    elif sub_project_val:  # 이다 (Specific sub-project)
                        queryset = queryset.filter(project_id=sub_project_val)
                    elif sub_project_exclude_val:  # 아니다 (Exclude specific sub-project)
                        queryset = queryset.filter(project__slug__in=[project.slug] + sub_projects_slugs).exclude(
                            project_id=sub_project_exclude_val)
                    else:  # 모두 (Default)
                        slugs = [project.slug] + sub_projects_slugs
                        queryset = queryset.filter(project__slug__in=slugs)
                except IssueProject.DoesNotExist:
                    pass
            elif value is not None and name not in ['project__slug', 'sub_project', 'sub_project__exclude',
                                                    'sub_project__isnull']:
                queryset = self.filters[name].filter(queryset, value)

        return queryset


def build_issue_queryset(user, base_qs=None):
    """
    사용자 권한에 따른 Issue 쿼리셋을 반환하는 공용 빌더.
    IssueViewSet.get_queryset() 및 SearchViewSet 검색에서 공통 사용.
    """
    if base_qs is None:
        base_qs = Issue.all_objects.all().select_related(
            'project', 'status', 'creator', 'assigned_to', 'tracker', 'fixed_version'
        )

    if getattr(user, 'work_manager', False) or user.is_superuser:
        return base_qs

    user_members = Member.objects.filter(user=user).prefetch_related('roles__permissions')
    member_all_pids, member_pub_pids, private_pids = [], [], []
    issue_visibility_order = {'ALL': 3, 'PUB': 2, 'PRI': 1, 'NOP': 0}

    for member in user_members:
        best_visible, has_private_perm = 'NOP', False
        for role in member.roles.all():
            if issue_visibility_order.get(role.issue_visible, 0) > issue_visibility_order.get(best_visible, 0):
                best_visible = role.issue_visible
            for perm in role.permissions.all():
                if perm.code == 'issue.private':
                    has_private_perm = True
        if best_visible == 'ALL':
            member_all_pids.append(member.project_id)
        elif best_visible == 'PUB':
            member_pub_pids.append(member.project_id)
        if has_private_perm:
            private_pids.append(member.project_id)

    try:
        non_member_visible = Role.objects.get(pk=2).issue_visible
    except Role.DoesNotExist:
        non_member_visible = 'NOP'

    q_expr = Q(creator=user) | Q(assigned_to=user)
    if member_all_pids:
        q_expr |= Q(project_id__in=member_all_pids)
    if member_pub_pids:
        q_expr |= Q(project_id__in=member_pub_pids, is_private=False)
    if private_pids:
        q_expr |= Q(project_id__in=private_pids)
    if non_member_visible == 'ALL':
        q_expr |= Q(project__is_public=True)
    elif non_member_visible == 'PUB':
        q_expr |= Q(project__is_public=True, is_private=False)

    return base_qs.filter(q_expr).distinct()


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
            'toggle_private': 'issue.private',
            'toggle_watch': 'issue.read',
        }
        return mapping.get(self.action, None)

    @action(detail=True, methods=['post'])
    def toggle_private(self, request, pk=None):
        issue = self.get_object()
        issue.is_private = not issue.is_private
        issue.save()
        return Response({'is_private': issue.is_private})

    @action(detail=True, methods=['post'])
    def toggle_watch(self, request, pk=None):
        issue = self.get_object()
        user = request.user

        if issue.watchers.filter(pk=user.pk).exists():
            issue.watchers.remove(user)
        else:
            issue.watchers.add(user)

        serializer = self.get_serializer(issue)
        return Response(serializer.data)

    def get_queryset(self):
        return build_issue_queryset(
            self.request.user,
            Issue.objects.all().select_related(
                'project', 'status', 'creator', 'assigned_to', 'tracker', 'fixed_version'
            )
        )

    def filter_queryset(self, queryset):
        if self.request and self.request.user and self.request.user.is_authenticated:
            user_pk = str(self.request.user.pk)
            q_params_mutable = self.request.query_params._mutable
            self.request.query_params._mutable = True
            for key in ['watcher', 'watcher__exclude', 'creator', 'creator__exclude', 'assigned_to',
                        'assigned_to__exclude', 'updater', 'updater__exclude', 'last_updater', 'last_updater__exclude']:
                val = self.request.query_params.get(key)
                if val == 'me':
                    self.request.query_params[key] = user_pk
            self.request.query_params._mutable = q_params_mutable
        return super().filter_queryset(queryset)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updater=self.request.user)


class IssueCountByMemberView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request, *args, **kwargs):
        user_param = request.query_params.get('user', None)
        user = user_param if user_param else request.user

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
    permission_classes = (permissions.IsAuthenticated, IssueRelationPermission)
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
    permission_classes = (permissions.IsAuthenticated, IssuePermission)
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
    permission_classes = (permissions.IsAuthenticated, IssueCommentPermission)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    @property
    def required_permission(self):
        mapping = {
            'list': 'issue.read',
            'retrieve': 'issue.read',
            'create': 'issue.comment_create',
            'update': 'issue.comment_update',
            'partial_update': 'issue.comment_update',
            'destroy': 'issue.comment_delete'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = IssueComment.objects.all().select_related('issue')

        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        # 1. 사용자의 멤버 프로젝트들을 가져와 권한 수준에 따라 분류
        from work.models.project import Member
        user_members = Member.objects.filter(user=user).prefetch_related('roles__permissions')

        member_all_pids = []
        member_pub_pids = []
        private_comment_read_pids = []

        issue_visibility_order = {'ALL': 3, 'PUB': 2, 'PRI': 1, 'NOP': 0}

        for member in user_members:
            # (A) issue_visible 수준 판별
            best_visible = 'NOP'
            has_private_read = False

            for role in member.roles.all():
                if issue_visibility_order.get(role.issue_visible, 0) > issue_visibility_order.get(best_visible, 0):
                    best_visible = role.issue_visible

                for perm in role.permissions.all():
                    if perm.code == 'issue.private_comment_read':
                        has_private_read = True

            if best_visible == 'ALL':
                member_all_pids.append(member.project_id)
            elif best_visible == 'PUB':
                member_pub_pids.append(member.project_id)

            if has_private_read:
                private_comment_read_pids.append(member.project_id)

        # 2. 비회원 역할(pk=2) 정보 가져오기
        from work.models.project import Role
        try:
            non_member_role = Role.objects.prefetch_related('permissions').get(pk=2)
            non_member_visible = non_member_role.issue_visible
            non_member_private_read = any(
                perm.code == 'issue.private_comment_read' for perm in non_member_role.permissions.all())
        except Role.DoesNotExist:
            non_member_visible = 'NOP'
            non_member_private_read = False

        # 3. 부모 업무(Issue) 가시성에 따른 필터 조건 (issue_q)
        issue_q = Q(issue__creator=user) | Q(issue__assigned_to=user)

        if member_all_pids:
            issue_q |= Q(issue__project_id__in=member_all_pids)
        if member_pub_pids:
            issue_q |= Q(issue__project_id__in=member_pub_pids, issue__is_private=False)

        if non_member_visible == 'ALL':
            issue_q |= Q(issue__project__is_public=True)
        elif non_member_visible == 'PUB':
            issue_q |= Q(issue__project__is_public=True, issue__is_private=False)

        # 4. 비공개 댓글 가시성에 따른 필터 조건 (comment_q)
        comment_q = Q(is_private=False) | Q(creator=user)

        if private_comment_read_pids:
            comment_q |= Q(issue__project_id__in=private_comment_read_pids)
        if non_member_private_read:
            comment_q |= Q(issue__project__is_public=True)

        return queryset.filter(issue_q & comment_q).distinct()

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

    @property
    def required_permission(self):
        mapping = {
            'list': 'issue.read',
            'retrieve': 'issue.read',
            'create': 'issue.category_manage',
            'update': 'issue.category_manage',
            'partial_update': 'issue.category_manage',
            'destroy': 'issue.category_manage'
        }
        return mapping.get(self.action, None)


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
