import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum


# ============================================
# Bank Account Models - 은행 계좌 모델
# ============================================

class BankCode(models.Model):
    """
    은행 코드

    금융기관 코드를 관리합니다.
    """
    code = models.CharField(max_length=3, unique=True, verbose_name='은행코드')
    name = models.CharField(max_length=20, db_index=True, verbose_name='은행명')

    class Meta:
        verbose_name = '은행 코드'
        verbose_name_plural = '은행 코드'

    def __str__(self):
        return self.name


class BankAccount(models.Model):
    """
    은행 계좌 추상 모델

    본사 및 프로젝트 은행 계좌의 공통 필드를 정의합니다.
    """
    order = models.PositiveSmallIntegerField('순서', null=True, blank=True)
    bankcode = models.ForeignKey(BankCode, on_delete=models.PROTECT, verbose_name='거래은행')
    alias_name = models.CharField('계좌별칭', max_length=20, db_index=True)
    number = models.CharField('계좌번호', max_length=30, blank=True)
    holder = models.CharField('예금주', max_length=20, blank=True)
    open_date = models.DateField('개설일자', null=True, blank=True)
    note = models.CharField('비고', max_length=50, blank=True)
    is_hide = models.BooleanField('숨기기 여부', default=False)
    inactive = models.BooleanField('비활성 여부', default=False)

    class Meta:
        abstract = True
        ordering = ['order', 'id']

    def __str__(self):
        return self.alias_name


class CompanyBankAccount(BankAccount):
    """
    본사 은행 계좌

    회사 본사의 은행 계좌 정보를 관리합니다.
    """
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name='회사정보',
                                related_name='com_bank_accounts')
    depart = models.ForeignKey('company.Department', on_delete=models.SET_NULL,
                               null=True, blank=True, verbose_name='관리부서', related_name='com_bank_accounts')

    class Meta:
        ordering = ['order', 'id']
        verbose_name = '본사 관리계좌'
        verbose_name_plural = '본사 관리계좌'


