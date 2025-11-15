from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from _utils.payment_adjustment import calculate_late_penalty
from company.models import Company
from project.models import Project


class BankCode(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=20, db_index=True)

    def __str__(self):
        return self.name


class CompanyBankAccount(models.Model):
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name='회사정보')
    order = models.PositiveSmallIntegerField('순서', null=True, blank=True)
    depart = models.ForeignKey('company.Department', on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name='관리부서')
    bankcode = models.ForeignKey(BankCode, on_delete=models.PROTECT, verbose_name='거래은행')
    alias_name = models.CharField('계좌별칭', max_length=20, db_index=True)
    number = models.CharField('계좌번호', max_length=30, blank=True)
    holder = models.CharField('예금주', max_length=20, blank=True)
    open_date = models.DateField('개설일자', null=True, blank=True)
    note = models.CharField('비고', max_length=50, blank=True)
    is_hide = models.BooleanField('숨기기 여부', default=False)
    inactive = models.BooleanField('비활성 여부', default=False)

    def __str__(self):
        return self.alias_name

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "01. 본사 관리계좌"
        verbose_name_plural = "01. 본사 관리계좌"


class CashBook(models.Model):
    company = models.ForeignKey('company.Company', on_delete=models.PROTECT, verbose_name='회사정보')
    sort = models.ForeignKey('ibs.AccountSort', on_delete=models.PROTECT, verbose_name='구분')
    account_d1 = models.ForeignKey('ibs.AccountSubD1', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='계정대분류')
    account_d2 = models.ForeignKey('ibs.AccountSubD2', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='계정중분류')
    account_d3 = models.ForeignKey('ibs.AccountSubD3', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='세부계정')
    project = models.ForeignKey('project.Project', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='투입 프로젝트')
    is_return = models.BooleanField('반환 정산 여부', default=False, help_text='관계회사(프로젝트) 대여금 반환 정산 여부')
    is_separate = models.BooleanField('상세 분리기록 등록', default=False,
                                      help_text='각기 다른 계정 항목이 1회에 같이 출금된 경우 이 항목을 체크')
    separated = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sepItems',
                                  verbose_name='분할 계정')
    content = models.CharField('적요', max_length=50, blank=True, default='')
    trader = models.CharField('거래처', max_length=25, blank=True, default='')
    bank_account = models.ForeignKey(CompanyBankAccount, on_delete=models.PROTECT, verbose_name='거래계좌')
    income = models.PositiveBigIntegerField('입금액', null=True, blank=True)
    outlay = models.PositiveBigIntegerField('출금액', null=True, blank=True)
    EVIDENCE_CHOICES = (
        ('0', '증빙 없음'), ('1', '세금계산서'), ('2', '계산서(면세)'),
        ('3', '카드전표/현금영수증'), ('4', '간이영수증'), ('5', '거래명세서'),
        ('6', '입금표'), ('7', '지출결의서'))
    evidence = models.CharField('지출증빙', max_length=1, choices=EVIDENCE_CHOICES, null=True, blank=True)
    note = models.CharField('비고', max_length=255, blank=True, default='')
    deal_date = models.DateField('거래일자')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_cashbooks', verbose_name='편집자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def __str__(self):
        return f'{self.pk}. {self.sort}'

    class Meta:
        ordering = ['-deal_date', '-id']
        verbose_name = '02. 본사 입출금거래'
        verbose_name_plural = '02. 본사 입출금거래'


