from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.postgres.indexes import GinIndex

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_work_file_path, populate_file_meta
from work.models.project import IssueProject


class IssueManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'project', 'tracker', 'status', 'priority', 'category',
            'fixed_version', 'assigned_to', 'parent', 'creator', 'updater', 'meeting'
        )


class ExpectedDuration(models.TextChoices):
    SAME_DAY = '1', '당일 처리'
    DAY_1 = '2', '2일 이내'
    DAY_3 = '3', '3일 이내'
    DAY_5 = '5', '5일 이내'
    DAY_10 = '10', '10일 이내'
    DAY_30 = '30', '30일 이내'
    MONTH_3 = '90', '3개월 이내'
    MONTH_6 = '180', '6개월 이내'
    YEAR_1 = '365', '1년 이내'
    OVER_YEAR = '366', '1년 이상'


class Issue(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.PROTECT, verbose_name='프로젝트')
    tracker = models.ForeignKey('Tracker', on_delete=models.PROTECT, verbose_name='유형')
    status = models.ForeignKey('IssueStatus', on_delete=models.PROTECT, verbose_name='상태')
    priority = models.ForeignKey('CodeIssuePriority', on_delete=models.PROTECT, verbose_name='우선순위')
    subject = models.CharField(max_length=100, verbose_name='제목', db_index=True)
    description = models.TextField(verbose_name='설명', blank=True, default='')
    category = models.ForeignKey('IssueCategory', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='범주')
    fixed_version = models.ForeignKey('work.Version', on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name='목표 단계', related_name='issues')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='담당자', related_name='assignees')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='상위 업무')
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name='업무 관람자',
                                      related_name='watchers')
    meeting = models.ForeignKey('Meeting', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='관련 회의', related_name='issues')
    is_private = models.BooleanField('비공개', default=False)
    expected_duration = models.CharField('예상 처리기간', max_length=3, choices=ExpectedDuration, null=True, blank=True,
                                         default=ExpectedDuration.SAME_DAY, help_text='시작 일자 기준 예상 처리기간')
    start_date = models.DateField('시작 일자')
    due_date = models.DateField('완료 기한', null=True, blank=True)
    done_ratio = models.PositiveSmallIntegerField('진척도', default=0)
    closed = models.DateTimeField('완료', null=True, blank=True, help_text='상태가 완료로 입력된 시간. 한 번 완료하면 다시 진행으로 변경해도 남아있음.')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자',
                                related_name='creator', null=True, blank=True)
    updater = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='수정자',
                                related_name='updater', null=True, blank=True)
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)

    objects = IssueManager()

    def __str__(self):
        return f'#{self.pk}-{self.subject}'

    def clean(self):
        super().clean()
        errors = {}
        # 1. 날짜 역전 방어
        if self.start_date and self.due_date and self.start_date > self.due_date:
            errors['due_date'] = '완료 기한은 시작 일자보다 빠를 수 없습니다.'

        # 2. 진척도 범위 제약 (0 ~ 100)
        if self.done_ratio is not None and (self.done_ratio < 0 or self.done_ratio > 100):
            errors['done_ratio'] = '진척도는 0에서 100 사이의 값이어야 합니다.'

        # 3. 상위 업무(parent) 무결성
        if self.parent:
            if self.pk and self.parent_id == self.pk:
                errors['parent'] = '자기 자신을 상위 업무로 지정할 수 없습니다.'
            elif self.project_id and self.parent.project_id and self.parent.project_id != self.project_id:
                errors['parent'] = '상위 업무는 동일한 워크스페이스 내의 업무여야 합니다.'

        # 4. 범주(category) 프로젝트 일치 여부
        if self.category and self.project_id:
            if self.category.project_id and self.category.project_id != self.project_id:
                errors['category'] = '지정된 범주는 현재 워크스페이스에 속한 범주가 아닙니다.'

        # 5. 목표 단계(fixed_version) 프로젝트 접근 가능 여부
        if self.fixed_version and self.project:
            from work.models.project import Version
            accessible_versions = Version.objects.accessible_from(self.project)
            if not accessible_versions.filter(pk=self.fixed_version_id).exists():
                errors['fixed_version'] = '지정된 목표 단계는 현재 워크스페이스에서 사용할 수 없는 단계입니다.'

        # 6. 회의(meeting) 프로젝트 일치 여부
        if self.meeting and self.project_id:
            if self.meeting.project_id != self.project_id:
                errors['meeting'] = '지정된 회의는 현재 워크스페이스에 속한 회의가 아닙니다.'

        if errors:
            raise ValidationError(errors)

    class Meta:
        ordering = ('-updated', '-created')
        verbose_name = '09. 업무(작업)'
        verbose_name_plural = '09. 업무(작업)'
        indexes = [
            GinIndex(fields=['subject'], opclasses=['gin_trgm_ops'], name='work_issue_subject_trgm'),
            GinIndex(fields=['description'], opclasses=['gin_trgm_ops'], name='work_issue_desc_trgm'),
        ]


