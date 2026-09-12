from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex
from django.core.files.storage import default_storage

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_docs_file_path, get_docs_image_path, get_letter_pdf_path, populate_file_meta
from .courts import COURT_CHOICES

DOC_TYPE_CHOICES = (('1', '일반문서'), ('2', '소송기록'))


class Category(models.Model):
    doc_type = models.CharField('유형', max_length=1, choices=DOC_TYPE_CHOICES, null=True, blank=True)
    color = models.CharField('색상', max_length=21, null=True, blank=True)
    name = models.CharField('이름', max_length=100, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='상위 카테고리')
    order = models.PositiveSmallIntegerField('정렬 순서', default=0)
    active = models.BooleanField('사용중', default=True)
    default = models.BooleanField('기본값', default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '01. 카테고리'
        verbose_name_plural = '01. 카테고리'


class BaseModel(models.Model):
    deleted = models.DateTimeField('휴지통', null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        """Mark the instance as deleted."""
        self.deleted = timezone.now()
        self.save(update_fields=['deleted'])

    def restore(self):
        """Restore a soft-deleted instance."""
        self.deleted = None
        self.save()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=None)


class Document(BaseModel):
    issue_project = models.ForeignKey('work.IssueProject', on_delete=models.PROTECT, verbose_name='업무 프로젝트')
    doc_type = models.CharField('유형', max_length=1, choices=DOC_TYPE_CHOICES, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='카테고리')
    lawsuit = models.ForeignKey('docs.LawsuitCase', on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='사건번호')
    title = models.CharField('제목', max_length=255, db_index=True)
    execution_date = models.DateField('문서 시행일자', null=True, blank=True, help_text='문서 발신/수신/시행일자')
    description = models.CharField('설명', max_length=255, blank=True, default='')
    hit = models.PositiveIntegerField('조회수', default=0)
    ip = models.GenericIPAddressField('아이피', null=True, blank=True)
    device = models.CharField('등록기기', max_length=255, blank=True, default='')
    is_pinned = models.BooleanField('상단 고정', default=False)

    # ── 보안 등급 (4단계) ──────────────────────────────────────────────
    SECURITY_PRIVATE = '1'  # 비공개: 작성자 + 명시적 허가자만
    SECURITY_TEAM = '2'  # 팀 공개: 작성자의 소속 부서원
    SECURITY_PROJECT = '3'  # 프로젝트 공개: 해당 워크스페이스 멤버
    SECURITY_COMPANY = '4'  # 전사 공개: 로그인한 모든 직원
    SECURITY_LEVEL_CHOICES = (
        (SECURITY_PRIVATE, '1등급 비공개 (작성자/허가자)'),
        (SECURITY_TEAM, '2등급 팀 공개 (소속 부서)'),
        (SECURITY_PROJECT, '3등급 프로젝트 공개 (워크스페이스 멤버)'),
        (SECURITY_COMPANY, '4등급 전사 공개'),
    )
    security_level = models.CharField(
        '보안 등급', max_length=1,
        choices=SECURITY_LEVEL_CHOICES, default=SECURITY_PROJECT,
        db_index=True,
        help_text='1:비공개 / 2:팀공개 / 3:프로젝트공개 / 4:전사공개',
    )

    # ── 명시적 열람 허가자 (등급 초월) ────────────────────────────────
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        related_name='granted_documents',
        verbose_name='개별 열람 허가자',
        help_text='보안 등급과 무관하게 열람을 허가할 사용자',
    )

    is_blind = models.BooleanField('숨김', default=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_documents', verbose_name='편집자')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()  # Default manager (exclude soft-deleted)
    all_objects = models.Manager()  # Include all objects

    def __str__(self):
        return self.title

    @property
    def is_new(self):
        return timezone.now() < self.created + timedelta(days=3)

    def is_visible_to(self, user) -> bool:
        """
        사용자의 이 문서 열람 가능 여부를 판단합니다.

        판단 순서:
        1. 슈퍼유저 / work_manager → 전체 허용
        2. is_blind → 위 관리자만 허용 (일반 사용자 차단)
        3. 작성자 본인 → 허용
        4. allowed_users(명시적 허가자) → 허용
        5. security_level별 조건 판단
        """
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, 'work_manager', False):
            return True
        if self.is_blind:
            return False
        if self.creator_id and self.creator_id == user.pk:
            return True
        if self.allowed_users.filter(pk=user.pk).exists():
            return True

        level = self.security_level
        if level == self.SECURITY_COMPANY:
            return True
        if level == self.SECURITY_PROJECT:
            return self.issue_project.members.filter(user=user).exists()
        if level == self.SECURITY_TEAM:
            from company.models import StaffAssignment
            creator_dept_ids = StaffAssignment.objects.filter(
                staff__user_id=self.creator_id
            ).values_list('department_id', flat=True)
            return StaffAssignment.objects.filter(
                staff__user=user,
                department_id__in=creator_dept_ids,
            ).exists()
        # SECURITY_PRIVATE (1등급): 위 조건 모두 불충족
        return False

    class Meta:
        ordering = ['-is_pinned', '-created']
        verbose_name = '02. 문서'
        verbose_name_plural = '02. 문서'
        indexes = [
            GinIndex(fields=['title'], opclasses=['gin_trgm_ops'], name='docs_document_title_trgm'),
            GinIndex(fields=['description'], opclasses=['gin_trgm_ops'], name='docs_document_desc_trgm'),
        ]


