from rest_framework import serializers

from cash.models import ProjectBankAccount, ProjectCashBook
from contract.models import OrderGroup, Contract, Contractor
from payment.models import InstallmentPaymentOrder, SalesPriceByGT, DownPayment, OverDueRule, PaymentPerInstallment
from .items import SimpleUnitTypeSerializer


# Payment --------------------------------------------------------------------------


class PaymentSummaryComponentSerializer(serializers.Serializer):
    """PaymentSummary 컴포넌트용 시리얼라이저"""
    unit_type_id = serializers.IntegerField()
    unit_type_name = serializers.CharField()
    unit_type_color = serializers.CharField()
    total_budget = serializers.IntegerField()
    total_contract_amount = serializers.IntegerField()
    total_paid_amount = serializers.IntegerField()
    unpaid_amount = serializers.IntegerField()
    unsold_amount = serializers.IntegerField()


class InstallmentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPaymentOrder
        fields = ('pk', 'project', '__str__', 'type_sort', 'pay_sort',
                  'pay_code', 'pay_time', 'pay_name', 'alias_name',
                  'pay_amt', 'pay_ratio', 'pay_due_date', 'days_since_prev',
                  'is_prep_discount', 'prep_discount_ratio', 'prep_ref_date',
                  'is_late_penalty', 'late_penalty_ratio', 'extra_due_date')


class SalesPriceSerializer(serializers.ModelSerializer):
    price_setting = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SalesPriceByGT
        fields = ('pk', 'project', 'order_group', 'unit_type', 'price_setting',
                  'unit_floor_type', 'price_build', 'price_land', 'price_tax', 'price')

    @staticmethod
    def get_price_setting(obj):
        return obj.unit_type.price_setting if obj.unit_type else None


class PaymentPerInstallmentSerializer(serializers.ModelSerializer):
    sales_price_info = serializers.SerializerMethodField(read_only=True)
    pay_order_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaymentPerInstallment
        fields = ('pk', 'sales_price', 'sales_price_info', 'pay_order', 'pay_order_info', 'amount')

    @staticmethod
    def get_sales_price_info(obj):
        if obj.sales_price:
            return {
                'project': obj.sales_price.project.name if obj.sales_price.project else None,
                'order_group': obj.sales_price.order_group.name if obj.sales_price.order_group else None,
                'unit_type': obj.sales_price.unit_type.name if obj.sales_price.unit_type else None,
                'unit_floor_type': obj.sales_price.unit_floor_type.alias_name if obj.sales_price.unit_floor_type else None,
                'price': obj.sales_price.price
            }
        return None

    @staticmethod
    def get_pay_order_info(obj):
        if obj.pay_order:
            return {
                'pay_sort': obj.pay_order.get_pay_sort_display(),
                'pay_name': obj.pay_order.pay_name,
                'pay_code': obj.pay_order.pay_code,
                'pay_time': obj.pay_order.pay_time
            }
        return None


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
        fields = ('pk', 'sort', 'name')


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


class PayOrderCollectionSerializer(serializers.Serializer):
    collected_amount = serializers.IntegerField()
    discount_amount = serializers.IntegerField()
    overdue_fee = serializers.IntegerField()
    actual_collected = serializers.IntegerField()
    collection_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class PayOrderDuePeriodSerializer(serializers.Serializer):
    contract_amount = serializers.IntegerField()
    unpaid_amount = serializers.IntegerField()
    unpaid_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    overdue_fee = serializers.IntegerField()
    subtotal = serializers.IntegerField()


class OverallSummaryPayOrderSerializer(serializers.ModelSerializer):
    contract_amount = serializers.IntegerField()
    non_contract_amount = serializers.IntegerField()
    collection = PayOrderCollectionSerializer()
    due_period = PayOrderDuePeriodSerializer()
    not_due_unpaid = serializers.IntegerField()
    total_unpaid = serializers.IntegerField()
    total_unpaid_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = InstallmentPaymentOrder
        fields = ('pk', 'pay_name', 'pay_due_date', 'pay_sort', 'pay_code',
                  'pay_time', 'contract_amount', 'non_contract_amount', 'collection', 'due_period',
                  'not_due_unpaid', 'total_unpaid', 'total_unpaid_rate')


class OverallSummaryAggregateSerializer(serializers.Serializer):
    conts_num = serializers.IntegerField()
    non_conts_num = serializers.IntegerField()
    total_units = serializers.IntegerField()
    contract_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class OverallSummarySerializer(serializers.Serializer):
    pay_orders = OverallSummaryPayOrderSerializer(many=True)
    aggregate = OverallSummaryAggregateSerializer()


class SalesSummaryByGroupTypeSerializer(serializers.Serializer):
    order_group = serializers.IntegerField()
    unit_type = serializers.IntegerField()
    total_sales_amount = serializers.IntegerField()
    contract_amount = serializers.IntegerField()
    non_contract_amount = serializers.IntegerField()


class PaymentStatusByUnitTypeSerializer(serializers.Serializer):
    order_group_id = serializers.IntegerField()
    order_group_name = serializers.CharField()
    unit_type_id = serializers.IntegerField()
    unit_type_name = serializers.CharField()
    unit_type_color = serializers.CharField()
    total_sales_amount = serializers.IntegerField()
    planned_units = serializers.IntegerField()
    contract_units = serializers.IntegerField()
    non_contract_units = serializers.IntegerField()
    contract_amount = serializers.IntegerField()
    paid_amount = serializers.IntegerField()
    unpaid_amount = serializers.IntegerField()
    non_contract_amount = serializers.IntegerField()
    total_budget = serializers.IntegerField()
