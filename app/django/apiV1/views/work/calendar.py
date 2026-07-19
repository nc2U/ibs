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

        # 프론트엔드에서 전달하는 조회 기간 파라미터 (형식: YYYY-MM-DD)
        start_date_str = request.query_params.get('start')
        end_date_str = request.query_params.get('end')

        is_admin = user.is_superuser or getattr(user, 'work_manager', False)

        # 1. Issue 쿼리셋 필터링
        issue_qs = Issue.objects.filter(project__status='1')
        if project_slug:
            issue_qs = issue_qs.filter(project__slug=project_slug)

        if not is_admin:
            issue_qs = issue_qs.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()

        issue_qs = IssueFilter(request.GET, queryset=issue_qs, request=request).qs

        print("Calendar GET params:", request.GET)
        print("Issue QS count:", issue_qs.count())

        # 기간 필터 적용 (업무의 진행 기간이 조회 기간과 오버랩되는지 판별)
        if start_date_str and end_date_str:
            issue_qs = issue_qs.filter(
                # due_date가 제공되어 범위에 겹치는 경우
                (Q(due_date__gte=start_date_str) & Q(start_date__lte=end_date_str)) |
                # due_date가 없어 시작일만 조회 기간에 속하는 경우
                Q(due_date__isnull=True, start_date__range=[start_date_str, end_date_str])
            )

        issue_data = issue_qs.select_related('project', 'status', 'assigned_to', 'tracker').values(
            'pk', 'subject', 'start_date', 'due_date', 'is_private',
            'project__slug', 'tracker__name', 'assigned_to__username',
            'status__pk', 'status__closed', 'expected_duration'
        )

        # 2. Meeting 쿼리셋 필터링
        meeting_qs = Meeting.objects.all()
        if project_slug:
            meeting_qs = meeting_qs.filter(project__slug=project_slug)

        if not is_admin:
            meeting_qs = meeting_qs.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()

        # 기간 필터 적용 (회의 일시가 조회 기간 내에 위치하는지 판별)
        if start_date_str and end_date_str:
            meeting_qs = meeting_qs.filter(meeting_date__date__range=[start_date_str, end_date_str])

        meeting_data = meeting_qs.select_related('project').values(
            'pk', 'title', 'meeting_date', 'project__slug'
        )

        # 3. 데이터 가공 및 통합
        events = []

        # Issue -> Event
        for issue in issue_data:
            assignee_name = issue['assigned_to__username']
            assignee = f"({assignee_name})" if assignee_name else ""

            events.append({
                'id': str(issue['pk']),
                'type': 'issue',
                'title': f"[{issue['tracker__name']}] {issue['subject']}{assignee}",
                'start': issue['start_date'],
                'end': issue['due_date'],
                'project': issue['project__slug'],
                'status': {
                    'pk': issue['status__pk'],
                    'closed': issue['status__closed']
                },
                'expected_duration': issue['expected_duration']
            })

        # Meeting -> Event
        for meeting in meeting_data:
            events.append({
                'id': f"m-{meeting['pk']}",
                'type': 'meeting',
                'title': f"[회의] {meeting['title']}",
                'start': meeting['meeting_date'].isoformat() if meeting['meeting_date'] else None,
                'project': meeting['project__slug']
            })

        return Response(events)
