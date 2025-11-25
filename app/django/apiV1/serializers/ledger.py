from django.db import transaction
from rest_framework import serializers

from ledger.models import (
    BankCode,
    CompanyBankAccount, ProjectBankAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
)
from payment.models import ContractPayment


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

    @staticmethod
    def get_is_balanced(obj):
        """회계 분개 금액 균형 여부"""
        result = obj.validate_accounting_entries()
        return result['is_valid']

    @staticmethod
    def get_accounting_entries(obj):
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

    class Meta:
        model = ProjectBankTransaction
        fields = ('pk', 'transaction_id', 'project', 'project_name', 'bank_account',
                  'bank_account_name', 'deal_date', 'amount', 'transaction_type',
                  'transaction_type_display', 'content', 'note', 'is_imprest',
                  'creator', 'creator_name', 'created_at', 'updated_at',
                  'is_balanced', 'accounting_entries')
        read_only_fields = ('transaction_id', 'created_at', 'updated_at')

    def get_is_balanced(self, obj):
        """회계 분개 금액 균형 여부"""
        result = obj.validate_accounting_entries()
        return result['is_valid']

    def get_accounting_entries(self, obj):
        """연관된 회계 분개 목록 (계약 결제 정보 포함)"""
        entries = ProjectAccountingEntry.objects.filter(
            transaction_id=obj.transaction_id
        ).select_related('contract_payment')
        return ProjectAccountingEntrySerializer(entries, many=True).data


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
        fields = ('pk', 'transaction_id', 'company',
                  'sort', 'sort_name',
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
    contract_payment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectAccountingEntry
        fields = ('pk', 'transaction_id', 'project', 'project_name',
                  'sort', 'sort_name',
                  'project_account_d2', 'project_account_d2_name',
                  'project_account_d3', 'project_account_d3_name',
                  'amount', 'trader', 'evidence_type', 'evidence_type_display',
                  'created_at', 'updated_at', 'contract_payment')
        read_only_fields = ('created_at', 'updated_at')

    @staticmethod
    def get_contract_payment(obj):
        """연관된 계약 결제 정보 (있는 경우)"""
        if hasattr(obj, 'contract_payment'):
            cp = obj.contract_payment
            return {
                'pk': cp.pk,
                'contract': cp.contract_id,
                'contract_serial': cp.contract.serial_number if cp.contract else None,
                'installment_order': cp.installment_order_id,
                'payment_type': cp.payment_type,
                'payment_type_display': cp.get_payment_type_display(),
                'is_special_purpose': cp.is_special_purpose,
                'special_purpose_type': cp.special_purpose_type,
            }
        return None


# ============================================
# Composite Serializers for Transaction Creation
# ============================================

class CompanyAccountingEntryInputSerializer(serializers.Serializer):
    """본사 회계분개 입력 시리얼라이저"""
    sort = serializers.IntegerField()
    account_d1 = serializers.IntegerField()
    account_d2 = serializers.IntegerField(required=False, allow_null=True)
    account_d3 = serializers.IntegerField(required=False, allow_null=True)
    amount = serializers.IntegerField()
    trader = serializers.CharField(max_length=50, required=False, allow_blank=True)
    evidence_type = serializers.ChoiceField(choices=['0', '1', '2', '3', '4', '5', '6'], required=False,
                                            allow_null=True)


class CompanyTransactionCreateSerializer(serializers.Serializer):
    """
    본사 거래 생성 복합 시리얼라이저

    은행 거래와 여러 회계 분개를 한 번에 생성합니다.
    """
    # Bank Transaction 필드
    company = serializers.IntegerField()
    bank_account = serializers.IntegerField()
    deal_date = serializers.DateField()
    amount = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=['INCOME', 'OUTLAY'])
    content = serializers.CharField(max_length=100)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    # Accounting Entries 필드 (배열)
    accounting_entries = CompanyAccountingEntryInputSerializer(many=True)

    def validate(self, attrs):
        """회계 분개 금액 합계 검증"""
        bank_amount = attrs['amount']
        entries_data = attrs['accounting_entries']

        # 회계 분개 금액 총합 계산
        entries_total = sum(entry['amount'] for entry in entries_data)

        if bank_amount != entries_total:
            raise serializers.ValidationError({
                'accounting_entries': f'회계 분개 금액 총합({entries_total:,}원)이 은행 거래 금액({bank_amount:,}원)과 일치하지 않습니다.'
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # 1. 회계분개 데이터 추출
        entries_data = validated_data.pop('accounting_entries')

        # 2. 은행 거래 생성
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

        # 3. 회계 분개 배열 생성
        accounting_entries = []
        for entry_data in entries_data:
            accounting_entry = CompanyAccountingEntry.objects.create(
                transaction_id=bank_tx.transaction_id,
                company_id=validated_data['company'],
                sort_id=entry_data['sort'],
                account_d1_id=entry_data['account_d1'],
                account_d2_id=entry_data.get('account_d2'),
                account_d3_id=entry_data.get('account_d3'),
                amount=entry_data['amount'],
                trader=entry_data.get('trader', ''),
                evidence_type=entry_data.get('evidence_type'),
            )
            accounting_entries.append(accounting_entry)

        return {
            'bank_transaction': bank_tx,
            'accounting_entries': accounting_entries,
        }


class ProjectAccountingEntryInputSerializer(serializers.Serializer):
    """프로젝트 회계분개 입력 시리얼라이저"""
    sort = serializers.IntegerField()
    project_account_d2 = serializers.IntegerField()
    project_account_d3 = serializers.IntegerField(required=False, allow_null=True)
    amount = serializers.IntegerField()
    trader = serializers.CharField(max_length=50, required=False, allow_blank=True)
    evidence_type = serializers.ChoiceField(choices=['0', '1', '2', '3', '4', '5', '6'], required=False,
                                            allow_null=True)

    # Contract Payment 필드 (선택적 - 이 회계분개가 계약 결제와 연결되는 경우)
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


class ProjectTransactionCreateSerializer(serializers.Serializer):
    """
    프로젝트 거래 생성 복합 시리얼라이저

    은행 거래, 여러 회계 분개, 계약 결제를 한 번에 생성합니다.
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

    # Accounting Entries 필드 (배열)
    accounting_entries = ProjectAccountingEntryInputSerializer(many=True)

    def validate(self, attrs):
        """회계 분개 금액 합계 검증"""
        bank_amount = attrs['amount']
        entries_data = attrs['accounting_entries']

        # 회계 분개 금액 총합 계산
        entries_total = sum(entry['amount'] for entry in entries_data)

        if bank_amount != entries_total:
            raise serializers.ValidationError({
                'accounting_entries': f'회계 분개 금액 총합({entries_total:,}원)이 은행 거래 금액({bank_amount:,}원)과 일치하지 않습니다.'
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # 1. 회계분개 데이터 추출
        entries_data = validated_data.pop('accounting_entries')

        # 2. 은행 거래 생성
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

        # 3. 회계 분개 배열 생성
        accounting_entries = []
        contract_payments = []

        for entry_data in entries_data:
            # 회계 분개 생성
            accounting_entry = ProjectAccountingEntry.objects.create(
                transaction_id=bank_tx.transaction_id,
                project_id=validated_data['project'],
                sort_id=entry_data['sort'],
                project_account_d2_id=entry_data['project_account_d2'],
                project_account_d3_id=entry_data.get('project_account_d3'),
                amount=entry_data['amount'],
                trader=entry_data.get('trader', ''),
                evidence_type=entry_data.get('evidence_type'),
            )
            accounting_entries.append(accounting_entry)

            # 계약 결제 생성 (계약 정보가 있는 경우)
            if entry_data.get('contract'):
                contract_payment = ContractPayment.objects.create(
                    accounting_entry=accounting_entry,  # AccountingEntry와 연결
                    project_id=validated_data['project'],
                    contract_id=entry_data['contract'],
                    installment_order_id=entry_data.get('installment_order'),
                    payment_type=entry_data.get('payment_type', 'PAYMENT'),
                    refund_contractor_id=entry_data.get('refund_contractor'),
                    refund_reason=entry_data.get('refund_reason', ''),
                    is_special_purpose=entry_data.get('is_special_purpose', False),
                    special_purpose_type=entry_data.get('special_purpose_type', ''),
                    creator=self.context.get('request').user if self.context.get('request') else None,
                )
                contract_payments.append(contract_payment)

        result = {
            'bank_transaction': bank_tx,
            'accounting_entries': accounting_entries,
        }

        # 계약 결제가 생성된 경우 포함
        if contract_payments:
            result['contract_payments'] = contract_payments

        return result
