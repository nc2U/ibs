import magic
from django.conf import settings
from django.db import models

from _utils.file_cleanup import file_cleanup_signals, related_file_cleanup


class OrderGroup(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order_number = models.PositiveSmallIntegerField('차수')
    SORT_CHOICES = (('1', '조합모집'), ('2', '일반분양'))
    sort = models.CharField('구분', max_length=1, choices=SORT_CHOICES, default='1')
    order_group_name = models.CharField('차수명', max_length=20, db_index=True)

    def __str__(self):
        return self.order_group_name

    class Meta:
        ordering = ['-project', 'id']
        verbose_name = '01. 차수 (계약그룹)'
        verbose_name_plural = '01. 차수 (계약그룹)'


class Contract(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.PROTECT, verbose_name='프로젝트')
    serial_number = models.CharField('계약 일련 번호', max_length=30, unique=True, db_index=True)
    order_group = models.ForeignKey(OrderGroup, on_delete=models.PROTECT, verbose_name='차수')
    unit_type = models.ForeignKey('items.UnitType', on_delete=models.PROTECT, verbose_name='타입')
    activation = models.BooleanField('계약 활성 여부', default=True)
    is_sup_cont = models.BooleanField('공급계약 체결여부', default=False)
    sup_cont_date = models.DateField('공급계약 체결일', null=True, blank=True)
    key_unit = models.OneToOneField('items.KeyUnit', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='계약유닛', related_name='contract')
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='등록자')

    def __str__(self):
        return f'[{self.project.id}] {self.serial_number}'

    class Meta:
        ordering = ('-project', '-created_at')
        verbose_name = '02. 계약 정보'
        verbose_name_plural = '02. 계약 정보'


def get_contract_file_name(instance, filename):
    return '/'.join(
        ['proj_cont',
         f'{instance.contract.project.issue_project.slug}',
         instance.contract.unit_type.name,
         f'ord_grp_{instance.contract.order_group.order_number}',
         filename])


class ContractFile(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, default=None, verbose_name='계약서',
                                 related_name='contract_files')
    file = models.FileField(upload_to=get_contract_file_name, verbose_name='파일경로')
    file_name = models.CharField('파일명', max_length=100, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='사용자')

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name.split('/')[-1]
            mime = magic.Magic(mime=True)
            file_pos = self.file.tell()  # 현재 파일 커서 위치 백업
            self.file_type = mime.from_buffer(self.file.read(2048))  # 2048바이트 정도면 충분
            self.file.seek(file_pos)  # 원래 위치로 복구
            self.file_size = self.file.size
        super().save(*args, **kwargs)


file_cleanup_signals(ContractFile)  # 파일인스턴스 직접 삭제시
related_file_cleanup(Contract, related_name='contract_files', file_field_name='file')  # 연관 모델 삭제 시


class ContractPrice(models.Model):
    contract = models.OneToOneField(Contract, on_delete=models.SET_NULL, null=True)
    price = models.PositiveIntegerField('분양가격')
    price_build = models.PositiveIntegerField('건물가', null=True, blank=True)
    price_land = models.PositiveIntegerField('대지가', null=True, blank=True)
    price_tax = models.PositiveIntegerField('부가세', null=True, blank=True)
    down_pay = models.PositiveIntegerField('계약금', help_text='계약금 분납 시 회당 납부하는 금액 기재')
    biz_agency_fee = models.PositiveIntegerField('업무대행비', null=True, blank=True)
    is_included_baf = models.BooleanField('업무대행비 포함 여부', default=False)
    middle_pay = models.PositiveIntegerField('중도금', help_text='중도금 분납 시 회당 납부하는 금액 기재')
    remain_pay = models.PositiveIntegerField('잔금', help_text='잔금 분납 시 회당 납부하는 금액 기재')

    def __str__(self):
        return f'{self.price}'

    class Meta:
        ordering = ('-contract__project', 'contract')
        verbose_name = '03. 계약 공급가격'
        verbose_name_plural = '03. 계약 공급가격'


class PaymentPerInstallment(models.Model):
    cont_price = models.ForeignKey(ContractPrice, on_delete=models.CASCADE, verbose_name='공급 가격')
    pay_order = models.ForeignKey('payment.InstallmentPaymentOrder', on_delete=models.CASCADE, verbose_name='납부 회차')
    amount = models.PositiveIntegerField('납부 약정금액')
    disable = models.BooleanField('비활성', default=False)

    class Meta:
        ordering = ('cont_price__contract__project', 'pay_order', 'cont_price')
        verbose_name = '04. 회차별 납부대금'
        verbose_name_plural = '04. 회차별 납부대금'


