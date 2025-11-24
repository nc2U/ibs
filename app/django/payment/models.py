from django.core.exceptions import ValidationError
from django.db import models

from items.models import UnitType


class InstallmentPaymentOrder(models.Model):  # 분할 납부 차수 등록
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    type_sort = models.CharField('타입종류', max_length=1, choices=UnitType.SORT_CHOICES, default='1')
    PAY_SORT_CHOICES = (('1', '계약금'), ('2', '중도금'), ('3', '잔금'), ('4', '계약금 정산'), ('5', '미납 연체료'),
                        ('6', '기타 부담금'), ('7', '제세 공과금'), ('8', '후불 이자'), ('9', '업무 대행비'))
    pay_sort = models.CharField('종류', max_length=1, choices=PAY_SORT_CHOICES, default='1')
    is_except_price = models.BooleanField('공급가 불포함 여부', default=False, help_text='취등록세, 후불 이자 등 공급가 불포함 항목인지 여부')
    pay_code = models.PositiveSmallIntegerField('납입회차 코드', help_text='프로젝트 내 납부회차별 코드번호 - 동일 회차 중복(분리) 등록 가능')
    pay_time = models.PositiveSmallIntegerField('납부순서',
                                                help_text='''동일 납부회차에 2가지 항목을 분리해서 납부하여야 하는 경우(ex: 분담금 + 업무대행료)
                                                하나의 납입회차 코드(ex: 1)에 2개의 납부순서(ex: 1, 2)를 등록한다.''')
    pay_name = models.CharField('납부회차 명', max_length=20, db_index=True)
    alias_name = models.CharField('회차 별칭', max_length=20, blank=True, db_index=True)
    pay_amt = models.PositiveIntegerField('납부 약정금액', null=True, blank=True,
                                          help_text='약정금이 차수, 타입/층수에 관계 없이 정액인 경우 설정 (예: 세대별 업무대행비)')
    pay_ratio = models.DecimalField('회당 납부비율(%)', max_digits=5, decimal_places=2, null=True, blank=True,
                                    help_text='''분양가 대비 납부비율, 계약금 항목인 경우 Downpayment 
                                    테이블 데이터 우선, 잔금 항목인 경우 분양가와 비교 차액 데이터 우선''')
    pay_due_date = models.DateField('냡부 약정일', null=True, blank=True, help_text="특정일자를 납부기한으로 지정할 경우")
    days_since_prev = models.PositiveSmallIntegerField('전회 기준 경과일수', null=True, blank=True,
                                                       help_text="전 회차(예: 계약일)로부터 __일 이내 형식으로 납부기한을 지정할 경우 해당 일수")
    is_prep_discount = models.BooleanField('선납할인 적용 여부', default=False)
    prep_discount_ratio = models.DecimalField('선납할인율(%)', max_digits=5, decimal_places=2, null=True, blank=True)
    prep_ref_date = models.DateField('선납 기준일', null=True, blank=True,
                                     help_text='선납 할인 기준은 납부 약정일이 원칙이나 이 값이 있는 경우 선납 기준일로 우선 적용한다.')
    is_late_penalty = models.BooleanField('연체가산 적용 여부', default=False)
    late_penalty_ratio = models.DecimalField('연체가산율(%)', max_digits=5, decimal_places=2, null=True, blank=True)
    extra_due_date = models.DateField('연체 기준일', null=True, blank=True,
                                      help_text='연체료 계산 기준은 납부 약정일이 원칙이나 이 값이 있는 경우 연체 기준일로 우선 적용한다.')

    # 계약금 계산 방식 선택 (계약금에만 적용)
    CALCULATION_METHOD_CHOICES = (
        ('auto', '자동 (기존 우선순위)'),  # 기본값: PaymentPerInstallment → DownPayment → pay_ratio
        ('ratio', '분양가 × 납부비율'),  # pay_ratio 강제 사용
        ('downpayment', 'DownPayment 우선'),  # DownPayment 강제 사용 (없으면 pay_ratio)
    )
    calculation_method = models.CharField(
        '계약금 계산 방식',
        max_length=20,
        choices=CALCULATION_METHOD_CHOICES,
        default='auto',
        help_text='계약금(pay_sort=1) 항목의 계산 방식 선택. 다른 납부 항목에는 적용되지 않음'
    )

    def __str__(self):
        return f'[{self.get_pay_sort_display()}] - {self.pay_name}'

    class Meta:
        ordering = ['-project', 'pay_code', 'pay_time']
        verbose_name = '01. 납입회차 관리'
        verbose_name_plural = '01. 납입회차 관리'