class IssueFile(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, default=None, verbose_name='업무', related_name='files')
    file = models.FileField(upload_to=get_work_file_path, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=100, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    description = models.CharField('부가설명', max_length=255, blank=True, default='')
    created = models.DateTimeField('등록일', auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='작성자')

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        populate_file_meta(self)
        super().save(*args, **kwargs)


file_cleanup_signals(IssueFile)  # 파일인스턴스 직접 삭제시


class IssueLink(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, default=None, verbose_name='업무', related_name='links')
    link = models.URLField('링크 URL', max_length=500)
    name = models.CharField('링크 이름(파일명)', max_length=255)
    hit = models.PositiveIntegerField('클릭수', default=0)
    created = models.DateTimeField('등록일', auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='작성자')

    def __str__(self):
        return self.name


class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, verbose_name='업무', related_name='comments')
    content = models.TextField('내용')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_private = models.BooleanField('비공개 댓글', default=False)
    is_blocked = models.BooleanField('관리자 잠금', default=False)
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='작성자')

    def __str__(self):
        return self.content

    class Meta:
        indexes = [
            GinIndex(fields=['content'], opclasses=['gin_trgm_ops'], name='work_comment_content_trgm'),
        ]


class IssueRelation(models.Model):
    source = models.ForeignKey(Issue, on_delete=models.CASCADE, verbose_name='선행 업무(이 업무를 우선 진행)',
                               related_name='outgoing_relations')
    target = models.OneToOneField(Issue, on_delete=models.CASCADE, verbose_name='후속 업무(이 업무를 다음에 진행)',
                                  related_name='incoming_relation')
    delay = models.PositiveSmallIntegerField('대기일수', null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True, blank=True, verbose_name='작성자')

    def __str__(self):
        return f'#{self.source.pk} ({self.source.subject}) → #{self.target.pk} ({self.target.subject})'

    def clean(self):
        super().clean()
        if self.source_id and self.target_id:
            if self.source_id == self.target_id:
                raise ValidationError({'target': '선행 업무와 후속 업무는 동일한 업무일 수 없습니다.'})
            reverse_relation = IssueRelation.objects.filter(
                source_id=self.target_id, target_id=self.source_id
            )
            if self.pk:
                reverse_relation = reverse_relation.exclude(pk=self.pk)
            if reverse_relation.exists():
                raise ValidationError({'target': '해당 업무와 상호 순환 참조되는 관계가 이미 존재합니다.'})


class TrackerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('default_status')


class Tracker(models.Model):
    name = models.CharField('이름', max_length=100, db_index=True)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    is_in_roadmap = models.BooleanField('로드맵에 표시', default=True)
    is_for_dev_project = models.BooleanField(
        '부동산개발 프로젝트 기본 적용',
        default=False,
        help_text='체크 시 신규 부동산 개발 프로젝트(type=2) 생성 시 trackers에 기본 포함됩니다.'
    )
    default_status = models.ForeignKey('IssueStatus', on_delete=models.PROTECT, verbose_name='초기 상태')
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    objects = TrackerManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id')
        verbose_name = '10. 업무 유형'
        verbose_name_plural = '10. 업무 유형'


class IssueStatus(models.Model):
    name = models.CharField('이름', max_length=20, db_index=True)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    closed = models.BooleanField('완료 상태', default=False)
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '11. 업무 상태'
        verbose_name_plural = '11. 업무 상태'


class CodeIssuePriority(models.Model):
    name = models.CharField('이름', max_length=20, db_index=True)
    active = models.BooleanField('사용중', default=True)
    default = models.BooleanField('기본값', default=False)
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '12. 업무 우선 순위'
        verbose_name_plural = '12. 업무 우선 순위'


class IssueCategory(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트', related_name='categories')
    name = models.CharField('범주', max_length=100, db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='담당자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-project', 'id',)
        verbose_name = '13. 업무 범주'
        verbose_name_plural = '13. 업무 범주'


class Workflow(models.Model):
    role = models.ForeignKey('work.Role', on_delete=models.CASCADE, verbose_name='역할')
    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE, verbose_name='업무 유형')
    old_status = models.OneToOneField(IssueStatus, on_delete=models.CASCADE, verbose_name='업무 상태',
                                      related_name='each_status')
    new_statuses = models.ManyToManyField(IssueStatus, verbose_name='허용 업무 상태', blank=True)

    def __str__(self):
        return f'{self.role} - {self.tracker}'

    class Meta:
        verbose_name = '14. 업무 흐름'
        verbose_name_plural = '14. 업무 흐름'
