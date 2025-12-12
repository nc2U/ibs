from django.db import transaction
from rest_framework import serializers

from ledger.models import (
    BankCode,
    CompanyAccount, ProjectAccount,
    CompanyBankAccount, ProjectBankAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    CompanyLedgerCalculation,
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
# Account Serializers
# ============================================

class CompanyAccountSerializer(serializers.ModelSerializer):
    """본사 계정 과목 시리얼라이저"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    computed_direction = serializers.SerializerMethodField(read_only=True)
    computed_direction_display = serializers.SerializerMethodField(read_only=True)
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    children_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompanyAccount
        fields = ('pk', 'code', 'name', 'description', 'parent', 'parent_name',
                  'depth', 'category', 'category_display', 'direction', 'direction_display',
                  'computed_direction', 'computed_direction_display',
                  'is_category_only', 'is_active', 'order',
                  'full_path', 'children_count')
        read_only_fields = ('depth',)

    @staticmethod
    def get_computed_direction(obj):
        """동적으로 계산된 거래 방향"""
        return obj.get_computed_direction()

    @staticmethod
    def get_computed_direction_display(obj):
        """동적으로 계산된 거래 방향의 표시 텍스트"""
        return obj.get_direction_display_computed()

    @staticmethod
    def get_children_count(obj):
        """하위 계정 수"""
        return obj.children.filter(is_active=True).count()


class ProjectAccountSerializer(serializers.ModelSerializer):
    """프로젝트 계정 과목 시리얼라이저"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    computed_direction = serializers.SerializerMethodField(read_only=True)
    computed_direction_display = serializers.SerializerMethodField(read_only=True)
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    children_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectAccount
        fields = ('pk', 'code', 'name', 'description', 'parent', 'parent_name',
                  'depth', 'category', 'category_display', 'direction', 'direction_display',
                  'computed_direction', 'computed_direction_display',
                  'is_category_only', 'is_active', 'order',
                  'is_payment', 'is_related_contract',
                  'full_path', 'children_count')
        read_only_fields = ('depth',)

    @staticmethod
    def get_computed_direction(obj):
        """동적으로 계산된 거래 방향"""
        return obj.get_computed_direction()

    @staticmethod
    def get_computed_direction_display(obj):
        """동적으로 계산된 거래 방향의 표시 텍스트"""
        return obj.get_direction_display_computed()

    @staticmethod
    def get_children_count(obj):
        """하위 계정 수"""
        return obj.children.filter(is_active=True).count()


class AccountSearchResultSerializer(serializers.Serializer):
    """계정 검색 결과 시리얼라이저"""
    pk = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    full_path = serializers.CharField()
    computed_direction = serializers.CharField()
    computed_direction_display = serializers.CharField()
    is_category_only = serializers.BooleanField()
    is_parent_of_matches = serializers.BooleanField(default=False)
    match_reason = serializers.CharField(default='직접 매치')

    # ProjectAccount 전용 필드
    is_payment = serializers.BooleanField(required=False)
    is_related_contract = serializers.BooleanField(required=False)


# ============================================
# Bank Transaction Serializers
# ============================================

class CompanyBankTransactionSerializer(serializers.ModelSerializer):
    """본사 은행 거래 시리얼라이저"""
    bank_account_name = serializers.CharField(source='bank_account.alias_name', read_only=True)
    sort_name = serializers.CharField(source='sort.name', read_only=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    is_balanced = serializers.SerializerMethodField(read_only=True)
    accounting_entries = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompanyBankTransaction
        fields = ('pk', 'transaction_id', 'company', 'bank_account', 'bank_account_name',
                  'deal_date', 'amount', 'sort', 'sort_name',
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


class CompanyLedgerCalculationSerializer(serializers.ModelSerializer):
    """본사 원장 정산 시리얼라이저"""
    creator_name = serializers.CharField(source='creator.username', read_only=True)

    class Meta:
        model = CompanyLedgerCalculation
        fields = ('pk', 'company', 'calculated', 'creator', 'creator_name',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class ProjectBankTransactionSerializer(serializers.ModelSerializer):
    """프로젝트 은행 거래 시리얼라이저"""
    bank_account_name = serializers.CharField(source='bank_account.alias_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    sort_name = serializers.CharField(source='sort.name', read_only=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    is_balanced = serializers.SerializerMethodField(read_only=True)
    accounting_entries = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectBankTransaction
        fields = ('pk', 'transaction_id', 'project', 'project_name', 'bank_account',
                  'bank_account_name', 'deal_date', 'amount', 'sort', 'sort_name',
                  'content', 'note', 'is_imprest',
                  'creator', 'creator_name', 'created_at', 'updated_at',
                  'is_balanced', 'accounting_entries')
        read_only_fields = ('transaction_id', 'created_at', 'updated_at')

    @staticmethod
    def get_is_balanced(obj):
        """회계 분개 금액 균형 여부"""
        result = obj.validate_accounting_entries()
        return result['is_valid']

    @staticmethod
    def get_accounting_entries(obj):
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
    sort = serializers.SerializerMethodField(read_only=True)
    sort_name = serializers.CharField(source='sort.name', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_full_path = serializers.CharField(source='account.get_full_path', read_only=True)
    affiliated_display = serializers.SerializerMethodField(read_only=True)
    evidence_type_display = serializers.CharField(source='get_evidence_type_display', read_only=True)

    class Meta:
        model = CompanyAccountingEntry
        fields = ('pk', 'transaction_id', 'company',
                  'sort', 'sort_name',
                  'account', 'account_name', 'account_code', 'account_full_path',
                  'affiliated', 'affiliated_display',
                  'amount', 'trader', 'evidence_type', 'evidence_type_display',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    @staticmethod
    def get_sort(obj):
        """BankTransaction의 sort ID 반환"""
        transaction = obj.related_transaction
        return transaction.sort_id if transaction else None

    @staticmethod
    def get_affiliated_display(obj):
        """관계회사/프로젝트 표시"""
        if obj.affiliated:
            return str(obj.affiliated)
        return None


class ProjectAccountingEntrySerializer(serializers.ModelSerializer):
    """프로젝트 회계 분개 시리얼라이저"""
    sort = serializers.SerializerMethodField(read_only=True)
    sort_name = serializers.CharField(source='sort.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_full_path = serializers.CharField(source='account.get_full_path', read_only=True)
    affiliated_display = serializers.SerializerMethodField(read_only=True)
    evidence_type_display = serializers.CharField(source='get_evidence_type_display', read_only=True)
    contract_payment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectAccountingEntry
        fields = ('pk', 'transaction_id', 'project', 'project_name',
                  'sort', 'sort_name',
                  'account', 'account_name', 'account_code', 'account_full_path',
                  'affiliated', 'affiliated_display',
                  'amount', 'trader', 'evidence_type', 'evidence_type_display',
                  'created_at', 'updated_at', 'contract_payment')
        read_only_fields = ('created_at', 'updated_at')

    @staticmethod
    def get_sort(obj):
        """BankTransaction의 sort ID 반환"""
        transaction = obj.related_transaction
        return transaction.sort_id if transaction else None

    @staticmethod
    def get_affiliated_display(obj):
        """관계회사/프로젝트 표시"""
        if obj.affiliated:
            return str(obj.affiliated)
        return None

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
    """본사 회계분개 입력 시리얼라이저 (sort는 BankTransaction의 sort를 자동 사용)"""
    account = serializers.IntegerField()
    amount = serializers.IntegerField()
    trader = serializers.CharField(max_length=50, required=False, allow_blank=True)
    evidence_type = serializers.ChoiceField(choices=['0', '1', '2', '3', '4', '5', '6'], required=False,
                                            allow_null=True)
    affiliated = serializers.IntegerField(required=False, allow_null=True)


class CompanyCompositeTransactionSerializer(serializers.Serializer):
    """
    본사 복합 거래 시리얼라이저

    은행 거래와 여러 회계 분개를 한 번에 생성/수정합니다.
    프론트엔드 거래 관리 UI에서 사용합니다.
    """
    # Bank Transaction 필드
    company = serializers.IntegerField()
    bank_account = serializers.IntegerField()
    deal_date = serializers.DateField()
    sort = serializers.IntegerField(help_text='거래구분 ID (1=입금, 2=출금)')
    amount = serializers.IntegerField()
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
    def create(self, validated_data, **kwargs):
        # 1. 회계분개 데이터 추출
        entries_data = validated_data.pop('accounting_entries')

        # 2. 은행 거래 생성
        bank_tx = CompanyBankTransaction.objects.create(
            company_id=validated_data['company'],
            bank_account_id=validated_data['bank_account'],
            deal_date=validated_data['deal_date'],
            sort_id=validated_data['sort'],
            amount=validated_data['amount'],
            content=validated_data['content'],
            note=validated_data.get('note', ''),
            creator=kwargs.get('creator'),  # creator를 kwargs에서 가져옴
        )

        # 3. 회계 분개 배열 생성
        accounting_entries = []
        for entry_data in entries_data:
            accounting_entry = CompanyAccountingEntry.objects.create(
                transaction_id=bank_tx.transaction_id,
                company_id=validated_data['company'],
                account_id=entry_data['account'],
                trader=entry_data.get('trader', ''),
                amount=entry_data['amount'],
                evidence_type=entry_data.get('evidence_type'),
                affiliated_id=entry_data.get('affiliated'),
            )
            accounting_entries.append(accounting_entry)

        return {
            'bank_transaction': bank_tx,
            'accounting_entries': accounting_entries,
        }

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        기존 본사 거래 업데이트

        회계분개 수정 방식:
        1. entries_data에 'id' 포함: 기존 분개 수정
        2. entries_data에 'id' 없음: 새 분개 생성
        3. 기존에 있던 분개가 entries_data에 없으면: 삭제
        """
        # 1. 회계분개 데이터 추출
        entries_data = validated_data.pop('accounting_entries', None)

        # 2. 은행 거래 업데이트
        instance.company_id = validated_data.get('company', instance.company_id)
        instance.bank_account_id = validated_data.get('bank_account', instance.bank_account_id)
        instance.deal_date = validated_data.get('deal_date', instance.deal_date)
        instance.sort_id = validated_data.get('sort', instance.sort_id)
        instance.amount = validated_data.get('amount', instance.amount)
        instance.content = validated_data.get('content', instance.content)
        instance.note = validated_data.get('note', instance.note)
        instance.save()

        # 3. 회계분개 업데이트 (제공된 경우)
        if entries_data is not None:
            # 기존 회계분개 조회
            existing_entries = CompanyAccountingEntry.objects.filter(
                transaction_id=instance.transaction_id
            )

            # 업데이트할 분개 pk 추출
            update_entry_pks = [entry_data.get('pk') for entry_data in entries_data if entry_data.get('pk')]

            # 삭제할 분개들 (entries_data에 없는 기존 분개들)
            entries_to_delete = existing_entries.exclude(pk__in=update_entry_pks)
            for entry in entries_to_delete:
                entry.delete()

            accounting_entries = []

            for entry_data in entries_data:
                entry_pk = entry_data.get('pk')

                if entry_pk:
                    # 기존 회계분개 수정
                    try:
                        accounting_entry = CompanyAccountingEntry.objects.get(
                            pk=entry_pk,
                            transaction_id=instance.transaction_id
                        )

                        # 회계분개 필드 업데이트
                        accounting_entry.company_id = instance.company_id  # 부모 거래의 company 정보와 동기화
                        accounting_entry.account_id = entry_data['account']
                        accounting_entry.trader = entry_data.get('trader', '')
                        accounting_entry.amount = entry_data['amount']
                        accounting_entry.evidence_type = entry_data.get('evidence_type')
                        accounting_entry.affiliated_id = entry_data.get('affiliated')
                        accounting_entry.save()

                    except CompanyAccountingEntry.DoesNotExist:
                        # ID가 잘못된 경우 새로 생성
                        accounting_entry = self._create_accounting_entry(instance, entry_data)
                else:
                    # 새 회계분개 생성
                    accounting_entry = self._create_accounting_entry(instance, entry_data)

                accounting_entries.append(accounting_entry)

        result = {
            'bank_transaction': instance,
            'accounting_entries': accounting_entries if entries_data else [],
        }

        return result

    @staticmethod
    def _create_accounting_entry(instance, entry_data):
        """회계분개 생성 헬퍼 메서드 (sort는 BankTransaction과 동기화)"""
        return CompanyAccountingEntry.objects.create(
            transaction_id=instance.transaction_id,
            company_id=instance.company_id,
            account_id=entry_data['account'],
            trader=entry_data.get('trader', ''),
            amount=entry_data['amount'],
            evidence_type=entry_data.get('evidence_type'),
            affiliated_id=entry_data.get('affiliated'),
        )


class ProjectAccountingEntryInputSerializer(serializers.Serializer):
    """프로젝트 회계분개 입력 시리얼라이저"""
    sort = serializers.IntegerField()
    account = serializers.IntegerField()
    affiliated = serializers.IntegerField(required=False, allow_null=True)
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


class ProjectCompositeTransactionSerializer(serializers.Serializer):
    """
    프로젝트 복합 거래 시리얼라이저

    은행 거래, 여러 회계 분개, 계약 결제를 한 번에 생성/수정합니다.
    프론트엔드 거래 관리 UI에서 사용합니다.
    """
    # Bank Transaction 필드
    project = serializers.IntegerField()
    bank_account = serializers.IntegerField()
    deal_date = serializers.DateField()
    amount = serializers.IntegerField()
    sort = serializers.IntegerField(help_text='거래구분 ID (1=입금, 2=출금)')
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
            sort_id=validated_data['sort'],
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
                account_id=entry_data['account'],
                affiliated_id=entry_data.get('affiliated'),
                amount=entry_data['amount'],
                trader=entry_data.get('trader', ''),
                evidence_type=entry_data.get('evidence_type'),
            )
            accounting_entries.append(accounting_entry)

            # ContractPayment 베이스 인스턴스 자동 생성 (is_payment=True인 경우)
            if accounting_entry.account and accounting_entry.account.is_payment:
                # 계약 정보가 제공된 경우: 완전한 인스턴스 생성
                if entry_data.get('contract'):
                    contract_payment = ContractPayment.objects.create(
                        accounting_entry=accounting_entry,
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
                else:
                    # 계약 정보 없는 경우: 베이스 인스턴스만 생성 (나중에 관리자에서 세부 정보 입력)
                    contract_payment = ContractPayment.objects.create(
                        accounting_entry=accounting_entry,
                        project_id=validated_data['project'],
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

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        기존 프로젝트 거래 업데이트

        회계분개 수정 방식:
        1. entries_data에 'id' 포함: 기존 분개 수정
        2. entries_data에 'id' 없음: 새 분개 생성
        3. 기존에 있던 분개가 entries_data에 없으면: 삭제

        ContractPayment 자동 처리:
        - is_payment 변경 감지하여 자동 생성/수정/삭제
        """
        # 1. 회계분개 데이터 추출
        entries_data = validated_data.pop('accounting_entries', None)

        # 2. 은행 거래 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 3. 회계분개 업데이트 (제공된 경우)
        if entries_data is not None:
            # 기존 회계분개 조회
            existing_entries = ProjectAccountingEntry.objects.filter(
                transaction_id=instance.transaction_id
            ).select_related('account')

            # 업데이트할 분개 ID 추출
            update_entry_ids = [entry_data.get('id') for entry_data in entries_data if entry_data.get('id')]

            # 삭제할 분개들 (entries_data에 없는 기존 분개들)
            entries_to_delete = existing_entries.exclude(id__in=update_entry_ids)
            for entry in entries_to_delete:
                # ContractPayment가 있으면 함께 삭제됨 (CASCADE)
                entry.delete()

            accounting_entries = []
            contract_payments = []

            for entry_data in entries_data:
                entry_id = entry_data.get('id')

                if entry_id:
                    # 기존 회계분개 수정
                    try:
                        accounting_entry = ProjectAccountingEntry.objects.get(
                            id=entry_id,
                            transaction_id=instance.transaction_id
                        )

                        # 이전 is_payment 상태 저장
                        old_is_payment = (
                                accounting_entry.account and
                                accounting_entry.account.is_payment
                        )

                        # 회계분개 필드 업데이트
                        # accounting_entry.sort_id = instance.sort_id # CompanyAccountingEntry 모델에 sort_id 필드가 없어 불필요함
                        accounting_entry.account_id = entry_data['account']
                        accounting_entry.affiliated_id = entry_data.get('affiliated')
                        accounting_entry.amount = entry_data['amount']
                        accounting_entry.trader = entry_data.get('trader', '')
                        accounting_entry.evidence_type = entry_data.get('evidence_type')
                        accounting_entry.save()

                        # 새로운 is_payment 상태 확인
                        new_is_payment = (
                                accounting_entry.account and
                                accounting_entry.account.is_payment
                        )

                        # ContractPayment 처리
                        has_contract_payment = hasattr(accounting_entry, 'contract_payment')

                        if not old_is_payment and new_is_payment:
                            # False → True: 새 ContractPayment 생성
                            if not has_contract_payment:
                                contract_payment = self._create_contract_payment(
                                    accounting_entry, instance.project_id, entry_data
                                )
                                contract_payments.append(contract_payment)

                        elif old_is_payment and not new_is_payment:
                            # True → False: Signal이 mismatch 플래그 설정 처리
                            pass  # Signal에서 자동 처리

                        elif old_is_payment and new_is_payment and has_contract_payment:
                            # True → True: 기존 ContractPayment 업데이트 (계약 정보가 있는 경우)
                            if entry_data.get('contract'):
                                contract_payment = accounting_entry.contract_payment
                                contract_payment.contract_id = entry_data['contract']
                                contract_payment.installment_order_id = entry_data.get('installment_order')
                                contract_payment.payment_type = entry_data.get('payment_type', 'PAYMENT')
                                contract_payment.refund_contractor_id = entry_data.get('refund_contractor')
                                contract_payment.refund_reason = entry_data.get('refund_reason', '')
                                contract_payment.is_special_purpose = entry_data.get('is_special_purpose', False)
                                contract_payment.special_purpose_type = entry_data.get('special_purpose_type', '')
                                contract_payment.save()
                                contract_payments.append(contract_payment)

                    except ProjectAccountingEntry.DoesNotExist:
                        # ID가 잘못된 경우 새로 생성
                        accounting_entry = self._create_accounting_entry(instance, entry_data)
                        contract_payment = self._handle_new_accounting_entry_payment(
                            accounting_entry, instance.project_id, entry_data
                        )
                        if contract_payment:
                            contract_payments.append(contract_payment)
                else:
                    # 새 회계분개 생성
                    accounting_entry = self._create_accounting_entry(instance, entry_data)
                    contract_payment = self._handle_new_accounting_entry_payment(
                        accounting_entry, instance.project_id, entry_data
                    )
                    if contract_payment:
                        contract_payments.append(contract_payment)

                accounting_entries.append(accounting_entry)

        result = {
            'bank_transaction': instance,
            'accounting_entries': accounting_entries if entries_data else [],
        }

        # 계약 결제가 생성/수정된 경우 포함
        if entries_data and contract_payments:
            result['contract_payments'] = contract_payments

        return result

    @staticmethod
    def _create_accounting_entry(instance, entry_data):
        """회계분개 생성 헬퍼 메서드"""
        return ProjectAccountingEntry.objects.create(
            transaction_id=instance.transaction_id,
            project_id=instance.project_id,
            sort_id=entry_data['sort'],
            account_id=entry_data['account'],
            affiliated_id=entry_data.get('affiliated'),
            amount=entry_data['amount'],
            trader=entry_data.get('trader', ''),
            evidence_type=entry_data.get('evidence_type'),
        )

    def _create_contract_payment(self, accounting_entry, project_id, entry_data):
        """ContractPayment 생성 헬퍼 메서드"""
        if entry_data.get('contract'):
            return ContractPayment.objects.create(
                accounting_entry=accounting_entry,
                project_id=project_id,
                contract_id=entry_data['contract'],
                installment_order_id=entry_data.get('installment_order'),
                payment_type=entry_data.get('payment_type', 'PAYMENT'),
                refund_contractor_id=entry_data.get('refund_contractor'),
                refund_reason=entry_data.get('refund_reason', ''),
                is_special_purpose=entry_data.get('is_special_purpose', False),
                special_purpose_type=entry_data.get('special_purpose_type', ''),
                creator=self.context.get('request').user if self.context.get('request') else None,
            )
        else:
            return ContractPayment.objects.create(
                accounting_entry=accounting_entry,
                project_id=project_id,
                creator=self.context.get('request').user if self.context.get('request') else None,
            )

    def _handle_new_accounting_entry_payment(self, accounting_entry, project_id, entry_data):
        """새 회계분개의 ContractPayment 처리 헬퍼 메서드"""
        if accounting_entry.account and accounting_entry.account.is_payment:
            return self._create_contract_payment(accounting_entry, project_id, entry_data)
        return None
