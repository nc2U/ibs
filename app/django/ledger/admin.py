from django.contrib import admin
from django.utils.html import format_html
from django.forms.models import BaseInlineFormSet
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from ledger.models import (
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
    readonly_fields = ('transaction_id', 'created_at', 'updated_at', 'related_accounting_entries')

    def related_accounting_entries(self, obj):
        """연관된 회계분개 항목들을 표시"""
        if not obj.pk:
            return "저장 후 회계분개를 확인할 수 있습니다."

        entries = CompanyAccountingEntry.objects.filter(transaction_id=obj.transaction_id)
        if not entries.exists():
            return format_html(
                '<a href="/admin/ledger/companyaccountingentry/add/?transaction_id={}" target="_blank">'
                '+ 회계분개 추가</a>',
                obj.transaction_id
            )

        links = []
        for entry in entries:
            links.append(format_html(
                '<a href="/admin/ledger/companyaccountingentry/{}/change/" target="_blank">'
                '{} - {}원 ({})</a>',
                entry.pk,
                entry.sort,
                f"{entry.amount:,}",
                entry.account_d3
            ))

        add_link = format_html(
            '<a href="/admin/ledger/companyaccountingentry/add/?transaction_id={}" target="_blank">'
            '+ 추가</a>',
            obj.transaction_id
        )

        return format_html('<br>'.join(links) + '<br>' + add_link)

    related_accounting_entries.short_description = '연관 회계분개'

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'blue' if obj.transaction_type == 'INCOME' else 'red'
        formatted_amount = f"{obj.amount:,}"
        return format_html('<span style="color: {};">{}원</span>', color, formatted_amount)


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
        formatted_amount = f"{obj.amount:,}"
        return format_html('<span style="color: {};">{}원</span>', color, formatted_amount)


# ============================================
# Accounting Entry Admin
# ============================================

@admin.register(CompanyAccountingEntry)
class CompanyAccountingEntryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'transaction_id_short', 'company', 'sort', 'account_d1',
                    'account_d2', 'account_d3', 'formatted_amount', 'trader', 'evidence_type', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('company', 'sort', 'account_d1', 'evidence_type')
    search_fields = ('transaction_id', 'trader')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def get_changeform_initial_data(self, request):
        """URL 파라미터에서 초기값 설정"""
        initial = super().get_changeform_initial_data(request)

        # transaction_id 파라미터가 있으면 초기값으로 설정
        if 'transaction_id' in request.GET:
            initial['transaction_id'] = request.GET['transaction_id']

            # CompanyBankTransaction에서 company 정보 가져오기
            try:
                bank_transaction = CompanyBankTransaction.objects.get(
                    transaction_id=request.GET['transaction_id']
                )
                initial['company'] = bank_transaction.company
            except CompanyBankTransaction.DoesNotExist:
                pass

        return initial

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        formatted_amount = f"{obj.amount:,}"
        return format_html('{}원', formatted_amount)


@admin.register(ProjectAccountingEntry)
class ProjectAccountingEntryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'transaction_id_short', 'project', 'sort', 'project_account_d2',
                    'project_account_d3', 'formatted_amount', 'trader', 'evidence_type', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('project', 'sort', 'project_account_d2', 'evidence_type')
    search_fields = ('transaction_id', 'trader', 'project__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        formatted_amount = f"{obj.amount:,}"
        return format_html('{}원', formatted_amount)
