from django.db.models import Q
from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from work.models import ActivityLogEntry, IssueLogEntry


@admin.register(ActivityLogEntry)
class ActivityLogEntryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'sort', 'title', 'project', 'act_date')
    list_display_links = ('title',)
    list_select_related = ('project', 'creator')
    list_filter = ('project', 'sort', ('act_date', DateRangeFilter))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        from apiV1.views.work.issue import build_issue_queryset, build_issue_comment_queryset
        from work.models.issue import IssueComment
        accessible_issue_ids = build_issue_queryset(user).values_list('pk', flat=True)
        hidden_private_comment_ids = IssueComment.objects.filter(
            is_private=True
        ).exclude(
            pk__in=build_issue_comment_queryset(user)
        ).values_list('pk', flat=True)
        return qs.filter(
            Q(project__is_public=True) | Q(project__members__user=user)
        ).filter(
            ~Q(sort__in=['1', '2']) |
            (Q(sort='1') & Q(target_id__in=accessible_issue_ids)) |
            (Q(sort='2') & Q(parent_id__in=accessible_issue_ids) & ~Q(target_id__in=hidden_private_comment_ids))
        ).distinct()


@admin.register(IssueLogEntry)
class IssueLogEntryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'action', 'issue', 'comment_id', 'details', 'diff', 'timestamp')
    list_display_links = ('issue',)
    list_select_related = ('issue', 'comment', 'creator')
    list_filter = ('action',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        from apiV1.views.work.issue import build_issue_queryset, build_issue_comment_queryset
        accessible_issues = build_issue_queryset(user)
        accessible_comments = build_issue_comment_queryset(user)
        return qs.filter(
            issue__in=accessible_issues
        ).filter(
            Q(comment__isnull=True) | Q(comment__in=accessible_comments)
        ).distinct()
