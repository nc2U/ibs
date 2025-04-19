from rest_framework import serializers

from cash.models import ProjectBankAccount, ProjectCashBook
from contract.models import OrderGroup, Contract, Contractor
from payment.models import InstallmentPaymentOrder, SalesPriceByGT, DownPayment, OverDueRule
from .items import SimpleUnitTypeSerializer


# Payment --------------------------------------------------------------------------


class InstallmentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPaymentOrder
        fields = ('pk', 'project', '__str__', 'pay_sort', 'pay_code', 'pay_time',
                  'pay_name', 'alias_name', 'is_pm_cost', 'pay_amt', 'pay_ratio',
                  'pay_due_date', 'days_since_prev', 'is_prep_discount', 'prep_discount_ratio',
                  'prep_ref_date', 'is_late_penalty', 'late_penalty_ratio', 'extra_due_date')


class SalesPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesPriceByGT
        fields = ('pk', 'project', 'order_group', 'unit_type', 'unit_floor_type',
                  'price_build', 'price_land', 'price_tax', 'price')


class DownPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownPayment
        fields = ('pk', 'project', 'order_group', 'unit_type', 'payment_amount')


class OverDueRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverDueRule
        fields = ('pk', 'project', 'term_start', 'term_end', 'rate_year')


class SimpleOrderGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderGroup
        fields = ('pk', 'sort', 'order_group_name')


class SimpleContractSerializer(serializers.ModelSerializer):
    order_group = SimpleOrderGroupSerializer()
    unit_type = SimpleUnitTypeSerializer()
    contractor = serializers.SlugRelatedField(queryset=Contractor.objects.all(), slug_field='name')

    class Meta:
        model = Contract
        fields = ('pk', 'order_group', 'unit_type', 'serial_number', 'contractor')


class SimpleInstallmentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPaymentOrder
        fields = ('pk', 'pay_sort', 'pay_time', 'pay_name', '__str__')


class SimpleProjectBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectBankAccount
        fields = ('pk', 'alias_name')


class PaymentSerializer(serializers.ModelSerializer):
    contract = SimpleContractSerializer()
    installment_order = SimpleInstallmentOrderSerializer()
    bank_account = SimpleProjectBankAccountSerializer()

    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'deal_date', 'contract', 'income', 'installment_order',
                  'bank_account', 'trader', 'note')


class PaymentSummarySerializer(serializers.ModelSerializer):
    order_group = serializers.IntegerField()
    unit_type = serializers.IntegerField()
    paid_sum = serializers.IntegerField()

    class Meta:
        model = ProjectCashBook
        fields = ('order_group', 'unit_type', 'paid_sum')
