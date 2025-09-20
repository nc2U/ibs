from django.contrib import admin
from import_export.admin import ImportExportMixin
from .models import (OrderGroup, Contract, ContractPrice, ContractFile,
                     PaymentPerInstallment, Contractor, ContractorAddress,
                     ContractorContact, Succession, ContractorRelease)


@admin.register(OrderGroup)
class OrderGroupAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'order_group_name', 'order_number', 'sort')
    list_display_links = ('project', 'order_group_name',)


class ContractPriceInline(admin.StackedInline):
    model = ContractPrice
    extra = 0


class ContractorInline(admin.StackedInline):
    model = Contractor
    fk_name = 'contract'
    extra = 0


class ContractFileAdmin(admin.StackedInline):
    model = ContractFile
    extra = 0


@admin.register(Contract)
class ContractAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'serial_number', 'key_unit', 'order_group', 'unit_type',
                    'activation', 'contractor', 'contractprice', 'is_sup_cont',
                    'sup_cont_date', 'created', 'creator')
    list_display_links = ('project', 'serial_number',)
    list_filter = ('project', 'order_group', 'unit_type', 'activation', 'contractor__status')
    search_fields = ('serial_number', 'contractor__name')
    inlines = [ContractPriceInline, ContractorInline, ContractFileAdmin]


class PaymentPerInstallmentInline(admin.TabularInline):
    model = PaymentPerInstallment
    extra = 0


@admin.register(ContractPrice)
class ContractPriceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'contract', 'price', 'price_build', 'price_land', 'price_tax',
                    'down_pay', 'biz_agency_fee', 'is_included_baf', 'middle_pay', 'remain_pay')
    list_display_links = ('contract',)
    list_editable = ('price', 'price_build', 'price_land', 'price_tax')
    list_filter = ('contract__project', 'contract__order_group', 'contract__unit_type',
                   'contract__activation', 'contract__contractor__status')
    inlines = [PaymentPerInstallmentInline]


@admin.register(PaymentPerInstallment)
class PaymentPerInstallmentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'get_contract_info', 'cont_price', 'pay_order',
                    'amount', 'is_manual_override', 'disable')
    list_display_links = ('get_contract_info',)
    list_editable = ('amount', 'is_manual_override', 'disable')
    list_filter = ('is_manual_override', 'disable')
    search_fields = ('pay_order__pay_name', 'override_reason')
    readonly_fields = ('created', 'updated')
    fieldsets = (
        ('기본 정보', {
            'fields': ('cont_price', 'pay_order', 'amount')
        }),
        ('설정 정보', {
            'fields': ('is_manual_override', 'override_reason', 'disable')
        }),
        ('시스템 정보', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def get_contract_info(self, obj):
        if obj.cont_price.contract:
            return obj.cont_price.contract
        return "No Contract"

    get_contract_info.short_description = '계약 정보'


class CAdressInline(ImportExportMixin, admin.StackedInline):
    model = ContractorAddress
    extra = 0


class CContactInline(ImportExportMixin, admin.TabularInline):
    model = ContractorContact
    extra = 0


@admin.register(Contractor)
class ContactorAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'contract', 'birth_date', 'gender', 'qualification', 'status',
                    'is_active', 'reservation_date', 'contract_date', 'created')
    search_fields = ('name',)
    list_display_links = ('name',)
    list_filter = ('contract__project', 'contract__order_group', 'contract__unit_type',
                   'contract_date', 'gender', 'qualification', 'status')
    list_editable = ('gender', 'qualification', 'is_active')
    inlines = (CContactInline, CAdressInline)


@admin.register(ContractorAddress)
class CAdressAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('__str__', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
                    'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3')


@admin.register(ContractorContact)
class CContactAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('__str__', 'cell_phone', 'home_phone', 'other_phone', 'email')


@admin.register(Succession)
class SuccessionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'contract', 'seller', 'buyer', 'apply_date', 'trading_date',
                    'is_approval', 'approval_date', 'creator')
    search_fields = ('seller', 'buyer')
    list_display_links = ('contract', 'seller', 'buyer')
    list_editable = ('is_approval', 'approval_date')


@admin.register(ContractorRelease)
class ContractorReleaseAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'contractor', 'status', 'refund_amount',
                    'refund_account_bank', 'refund_account_number',
                    'refund_account_depositor', 'request_date', 'completion_date')
    list_editable = ('request_date', 'completion_date')
