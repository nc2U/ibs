from django.conf import settings
from django.db import models

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_upload_path, populate_file_meta


class SalesAgency(models.Model):
    """분양 대행사 (직영 사업부 또는 외주 대행사)"""

    project = models.ForeignKey(
        'project.Project', on_delete=models.CASCADE,
        related_name='sales_agencies', verbose_name='프로젝트'
    )
    name = models.CharField('대행사명', max_length=100)
    is_direct_managed = models.BooleanField(
        '직영 여부', default=True,
        help_text='자체 직영 분양팀인 경우 체크'
    )
    business_number = models.CharField('사업자등록번호', max_length=20, blank=True, default='')
    ceo_name = models.CharField('대표자명', max_length=50, blank=True, default='')
    phone = models.CharField('대표 전화', max_length=20, blank=True, default='')
    order = models.PositiveSmallIntegerField('정렬 순서', default=1)
    is_active = models.BooleanField('사용 여부', default=True)
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['project', 'order', 'id']
        verbose_name = '01. 분양 대행사'
        verbose_name_plural = '01. 분양 대행사 목록'

    def __str__(self):
        direct_tag = '[직영]' if self.is_direct_managed else '[외주]'
        return f'{direct_tag} {self.name} ({self.project})'


class SalesTeam(models.Model):
    """영업 조직 (본부 / 팀)"""

    agency = models.ForeignKey(
        SalesAgency, on_delete=models.CASCADE,
        related_name='teams', verbose_name='분양 대행사'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sub_teams',
        verbose_name='상위 조직 (본부)'
    )
    name = models.CharField('조직/팀명', max_length=100)
    order = models.PositiveSmallIntegerField('정렬 순서', default=1)
    is_active = models.BooleanField('사용 여부', default=True)
    created_at = models.DateTimeField('등록일시', auto_now_add=True)

    class Meta:
        ordering = ['agency', 'order', 'id']
        verbose_name = '02. 영업 조직/팀'
        verbose_name_plural = '02. 영업 조직/팀 목록'

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} > {self.name}'
        return self.name


class SalesPerson(models.Model):
    """영업 인력 (분양상담사 / 팀장 / 본부장 / 프리랜서)"""

    DUTY_CHOICES = (
        ('1', '분양상담사'),
        ('2', '팀장'),
        ('3', '본부장'),
        ('4', '총괄본부장'),
        ('5', '지원/기타'),
    )
    STATUS_CHOICES = (
        ('1', '재직 (활동 중)'),
        ('2', '휴직'),
        ('3', '해촉 (퇴사)'),
    )
    TAX_TYPE_CHOICES = (
        ('1', '3.3% 사업소득 (프리랜서)'),
        ('2', '근로소득'),
        ('3', '사업자 (세금계산서)'),
        ('4', '기타'),
    )

    team = models.ForeignKey(
        SalesTeam, on_delete=models.PROTECT,
        related_name='members', verbose_name='소속 팀'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sales_profiles',
        verbose_name='시스템 연동 계정',
        help_text='로그인 계정이 부여된 경우 연동'
    )
    name = models.CharField('성명', max_length=50)
    duty = models.CharField('직책', max_length=2, choices=DUTY_CHOICES, default='1')
    status = models.CharField('상태', max_length=2, choices=STATUS_CHOICES, default='1')
    phone = models.CharField('연락처', max_length=20)
    id_number = models.CharField(
        '주민등록번호', max_length=20, blank=True, default='',
        help_text='원천세 신고용 (앞자리 또는 마스킹 식별번호)'
    )
    tax_type = models.CharField('소득 구분', max_length=2, choices=TAX_TYPE_CHOICES, default='1')
    bank_name = models.CharField('정산 은행', max_length=30, blank=True, default='')
    account_number = models.CharField('계좌번호', max_length=50, blank=True, default='')
    account_holder = models.CharField('예금주', max_length=50, blank=True, default='')
    join_date = models.DateField('위촉/입사일', null=True, blank=True)
    quit_date = models.DateField('해촉/퇴사일', null=True, blank=True)
    notes = models.TextField('비고/특이사항', blank=True, default='')
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['team', 'duty', 'name']
        verbose_name = '03. 영업 인력'
        verbose_name_plural = '03. 영업 인력 목록'

    def __str__(self):
        return f'{self.name} ({self.get_duty_display()} / {self.team})'


