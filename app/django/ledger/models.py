import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ============================================
# Bank Account Models - 본사 / 현장 은행 계좌 모델
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
        verbose_name = '07. 프로젝트 관리 계좌'
        verbose_name_plural = '07. 프로젝트 관리 계좌'


# ============================================
# Account Models - 본사 / 현장 회계 계정 모델
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
    # 분류 전용 계정 (거래 사용 불가)
    is_category_only = models.BooleanField(default=False, verbose_name='분류 전용',
                                           help_text='체크 시: 이 계정은 분류 목적으로만 사용되며 직접 거래에 사용 불가. '
                                                     '대분류/중분류 등 상위 계정에 주로 사용')

    # 거래 방향
    direction = models.CharField(max_length=10, choices=[('deposit', '입금'), ('withdraw', '출금')],
                                 null=True, blank=True, verbose_name='거래방향',
                                 help_text='이 계정이 사용되는 기본 거래 방향 (분류 전용 계정은 비워둠)')

    # 활성화 상태
    is_active = models.BooleanField(default=True, verbose_name='활성 여부', help_text='비활성화 시 신규 거래에 사용 불가')

    # 관계회사/프로젝트 추적 필수 여부
    requires_affiliate = models.BooleanField(default=False, verbose_name='관계회사/프로젝트 필수',
                                             help_text='체크 시: 회계분개 입력 시 관계회사 또는 프로젝트 선택 필수<br>'
                                                       '용도: 관계회사 대여금, 투자금 등 집계가 필요한 계정')

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
            # 최상위 계정: category별 기본 코드에서 시작하여 100 단위로 증가
            base_code = self.CATEGORY_BASE_CODES[self.category]
            code_candidate = base_code
            increment = 0

            while True:
                test_code = str(code_candidate + (increment * 100))
                # 자신을 제외하고 중복 검사
                existing = self.__class__.objects.filter(code=test_code)
                if self.pk:  # 업데이트인 경우 자신 제외
                    existing = existing.exclude(pk=self.pk)

                if not existing.exists():
                    return test_code
                increment += 1

        # 하위 계정: 부모 코드 + (순서 * 깊이별 간격)
        parent_code = int(self.parent.code)

        # 같은 parent를 가진 형제 계정 수 확인 (자신 제외)
        # 추상 클래스이므로 self.__class__를 사용하여 실제 모델 클래스의 매니저 접근
        siblings_count = self.__class__.objects.filter(parent=self.parent).count()
        if self.pk:  # 업데이트인 경우 자신 제외
            siblings_count -= 1

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
        """모든 하위 계정 조회 (재귀)"""
        descendants = []
        if include_self:
            descendants.append(self)

        for child in self.children.all():
            descendants.extend(child.get_descendants(include_self=True))

        return descendants

    def get_ancestors(self, include_self=False):
        """모든 상위 계정 조회 (루트까지)"""
        ancestors = []
        if include_self:
            ancestors.append(self)

        parent = self.parent
        while parent:
            ancestors.append(parent)
            parent = parent.parent

        return ancestors

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

    class Meta:
        ordering = ['code', 'order']
        verbose_name = '01. 본사 계정 과목'
        verbose_name_plural = '01. 본사 계정 과목'
        indexes = [
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['category', 'is_active']),
        ]


class ProjectAccount(Account):
    """
    프로젝트 계정 과목

    프로젝트의 회계 계정 체계를 관리합니다.
    Account 추상 모델의 모든 필드와 메서드를 상속받으며,
    프로젝트만의 독립적인 계정 데이터를 관리합니다.
    """
    is_payment = models.BooleanField(default=False)
    is_related_contract = models.BooleanField(default=False)

    class Meta:
        ordering = ['code', 'order']
        verbose_name = '06. 프로젝트 계정 과목'
        verbose_name_plural = '06. 프로젝트 계정 과목'
        indexes = [
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_payment']),
            models.Index(fields=['is_related_contract']),
            models.Index(fields=['is_payment', 'is_related_contract']),
        ]


# ============================================
# Banking Domain - 본사 / 현장 은행 거래 도메인
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
    sort = models.ForeignKey('ibs.AccountSort', on_delete=models.PROTECT, verbose_name='거래구분',
                             help_text='입금/출금 구분', db_index=True)
    amount = models.PositiveBigIntegerField(verbose_name='금액', help_text='거래 금액 (양수)')
    content = models.CharField(max_length=100, verbose_name='적요', help_text='거래 기록 사항')
    note = models.TextField(blank=True, default='', verbose_name='비고', help_text='추가 설명')

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    creator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='생성자')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['deal_date']),
            models.Index(fields=['deal_date', 'sort']),
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
        return f"{self.sort.name} - {self.amount:,}원 ({self.deal_date})"


