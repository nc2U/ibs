from django.db.models import Q
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

    parent__subject = CharFilter(field_name='parent__subject', lookup_expr='icontains', label='상위업무-제목')
    parent__isnull = BooleanFilter(field_name='parent', lookup_expr='isnull', label='상위업무-유무')
    parent_issue = NumberFilter(method='filter_parent_issue', label='상위업무-검색')
    parent = NumberFilter(method='filter_parent', label='하위업무-검색')
    follows_issue = NumberFilter(method='filter_follows', label='선행업무-검색')
    precedes_issue = NumberFilter(method='filter_precedes', label='후속업무-검색')

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
        fields = ('project__slug', 'status__closed', 'status', 'tracker', 'priority', 'category', 'category__exclude', 'category__isnull',
                  'creator', 'assigned_to', 'fixed_version', 'id', 'id__gte', 'id__lte', 'id__between', 'id__any',
                  'done_ratio', 'done_ratio__gte', 'done_ratio__lte', 'done_ratio__between', 'done_ratio__isnull',
                  'parent', 'parent_issue', 'precedes_issue', 'follows_issue', 'project__my_project', 'is_private',
                  'watcher', 'watcher__exclude', 'updater', 'updater__exclude')

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
    def filter_parent_issue(queryset, name, value):
        try:
            parent = Issue.objects.get(pk=value).parent
            return queryset.filter(pk=parent.pk) if parent else queryset.none()
        except Issue.DoesNotExist:
            return queryset.none()

    @staticmethod
    def filter_parent(queryset, name, value):
        return queryset.filter(parent=value)

    @staticmethod
    def filter_precedes(queryset, name, value):
        # 내가 선행하는 업무들 (내가 source이므로, 대상 target_id들을 찾음)
        pks = IssueRelation.objects.filter(source_id=value).values_list('target_id', flat=True)
        return queryset.filter(pk__in=pks)

    @staticmethod
    def filter_follows(queryset, name, value):
        # 내가 후속하는 업무들 (내가 target이므로, 대상 source_id들을 찾음)
        pks = IssueRelation.objects.filter(target_id=value).values_list('source_id', flat=True)
        return queryset.filter(pk__in=pks)

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
                    slugs = [project.slug] + sub_projects_slugs
                    queryset = queryset.filter(project__slug__in=slugs)
                except IssueProject.DoesNotExist:
                    pass
            elif value is not None and name != 'project__slug':
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
            Issue.all_objects.all().select_related(
                'project', 'status', 'creator', 'assigned_to', 'tracker', 'fixed_version'
            )
        )

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