class ProjectBankAccount(BankAccount):
    """
    프로젝트 은행 계좌

    프로젝트별 은행 계좌 정보를 관리합니다.
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트',
                                related_name='proj_bank_accounts')
    directpay = models.BooleanField('용역비 직불 여부', default=False)
    is_imprest = models.BooleanField('운영비 계좌 여부', default=False)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = '프로젝트 관리계좌'
        verbose_name_plural = '프로젝트 관리계좌'


# ============================================
# Banking Domain - 은행 거래 도메인
# ============================================

class BankTransaction(models.Model):
    """
    은행 거래 추상 모델

    Banking Domain의 핵심 모델로, 실제 은행 계좌의 입출금 거래를 표현합니다.
    UUID 기반 식별자를 통해 다른 도메인과 느슨하게 결합됩니다.
    """
    # Primary Identifier
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True,
                                      verbose_name='거래 ID', help_text='도메인 간 연결을 위한 UUID 식별자')

    # 거래 정보
    deal_date = models.DateField(verbose_name='거래일자')
    amount = models.PositiveBigIntegerField(verbose_name='금액', help_text='거래 금액 (양수)')
    transaction_type = models.CharField(max_length=10, choices=[('INCOME', '입금'), ('OUTLAY', '출금')],
                                        verbose_name='거래 유형')
    content = models.CharField(max_length=100, verbose_name='적요', help_text='거래 내용 요약')
    note = models.TextField(blank=True, verbose_name='비고', help_text='추가 설명')

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    creator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='생성자')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['deal_date']),
            models.Index(fields=['deal_date', 'transaction_type']),
        ]

    def clean(self):
        """모델 유효성 검증"""
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': '거래 금액은 0보다 커야 합니다.'})

        if self.deal_date and self.deal_date > timezone.now().date():
            raise ValidationError({'deal_date': '미래 날짜로 거래를 생성할 수 없습니다.'})

    def save(self, *args, **kwargs):
        """저장 전 유효성 검증"""
        self.full_clean()
        super().save(*args, **kwargs)

    def validate_accounting_entries(self):
        """
        이 거래에 대한 AccountingEntry의 금액 합계 검증

        Returns:
            dict: {'is_valid': bool, 'bank_amount': int, 'accounting_total': int, 'difference': int}
        """
        # 하위 클래스에서 구현해야 함
        raise NotImplementedError('하위 클래스에서 구현해야 합니다.')

    @property
    def is_balanced(self):
        """금액 균형 여부 (간편 체크)"""
        result = self.validate_accounting_entries()
        return result['is_valid']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount:,}원 ({self.deal_date})"


class CompanyBankTransaction(BankTransaction):
    """
    본사 은행 거래

    회사 본사의 은행 거래를 관리합니다.
    """
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name='회사')
    bank_account = models.ForeignKey(CompanyBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')

    class Meta:
        verbose_name = '본사 은행 거래'
        verbose_name_plural = '본사 은행 거래'
        ordering = ['-deal_date', '-created_at']
        indexes = [
            models.Index(fields=['bank_account', 'deal_date']),
        ]

    def validate_accounting_entries(self):
        """
        본사 회계 분개 금액 합계 검증

        Returns:
            dict: 검증 결과
        """
        entries = CompanyAccountingEntry.objects.filter(transaction_id=self.transaction_id)
        accounting_total = sum(e.amount for e in entries) if entries.exists() else 0
        difference = self.amount - accounting_total

        return {
            'is_valid': difference == 0,
            'bank_amount': self.amount,
            'accounting_total': accounting_total,
            'difference': difference,
            'entry_count': entries.count(),
        }


class ProjectBankTransaction(BankTransaction):
    """
    프로젝트 은행 거래

    프로젝트별 은행 거래를 관리합니다.
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    bank_account = models.ForeignKey(ProjectBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')
    is_imprest = models.BooleanField(default=False, verbose_name='운영비 여부', help_text='프로젝트 운영비 계정 거래 여부')

    class Meta:
        verbose_name = '프로젝트 은행 거래'
        verbose_name_plural = '프로젝트 은행 거래'
        ordering = ['-deal_date', '-created_at']
        indexes = [
            models.Index(fields=['bank_account', 'deal_date']),
        ]

    def validate_accounting_entries(self):
        """
        프로젝트 회계 분개 금액 합계 검증

        Returns:
            dict: 검증 결과
        """
        entries = ProjectAccountingEntry.objects.filter(transaction_id=self.transaction_id)
        accounting_total = sum(e.amount for e in entries) if entries.exists() else 0
        difference = self.amount - accounting_total

        return {
            'is_valid': difference == 0,
            'bank_amount': self.amount,
            'accounting_total': accounting_total,
            'difference': difference,
            'entry_count': entries.count(),
        }


# ============================================
# Accounting Domain - 회계 분개 도메인
# ============================================

class AccountingEntry(models.Model):
    """
    회계 분개 추상 모델

    Accounting Domain의 핵심 모델로, 은행 거래에 대한 회계 분류 정보를 표현합니다.
    transaction_id를 통해 BankTransaction과 느슨하게 연결됩니다.

    일반 거래: BankTransaction 1개 → AccountingEntry 1개 (금액 동일)
    분할 거래: BankTransaction 1개 → AccountingEntry N개 (금액 합계 일치)
    """
    # Banking Domain 연결 (UUID 참조)
    transaction_id = models.UUIDField(db_index=True, verbose_name='거래 ID',
                                      help_text='BankTransaction.transaction_id 참조')
    transaction_type = models.CharField(max_length=10, choices=[('COMPANY', 'CompanyBankTransaction'),
                                                                ('PROJECT', 'ProjectBankTransaction')],
                                        verbose_name='거래 유형')

    # 회계 분류
    sort = models.ForeignKey('ibs.AccountSort', on_delete=models.CASCADE, verbose_name='계정구분', help_text='수입/지출 구분')
    account_code = models.CharField(max_length=10, verbose_name='계정코드', help_text='회계 계정 코드')

    # 금액 (분할 거래 지원)
    amount = models.PositiveBigIntegerField(verbose_name='금액', help_text='이 회계 분개의 금액 (분할 시 일부 금액)')

    # 거래자
    trader = models.CharField(max_length=50, verbose_name='거래처', help_text='거래 상대방')

    # 증빙
    evidence_type = models.CharField(
        max_length=1,
        choices=[
            ('0', '세금계산서'),
            ('1', '계산서(면세)'),
            ('2', '신용/체크카드 매출전표'),
            ('3', '현금영수증'),
            ('4', '원천징수영수증/지급명세서'),
            ('5', '지로용지 및 청구서')
        ],
        verbose_name='증빙종류')

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['account_code', 'created_at']),
            models.Index(fields=['sort', 'evidence_type']),
            models.Index(fields=['transaction_type', 'account_code']),
        ]

    @property
    def related_transaction(self):
        """연관된 BankTransaction 조회"""
        if self.transaction_type == 'COMPANY':
            return CompanyBankTransaction.objects.filter(
                transaction_id=self.transaction_id
            ).first()
        else:
            return ProjectBankTransaction.objects.filter(
                transaction_id=self.transaction_id
            ).first()

    def __str__(self):
        return f"{self.content} - {self.trader}"


