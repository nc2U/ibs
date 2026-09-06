from django.contrib import admin
from .models import (
    SalesAgency, SalesTeam, SalesPerson, CommissionPolicy,
    ContractSalesAgent, SettlementPeriod, CommissionPayout,
    PayoutContractDetail, CommissionClawback
)


@admin.register(SalesAgency)
class SalesAgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'project', 'is_direct_managed', 'ceo_name', 'phone', 'is_active')
    list_filter = ('project', 'is_direct_managed', 'is_active')
    search_fields = ('name', 'ceo_name', 'business_number')


@admin.register(SalesTeam)
class SalesTeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'agency', 'parent', 'order', 'is_active')
    list_filter = ('agency__project', 'agency', 'is_active')
    search_fields = ('name',)


@admin.register(SalesPerson)
class SalesPersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'duty', 'team', 'status', 'phone', 'tax_type', 'bank_name', 'account_holder')
    list_filter = ('duty', 'status', 'tax_type', 'team__agency__project', 'team')
    search_fields = ('name', 'phone', 'id_number', 'account_holder')


@admin.register(CommissionPolicy)
class CommissionPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'project', 'order_group', 'unit_type', 'agent_fee', 'leader_fee', 'director_fee', 'pay_condition', 'is_active')
    list_filter = ('project', 'pay_condition', 'is_active')
    search_fields = ('name',)


@admin.register(ContractSalesAgent)
class ContractSalesAgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'sales_person', 'team', 'contract_date', 'mgm_name', 'mgm_fee')
    list_filter = ('team__agency__project', 'team')
    search_fields = ('contract__serial_number', 'sales_person__name', 'mgm_name')


class CommissionPayoutInline(admin.TabularInline):
    model = CommissionPayout
    extra = 0
    fields = ('sales_person', 'contract_count', 'base_pay', 'commission_amount', 'gross_amount', 'total_tax', 'net_amount', 'pay_status')
    readonly_fields = ('gross_amount', 'total_tax', 'net_amount')


@admin.register(SettlementPeriod)
class SettlementPeriodAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'project', 'start_date', 'end_date', 'status', 'total_contracts', 'total_gross_amount', 'total_net_amount')
    list_filter = ('project', 'status')
    search_fields = ('title',)
    inlines = [CommissionPayoutInline]


@admin.register(CommissionPayout)
class CommissionPayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'period', 'sales_person', 'contract_count', 'gross_amount', 'total_tax', 'net_amount', 'pay_status', 'paid_date')
    list_filter = ('period__project', 'pay_status', 'period')
    search_fields = ('sales_person__name', 'account_holder')


@admin.register(PayoutContractDetail)
class PayoutContractDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'payout', 'contract', 'role_type', 'unit_fee')
    list_filter = ('role_type',)


@admin.register(CommissionClawback)
class CommissionClawbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'sales_person', 'contract', 'amount', 'is_settled', 'settled_payout', 'created_at')
    list_filter = ('is_settled',)
    search_fields = ('sales_person__name', 'contract__serial_number')
