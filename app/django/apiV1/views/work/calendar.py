from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.response import Response

from apiV1.permissions.work_perms import ProjectPermission
from apiV1.views.work.issue import IssueFilter
from work.models.issue import Issue
from work.models.meeting import Meeting


class CalendarViewSet(viewsets.ViewSet):
    """
    캘린더 화면 전용 통합 이벤트 API ViewSet
    `calendar.read` 권한이 적용되며, start/end 날짜 파라미터를 받아 기간 내의 Issue와 Meeting 데이터를 조회 및 가공합니다.
    """
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)

    @property
    def required_permission(self):
        return 'calendar.read'

    def list(self, request):
        user = self.request.user
        project_slug = request.query_params.get('project')

        # 조회 기간 파라미터 (형식: YYYY-MM-DD)
        start_date_str = request.query_params.get('start')
        end_date_str = request.query_params.get('end')

        # 이벤트 종류 파라미터: 'all' | 'issue' | 'meeting' (기본값: 'all')
        event_type = request.query_params.get('event_type', 'all')

        is_admin = user.is_superuser or getattr(user, 'work_manager', False)

        events = []

        # ── 1. Issue 쿼리셋 ────────────────────────────────────────────────
        if event_type in ('all', 'issue'):
            issue_qs = Issue.objects.filter(project__status='1')
            if project_slug:
                issue_qs = issue_qs.filter(project__slug=project_slug)

            if not is_admin:
                issue_qs = issue_qs.filter(
                    Q(project__is_public=True) | Q(project__members__user=user)
                ).distinct()

            # IssueFilter로 업무 전용 검색조건 적용 (status, tracker, priority, assignee, subject 등)
            issue_qs = IssueFilter(request.GET, queryset=issue_qs, request=request).qs

            # FullCalendar 조회 기간과 겹치는 업무 필터
            if start_date_str and end_date_str:
                issue_qs = issue_qs.filter(
                    (Q(due_date__gte=start_date_str) & Q(start_date__lte=end_date_str)) |
                    Q(due_date__isnull=True, start_date__range=[start_date_str, end_date_str])
                )

            issue_data = issue_qs.select_related(
                'project', 'status', 'assigned_to', 'tracker'
            ).values(
                'pk', 'subject', 'start_date', 'due_date', 'is_private',
                'project__slug', 'tracker__name', 'assigned_to__username',
                'status__pk', 'status__closed', 'expected_duration',
            )

            for issue in issue_data:
                assignee_name = issue['assigned_to__username']
                assignee = f" ({assignee_name})" if assignee_name else ""
                events.append({
                    'id': str(issue['pk']),
                    'type': 'issue',
                    'title': f"[{issue['tracker__name']}] {issue['subject']}{assignee}",
                    'start': issue['start_date'],
                    'end': issue['due_date'],
                    'project': issue['project__slug'],
                    'status': {
                        'pk': issue['status__pk'],
                        'closed': issue['status__closed'],
                    },
                    'expected_duration': issue['expected_duration'],
                })

        # ── 2. Meeting 쿼리셋 ──────────────────────────────────────────────
        if event_type in ('all', 'meeting'):
            meeting_qs = Meeting.objects.all()
            if project_slug:
                meeting_qs = meeting_qs.filter(project__slug=project_slug)

            if not is_admin:
                meeting_qs = meeting_qs.filter(
                    Q(project__is_public=True) | Q(project__members__user=user)
                ).distinct()

            # 회의 전용 검색조건
            meeting_status = request.query_params.get('meeting_status')
            meeting_status__exclude = request.query_params.get('meeting_status__exclude')
            meeting_category = request.query_params.get('meeting_category')
            meeting_category__exclude = request.query_params.get('meeting_category__exclude')
            meeting_attendees = request.query_params.get('meeting_attendees')
            meeting_attendees__exclude = request.query_params.get('meeting_attendees__exclude')
            meeting_creator = request.query_params.get('meeting_creator')
            meeting_creator__exclude = request.query_params.get('meeting_creator__exclude')
            meeting_search = request.query_params.get('meeting_search')
            meeting_search__exclude = request.query_params.get('meeting_search__exclude')
            meeting_date__gte = request.query_params.get('meeting_date__gte')
            meeting_date__lte = request.query_params.get('meeting_date__lte')
            meeting_date_exact = request.query_params.get('meeting_date')

            if meeting_status:
                meeting_qs = meeting_qs.filter(status=meeting_status)
            if meeting_status__exclude:
                meeting_qs = meeting_qs.exclude(status=meeting_status__exclude)
            if meeting_category:
                meeting_qs = meeting_qs.filter(category=meeting_category)
            if meeting_category__exclude:
                meeting_qs = meeting_qs.exclude(category=meeting_category__exclude)
            if meeting_attendees:
                meeting_qs = meeting_qs.filter(attendees=meeting_attendees)
            if meeting_attendees__exclude:
                meeting_qs = meeting_qs.exclude(attendees=meeting_attendees__exclude)
            if meeting_creator:
                meeting_qs = meeting_qs.filter(creator=meeting_creator)
            if meeting_creator__exclude:
                meeting_qs = meeting_qs.exclude(creator=meeting_creator__exclude)
            if meeting_search:
                meeting_qs = meeting_qs.filter(
                    Q(title__icontains=meeting_search) |
                    Q(agenda__icontains=meeting_search) |
                    Q(decisions__icontains=meeting_search)
                )
            if meeting_search__exclude:
                meeting_qs = meeting_qs.exclude(
                    Q(title__icontains=meeting_search__exclude) |
                    Q(agenda__icontains=meeting_search__exclude) |
                    Q(decisions__icontains=meeting_search__exclude)
                )
            if meeting_date_exact:
                meeting_qs = meeting_qs.filter(meeting_date__date=meeting_date_exact)
            if meeting_date__gte:
                meeting_qs = meeting_qs.filter(meeting_date__date__gte=meeting_date__gte)
            if meeting_date__lte:
                meeting_qs = meeting_qs.filter(meeting_date__date__lte=meeting_date__lte)

            # FullCalendar 조회 기간 필터
            if start_date_str and end_date_str:
                meeting_qs = meeting_qs.filter(
                    meeting_date__date__range=[start_date_str, end_date_str]
                )

            meeting_data = meeting_qs.select_related('project').values(
                'pk', 'title', 'meeting_date', 'project__slug'
            )

            for meeting in meeting_data:
                events.append({
                    'id': f"m-{meeting['pk']}",
                    'type': 'meeting',
                    'title': f"[회의] {meeting['title']}",
                    'start': meeting['meeting_date'].isoformat() if meeting['meeting_date'] else None,
                    'project': meeting['project__slug'],
                })

        return Response(events)
