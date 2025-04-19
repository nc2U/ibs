from django.db import models


class SalesPriceByGT(models.Model):  # 차수별 타입별 분양가격
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order_group = models.ForeignKey('contract.OrderGroup', on_delete=models.PROTECT, verbose_name='차수')
    unit_type = models.ForeignKey('items.UnitType', on_delete=models.PROTECT, verbose_name='타입')
    unit_floor_type = models.ForeignKey('items.UnitFloorType', on_delete=models.PROTECT, verbose_name='층별타입')
    price_build = models.PositiveIntegerField('건물가', null=True, blank=True)
    price_land = models.PositiveIntegerField('대지가', null=True, blank=True)
    price_tax = models.PositiveIntegerField('부가세', null=True, blank=True)
    price = models.PositiveIntegerField('분양가격')
    down_pay = models.PositiveIntegerField('계약금', null=True, blank=True, help_text='계약금 분납 시 회당 납부하는 금액 기재')
    middle_pay = models.PositiveIntegerField('중도금', null=True, blank=True, help_text='중도금 분납 시 회당 납부하는 금액 기재')
    remain_pay = models.PositiveIntegerField('잔금', null=True, blank=True, help_text='잔금 분납 시 회당 납부하는 금액 기재')

    def __str__(self):
        return f'{self.price}'

    class Meta:
        ordering = ('order_group', 'unit_type', 'unit_floor_type', 'project')
        verbose_name = '01. 프로젝트 분양가 관리'
        verbose_name_plural = '01. 프로젝트 분양가 관리'


class InstallmentPaymentOrder(models.Model):  # 분할 납부 차수 등록
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    SORT_CHOICES = (('1', '계약금'), ('2', '중도금'), ('3', '잔금'))
    pay_sort = models.CharField('종류', max_length=1, choices=SORT_CHOICES, default='1')
    pay_code = models.PositiveSmallIntegerField('납입회차 코드', help_text='프로젝트 내 납부회차별 코드번호 - 동일 회차 중복(분리) 등록 가능')
    pay_time = models.PositiveSmallIntegerField('납부순서',
                                                help_text='''동일 납부회차에 2가지 항목을 분리해서 납부하여야 하는 경우(ex: 분담금 + 업무대행료)
                                                하나의 납입회차 코드(ex: 1)에 2개의 납부순서(ex: 1, 2)를 등록한다.''')
    pay_name = models.CharField('납부회차 명', max_length=20)
    alias_name = models.CharField('회차 별칭', max_length=20, blank=True)
    is_pm_cost = models.BooleanField('PM용역비 여부', default=False)
    pay_amt = models.PositiveIntegerField('납부 약정금액', null=True, blank=True,
                                          help_text='약정금이 차수, 타입에 관계 없이 정액인 경우 설정(예: 세대별 업무대행비)')
    pay_ratio = models.DecimalField('회당 납부비율(%)', max_digits=5, decimal_places=2, null=True, blank=True,
                                    help_text='''분양가 대비 납부비율, 계약금 항목인 경우 Downpayment 
                                    테이블 데이터 우선, 잔금 항목인 경우 분양가와 비교 차액 데이터 우선''')
    pay_due_date = models.DateField('냡부 약정일', null=True, blank=True, help_text="특정일자를 납부기한으로 지정할 경우")
    days_since_prev = models.PositiveSmallIntegerField('전회 기준 경과일수', null=True, blank=True,
                                                       help_text="전 회차(예: 계약일)로부터 __일 이내 형식으로 납부기한을 지정할 경우 해당 일수")
    is_calc_start = models.BooleanField('할인/가산 시작 여부', default=False)
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
        ordering = ['-project', 'pay_code']
        verbose_name = '02. 납입회차 관리'
        verbose_name_plural = '02. 납입회차 관리'


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
        verbose_name = '03. 타입별 계약금 관리'
        verbose_name_plural = '03. 타입별 계약금 관리'


