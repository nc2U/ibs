"""
Ledger-based payment serializers

Serializers for ContractPayment and related ledger models
"""
from rest_framework import serializers

from contract.models import Contract, Contractor
from ledger.models import ProjectAccountingEntry, ProjectBankTransaction
from payment.models import ContractPayment, InstallmentPaymentOrder
from .payment import SimpleOrderGroupSerializer, SimpleUnitTypeSerializer, SimpleInstallmentOrderSerializer


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


class SimpleContractSerializer(serializers.ModelSerializer):
    """Contract 간단 직렬화 (Ledger용)"""
    order_group = SimpleOrderGroupSerializer()
    unit_type = SimpleUnitTypeSerializer()
    contractor = serializers.SlugRelatedField(queryset=Contractor.objects.all(), slug_field='name')

    class Meta:
        model = Contract
        fields = ('pk', 'order_group', 'unit_type', 'serial_number', 'contractor')


class ContractPaymentSerializer(serializers.ModelSerializer):
    """
    ContractPayment 직렬화

    기존 PaymentSerializer와 유사한 응답 구조 제공 (호환성 유지)
    """
    contract = SimpleContractSerializer(read_only=True)
    installment_order = SimpleInstallmentOrderSerializer(read_only=True)
    accounting_entry = SimpleLedgerAccountingEntrySerializer(read_only=True)

    # 계산된 필드
    deal_date = serializers.DateField(read_only=True)
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = ContractPayment
        fields = (
            'pk', 'project', 'contract', 'installment_order',
            'accounting_entry', 'deal_date', 'amount',
            'is_payment_mismatch', 'created_at', 'updated_at', 'creator'
        )
        read_only_fields = ('deal_date', 'amount', 'created_at', 'updated_at')


class ContractPaymentListSerializer(serializers.ModelSerializer):
    """
    ContractPayment 목록용 최적화된 직렬화

    기존 PaymentSerializer와 호환되는 필드 구조
    """
    contract = SimpleContractSerializer(read_only=True)
    installment_order = SimpleInstallmentOrderSerializer(read_only=True)

    # ProjectCashBook과 호환되는 필드명
    deal_date = serializers.DateField(source='related_transaction.deal_date', read_only=True)
    income = serializers.IntegerField(source='amount', read_only=True)
    bank_account = serializers.SerializerMethodField(read_only=True)
    trader = serializers.CharField(source='accounting_entry.trader', read_only=True)
    note = serializers.CharField(source='accounting_entry.related_transaction.note', read_only=True)

    class Meta:
        model = ContractPayment
        fields = (
            'pk', 'deal_date', 'contract', 'income', 'installment_order',
            'bank_account', 'trader', 'note'
        )

    def get_bank_account(self, obj):
        """
        은행계좌 정보 조회

        ProjectBankTransaction에서 bank_account 정보 추출
        """
        try:
            transaction = obj.accounting_entry.related_transaction
            if hasattr(transaction, 'bank_account') and transaction.bank_account:
                return {
                    'pk': transaction.bank_account.pk,
                    'alias_name': transaction.bank_account.alias_name
                }
        except AttributeError:
            pass
        return None
