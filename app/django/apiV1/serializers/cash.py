from django.db import transaction
from rest_framework import serializers

from cash.models import BankCode, CompanyBankAccount, ProjectBankAccount, CashBook, \
    ProjectCashBook, CompanyCashBookCalculation, ProjectCashBookCalculation
from ibs.models import AccountSubD1, AccountSubD2, AccountSubD3
from project.models import Project
from .contract import SimpleUserSerializer


# Cash --------------------------------------------------------------------------
class BankCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankCode
        fields = ('pk', 'code', 'name')


class CompanyBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyBankAccount
        fields = ('pk', 'company', 'depart', 'bankcode', 'alias_name', 'number',
                  'holder', 'open_date', 'note', 'is_hide', 'inactive')


class BalanceByAccountSerializer(serializers.ModelSerializer):
    bank_acc = serializers.CharField()
    bank_num = serializers.CharField()
    date_inc = serializers.IntegerField()
    date_out = serializers.IntegerField()
    inc_sum = serializers.IntegerField()
    out_sum = serializers.IntegerField()
    balance = serializers.IntegerField()

    class Meta:
        model = ProjectCashBook
        fields = ('bank_acc', 'bank_num', 'date_inc', 'date_out', 'inc_sum', 'out_sum', 'balance')


class SepItemsInCashBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBook
        fields = ('pk', 'account_d1', 'account_d2', 'account_d3', 'separated',
                  'content', 'trader', 'income', 'outlay', 'evidence', 'note')


