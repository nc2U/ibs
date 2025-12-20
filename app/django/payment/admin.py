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
                    'formatted_amount', 'payment_status_display', 'installment_order',
                    'creator', 'created_at')
    list_display_links = ('accounting_entry_short',)
    list_filter = ('project', 'payment_type', 'is_payment_mismatch')
    search_fields = ('contract__serial_number', 'refund_reason', 'accounting_entry__transaction_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'payment_mismatch_info')
    raw_id_fields = ('accounting_entry', 'contract', 'installment_order', 'refund_contractor')

    fieldsets = (
        ('기본 정보', {
            'fields': ('accounting_entry', 'project')
        }),
        ('계약 정보', {
            'fields': ('contract', 'installment_order', 'payment_type')
        }),
        ('환불 정보', {
            'fields': ('refund_contractor', 'refund_reason'),
            'classes': ('collapse',)
        }),
        ('상태 정보', {
            'fields': ('is_payment_mismatch', 'payment_mismatch_info')
        }),
        ('메타데이터', {
            'fields': ('creator', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description='회계 분개')
    def accounting_entry_short(self, obj):
        if obj.accounting_entry:
            return format_html(
                '<a href="/admin/ledger/projectaccountingentry/{}/change/" target="_blank">'
                'Entry #{}</a>',
                obj.accounting_entry.pk,
                obj.accounting_entry_id
            )
        return f"Entry #{obj.accounting_entry_id}"

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'blue' if obj.payment_type == 'PAYMENT' else 'red'
        return format_html('<span style="color: {};">{:,}원</span>', color, obj.amount)

    @admin.display(description='결제 상태')
    def payment_status_display(self, obj):
        """결제계정 일치 여부 및 완성도 표시"""
        if obj.is_payment_mismatch:
            return format_html(
                '<span style="color: red; font-weight: bold;">❌ 계정 불일치</span>'
            )

        # 베이스 인스턴스인지 확인 (계약 정보 미완성)
        if not obj.contract:
            return format_html(
                '<span style="color: orange;">⚠️ 세부 정보 미입력</span>'
            )

        # 완전한 상태
        return format_html(
            '<span style="color: green;">✅ 정상</span>'
        )

    def payment_mismatch_info(self, obj):
        """계정 불일치 상세 정보"""
        if not obj.accounting_entry:
            return "회계분개 정보 없음"

        ae = obj.accounting_entry
        if not ae.account:
            return "계정 분류 정보 없음"

        is_payment_account = ae.account.is_payment

        if obj.is_payment_mismatch:
            if not is_payment_account:
                return format_html(
                    '<div style="color: red;">'
                    '<strong>⚠️ 불일치 감지</strong><br>'
                    '연결된 회계 계정이 비결제 계정으로 변경되었습니다.<br>'
                    '계정: {} (is_payment=False)<br>'
                    '<em>사용자가 계정 분류를 수정하거나 이 계약납부를 다른 회계분개로 이전해야 합니다.</em>'
                    '</div>',
                    ae.account.name
                )
        else:
            if is_payment_account:
                return format_html(
                    '<div style="color: green;">'
                    '<strong>✅ 정상</strong><br>'
                    '계정: {} (is_payment=True)'
                    '</div>',
                    ae.account.name
                )
            else:
                return format_html(
                    '<div style="color: orange;">'
                    '<strong>⚠️ 주의</strong><br>'
                    '계정이 비결제 계정이지만 mismatch 플래그가 설정되지 않았습니다.<br>'
                    '계정: {} (is_payment=False)'
                    '</div>',
                    ae.account.name
                )

        return "상태 확인 불가"

    payment_mismatch_info.short_description = '계정 일치성 상세 정보'

    def get_queryset(self, request):
        """관련 정보를 함께 로드"""
        return super().get_queryset(request).select_related(
            'accounting_entry__account',
            'contract',
            'project',
            'creator'
        )

    actions = ['fix_payment_mismatch', 'mark_as_mismatch']

    @admin.action(description='선택된 항목의 결제계정 불일치 해결')
    def fix_payment_mismatch(self, request, queryset):
        """불일치 플래그 해제 (계정이 실제로 is_payment=True인 경우만)"""
        updated_count = 0
        for payment in queryset.filter(is_payment_mismatch=True):
            if (payment.accounting_entry and
                    payment.accounting_entry.account and
                    payment.accounting_entry.account.is_payment):
                payment.is_payment_mismatch = False
                payment.save(update_fields=['is_payment_mismatch', 'updated_at'])
                updated_count += 1

        self.message_user(request, f"{updated_count}개 항목의 불일치 상태를 해결했습니다.")

    @admin.action(description='선택된 항목을 결제계정 불일치로 표시')
    def mark_as_mismatch(self, request, queryset):
        """수동으로 불일치 플래그 설정"""
        updated_count = queryset.update(is_payment_mismatch=True)
        self.message_user(request, f"{updated_count}개 항목을 불일치로 표시했습니다.")