class Link(models.Model):
    docs = models.ForeignKey(Document, on_delete=models.CASCADE, default=None, verbose_name='문서', related_name='links')
    link = models.URLField(max_length=500, verbose_name='링크')
    description = models.CharField('부가설명', max_length=255, blank=True, default='')
    hit = models.PositiveIntegerField('클릭수', default=0)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_DEFAULT, default=1, verbose_name='등록자')
    created = models.DateTimeField('등록일', auto_now_add=True)

    def __str__(self):
        return self.link


class File(models.Model):
    docs = models.ForeignKey(Document, on_delete=models.CASCADE, default=None, verbose_name='문서', related_name='files')
    file = models.FileField(upload_to=get_docs_file_path, storage=default_storage, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    description = models.CharField('부가설명', max_length=255, blank=True, default='')
    hit = models.PositiveIntegerField('다운로드수', default=0)
    created = models.DateTimeField('등록일', auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='등록자')

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            populate_file_meta(self)
        super().save(*args, **kwargs)


file_cleanup_signals(File)  # 파일인스턴스 직접 삭제시


class Image(models.Model):
    docs = models.ForeignKey(Document, on_delete=models.CASCADE, default=None, verbose_name='문서',
                             related_name='images')
    image = models.ImageField(upload_to=get_docs_image_path, storage=default_storage, verbose_name='이미지')
    image_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    image_type = models.CharField('타입', max_length=30, blank=True)
    image_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        if self.image and not self.image_name:
            populate_file_meta(self, file_field='image', name_field='image_name', type_field='image_type',
                               size_field='image_size')
        super().save(*args, **kwargs)


file_cleanup_signals(Image)  # 파일인스턴스 직접 삭제시


class LawsuitCase(models.Model):
    issue_project = models.ForeignKey('work.IssueProject', on_delete=models.PROTECT, verbose_name='업무 프로젝트')
    SORT_CHOICES = (('1', '민사'), ('2', '형사'), ('3', '행정'), ('4', '신청'), ('5', '집행'))
    sort = models.CharField('유형', max_length=1, choices=SORT_CHOICES)
    LEVEL_CHOICES = (
        ('1', '1심'), ('2', '2심'), ('3', '3심'), ('4', '고소/수사'),
        ('5', '신청'), ('6', '항고/이의'), ('7', '압류/추심'), ('8', '정지/이의'))
    level = models.CharField('심급', max_length=1, choices=LEVEL_CHOICES, blank=True)
    related_case = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='관련사건',
                                     help_text='본안 사건인 경우 원심 사건, 신청/집행 사건인 경우 관련 본안 사건 지정')
    court = models.CharField('법원명', max_length=10, choices=COURT_CHOICES, blank=True, default='')
    other_agency = models.CharField('기타 처리기관', max_length=30, blank=True, default='',
                                    help_text='사건 유형이 기소 전 형사 사건인 경우 해당 수사기관을 기재')
    case_number = models.CharField('사건번호', max_length=20)
    case_name = models.CharField('사건명', max_length=30, db_index=True)
    plaintiff = models.CharField('원고(신청인)', max_length=30, blank=True, default='')
    plaintiff_attorney = models.CharField('원고 대리인', max_length=50, blank=True, default='')
    plaintiff_case_price = models.PositiveBigIntegerField('원고 소가', null=True, blank=True)
    defendant = models.CharField('피고(피신청인)', max_length=30)
    defendant_attorney = models.CharField('피고 대리인', max_length=50, blank=True, default='')
    defendant_case_price = models.PositiveBigIntegerField('피고 소가', null=True, blank=True)
    related_debtor = models.CharField('제3채무자', max_length=30, blank=True, default='')
    case_start_date = models.DateField('사건개시일')
    case_end_date = models.DateField('사건종결일', null=True, blank=True)
    summary = models.TextField('개요 및 경과', blank=True, default='')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자',
                                related_name='lawsuitcases')
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='updated_lawsuitcases', verbose_name='편집자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def __str__(self):
        agency = self.get_court_display() if self.get_court_display() else self.other_agency
        return f'{agency} {self.case_number} {self.case_name}'

    class Meta:
        ordering = ['-case_start_date', '-id']
        verbose_name = '03. 소송사건'
        verbose_name_plural = '03. 소송사건'


