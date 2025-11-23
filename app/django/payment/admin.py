from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportMixin

from .models import (InstallmentPaymentOrder, SalesPriceByGT, PaymentPerInstallment,
                     DownPayment, OverDueRule, SpecialPaymentOrder, SpecialDownPay, SpecialOverDueRule,
                     ContractPayment)


@admin.register(InstallmentPaymentOrder)
class InstallmentPaymentOrderAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'pay_sort', 'pay_code', 'pay_name', 'alias_name',
                    'pay_amt', 'pay_ratio', 'pay_due_date', 'days_since_prev',
                    'is_prep_discount', 'prep_discount_ratio', 'prep_ref_date',
                    'is_late_penalty', 'late_penalty_ratio', 'extra_due_date')
    search_fields = ('pay_name', 'alias_name',)
    list_editable = ('pay_name', 'pay_ratio', 'pay_amt', 'alias_name', 'is_prep_discount',
                     'prep_discount_ratio', 'is_late_penalty', 'late_penalty_ratio', 'days_since_prev',
                     'pay_due_date', 'prep_ref_date', 'extra_due_date')
    list_display_links = ('project', 'pay_sort')
    list_filter = ('project', 'pay_sort')


class PaymentPerInstallmentInline(admin.TabularInline):
    model = PaymentPerInstallment
    extra = 0
    fields = ('pay_order', 'amount')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "pay_order":
            # 중도금(2)과 잔금(3)을 제외한 항목만 선택 가능
            # 계약금(1), 기타 부담금(4), 제세 공과금(5), 금융 비용(6), 업무 대행비(7)만 허용
            queryset = db_field.related_model.objects.filter(
                pay_sort__in=['1', '4', '5', '6', '7']
            )

            # 현재 SalesPriceByGT의 프로젝트에 해당하는 항목만 필터링
            if hasattr(self, 'parent_obj') and self.parent_obj and hasattr(self.parent_obj, 'project'):
                queryset = queryset.filter(project=self.parent_obj.project)

            kwargs["queryset"] = queryset
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        # parent_obj를 설정하여 프로젝트 필터링에 사용
        self.parent_obj = obj
        return super().get_formset(request, obj, **kwargs)


@admin.register(SalesPriceByGT)
class SalesPriceByGTAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'order_group', 'unit_type', 'unit_floor_type',
                    'price_build', 'price_land', 'price_tax', 'price')
    list_display_links = ('project', 'unit_type', 'unit_floor_type')
    list_editable = ('price_build', 'price_land', 'price_tax', 'price')
    list_filter = ('project', 'order_group', 'unit_type')
    inlines = (PaymentPerInstallmentInline,)


@admin.register(PaymentPerInstallment)
class PaymentPerInstallmentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'get_sales_price_info', 'pay_order', 'amount')
    list_display_links = ('get_sales_price_info',)
    list_editable = ('amount',)
    list_filter = ('sales_price__project', 'sales_price__order_group', 'sales_price__unit_type')
    search_fields = ('pay_order__pay_name',)

    def get_sales_price_info(self, obj):
        if obj.sales_price:
            return f"{obj.sales_price.project}-{obj.sales_price.order_group}-{obj.sales_price.unit_type}-[{obj.sales_price.unit_floor_type}]"
        return "No Sales Price"

    get_sales_price_info.short_description = '기준 공급가격 정보'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "pay_order":
            # 중도금(2)과 잔금(3)을 제외한 항목만 선택 가능
            # 계약금(1), 기타 부담금(4), 제세 공과금(5), 금융 비용(6), 업무 대행비(7)만 허용
            kwargs["queryset"] = db_field.related_model.objects.filter(
                pay_sort__in=['1', '4', '5', '6', '7']
            )
        elif db_field.name == "sales_price":
            # SalesPriceByGT를 선택할 때 프로젝트별로 구분해서 표시
            kwargs["queryset"] = db_field.related_model.objects.select_related(
                'project', 'order_group', 'unit_type'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DownPayment)
class DownPaymentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'order_group', 'unit_type', 'payment_amount')
    list_display_links = ('project', 'order_group', 'unit_type')
    list_editable = ('payment_amount',)
    list_filter = ('project', 'order_group', 'unit_type')


@admin.register(OverDueRule)
class OverDueRuleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', '__str__', 'term_start', 'term_end', 'rate_year')
    list_display_links = ('__str__',)
    list_editable = ('term_start', 'term_end', 'rate_year')
    list_filter = ('project',)


@admin.register(SpecialPaymentOrder)
class SpecialPaymentOrderAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'pay_name', 'pay_sort', 'pay_code', 'alias_name',
                    'days_since_prev', 'pay_due_date', 'extra_due_date')
    search_fields = ('pay_name', 'alias_name',)
    list_editable = ('alias_name', 'days_since_prev', 'pay_due_date', 'extra_due_date')
    list_display_links = ('project', 'pay_name',)
    list_filter = ('project', 'pay_sort')


@admin.register(SpecialDownPay)
class SpecialDownPayAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'order_group', 'unit_type', 'payment_amount', 'payment_remain')
    list_display_links = ('project',)
    list_editable = ('order_group', 'unit_type', 'payment_amount', 'payment_remain')
    list_filter = ('project', 'order_group', 'unit_type')


@admin.register(SpecialOverDueRule)
class SpecialOverDueRuleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', '__str__', 'term_start', 'term_end', 'rate_year')
    list_display_links = ('__str__',)
    list_editable = ('term_start', 'term_end', 'rate_year')
    list_filter = ('project',)


# ============================================
# Contract Payment Admin
# ============================================

@admin.register(ContractPayment)
class ContractPaymentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'accounting_entry_short', 'project', 'contract', 'payment_type',
                    'formatted_amount', 'installment_order', 'is_special_purpose', 'creator', 'created_at')
    list_display_links = ('accounting_entry_short',)
    list_filter = ('project', 'payment_type', 'is_special_purpose', 'special_purpose_type')
    search_fields = ('contract__serial_number', 'refund_reason')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('accounting_entry', 'contract', 'installment_order', 'refund_contractor')

    @admin.display(description='회계 분개')
    def accounting_entry_short(self, obj):
        return f"Entry #{obj.accounting_entry_id}"

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'blue' if obj.payment_type == 'PAYMENT' else 'red'
        return format_html('<span style="color: {};">{:,}원</span>', color, obj.amount)
