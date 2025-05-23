from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from work.models.logging import ActivityLogEntry, IssueLogEntry


@admin.register(ActivityLogEntry)
class ActivityLogEntryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'sort', 'issue', 'project', 'spent_time', 'act_date')
    list_display_links = ('issue',)
    list_filter = ('project', 'sort', ('act_date', DateRangeFilter))


@admin.register(IssueLogEntry)
class IssueLogEntryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'action', 'issue', 'comment_id', 'details', 'diff', 'timestamp')
    list_display_links = ('issue',)
    list_filter = ('action',)
