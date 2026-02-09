import os

import magic
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from _utils.contract_price import get_contract_payment_plan
from _utils.file_cleanup import file_cleanup_signals, related_file_cleanup
from _utils.file_upload import get_contract_file_path, get_upload_path
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
        verbose_name = '01. 계약 차수 그룹'
        verbose_name_plural = '01. 계약 차수 그룹'
        constraints = [
            models.UniqueConstraint(
                fields=['project'],
                condition=models.Q(is_default_for_uncontracted=True),
                name='unique_default_uncontracted_per_project'
            )
        ]


class DocumentType(models.Model):
    """서류 유형 마스터 테이블"""
    DOCUMENT_SORT = (('proof', '증명서류'), ('pledge', '동의서류'))
    sort = models.CharField('서류구분', max_length=20, choices=DOCUMENT_SORT, default='proof')
    name = models.CharField('서류명', max_length=100, unique=True)
    default_quantity = models.PositiveIntegerField('기본 수량', default=1)
    DOCUMENT_REQUIRE_TYPE = (('required', '필수'), ('optional', '선택'), ('conditional', '조건부 필수'))
    require_type = models.CharField('필수 여부', max_length=20, choices=DOCUMENT_REQUIRE_TYPE, default='required')
    is_default_item = models.BooleanField('기본 서류 여부', default=True,
                                          help_text='프로젝트 생성 시 자동으로 추가될 필수 서류')
    description = models.CharField('설명', max_length=255, blank=True, default='')
    is_active = models.BooleanField('사용 여부', default=True)
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_document_types', verbose_name='편집자')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'contract_document_type'
        ordering = ['id']
        verbose_name = '02. 필요 서류 유형 [템플릿]'
        verbose_name_plural = '02. 필요 서류 유형 [템플릿]'


class RequiredDocument(models.Model):
    """계약 시 필요 서류 (프로젝트별 관리)"""
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE,
                                verbose_name='프로젝트', related_name='contract_required_documents')
    sort = models.CharField('서류구분', max_length=20, choices=DocumentType.DOCUMENT_SORT, default='proof')
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT,
                                      verbose_name='서류 유형', related_name='project_requirements')
    quantity = models.PositiveIntegerField('필요 수량', blank=True, default=1)
    require_type = models.CharField('필수 여부', max_length=20, choices=DocumentType.DOCUMENT_REQUIRE_TYPE,
                                    default='required')
    description = models.CharField('설명', max_length=255, blank=True, default='',
                                   help_text='프로젝트별 특이사항, 요구 조건 또는 추가 요구사항')
    display_order = models.PositiveIntegerField('표시 순서', blank=True, default=0, help_text='서류 목록 표시 시 정렬 순서')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_required_documents', verbose_name='편집자')

    def __str__(self):
        return f'{self.project.name} - {self.document_type.name}'

    class Meta:
        ordering = ['display_order', 'id']
        unique_together = [['project', 'document_type']]
        verbose_name = '03. 프로젝트별 필요 서류'
        verbose_name_plural = '03. 프로젝트별 필요 서류'


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

    @property
    def document_completion_rate(self):
        """서류 제출 완료율 (백분율) - 현재 계약자 기준"""
        if not hasattr(self, 'contractor'):
            return 0
        total = self.contractor.submitted_documents.count()
        if total == 0:
            return 0
        completed = self.contractor.submitted_documents.filter(
            submitted_quantity__gte=models.F('required_quantity')
        ).count()
        return round((completed / total) * 100, 1)

    @property
    def all_required_documents_submitted(self):
        """필수 서류가 모두 제출되었는지 확인 - 현재 계약자 기준"""
        if not hasattr(self, 'contractor'):
            return False
        return not self.contractor.submitted_documents.filter(
            require_type='required',
            submitted_quantity__lt=models.F('required_quantity')
        ).exists()

    def get_missing_documents(self):
        """미비 서류 목록 조회 - 현재 계약자 기준"""
        if not hasattr(self, 'contractor'):
            return ContractDocument.objects.none()
        return self.contractor.submitted_documents.filter(
            submitted_quantity__lt=models.F('required_quantity')
        )

    def get_pending_required_documents(self):
        """미제출 필수 서류 목록 조회 - 현재 계약자 기준"""
        if not hasattr(self, 'contractor'):
            return ContractDocument.objects.none()
        return self.contractor.submitted_documents.filter(
            require_type='required',
            status='pending'
        )

    @property
    def contract_files(self):
        """하위 호환성: 계약자의 계약서 파일 접근"""
        if hasattr(self, 'contractor'):
            return self.contractor.contractor_files.all()
        return ContractFile.objects.none()

    def clean(self):
        super().clean()
        if self.key_unit_id and self.unit_type_id:
            if self.key_unit.unit_type_id != self.unit_type_id:
                raise ValidationError({
                    'unit_type': '계약의 타입과 유닛의 타입이 일치하지 않습니다.'
                })

    class Meta:
        ordering = ('-project', '-created', '-pk')  # pk로 정렬 안정성 보장
        verbose_name = '04. 계약 정보'
        verbose_name_plural = '04. 계약 정보'


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
        verbose_name = '05. 계약 공급가격'
        verbose_name_plural = '05. 계약 공급가격'


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

    @property
    def contractoraddress(self):
        """현주소 반환 (하위 호환성을 위한 프로퍼티)"""
        return self.addresses.filter(is_current=True).first()

    class Meta:
        verbose_name = '06. 계약자 정보'
        verbose_name_plural = '06. 계약자 정보'


