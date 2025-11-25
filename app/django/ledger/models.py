import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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

    # 금액 (분할 거래 지원)
    amount = models.PositiveBigIntegerField(verbose_name='금액', help_text='이 회계 분개의 금액 (분할 시 일부 금액)')

    # 거래자
    trader = models.CharField(max_length=50, verbose_name='거래처', help_text='거래 상대방', null=True, blank=True)

    # 증빙
    evidence_type = models.CharField(
        max_length=1,
        choices=[
            ('0', '증빙없음'),
            ('1', '세금계산서'),
            ('2', '계산서(면세)'),
            ('3', '신용/체크카드 매출전표'),
            ('4', '현금영수증'),
            ('5', '원천징수영수증/지급명세서'),
            ('6', '지로용지 및 청구서')
        ],
        verbose_name='증빙종류', null=True, blank=True)

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['sort', 'created_at']),
            models.Index(fields=['sort', 'evidence_type']),
            models.Index(fields=['transaction_type', 'sort']),
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
        return f"{self.sort} - {self.amount:,} ({self.trader or '거래처 미지정'})"


# ============================================
# Company Ledger - 본사 회계 원장
# ============================================

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
        verbose_name = '01. 본사 관리 계좌'
        verbose_name_plural = '01. 본사 관리 계좌'


class CompanyBankTransaction(BankTransaction):
    """
    본사 은행 거래

    회사 본사의 은행 거래를 관리합니다.
    """
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name='회사')
    bank_account = models.ForeignKey(CompanyBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')

    class Meta:
        verbose_name = '02. 본사 은행 거래'
        verbose_name_plural = '02. 본사 은행 거래'
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
        verbose_name = '03. 본사 회계 분개'
        verbose_name_plural = '03. 본사 회계 분개'
        ordering = ['-created_at']


# ============================================
# Project Ledger - 현장 회계 원장
# ============================================

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
        verbose_name = '04. 프로젝트 관리 계좌'
        verbose_name_plural = '04. 프로젝트 관리 계좌'


class ProjectBankTransaction(BankTransaction):
    """
    프로젝트 은행 거래

    프로젝트별 은행 거래를 관리합니다.
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    bank_account = models.ForeignKey(ProjectBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')
    is_imprest = models.BooleanField(default=False, verbose_name='운영비 여부', help_text='프로젝트 운영비 계정 거래 여부')

    class Meta:
        verbose_name = '05. 프로젝트 은행 거래'
        verbose_name_plural = '05. 프로젝트 은행 거래'
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
        verbose_name = '06. 프로젝트 회계 분개'
        verbose_name_plural = '06. 프로젝트 회계 분개'
        ordering = ['-created_at']
