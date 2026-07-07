import os
from datetime import datetime, timedelta

import magic
from django.conf import settings
from django.db import models
from django.utils import timezone

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_docs_file_path, get_docs_image_path, get_letter_pdf_path
from .courts import COURT_CHOICES


class DocType(models.Model):
    TYPE_CHOICES = (('1', '업무 문서'), ('2', '소송 기록'), ('3', '기타 문서'))
    type = models.CharField('이름', max_length=1, choices=TYPE_CHOICES)

    def __str__(self):
        return self.get_type_display()

    class Meta:
        ordering = ['id']
        verbose_name = '01. 유형'
        verbose_name_plural = '01. 유형'


DOC_TYPE_CHOICES = (('1', '일반 업무'), ('2', '소송 업무'))


class Category(models.Model):
    doc_type_new = models.CharField('유형', max_length=1, choices=DOC_TYPE_CHOICES, null=True, blank=True)
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
        self.deleted = datetime.now()
        self.save()

    def restore(self):
        """Restore a soft-deleted instance."""
        self.deleted = None
        self.save()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=None)


class Document(BaseModel):
    issue_project = models.ForeignKey('work.IssueProject', on_delete=models.PROTECT, verbose_name='업무 프로젝트')
    doc_type_new = models.CharField('유형', max_length=1, choices=DOC_TYPE_CHOICES, null=True, blank=True)
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
    is_secret = models.BooleanField('비밀글', default=False)
    password = models.CharField('패스워드', max_length=255, blank=True, default='')
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

    def is_new(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M')
        new_period = self.created + timedelta(days=3)
        return today < new_period.strftime('%Y-%m-%d %H:%M')

    class Meta:
        ordering = ['-is_pinned', '-created']
        verbose_name = '02. 문서'
        verbose_name_plural = '02. 문서'


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
    file = models.FileField(upload_to=get_docs_file_path, verbose_name='파일')
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


file_cleanup_signals(File)  # 파일인스턴스 직접 삭제시


class Image(models.Model):
    docs = models.ForeignKey(Document, on_delete=models.CASCADE, default=None, verbose_name='문서',
                             related_name='images')
    image = models.ImageField(upload_to=get_docs_image_path, verbose_name='이미지')
    image_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    image_type = models.CharField('타입', max_length=30, blank=True)
    image_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        if self.image and not self.image_name:
            self.image_name = self.image.name.split('/')[-1]
            mime = magic.Magic(mime=True)
            image_pos = self.image.tell()  # 현재 이미지 파일 커서 위치 백업
            self.image_type = mime.from_buffer(self.image.read(2048))  # 2048바이트 정도면 충분
            self.image.seek(image_pos)  # 원래 위치로 복구
            self.image_size = self.image.size
        super().save(*args, **kwargs)


file_cleanup_signals(Image)  # 파일인스턴스 직접 삭제시


class LawsuitCase(models.Model):
    issue_project = models.ForeignKey('work.IssueProject', on_delete=models.CASCADE, verbose_name='업무 프로젝트')
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
    def get_next_document_number(cls, company):
        """다음 문서번호 생성 (YYYY-NNN 형식)"""
        current_year = timezone.now().year

        sequence, created = cls.objects.get_or_create(
            company=company,
            year=current_year,
            defaults={'last_sequence': 0}
        )

        sequence.last_sequence += 1
        sequence.save()

        return f'{current_year}-{sequence.last_sequence:03d}'


class OfficialLetter(models.Model):
    """공문 모델"""
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE,
                                related_name='official_letters', verbose_name='회사')  # 회사
    document_number = models.CharField('문서번호', max_length=20, unique=True,
                                       db_index=True, editable=False)  # 문서번호 (자동 생성)
    title = models.CharField('제목', max_length=255, db_index=True)  # 제목
    recipient_name = models.CharField('수신처명', max_length=100)  # 수신처 정보
    recipient_address = models.CharField('수신처 주소', max_length=255, blank=True, default='')
    recipient_contact = models.CharField('수신처 연락처', max_length=50, blank=True, default='')
    recipient_reference = models.CharField('참조', max_length=100, blank=True, default='',
                                           help_text='참조인 또는 부서')
    sender_name = models.CharField('발신자명', max_length=50)  # 발신자 정보
    sender_position = models.CharField('발신자 직위', max_length=50, blank=True, default='')
    sender_department = models.CharField('발신 부서', max_length=50, blank=True, default='')
    content = models.TextField('내용')  # 내용
    issue_date = models.DateField('발신일자')  # 발신일자
    pdf_file = models.FileField('PDF 파일', upload_to=get_letter_pdf_path,
                                null=True, blank=True)  # 생성된 PDF
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

    def get_pdf_filename(self):
        """PDF 다운로드용 파일명 생성"""
        safe_title = self.title[:30].replace(' ', '_').replace('/', '_')
        return f'{self.document_number}_{safe_title}.pdf'


file_cleanup_signals(OfficialLetter, file_field_names=['pdf_file'])  # PDF 파일 자동 삭제
