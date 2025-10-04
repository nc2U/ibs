from django.contrib import admin
from .models import SalesBillIssue, RegisteredSenderNumber, MessageTemplate


@admin.register(SalesBillIssue)
class SalesBillIssueAdmin(admin.ModelAdmin):
    pass


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
