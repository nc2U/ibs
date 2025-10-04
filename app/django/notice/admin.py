from django.contrib import admin
from .models import SalesBillIssue, RegisteredSenderNumber


@admin.register(RegisteredSenderNumber)
class RegisteredSenderNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'label', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('phone_number', 'label')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SalesBillIssue)
class SalesBillIssueAdmin(admin.ModelAdmin):
    pass
