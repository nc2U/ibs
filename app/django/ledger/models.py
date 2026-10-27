import hashlib
import logging
import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Count, Sum
from django.utils import timezone
from tree_queries.query import TreeQuerySet

from ledger.services.sync_payment_contract import trigger_sync_contract_payment

logger = logging.getLogger(__name__)


# ============================================
# Bank Account Models - 본사 / 프로젝트 은행 계좌 모델
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
        verbose_name = '02. 본사 관리 계좌'
        verbose_name_plural = '02. 본사 관리 계좌'


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
        verbose_name = '08. 프로젝트 관리 계좌'
        verbose_name_plural = '08. 프로젝트 관리 계좌'


# ============================================
# Account Models - 본사 / 프로젝트 회계 계정 모델
# ============================================

class Account(models.Model):
    """
    계정 과목 추상 모델 (가변 깊이 계층 구조)

    회계 계정 체계를 트리 구조로 관리합니다.
    예: 수익 > 매출 > 분양매출 > ... (깊이 제한 없음)

    코드 체계:
    - 자산(1000), 부채(2000), 자본(3000), 수익(4000), 비용(5000), 대체(6000)
    - 1단계: 100 단위 (5000 → 5100 → 5200...)
    - 2단계: 10 단위 (5000 → 5010 → 5020...)
    - 3단계+: 1 단위 (5010 → 5011 → 5012...)

    이 모델은 추상 모델로, CompanyAccount와 ProjectAccount로 상속됩니다.
    구조는 동일하지만 계정 데이터는 완전히 분리되어 관리됩니다.
    """
    objects = TreeQuerySet.as_manager()

    # Category별 시작 코드
    CATEGORY_BASE_CODES = {
        'asset': 1000,
        'liability': 2000,
        'equity': 3000,
        'revenue': 4000,
        'expense': 5000,
        'transfer': 6000,
        'cancel': 7000,
    }

    # Depth별 코드 간격
    DEPTH_STEPS = {
        2: 10,  # 2단계: 10 단위
        3: 1,  # 3단계 이상: 1 단위
    }

    # 기본 정보
    code = models.CharField(max_length=50, unique=True, blank=True, verbose_name='계정코드',
                            help_text='자동 생성됨. 수동 입력 시 규칙 무시')
    name = models.CharField(max_length=255, verbose_name='계정명')
    description = models.CharField(blank=True, default='', max_length=255, verbose_name='설명', help_text='계정 용도 및 사용 지침')

    # 계층 구조
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT,
                               related_name='children', verbose_name='상위 계정')
    depth = models.PositiveIntegerField(default=1, editable=False, verbose_name='계층 깊이')

    # 회계 분류
    category = models.CharField(
        max_length=20,
        choices=[
            ('asset', '자산'),
            ('liability', '부채'),
            ('equity', '자본'),
            ('revenue', '수익'),
            ('expense', '비용'),
            ('transfer', '대체'),
            ('cancel', '취소'),
        ],
        verbose_name='계정구분',
        help_text='회계 계정의 대분류'
    )

    # 거래 방향
    direction = models.CharField(max_length=10, choices=[('deposit', '입금'), ('withdraw', '출금')],
                                 null=True, blank=True, verbose_name='거래방향',
                                 help_text='이 계정이 사용되는 기본 거래 방향 (분류 전용 계정은 비워둠)')

    # 분류 전용 계정 (거래 사용 불가)
    is_category_only = models.BooleanField(default=False, verbose_name='분류 전용',
                                           help_text='체크 시: 이 계정은 분류 목적으로만 사용되며 직접 거래에 사용 불가. '
                                                     '대분류/중분류 등 상위 계정에 주로 사용')
    is_transfer_fee = models.BooleanField(default=False, verbose_name='이체수수료 여부',
                                          help_text='체크 시: 이 계정은 은행 송금 이체수수료 계정임.')
    # 활성화 상태
    is_active = models.BooleanField(default=True, verbose_name='활성 여부', help_text='비활성화 시 신규 거래에 사용 불가')

    # 정렬 순서
    order = models.PositiveIntegerField(default=0, verbose_name='정렬순서', help_text='같은 레벨 내 표시 순서')

    class Meta:
        abstract = True
        ordering = ['code', 'order']
        indexes = [
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['category', 'is_active']),
        ]

    def _generate_code(self):
        """계정 코드 자동 생성"""
        if self.depth == 1:
            # 최상위 계정: 해당 category의 기존 코드를 한 번에 로딩하여 중복 체크
            base_code = self.CATEGORY_BASE_CODES[self.category]
            existing_codes = set(
                self.__class__.objects.filter(category=self.category)
                .exclude(pk=self.pk or 0)
                .values_list('code', flat=True)
            )
            increment = 0
            while True:
                test_code = str(base_code + (increment * 100))
                if test_code not in existing_codes:
                    return test_code
                increment += 1

        # 하위 계정: 부모 코드 + (순서 * 깊이별 간격)
        parent_code = int(self.parent.code)

        # 같은 parent를 가진 형제 계정 코드를 한 번에 로딩하여 중복 체크
        existing_codes = set(
            self.__class__.objects.filter(parent=self.parent)
            .exclude(pk=self.pk or 0)
            .values_list('code', flat=True)
        )
        siblings_count = len(existing_codes)

        # 순서 계산 (1부터 시작)
        sibling_order = siblings_count + 1

        # 깊이별 간격 (depth 4 이상은 1로 고정)
        step = self.DEPTH_STEPS.get(self.depth, 1)

        new_code = parent_code + (sibling_order * step)
        return str(new_code)

    def save(self, *args, **kwargs):
        # 깊이 자동 계산
        if self.parent:
            self.depth = self.parent.depth + 1
            # 상위 계정의 category와 direction 상속 (선택적)
            if not self.pk:  # 신규 생성 시에만
                if not self.category:
                    self.category = self.parent.category
                if not self.direction:
                    self.direction = self.parent.direction
        else:
            self.depth = 1

        # 코드 자동 생성 (비어있을 경우에만)
        if not self.code:
            self.code = self._generate_code()

        super().save(*args, **kwargs)

    def clean(self):
        """유효성 검증"""
        # 순환 참조 방지
        if self.parent:
            parent = self.parent
            while parent:
                if parent == self:
                    raise ValidationError({'parent': '순환 참조가 발생했습니다.'})
                parent = parent.parent

    def get_full_path(self):
        """전체 경로 반환 (예: '수익 > 매출 > 분양매출')"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)

    def get_descendants(self, include_self=False):
        """모든 하위 계정 조회"""
        return list(self.__class__._default_manager.descendants(self, include_self=include_self))

    def get_ancestors(self, include_self=False):
        """모든 상위 계정 조회 (루트까지)"""
        return list(self.__class__._default_manager.ancestors(self, include_self=include_self))

    def get_computed_direction(self):
        """
        분류 전용 계정의 거래 방향을 하위 계정들을 기반으로 계산

        Returns:
            str: 'deposit', 'withdraw', 'both', None
        """
        if not self.is_category_only:
            # 거래 계정인 경우 실제 direction 반환
            return self.direction

        # 분류 전용 계정인 경우 하위 계정들의 direction 분석
        child_directions = set()
        for child in self.children.filter(is_active=True):
            child_direction = child.get_computed_direction()
            if child_direction == 'both':
                # 하위에 'both'가 있으면 즉시 'both' 반환
                return 'both'
            elif child_direction:
                child_directions.add(child_direction)

        if len(child_directions) == 0:
            return None
        elif len(child_directions) == 1:
            return list(child_directions)[0]
        else:
            # 입금과 출금이 모두 있는 경우
            return 'both'

    def get_direction_display_computed(self):
        """computed_direction의 표시용 텍스트"""
        computed = self.get_computed_direction()
        if computed == 'deposit':
            return '입금'
        elif computed == 'withdraw':
            return '출금'
        elif computed == 'both':
            return '입금/출금'
        else:
            return '-'

    def __str__(self):
        return f"{self.code} {self.name}"


class CompanyAccount(Account):
    """
    본사 계정 과목

    본사의 회계 계정 체계를 관리합니다.
    Account 추상 모델의 모든 필드와 메서드를 상속받으며,
    본사만의 독립적인 계정 데이터를 관리합니다.
    """
    # 관계회사/프로젝트 추적 필수 여부 (본사 전용)
    requires_affiliate = models.BooleanField(default=False, verbose_name='관계회사/프로젝트 필수',
                                             help_text='체크 시: 회계분개 입력 시 관계회사 또는 프로젝트 선택 필수<br>'
                                                       '용도: 관계회사 대여금, 투자금 등 집계가 필요한 계정')

    class Meta:
        ordering = ['code', 'order']
        verbose_name = '01. 본사 계정 과목'
        verbose_name_plural = '01. 본사 계정 과목'
        indexes = [
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['requires_affiliate']),
        ]


class ProjectAccount(Account):
    """
    프로젝트 계정 과목

    프로젝트의 회계 계정 체계를 관리합니다.
    Account 추상 모델의 모든 필드와 메서드를 상속받으며,
    프로젝트만의 독립적인 계정 데이터를 관리합니다.
    """
    is_payment = models.BooleanField('공급대금 여부', default=False)
    requires_contract = models.BooleanField('계약 관련 여부', default=False)
    is_related_contractor = models.BooleanField('계약자 관련 여부', default=False)

    class Meta:
        ordering = ['code', 'order']
        verbose_name = '07. 프로젝트 계정 과목'
        verbose_name_plural = '07. 프로젝트 계정 과목'
        indexes = [
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_payment']),
            models.Index(fields=['requires_contract']),
            models.Index(fields=['is_payment', 'requires_contract']),
        ]


# ============================================
# Affiliate Model
# ============================================

class Affiliate(models.Model):
    """
    관계회사/프로젝트 참조 모델

    회계 분개에서 관계회사 대여금, 투자금 등을 추적하기 위한 모델입니다.
    """
    sort = models.CharField('구분', max_length=20,
                            choices=(('company', '관계 회사'), ('project', '관련 프로젝트')),
                            db_index=True,
                            help_text='관계회사 또는 관련 프로젝트 구분')
    company = models.ForeignKey('company.Company', on_delete=models.PROTECT,
                                null=True, blank=True, verbose_name='관계 회사',
                                help_text='대여금/투자금 등이 발생한 관계회사')
    project = models.ForeignKey('project.Project', on_delete=models.PROTECT,
                                null=True, blank=True, verbose_name='관련 프로젝트',
                                help_text='대여금/투자금 등이 발생한 관련 프로젝트')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='설명',
                                   help_text='대여 목적, 조건 등 추가 설명')

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        verbose_name = '06. 관계회사/프로젝트'
        verbose_name_plural = '06. 관계회사/프로젝트'
        ordering = ['id', ]
        indexes = [
            models.Index(fields=['sort', 'company']),
            models.Index(fields=['sort', 'project']),
        ]

    def clean(self):
        """유효성 검증"""
        # company와 project 중 정확히 하나만 입력되어야 함
        if self.sort == 'company':
            if not self.company:
                raise ValidationError({'company': '관계 회사 구분일 경우 회사를 선택해야 합니다.'})
            if self.project:
                raise ValidationError({'project': '관계 회사 구분일 경우 프로젝트를 선택할 수 없습니다.'})
        elif self.sort == 'project':
            if not self.project:
                raise ValidationError({'project': '관련 프로젝트 구분일 경우 프로젝트를 선택해야 합니다.'})
            if self.company:
                raise ValidationError({'company': '관련 프로젝트 구분일 경우 회사를 선택할 수 없습니다.'})

    def save(self, *args, **kwargs):
        """저장 전 유효성 검증"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.sort == 'company' and self.company:
            return f"회사: {self.company.name}"
        elif self.sort == 'project' and self.project:
            return f"프로젝트: {self.project.name}"
        return f"{self.get_sort_display()}"