class Contractor(models.Model):
    contract = models.OneToOneField('Contract', on_delete=models.PROTECT, null=True, verbose_name='계약 정보')
    prev_contract = models.ForeignKey('Contract', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='prev_contractors', verbose_name='종전 계약건',
                                      help_text='계약해지/양도승계 전 계약건')
    name = models.CharField('계약자명', max_length=20, db_index=True)
    birth_date = models.DateField('생년월일', null=True, blank=True)
    GENDER_CHOICES = (('M', '남자'), ('F', '여자'))
    gender = models.CharField('성별', max_length=1, choices=GENDER_CHOICES, blank=True)
    QUA_CHOICES = (('1', '일반분양'), ('2', '미인가조합원'), ('3', '인가조합원'), ('4', '부적격조합원'))
    qualification = models.CharField('등록상태', max_length=1, choices=QUA_CHOICES, default='1')
    STATUS_CHOICES = (('1', '청약'), ('2', '계약'), ('3', '청약 해지'), ('4', '계약 해지'), ('5', '양도 승계'))
    status = models.CharField('계약상태', max_length=1, choices=STATUS_CHOICES)
    reservation_date = models.DateField('청약일자', null=True, blank=True)
    contract_date = models.DateField('계약일자', null=True, blank=True)
    is_active = models.BooleanField('유효계약자여부', default=True)
    note = models.TextField('비고', blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, verbose_name='등록자')

    def __str__(self):
        return f'{self.name}({self.contract.serial_number if self.contract else self.prev_contract.serial_number})'

    class Meta:
        verbose_name = '05. 계약자 정보'
        verbose_name_plural = '05. 계약자 정보'


class ContractorAddress(models.Model):
    contractor = models.OneToOneField('Contractor', on_delete=models.CASCADE, verbose_name='계약자 정보')
    id_zipcode = models.CharField('우편번호', max_length=5)
    id_address1 = models.CharField('주민등록 주소', max_length=50)
    id_address2 = models.CharField('상세주소', max_length=30, blank=True)
    id_address3 = models.CharField('참고항목', max_length=30, blank=True)
    dm_zipcode = models.CharField('우편번호', max_length=5)
    dm_address1 = models.CharField('우편송부 주소', max_length=50)
    dm_address2 = models.CharField('상세주소', max_length=50, blank=True)
    dm_address3 = models.CharField('참고항목', max_length=30, blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='등록자')

    def __str__(self):
        return f'[주소] - {self.contractor}'

    class Meta:
        verbose_name = '06. 계약자 주소'
        verbose_name_plural = '06. 계약자 주소'


class ContractorContact(models.Model):
    contractor = models.OneToOneField('Contractor', on_delete=models.CASCADE, verbose_name='계약자 정보')
    cell_phone = models.CharField('휴대전화', max_length=13)
    home_phone = models.CharField('집 전화', max_length=13, blank=True)
    other_phone = models.CharField('기타 전화', max_length=13, blank=True)
    email = models.EmailField('이메일', max_length=30, blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='등록자')

    def __str__(self):
        return f'[연락처] - {self.contractor}'

    class Meta:
        verbose_name = '07. 계약자 연락처'
        verbose_name_plural = '07. 계약자 연락처'


class Succession(models.Model):
    contract = models.ForeignKey('Contract', on_delete=models.PROTECT, verbose_name='계약 정보')
    seller = models.OneToOneField('Contractor', on_delete=models.CASCADE, verbose_name='양도계약자',
                                  related_name='prev_contractor')
    buyer = models.OneToOneField('Contractor', on_delete=models.CASCADE, verbose_name='양수계약자',
                                 related_name='curr_contractor')
    apply_date = models.DateField('승계신청일')
    trading_date = models.DateField('매매계약일')
    approval_date = models.DateField('변경인가일', null=True, blank=True)
    is_approval = models.BooleanField('변경인가여부', default=False)
    note = models.TextField('비고', blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='등록자')

    def __str__(self):
        return f'{self.seller}'

    class Meta:
        ordering = ['-apply_date', '-trading_date', '-id']
        verbose_name = '08. 권리 의무 승계'
        verbose_name_plural = '08. 권리 의무 승계'


class ContractorRelease(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    contractor = models.OneToOneField('Contractor', on_delete=models.CASCADE, verbose_name='계약자 정보')
    STATUS_CHOICES = (('0', '신청 취소'), ('3', '해지 신청'), ('4', '해지 완료'), ('5', '자격 상실'))
    status = models.CharField('상태', choices=STATUS_CHOICES, max_length=1)
    refund_amount = models.PositiveIntegerField('환불(예정)금액')
    refund_account_bank = models.CharField('환불계좌(은행)', max_length=20)
    refund_account_number = models.CharField('환불계좌(번호)', max_length=25)
    refund_account_depositor = models.CharField('환불계좌(예금주)', max_length=20)
    request_date = models.DateField('해지신청일')
    completion_date = models.DateField('해지(환불)처리일', null=True, blank=True)
    note = models.TextField('비고', blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='등록자')

    def __str__(self):
        return f'{self.contractor}'

    class Meta:
        verbose_name = '09. 계약 해지 정보'
        verbose_name_plural = '09. 계약 해지 정보'