class CompanyAccountingEntry(AccountingEntry):
    """
    본사 회계 분개

    본사 거래에 대한 회계 분개 정보를 관리합니다.
    본사 계정 체계(d1/d2/d3)를 사용합니다.
    """
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name='회사')

    # 본사 계정 체계
    account_d1 = models.ForeignKey('ibs.AccountSubD1', on_delete=models.CASCADE, verbose_name='계정 대분류')
    account_d2 = models.ForeignKey('ibs.AccountSubD2', on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='계정 중분류')
    account_d3 = models.ForeignKey('ibs.AccountSubD3', on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='계정 소분류')

    class Meta:
        verbose_name = '본사 회계 분개'
        verbose_name_plural = '본사 회계 분개'
        ordering = ['-created_at']


class ProjectAccountingEntry(AccountingEntry):
    """
    프로젝트 회계 분개

    프로젝트 거래에 대한 회계 분개 정보를 관리합니다.
    프로젝트 계정 체계(d2/d3)를 사용합니다.
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')

    # 프로젝트 계정 체계
    project_account_d2 = models.ForeignKey('ibs.ProjectAccountD2',
                                           on_delete=models.CASCADE, verbose_name='프로젝트 계정 중분류')
    project_account_d3 = models.ForeignKey('ibs.ProjectAccountD3', on_delete=models.SET_NULL,
                                           null=True, blank=True, verbose_name='프로젝트 계정 소분류')

    class Meta:
        verbose_name = '프로젝트 회계 분개'
        verbose_name_plural = '프로젝트 회계 분개'
        ordering = ['-created_at']


# ============================================
# Contract Domain - 계약 결제 도메인
# ============================================

class ContractPayment(models.Model):
    """
    계약 결제

    프로젝트의 분양 계약에 대한 결제 정보를 관리합니다.
    ProjectBankTransaction과 연결되어 계약자의 납부, 환불, 조정 등을 추적합니다.
    """
    # Banking Domain 연결
    transaction_id = models.UUIDField(unique=True, db_index=True, verbose_name='거래 ID',
                                      help_text='ProjectBankTransaction.transaction_id 참조')

    # 계약 정보
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    contract = models.ForeignKey('contract.Contract', on_delete=models.CASCADE, verbose_name='계약', help_text='분양 계약')
    installment_order = models.ForeignKey('payment.InstallmentPaymentOrder', on_delete=models.SET_NULL,
                                          null=True, blank=True, verbose_name='납부회차', help_text='분할 납부 회차 정보')

    # 결제 유형
    payment_type = models.CharField(max_length=10,
                                    choices=[('PAYMENT', '납부'), ('REFUND', '환불'), ('ADJUSTMENT', '조정'), ],
                                    verbose_name='결제 유형')

    # 환불 정보
    refund_contractor = models.ForeignKey('contract.Contractor', on_delete=models.SET_NULL,
                                          null=True, blank=True, verbose_name='환불 계약자', help_text='환불 시 대상 계약자')
    refund_reason = models.CharField(max_length=100, blank=True, verbose_name='환불 사유')

    # 특수 목적
    is_special_purpose = models.BooleanField(default=False, verbose_name='특수 목적 여부')
    special_purpose_type = models.CharField(max_length=10, blank=True,
                                            choices=[('IMPREST', '운영비'), ('LOAN', '대여금'), ('GUARANTEE', '보증금'),
                                                     ('OTHERS', '기타')], verbose_name='특수 목적 유형')

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    creator = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='생성자'
    )

    class Meta:
        verbose_name = '계약 결제'
        verbose_name_plural = '계약 결제'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['contract', 'payment_type']),
            models.Index(fields=['installment_order', 'created_at']),
        ]

    @property
    def related_transaction(self):
        """연관된 ProjectBankTransaction 조회"""
        return ProjectBankTransaction.objects.filter(
            transaction_id=self.transaction_id
        ).first()

    def get_payment_amount(self):
        """결제 금액 조회"""
        tx = self.related_transaction
        return tx.amount if tx else 0

    def calculate_late_penalty(self):
        """
        연체료 계산

        납부 회차의 납부기한을 기준으로 연체료를 계산합니다.
        실제 계산 로직은 _utils.payment_adjustment 모듈에서 처리합니다.
        """
        if self.payment_type != 'PAYMENT' or not self.installment_order:
            return None

        # TODO: Phase 2에서 실제 계산 로직 구현
        # from _utils.payment_adjustment import calculate_late_penalty
        # return calculate_late_penalty(self)
        return {
            'is_late': False,
            'penalty_amount': 0,
            'message': '연체료 계산 로직 구현 예정'
        }

    def is_prepayment_eligible(self):
        """
        선납 할인 대상 여부 확인

        Returns:
            bool: 선납 할인 대상이면 True
        """
        return (
                self.payment_type == 'PAYMENT' and
                self.installment_order and
                hasattr(self.installment_order, 'is_prep_discount') and
                self.installment_order.is_prep_discount
        )

    def clean(self):
        """모델 유효성 검증"""
        # 환불 시 환불계약자 필수
        if self.payment_type == 'REFUND' and not self.refund_contractor:
            raise ValidationError({
                'refund_contractor': '환불 시 환불계약자를 지정해야 합니다.'
            })

        # 계약의 프로젝트와 일치 확인
        if self.contract and self.contract.project_id != self.project_id:
            raise ValidationError({
                'contract': '계약의 프로젝트와 일치하지 않습니다.'
            })

        # 납부회차의 프로젝트와 일치 확인
        if self.installment_order and self.installment_order.project_id != self.project_id:
            raise ValidationError({
                'installment_order': '납부회차의 프로젝트와 일치하지 않습니다.'
            })

    def save(self, *args, **kwargs):
        """저장 전 유효성 검증"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.contract} - {self.get_payment_type_display()} ({self.get_payment_amount():,}원)"


