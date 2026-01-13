from rest_framework import serializers

from cash.models import ProjectBankAccount, ProjectCashBook
from contract.models import OrderGroup, Contract, Contractor
from ledger.models import ProjectBankTransaction, ProjectAccountingEntry
from payment.models import (InstallmentPaymentOrder, SalesPriceByGT, DownPayment,
                            ContractPayment, OverDueRule, PaymentPerInstallment)
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


# will be deprecated - use ProjectCashBook
class PaymentSerializer(serializers.ModelSerializer):
    contract = SimpleContractSerializer()
    installment_order = SimpleInstallmentOrderSerializer()
    bank_account = SimpleProjectBankAccountSerializer()

    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'deal_date', 'contract', 'income', 'installment_order',
                  'bank_account', 'trader', 'note')


# will be deprecated - use ProjectCashBook
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
    contract_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    collection = PayOrderCollectionSerializer()
    due_period = PayOrderDuePeriodSerializer()
    not_due_unpaid = serializers.IntegerField()
    total_unpaid = serializers.IntegerField()
    total_unpaid_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = InstallmentPaymentOrder
        fields = ('pk', 'pay_name', 'pay_due_date', 'pay_sort', 'pay_code',
                  'pay_time', 'contract_amount', 'non_contract_amount', 'contract_rate', 'collection', 'due_period',
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


# --------------------------------------------------------------------
# ledger based new api
# --------------------------------------------------------------------

class SimpleLedgerBankTransactionSerializer(serializers.ModelSerializer):
    """ProjectBankTransaction 간단 직렬화"""

    class Meta:
        model = ProjectBankTransaction
        fields = ('pk', 'deal_date', 'amount', 'content', 'note')


class SimpleLedgerAccountingEntrySerializer(serializers.ModelSerializer):
    """ProjectAccountingEntry 간단 직렬화"""
    related_transaction = SimpleLedgerBankTransactionSerializer(read_only=True)

    class Meta:
        model = ProjectAccountingEntry
        fields = ('pk', 'transaction_id', 'amount', 'account', 'related_transaction')


class ContractPaymentSerializer(serializers.ModelSerializer):
    """
    ContractPayment 통합 직렬화 (기본 + 목록)

    기존 PaymentSerializer와 호환되는 응답 구조 제공
    retrieve, list, create, update, delete 모든 액션에서 사용
    """
    # 관계 필드
    contract = SimpleContractSerializer(read_only=True)
    installment_order = SimpleInstallmentOrderSerializer(read_only=True)
    accounting_entry = SimpleLedgerAccountingEntrySerializer(read_only=True)

    # 모델 프로퍼티 (효율적)
    deal_date = serializers.DateField(read_only=True)
    amount = serializers.IntegerField(read_only=True)

    # 추가 필드 (목록용 - accounting_entry를 통해 조회)
    bank_account = serializers.SerializerMethodField(read_only=True)
    trader = serializers.SerializerMethodField(read_only=True)
    note = serializers.SerializerMethodField(read_only=True)
    bank_transaction_id = serializers.SerializerMethodField(read_only=True)

    # 폼 수정용 추가 필드
    bank_transaction_amount = serializers.SerializerMethodField(read_only=True)
    sibling_entries = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ContractPayment
        fields = (
            # 기본 필드
            'pk', 'project', 'contract', 'installment_order',
            'accounting_entry', 'deal_date', 'amount', 'is_payment_mismatch',
            'created_at', 'updated_at', 'creator',
            # 목록용 추가 필드
            'bank_account', 'trader', 'note', 'bank_transaction_id',
            # 폼 수정용 추가 필드
            'bank_transaction_amount', 'sibling_entries'
        )
        read_only_fields = ('deal_date', 'amount', 'created_at', 'updated_at')

    def get_trader(self, obj):
        """거래처 조회"""
        try:
            return obj.accounting_entry.trader
        except AttributeError:
            return None

    def get_note(self, obj):
        """비고 조회"""
        try:
            return obj.accounting_entry.related_transaction.note
        except (AttributeError, TypeError):
            return None

    def get_bank_account(self, obj):
        """
        은행계좌 정보 조회

        ProjectBankTransaction에서 bank_account 정보 추출
        """
        try:
            transaction = obj.accounting_entry.related_transaction
            if transaction and hasattr(transaction, 'bank_account') and transaction.bank_account:
                return {
                    'pk': transaction.bank_account.pk,
                    'alias_name': transaction.bank_account.alias_name
                }
        except (AttributeError, TypeError):
            pass
        return None

    def get_bank_transaction_id(self, obj):
        """
        은행 거래 ID 조회

        프론트엔드에서 수정/삭제 시 ProjectCompositeTransactionSerializer 에 필요
        updateContractPayment(bank_transaction_id, payload)
        patchContractPayment(bank_transaction_id, payload)
        deleteContractPayment(bank_transaction_id)
        """
        try:
            return obj.related_transaction.pk
        except (AttributeError, TypeError):
            return None

    def get_bank_transaction_amount(self, obj):
        """
        실제 은행 거래 금액 조회

        PaymentForm 수정 시 은행거래 금액을 정확히 표시하기 위해 필요
        obj.amount는 분개 금액(분할 납부 시 일부 금액)
        이 필드는 실제 은행 거래의 총 금액을 반환
        """
        try:
            return obj.accounting_entry.related_transaction.amount
        except (AttributeError, TypeError):
            return None

    def get_sibling_entries(self, obj):
        """
        같은 은행 거래에 속한 모든 형제 분개 조회

        PaymentForm 수정 시 모든 분개를 가져와서 ContractPayment 여부로 구분
        - ContractPayment에 해당하는 항목: 편집 가능한 폼
        - ContractPayment에 해당하지 않는 항목: 참조용 표시

        예시:
        - 은행거래: 24,811,705원
        - 분개1: 분담금 16,734,356원 → ContractPayment (편집 가능)
        - 분개2: 영업외수익 8,077,349원 → 기타 분개 (참조용)

        Returns:
            List[dict]: 모든 형제 분개 정보 목록 (is_contract_payment로 구분)
        """
        try:
            # 현재 분개의 transaction_id 가져오기
            transaction_id = obj.accounting_entry.transaction_id

            # 같은 transaction_id를 가진 모든 분개 조회
            sibling_entries = ProjectAccountingEntry.objects.filter(
                transaction_id=transaction_id
            ).select_related(
                'account',
                'contract',
                'contract__order_group',
                'contract__unit_type'
            ).order_by('pk')

            # 각 분개 정보를 직렬화
            result = []
            for entry in sibling_entries:
                # ContractPayment 존재 여부 확인
                contract_payment = None
                try:
                    contract_payment = ContractPayment.objects.select_related(
                        'installment_order'
                    ).get(accounting_entry=entry)
                except ContractPayment.DoesNotExist:
                    pass

                # 기본 분개 정보
                entry_data = {
                    'pk': entry.pk,  # AccountingEntry PK
                    'amount': entry.amount,
                    'trader': entry.trader,
                    'contract': entry.contract.pk if entry.contract else None,
                    'account': {
                        'pk': entry.account.pk if entry.account else None,
                        'name': entry.account.name if entry.account else None,
                        'is_payment': getattr(entry.account, 'is_payment', False) if entry.account else False
                    },
                    'is_contract_payment': contract_payment is not None
                }

                # ContractPayment가 있는 경우 추가 정보
                if contract_payment:
                    entry_data.update({
                        'contract_payment_pk': contract_payment.pk,
                        'installment_order': contract_payment.installment_order.pk if contract_payment.installment_order else None,
                        'installment_order_display': str(contract_payment.installment_order) if contract_payment.installment_order else None,
                    })
                else:
                    entry_data.update({
                        'contract_payment_pk': None,
                        'installment_order': None,
                        'installment_order_display': None,
                    })

                result.append(entry_data)

            return result

        except (AttributeError, TypeError):
            return []