class CommissionPolicy(models.Model):
    """수수료 정책 (유니트/타입별 건당 인센티브 기준표)"""

    PAY_CONDITION_CHOICES = (
        ('1', '계약금 100% 완납 시 전액 지급'),
        ('2', '계약금 1차 납부 시 50%, 2차 완납 시 50% 분할 지급'),
        ('3', '공급계약 체결 시 지급'),
        ('4', '청약/가계약금 납부 시 선지급'),
    )

    project = models.ForeignKey(
        'project.Project', on_delete=models.CASCADE,
        related_name='commission_policies', verbose_name='프로젝트'
    )
    order_group = models.ForeignKey(
        'contract.OrderGroup', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='차수'
    )
    unit_type = models.ForeignKey(
        'items.UnitType', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='타입',
        help_text='미지정 시 해당 차수/프로젝트 전체 공통 적용'
    )
    name = models.CharField('정책명', max_length=100, help_text='예: 84A 정규 분양 수수료 기준')
    agent_fee = models.PositiveIntegerField('상담사 건당 수수료 (원)', default=0)
    leader_fee = models.PositiveIntegerField('팀장 건당 수수료 (원)', default=0)
    director_fee = models.PositiveIntegerField('본부장 건당 수수료 (원)', default=0)
    agency_fee = models.PositiveIntegerField('대행사 건당 수수료 (원)', default=0)
    pay_condition = models.CharField('지급 조건', max_length=2, choices=PAY_CONDITION_CHOICES, default='1')
    start_date = models.DateField('적용 시작일')
    end_date = models.DateField('적용 종료일', null=True, blank=True)
    is_active = models.BooleanField('활성 여부', default=True)
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['project', '-start_date', 'id']
        verbose_name = '04. 수수료 정책'
        verbose_name_plural = '04. 수수료 정책 목록'

    def __str__(self):
        type_str = f' - {self.unit_type.name}' if self.unit_type else ' (전체 공통)'
        return f'{self.name}{type_str} ({self.project})'


class ContractSalesAgent(models.Model):
    """계약별 영업 담당자 매핑 (Contract ↔ SalesPerson)"""

    contract = models.OneToOneField(
        'contract.Contract', on_delete=models.CASCADE,
        related_name='sales_agent_mapping', verbose_name='분양 계약'
    )
    sales_person = models.ForeignKey(
        SalesPerson, on_delete=models.PROTECT,
        related_name='contract_mappings', verbose_name='담당 영업직원 (상담사)'
    )
    team = models.ForeignKey(
        SalesTeam, on_delete=models.PROTECT,
        related_name='contract_mappings', verbose_name='소속 팀'
    )
    policy = models.ForeignKey(
        CommissionPolicy, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contract_mappings',
        verbose_name='적용 수수료 정책'
    )
    contract_date = models.DateField('영업 성과 인정일', null=True, blank=True)
    mgm_name = models.CharField('MGM/중개사 성명', max_length=50, blank=True, default='')
    mgm_phone = models.CharField('MGM 연락처', max_length=20, blank=True, default='')
    mgm_fee = models.PositiveIntegerField('MGM 지급 수수료 (원)', default=0)
    note = models.CharField('비고', max_length=255, blank=True, default='')
    is_settlement_approved = models.BooleanField(
        '수수료 정산 승인', default=True,
        help_text='서류 완비 및 완납 확인 후 승인 시 정산 대상에 포함'
    )
    approval_note = models.CharField(
        '정산 승인/보류 사유', max_length=255, blank=True, default='',
        help_text='보류 사유 예: 계약금 2차 미납, 인감증명서 미징구 등'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='승인 관리자'
    )
    approved_at = models.DateTimeField('승인일시', null=True, blank=True)
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['-contract_date', '-id']
        verbose_name = '05. 계약 영업 매핑'
        verbose_name_plural = '05. 계약 영업 매핑 목록'

    def __str__(self):
        return f'{self.contract} ➔ {self.sales_person.name} ({self.team.name})'

    def save(self, *args, **kwargs):
        # 소속 팀이 명시되지 않았을 경우 영업직원의 팀으로 자동 설정
        if not self.team_id and self.sales_person_id:
            self.team = self.sales_person.team
        super().save(*args, **kwargs)