# ============================================
# Split Domain - 거래 분할 도메인
# ============================================

class TransactionSplit(models.Model):
    """
    거래 분할

    하나의 은행 거래를 여러 회계 계정으로 분할하여 관리합니다.
    예: 100만원 입금을 50만원(매출), 30만원(선수금), 20만원(기타수입)으로 분할
    """
    # 원거래 참조
    parent_transaction_id = models.UUIDField(
        db_index=True,
        verbose_name='원거래 ID',
        help_text='분할 대상 BankTransaction의 transaction_id'
    )

    parent_transaction_type = models.CharField(
        max_length=10,
        choices=[
            ('COMPANY', 'CompanyBankTransaction'),
            ('PROJECT', 'ProjectBankTransaction'),
        ],
        verbose_name='원거래 유형'
    )

    # 분할 메타데이터
    split_reason = models.CharField(
        max_length=200,
        verbose_name='분할 사유',
        help_text='거래를 분할하는 이유'
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='총 금액',
        help_text='분할 항목의 합계 (원거래 금액과 일치해야 함)'
    )

    split_count = models.PositiveSmallIntegerField(
        verbose_name='분할 개수',
        help_text='분할 항목 개수 (최소 2개)'
    )

    # 분할 상태
    status = models.CharField(
        max_length=10,
        default='DRAFT',
        choices=[
            ('DRAFT', '임시저장'),
            ('CONFIRMED', '확정'),
            ('CANCELLED', '취소'),
        ],
        verbose_name='분할 상태'
    )

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    creator = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='생성자'
    )

    class Meta:
        verbose_name = '거래 분할'
        verbose_name_plural = '거래 분할'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['parent_transaction_id']),
            models.Index(fields=['status']),
        ]

    @property
    def parent_transaction(self):
        """부모 거래 조회"""
        if self.parent_transaction_type == 'COMPANY':
            return CompanyBankTransaction.objects.filter(
                transaction_id=self.parent_transaction_id
            ).first()
        else:
            return ProjectBankTransaction.objects.filter(
                transaction_id=self.parent_transaction_id
            ).first()

    def confirm_split(self):
        """
        분할 확정 및 회계 분개 생성

        임시저장 상태의 분할을 확정하고, 각 분할 항목에 대해
        AccountingEntry를 생성합니다.

        Raises:
            ValidationError: 임시저장 상태가 아니거나 분할 항목이 없는 경우
        """
        if self.status != 'DRAFT':
            raise ValidationError('임시저장 상태에서만 확정할 수 있습니다.')

        if not self.split_items.exists():
            raise ValidationError('분할 항목이 없습니다.')

        # 분할 상태를 확정으로 변경
        self.status = 'CONFIRMED'
        self.save()

        # 각 분할 항목에 대해 회계 분개 생성
        for item in self.split_items.all():
            item.create_accounting_entry()

    def clean(self):
        """모델 유효성 검증"""
        # 분할 개수 검증
        if self.split_count is not None and self.split_count < 2:
            raise ValidationError({
                'split_count': '분할 개수는 최소 2개 이상이어야 합니다.'
            })

        # 분할 항목 합계 검증 (업데이트 시에만)
        if self.pk:
            split_total = self.split_items.aggregate(
                total=Sum('amount')
            )['total'] or 0

            if split_total != self.total_amount:
                raise ValidationError({
                    'total_amount': f'분할 항목의 합계({split_total:,})가 총액({self.total_amount:,})과 일치하지 않습니다.'
                })

    def save(self, *args, **kwargs):
        """저장 전 유효성 검증 (생성 시에만)"""
        if not self.pk:  # 생성 시에만 검증 (업데이트는 clean에서)
            if self.split_count is not None and self.split_count < 2:
                raise ValidationError('분할 개수는 최소 2개 이상이어야 합니다.')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"거래 분할 {self.id} - {self.split_count}개 항목 ({self.get_status_display()})"


