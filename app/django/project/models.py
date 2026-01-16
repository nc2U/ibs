import os

import magic
from django.conf import settings
from django.db import models

from _utils.file_cleanup import file_cleanup_signals, related_file_cleanup
from _utils.file_upload import get_project_file_path


class Project(models.Model):
    issue_project = models.OneToOneField('work.IssueProject', on_delete=models.CASCADE, verbose_name="업무 프로젝트")
    name = models.CharField('프로젝트명', max_length=30, unique=True, db_index=True)
    order = models.PositiveSmallIntegerField('정렬순서', default=100)
    KIND_CHOICES = (('1', '공동주택(아파트)'), ('2', '공동주택(타운하우스)'), ('3', '주상복합(아파트)'), ('4', '주상복합(오피스텔)'),
                    ('5', '근린생활시설'), ('6', '생활형숙박시설'), ('7', '지식산업센터'), ('8', '기타'))
    kind = models.CharField('프로젝트종류', max_length=1, choices=KIND_CHOICES)
    start_year = models.CharField('사업개시년도', max_length=4)
    is_direct_manage = models.BooleanField('직영운영여부', default=False,
                                           help_text='본사 직접 운영하는 프로젝트인 경우 체크, 즉 시행대행이나 업무대행이 아닌 경우')
    is_returned_area = models.BooleanField('토지환지여부', default=False, help_text='해당 사업부지가 환지방식 도시개발사업구역인 경우 체크')
    is_unit_set = models.BooleanField('동호지정여부', default=False, help_text='현재 동호수를 지정하지 않는 경우 체크하지 않음')
    # 사업 일정 필드 (캐시 플로우 동적 생성용) - 필수 입력
    monthly_aggr_start_date = models.DateField('월별집계시작일', help_text='이 날짜 이전은 누계로 집계됩니다.')
    construction_start_date = models.DateField('착공월(예상)', help_text='착공 예정일 또는 실제 착공일. 이 날짜부터 공사기간을 계산합니다.')
    construction_period_months = models.PositiveSmallIntegerField('공사기간(개월)',
                                                                  help_text='예상 공사기간 (개월 단위). 착공월부터 이 기간 + 5개월까지 월별 집계됩니다.')
    location = models.CharField('대지위치', max_length=255, blank=True, default='')
    area_usage = models.CharField('용도지역지구', max_length=50, blank=True, default='', null=True)
    build_size = models.CharField('건축규모', max_length=50, blank=True, default='', null=True)
    num_unit = models.PositiveSmallIntegerField('세대(호/실)수', null=True, blank=True)
    buy_land_extent = models.DecimalField('대지매입면적', max_digits=12, decimal_places=4, null=True, blank=True)
    scheme_land_extent = models.DecimalField('계획대지면적', max_digits=12, decimal_places=4, null=True, blank=True)
    donation_land_extent = models.DecimalField('기부채납면적', max_digits=11, decimal_places=4, null=True, blank=True)
    on_floor_area = models.DecimalField('지상연면적', max_digits=12, decimal_places=4, null=True, blank=True)
    under_floor_area = models.DecimalField('지하연면적', max_digits=11, decimal_places=4, null=True, blank=True)
    total_floor_area = models.DecimalField('총 연면적', max_digits=12, decimal_places=4, null=True, blank=True)
    build_area = models.DecimalField('건축면적', max_digits=11, decimal_places=4, null=True, blank=True)
    floor_area_ratio = models.DecimalField('용적율', max_digits=7, decimal_places=4, null=True, blank=True)
    build_to_land_ratio = models.DecimalField('건폐율', max_digits=6, decimal_places=4, null=True, blank=True)
    num_legal_parking = models.PositiveSmallIntegerField('법정주차대수', null=True, blank=True)
    num_planed_parking = models.PositiveSmallIntegerField('계획주차대수', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', '-start_year', 'id']
        verbose_name = '01. 프로젝트(현장)'
        verbose_name_plural = '01. 프로젝트(현장)'


class ProjectIncBudget(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    account = models.ForeignKey('ledger.ProjectAccount', on_delete=models.PROTECT, null=True, blank=True,
                                verbose_name='계정')
    account_d2 = models.ForeignKey('ibs.ProjectAccountD2', on_delete=models.PROTECT, verbose_name='대분류')
    account_d3 = models.ForeignKey('ibs.ProjectAccountD3', on_delete=models.PROTECT, verbose_name='소분류')
    order_group = models.ForeignKey('contract.OrderGroup', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='차수', help_text='해당 차수가 없는 경우 생략가능')
    unit_type = models.ForeignKey('items.UnitType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='타입',
                                  help_text='해당 타입이 없는 경우 생략가능')
    item_name = models.CharField('항목명칭', max_length=20, blank=True, default='',
                                 help_text='차수와 타입을 선택하지 않은 경우 기재. 그렇지 않은 경우 생략할 것')
    average_price = models.PositiveBigIntegerField(verbose_name='평균 가격', null=True, blank=True,
                                                   help_text='이 항목 생략 시 수량 및 수입 예산을 바탕으로 자동 계산')
    quantity = models.PositiveSmallIntegerField(verbose_name='수량')
    budget = models.PositiveBigIntegerField(verbose_name='기초(인준) 수입 예산')
    revised_budget = models.PositiveBigIntegerField(verbose_name='현황(변경) 수입 예산', null=True, blank=True)

    def __str__(self):
        return self.item_name

    class Meta:
        ordering = ('id', '-project')
        verbose_name = '02. 현장 수입예산'
        verbose_name_plural = '02. 현장 수입예산'


class ProjectOutBudget(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    order = models.PositiveSmallIntegerField('순서', blank=True, null=True)
    account = models.ForeignKey('ledger.ProjectAccount', on_delete=models.PROTECT, null=True, blank=True,
                                verbose_name='계정')
    account_d2 = models.ForeignKey('ibs.ProjectAccountD2', on_delete=models.PROTECT, verbose_name='대분류')
    account_d3 = models.ForeignKey('ibs.ProjectAccountD3', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='소분류')
    account_opt = models.CharField('중분류', max_length=10, blank=True, default='')
    basis_calc = models.CharField('산출근거', max_length=255, blank=True, default='',
                                  help_text='사업수지표 항목 상 해당 금액의 산출 근거 기재')
    budget = models.PositiveBigIntegerField(verbose_name='기초(인준) 지출 예산')
    revised_budget = models.PositiveBigIntegerField(verbose_name='현황(변경) 지출 예산', null=True, blank=True)

    def __str__(self):
        return self.account_d3.name

    class Meta:
        ordering = ('order', 'id', '-project')
        verbose_name = '03. 현장 지출예산'
        verbose_name_plural = '03. 현장 지출예산'


class Site(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.PROTECT, verbose_name='프로젝트')
    order = models.PositiveSmallIntegerField('순서')
    district = models.CharField('행정동', max_length=10)
    lot_number = models.CharField('지번', max_length=10, db_index=True)
    site_purpose = models.CharField('지목', max_length=10)
    official_area = models.DecimalField('대지면적', max_digits=12, decimal_places=7)
    returned_area = models.DecimalField('환지면적', max_digits=12, decimal_places=7, null=True, blank=True)
    notice_price = models.PositiveIntegerField('공시지가', null=True, blank=True)
    dup_issue_date = models.DateField('등본발급일', null=True, blank=True)
    rights_a = models.TextField('갑구 권리 제한사항', blank=True, default='')
    rights_b = models.TextField('을구 권리 제한사항', blank=True, default='')
    note = models.TextField('비고', blank=True, default='')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_sites', verbose_name='편집자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def __str__(self):
        return f'{self.district} {self.lot_number}'

    class Meta:
        ordering = ('-project', 'order', 'lot_number')
        verbose_name = '04. 사업부지 목록'
        verbose_name_plural = '04. 사업부지 목록'


def get_info_file(instance, filename):
    return get_project_file_path(instance, filename)


class SiteInfoFile(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=None, verbose_name='등기사항전부증명서',
                             related_name='site_info_files')
    file = models.FileField(upload_to=get_info_file, verbose_name='파일경로')
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


file_cleanup_signals(SiteInfoFile)  # 파일 인스턴스 직접 삭제시
related_file_cleanup(Site, related_name='site_info_files', file_field_name='file')  # 연관 모델 삭제 시


class SiteOwner(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.PROTECT, verbose_name='프로젝트')
    owner = models.CharField('소유자', max_length=20, db_index=True)
    use_consent = models.BooleanField('사용동의 여부', default=False)
    date_of_birth = models.DateField('생년월일', null=True, blank=True)
    phone1 = models.CharField('주연락처', max_length=13, blank=True)
    phone2 = models.CharField('비상연락처', max_length=13, blank=True)
    zipcode = models.CharField('우편번호', max_length=5, blank=True)
    address1 = models.CharField('주소', max_length=35, blank=True)
    address2 = models.CharField('상세주소', max_length=50, blank=True)
    address3 = models.CharField('참고항목', max_length=30, blank=True)
    OWN_CHOICES = (('1', '개인'), ('2', '법인'), ('3', '국공유지'))
    own_sort = models.CharField('소유구분', max_length=1, choices=OWN_CHOICES, default='1')
    sites = models.ManyToManyField(Site, through='SiteOwnshipRelationship', through_fields=('site_owner', 'site'),
                                   related_name='owners', verbose_name='소유부지')
    note = models.TextField('특이사항', blank=True, default='')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_site_owners', verbose_name='편집자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def __str__(self):
        return self.owner

    class Meta:
        ordering = ('-id',)
        verbose_name = '05. 사업부지 소유자'
        verbose_name_plural = '05. 사업부지 소유자'


class SiteOwnshipRelationship(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    site_owner = models.ForeignKey(SiteOwner, on_delete=models.CASCADE, related_name='relations')
    ownership_ratio = models.DecimalField('소유지분', max_digits=10, decimal_places=7, null=True, blank=True)
    owned_area = models.DecimalField('소유면적', max_digits=12, decimal_places=7, null=True, blank=True)
    acquisition_date = models.DateField('취득일자', null=True, blank=True)

    def __str__(self):
        return f'{self.site} {self.site_owner}'

    class Meta:
        ordering = ('-id',)
        verbose_name = '06. 사업부지 소유관계'
        verbose_name_plural = '06. 사업부지 소유관계'


class SiteOwnerConsultationLogs(models.Model):
    site_owner = models.ForeignKey('SiteOwner', on_delete=models.CASCADE, verbose_name='토지소유자',
                                   related_name='consultation_logs')
    # 상담 기본 정보
    consultation_date = models.DateField('상담일자')
    CHANNEL_CHOICES = (('visit', '방문'), ('phone', '전화'), ('email', '이메일'),
                       ('sms', '문자'), ('kakao', '카카오톡'), ('other', '기타'))
    channel = models.CharField('상담채널', max_length=10, choices=CHANNEL_CHOICES)
    # 상담 관련
    title = models.CharField('상담제목', max_length=255, blank=True, default='')
    content = models.TextField('상담내용', blank=True, default='')
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='site_owner_consultations', verbose_name='상담담당자')
    # 후속 조치
    follow_up_required = models.BooleanField('후속조치 필요', default=False)
    follow_up_note = models.TextField('후속조치 내용', blank=True)
    completion_date = models.DateField('처리완료일', null=True, blank=True)
    # 시스템 필드
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('수정일시', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='created_site_consultations', verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_site_consultations', verbose_name='수정자')

    def __str__(self):
        return f'[{self.consultation_date}] {self.site_owner.owner} - {self.title}'

    class Meta:
        ordering = ['-consultation_date', '-created']
        verbose_name = '07. 소유자 상담 기록'
        verbose_name_plural = '07. 소유자 상담 기록'
        indexes = [
            models.Index(fields=['site_owner', '-consultation_date']),
        ]


class SiteContract(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.PROTECT, verbose_name='프로젝트')
    owner = models.ForeignKey(SiteOwner, on_delete=models.CASCADE, verbose_name='소유자')
    contract_date = models.DateField('계약체결일')
    total_price = models.PositiveBigIntegerField('총매매대금')
    contract_area = models.DecimalField('계약면적', max_digits=12, decimal_places=7, null=True, blank=True)
    down_pay1 = models.PositiveBigIntegerField('계약금1', null=True, blank=True)
    down_pay1_date = models.DateField('계약금1 지급일', null=True, blank=True)
    down_pay1_is_paid = models.BooleanField('계약금1 지급여부', default=False)
    down_pay2 = models.PositiveBigIntegerField('계약금2', null=True, blank=True)
    down_pay2_date = models.DateField('계약금2 지급일', null=True, blank=True)
    down_pay2_is_paid = models.BooleanField('계약금2 지급여부', default=False)
    inter_pay1 = models.PositiveBigIntegerField('중도금1', null=True, blank=True)
    inter_pay1_date = models.DateField('중도금1 지급일', null=True, blank=True)
    inter_pay1_is_paid = models.BooleanField('중도금1 지급여부', default=False)
    inter_pay2 = models.PositiveBigIntegerField('중도금2', null=True, blank=True)
    inter_pay2_date = models.DateField('중도금2 지급일', null=True, blank=True)
    inter_pay2_is_paid = models.BooleanField('중도금2 지급여부', default=False)
    remain_pay = models.PositiveBigIntegerField('잔금')
    remain_pay_date = models.DateField('잔금 지급일', null=True, blank=True)
    remain_pay_is_paid = models.BooleanField('잔금 지급여부', default=False)
    ownership_completion = models.BooleanField('소유권 확보여부', default=False)
    acc_bank = models.CharField('은행', max_length=20)
    acc_number = models.CharField('계좌번호', max_length=25)
    acc_owner = models.CharField('예금주', max_length=20)
    note = models.TextField('특이사항', blank=True, default='')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_site_contracts', verbose_name='편집자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def __str__(self):
        return f'{self.owner.owner} - [{self.total_price}]'

    class Meta:
        ordering = ('-id',)
        verbose_name = '08. 사업부지 계약현황'
        verbose_name_plural = '08. 사업부지 계약현황'


def get_cont_file(instance, filename):
    return get_project_file_path(instance, filename)


class SiteContractFile(models.Model):
    site_contract = models.ForeignKey(SiteContract, on_delete=models.CASCADE, default=None, verbose_name='계약서',
                                      related_name='site_cont_files')
    file = models.FileField(upload_to=get_cont_file, verbose_name='파일경로', max_length=150)
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='등록자')

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


file_cleanup_signals(SiteContractFile)  # 파일 인스턴스 직접 삭제시
related_file_cleanup(SiteContract, related_name='site_cont_files', file_field_name='file')  # 연관 모델 삭제 시