class CashBookSerializer(serializers.ModelSerializer):
    sort_desc = serializers.SerializerMethodField(read_only=True)
    account_d1_desc = serializers.SerializerMethodField(read_only=True)
    account_d2_desc = serializers.SerializerMethodField(read_only=True)
    account_d3_desc = serializers.SerializerMethodField(read_only=True)
    project_desc = serializers.SerializerMethodField(read_only=True)
    sepItems = SepItemsInCashBookSerializer(many=True, read_only=True)
    bank_account_desc = serializers.SerializerMethodField(read_only=True)
    evidence_desc = serializers.CharField(source='get_evidence_display', read_only=True)
    updator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = CashBook
        fields = (
            'pk', 'company', 'sort', 'sort_desc', 'account_d1', 'account_d1_desc', 'account_d2',
            'account_d2_desc', 'account_d3', 'account_d3_desc', 'project', 'project_desc'
            , 'is_return', 'is_separate', 'separated', 'sepItems', 'content', 'trader', 'bank_account',
            'bank_account_desc', 'income', 'outlay', 'evidence', 'evidence_desc', 'note', 'deal_date', 'updator')

    @staticmethod
    def get_sort_desc(obj):
        return obj.sort.name

    @staticmethod
    def get_account_d1_desc(obj):
        return obj.account_d1.name if obj.account_d1 else None

    @staticmethod
    def get_account_d2_desc(obj):
        return obj.account_d2.name if obj.account_d2 else None

    @staticmethod
    def get_account_d3_desc(obj):
        return obj.account_d3.name if obj.account_d3 else None

    @staticmethod
    def get_project_desc(obj):
        return obj.project.name if obj.project else None

    @staticmethod
    def get_bank_account_desc(obj):
        return obj.bank_account.alias_name

    @transaction.atomic
    def create(self, validated_data):
        # 1. 거래정보 입력
        cashbook = CashBook.objects.create(**validated_data)

        # 2. sep 정보 확인
        sep_data = self.initial_data.get('sepData')
        if sep_data:
            sep_cashbook_account_d1 = AccountSubD1.objects.get(pk=sep_data.get('account_d1'))
            sep_cashbook_account_d2 = AccountSubD2.objects.get(pk=sep_data.get('account_d2'))
            sep_cashbook_account_d3 = AccountSubD3.objects.get(pk=sep_data.get('account_d3'))
            try:
                sep_cashbook_project = Project.objects.get(pk=sep_data.get('project'))
            except Project.DoesNotExist:
                sep_cashbook_project = None
            sep_cashbook_is_return = sep_data.get('is_return')
            sep_cashbook_content = sep_data.get('content')
            sep_cashbook_trader = sep_data.get('trader')
            sep_cashbook_income = sep_data.get('income')
            sep_cashbook_outlay = sep_data.get('outlay')
            sep_cashbook_evidence = sep_data.get('evidence')
            sep_cashbook_note = sep_data.get('note')
            if not sep_data.get('pk'):
                sep_cashbook = CashBook(company=cashbook.company,
                                        sort=cashbook.sort,
                                        account_d1=sep_cashbook_account_d1,
                                        account_d2=sep_cashbook_account_d2,
                                        account_d3=sep_cashbook_account_d3,
                                        project=sep_cashbook_project,
                                        is_return=sep_cashbook_is_return,
                                        separated=cashbook,
                                        content=sep_cashbook_content,
                                        trader=sep_cashbook_trader,
                                        bank_account=cashbook.bank_account,
                                        income=sep_cashbook_income,
                                        outlay=sep_cashbook_outlay,
                                        evidence=sep_cashbook_evidence,
                                        note=sep_cashbook_note,
                                        deal_date=cashbook.deal_date)
                sep_cashbook.save()
            else:
                sep_cashbook = CashBook.objects.get(pk=sep_data.get('pk'))
                sep_cashbook.company = cashbook.company
                sep_cashbook.sort = cashbook.sort
                sep_cashbook.account_d1 = sep_cashbook_account_d1
                sep_cashbook.account_d2 = sep_cashbook_account_d2
                sep_cashbook.account_d3 = sep_cashbook_account_d3
                sep_cashbook.project = sep_cashbook_project
                sep_cashbook.is_return = sep_cashbook_is_return
                sep_cashbook.separated = cashbook
                sep_cashbook.content = sep_cashbook_content
                sep_cashbook.trader = sep_cashbook_trader
                sep_cashbook.bank_account = cashbook.bank_account
                sep_cashbook.income = sep_cashbook_income
                sep_cashbook.outlay = sep_cashbook_outlay
                sep_cashbook.evidence = sep_cashbook_evidence
                sep_cashbook.note = sep_cashbook_note
                sep_cashbook.deal_date = cashbook.deal_date
                sep_cashbook.save()
        return cashbook

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        instance.account_d1 = validated_data.get('account_d1', instance.account_d1)
        instance.account_d2 = validated_data.get('account_d2', instance.account_d2)
        instance.account_d3 = validated_data.get('account_d3', instance.account_d3)
        instance.project = validated_data.get('project', instance.project)
        instance.bank_account = validated_data.get('bank_account', instance.bank_account)

        # updator 설정
        if 'updator' in self.context.get('request', {}).__dict__.get('_data', {}):
            instance.updator = self.context['request'].user
        elif hasattr(self.context.get('request'), 'user'):
            instance.updator = self.context['request'].user

        instance.save()

        # 2. sep 정보 확인 후 저장
        sep_data = self.initial_data.get('sepData')
        if sep_data:
            sep_cashbook_account_d1 = AccountSubD1.objects.get(pk=sep_data.get('account_d1'))
            sep_cashbook_account_d2 = AccountSubD2.objects.get(pk=sep_data.get('account_d2'))
            sep_cashbook_account_d3 = AccountSubD3.objects.get(pk=sep_data.get('account_d3'))
            try:
                sep_cashbook_project = Project.objects.get(pk=sep_data.get('project'))
            except Project.DoesNotExist:
                sep_cashbook_project = None
            sep_cashbook_is_return = sep_data.get('is_return')
            sep_cashbook_content = sep_data.get('content')
            sep_cashbook_trader = sep_data.get('trader')
            sep_cashbook_income = sep_data.get('income')
            sep_cashbook_outlay = sep_data.get('outlay')
            sep_cashbook_evidence = sep_data.get('evidence')
            sep_cashbook_note = sep_data.get('note')
            if not sep_data.get('pk'):
                sep_cashbook = CashBook(company=instance.company,
                                        sort=instance.sort,
                                        account_d1=sep_cashbook_account_d1,
                                        account_d2=sep_cashbook_account_d2,
                                        account_d3=sep_cashbook_account_d3,
                                        project=sep_cashbook_project,
                                        is_return=sep_cashbook_is_return,
                                        separated=instance,
                                        content=sep_cashbook_content,
                                        trader=sep_cashbook_trader,
                                        bank_account=instance.bank_account,
                                        income=sep_cashbook_income,
                                        outlay=sep_cashbook_outlay,
                                        evidence=sep_cashbook_evidence,
                                        note=sep_cashbook_note,
                                        deal_date=instance.deal_date,
                                        creator=self.context['request'].user if hasattr(self.context.get('request'),
                                                                                        'user') else None)
                sep_cashbook.save()
            else:
                sep_cashbook = CashBook.objects.get(pk=sep_data.get('pk'))
                sep_cashbook.company = instance.company
                sep_cashbook.sort = instance.sort
                sep_cashbook.account_d1 = sep_cashbook_account_d1
                sep_cashbook.account_d2 = sep_cashbook_account_d2
                sep_cashbook.account_d3 = sep_cashbook_account_d3
                sep_cashbook.project = sep_cashbook_project
                sep_cashbook.is_return = sep_cashbook_is_return
                sep_cashbook.separated = instance
                sep_cashbook.content = sep_cashbook_content
                sep_cashbook.trader = sep_cashbook_trader
                sep_cashbook.bank_account = instance.bank_account
                sep_cashbook.income = sep_cashbook_income
                sep_cashbook.outlay = sep_cashbook_outlay
                sep_cashbook.evidence = sep_cashbook_evidence
                sep_cashbook.note = sep_cashbook_note
                sep_cashbook.deal_date = instance.deal_date
                # 분리 기록 수정시에도 updator 설정
                if hasattr(self.context.get('request'), 'user'):
                    sep_cashbook.updator = self.context['request'].user
                sep_cashbook.save()
        return instance


class CompanyCashCalcSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = CompanyCashBookCalculation
        fields = ('pk', 'company', 'calculated', 'creator')


class CompanyLastDealDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBook
        fields = ('deal_date',)


class ProjectBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectBankAccount
        fields = ('pk', 'project', 'bankcode', 'alias_name', 'number', 'holder', 'open_date',
                  'note', 'is_hide', 'inactive', 'directpay', 'is_imprest')


class SepItemsInPrCashBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'project', 'project_account_d2', 'project_account_d3', 'separated',
                  'content', 'trader', 'income', 'outlay', 'evidence', 'note',)


class PrBalanceByAccountSerializer(serializers.ModelSerializer):
    bank_acc = serializers.CharField()
    bank_num = serializers.CharField()
    date_inc = serializers.IntegerField()
    date_out = serializers.IntegerField()
    inc_sum = serializers.IntegerField()
    out_sum = serializers.IntegerField()
    balance = serializers.IntegerField()

    class Meta:
        model = ProjectCashBook
        fields = ('bank_acc', 'bank_num', 'date_inc', 'date_out', 'inc_sum', 'out_sum', 'balance')


class ProjectCashBookSerializer(serializers.ModelSerializer):
    sort_desc = serializers.SlugField(source='sort', read_only=True)
    project_account_d2_desc = serializers.SlugField(source='project_account_d2', read_only=True)
    project_account_d3_desc = serializers.SlugField(source='project_account_d3', read_only=True)
    bank_account_desc = serializers.SlugField(source='bank_account', read_only=True)
    evidence_desc = serializers.CharField(source='get_evidence_display', read_only=True)
    sepItems = SepItemsInPrCashBookSerializer(many=True, read_only=True)
    updator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'project', 'sort', 'sort_desc', 'project_account_d2',
                  'project_account_d2_desc', 'project_account_d3', 'project_account_d3_desc',
                  'is_separate', 'separated', 'is_imprest', 'sepItems', 'contract', 'installment_order',
                  'refund_contractor', 'content', 'trader', 'bank_account', 'bank_account_desc',
                  'income', 'outlay', 'evidence', 'evidence_desc', 'note', 'deal_date', 'updator')

    def validate(self, attrs):
        """
        분리 항목 금액 합계 검증

        sepData가 있는 경우, 자식 항목들의 금액 합계가 부모 금액과 일치하는지 검증
        """
        sep_data = self.initial_data.get('sepData')

        if sep_data:
            # sepData가 리스트인 경우 (다중 분리 항목)
            if isinstance(sep_data, list):
                children_income = sum(int(child.get('income', 0) or 0) for child in sep_data)
                children_outlay = sum(int(child.get('outlay', 0) or 0) for child in sep_data)
            # sepData가 단일 객체인 경우 (현재 구현)
            else:
                children_income = int(sep_data.get('income', 0) or 0)
                children_outlay = int(sep_data.get('outlay', 0) or 0)

            parent_income = attrs.get('income', 0) or 0
            parent_outlay = attrs.get('outlay', 0) or 0

            # 금액 불일치 검증
            if children_income != parent_income or children_outlay != parent_outlay:
                error_msg = []
                if children_outlay != parent_outlay:
                    error_msg.append(
                        f'출금 합계 불일치: 자식(₩{children_outlay:,}) ≠ 부모(₩{parent_outlay:,})'
                    )
                if children_income != parent_income:
                    error_msg.append(
                        f'입금 합계 불일치: 자식(₩{children_income:,}) ≠ 부모(₩{parent_income:,})'
                    )
                raise serializers.ValidationError({
                    'sepData': ' | '.join(error_msg)
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        pr_cashbook = ProjectCashBook.objects.create(**validated_data)

        # 2. sep 정보 확인
        sep_data = self.initial_data.get('sepData')
        if sep_data:
            sep_pr_cashbook_project_account_d2 = sep_data.get('project_account_d2')
            sep_pr_cashbook_project_account_d3 = sep_data.get('project_account_d3')
            sep_pr_cashbook_is_imprest = sep_data.get('is_imprest')
            sep_pr_cashbook_contract = sep_data.get('contract')
            sep_pr_cashbook_installment_order = sep_data.get('installment_order')
            sep_pr_cashbook_content = sep_data.get('content')
            sep_pr_cashbook_trader = sep_data.get('trader')
            sep_pr_cashbook_income = sep_data.get('income')
            sep_pr_cashbook_outlay = sep_data.get('outlay')
            sep_pr_cashbook_evidence = sep_data.get('evidence')
            sep_pr_cashbook_note = sep_data.get('note')
            if not sep_data.get('pk'):
                sep_pr_cashbook = ProjectCashBook(project=pr_cashbook.project,
                                                  sort=pr_cashbook.sort,
                                                  project_account_d2_id=sep_pr_cashbook_project_account_d2,
                                                  project_account_d3_id=sep_pr_cashbook_project_account_d3,
                                                  is_separate=True,  # 명시적으로 True 설정
                                                  separated=pr_cashbook,
                                                  is_imprest=sep_pr_cashbook_is_imprest,
                                                  contract_id=sep_pr_cashbook_contract,
                                                  installment_order_id=sep_pr_cashbook_installment_order,
                                                  content=sep_pr_cashbook_content,
                                                  trader=sep_pr_cashbook_trader,
                                                  bank_account=pr_cashbook.bank_account,
                                                  income=sep_pr_cashbook_income,
                                                  outlay=sep_pr_cashbook_outlay,
                                                  evidence=sep_pr_cashbook_evidence,
                                                  note=sep_pr_cashbook_note,
                                                  deal_date=pr_cashbook.deal_date)
                sep_pr_cashbook.save()
            else:
                sep_pr_cashbook = ProjectCashBook.objects.get(pk=sep_data.get('pk'))
                sep_pr_cashbook.project = pr_cashbook.project
                sep_pr_cashbook.sort = pr_cashbook.sort
                sep_pr_cashbook.project_account_d2_id = sep_pr_cashbook_project_account_d2
                sep_pr_cashbook.project_account_d3_id = sep_pr_cashbook_project_account_d3
                sep_pr_cashbook.is_separate = True  # 명시적으로 True 설정
                sep_pr_cashbook.separated = pr_cashbook
                sep_pr_cashbook.is_imprest = sep_pr_cashbook_is_imprest
                sep_pr_cashbook.contract_id = sep_pr_cashbook_contract
                sep_pr_cashbook.installment_order_id = sep_pr_cashbook_installment_order
                sep_pr_cashbook.content = sep_pr_cashbook_content
                sep_pr_cashbook.trader = sep_pr_cashbook_trader
                sep_pr_cashbook.bank_account = pr_cashbook.bank_account
                sep_pr_cashbook.income = sep_pr_cashbook_income
                sep_pr_cashbook.outlay = sep_pr_cashbook_outlay
                sep_pr_cashbook.evidence = sep_pr_cashbook_evidence
                sep_pr_cashbook.note = sep_pr_cashbook_note
                sep_pr_cashbook.deal_date = pr_cashbook.deal_date
                sep_pr_cashbook.save()
        return pr_cashbook

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        instance.project_account_d2 = validated_data.get('project_account_d2', instance.project_account_d2)
        instance.project_account_d3 = validated_data.get('project_account_d3', instance.project_account_d3)
        instance.contract = validated_data.get('contract', instance.contract)
        instance.installment_order = validated_data.get('installment_order', instance.installment_order)
        instance.refund_contractor = validated_data.get('refund_contractor', instance.refund_contractor)
        instance.bank_account = validated_data.get('bank_account', instance.bank_account)

        # updator 설정
        if hasattr(self.context.get('request'), 'user'):
            instance.updator = self.context['request'].user

        instance.save()

        # 2. sep 정보 확인
        sep_data = self.initial_data.get('sepData')
        if sep_data:
            sep_pr_cashbook_project_account_d2 = sep_data.get('project_account_d2')
            sep_pr_cashbook_project_account_d3 = sep_data.get('project_account_d3')
            sep_pr_cashbook_is_imprest = sep_data.get('is_imprest')
            sep_pr_cashbook_contract = sep_data.get('contract')
            sep_pr_cashbook_installment_order = sep_data.get('installment_order')
            sep_pr_cashbook_content = sep_data.get('content')
            sep_pr_cashbook_trader = sep_data.get('trader')
            sep_pr_cashbook_income = sep_data.get('income')
            sep_pr_cashbook_outlay = sep_data.get('outlay')
            sep_pr_cashbook_evidence = sep_data.get('evidence')
            sep_pr_cashbook_note = sep_data.get('note')
            if not sep_data.get('pk'):
                sep_pr_cashbook = ProjectCashBook(project=instance.project,
                                                  sort=instance.sort,
                                                  project_account_d2_id=sep_pr_cashbook_project_account_d2,
                                                  project_account_d3_id=sep_pr_cashbook_project_account_d3,
                                                  is_separate=True,  # 명시적으로 True 설정
                                                  separated=instance,
                                                  is_imprest=sep_pr_cashbook_is_imprest,
                                                  contract_id=sep_pr_cashbook_contract,
                                                  installment_order_id=sep_pr_cashbook_installment_order,
                                                  content=sep_pr_cashbook_content,
                                                  trader=sep_pr_cashbook_trader,
                                                  bank_account=instance.bank_account,
                                                  income=sep_pr_cashbook_income,
                                                  outlay=sep_pr_cashbook_outlay,
                                                  evidence=sep_pr_cashbook_evidence,
                                                  note=sep_pr_cashbook_note,
                                                  deal_date=instance.deal_date,
                                                  creator=self.context['request'].user if hasattr(
                                                      self.context.get('request'), 'user') else None)
                sep_pr_cashbook.save()
            else:
                sep_pr_cashbook = ProjectCashBook.objects.get(pk=sep_data.get('pk'))
                sep_pr_cashbook.project = instance.project
                sep_pr_cashbook.sort = instance.sort
                sep_pr_cashbook.project_account_d2_id = sep_pr_cashbook_project_account_d2
                sep_pr_cashbook.project_account_d3_id = sep_pr_cashbook_project_account_d3
                sep_pr_cashbook.is_separate = True  # 명시적으로 True 설정
                sep_pr_cashbook.separated = instance
                sep_pr_cashbook.is_imprest = sep_pr_cashbook_is_imprest
                sep_pr_cashbook.contract_id = sep_pr_cashbook_contract
                sep_pr_cashbook.installment_order_id = sep_pr_cashbook_installment_order
                sep_pr_cashbook.content = sep_pr_cashbook_content
                sep_pr_cashbook.trader = sep_pr_cashbook_trader
                sep_pr_cashbook.bank_account = instance.bank_account
                sep_pr_cashbook.income = sep_pr_cashbook_income
                sep_pr_cashbook.outlay = sep_pr_cashbook_outlay
                sep_pr_cashbook.evidence = sep_pr_cashbook_evidence
                sep_pr_cashbook.note = sep_pr_cashbook_note
                sep_pr_cashbook.deal_date = instance.deal_date
                # 분리 기록 수정시에도 updator 설정
                if hasattr(self.context.get('request'), 'user'):
                    sep_pr_cashbook.updator = self.context['request'].user
                sep_pr_cashbook.save()
        return instance


class ProjectCashCalcSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ProjectCashBookCalculation
        fields = ('pk', 'project', 'calculated', 'creator')


class ProjectLastDealDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCashBook
        fields = ('deal_date',)
