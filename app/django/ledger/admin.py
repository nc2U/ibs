from django.contrib import admin
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from ledger.models import CompanyBankAccount, ProjectBankAccount, CompanyBankTransaction


@admin.register(CompanyBankAccount)
class CompanyBankAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order', 'depart', 'bankcode', 'alias_name',
                    'number', 'holder', 'open_date', 'note', 'inactive')
    list_editable = ('order', 'number', 'inactive')
    list_display_links = ('depart', 'bankcode')
    list_filter = ('company', 'depart', 'bankcode', 'holder')


@admin.register(ProjectBankAccount)
class ProjectBankAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order', 'project', 'alias_name', 'bankcode', 'number',
                    'holder', 'open_date', 'note', 'inactive', 'directpay')
    list_editable = ('order', 'number', 'inactive', 'directpay')
    list_display_links = ('project', 'bankcode')
    list_filter = ('bankcode', 'holder')


@admin.register(CompanyBankTransaction)
class CompanyBankTransactionAdmin(ImportExportMixin, admin.ModelAdmin):
    pass
