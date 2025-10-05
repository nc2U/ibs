from django.contrib import admin
from import_export.admin import ImportExportMixin
from .models import SalesBillIssue, RegisteredSenderNumber, MessageTemplate, MessageSendHistory


@admin.register(SalesBillIssue)
class SalesBillIssueAdmin(admin.ModelAdmin):
    list_display = ('project', 'now_payment_order', 'host_name', 'host_tel', 'agency', 'agency_tel')


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
    readonly_fields = ('created_by', 'created_at', 'updated_at')


@admin.register(MessageSendHistory)
class MessageSendHistoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('company_id', 'project', 'request_no', 'message_type',
                    'sender_number', 'title', 'sent_at', 'sent_by')
    list_filter = ('message_type', 'sent_by')
    search_fields = ('title', 'message_content')