# ============================================================
# 공문 관리 (Official Letter)
# ============================================================

class LetterSequence(models.Model):
    """회사별 연도별 공문 번호 시퀀스 관리"""
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE,
                                related_name='letter_sequences', verbose_name='회사')
    year = models.PositiveIntegerField('연도')
    last_sequence = models.PositiveIntegerField('마지막 번호', default=0)

    class Meta:
        ordering = ['-year']
        unique_together = ['company', 'year']
        verbose_name = '05. 공문 번호 시퀀스'
        verbose_name_plural = '05. 공문 번호 시퀀스'

    def __str__(self):
        return f'{self.company.name} - {self.year}'

    @classmethod
    def _get_prefix(cls, company):
        import re
        prefix = company.short_name.strip() if getattr(company, 'short_name', None) else ''
        if not prefix and getattr(company, 'name', None):
            prefix = re.sub(r'\(주\)|주식회사|\s+', '', company.name)
        return prefix

    @classmethod
    def peek_next_document_number(cls, company):
        """다음에 발급될 예상 문서번호 조회 (시퀀스를 증가시키지 않음)"""
        current_year = timezone.now().year
        sequence = cls.objects.filter(company=company, year=current_year).first()
        next_seq = (sequence.last_sequence + 1) if sequence else 1
        prefix = cls._get_prefix(company)
        if prefix:
            return f'{prefix}-{current_year}-{next_seq:03d}'
        return f'{current_year}-{next_seq:03d}'

    @classmethod
    def get_next_document_number(cls, company):
        """다음 문서번호 생성 ([회사약칭]-YYYY-NNN 형식, 시퀀스 원자적 증가)"""
        current_year = timezone.now().year

        sequence, created = cls.objects.get_or_create(
            company=company,
            year=current_year,
            defaults={'last_sequence': 0}
        )

        sequence.last_sequence += 1
        sequence.save()

        prefix = cls._get_prefix(company)
        if prefix:
            return f'{prefix}-{current_year}-{sequence.last_sequence:03d}'
        return f'{current_year}-{sequence.last_sequence:03d}'


