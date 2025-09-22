from django.contrib import admin
from import_export.admin import ImportExportMixin
from .models import (OrderGroup, Contract, ContractPrice, ContractFile,
                     Contractor, ContractorAddress,
                     ContractorContact, Succession, ContractorRelease)


@admin.register(OrderGroup)
class OrderGroupAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'order_number', 'sort')
    list_display_links = ('project', 'name',)
    list_filter = ('project', 'sort')
    search_fields = ('name',)


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


@admin.register(ContractPrice)
class ContractPriceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'contract', 'price', 'price_build', 'price_land', 'price_tax',
                    'down_pay', 'middle_pay', 'remain_pay')
    list_display_links = ('contract',)
    list_editable = ('price', 'price_build', 'price_land', 'price_tax')
    list_filter = ('contract__project', 'contract__order_group', 'contract__unit_type',
                   'contract__activation', 'contract__contractor__status')


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