class CompanyBankTransaction(BankTransaction):
    """
    본사 은행 거래

    회사 본사의 은행 거래를 관리합니다.
    """
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name='회사')
    bank_account = models.ForeignKey(CompanyBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')

    class Meta:
        verbose_name = '03. 본사 은행 거래'
        verbose_name_plural = '03. 본사 은행 거래'
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
        verbose_name = '11. 관계회사/프로젝트'
        verbose_name_plural = '11. 관계회사/프로젝트'
        ordering = ['sort', '-created_at']
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


class CompanyLedgerCalculation(models.Model):
    """본사 원장 정산 기록"""
    company = models.OneToOneField(
        'company.Company',
        on_delete=models.CASCADE,
        unique=True,
        verbose_name='회사'
    )
    calculated = models.DateField('정산일', null=True, blank=True)
    creator = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='등록자'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '05. 본사 원장 정산'
        verbose_name_plural = '05. 본사 원장 정산'

    def __str__(self):
        return f'{self.company} 정산일: {self.calculated}'


class ProjectBankTransaction(BankTransaction):
    """
    프로젝트 은행 거래

    프로젝트별 은행 거래를 관리합니다.
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    bank_account = models.ForeignKey(ProjectBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')
    is_imprest = models.BooleanField(default=False, verbose_name='운영비 여부', help_text='프로젝트 운영비 계정 거래 여부')

    class Meta:
        verbose_name = '08. 프로젝트 은행 거래'
        verbose_name_plural = '08. 프로젝트 은행 거래'
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
# Accounting Domain - 본사 / 현장 회계 분개 도메인
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
    trader = models.CharField(max_length=50, verbose_name='거래처', help_text='거래 상대방', null=True, blank=True)
    amount = models.PositiveBigIntegerField(verbose_name='금액', help_text='이 회계 분개의 금액 (분할 시 일부 금액)')
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

    # 관계회사/프로젝트 추적
    affiliate = models.ForeignKey('Affiliate', on_delete=models.PROTECT,
                                  null=True, blank=True, verbose_name='관계회사/프로젝트',
                                  help_text='관계회사 대여금, 투자금 등의 경우 필수 입력')

    # 감사 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['evidence_type']),
            models.Index(fields=['affiliate']),
        ]

    @property
    def related_transaction(self):
        """연관된 BankTransaction 조회"""
        # 클래스 타입으로 구분하여 적절한 BankTransaction 모델 조회
        if isinstance(self, CompanyAccountingEntry):
            return CompanyBankTransaction.objects.filter(
                transaction_id=self.transaction_id
            ).first()
        elif isinstance(self, ProjectAccountingEntry):
            return ProjectBankTransaction.objects.filter(
                transaction_id=self.transaction_id
            ).first()
        return None

    @property
    def sort(self):
        """BankTransaction의 sort 접근 (하위 호환성)"""
        transaction = self.related_transaction
        return transaction.sort if transaction else None

    def __str__(self):
        transaction = self.related_transaction
        sort_name = transaction.sort.name if transaction and transaction.sort else '미분류'
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

    class Meta:
        verbose_name = '04. 본사 회계 분개'
        verbose_name_plural = '04. 본사 회계 분개'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'created_at']),
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
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')

    # 프로젝트 계정 체계 (ProjectAccount 참조)
    account = models.ForeignKey(ProjectAccount, on_delete=models.PROTECT, verbose_name='계정 과목',
                                help_text='회계 분개에 사용할 계정 과목',
                                limit_choices_to={'is_active': True, 'is_category_only': False})

    class Meta:
        verbose_name = '09. 프로젝트 회계 분개'
        verbose_name_plural = '09. 프로젝트 회계 분개'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'created_at']),
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
    progress = models.IntegerField('진행률', default=0)
    total_records = models.IntegerField('전체 레코드', default=0)
    processed_records = models.IntegerField('처리된 레코드', default=0)
    success_count = models.IntegerField('성공 건수', default=0)
    error_count = models.IntegerField('오류 건수', default=0)
    error_message = models.TextField('오류 메시지', blank=True)
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
    def duration(self):
        """작업 소요 시간 계산"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def update_progress(self, processed: int, total: int, status: str = None):
        """진행률 업데이트"""
        self.processed_records = processed
        self.total_records = total
        if total > 0:
            self.progress = int((processed / total) * 100)
        if status:
            self.status = status
        self.save()
