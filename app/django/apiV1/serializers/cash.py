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
        fields = ('pk', 'account_d1', 'account_d2', 'account_d3', 'project', 'is_return',
                  'separated', 'content', 'trader', 'income', 'outlay', 'evidence', 'note')


class CashBookSerializer(serializers.ModelSerializer):
    sort_desc = serializers.SerializerMethodField(read_only=True)
    account_d1_desc = serializers.SerializerMethodField(read_only=True)
    account_d2_desc = serializers.SerializerMethodField(read_only=True)
    account_d3_desc = serializers.SerializerMethodField(read_only=True)
    project_desc = serializers.SerializerMethodField(read_only=True)
    sepItems = SepItemsInCashBookSerializer(many=True, read_only=True)
    bank_account_desc = serializers.SerializerMethodField(read_only=True)
    evidence_desc = serializers.CharField(source='get_evidence_display', read_only=True)
    has_children = serializers.SerializerMethodField(read_only=True)
    updator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = CashBook
        fields = (
            'pk', 'company', 'sort', 'sort_desc', 'account_d1', 'account_d1_desc', 'account_d2',
            'account_d2_desc', 'account_d3', 'account_d3_desc', 'project', 'project_desc'
            , 'is_return', 'is_separate', 'separated', 'sepItems', 'has_children', 'content', 'trader', 'bank_account',
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

    @staticmethod
    def get_has_children(obj):
        """부모 레코드가 자식 레코드를 가지고 있는지 확인"""
        return CashBook.objects.filter(separated=obj).exists()

    def to_representation(self, instance):
        """
        응답에 합계 검증 결과 포함
        """
        data = super().to_representation(instance)

        # 부모 레코드이고 분리 항목이 있는 경우 합계 검증
        if instance.is_separate and not instance.separated:
            children = CashBook.objects.filter(separated=instance)
            if children.exists():
                children_income = sum(child.income or 0 for child in children)
                children_outlay = sum(child.outlay or 0 for child in children)
                parent_income = instance.income or 0
                parent_outlay = instance.outlay or 0

                data['is_balanced'] = (
                    children_income == parent_income and
                    children_outlay == parent_outlay
                )
                data['balance_info'] = {
                    'parent_income': parent_income,
                    'parent_outlay': parent_outlay,
                    'children_income': children_income,
                    'children_outlay': children_outlay,
                }
            else:
                data['is_balanced'] = True
        else:
            data['is_balanced'] = True

        return data

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
                                        is_separate=False,  # 자식 레코드는 False
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
                sep_cashbook.is_separate = False  # 자식 레코드는 False
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
        # creator는 수정 불가 필드이므로 validated_data에서 제거
        validated_data.pop('creator', None)

        # is_return이 None이면 제거 (BooleanField는 None을 허용하지 않음)
        if validated_data.get('is_return') is None:
            validated_data.pop('is_return', None)

        # 각 필드를 개별적으로 업데이트 (creator는 보존)
        instance.deal_date = validated_data.get('deal_date', instance.deal_date)
        instance.sort = validated_data.get('sort', instance.sort)
        instance.account_d1 = validated_data.get('account_d1', instance.account_d1)
        instance.account_d2 = validated_data.get('account_d2', instance.account_d2)
        instance.account_d3 = validated_data.get('account_d3', instance.account_d3)
        instance.project = validated_data.get('project', instance.project)
        instance.content = validated_data.get('content', instance.content)
        instance.trader = validated_data.get('trader', instance.trader)
        instance.bank_account = validated_data.get('bank_account', instance.bank_account)
        instance.income = validated_data.get('income', instance.income)
        instance.outlay = validated_data.get('outlay', instance.outlay)
        instance.evidence = validated_data.get('evidence', instance.evidence)
        instance.note = validated_data.get('note', instance.note)

        # is_separate와 separated 업데이트
        # 자식 레코드(separated가 있는 경우)는 is_separate를 False로 강제
        new_separated = validated_data.get('separated', instance.separated)
        if new_separated is not None:
            # 자식 레코드인 경우 is_separate는 항상 False
            instance.is_separate = False
            instance.separated = new_separated
        else:
            # 부모 레코드인 경우 is_separate 업데이트 허용
            instance.is_separate = validated_data.get('is_separate', instance.is_separate)
            instance.separated = None
        if 'is_return' in validated_data:
            instance.is_return = validated_data['is_return']

        # is_return이 여전히 None이면 False로 설정 (BooleanField 기본값)
        if instance.is_return is None:
            instance.is_return = False

        # creator가 None이면 현재 사용자로 설정 (데이터 무결성 보장)
        if instance.creator is None and hasattr(self.context.get('request'), 'user'):
            instance.creator = self.context['request'].user

        # updator 설정
        if hasattr(self.context.get('request'), 'user'):
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
                                        is_separate=False,  # 자식 레코드는 False
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
                sep_cashbook.is_separate = False  # 자식 레코드는 False
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
    project_account_d2_desc = serializers.SlugField(source='project_account_d2', read_only=True)
    project_account_d3_desc = serializers.SlugField(source='project_account_d3', read_only=True)
    evidence_desc = serializers.CharField(source='get_evidence_display', read_only=True)

    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'project', 'project_account_d2', 'project_account_d2_desc',
                  'project_account_d3', 'project_account_d3_desc', 'separated', 'is_imprest',
                  'contract', 'installment_order', 'content', 'trader', 'income', 'outlay',
                  'evidence', 'evidence_desc', 'note',)


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
    updator = SimpleUserSerializer(read_only=True)
    has_children = serializers.SerializerMethodField(read_only=True)
    sepItems = SepItemsInPrCashBookSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'project', 'sort', 'sort_desc', 'project_account_d2',
                  'project_account_d2_desc', 'project_account_d3', 'project_account_d3_desc',
                  'is_separate', 'separated', 'sepItems', 'is_imprest', 'contract', 'installment_order',
                  'refund_contractor', 'content', 'trader', 'bank_account', 'bank_account_desc',
                  'income', 'outlay', 'evidence', 'evidence_desc', 'note', 'deal_date', 'updator', 'has_children')

    def get_has_children(self, obj):
        """부모 레코드가 자식을 가지고 있는지 확인"""
        # separated가 null인 레코드만 부모 레코드 (is_separate 값과 무관)
        if obj.separated is not None:
            return False
        # sepItems의 개수를 확인
        return obj.sepItems.count() > 0

    def to_representation(self, instance):
        """
        응답에 합계 검증 결과 포함
        """
        data = super().to_representation(instance)

        # 부모 레코드이고 분리 항목이 있는 경우 합계 검증
        if instance.is_separate and not instance.separated:
            children = ProjectCashBook.objects.filter(separated=instance)
            if children.exists():
                children_income = sum(child.income or 0 for child in children)
                children_outlay = sum(child.outlay or 0 for child in children)
                parent_income = instance.income or 0
                parent_outlay = instance.outlay or 0

                data['is_balanced'] = (
                    children_income == parent_income and
                    children_outlay == parent_outlay
                )
                data['balance_info'] = {
                    'parent_income': parent_income,
                    'parent_outlay': parent_outlay,
                    'children_income': children_income,
                    'children_outlay': children_outlay,
                }
            else:
                data['is_balanced'] = True
        else:
            data['is_balanced'] = True

        return data

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
                                                  is_separate=False,  # 자식 레코드는 False
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
                sep_pr_cashbook.is_separate = False  # 자식 레코드는 False
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
        # creator는 수정 불가 필드이므로 validated_data에서 제거
        validated_data.pop('creator', None)

        # 각 필드를 개별적으로 업데이트 (creator는 보존)
        instance.deal_date = validated_data.get('deal_date', instance.deal_date)
        instance.sort = validated_data.get('sort', instance.sort)
        instance.project_account_d2 = validated_data.get('project_account_d2', instance.project_account_d2)
        instance.project_account_d3 = validated_data.get('project_account_d3', instance.project_account_d3)

        # is_separate와 separated 업데이트
        # 자식 레코드(separated가 있는 경우)는 is_separate를 False로 강제
        new_separated = validated_data.get('separated', instance.separated)
        if new_separated is not None:
            # 자식 레코드인 경우 is_separate는 항상 False
            instance.is_separate = False
            instance.separated = new_separated
        else:
            # 부모 레코드인 경우 is_separate 업데이트 허용
            instance.is_separate = validated_data.get('is_separate', instance.is_separate)
            instance.separated = None

        instance.is_imprest = validated_data.get('is_imprest', instance.is_imprest)
        instance.contract = validated_data.get('contract', instance.contract)
        instance.installment_order = validated_data.get('installment_order', instance.installment_order)
        instance.refund_contractor = validated_data.get('refund_contractor', instance.refund_contractor)
        instance.content = validated_data.get('content', instance.content)
        instance.trader = validated_data.get('trader', instance.trader)
        instance.bank_account = validated_data.get('bank_account', instance.bank_account)
        instance.income = validated_data.get('income', instance.income)
        instance.outlay = validated_data.get('outlay', instance.outlay)
        instance.evidence = validated_data.get('evidence', instance.evidence)
        instance.note = validated_data.get('note', instance.note)

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
                                                  is_separate=False,  # 자식 레코드는 False
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
                sep_pr_cashbook.is_separate = False  # 자식 레코드는 False
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