# ============================================
# Banking Domain - 본사 / 프로젝트 은행 거래 도메인
# ============================================

class BankTransaction(models.Model):
    """
    은행 거래 추상 모델

    Banking Domain의 핵심 모델로, 실제 은행 계좌의 입출금 거래를 표현합니다.
    UUID 기반 식별자를 통해 다른 도메인과 느슨하게 결합됩니다.
    """
    # Primary Identifier
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False,
                                      verbose_name='거래 ID', help_text='도메인 간 연결을 위한 UUID 식별자')

    # 거래 정보
    deal_date = models.DateField(verbose_name='거래일자')
    sort = models.ForeignKey('ibs.AccountSort', on_delete=models.PROTECT, verbose_name='거래구분',
                             help_text='입금/출금 구분', db_index=True)
    amount = models.PositiveBigIntegerField(verbose_name='금액', help_text='거래 금액 (양수)')
    content = models.CharField(max_length=100, blank=True, default='', verbose_name='적요', help_text='거래 기록 사항')
    note = models.TextField(blank=True, default='', verbose_name='비고', help_text='추가 설명')

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    creator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='생성자')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['deal_date']),
            models.Index(fields=['deal_date', 'sort']),
        ]

    def clean(self):
        """모델 유효성 검증"""
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': '거래 금액은 0보다 커야 합니다.'})

        if self.deal_date and self.deal_date > timezone.localdate():
            raise ValidationError({'deal_date': '미래 날짜로 거래를 생성할 수 없습니다.'})

    def save(self, *args, **kwargs):
        """저장 전 유효성 검증"""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_balanced(self):
        """
        회계 분개 금액 균형 여부 (실시간 계산)

        은행 거래 금액과 회계 분개 금액 합계가 일치하는지 실시간으로 검증합니다.
        """
        try:
            result = self.validate_accounting_entries()
            return result['is_valid']
        except (AttributeError, NotImplementedError):
            return False

    @property
    def accounting_entries(self):
        """
        이 은행 거래에 연결된 모든 회계 분개 항목들을 반환합니다.
        하위 클래스에서 구현해야 합니다.
        """
        raise NotImplementedError('하위 클래스에서 구현해야 합니다.')

    def validate_accounting_entries(self):
        """
        이 거래에 대한 AccountingEntry의 금액 합계 검증
        (prefetched_accounting_entries 캐시 존재 시 메모리 계산으로 N+1 쿼리 방지)

        Returns:
            dict: {'is_valid': bool, 'bank_amount': int, 'accounting_total': int, 'difference': int}
        """
        if hasattr(self, 'prefetched_accounting_entries'):
            entries = self.prefetched_accounting_entries
            accounting_total = sum(e.amount for e in entries)
            entry_count = len(entries)
        else:
            result = self.accounting_entries.aggregate(total=Sum('amount'), count=Count('id'))
            accounting_total = result['total'] or 0
            entry_count = result['count'] or 0
        difference = self.amount - accounting_total

        return {
            'is_valid': difference == 0,
            'bank_amount': self.amount,
            'accounting_total': accounting_total,
            'difference': difference,
            'entry_count': entry_count,
        }

    def __str__(self):
        return f"{self.sort.name} - {self.amount:,}원 ({self.deal_date})"