class SalesPriceByGT(models.Model):  # 차수별 타입별 분양가격
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order_group = models.ForeignKey('contract.OrderGroup', on_delete=models.PROTECT, verbose_name='차수')
    unit_type = models.ForeignKey('items.UnitType', on_delete=models.PROTECT, verbose_name='타입')
    unit_floor_type = models.ForeignKey('items.UnitFloorType', on_delete=models.PROTECT, verbose_name='층별타입')
    price_build = models.PositiveIntegerField('건물가', null=True, blank=True)
    price_land = models.PositiveIntegerField('대지가', null=True, blank=True)
    price_tax = models.PositiveIntegerField('부가세', null=True, blank=True)
    price = models.PositiveIntegerField('기준공급가')

    def __str__(self):
        return f'{self.price}'

    class Meta:
        ordering = ('order_group', 'unit_type', 'unit_floor_type', 'project')
        verbose_name = '02. 기준 공급가격'
        verbose_name_plural = '02. 기준 공급가격'
        unique_together = (('project', 'order_group', 'unit_type', 'unit_floor_type'),)


class PaymentPerInstallment(models.Model):
    sales_price = models.ForeignKey(SalesPriceByGT, on_delete=models.CASCADE, verbose_name='기준 공급가격')
    pay_order = models.ForeignKey(InstallmentPaymentOrder, on_delete=models.CASCADE, verbose_name='납부 회차',
                                  related_name='payment_installments')
    amount = models.PositiveIntegerField('납부 약정금액', help_text='''일반 납부회차의 경우 기준 공급가 * 회당 납부비율을 적용 하나,
                                         이 데이터 등록 시 예외적으로 이 데이터를 우선 적용함''')

    def __str__(self):
        return f'{self.sales_price.project}-{self.sales_price.order_group}-{self.sales_price.unit_type}-[{self.sales_price.unit_floor_type}]'

    class Meta:
        ordering = ('sales_price__order_group', 'pay_order', 'sales_price__unit_type')
        verbose_name = '03. 특별 약정금액'
        verbose_name_plural = '03. 특별 약정금액'
        unique_together = (('sales_price', 'pay_order'),)


