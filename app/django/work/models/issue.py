import magic
from django.conf import settings
from django.db import models

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_work_file_path
from work.models.project import IssueProject


class IssueManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'project', 'tracker', 'status', 'priority', 'category',
            'fixed_version', 'assigned_to', 'parent', 'creator', 'updater', 'meeting'
        )


class ExpectedDuration(models.TextChoices):
    SAME_DAY = '0', '당일처리'
    DAY_1 = '1', '익일처리'
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

    class Meta:
        ordering = ('-id',)
        verbose_name = '09. 업무(작업)'
        verbose_name_plural = '09. 업무(작업)'


class IssueRelation(models.Model):
    source = models.ForeignKey(Issue, on_delete=models.CASCADE, verbose_name='선행 업무', related_name='outgoing_relations')
    target = models.OneToOneField(Issue, on_delete=models.CASCADE, verbose_name='후속 업무',
                                  related_name='incoming_relation')
    delay = models.PositiveSmallIntegerField('대기일수', null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True, blank=True, verbose_name='작성자')

    def __str__(self):
        return f'#{self.source.pk} ({self.source.subject}) → #{self.target.pk} ({self.target.subject})'


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
        if self.file:
            self.file_name = self.file.name.split('/')[-1]
            mime = magic.Magic(mime=True)
            self.file_type = mime.from_buffer(self.file.read())
            self.file_size = self.file.size
        super().save(*args, **kwargs)


file_cleanup_signals(IssueFile)  # 파일인스턴스 직접 삭제시


class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, verbose_name='업무', related_name='comments')
    content = models.TextField('내용')
    is_private = models.BooleanField('비공개 댓글', default=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='작성자')

    def __str__(self):
        return self.content


class TrackerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('default_status')


class Tracker(models.Model):
    name = models.CharField('이름', max_length=100, db_index=True)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    is_in_roadmap = models.BooleanField('로드맵에 표시', default=True)
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


class Workflow(models.Model):
    role = models.ForeignKey('work.Role', on_delete=models.CASCADE, verbose_name='역할')
    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE, verbose_name='업무 유형')
    old_status = models.OneToOneField(IssueStatus, on_delete=models.CASCADE, verbose_name='업무 상태',
                                      related_name='each_status')
    new_statuses = models.ManyToManyField(IssueStatus, verbose_name='허용 업무 상태', blank=True)

    def __str__(self):
        return f'{self.role} - {self.tracker}'

    class Meta:
        verbose_name = '13. 업무 흐름'
        verbose_name_plural = '13. 업무 흐름'


class IssueCategory(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트', related_name='categories')
    name = models.CharField('범주', max_length=100, db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='담당자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-project', 'id',)
        verbose_name = '14. 업무 범주'
        verbose_name_plural = '14. 업무 범주'
