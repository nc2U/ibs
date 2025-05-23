from django.contrib import admin
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from work.models import (Issue, IssueRelation, IssueFile, IssueComment,
                         TimeEntry, Tracker, IssueCategory, IssueStatus,
                         Workflow, CodeActivity, CodeIssuePriority)


class IssueFileInline(admin.TabularInline):
    model = IssueFile
    extra = 1


class IssueCommentInline(admin.TabularInline):
    model = IssueComment
    extra = 1


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 1


class IssueRelationInline(admin.TabularInline):
    model = IssueRelation
    fk_name = 'issue'
    extra = 1


@admin.register(Issue)
class IssueAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'tracker', 'is_private', 'subject', 'project',
                    'parent', 'status', 'priority', 'start_date', 'due_date')
    list_display_links = ('subject',)
    list_filter = ('project', 'tracker', 'status', 'priority',
                   ('start_date', DateRangeFilter), ('due_date', DateRangeFilter))
    search_fields = ('subject',)
    inlines = (IssueFileInline, IssueCommentInline, TimeEntryInline, IssueRelationInline)


@admin.register(TimeEntry)
class TimeEntryAdmin(ImportExportMixin, admin.ModelAdmin):
    pass


@admin.register(Tracker)
class TrackerAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'is_in_roadmap', 'default_status', 'description', 'order')
    list_display_links = ('name',)
    list_editable = ('is_in_roadmap', 'default_status', 'description', 'order')
    list_filter = ('default_status',)


@admin.register(IssueCategory)
class IssueCategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'project', 'assigned_to')
    list_display_links = ('name',)
    list_editable = ('project', 'assigned_to')


@admin.register(IssueStatus)
class IssueStatusAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'closed', 'order', 'user')
    list_display_links = ('name',)


@admin.register(Workflow)
class WorkflowAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'role', 'tracker', 'old_status', 'get_new_statuses')
    list_display_links = ('role', 'tracker', 'old_status')

    def get_new_statuses(self, obj):
        return ", ".join([status.name for status in obj.new_statuses.all()]) if obj.new_statuses.all() else '-'

    get_new_statuses.short_description = '허용 업무 상태'


@admin.register(CodeActivity)
class CodeActivityAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'active', 'default', 'order', 'user')
    list_display_links = ('name',)
    list_editable = ('active', 'default', 'order')


@admin.register(CodeIssuePriority)
class CodeIssuePriorityAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'active', 'default', 'order', 'user')
    list_display_links = ('name',)
    list_editable = ('active', 'default', 'order')
