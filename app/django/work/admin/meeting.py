from django.contrib import admin
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from work.models.meeting import MeetingCategory, Meeting, MeetingFile


@admin.register(MeetingCategory)
class MeetingCategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'project', 'name', 'color', 'order')
    list_display_links = ('name',)
    list_editable = ('color', 'order')
    list_filter = ('project',)


class MeetingFileInline(admin.TabularInline):
    model = MeetingFile
    extra = 1


@admin.register(Meeting)
class MeetingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'project', 'category', 'title', 'meeting_date', 'creator', 'created')
    list_display_links = ('title',)
    list_filter = ('project', 'category', ('meeting_date', DateRangeFilter))
    search_fields = ('title', 'agenda', 'content', 'decisions', 'action_items')
    filter_horizontal = ('attendees',)
    inlines = (MeetingFileInline,)

    fieldsets = (
        ('기본 정보', {
            'fields': ('project', 'category', 'title', 'meeting_date')
        }),
        ('회의 준비 (Agenda)', {
            'fields': ('agenda',)
        }),
        ('회의 내용 (Minutes)', {
            'fields': ('content',)
        }),
        ('결과 및 후속 조치', {
            'fields': ('decisions', 'action_items')
        }),
        ('참석자 정보', {
            'fields': ('attendees', 'other_attendees')
        }),
        ('관리 정보', {
            'fields': ('creator', 'updater'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.updater = request.user
        super().save_model(request, obj, form, change)