class OverDueRule(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    term_start = models.IntegerField('최소연체(선납)일', null=True, blank=True, help_text='비어 있을 경우 최대 음수')
    term_end = models.IntegerField('최대연체(선납)일', null=True, blank=True, help_text='비어 있을 경우 최대 양수')
    rate_year = models.DecimalField('연체(할인)이율', max_digits=4, decimal_places=2, help_text='연체일이 0 또는 음수 구간인 경우 할인 적용')

    def __str__(self):
        ts = str(self.term_start) + '일' if self.term_start != None else 'Min'
        te = str(self.term_end) + '일' if self.term_end != None else 'Max'
        return f'{ts} - {te}'

    class Meta:
        ordering = ('-project', 'term_start', 'term_end')
        verbose_name = '04. 선납할인/연체이율 관리'
        verbose_name_plural = '04. 선납할인/연체이율 관리'


class SpecialPaymentOrder(models.Model):  # 가산금 / 할인액 계산을 위한 별도 테이블
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    SORT_CHOICES = (('1', '계약금'), ('2', '중도금'), ('3', '잔금'))
    pay_sort = models.CharField('종류', max_length=1, choices=SORT_CHOICES, default='1')
    pay_code = models.PositiveSmallIntegerField('납입회차 코드', help_text='프로젝트 내에서 모든 납부회차를 고유 순서대로 숫자로 부여한다.')
    pay_time = models.PositiveSmallIntegerField('납부순서',
                                                help_text='''동일 납부회차에 2가지 항목을 별도로 납부하여야 하는 경우(ex: 분담금 + 업무대행료)
                                                하나의 납입회차 코드(ex: 1)에 2개의 납부순서(ex: 1, 2)를 등록한다.''')
    is_calc_start = models.BooleanField('할인/가산 시작 여부', default=False)
    pay_name = models.CharField('납부회차 명', max_length=20)
    alias_name = models.CharField('회차 별칭', max_length=20, blank=True)
    days_since_prev = models.PositiveSmallIntegerField('전회 기준 경과일수', null=True, blank=True,
                                                       help_text="전 회차(예: 계약일)로부터 __일 이내 형식으로 납부기한을 지정할 경우 해당 일수")
    pay_due_date = models.DateField('지정 납부기한', null=True, blank=True, help_text="특정일자를 납부기한으로 지정할 경우")
    extra_due_date = models.DateField('납부유예일', null=True, blank=True,
                                      help_text='연체료 계산 기준은 지정 납부기한이 원칙이나 이 값이 있는 경우 납부유예일을 연체료 계산 기준으로 한다.')

    def __str__(self):
        return f'[{self.get_pay_sort_display()}] - {self.pay_name}'

    class Meta:
        ordering = ['-project', 'pay_code']
        verbose_name = '05. 특별 납입회차'
        verbose_name_plural = '05. 특별 납입회차'


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
        verbose_name = '06. 특별 회차별 납입금'
        verbose_name_plural = '06. 특별 회차별 납입금'


class SpecialOverDueRule(models.Model):  # 가산금 / 할인액 계산을 위한 별도 테이블
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    term_start = models.IntegerField('최소연체(선납)일', null=True, blank=True, help_text='비어 있을 경우 최대 음수')
    term_end = models.IntegerField('최대연체(선납)일', null=True, blank=True, help_text='비어 있을 경우 최대 양수')
    rate_year = models.DecimalField('연체(할인)이율', max_digits=4, decimal_places=2, help_text='연체일이 0 또는 음수 구간인 경우 할인 적용')

    def __str__(self):
        ts = str(self.term_start) + '일' if self.term_start != None else 'Min'
        te = str(self.term_end) + '일' if self.term_end != None else 'Max'
        return f'{ts} - {te}'

    class Meta:
        ordering = ('-project', 'term_start', 'term_end')
        verbose_name = '07. 특별 선납할인/연체이율'
        verbose_name_plural = '07. 특별 선납할인/연체이율'