class SettlementPeriod(models.Model):
    """수수료 정산 회차 (월별 / 주기별 정산 대장)"""

    STATUS_CHOICES = (
        ('1', '정산 작성 중'),
        ('2', '정산 확정 (승인 대기)'),
        ('3', '지급 완료'),
    )

    project = models.ForeignKey(
        'project.Project', on_delete=models.CASCADE,
        related_name='settlement_periods', verbose_name='프로젝트'
    )
    title = models.CharField('정산 회차명', max_length=100, help_text='예: 2026년 9월 1회차 수수료 정산')
    start_date = models.DateField('정산 대상 시작일')
    end_date = models.DateField('정산 대상 종료일')
    payout_date = models.DateField('지급 예정일', null=True, blank=True)
    status = models.CharField('정산 상태', max_length=2, choices=STATUS_CHOICES, default='1')
    total_contracts = models.PositiveIntegerField('정산 계약 건수', default=0)
    total_gross_amount = models.PositiveBigIntegerField('총 지급액 (세전)', default=0)
    total_tax_amount = models.PositiveBigIntegerField('총 원천세 (3.3%)', default=0)
    total_net_amount = models.PositiveBigIntegerField('총 실지급액 (세후)', default=0)
    agency_fee_total = models.PositiveBigIntegerField('대행사 수수료(차지) 합계', default=0)
    billing_supply_price = models.PositiveBigIntegerField('시행사 청구 공급가액 (VAT 별도)', default=0)
    billing_vat = models.PositiveBigIntegerField('시행사 청구 부가가치세 (10%)', default=0)
    billing_total_amount = models.PositiveBigIntegerField('시행사 총 청구금액 (VAT 포함)', default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='작성자'
    )
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['project', '-start_date', '-id']
        verbose_name = '06. 수수료 정산 회차'
        verbose_name_plural = '06. 수수료 정산 회차 목록'

    def __str__(self):
        return f'[{self.get_status_display()}] {self.title} ({self.project})'