class ProjectBankAccount(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order = models.PositiveSmallIntegerField('순서', null=True, blank=True)
    bankcode = models.ForeignKey(BankCode, on_delete=models.PROTECT, verbose_name='은행코드')
    alias_name = models.CharField('계좌별칭', max_length=20, db_index=True)
    number = models.CharField('계좌번호', max_length=30, blank=True)
    holder = models.CharField('예금주', max_length=20, blank=True)
    open_date = models.DateField('개설일자', null=True, blank=True)
    note = models.CharField('비고', max_length=50, blank=True)
    is_hide = models.BooleanField('숨기기 여부', default=False)
    inactive = models.BooleanField('비활성 여부', default=False)
    directpay = models.BooleanField('용역비 직불 여부', default=False)
    is_imprest = models.BooleanField('운영비 계좌 여부', default=False)

    def __str__(self):
        return self.alias_name

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "03. 프로젝트 관리계좌"
        verbose_name_plural = "03. 프로젝트 관리계좌"


class ProjectCashBookQuerySet(models.QuerySet):
    """ProjectCashBook 전용 QuerySet - 납부내역 필터링 및 조정금액 조회"""

    def payment_records(self):
        """
        유효 계약자의 납부내역 (선납 할인 및 연체 가산금 계산 대상)

        is_payment=True는 현재 유효한 계약자가 납부한 입금만을 의미
        - 포함: 111 (분담금), 811 (분양매출금)
        - 제외: is_payment=False인 모든 계정 (해지 입금, 환불, 기타 60여개 출금 계정)

        Note:
            is_payment=True는 이미 입금만 포함하므로 income 필터 불필요
            선납 할인 및 연체 가산금 계산의 기본 대상

        Returns:
            QuerySet: 유효 계약자 납부 내역 (입금만), select_related 최적화 적용
        """
        return self.filter(
            project_account_d3__is_payment=True
        ).select_related(
            'project_account_d3',
            'project_account_d2',
            'installment_order',
            'contract',
            'contract__project',
            'contract__unit_type'
        )

    def for_contract(self, contract):
        """특정 계약의 전체 내역"""
        return self.filter(contract=contract)

    def for_installment(self, installment_order):
        """특정 회차의 전체 내역"""
        return self.filter(installment_order=installment_order)

    def with_discount_eligible(self):
        """선납 할인 대상 회차 필터"""
        return self.filter(installment_order__is_prep_discount=True)

    def with_penalty_eligible(self):
        """연체 가산 대상 회차 필터"""
        return self.filter(installment_order__is_late_penalty=True)


class ProjectCashBookManager(models.Manager):
    """ProjectCashBook 전용 Manager"""

    def get_queryset(self):
        return ProjectCashBookQuerySet(self.model, using=self._db)

    def payment_records(self):
        """유효 계약자 납부내역 (선납 할인 및 연체 가산금 계산 대상)"""
        return self.get_queryset().payment_records()

    def for_contract(self, contract):
        """특정 계약의 전체 내역"""
        return self.get_queryset().for_contract(contract)

    def for_installment(self, installment_order):
        """특정 회차의 전체 내역"""
        return self.get_queryset().for_installment(installment_order)


class ProjectCashBook(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.PROTECT, verbose_name='프로젝트')
    sort = models.ForeignKey('ibs.AccountSort', on_delete=models.PROTECT,
                             verbose_name='구분')  # icp=True -> 1=수납 or 2=환불
    project_account_d2 = models.ForeignKey('ibs.ProjectAccountD2', on_delete=models.PROTECT, null=True, blank=True,
                                           verbose_name='프로젝트 계정')
    project_account_d3 = models.ForeignKey('ibs.ProjectAccountD3', on_delete=models.PROTECT, null=True, blank=True,
                                           verbose_name='프로젝트 세부계정')
    is_separate = models.BooleanField('상세 분리기록 등록', default=False,
                                      help_text='각기 다른 계정 항목이 1회에 같이 출금된 경우 이 항목을 체크')
    separated = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sepItems',
                                  verbose_name='분할 계정')
    is_imprest = models.BooleanField('운영비 항목 여부', default=False, help_text='전도금 대체 후 해당 전도금(운영비) 항목을 상세 기록하는 경우 이 항목')
    contract = models.ForeignKey('contract.Contract', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='payments', verbose_name='계약일련번호')  # 계약일련번호  (프로젝트 귀속)
    installment_order = models.ForeignKey('payment.InstallmentPaymentOrder', on_delete=models.SET_NULL,
                                          null=True, blank=True, verbose_name='납부회차')  # 분할납부차수  (프로젝트 귀속)
    refund_contractor = models.ForeignKey('contract.Contractor', on_delete=models.PROTECT, null=True,
                                          blank=True, verbose_name='환불 계약자',
                                          help_text='이 건 거래가 환불금 출금인 경우 이 건을 납부한 계약자를 선택')  # 환불 종결 여부
    content = models.CharField('적요', max_length=50, blank=True, default='')
    trader = models.CharField('거래처', max_length=25, blank=True, default='',
                              help_text='분양대금(분담금) 수납 건인 경우 반드시 해당 계좌에 기재된 입금자를 기재')  # icp=True -> 분양대금 납입자
    bank_account = models.ForeignKey(ProjectBankAccount, on_delete=models.PROTECT,
                                     verbose_name='거래계좌')  # icp=True -> 분양대금 납입계좌
    income = models.PositiveBigIntegerField('입금액', null=True, blank=True)  # icp=True -> 분양대금 납입금액
    outlay = models.PositiveBigIntegerField('출금액', null=True, blank=True)  # icp=True -> 분양대금 환불금액
    EVIDENCE_CHOICES = (
        ('0', '증빙 없음'), ('1', '세금계산서'), ('2', '계산서(면세)'),
        ('3', '카드전표/현금영수증'), ('4', '간이영수증'), ('5', '거래명세서'),
        ('6', '입금표'), ('7', '지출결의서'))
    evidence = models.CharField('지출증빙', max_length=1, choices=EVIDENCE_CHOICES, null=True, blank=True)
    note = models.TextField('비고', blank=True, default='')
    deal_date = models.DateField('거래일자')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_project_cashbooks', verbose_name='편집자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    # Custom Manager 설정
    objects = ProjectCashBookManager()

    @property
    def is_parent(self):
        """
        이 레코드가 실제 은행 거래(부모 레코드)인지 확인

        Returns:
            bool: 부모 레코드 여부
        """
        return not self.is_separate and self.separated is None

    @property
    def is_child(self):
        """
        이 레코드가 분리 항목(자식 레코드)인지 확인

        Returns:
            bool: 자식 레코드 여부
        """
        return self.is_separate and self.separated is not None

    @property
    def split_balance_valid(self):
        """
        분리 항목들의 금액 합계가 부모 금액과 일치하는지 검증

        Returns:
            bool: 금액 일치 여부 (자식 레코드인 경우 항상 True)
        """
        if not self.is_parent:
            return True

        children_sum = self.sepItems.aggregate(
            total_outlay=Sum('outlay'),
            total_income=Sum('income')
        )

        expected_outlay = self.outlay or 0
        expected_income = self.income or 0
        actual_outlay = children_sum['total_outlay'] or 0
        actual_income = children_sum['total_income'] or 0

        return (expected_outlay == actual_outlay and expected_income == actual_income)

    def __str__(self):
        return f'{self.pk}. {self.sort}'

    def clean(self):
        """
        모델 레벨 데이터 검증

        Raises:
            ValidationError: 검증 실패 시
        """

        errors = {}

        # 1. 자기 참조 방지
        if self.separated and self.separated == self:
            errors['separated'] = '자기 자신을 참조할 수 없습니다.'

        # 2. 순환 참조 방지 (1단계만 체크 - 현재 요구사항에 충분)
        if self.separated and self.separated.separated == self:
            errors['separated'] = '순환 참조가 감지되었습니다.'

        # 3. 분리 레코드는 반드시 부모 필요
        if self.is_separate and not self.separated:
            errors['separated'] = '분리 레코드는 부모 거래를 참조해야 합니다.'

        # 4. 부모 레코드는 separated 필드가 NULL이어야 함
        if not self.is_separate and self.separated:
            errors['is_separate'] = '부모 거래는 is_separate가 False여야 합니다.'

        # 5. 입금과 출금 중 하나만 있어야 함 (둘 다 양수인 경우만 체크)
        if self.income and self.income > 0 and self.outlay and self.outlay > 0:
            errors['__all__'] = '입금과 출금을 동시에 등록할 수 없습니다.'

        # 6. 부모 레코드는 입금 또는 출금이 반드시 하나는 있어야 함
        # 자식 레코드는 0원 항목이 있을 수 있으므로 제외
        if not self.is_separate and not self.separated:  # 부모 레코드만
            if (not self.income or self.income == 0) and (not self.outlay or self.outlay == 0):
                errors['__all__'] = '입금 또는 출금 금액을 입력해야 합니다.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        저장 시 검증 수행
        """
        # skip_validation이 True인 경우 검증 건너뛰기 (마이그레이션 등에서 사용)
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)

    def get_late_penalty(self):
        """
        개별 납부건의 연체 가산금 조회

        Returns:
            dict or None: 연체 가산금 정보 또는 None (가산 대상이 아닌 경우)
                {
                    'penalty_amount': int,
                    'late_days': int,
                    'penalty_rate': Decimal,
                    'payment_amount': int,
                    'payment_date': date,
                    'due_date': date
                }
        """
        return calculate_late_penalty(self)

    def is_discount_eligible(self):
        """
        선납 할인 대상 여부 (회차 및 계정 기준)

        Note:
            is_payment=True인 유효 계약자 납부만 할인 대상 (111, 811)
            is_payment=False인 모든 계정은 제외

        Returns:
            bool: 선납 할인 대상 여부
        """
        return (
                self.installment_order and
                self.installment_order.is_prep_discount and
                self.project_account_d3 and
                self.project_account_d3.is_payment
        )

    def is_penalty_eligible(self):
        """
        연체 가산 대상 여부 (회차 및 계정 기준)

        Note:
            is_payment=True인 유효 계약자 납부만 가산 대상 (111, 811)
            is_payment=False인 모든 계정은 제외

        Returns:
            bool: 연체 가산 대상 여부
        """
        return (
                self.installment_order and
                self.installment_order.is_late_penalty and
                self.project_account_d3 and
                self.project_account_d3.is_payment
        )

    class Meta:
        ordering = ['-deal_date', '-id']
        verbose_name = '04. 프로젝트 입출금거래'
        verbose_name_plural = '04. 프로젝트 입출금거래'
        indexes = [
            models.Index(fields=['separated'], name='idx_pcb_separated'),
            models.Index(fields=['is_separate', 'deal_date'], name='idx_pcb_issep_date'),
        ]


class CompanyCashBookCalculation(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, unique=True, verbose_name='회사')
    calculated = models.DateField('정산일', null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')

    def __str__(self):
        return f'{self.company} 결산일 : {self.calculated}'


class ProjectCashBookCalculation(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, unique=True, verbose_name='프로젝트')
    calculated = models.DateField('정산일', null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')

    def __str__(self):
        return f'{self.project} 결산일 : {self.calculated}'


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
        ('cashbook', 'CashBook'),
        ('project_cashbook', 'ProjectCashBook'),
    ]

    job_type = models.CharField('작업 유형', max_length=10, choices=JOB_TYPE_CHOICES)
    resource_type = models.CharField('리소스 유형', max_length=20, choices=RESOURCE_TYPE_CHOICES)
    file = models.FileField('파일', upload_to='import_jobs/', blank=True, null=True)
    task_id = models.CharField('태스크 ID', max_length=255, blank=True)
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default=PENDING)
    progress = models.IntegerField('진행률', default=0)
    total_records = models.IntegerField('전체 레코드', default=0)
    processed_records = models.IntegerField('처리된 레코드', default=0)
    success_count = models.IntegerField('성공 건수', default=0)
    error_count = models.IntegerField('오류 건수', default=0)
    error_message = models.TextField('오류 메시지', blank=True)
    result_file = models.FileField('결과 파일', upload_to='export_results/', blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='생성자')
    created_at = models.DateTimeField('생성일시', auto_now_add=True)
    started_at = models.DateTimeField('시작일시', blank=True, null=True)
    completed_at = models.DateTimeField('완료일시', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '가져오기/내보내기 작업'
        verbose_name_plural = '가져오기/내보내기 작업'

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
        self.progress = int((processed / total) * 100) if total > 0 else 0
        if status:
            self.status = status
        self.save(update_fields=['processed_records', 'total_records', 'progress', 'status'])
