from django.db import transaction
from rest_framework import serializers

from ledger.models import (
    BankCode,
    CompanyBankAccount, ProjectBankAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    ContractPayment,
)


# ============================================
# Bank Code Serializers
# ============================================

class LedgerBankCodeSerializer(serializers.ModelSerializer):
    """은행 코드 시리얼라이저"""
    class Meta:
        model = BankCode
        fields = ('pk', 'code', 'name')


# ============================================
# Bank Account Serializers
# ============================================

class LedgerCompanyBankAccountSerializer(serializers.ModelSerializer):
    """본사 은행 계좌 시리얼라이저"""
    bankcode_name = serializers.CharField(source='bankcode.name', read_only=True)
    depart_name = serializers.CharField(source='depart.name', read_only=True)

    class Meta:
        model = CompanyBankAccount
        fields = ('pk', 'company', 'depart', 'depart_name', 'bankcode', 'bankcode_name',
                  'order', 'alias_name', 'number', 'holder', 'open_date', 'note',
                  'is_hide', 'inactive')


class LedgerProjectBankAccountSerializer(serializers.ModelSerializer):
    """프로젝트 은행 계좌 시리얼라이저"""
    bankcode_name = serializers.CharField(source='bankcode.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = ProjectBankAccount
        fields = ('pk', 'project', 'project_name', 'bankcode', 'bankcode_name',
                  'order', 'alias_name', 'number', 'holder', 'open_date', 'note',
                  'is_hide', 'inactive', 'directpay', 'is_imprest')


# ============================================
# Bank Transaction Serializers
# ============================================

class CompanyBankTransactionSerializer(serializers.ModelSerializer):
    """본사 은행 거래 시리얼라이저"""
    bank_account_name = serializers.CharField(source='bank_account.alias_name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    is_balanced = serializers.SerializerMethodField(read_only=True)
    accounting_entries = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompanyBankTransaction
        fields = ('pk', 'transaction_id', 'company', 'bank_account', 'bank_account_name',
                  'deal_date', 'amount', 'transaction_type', 'transaction_type_display',
                  'content', 'note', 'creator', 'creator_name', 'created_at', 'updated_at',
                  'is_balanced', 'accounting_entries')
        read_only_fields = ('transaction_id', 'created_at', 'updated_at')

    def get_is_balanced(self, obj):
        """회계 분개 금액 균형 여부"""
        result = obj.validate_accounting_entries()
        return result['is_valid']

    def get_accounting_entries(self, obj):
        """연관된 회계 분개 목록"""
        entries = CompanyAccountingEntry.objects.filter(transaction_id=obj.transaction_id)
        return CompanyAccountingEntrySerializer(entries, many=True).data


class ProjectBankTransactionSerializer(serializers.ModelSerializer):
    """프로젝트 은행 거래 시리얼라이저"""
    bank_account_name = serializers.CharField(source='bank_account.alias_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    is_balanced = serializers.SerializerMethodField(read_only=True)
    accounting_entries = serializers.SerializerMethodField(read_only=True)
    contract_payment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectBankTransaction
        fields = ('pk', 'transaction_id', 'project', 'project_name', 'bank_account',
                  'bank_account_name', 'deal_date', 'amount', 'transaction_type',
                  'transaction_type_display', 'content', 'note', 'is_imprest',
                  'creator', 'creator_name', 'created_at', 'updated_at',
                  'is_balanced', 'accounting_entries', 'contract_payment')
        read_only_fields = ('transaction_id', 'created_at', 'updated_at')

    def get_is_balanced(self, obj):
        """회계 분개 금액 균형 여부"""
        result = obj.validate_accounting_entries()
        return result['is_valid']

    def get_accounting_entries(self, obj):
        """연관된 회계 분개 목록"""
        entries = ProjectAccountingEntry.objects.filter(transaction_id=obj.transaction_id)
        return ProjectAccountingEntrySerializer(entries, many=True).data

    def get_contract_payment(self, obj):
        """연관된 계약 결제 정보"""
        try:
            payment = ContractPayment.objects.get(transaction_id=obj.transaction_id)
            return ContractPaymentSerializer(payment).data
        except ContractPayment.DoesNotExist:
            return None


# ============================================
# Accounting Entry Serializers
# ============================================

class CompanyAccountingEntrySerializer(serializers.ModelSerializer):
    """본사 회계 분개 시리얼라이저"""
    sort_name = serializers.CharField(source='sort.name', read_only=True)
    account_d1_name = serializers.CharField(source='account_d1.name', read_only=True)
    account_d2_name = serializers.CharField(source='account_d2.name', read_only=True)
    account_d3_name = serializers.CharField(source='account_d3.name', read_only=True)
    evidence_type_display = serializers.CharField(source='get_evidence_type_display', read_only=True)

    class Meta:
        model = CompanyAccountingEntry
        fields = ('pk', 'transaction_id', 'transaction_type', 'company',
                  'sort', 'sort_name', 'account_code',
                  'account_d1', 'account_d1_name',
                  'account_d2', 'account_d2_name',
                  'account_d3', 'account_d3_name',
                  'amount', 'trader', 'evidence_type', 'evidence_type_display',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class ProjectAccountingEntrySerializer(serializers.ModelSerializer):
    """프로젝트 회계 분개 시리얼라이저"""
    sort_name = serializers.CharField(source='sort.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_account_d2_name = serializers.CharField(source='project_account_d2.name', read_only=True)
    project_account_d3_name = serializers.CharField(source='project_account_d3.name', read_only=True)
    evidence_type_display = serializers.CharField(source='get_evidence_type_display', read_only=True)

    class Meta:
        model = ProjectAccountingEntry
        fields = ('pk', 'transaction_id', 'transaction_type', 'project', 'project_name',
                  'sort', 'sort_name', 'account_code',
                  'project_account_d2', 'project_account_d2_name',
                  'project_account_d3', 'project_account_d3_name',
                  'amount', 'trader', 'evidence_type', 'evidence_type_display',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


# ============================================
# Contract Payment Serializers
# ============================================

class ContractPaymentSerializer(serializers.ModelSerializer):
    """계약 결제 시리얼라이저"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    contract_serial = serializers.CharField(source='contract.serial_number', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    special_purpose_type_display = serializers.CharField(source='get_special_purpose_type_display', read_only=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    payment_amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ContractPayment
        fields = ('pk', 'transaction_id', 'project', 'project_name',
                  'contract', 'contract_serial', 'installment_order',
                  'payment_type', 'payment_type_display',
                  'refund_contractor', 'refund_reason',
                  'is_special_purpose', 'special_purpose_type', 'special_purpose_type_display',
                  'creator', 'creator_name', 'created_at', 'updated_at',
                  'payment_amount')
        read_only_fields = ('created_at', 'updated_at')

    def get_payment_amount(self, obj):
        """결제 금액 조회"""
        return obj.get_payment_amount()


# ============================================
# Composite Serializers for Transaction Creation
# ============================================

class CompanyTransactionCreateSerializer(serializers.Serializer):
    """
    본사 거래 생성 복합 시리얼라이저

    은행 거래와 회계 분개를 한 번에 생성합니다.
    """
    # Bank Transaction 필드
    company = serializers.IntegerField()
    bank_account = serializers.IntegerField()
    deal_date = serializers.DateField()
    amount = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=['INCOME', 'OUTLAY'])
    content = serializers.CharField(max_length=100)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    # Accounting Entry 필드
    sort = serializers.IntegerField()
    account_d1 = serializers.IntegerField()
    account_d2 = serializers.IntegerField(required=False, allow_null=True)
    account_d3 = serializers.IntegerField(required=False, allow_null=True)
    account_code = serializers.CharField(max_length=10)
    trader = serializers.CharField(max_length=50)
    evidence_type = serializers.ChoiceField(choices=['0', '1', '2', '3', '4', '5'])

    @transaction.atomic
    def create(self, validated_data):
        from company.models import Company
        from ibs.models import AccountSort, AccountSubD1, AccountSubD2, AccountSubD3

        # 1. 은행 거래 생성
        bank_tx = CompanyBankTransaction.objects.create(
            company_id=validated_data['company'],
            bank_account_id=validated_data['bank_account'],
            deal_date=validated_data['deal_date'],
            amount=validated_data['amount'],
            transaction_type=validated_data['transaction_type'],
            content=validated_data['content'],
            note=validated_data.get('note', ''),
            creator=self.context.get('request').user if self.context.get('request') else None,
        )

        # 2. 회계 분개 생성
        accounting_entry = CompanyAccountingEntry.objects.create(
            transaction_id=bank_tx.transaction_id,
            transaction_type='COMPANY',
            company_id=validated_data['company'],
            sort_id=validated_data['sort'],
            account_d1_id=validated_data['account_d1'],
            account_d2_id=validated_data.get('account_d2'),
            account_d3_id=validated_data.get('account_d3'),
            account_code=validated_data['account_code'],
            amount=validated_data['amount'],
            trader=validated_data['trader'],
            evidence_type=validated_data['evidence_type'],
        )

        return {
            'bank_transaction': bank_tx,
            'accounting_entry': accounting_entry,
        }


class ProjectTransactionCreateSerializer(serializers.Serializer):
    """
    프로젝트 거래 생성 복합 시리얼라이저

    은행 거래, 회계 분개, 계약 결제를 한 번에 생성합니다.
    """
    # Bank Transaction 필드
    project = serializers.IntegerField()
    bank_account = serializers.IntegerField()
    deal_date = serializers.DateField()
    amount = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=['INCOME', 'OUTLAY'])
    content = serializers.CharField(max_length=100)
    note = serializers.CharField(required=False, allow_blank=True, default='')
    is_imprest = serializers.BooleanField(default=False)

    # Accounting Entry 필드
    sort = serializers.IntegerField()
    project_account_d2 = serializers.IntegerField()
    project_account_d3 = serializers.IntegerField(required=False, allow_null=True)
    account_code = serializers.CharField(max_length=10)
    trader = serializers.CharField(max_length=50)
    evidence_type = serializers.ChoiceField(choices=['0', '1', '2', '3', '4', '5'])

    # Contract Payment 필드 (선택적)
    contract = serializers.IntegerField(required=False, allow_null=True)
    installment_order = serializers.IntegerField(required=False, allow_null=True)
    payment_type = serializers.ChoiceField(
        choices=['PAYMENT', 'REFUND', 'ADJUSTMENT'],
        required=False,
        allow_null=True
    )
    refund_contractor = serializers.IntegerField(required=False, allow_null=True)
    refund_reason = serializers.CharField(required=False, allow_blank=True, default='')
    is_special_purpose = serializers.BooleanField(default=False)
    special_purpose_type = serializers.ChoiceField(
        choices=['IMPREST', 'LOAN', 'GUARANTEE', 'OTHERS', ''],
        required=False,
        allow_blank=True
    )

    @transaction.atomic
    def create(self, validated_data):
        # 1. 은행 거래 생성
        bank_tx = ProjectBankTransaction.objects.create(
            project_id=validated_data['project'],
            bank_account_id=validated_data['bank_account'],
            deal_date=validated_data['deal_date'],
            amount=validated_data['amount'],
            transaction_type=validated_data['transaction_type'],
            content=validated_data['content'],
            note=validated_data.get('note', ''),
            is_imprest=validated_data.get('is_imprest', False),
            creator=self.context.get('request').user if self.context.get('request') else None,
        )

        # 2. 회계 분개 생성
        accounting_entry = ProjectAccountingEntry.objects.create(
            transaction_id=bank_tx.transaction_id,
            transaction_type='PROJECT',
            project_id=validated_data['project'],
            sort_id=validated_data['sort'],
            project_account_d2_id=validated_data['project_account_d2'],
            project_account_d3_id=validated_data.get('project_account_d3'),
            account_code=validated_data['account_code'],
            amount=validated_data['amount'],
            trader=validated_data['trader'],
            evidence_type=validated_data['evidence_type'],
        )

        result = {
            'bank_transaction': bank_tx,
            'accounting_entry': accounting_entry,
        }

        # 3. 계약 결제 생성 (계약 정보가 있는 경우)
        if validated_data.get('contract'):
            contract_payment = ContractPayment.objects.create(
                transaction_id=bank_tx.transaction_id,
                project_id=validated_data['project'],
                contract_id=validated_data['contract'],
                installment_order_id=validated_data.get('installment_order'),
                payment_type=validated_data.get('payment_type', 'PAYMENT'),
                refund_contractor_id=validated_data.get('refund_contractor'),
                refund_reason=validated_data.get('refund_reason', ''),
                is_special_purpose=validated_data.get('is_special_purpose', False),
                special_purpose_type=validated_data.get('special_purpose_type', ''),
                creator=self.context.get('request').user if self.context.get('request') else None,
            )
            result['contract_payment'] = contract_payment

        return result