class CommissionPayout(models.Model):
    """개인별 수수료 정산 및 지급 내역"""

    PAY_STATUS_CHOICES = (
        ('1', '대기'),
        ('2', '승인'),
        ('3', '지급 완료'),
        ('4', '지급 보류'),
    )

    period = models.ForeignKey(
        SettlementPeriod, on_delete=models.CASCADE,
        related_name='payouts', verbose_name='정산 회차'
    )
    sales_person = models.ForeignKey(
        SalesPerson, on_delete=models.PROTECT,
        related_name='payouts', verbose_name='영업 인력'
    )
    base_pay = models.PositiveIntegerField('기본급/일비', default=0)
    contract_count = models.PositiveIntegerField('계약 건수', default=0)
    commission_amount = models.PositiveBigIntegerField('계약 인센티브 합계', default=0)
    bonus_amount = models.PositiveIntegerField('보너스/활동비', default=0)
    deduction_amount = models.PositiveIntegerField('공제/환수액', default=0)
    gross_amount = models.PositiveBigIntegerField(
        '총 지급액 (세전)', default=0,
        help_text='기본급 + 인센티브 + 보너스 - 공제액'
    )
    # 3.3% 원천징수 세금 필드
    income_tax = models.PositiveIntegerField('사업소득세 (3%)', default=0)
    local_income_tax = models.PositiveIntegerField('지방소득세 (0.3%)', default=0)
    total_tax = models.PositiveIntegerField('원천징수 합계 (3.3%)', default=0)
    net_amount = models.PositiveBigIntegerField('실지급액 (세후)', default=0)
    pay_status = models.CharField('지급 상태', max_length=2, choices=PAY_STATUS_CHOICES, default='1')
    paid_date = models.DateField('실제 지급일', null=True, blank=True)
    bank_name = models.CharField('입금 은행', max_length=30, blank=True, default='')
    account_number = models.CharField('입금 계좌', max_length=50, blank=True, default='')
    account_holder = models.CharField('예금주', max_length=50, blank=True, default='')
    note = models.TextField('비고/정산 메모', blank=True, default='')
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['period', 'sales_person__duty', 'sales_person__name']
        unique_together = ('period', 'sales_person')
        verbose_name = '07. 수수료 지급 명세'
        verbose_name_plural = '07. 수수료 지급 명세 목록'

    def __str__(self):
        return f'{self.sales_person.name} - {self.gross_amount:,}원 (실지급: {self.net_amount:,}원)'

    def calculate_taxes(self):
        """총 지급액 및 3.3% 원천징수 세금 자동 계산"""
        self.gross_amount = max(0, self.base_pay + self.commission_amount + self.bonus_amount - self.deduction_amount)

        if self.sales_person.tax_type == '1':  # 3.3% 프리랜서 사업소득
            # 소득세 3% (원 단위 절사)
            self.income_tax = int(self.gross_amount * 0.03 // 10 * 10)
            # 지방소득세 0.3% (소득세의 10%, 원 단위 절사)
            self.local_income_tax = int(self.income_tax * 0.1 // 10 * 10)
            self.total_tax = self.income_tax + self.local_income_tax
        else:
            self.income_tax = 0
            self.local_income_tax = 0
            self.total_tax = 0

        self.net_amount = max(0, self.gross_amount - self.total_tax)

    def save(self, *args, **kwargs):
        # 계좌 정보 동기화 (비어있는 경우 영업인력 프로필 계좌 복사)
        if not self.bank_name and self.sales_person_id:
            self.bank_name = self.sales_person.bank_name
            self.account_number = self.sales_person.account_number
            self.account_holder = self.sales_person.account_holder
        self.calculate_taxes()
        super().save(*args, **kwargs)


class PayoutContractDetail(models.Model):
    """지급 내역에 포함된 개별 계약 건 상세 내역"""

    ROLE_CHOICES = (
        ('agent', '상담사 인센티브'),
        ('leader', '팀장 인센티브'),
        ('director', '본부장 인센티브'),
        ('mgm', 'MGM 수수료'),
    )

    payout = models.ForeignKey(
        CommissionPayout, on_delete=models.CASCADE,
        related_name='contract_details', verbose_name='수수료 지급 명세'
    )
    contract = models.ForeignKey(
        'contract.Contract', on_delete=models.PROTECT,
        related_name='sales_payout_details', verbose_name='분양 계약'
    )
    role_type = models.CharField('지급 구분', max_length=10, choices=ROLE_CHOICES, default='agent')
    unit_fee = models.PositiveIntegerField('지급 수수료 (원)', default=0)

    class Meta:
        ordering = ['payout', 'contract']
        verbose_name = '08. 지급 대상 계약 상세'
        verbose_name_plural = '08. 지급 대상 계약 상세 목록'

    def __str__(self):
        return f'{self.payout.sales_person.name} ➔ {self.contract} ({self.unit_fee:,}원)'


class CommissionClawback(models.Model):
    """계약 해지 시 수수료 환수 관리"""

    contract = models.ForeignKey(
        'contract.Contract', on_delete=models.CASCADE,
        related_name='sales_clawbacks', verbose_name='해지 계약'
    )
    sales_person = models.ForeignKey(
        SalesPerson, on_delete=models.PROTECT,
        related_name='clawbacks', verbose_name='환수 대상자'
    )
    amount = models.PositiveIntegerField('환수 금액 (원)', default=0)
    reason = models.CharField('환수 사유', max_length=200, default='계약 해지에 따른 수수료 환수')
    is_settled = models.BooleanField('차기 정산 상계 완료 여부', default=False)
    settled_payout = models.ForeignKey(
        CommissionPayout, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='settled_clawbacks',
        verbose_name='상계 처리된 정산 명세'
    )
    created_at = models.DateTimeField('환수 등록일시', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '09. 수수료 환수 관리'
        verbose_name_plural = '09. 수수료 환수 관리 목록'

    def __str__(self):
        settled_tag = '[상계완료]' if self.is_settled else '[미상계]'
        return f'{settled_tag} {self.sales_person.name} - {self.contract} ({self.amount:,}원)'


class AgencyPayout(models.Model):
    """외주 대행사 단위 정산 지급 내역 (시행사 → 대행사 지급 기록)"""

    PAY_STATUS_CHOICES = (
        ('1', '대기'),
        ('2', '승인'),
        ('3', '지급 완료'),
        ('4', '지급 보류'),
    )

    period = models.ForeignKey(
        SettlementPeriod, on_delete=models.CASCADE,
        related_name='agency_payouts', verbose_name='정산 회차'
    )
    agency = models.ForeignKey(
        SalesAgency, on_delete=models.PROTECT,
        related_name='payouts', verbose_name='분양 대행사'
    )
    contract_count = models.PositiveIntegerField('계약 건수', default=0)
    agency_fee_sum = models.PositiveBigIntegerField(
        '대행사 수수료 합계 (VAT 제외)', default=0,
        help_text='CommissionPolicy.agency_fee × 계약 건수'
    )
    vat_amount = models.PositiveBigIntegerField('부가가치세 (10%)', default=0)
    total_amount = models.PositiveBigIntegerField(
        '총 지급액 (VAT 포함)', default=0,
        help_text='agency_fee_sum + vat_amount'
    )
    pay_status = models.CharField('지급 상태', max_length=2, choices=PAY_STATUS_CHOICES, default='1')
    paid_date = models.DateField('실제 지급일', null=True, blank=True)
    business_number = models.CharField('사업자등록번호', max_length=20, blank=True, default='')
    bank_name = models.CharField('입금 은행', max_length=30, blank=True, default='')
    account_number = models.CharField('입금 계좌', max_length=50, blank=True, default='')
    account_holder = models.CharField('예금주', max_length=50, blank=True, default='')
    note = models.TextField('비고/정산 메모', blank=True, default='')
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['period', 'agency']
        unique_together = ('period', 'agency')
        verbose_name = '10. 대행사 수수료 지급 명세'
        verbose_name_plural = '10. 대행사 수수료 지급 명세 목록'

    def __str__(self):
        return f'[외주] {self.agency.name} - {self.total_amount:,}원 (VAT 포함)'

    def calculate_vat(self):
        """VAT 10% 자동 계산"""
        self.vat_amount = int(self.agency_fee_sum * 0.1 // 10 * 10)
        self.total_amount = self.agency_fee_sum + self.vat_amount

    def save(self, *args, **kwargs):
        # 대행사 사업자정보 동기화
        if not self.business_number and self.agency_id:
            self.business_number = self.agency.business_number
        self.calculate_vat()
        super().save(*args, **kwargs)


class AgencyPayoutContractDetail(models.Model):
    """대행사 지급 내역에 포함된 개별 계약 건 상세"""

    payout = models.ForeignKey(
        AgencyPayout, on_delete=models.CASCADE,
        related_name='contract_details', verbose_name='대행사 지급 명세'
    )
    contract = models.ForeignKey(
        'contract.Contract', on_delete=models.PROTECT,
        related_name='agency_payout_details', verbose_name='분양 계약'
    )
    unit_fee = models.PositiveIntegerField('대행사 건당 수수료 (원)', default=0)

    class Meta:
        ordering = ['payout', 'contract']
        verbose_name = '11. 대행사 지급 대상 계약 상세'
        verbose_name_plural = '11. 대행사 지급 대상 계약 상세 목록'

    def __str__(self):
        return f'{self.payout.agency.name} ➔ {self.contract} ({self.unit_fee:,}원)'


def get_sales_docs_upload_path(instance, filename):
    return get_upload_path(instance, filename, 'sales', 'person_docs')


class SalesPersonDocument(models.Model):
    """영업 인력 제출 증빙 서류 (등본, 통장사본, 각서 등)"""

    DOC_TYPE_CHOICES = (
        ('1', '주민등록등본/초본'),
        ('2', '통장 사본 (계좌 사본)'),
        ('3', '신분증 사본'),
        ('4', '영업 위촉계약서'),
        ('5', '각종 서약서/각서'),
        ('9', '기타 증빙서류'),
    )

    sales_person = models.ForeignKey(
        SalesPerson, on_delete=models.CASCADE,
        related_name='documents', verbose_name='영업 인력'
    )
    doc_type = models.CharField('서류 구분', max_length=2, choices=DOC_TYPE_CHOICES, default='1')
    title = models.CharField(
        '서류 세부 명칭', max_length=100, blank=True, default='',
        help_text='서류 세부 명칭 (예: 보안서약서, 청렴각서, 사업자등록증 등. 미입력 시 서류 구분이 기본 적용됩니다)'
    )
    file = models.FileField(upload_to=get_sales_docs_upload_path, verbose_name='첨부 파일')
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('파일 타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('파일 크기', null=True, blank=True)

    # 관리자 진위 확인 프로세스
    is_verified = models.BooleanField('서류 검증 여부', default=False, help_text='관리자가 서류 유효성을 확인한 경우 체크')
    verified_at = models.DateTimeField('검증일시', null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='verified_sales_docs', verbose_name='검증자'
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='uploaded_sales_docs', verbose_name='등록자'
    )
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['sales_person', 'doc_type', '-created_at']
        verbose_name = '10. 영업 인력 제출 서류'
        verbose_name_plural = '10. 영업 인력 제출 서류 목록'

    def __str__(self):
        return f'{self.sales_person.name} - {self.title or self.get_doc_type_display()}'

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.get_doc_type_display()
        populate_file_meta(self)
        super().save(*args, **kwargs)


file_cleanup_signals(SalesPersonDocument)
