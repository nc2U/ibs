from django.db import models
from django.conf import settings

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
    project = models.ForeignKey('project.Project', on_delete=models.SET_NULL, null=True, verbose_name='투입 프로젝트')
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    def __str__(self):
        return f'{self.pk}. {self.sort}'

    class Meta:
        ordering = ['-deal_date', '-id']
        verbose_name = '04. 프로젝트 입출금거래'
        verbose_name_plural = '04. 프로젝트 입출금거래'


class CompanyCashBookCalculation(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, unique=True, verbose_name='회사')
    calculated = models.DateField('정산일', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')

    def __str__(self):
        return f'{self.company} 결산일 : {self.calculated}'


class ProjectCashBookCalculation(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, unique=True, verbose_name='프로젝트')
    calculated = models.DateField('정산일', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')

    def __str__(self):
        return f'{self.project} 결산일 : {self.calculated}'
