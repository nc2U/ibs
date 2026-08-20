import hashlib
import json

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_approval_file_path, populate_file_meta
from .document_type import DocumentType, RouteTemplate


class ApprovalDocument(models.Model):
    """결재 문서 (기안서)"""

    STATUS_DRAFT = 'draft'
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_DRAFT, '임시저장'),
        (STATUS_PENDING, '결재 진행 중'),
        (STATUS_APPROVED, '최종 승인'),
        (STATUS_REJECTED, '반려'),
        (STATUS_CANCELLED, '취소'),
    )

    doc_type = models.ForeignKey(
        DocumentType, on_delete=models.PROTECT,
        related_name='documents', verbose_name='문서 유형'
    )
    doc_number = models.CharField(
        '문서 번호', max_length=30, unique=True, blank=True, null=True, default=None,
        help_text='승인 후 자동 채번 (예: BIZ-2026-0001)'
    )
    title = models.CharField('제목', max_length=255)
    content = models.JSONField(
        '결재 내용',
        default=dict,
        help_text='문서 유형의 form_template_key에 따른 결재 양식 데이터'
    )
    attachment = models.FileField(
        '대표 첨부파일', upload_to=get_approval_file_path, storage=default_storage, blank=True, null=True
    )
    drafter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='drafted_documents', verbose_name='기안자'
    )
    drafter_assignment = models.ForeignKey(
        'company.StaffAssignment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='drafted_documents',
        verbose_name='기안 보직',
        help_text='기안 당시 선택한 소속 부서 및 직책'
    )
    # 워크스페이스 / 프로젝트 연결 (선택)
    workspace = models.ForeignKey(
        'work.IssueProject', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approval_documents',
        verbose_name='워크스페이스'
    )
    # 참조자 (공람자) 목록
    observers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        related_name='observed_approval_documents',
        verbose_name='참조자 목록',
        help_text='결재 진행 및 완료 시 열람 권한 및 알림을 수신하는 참조자'
    )
    status = models.CharField(
        '결재 상태', max_length=15,
        choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    current_step = models.PositiveSmallIntegerField('현재 결재 단계', default=0)
    content_hash = models.CharField(
        '문서 해시', max_length=64, blank=True,
        help_text='상신 시 SHA-256으로 생성. 위변조 검증용.'
    )
    pdf_file = models.FileField(
        'PDF 보관 파일', upload_to='approval/pdf/%Y/%m/', blank=True, null=True
    )
    created_at = models.DateTimeField('기안일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)
    submitted_at = models.DateTimeField('상신일시', null=True, blank=True)
    completed_at = models.DateTimeField('완료일시', null=True, blank=True)

    def compute_hash(self):
        """문서 내용의 SHA-256 해시 생성 (위변조 방지)"""
        payload = json.dumps({
            'doc_type': self.doc_type_id,
            'title': self.title,
            'content': self.content,
        }, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def generate_doc_number(self):
        """최종 승인 시 문서 번호 자동 채번 (예: BIZ-2026-0001)"""
        code = self.doc_type.code
        year = self.completed_at.year if self.completed_at else self.created_at.year
        count = ApprovalDocument.objects.filter(
            doc_type=self.doc_type,
            status=self.STATUS_APPROVED,
            completed_at__year=year,
        ).count()
        return f'{code}-{year}-{str(count).zfill(4)}'

    def __str__(self):
        return f'[{self.get_status_display()}] {self.title} ({self.drafter})'

    class Meta:
        ordering = ['-created_at']
        verbose_name = '03. 결재 문서'
        verbose_name_plural = '03. 결재 문서 목록'


class ApprovalStep(models.Model):
    """결재 단계 인스턴스 (상신 시 RouteTemplate → 복사 생성)"""

    CONDITION_AND = 'AND'
    CONDITION_OR = 'OR'
    CONDITION_CHOICES = (
        (CONDITION_AND, '전원 승인 (AND)'),
        (CONDITION_OR, '1인 승인 (OR)'),
    )

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_SKIPPED = 'skipped'
    STATUS_CHOICES = (
        (STATUS_PENDING, '대기'),
        (STATUS_APPROVED, '승인'),
        (STATUS_REJECTED, '반려'),
        (STATUS_SKIPPED, '건너뜀'),
    )

    document = models.ForeignKey(
        ApprovalDocument, on_delete=models.CASCADE,
        related_name='steps', verbose_name='결재 문서'
    )
    step_order = models.PositiveSmallIntegerField('결재 순서')
    role_label = models.CharField('결재 단계명', max_length=50)
    approvers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='approval_steps',
        verbose_name='결재자 목록'
    )
    condition = models.CharField(
        '결재 조건', max_length=3,
        choices=CONDITION_CHOICES, default=CONDITION_AND
    )
    status = models.CharField(
        '단계 상태', max_length=10,
        choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    def is_completed(self):
        """이 단계의 결재가 완료되었는지 확인 (AND/OR 조건 처리)"""
        actions = self.actions.filter(action__in=[
            ApprovalAction.ACTION_APPROVED, ApprovalAction.ACTION_REJECTED
        ])
        rejected = actions.filter(action=ApprovalAction.ACTION_REJECTED).exists()
        if rejected:
            return True, False  # (완료여부, 승인여부)

        approved_ids = set(actions.filter(action=ApprovalAction.ACTION_APPROVED)
                           .values_list('approver_id', flat=True))
        approver_ids = set(self.approvers.values_list('id', flat=True))

        if self.condition == self.CONDITION_OR:
            completed = bool(approved_ids)
        else:  # AND
            completed = approver_ids == approved_ids

        return completed, completed

    def __str__(self):
        return f'{self.document.title} - Step {self.step_order}: {self.role_label}'

    class Meta:
        ordering = ['document', 'step_order']
        unique_together = ('document', 'step_order')
        verbose_name = '04. 결재 단계'
        verbose_name_plural = '04. 결재 단계 목록'


class ApprovalAction(models.Model):
    """결재자 개별 행동 기록 (승인/반려/의견)"""

    ACTION_APPROVED = 'approved'
    ACTION_REJECTED = 'rejected'
    ACTION_COMMENTED = 'commented'
    ACTION_CHOICES = (
        (ACTION_APPROVED, '승인'),
        (ACTION_REJECTED, '반려'),
        (ACTION_COMMENTED, '의견'),
    )

    step = models.ForeignKey(
        ApprovalStep, on_delete=models.CASCADE,
        related_name='actions', verbose_name='결재 단계'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='approval_actions', verbose_name='결재자'
    )
    action = models.CharField(
        '결재 행동', max_length=15,
        choices=ACTION_CHOICES
    )
    comment = models.TextField('의견/반려 사유', blank=True)
    content_hash = models.CharField(
        '문서 해시', max_length=64, blank=True,
        help_text='결재 시점의 문서 SHA-256 해시값 (위변조 검증용)'
    )
    acted_at = models.DateTimeField('결재일시', auto_now_add=True)

    def __str__(self):
        return f'{self.approver} → {self.get_action_display()} ({self.step})'

    class Meta:
        ordering = ['acted_at']
        verbose_name = '05. 결재 행동 이력'
        verbose_name_plural = '05. 결재 행동 이력 목록'


class ApprovalAttachment(models.Model):
    """결재 문서 첨부파일 (복수 파일 지원)"""

    document = models.ForeignKey(
        ApprovalDocument, on_delete=models.CASCADE,
        related_name='attachments', verbose_name='결재 문서'
    )
    file = models.FileField(
        '첨부파일', upload_to=get_approval_file_path, storage=default_storage
    )
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('파일 타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('파일 크기', blank=True, null=True)
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='등록자'
    )

    def __str__(self):
        return self.file_name or (self.file.name if self.file else '첨부파일')

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            populate_file_meta(self)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['id']
        verbose_name = '06. 결재 첨부파일'
        verbose_name_plural = '06. 결재 첨부파일 목록'


file_cleanup_signals(ApprovalDocument, 'attachment')
file_cleanup_signals(ApprovalAttachment, 'file')