class OfficialLetter(models.Model):
    """공문 모델"""
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='official_letters',
                                verbose_name='회사')  # 회사
    document_number = models.CharField('문서번호', max_length=50, unique=True, db_index=True,
                                       editable=False)  # 문서번호 (자동 생성)
    recipient_name = models.CharField('수신처명', max_length=100)  # 수신처 정보
    via = models.CharField('경유', max_length=100, blank=True, default='', help_text='최종 수신처로 가기 전 거치는 중간 기관 또는 부서')
    recipient_reference = models.CharField('참조', max_length=100, blank=True, default='', help_text='참조인 또는 부서')
    title = models.CharField('제목', max_length=255, db_index=True)  # 제목
    content = models.TextField('내용')  # 내용
    seal = models.ForeignKey('company.CompanySeal', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='official_letters', verbose_name='날인 인감')
    co_seal = models.ForeignKey('company.CompanySeal', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='co_official_letters', verbose_name='공동대표 보조 인감',
                                help_text='공동대표 체제 시 두 번째 대표이사의 날인 인감')

    SENDER_DISPLAY_CHOICES = (
        ('company_only', '회사명만 표기 (주식회사 OOO)'),
        ('company_rep', '회사명 + 대표직함 및 성명 표기 (주식회사 OOO 대표이사 홍길동)'),
        ('co_rep', '공동대표 병기 (공동대표이사 A & B 나란히 날인)'),
    )
    sender_display_type = models.CharField(
        '발신 명의 표기 방식', max_length=20, choices=SENDER_DISPLAY_CHOICES, default='company_only',
        help_text='공문서 하단 중앙 발신 명의 및 인장 날인 형태 선택'
    )
    sender_duty_title = models.CharField(
        '발신 명의 표기 직책', max_length=20, blank=True, default='',
        help_text='예: 대표이사, 본부장, 현장소장 (단독/직접 발송 시 지정, 미지정 시 결재선/기본값 자동 산출)'
    )
    sender_name = models.CharField(
        '발신 명의 표기 성명', max_length=30, blank=True, default='',
        help_text='예: 유용식, 고창균 (단독/직접 발송 시 지정, 미지정 시 결재선/기본값 자동 산출)'
    )

    issue_date = models.DateField(
        '발신 요청일(예정일)',
        help_text='기안자가 희망하는 발신 예정일/요청일. 실제 공문서 시행일자는 최종 결재 승인일(또는 발송 완료일)로 자동 확정됩니다.'
    )
    sender_zipcode = models.CharField('발신 우편번호', max_length=5, blank=True, default='')
    sender_address = models.CharField('발신 주소', max_length=255, blank=True, default='')

    drafter_name = models.CharField('기안/담당자명', max_length=50)  # 기안/담당자 정보
    drafter_position = models.CharField('기안/담당 직위', max_length=50, blank=True, default='')
    is_solo_approval = models.BooleanField(
        '승인(전결)권자 직접 기안 (담당 생략)', default=False,
        help_text='대표이사, 현장소장, 본부장 등 최종 승인(전결)권자가 직접 기안하여 공문서 하단 담당자란을 생략하고 단독 결재로 처리하는 경우'
    )

    recipient_address = models.CharField('수신처 주소', max_length=255, blank=True, default='')
    recipient_contact = models.CharField('수신처 연락처', max_length=50, blank=True, default='')

    attachment_text = models.TextField('붙임 텍스트', blank=True, default='',
                                       help_text='직접 텍스트로 붙임 목록을 기입할 경우 사용')

    DISCLOSURE_CHOICES = (
        ('1', '공개'),
        ('2', '부분공개'),
        ('3', '비공개'),
    )
    disclosure_type = models.CharField(
        '공개 구분', max_length=1, choices=DISCLOSURE_CHOICES, default='1',
        help_text='1: 공개, 2: 부분공개, 3: 비공개(영업비밀/대외비)'
    )

    DISPATCH_METHOD_CHOICES = (
        ('email', '이메일'),
        ('registered_mail', '등기우편'),
        ('direct', '인편/직접교부'),
        ('courier', '퀵/택배'),
        ('fax', '팩스'),
        ('etc', '기타'),
    )
    dispatch_method = models.CharField('발송 방법', max_length=20, choices=DISPATCH_METHOD_CHOICES,
                                       default='email')
    tracking_number = models.CharField('등기/송장 번호', max_length=50, blank=True, default='',
                                       help_text='등기우편 번호, 송장번호, 팩스 확인번호 등')
    dispatched_at = models.DateTimeField('발송 완료일시', null=True, blank=True)

    pdf_file = models.FileField('PDF 파일', upload_to=get_letter_pdf_path, storage=default_storage,
                                null=True, blank=True)  # 생성된 PDF
    APPROVAL_STATUS_CHOICES = (
        ('none', '미상신'),
        ('pending', '결재진행중'),
        ('approved', '결재승인'),
        ('rejected', '반려'),
    )
    approval_document = models.ForeignKey(
        'approval.ApprovalDocument', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='official_letters',
        verbose_name='연동 전자결재 문서'
    )
    approval_status = models.CharField(
        '결재 상태', max_length=10, choices=APPROVAL_STATUS_CHOICES,
        default='none', db_index=True
    )
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, verbose_name='작성자', related_name='created_letters')  # 메타데이터
    updator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='수정자',
                                related_name='updated_letters')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-created']
        verbose_name = '06. 공문'
        verbose_name_plural = '06. 공문'

    def __str__(self):
        return f'{self.document_number} - {self.title}'

    def save(self, *args, **kwargs):
        # 문서번호 자동 생성
        if not self.document_number:
            self.document_number = LetterSequence.get_next_document_number(self.company)
        super().save(*args, **kwargs)

    @property
    def effective_issue_date(self):
        """
        공문서(PDF/시행)에 공식 표기되는 유효 시행일자:
        1. 이미 대외 발송이 완료된 경우: dispatched_at의 날짜 (실제 발송 시행일)
        2. 전자결재가 최종 승인된 경우:
           - 승인 완료일(completed_at)이 발신 요청일보다 늦거나 같으면 승인일 확정
           - 기안자가 먼 미래 일자로 발송 요청한 경우 요청일 유지
        3. 그 외 결재 진행 중 또는 수동 발송: 기안 시 입력한 발신 예정일(issue_date)
        """
        if self.dispatched_at:
            return self.dispatched_at.date()

        if self.approval_document and self.approval_document.completed_at:
            app_date = self.approval_document.completed_at.date()
            if not self.issue_date or app_date >= self.issue_date:
                return app_date
            return self.issue_date

        return self.issue_date

    def get_pdf_filename(self):
        """PDF 다운로드용 파일명 생성"""
        safe_title = self.title[:30].replace(' ', '_').replace('/', '_')
        return f'{self.document_number}_{safe_title}.pdf'


file_cleanup_signals(OfficialLetter, file_field_names=['pdf_file'])  # PDF 파일 자동 삭제


def get_letter_attachment_path(instance, filename):
    return f'official_letters/{instance.letter.company_id}/attachments/{filename}'


class OfficialLetterAttachment(models.Model):
    """공문 첨부파일 모델"""
    letter = models.ForeignKey(
        OfficialLetter, on_delete=models.CASCADE,
        related_name='attachments', verbose_name='공문'
    )
    file = models.FileField('첨부파일', upload_to=get_letter_attachment_path, storage=default_storage)
    name = models.CharField('붙임 명칭', max_length=255, blank=True, default='',
                            help_text='공문에 표기될 명칭 (미입력 시 파일명 사용)')
    quantity = models.CharField('수량/부수', max_length=50, blank=True, default='1부',
                                help_text='예: 1부, 2부, 1식 등')
    ordering = models.PositiveSmallIntegerField('표시 순서', default=1)
    created = models.DateTimeField('등록일시', auto_now_add=True)

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name = '07. 공문 첨부파일'
        verbose_name_plural = '07. 공문 첨부파일'

    def __str__(self):
        return self.name or self.file.name


file_cleanup_signals(OfficialLetterAttachment, file_field_names=['file'])
