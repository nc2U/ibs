from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportMixin
from .models import (OrderGroup, Contract, ContractPrice, ContractFile,
                     Contractor, ContractorAddress, ContractorContact, Succession,
                     ContractorRelease, DocumentType, ContractRequiredDocument)


@admin.register(OrderGroup)
class OrderGroupAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'order_number', 'sort', 'is_default_for_uncontracted')
    list_display_links = ('project', 'name',)
    list_filter = ('project', 'sort')
    list_editable = ('order_number', 'is_default_for_uncontracted',)
    search_fields = ('name',)


@admin.register(DocumentType)
class DocumentTypeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'default_quantity', 'is_default_item',
                    'is_active', 'description', 'display_order')
    list_display_links = ('name',)
    list_editable = ('code', 'default_quantity', 'is_default_item', 'is_active', 'display_order')
    list_filter = ('is_default_item', 'is_active')
    search_fields = ('name',)


@admin.register(ContractRequiredDocument)
class ContractRequiredDocumentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'document_type', 'quantity', 'notes', 'require_type')
    list_display_links = ('project', 'document_type')
    list_filter = ('project', 'document_type', 'require_type')
    search_fields = ('document_type__name',)


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


class ContractStatusFilter(admin.SimpleListFilter):
    """계약 상태에 따른 필터 (계약 있음/미계약)"""
    title = _('계약 상태')
    parameter_name = 'contract_status'

    def lookups(self, request, model_admin):
        return (
            ('contracted', _('계약 - 체결')),
            ('uncontracted', _('미계약')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'contracted':
            return queryset.filter(contract__isnull=False)
        if self.value() == 'uncontracted':
            return queryset.filter(contract__isnull=True)
        return queryset


@admin.register(ContractPrice)
class ContractPriceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order_group', 'contract_status', 'contract', 'house_unit', 'unit_type_display', 'price',
                    'is_cache_valid')
    list_display_links = ('contract', 'house_unit')
    list_editable = ('order_group', 'price')
    list_filter = (
        'contract__project',
        'order_group',  # order_group 직접 필터
        'house_unit__unit_type',  # 미계약 세대의 unit_type 필터
        ContractStatusFilter,  # 계약 상태 필터 추가
        'is_cache_valid',  # 캐시 유효성 필터
    )
    search_fields = (
        'contract__serial_number',
        'contract__contractor__name',
        'house_unit__name',
        'house_unit__unit_type__name'
    )
    readonly_fields = ('calculated',)

    def contract_status(self, obj):
        """계약 상태 표시"""
        if obj.contract:
            return "✅ 계약"
        else:
            return "⚪ 미계약"

    contract_status.short_description = "계약 상태"

    def unit_type_display(self, obj):
        """유닛 타입 표시 (계약 또는 house_unit에서)"""
        if obj.contract and obj.contract.unit_type:
            return obj.contract.unit_type.name
        elif obj.house_unit and obj.house_unit.unit_type:
            return obj.house_unit.unit_type.name
        return "-"

    unit_type_display.short_description = "유닛 타입"


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
    list_display = ('__str__', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3', 'is_current')
    list_editable = ('is_current',)


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
