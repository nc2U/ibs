from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from ledger.models import (
    BankCode,
    CompanyBankAccount, ProjectBankAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
)


# ============================================
# Bank Account Admin
# ============================================

@admin.register(CompanyBankAccount)
class CompanyBankAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order', 'company', 'depart', 'bankcode', 'alias_name',
                    'number', 'holder', 'open_date', 'note', 'is_hide', 'inactive')
    list_editable = ('order', 'number', 'is_hide', 'inactive')
    list_display_links = ('alias_name',)
    list_filter = ('company', 'depart', 'bankcode', 'holder', 'is_hide', 'inactive')
    search_fields = ('alias_name', 'number', 'holder', 'note')
    ordering = ('order', 'id')


@admin.register(ProjectBankAccount)
class ProjectBankAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order', 'project', 'alias_name', 'bankcode', 'number',
                    'holder', 'open_date', 'note', 'is_hide', 'inactive', 'directpay', 'is_imprest')
    list_editable = ('order', 'number', 'is_hide', 'inactive', 'directpay', 'is_imprest')
    list_display_links = ('alias_name',)
    list_filter = ('project', 'bankcode', 'holder', 'is_hide', 'inactive', 'directpay', 'is_imprest')
    search_fields = ('alias_name', 'number', 'holder', 'note', 'project__name')
    ordering = ('order', 'id')


# ============================================
# Bank Transaction Admin
# ============================================

@admin.register(CompanyBankTransaction)
class CompanyBankTransactionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'transaction_id_short', 'company', 'bank_account', 'deal_date',
                    'transaction_type', 'formatted_amount', 'content', 'creator', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('company', 'bank_account', 'transaction_type', ('deal_date', DateRangeFilter))
    search_fields = ('transaction_id', 'content', 'note')
    date_hierarchy = 'deal_date'
    ordering = ('-deal_date', '-created_at')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'blue' if obj.transaction_type == 'INCOME' else 'red'
        return format_html('<span style="color: {};">{:,}원</span>', color, obj.amount)


@admin.register(ProjectBankTransaction)
class ProjectBankTransactionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'transaction_id_short', 'project', 'bank_account', 'deal_date',
                    'transaction_type', 'formatted_amount', 'content', 'is_imprest', 'creator', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('project', 'bank_account', 'transaction_type', 'is_imprest', ('deal_date', DateRangeFilter))
    search_fields = ('transaction_id', 'content', 'note', 'project__name')
    date_hierarchy = 'deal_date'
    ordering = ('-deal_date', '-created_at')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'blue' if obj.transaction_type == 'INCOME' else 'red'
        return format_html('<span style="color: {};">{:,}원</span>', color, obj.amount)


# ============================================
# Accounting Entry Admin
# ============================================

@admin.register(CompanyAccountingEntry)
class CompanyAccountingEntryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'transaction_id_short', 'company', 'sort', 'account_d1',
                    'account_d2', 'account_d3', 'formatted_amount', 'trader', 'evidence_type', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('company', 'sort', 'account_d1', 'evidence_type')
    search_fields = ('transaction_id', 'account_code', 'trader')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        return format_html('{:,}원', obj.amount)


@admin.register(ProjectAccountingEntry)
class ProjectAccountingEntryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'transaction_id_short', 'project', 'sort', 'project_account_d2',
                    'project_account_d3', 'formatted_amount', 'trader', 'evidence_type', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('project', 'sort', 'project_account_d2', 'evidence_type')
    search_fields = ('transaction_id', 'account_code', 'trader', 'project__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        return format_html('{:,}원', obj.amount)