class TransactionSplitItem(models.Model):
    """
    거래 분할 항목

    TransactionSplit의 개별 분할 항목을 표현합니다.
    각 항목은 서로 다른 회계 계정에 배분됩니다.
    """
    split = models.ForeignKey(
        TransactionSplit,
        on_delete=models.CASCADE,
        related_name='split_items',
        verbose_name='거래 분할'
    )

    sequence = models.PositiveSmallIntegerField(
        verbose_name='순서',
        help_text='분할 항목의 표시 순서'
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='금액',
        help_text='이 분할 항목의 금액'
    )

    # 회계 정보
    account_code = models.CharField(
        max_length=10,
        verbose_name='계정코드',
        help_text='이 분할 항목의 회계 계정 코드'
    )

    content = models.CharField(
        max_length=100,
        verbose_name='적요',
        help_text='이 분할 항목의 거래 내용'
    )

    trader = models.CharField(
        max_length=50,
        verbose_name='거래처',
        help_text='이 분할 항목의 거래 상대방'
    )

    note = models.TextField(
        blank=True,
        verbose_name='비고'
    )

    # 생성된 회계 분개 참조
    accounting_entry_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='회계 분개 ID',
        help_text='생성된 AccountingEntry의 ID'
    )

    class Meta:
        verbose_name = '거래 분할 항목'
        verbose_name_plural = '거래 분할 항목'
        ordering = ['sequence']
        unique_together = [['split', 'sequence']]

    def create_accounting_entry(self):
        """
        회계 분개 생성

        이 분할 항목에 대한 AccountingEntry를 생성합니다.
        부모 거래 유형(Company/Project)에 따라 적절한 모델을 선택합니다.

        Returns:
            AccountingEntry: 생성된 회계 분개 객체
        """
        parent_tx = self.split.parent_transaction

        if not parent_tx:
            raise ValidationError('부모 거래를 찾을 수 없습니다.')

        if self.split.parent_transaction_type == 'COMPANY':
            # 본사 회계 분개 생성
            # TODO: Phase 2에서 실제 account_d1/d2/d3 매핑 로직 구현
            entry = CompanyAccountingEntry.objects.create(
                transaction_id=self.split.parent_transaction_id,
                transaction_type='COMPANY',
                company=parent_tx.company,
                sort_id=1,  # TODO: 실제 sort 매핑
                account_code=self.account_code,
                amount=self.amount,  # ✅ 분할 항목의 금액
                content=self.content,
                trader=self.trader,
                note=self.note,
                evidence_type='0',  # TODO: 실제 증빙 유형 매핑
                account_d1_id=1,  # TODO: 실제 계정 매핑
            )
        else:
            # 프로젝트 회계 분개 생성
            # TODO: Phase 2에서 실제 project_account_d2/d3 매핑 로직 구현
            entry = ProjectAccountingEntry.objects.create(
                transaction_id=self.split.parent_transaction_id,
                transaction_type='PROJECT',
                project=parent_tx.project,
                sort_id=1,  # TODO: 실제 sort 매핑
                account_code=self.account_code,
                amount=self.amount,  # ✅ 분할 항목의 금액
                content=self.content,
                trader=self.trader,
                note=self.note,
                evidence_type='0',  # TODO: 실제 증빙 유형 매핑
                project_account_d2_id=1,  # TODO: 실제 계정 매핑
            )

        # 생성된 회계 분개 ID 저장
        self.accounting_entry_id = entry.pk
        self.save(update_fields=['accounting_entry_id'])

        return entry

    def clean(self):
        """모델 유효성 검증"""
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({
                'amount': '분할 항목의 금액은 0보다 커야 합니다.'
            })

    def save(self, *args, **kwargs):
        """저장 전 유효성 검증"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.split.id}-{self.sequence}: {self.content} ({self.amount:,}원)"