class CompanyBankTransaction(BankTransaction):
    """
    본사 은행 거래

    회사 본사의 은행 거래를 관리합니다.
    """
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name='회사')
    bank_account = models.ForeignKey(CompanyBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')
    updator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='편집자',
                                related_name='updated_transactions')

    class Meta:
        verbose_name = '03. 본사 은행 거래'
        verbose_name_plural = '03. 본사 은행 거래'
        ordering = ['-deal_date', '-created_at']
        indexes = [
            models.Index(fields=['bank_account', 'deal_date']),
        ]

    def clean(self):
        super().clean()
        if self.bank_account_id and self.company_id:
            if self.bank_account.company_id != self.company_id:
                raise ValidationError({'bank_account': '거래 계좌의 회사와 거래 회사가 일치하지 않습니다.'})

    @property
    def accounting_entries(self):
        """이 은행 거래에 연결된 모든 회계 분개 항목들을 반환합니다."""
        return CompanyAccountingEntry.objects.filter(transaction_id=self.transaction_id)

    def get_accounting_entries_with_tx(self):
        """_related_transaction 주입이 필요한 경우에만 호출합니다."""
        entries = list(self.accounting_entries)
        for entry in entries:
            entry._related_transaction = self
        return entries


class ProjectBankTransaction(BankTransaction):
    """
    프로젝트 은행 거래

    프로젝트별 은행 거래를 관리합니다.
    운영비 여부는 bank_account.is_imprest를 통해 판단합니다.
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    bank_account = models.ForeignKey(ProjectBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')
    updator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='편집자',
                                related_name='updated_project_transactions')

    class Meta:
        verbose_name = '09. 프로젝트 은행 거래'
        verbose_name_plural = '09. 프로젝트 은행 거래'
        ordering = ['-deal_date', '-created_at']
        indexes = [
            models.Index(fields=['bank_account', 'deal_date']),
        ]

    def clean(self):
        super().clean()
        if self.bank_account_id and self.project_id:
            if self.bank_account.project_id != self.project_id:
                raise ValidationError({'bank_account': '거래 계좌의 프로젝트와 거래 프로젝트가 일치하지 않습니다.'})

    def save(self, *args, **kwargs):
        """
        은행 거래 저장 시 연결된 회계 분개 및 ContractPayment 동기화

        변경 감지 및 동기화:
        - project 변경: AccountingEntry.project 업데이트 → ContractPayment.project 동기화
        - deal_date 변경: ContractPayment.deal_date 동기화
        """
        # 기존 인스턴스인지 확인 (pk 존재 여부)
        is_update = self.pk is not None

        if is_update:
            # 기존 값 조회 (변경 감지용)
            try:
                old_instance = ProjectBankTransaction.objects.get(pk=self.pk)
                old_project_id = old_instance.project_id
                old_deal_date = old_instance.deal_date
            except ProjectBankTransaction.DoesNotExist:
                old_project_id = None
                old_deal_date = None
        else:
            old_project_id = None
            old_deal_date = None

        # 부모 클래스 save() 호출
        super().save(*args, **kwargs)

        # 변경 감지 플래그
        project_changed = is_update and old_project_id and old_project_id != self.project_id
        deal_date_changed = is_update and old_deal_date and old_deal_date != self.deal_date

        # project 변경 시 연결된 회계 분개 동기화
        if project_changed:
            # 연결된 모든 회계 분개의 project 업데이트
            updated_count = ProjectAccountingEntry.objects.filter(
                transaction_id=self.transaction_id
            ).update(project=self.project)

            if updated_count > 0:
                logger.info(
                    f"ProjectBankTransaction(pk={self.pk}) project 변경: "
                    f"{old_project_id} → {self.project_id}, "
                    f"연결된 {updated_count}개 회계분개 동기화 완료"
                )

        # project 또는 deal_date 변경 시 ContractPayment 동기화
        if project_changed or deal_date_changed:
            entries = list(ProjectAccountingEntry.objects.filter(transaction_id=self.transaction_id))

            for entry in entries:
                trigger_sync_contract_payment(entry)

            if deal_date_changed:
                logger.info(
                    f"ProjectBankTransaction(pk={self.pk}) deal_date 변경: "
                    f"{old_deal_date} → {self.deal_date}, "
                    f"연결된 {len(entries)}개 ContractPayment 동기화 완료"
                )

    @property
    def accounting_entries(self):
        """이 은행 거래에 연결된 모든 회계 분개 항목들을 반환합니다."""
        return ProjectAccountingEntry.objects.filter(transaction_id=self.transaction_id)

    def get_accounting_entries_with_tx(self):
        """_related_transaction 주입이 필요한 경우에만 호출합니다."""
        entries = list(self.accounting_entries)
        for entry in entries:
            entry._related_transaction = self
        return entries


# ============================================
# Accounting Domain - 본사 / 프로젝트 회계 분개 도메인
# ============================================

class AccountingEntry(models.Model):
    """
    회계 분개 추상 모델

    Accounting Domain의 핵심 모델로, 은행 거래에 대한 회계 분류 정보를 표현합니다.
    transaction_id를 통해 BankTransaction과 느슨하게 연결됩니다.

    일반 거래: BankTransaction 1개 → AccountingEntry 1개 (금액 동일)
    분할 거래: BankTransaction 1개 → AccountingEntry N개 (금액 합계 일치)

    Note: sort(계정구분)는 BankTransaction에만 존재하며, AccountingEntry는
          related_transaction.sort를 통해 접근합니다.
    """
    # Banking Domain 연결 (UUID 참조)
    transaction_id = models.UUIDField(db_index=True, verbose_name='거래 ID',
                                      help_text='BankTransaction.transaction_id 참조')
    amount = models.PositiveBigIntegerField(verbose_name='금액', help_text='이 회계 분개의 금액 (분할 시 일부 금액)')
    trader = models.CharField(max_length=50, verbose_name='거래처', help_text='거래 상대방', null=True, blank=True)
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
            models.Index(fields=['created_at']),
            models.Index(fields=['evidence_type']),
        ]

    @property
    def related_transaction(self):
        """연관된 BankTransaction 조회"""
        if not hasattr(self, '_related_transaction'):
            db = self._state.db or 'default'
            if isinstance(self, CompanyAccountingEntry):
                self._related_transaction = CompanyBankTransaction.objects.using(db).filter(
                    transaction_id=self.transaction_id
                ).first()
            elif isinstance(self, ProjectAccountingEntry):
                self._related_transaction = ProjectBankTransaction.objects.using(db).filter(
                    transaction_id=self.transaction_id
                ).first()
            else:
                self._related_transaction = None
        return self._related_transaction

    @property
    def sort(self):
        """BankTransaction의 sort 접근 (하위 호환성)"""
        trans = self.related_transaction
        return trans.sort if trans else None

    def __str__(self):
        trans = self.related_transaction
        sort_name = trans.sort.name if trans and trans.sort else '미분류'
        return f"{sort_name} - {self.amount:,} ({self.trader or '거래처 미지정'})"


class CompanyAccountingEntry(AccountingEntry):
    """
    본사 회계 분개

    본사 거래에 대한 회계 분개 정보를 관리합니다.
    CompanyAccount 계정 체계를 사용합니다.
    """
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name='회사')

    # 본사 계정 체계 (CompanyAccount 참조)
    account = models.ForeignKey(CompanyAccount, on_delete=models.PROTECT, verbose_name='계정 과목',
                                help_text='회계 분개에 사용할 계정 과목',
                                limit_choices_to={'is_active': True, 'is_category_only': False})

    # 관계회사/프로젝트 추적 (본사 전용)
    affiliate = models.ForeignKey('Affiliate', on_delete=models.PROTECT,
                                  null=True, blank=True, verbose_name='관계회사/프로젝트',
                                  help_text='관계회사 대여금, 투자금 등의 경우 필수 입력')

    class Meta:
        verbose_name = '04. 본사 회계 분개'
        verbose_name_plural = '04. 본사 회계 분개'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'created_at']),
            models.Index(fields=['affiliate']),
        ]

    def clean(self):
        """유효성 검증"""
        super().clean()

        # 계정이 분류 전용인지 확인
        if self.account and self.account.is_category_only:
            raise ValidationError({
                'account': f'"{self.account.name}"는 분류 전용 계정이므로 거래에 사용할 수 없습니다. 하위 계정을 선택해주세요.'
            })

        # 계정이 비활성화 상태인지 확인
        if self.account and not self.account.is_active:
            raise ValidationError({
                'account': f'"{self.account.name}"는 비활성 계정이므로 사용할 수 없습니다.'
            })

        # requires_affiliate 검증
        if self.account and self.account.requires_affiliate and not self.affiliate:
            raise ValidationError({
                'affiliate': f'"{self.account.name}" 계정은 관계회사/프로젝트 선택이 필수입니다.'
            })

    def save(self, *args, **kwargs):
        """저장 전 유효성 검증"""
        self.full_clean()
        super().save(*args, **kwargs)


class ProjectAccountingEntry(AccountingEntry):
    """
    프로젝트 회계 분개

    프로젝트 거래에 대한 회계 분개 정보를 관리합니다.
    ProjectAccount 계정 체계를 사용합니다.

    ⚠️ 중요: project 변경 시 주의사항
    - project 변경 시 연결된 BankTransaction과 ContractPayment도 함께 동기화됩니다.
    - 일반적으로 project는 생성 시에만 지정하고, 이후 변경하지 않는 것을 권장합니다.
    - 변경이 필요한 경우 ProjectBankTransaction.project를 변경하면 자동으로 동기화됩니다.
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')

    # 프로젝트 계정 체계 (ProjectAccount 참조)
    account = models.ForeignKey(ProjectAccount, on_delete=models.PROTECT, verbose_name='계정 과목',
                                help_text='회계 분개에 사용할 계정 과목',
                                limit_choices_to={'is_active': True, 'is_category_only': False})

    # 공급계약 및 계약자 연결 (프로젝트 전용)
    contract = models.ForeignKey('contract.Contract', on_delete=models.PROTECT,
                                 null=True, blank=True, verbose_name='공급계약',
                                 help_text='공급계약 관련 계정 사용 시 필수 입력')
    contractor = models.ForeignKey('contract.Contractor', on_delete=models.PROTECT, null=True, blank=True,
                                   verbose_name='계약자', help_text='계정 관련 계약자')

    class Meta:
        verbose_name = '10. 프로젝트 회계 분개'
        verbose_name_plural = '10. 프로젝트 회계 분개'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'created_at']),
            models.Index(fields=['contract']),
        ]

    def clean_fields(self, exclude=None):
        """
        FK 유효성 검증 오버라이드

        신규 생성 시 contract FK 검증 제외:
        Django FK.validate()는 router.db_for_read()를 사용하므로 replica를 조회함.
        동일 트랜잭션 내 생성된 contract는 아직 replica에 반영되지 않아 검증 실패 가능.
        DB 수준의 FK 제약 조건이 무결성을 보장하므로 안전하게 제외 가능.
        """
        if self.pk is None and self.contract_id is not None:
            exclude = list(exclude or []) + ['contract']
        super().clean_fields(exclude=exclude)

    def clean(self):
        """유효성 검증"""
        super().clean()

        # 계정이 분류 전용인지 확인
        if self.account and self.account.is_category_only:
            raise ValidationError({
                'account': f'"{self.account.name}"는 분류 전용 계정이므로 거래에 사용할 수 없습니다. 하위 계정을 선택해주세요.'
            })

        # 계정이 비활성화 상태인지 확인
        if self.account and not self.account.is_active:
            raise ValidationError({
                'account': f'"{self.account.name}"는 비활성 계정이므로 사용할 수 없습니다.'
            })

        # 계약-프로젝트 일치 검증
        if self.contract_id and self.project_id:
            contract_project_id = self.contract.project_id if self.contract else None
            if contract_project_id and contract_project_id != self.project_id:
                raise ValidationError({
                    'contract': '분개의 프로젝트와 계약의 프로젝트가 일치하지 않습니다.'
                })

        # 계약자-계약 일치 검증
        if self.contractor_id and self.contract_id:
            contractor_contract_id = self.contractor.contract_id if self.contractor else None
            if contractor_contract_id and contractor_contract_id != self.contract_id:
                raise ValidationError({
                    'contractor': '계약자와 계약 정보가 일치하지 않습니다.'
                })

        # requires_contract 여부와 무관하게 회계 거래에서는 contract 없이도 '미매칭 수납건'으로 입력을 허용함
        # (현장/분양 수납 관리 부서에서 사후에 계약자를 매칭할 수 있도록 지원)

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        저장 전 유효성 검증 및 ContractPayment 동기화

        ⚠️ 권장 사항:
        1. 생성: 복합 거래 API를 통해 BankTransaction과 함께 생성
        2. 수정: contract, amount 등만 수정 (project 변경 권장 안 함)
        3. project 변경 필요 시: ProjectBankTransaction.project 변경 → 자동 동기화

        데이터 흐름:
        - 저장 후 trigger_sync_contract_payment 호출
        - ContractPayment의 project/contract 자동 업데이트
        """
        is_update = self.pk is not None
        old_project_id = None

        # project 변경 감지 (경고용)
        if is_update:
            try:
                old_instance = ProjectAccountingEntry.objects.get(pk=self.pk)
                old_project_id = old_instance.project_id
            except ProjectAccountingEntry.DoesNotExist:
                pass

        # 유효성 검증
        self.full_clean()

        # project 변경 시 경고 로깅
        if is_update and old_project_id and old_project_id != self.project_id:
            logger.warning(
                f"⚠️ ProjectAccountingEntry(pk={self.pk}) project 직접 변경 감지: "
                f"{old_project_id} → {self.project_id}. "
                f"권장: ProjectBankTransaction.project를 변경하면 자동 동기화됩니다. "
                f"현재 변경은 BankTransaction과 불일치를 유발할 수 있습니다."
            )

        super().save(*args, **kwargs)

        # ContractPayment 자동 동기화
        trigger_sync_contract_payment(self)


# ============================================
# Calculation Domain - 본사 / 프로젝트 정산 확인 도메인
# ============================================


class CompanyLedgerCalculation(models.Model):
    """본사 원장 정산 기록"""
    company = models.OneToOneField('company.Company', on_delete=models.CASCADE, unique=True, verbose_name='회사')
    calculated = models.DateField('정산일', null=True, blank=True)
    creator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '05. 본사 원장 정산'
        verbose_name_plural = '05. 본사 원장 정산'

    def __str__(self):
        return f'{self.company} 정산일: {self.calculated}'


class ProjectLedgerCalculation(models.Model):
    """프로젝트 원장 정산 기록"""
    project = models.OneToOneField('project.Project', on_delete=models.CASCADE, unique=True, verbose_name='프로젝트')
    calculated = models.DateField('정산일', null=True, blank=True)
    creator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '11. 프로젝트 원장 정산'
        verbose_name_plural = '11. 프로젝트 원장 정산'

    def __str__(self):
        return f'{self.project} 정산일: {self.calculated}'


# ============================================
# Import/Export Job - 비동기 가져오기/내보내기
# ============================================

class ImportJob(models.Model):
    """비동기 가져오기/내보내기 작업 추적"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = [
        (PENDING, '대기 중'),
        (PROCESSING, '처리 중'),
        (COMPLETED, '완료'),
        (FAILED, '실패'),
    ]

    JOB_TYPE_CHOICES = [
        ('import', '가져오기'),
        ('export', '내보내기'),
    ]

    RESOURCE_TYPE_CHOICES = [
        ('company_account', 'CompanyAccount'),
        ('project_account', 'ProjectAccount'),
    ]

    job_type = models.CharField('작업 유형', max_length=10, choices=JOB_TYPE_CHOICES)
    resource_type = models.CharField('리소스 유형', max_length=30, choices=RESOURCE_TYPE_CHOICES)
    file = models.FileField('파일', upload_to='ledger_import_jobs/', blank=True, null=True)
    task_id = models.CharField('태스크 ID', max_length=255, blank=True)
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default=PENDING)
    total_records = models.IntegerField('전체 레코드', default=0)
    processed_records = models.IntegerField('처리된 레코드', default=0)
    success_count = models.IntegerField('성공 건수', default=0)
    error_count = models.IntegerField('오류 건수', default=0)
    error_message = models.TextField('오류 메시지', blank=True)
    error_details = models.JSONField('오류 상세', null=True, blank=True)
    result_file = models.FileField('결과 파일', upload_to='ledger_export_results/', blank=True, null=True)
    creator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, verbose_name='생성자',
                                related_name='ledger_import_jobs')
    created_at = models.DateTimeField('생성일시', auto_now_add=True)
    started_at = models.DateTimeField('시작일시', blank=True, null=True)
    completed_at = models.DateTimeField('완료일시', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '12. 가져오기/내보내기 작업'
        verbose_name_plural = '12. 가져오기/내보내기 작업'

    def __str__(self):
        return f'{self.get_job_type_display()} - {self.get_resource_type_display()} ({self.get_status_display()})'

    @property
    def progress(self):
        """진행률 계산 (0-100)"""
        if self.total_records > 0:
            return int((self.processed_records / self.total_records) * 100)
        return 0

    @property
    def duration(self):
        """작업 소요 시간 계산"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def update_progress(self, processed: int, total: int, status: str = None):
        """진행률 업데이트"""
        self.processed_records = processed
        self.total_records = total
        update_fields = ['processed_records', 'total_records']
        if status:
            self.status = status
            update_fields.append('status')
        self.save(update_fields=update_fields)


# ============================================
# Bank Scraping Domain - 은행 거래 자동 수집 및 버퍼
# ============================================

class BankApiCredential(models.Model):
    """
    은행 API 계정 연동 정보
    
    본사 또는 프로젝트 은행 계좌와 CODEF의 connectedId를 매핑하여
    자동 수집 대상 계좌 및 인증 상태를 관리합니다.
    """
    AUTH_TYPE_CHOICES = [
        ('cert', '공동인증서/아이디'),
        ('fast', '빠른조회 (신탁/조합)'),
    ]

    STATUS_CHOICES = [
        ('ready', '대기'),
        ('success', '정상'),
        ('error', '오류'),
    ]

    company_bank_account = models.OneToOneField(
        'CompanyBankAccount', on_delete=models.CASCADE, null=True, blank=True,
        related_name='api_credential', verbose_name='본사 관리 계좌'
    )
    project_bank_account = models.OneToOneField(
        'ProjectBankAccount', on_delete=models.CASCADE, null=True, blank=True,
        related_name='api_credential', verbose_name='프로젝트 관리 계좌'
    )

    auth_type = models.CharField('인증방식', max_length=10, choices=AUTH_TYPE_CHOICES, default='cert', help_text='인증서 방식 또는 신탁사 빠른조회 방식')
    connected_id = models.CharField('CODEF 커넥티드ID', max_length=100, blank=True, default='', db_index=True, help_text='공동인증서/ID 연동 시 필수, 빠른조회 시 비워둠')
    fast_business_number = models.CharField('빠른조회 사업자번호', max_length=20, blank=True, default='', help_text='신탁사/조합 사업자등록번호 (숫자 10자리)')
    fast_password = models.CharField('빠른조회 비밀번호(암호화)', max_length=255, blank=True, default='', help_text='통장 또는 빠른조회 비밀번호')
    bank_code = models.CharField('은행기관코드', max_length=10, help_text='CODEF 기관코드 (예: 0004 국민, 0088 신한, 0020 우리)')
    account_number = models.CharField('계좌번호', max_length=50)

    is_active = models.BooleanField('자동수집 활성화', default=True, help_text='체크 시 정기 수집 스케줄 대상에 포함')
    last_scraped_at = models.DateTimeField('최종수집일시', null=True, blank=True)
    last_status = models.CharField('최종상태', max_length=20, choices=STATUS_CHOICES, default='ready')
    last_error_message = models.TextField('최종에러메시지', blank=True, default='')

    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        verbose_name = '13. 은행 API 연동 계좌'
        verbose_name_plural = '13. 은행 API 연동 계좌'
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if not self.company_bank_account and not self.project_bank_account:
            raise ValidationError('본사 계좌 또는 프로젝트 계좌 중 하나를 반드시 선택해야 합니다.')
        if self.company_bank_account and self.project_bank_account:
            raise ValidationError('본사 계좌와 프로젝트 계좌를 동시에 선택할 수 없습니다.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def target_account(self):
        """연결된 실제 은행 계좌 객체 반환"""
        return self.company_bank_account or self.project_bank_account

    @property
    def is_project(self) -> bool:
        """프로젝트 계좌 여부"""
        return self.project_bank_account is not None

    def __str__(self):
        acc = self.target_account
        alias = acc.alias_name if acc else self.account_number
        return f"[{self.bank_code}] {alias} ({self.account_number})"


class RawBankTransaction(models.Model):
    """
    은행 API 수집 원시 거래내역 (Staging Buffer)
    
    은행에서 스크래핑/API로 수집된 미가공 거래 데이터입니다.
    중복 검증 후 저장되며, AI/규칙 기반 잠정 계정 분류를 거쳐
    담당자의 승인(Confirm) 후 정식 원장(ProjectBankTransaction 등)으로 승격됩니다.
    """
    STATUS_CHOICES = [
        ('pending', 'AI분류 대기'),
        ('ready', '컨펌 대기'),
        ('confirmed', '원장 반영 완료'),
        ('ignored', '제외/무시'),
    ]

    SORT_CHOICES = [
        ('deposit', '입금'),
        ('withdraw', '출금'),
    ]

    # 은행 수집 기본 데이터
    credential = models.ForeignKey(
        BankApiCredential, on_delete=models.CASCADE, related_name='raw_transactions',
        verbose_name='연동 계좌'
    )
    deal_date = models.DateField('거래일자', db_index=True)
    deal_time = models.TimeField('거래시간', null=True, blank=True)
    sort_type = models.CharField('입출금구분', max_length=10, choices=SORT_CHOICES, db_index=True)
    amount = models.PositiveBigIntegerField('거래금액')
    balance = models.PositiveBigIntegerField('거래후잔액', null=True, blank=True)
    client_name = models.CharField('거래처/입금자명', max_length=100, blank=True, default='')
    content = models.CharField('적요', max_length=100, blank=True, default='')
    branch_name = models.CharField('취급점', max_length=100, blank=True, default='')
    raw_data = models.JSONField('은행 원본 JSON', null=True, blank=True)

    # 멱등성 보장 (중복 수집 방지 해시)
    tx_hash = models.CharField(
        '거래 식별 해시', max_length=64, unique=True, db_index=True,
        help_text='중복 수집 방지를 위한 SHA-256 고유 해시'
    )

    # AI / 규칙 기반 잠정 추천 데이터
    status = models.CharField('처리상태', max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    suggested_company_account = models.ForeignKey(
        'CompanyAccount', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='추천 본사계정'
    )
    suggested_project_account = models.ForeignKey(
        'ProjectAccount', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='추천 프로젝트계정'
    )
    suggested_contract = models.ForeignKey(
        'contract.Contract', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='추천 분양계약'
    )
    confidence_score = models.PositiveSmallIntegerField('AI 신뢰도점수(%)', default=0)
    ai_reason = models.CharField('추천 사유', max_length=255, blank=True, default='')

    # 담당자 컨펌 및 원장 승격 정보
    confirmed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='승인자'
    )
    confirmed_at = models.DateTimeField('승인일시', null=True, blank=True)
    created_company_transaction = models.ForeignKey(
        'CompanyBankTransaction', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='생성된 본사 거래'
    )
    created_project_transaction = models.ForeignKey(
        'ProjectBankTransaction', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='생성된 프로젝트 거래'
    )

    created_at = models.DateTimeField('수집일시', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        verbose_name = '14. 수집 원시 거래내역'
        verbose_name_plural = '14. 수집 원시 거래내역'
        ordering = ['-deal_date', '-deal_time', '-id']
        indexes = [
            models.Index(fields=['credential', 'deal_date']),
            models.Index(fields=['status', 'deal_date']),
        ]

    @staticmethod
    def generate_hash(account_no: str, date: Any, time: Any, sort_type: str, amount: int, balance: Any, client_name: str, content: str) -> str:
        """은행 거래 고유 복합 해시 생성 (Idempotency Key)"""
        raw_key = f"{account_no}_{date}_{time or ''}_{sort_type}_{amount}_{balance or ''}_{client_name or ''}_{content or ''}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    def __str__(self):
        time_str = f" {self.deal_time}" if self.deal_time else ""
        return f"[{self.get_sort_type_display()}] {self.deal_date}{time_str} - {self.amount:,}원 ({self.client_name or self.content})"