def get_contract_file_name(instance, filename):
    return get_contract_file_path(instance, filename)


class ContractFile(models.Model):
    contractor = models.ForeignKey('Contractor', on_delete=models.CASCADE, verbose_name='계약자',
                                   related_name='contractor_files')
    file = models.FileField(upload_to=get_contract_file_name, verbose_name='파일경로')
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='사용자')

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if self.file:
            # Preserve original filename before upload_to function changes it
            original_name = getattr(self.file, '_name', None) or getattr(self.file, 'name', None)
            if original_name:
                self.file_name = os.path.basename(original_name)
            else:
                self.file_name = self.file.name.split('/')[-1]

            mime = magic.Magic(mime=True)
            file_pos = self.file.tell()  # 현재 파일 커서 위치 백업
            self.file_type = mime.from_buffer(self.file.read(2048))  # 2048바이트 정도면 충분
            self.file.seek(file_pos)  # 원래 위치로 복구
            self.file_size = self.file.size
        super().save(*args, **kwargs)


file_cleanup_signals(ContractFile)  # ContractFile 파일인스턴스 직접 삭제시
related_file_cleanup(Contractor, related_name='contractor_files', file_field_name='file')  # Contractor 연관 모델 삭제 시


class ContractDocument(models.Model):
    """계약자별 서류 제출 기록"""
    contractor = models.ForeignKey('Contractor', on_delete=models.CASCADE,
                                   verbose_name='계약자', related_name='submitted_documents')
    required_document = models.ForeignKey(RequiredDocument, on_delete=models.PROTECT,
                                          verbose_name='필요 서류', related_name='contractor_submissions')
    submitted_quantity = models.PositiveIntegerField('제출 수량', default=0)
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='updated_contract_documents',
                                verbose_name='편집자')

    def __str__(self):
        if self.required_document:
            return f'{self.contractor.name} - {self.required_document.document_type.name}'
        return f'{self.contractor.name} - (서류 미지정)'

    @property
    def is_complete(self):
        """제출 완료 여부 확인"""
        if not self.required_document:
            return False
        return self.submitted_quantity >= self.required_document.quantity

    @property
    def document_type(self):
        """하위 호환성을 위한 속성"""
        return self.required_document.document_type if self.required_document else None

    @property
    def required_quantity(self):
        """필요 수량 (RequiredDocument에서 가져옴)"""
        return self.required_document.quantity if self.required_document else 0

    @property
    def require_type(self):
        """필수 여부 (RequiredDocument에서 가져옴)"""
        return self.required_document.require_type if self.required_document else 'required'

    class Meta:
        db_table = 'contract_document'
        ordering = ['required_document__display_order', 'id']
        unique_together = [['contractor', 'required_document']]
        verbose_name = '계약자 제출 서류'
        verbose_name_plural = '계약자 제출 서류'


def get_contract_document_file_name(instance, filename):
    """계약자 제출 서류 파일 업로드 경로"""
    return get_upload_path(instance, filename, 'contract_documents', 'files')


