from django.db import models

from items.models import UnitType


class InstallmentPaymentOrder(models.Model):  # 분할 납부 차수 등록
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    type_sort = models.CharField('타입종류', max_length=1, choices=UnitType.SORT_CHOICES, default='1')
    PAY_SORT_CHOICES = (('1', '계약금'), ('2', '중도금'), ('3', '잔금'), ('4', '기타 부담금'),
                        ('5', '제세 공과금'), ('6', '금융 비용'), ('7', '업무 대행비'))
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
    down_pay = models.PositiveIntegerField('계약금', null=True, blank=True, help_text='계약금 분납 시 회당 납부하는 금액 기재')
    biz_agency_fee = models.PositiveIntegerField('업무대행비', null=True, blank=True)
    is_included_baf = models.BooleanField('업무대행비 포함 여부', default=False)
    middle_pay = models.PositiveIntegerField('중도금', null=True, blank=True, help_text='중도금 분납 시 회당 납부하는 금액 기재')
    remain_pay = models.PositiveIntegerField('잔금', null=True, blank=True, help_text='잔금 분납 시 회당 납부하는 금액 기재')

    def __str__(self):
        return f'{self.price}'

    class Meta:
        ordering = ('order_group', 'unit_type', 'unit_floor_type', 'project')
        verbose_name = '02. 기준 공급가격'
        verbose_name_plural = '02. 기준 공급가격'


class PaymentPerInstallment(models.Model):
    sales_price = models.ForeignKey(SalesPriceByGT, on_delete=models.CASCADE, verbose_name='기준 공급가격')
    pay_order = models.ForeignKey(InstallmentPaymentOrder, on_delete=models.CASCADE, verbose_name='납부 회차',
                                  related_name='payment_installments')
    amount = models.PositiveIntegerField('납부 약정금액', help_text='''일반 납부회차의 경우 기준 공급가 * 회당 납부비율을 적용 하나,
                                         이 데이터 등록 시 예외적으로 이 데이터를 우선 적용함''')
    is_manual_override = models.BooleanField('수동 설정 여부', default=True,
                                             help_text='True: 수동 설정된 예외 금액, False: 자동 계산된 금액')
    override_reason = models.CharField('수정 사유', max_length=100, blank=True,
                                       help_text='수동 설정 시 사유 기록')
    disable = models.BooleanField('비활성', default=False)
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ('sales_price__order_group', 'pay_order', 'sales_price__unit_type')
        verbose_name = '03. 특별 약정금액'
        verbose_name_plural = '03. 특별 약정금액'
        unique_together = (('sales_price', 'pay_order'),)


# class SpecialAmount(models.Model):
#     sales_price = models.ForeignKey(SalesPriceByGT, on_delete=models.CASCADE, verbose_name='기준 공급가격')
#     pay_order = models.ForeignKey(InstallmentPaymentOrder, on_delete=models.CASCADE, verbose_name='납부 회차')
#     amount = models.PositiveIntegerField('납부 약정금액',
#                                          help_text='일반 납부회차의 경우 기준 공급가 * 회당 납부비율을 적용 하나, 이 데이터 등록 시 예외적으로 이 데이터를 우선 적용함')
#
#     class Meta:
#         ordering = ('id',)
#         verbose_name = '03. 특별 약정금액'
#         verbose_name_plural = '03. 특별 약정금액'


class DownPayment(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order_group = models.ForeignKey('contract.OrderGroup', on_delete=models.CASCADE, verbose_name='차수정보')
    unit_type = models.ForeignKey('items.UnitType', on_delete=models.CASCADE, verbose_name='타입정보')
    payment_amount = models.PositiveIntegerField('회차별 계약금액',
                                                 help_text='차수 및 타입별 고정 납부 계약금액, 납부 회수는 납부 회차 모델에서 별도 등록/설정')

    def __str__(self):
        return f'{self.payment_amount}'

    class Meta:
        ordering = ('id',)
        verbose_name = '04. 타입별 일괄 계약금'
        verbose_name_plural = '04. 타입별 일괄 계약금'


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
        verbose_name = '05. 선납할인/연체이율 관리'
        verbose_name_plural = '05. 선납할인/연체이율 관리'


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
        verbose_name = '06. 특별 납입회차'
        verbose_name_plural = '06. 특별 납입회차'


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
        verbose_name = '07. 특별 회차별 납입금'
        verbose_name_plural = '07. 특별 회차별 납입금'


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
        verbose_name = '08. 특별 선납할인/연체이율'
        verbose_name_plural = '08. 특별 선납할인/연체이율'
