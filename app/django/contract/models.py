import os

import magic
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from _utils.contract_price import get_contract_payment_plan
from _utils.file_cleanup import file_cleanup_signals, related_file_cleanup
from payment.models import InstallmentPaymentOrder


class OrderGroup(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order_number = models.PositiveSmallIntegerField('차수')
    SORT_CHOICES = (('1', '조합모집'), ('2', '일반분양'))
    sort = models.CharField('구분', max_length=1, choices=SORT_CHOICES, default='1')
    name = models.CharField('차수명', max_length=20, db_index=True)
    is_default_for_uncontracted = models.BooleanField('미계약세대 기본설정', default=False,
                                                      help_text='미계약 세대 ContractPrice 생성 시 적용할 기본 차수 여부')

    def __str__(self):
        return self.name

    @classmethod
    def get_default_for_project(cls, project):
        """
        프로젝트의 기본 미계약 차수를 반환합니다.
        Args: project: Project 인스턴스
        Returns: OrderGroup 인스턴스 또는 None
        """
        if not project:
            return None

        return cls.objects.filter(
            project=project,
            is_default_for_uncontracted=True
        ).first()

    def clean(self):
        """모델 검증"""
        super().clean()

        if self.is_default_for_uncontracted:
            # 동일 프로젝트에서 이미 기본으로 설정된 다른 OrderGroup이 있는지 확인
            existing_default = OrderGroup.objects.filter(
                project=self.project,
                is_default_for_uncontracted=True
            ).exclude(pk=self.pk)

            if existing_default.exists():
                raise ValidationError({
                    'is_default_for_uncontracted':
                        f'프로젝트 "{self.project.name}"에서는 하나의 차수만 미계약세대 기본설정으로 지정할 수 있습니다. '
                        f'현재 "{existing_default.first().name}"이(가) 이미 설정되어 있습니다.'
                })

    class Meta:
        ordering = ['-project', 'id']
        verbose_name = '01. 차수 (계약그룹)'
        verbose_name_plural = '01. 차수 (계약그룹)'
        constraints = [
            models.UniqueConstraint(
                fields=['project'],
                condition=models.Q(is_default_for_uncontracted=True),
                name='unique_default_uncontracted_per_project'
            )
        ]


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
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_contracts', verbose_name='편집자')

    def __str__(self):
        return f'[{self.project.id}] {self.serial_number}'

    def get_cached_payment_plan(self):
        """
        Get a cached payment plan if available.
        Returns: list or None: Cached payment plan data if available, None otherwise
        """
        return getattr(self, '_cached_payment_plan', None)

    def set_cached_payment_plan(self, payment_plan):
        """
        Set cached payment plan data.
        Args: payment_plan: Payment plan data to cache
        """
        self._cached_payment_plan = payment_plan

    class Meta:
        ordering = ('-project', '-created')
        verbose_name = '02. 계약 정보'
        verbose_name_plural = '02. 계약 정보'


def get_contract_file_name(instance, filename):
    slug = instance.contract.project.issue_project.slug
    unit_type = instance.contract.unit_type.name
    ord_group = f'ord_grp_{instance.contract.order_group.order_number}'
    return os.path.join('contract', f'{slug}', unit_type, ord_group, filename)


class ContractFile(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, default=None, verbose_name='계약서',
                                 related_name='contract_files')
    file = models.FileField(upload_to=get_contract_file_name, verbose_name='파일경로')
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='사용자')

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
    contract = models.OneToOneField(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    house_unit = models.OneToOneField('items.HouseUnit', on_delete=models.PROTECT,
                                      verbose_name='세대정보', related_name='contract_price',
                                      null=True, blank=True)
    order_group = models.ForeignKey('OrderGroup', on_delete=models.PROTECT,
                                    null=True, blank=True, verbose_name='차수',
                                    help_text='분양 차수 - 생성 시 자동 설정, 수정 시 유지')
    price = models.PositiveIntegerField('분양가격')
    price_build = models.PositiveIntegerField('건물가', null=True, blank=True)
    price_land = models.PositiveIntegerField('대지가', null=True, blank=True)
    price_tax = models.PositiveIntegerField('부가세', null=True, blank=True)

    # 회차별 납부 금액 저장 (JSON 필드)
    payment_amounts = models.JSONField('회차별 납부금액', default=dict, blank=True,
                                       help_text='납부순서별 납부 금액 {"1": 10000000, "2": 30000000, "3": 20000000} (pay_time 기준)')

    # 캐시 갱신 관련 필드
    calculated = models.DateTimeField('계산일시', auto_now=True, help_text='마지막 계산 수행 시각')
    is_cache_valid = models.BooleanField('캐시 유효성', default=False, help_text='저장된 계산값이 유효한지 여부')

    def save(self, *args, **kwargs):
        # order_group은 생성 시에만 자동 설정 (수정 시에는 기존값 유지)
        if not self.pk and not self.order_group:  # 새로 생성하는 경우에만
            if self.contract and self.contract.order_group:
                # 계약이 있으면 계약의 차수 사용
                self.order_group = self.contract.order_group
            elif self.house_unit and self.house_unit.unit_type:
                # 미계약이면 프로젝트의 기본 차수 사용
                default_og = OrderGroup.get_default_for_project(
                    self.house_unit.unit_type.project
                )
                if default_og:
                    self.order_group = default_og

        # 저장 시 자동으로 납부 금액 계산 및 캐시
        if self.contract:
            # 계약이 있는 경우 일반 계산
            self.calculate_and_cache_payments()
        elif self.house_unit and self.house_unit.unit_type:
            # 미계약 상태이지만 house_unit이 있는 경우 임시 계약으로 계산
            self.calculate_uncontracted_payments()
        super().save(*args, **kwargs)

    def calculate_and_cache_payments(self):
        """계약의 납부 계획을 계산하여 JSON 필드에 저장"""

        try:
            payment_plan = get_contract_payment_plan(self.contract)
            payment_amounts = {}

            # pay_time별 금액 저장 (고유 식별자)
            for plan_item in payment_plan:
                installment = plan_item['installment_order']
                amount = plan_item['amount']
                pay_time = str(installment.pay_time)  # JSON 키는 문자열

                payment_amounts[pay_time] = amount

            self.payment_amounts = payment_amounts
            self.is_cache_valid = True

        except Exception as e:
            # 계산 실패 시 캐시 무효화
            self.is_cache_valid = False
            # 에러 로깅은 상위에서 처리하도록 함
            pass

    def calculate_uncontracted_payments(self):
        """미계약 상태에서 house_unit 기반으로 납부 계획을 계산하여 JSON 필드에 저장"""
        try:
            project = self.house_unit.unit_type.project

            # 프로젝트의 기본 미계약 차수를 OrderGroup.get_default_for_project로 조회
            default_order_group = OrderGroup.get_default_for_project(project)
            if not default_order_group:
                self.is_cache_valid = False
                return

            # InstallmentPaymentOrder 직접 조회하여 납부 계획 계산
            from payment.models import InstallmentPaymentOrder
            from _utils.contract_price import get_payment_amount

            # 임시 계약 객체 생성 - get_payment_amount 함수용
            class TempContract:
                def __init__(self, _project, order_group, unit_type):
                    self.project = _project
                    self.order_group = order_group
                    self.unit_type = unit_type

            temp_contract = TempContract(
                project,
                default_order_group,
                self.house_unit.unit_type
            )

            # 해당 프로젝트와 타입의 분할납부차수 조회
            installments = InstallmentPaymentOrder.objects.filter(
                project=project,
                type_sort=self.house_unit.unit_type.sort
            ).order_by('pay_code', 'pay_time')

            payment_amounts = {}

            # 각 분할납부차수별 금액 계산
            for installment in installments:
                amount = get_payment_amount(temp_contract, installment)
                pay_time = str(installment.pay_time)  # JSON 키는 문자열
                payment_amounts[pay_time] = amount

            # 근린생활시설의 경우 InstallmentPaymentOrder가 없으면 기본 납부회차 적용
            if not payment_amounts and self.house_unit.unit_type.name == '근린생활시설':
                # 기본 납부회차: 잔금 100%
                # 잔금(pay_sort='3')에 해당하는 pay_time 찾기
                from payment.models import InstallmentPaymentOrder
                try:
                    final_payment_order = InstallmentPaymentOrder.objects.get(
                        project=project,
                        pay_sort='3'  # 잔금
                    )
                    final_pay_time = str(final_payment_order.pay_time)
                    payment_amounts = {
                        final_pay_time: self.price  # 잔금 100%
                    }
                except InstallmentPaymentOrder.DoesNotExist:
                    # 잔금 InstallmentPaymentOrder가 없으면 기본적으로 "10" 사용
                    payment_amounts = {
                        "10": self.price  # 잔금 100%
                    }

            self.payment_amounts = payment_amounts
            self.is_cache_valid = True

        except Exception as e:
            # 계산 실패 시 캐시 무효화
            self.is_cache_valid = False

    def get_payment_amount_by_time(self, pay_time):
        """납부순서별 납부 금액 조회"""
        if not self.is_cache_valid:
            self.calculate_and_cache_payments()
            self.save()

        return self.payment_amounts.get(str(pay_time), 0)

    def get_payment_amount_by_sort(self, pay_sort):
        """납부종류별 납부 금액 합계 조회 (동일 pay_sort의 모든 pay_time 합계)"""
        if not self.is_cache_valid:
            self.calculate_and_cache_payments()
            self.save()

        # pay_sort와 매칭되는 모든 pay_time의 금액 합계
        # 해당 계약의 프로젝트에서 pay_sort에 해당하는 모든 pay_time 조회
        pay_times = InstallmentPaymentOrder.objects.filter(
            project=self.contract.project,
            pay_sort=pay_sort
        ).values_list('pay_time', flat=True)

        total_amount = 0
        for pay_time in pay_times:
            total_amount += self.payment_amounts.get(str(pay_time), 0)

        return total_amount

    def __str__(self):
        return f'{self.price}'

    class Meta:
        ordering = ('-contract__project', 'contract')
        verbose_name = '03. 계약 공급가격'
        verbose_name_plural = '03. 계약 공급가격'


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
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
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
    is_current = models.BooleanField('현주소 여부', default=True)
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='등록자')

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
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
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
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_successions', verbose_name='편집자')

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
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_contractor_releases', verbose_name='편집자')

    def __str__(self):
        return f'{self.contractor}'

    class Meta:
        verbose_name = '09. 계약 해지 정보'
        verbose_name_plural = '09. 계약 해지 정보'