class ContractDocumentFile(models.Model):
    """계약자 제출 서류 첨부 파일"""
    contract_document = models.ForeignKey(ContractDocument, on_delete=models.CASCADE,
                                          verbose_name='계약 서류', related_name='files')
    file = models.FileField(upload_to=get_contract_document_file_name, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('파일 타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('파일 크기', null=True, blank=True)
    uploaded_date = models.DateTimeField('업로드일시', auto_now_add=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, blank=True, verbose_name='업로드자')

    def __str__(self):
        return f'{self.contract_document} - {self.file_name}'

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name.split('/')[-1]
            mime = magic.Magic(mime=True)
            file_pos = self.file.tell()
            self.file_type = mime.from_buffer(self.file.read(2048))
            self.file.seek(file_pos)
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'contract_document_file'
        ordering = ['-uploaded_date']
        verbose_name = '제출 서류 파일'
        verbose_name_plural = '제출 서류 파일'


# 파일 삭제 시그널 설정
file_cleanup_signals(ContractDocumentFile)
related_file_cleanup(ContractDocument, related_name='files', file_field_name='file')


class ContractorAddress(models.Model):
    contractor = models.ForeignKey('Contractor', on_delete=models.CASCADE, verbose_name='계약자 정보',
                                   related_name='addresses')
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
        verbose_name = '07. 계약자 주소'
        verbose_name_plural = '07. 계약자 주소'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['contractor'],
                condition=models.Q(is_current=True),
                name='unique_current_address_per_contractor'
            )
        ]


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


class ContractorConsultationLogs(models.Model):
    contractor = models.ForeignKey('Contractor', on_delete=models.CASCADE, verbose_name='계약자',
                                   related_name='consultation_logs')
    # 상담 기본 정보
    consultation_date = models.DateField('상담일자')
    CHANNEL_CHOICES = (('visit', '방문'), ('phone', '전화'), ('email', '이메일'),
                       ('sms', '문자'), ('kakao', '카카오톡'), ('other', '기타'))
    channel = models.CharField('상담채널', max_length=10, choices=CHANNEL_CHOICES)
    CATEGORY_CHOICES = (('payment', '납부상담'), ('contract', '계약상담'), ('change', '변경상담'),
                        ('complaint', '민원/불만'), ('question', '문의'), ('succession', '승계상담'),
                        ('release', '해지상담'), ('document', '서류관련'), ('etc', '기타'))
    category = models.CharField('상담유형', max_length=20, choices=CATEGORY_CHOICES)
    # 상담 내용
    title = models.CharField('상담제목', max_length=255, blank=True, default='')
    content = models.TextField('상담내용', blank=True, default='')
    # 상담 처리 상태
    STATUS_CHOICES = (('1', '처리대기'), ('2', '처리중'), ('3', '처리완료'), ('4', '보류'))
    status = models.CharField('처리상태', max_length=1, choices=STATUS_CHOICES, default='1')
    PRIORITY_CHOICES = (('low', '낮음'), ('normal', '보통'), ('high', '높음'), ('urgent', '긴급'))
    priority = models.CharField('중요도', max_length=10, choices=PRIORITY_CHOICES, default='normal')
    # 상담 담당자
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='consultations', verbose_name='상담담당자')
    # 후속 조치
    follow_up_required = models.BooleanField('후속조치 필요', default=False)
    # follow_up_date = models.DateField('후속조치일', null=True, blank=True)
    follow_up_note = models.TextField('후속조치 내용', blank=True)
    completion_date = models.DateField('처리완료일', null=True, blank=True)
    # 기타
    is_important = models.BooleanField('중요표시', default=False)
    # 시스템 필드
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('수정일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='created_consultations', verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_consultations', verbose_name='수정자')

    def __str__(self):
        return f'[{self.consultation_date}] {self.contractor.name} - {self.get_category_display()}'

    class Meta:
        ordering = ['-consultation_date', '-created']
        verbose_name = '08. 계약자 상담 기록'
        verbose_name_plural = '08. 계약자 상담 기록'


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
        verbose_name = '09. 권리 의무 승계'
        verbose_name_plural = '09. 권리 의무 승계'


class ContractorRelease(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    contractor = models.OneToOneField('Contractor', on_delete=models.CASCADE, verbose_name='계약자 정보')
    STATUS_CHOICES = (('0', '신청 취소'), ('3', '해지 신청'), ('4', '해지 완료'), ('5', '자격 상실'))
    status = models.CharField('상태', choices=STATUS_CHOICES, max_length=1)
    refund_amount = models.PositiveIntegerField('환불(예정)금액', null=True, blank=True)
    refund_account_bank = models.CharField('환불계좌(은행)', max_length=20, null=True, blank=True)
    refund_account_number = models.CharField('환불계좌(번호)', max_length=25, null=True, blank=True)
    refund_account_depositor = models.CharField('환불계좌(예금주)', max_length=20, null=True, blank=True)
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
        verbose_name = '10. 계약 해지 정보'
        verbose_name_plural = '10. 계약 해지 정보'
