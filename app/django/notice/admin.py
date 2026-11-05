from django.contrib import admin
from import_export.admin import ImportExportMixin

from apiV1.permissions._utils import get_project_ids_with_permission
from .models import (
    SalesBillIssue, RegisteredSenderNumber, MessageTemplate, MessageSendHistory,
    EmailNotice, EmailSendLog
)


@admin.register(SalesBillIssue)
class SalesBillIssueAdmin(admin.ModelAdmin):
    list_display = ('project', 'now_payment_order', 'host_name', 'host_tel', 'agency', 'agency_tel')
    list_select_related = ('project', 'now_payment_order')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return qs
        accessible_projects = get_project_ids_with_permission(request.user, 'notice.read')
        return qs.filter(project_id__in=accessible_projects)


@admin.register(RegisteredSenderNumber)
class RegisteredSenderNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'label', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('phone_number', 'label')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'message_type', 'is_active', 'created_by', 'created_at')
    list_filter = ('message_type', 'is_active', 'created_at')
    search_fields = ('title', 'content')
    list_select_related = ('created_by',)
    readonly_fields = ('created_by', 'created_at', 'updated_at')


@admin.register(MessageSendHistory)
class MessageSendHistoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('company_id', 'project', 'request_no', 'message_type',
                    'sender_number', 'title', 'sent_at', 'sent_by')
    list_filter = ('message_type', 'project', 'sent_by')
    search_fields = ('title', 'message_content')
    list_select_related = ('project', 'sent_by')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return qs
        accessible_projects = get_project_ids_with_permission(request.user, 'notice.read')
        return qs.filter(project_id__in=accessible_projects)


@admin.register(EmailNotice)
class EmailNoticeAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'title', 'sender_name', 'status',
                    'total_recipients', 'success_count', 'fail_count', 'sent_by', 'created')
    list_filter = ('status', 'project')
    search_fields = ('title', 'sender_name', 'sender_email')
    list_select_related = ('project', 'sent_by')
    readonly_fields = ('total_recipients', 'success_count', 'fail_count', 'status', 'created', 'completed_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return qs
        accessible_projects = get_project_ids_with_permission(request.user, 'notice.read')
        return qs.filter(project_id__in=accessible_projects)


@admin.register(EmailSendLog)
class EmailSendLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'email_notice', 'contractor', 'recipient_name',
                    'recipient_email', 'unit_info', 'status', 'sent_at')
    list_filter = ('status', 'email_notice__project')
    search_fields = ('recipient_name', 'recipient_email', 'unit_info')
    list_select_related = ('email_notice__project', 'contractor')
    readonly_fields = ('sent_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return qs
        accessible_projects = get_project_ids_with_permission(request.user, 'notice.read')
        return qs.filter(email_notice__project_id__in=accessible_projects)