class DownPayment(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order_group = models.ForeignKey('contract.OrderGroup', on_delete=models.CASCADE, verbose_name='차수정보')
    unit_type = models.ForeignKey('items.UnitType', on_delete=models.CASCADE, verbose_name='타입정보')
    payment_amount = models.PositiveIntegerField('회차별 계약금액',
                                                 help_text='동호 미지정 계약 등 차수 및 타입별 각 계약금 회차 고정 납부 계약금. 미지정 시 공급가격 * 회차별 납부비율 적용')

    def __str__(self):
        return f'{self.payment_amount}'

    class Meta:
        ordering = ('id',)
        verbose_name = '04. 타입별 일괄 계약금'
        verbose_name_plural = '04. 타입별 일괄 계약금'
        unique_together = (('project', 'order_group', 'unit_type'),)


# ============================================
# Contract Payment - 계약 결제
# ============================================

class ContractPaymentQuerySet(models.QuerySet):
    """ContractPayment 전용 QuerySet - 계약별/회차별 필터링"""

    def for_contract(self, contract):
        """특정 계약의 납부 내역"""
        return self.filter(contract=contract)

    def for_installment(self, installment_order):
        """특정 회차의 납부 내역"""
        return self.filter(installment_order=installment_order)

    def with_discount_eligible(self):
        """선납 할인 대상 필터"""
        return self.filter(
            payment_type='PAYMENT',
            installment_order__is_prep_discount=True
        )

    def with_penalty_eligible(self):
        """연체 가산 대상 필터"""
        return self.filter(
            payment_type='PAYMENT',
            installment_order__is_late_penalty=True
        )


class ContractPaymentManager(models.Manager):
    """ContractPayment 전용 Manager"""

    def get_queryset(self):
        return ContractPaymentQuerySet(self.model, using=self._db)

    def for_contract(self, contract):
        """특정 계약의 납부 내역"""
        return self.get_queryset().for_contract(contract)

    def for_installment(self, installment_order):
        """특정 회차의 납부 내역"""
        return self.get_queryset().for_installment(installment_order)


class ContractPayment(models.Model):
    """
    계약 결제

    프로젝트의 분양 계약에 대한 결제 정보를 관리합니다.
    ledger.ProjectAccountingEntry와 1:1로 연결되어 계약자의 납부, 환불, 조정 등을 추적합니다.

    생성 조건:
        - ProjectAccountD3.is_payment=True인 회계 분개에 대해서만 생성

    금액 조회:
        - accounting_entry.amount를 통해 조회 (별도 amount 필드 불필요)

    집계 전략:
        - 전체/프로젝트 집계: ProjectAccountingEntry에서 직접 집계 (JOIN 없음)
        - 계약별 상세 조회: ContractPayment.select_related('accounting_entry')

    데이터 흐름:
        ProjectBankTransaction (은행 거래 1건)
            → ProjectAccountingEntry (회계 분개 N건, 회차별 분리)
                → ContractPayment (계약 납부 정보, 1:1 연결)
    """
    # Accounting Domain 연결 (1:1)
    accounting_entry = models.OneToOneField(
        'ledger.ProjectAccountingEntry',
        on_delete=models.CASCADE,
        related_name='contract_payment',
        verbose_name='회계 분개',
        help_text='ProjectAccountingEntry와 1:1 연결 (is_payment=True인 분개)'
    )

    # 계약 정보
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    contract = models.ForeignKey('contract.Contract', on_delete=models.CASCADE, verbose_name='계약', help_text='분양 계약')
    installment_order = models.ForeignKey(InstallmentPaymentOrder, on_delete=models.SET_NULL,
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
    creator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='생성자')

    # Custom Manager 설정
    objects = ContractPaymentManager()

    class Meta:
        verbose_name = '05. 분양 대금 납부'
        verbose_name_plural = '05. 분양 대금 납부'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract', 'payment_type']),
            models.Index(fields=['installment_order', 'created_at']),
        ]

    @property
    def amount(self):
        """결제 금액 (accounting_entry.amount 참조)"""
        return self.accounting_entry.amount

    @property
    def related_transaction(self):
        """연관된 ProjectBankTransaction 조회"""
        return self.accounting_entry.related_transaction

    def get_payment_amount(self):
        """결제 금액 조회 (하위 호환용)"""
        return self.amount

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

    def is_penalty_eligible(self):
        """
        연체 가산 대상 여부 확인

        Returns:
            bool: 연체 가산 대상이면 True
        """
        return (
                self.payment_type == 'PAYMENT' and
                self.installment_order and
                hasattr(self.installment_order, 'is_late_penalty') and
                self.installment_order.is_late_penalty
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
        return f"{self.contract} - {self.get_payment_type_display()} ({self.amount:,}원)"


class OverDueRule(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    term_start = models.IntegerField('최소연체(선납)일', null=True, blank=True, help_text='비어 있을 경우 최대 음수')
    term_end = models.IntegerField('최대연체(선납)일', null=True, blank=True, help_text='비어 있을 경우 최대 양수')
    rate_year = models.DecimalField('연체(할인)이율', max_digits=4, decimal_places=2, help_text='연체일이 0 또는 음수 구간인 경우 할인 적용')

    def __str__(self):
        ts = str(self.term_start) + '일' if self.term_start is not None else 'Min'
        te = str(self.term_end) + '일' if self.term_end is not None else 'Max'
        return f'{ts} - {te}'

    class Meta:
        ordering = ('-project', 'term_start', 'term_end')
        verbose_name = '06. 선납할인/연체이율 관리'
        verbose_name_plural = '06. 선납할인/연체이율 관리'


# 동춘프로젝트 공급계약 체결전 가산금 등 처리 로직 ---------------------------------------------------------------------------------
class SpecialPaymentOrder(models.Model):  # 가산금 / 할인액 계산을 위한 별도 테이블
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    pay_sort = models.CharField('종류', max_length=1, choices=InstallmentPaymentOrder.PAY_SORT_CHOICES, default='1')
    pay_code = models.PositiveSmallIntegerField('납입회차 코드', help_text='프로젝트 내에서 모든 납부회차를 고유 순서대로 숫자로 부여한다.')
    pay_time = models.PositiveSmallIntegerField('납부순서',
                                                help_text='''동일 납부회차에 2가지 항목을 별도로 납부하여야 하는 경우(ex: 분담금 + 업무대행료)
                                                하나의 납입회차 코드(ex: 1)에 2개의 납부순서(ex: 1, 2)를 등록한다.''')
    pay_name = models.CharField('납부회차 명', max_length=20)
    alias_name = models.CharField('회차 별칭', max_length=20, blank=True)
    days_since_prev = models.PositiveSmallIntegerField('전회 기준 경과일수', null=True, blank=True,
                                                       help_text="전 회차(예: 계약일)로부터 __일 이내 형식으로 납부기한을 지정할 경우 해당 일수")
    is_prep_discount = models.BooleanField('선납할인 적용 여부', default=False)
    is_late_penalty = models.BooleanField('연체가산 적용 여부', default=False)
    pay_due_date = models.DateField('지정 납부기한', null=True, blank=True, help_text="특정일자를 납부기한으로 지정할 경우")
    extra_due_date = models.DateField('납부유예일', null=True, blank=True,
                                      help_text='연체료 계산 기준은 지정 납부기한이 원칙이나 이 값이 있는 경우 납부유예일을 연체료 계산 기준으로 한다.')

    def __str__(self):
        return f'[{self.get_pay_sort_display()}] - {self.pay_name}'

    class Meta:
        ordering = ['-project', 'pay_code']
        verbose_name = '07. 특별 납입회차'
        verbose_name_plural = '07. 특별 납입회차'


class SpecialDownPay(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order_group = models.ForeignKey('contract.OrderGroup', on_delete=models.CASCADE, verbose_name='차수정보')
    unit_type = models.ForeignKey('items.UnitType', on_delete=models.CASCADE, verbose_name='타입정보')
    payment_amount = models.PositiveIntegerField('회차별 계약금액',
                                                 help_text='차수 및 타입별 고정 납부 계약금액, 납부 회수는 납부 회차 모델에서 별도 등록/설정')
    payment_remain = models.IntegerField('나머지 계약금액', default=0)

    def __str__(self):
        return f'{self.payment_amount}'

    class Meta:
        ordering = ('id',)
        verbose_name = '08. 특별 회차별 납입금'
        verbose_name_plural = '08. 특별 회차별 납입금'


class SpecialOverDueRule(models.Model):  # 가산금 / 할인액 계산을 위한 별도 테이블
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    term_start = models.IntegerField('최소연체(선납)일', null=True, blank=True, help_text='비어 있을 경우 최대 음수')
    term_end = models.IntegerField('최대연체(선납)일', null=True, blank=True, help_text='비어 있을 경우 최대 양수')
    rate_year = models.DecimalField('연체(할인)이율', max_digits=4, decimal_places=2, help_text='연체일이 0 또는 음수 구간인 경우 할인 적용')

    def __str__(self):
        ts = str(self.term_start) + '일' if self.term_start is not None else 'Min'
        te = str(self.term_end) + '일' if self.term_end is not None else 'Max'
        return f'{ts} - {te}'

    class Meta:
        ordering = ('-project', 'term_start', 'term_end')
        verbose_name = '09. 특별 선납할인/연체이율'
        verbose_name_plural = '09. 특별 선납할인/연체이율'
