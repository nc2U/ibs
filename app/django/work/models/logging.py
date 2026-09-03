from django.conf import settings
from django.db import models

from work.models import News
from work.models.issue import IssueComment, Issue
from work.models.project import IssueProject


class ActivityLogEntryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('project', 'creator')


class ActivityLogEntry(models.Model):
    SORT_CHOICES = (('1', '업무'), ('2', '댓글'), ('3', '회의'), ('4', '공지'), ('5', '문서'), ('6', '글'))
    sort = models.CharField('구분', max_length=1, choices=SORT_CHOICES, default='1')
    project = models.ForeignKey(IssueProject, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='프로젝트')

    # 단일 식별자 구조 (물리적/논리적 FK 없이 무결성 충돌 0% 보장)
    target_id = models.PositiveIntegerField('대상 객체 PK', null=True, blank=True)
    parent_id = models.PositiveIntegerField('상위 객체 PK(업무/포럼 등)', null=True, blank=True)

    # 스냅샷 필드 (JOIN 없는 초고속 렌더링 및 원본 삭제 시 영구 보존)
    title = models.CharField('제목 스냅샷', max_length=255, blank=True, default='')
    summary = models.CharField('내용/의제 요약 스냅샷', max_length=255, blank=True, default='')

    status_log = models.CharField('상태 기록', max_length=30, blank=True, default='')
    act_date = models.DateField('로그 일자', auto_now_add=True)
    timestamp = models.DateTimeField('로그 시간', auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='작성자')

    objects = ActivityLogEntryManager()

    def __str__(self):
        return f"{self.creator.__str__()} - {self.timestamp}"

    class Meta:
        ordering = ('-id',)
        verbose_name = '15. 실행 기록'
        verbose_name_plural = '15. 실행 기록'
        indexes = [models.Index(fields=['timestamp', 'project'])]


class SequentialIntegerField(models.IntegerField):
    def pre_save(self, model_instance, add):
        if add:
            # Get the maximum value of the sequential field for the current issue
            max_value = \
                model_instance.__class__.objects.filter(issue=model_instance.issue).aggregate(models.Max(self.attname))[
                    f'{self.attname}__max'
                ]
            # Increment the maximum value by 1 if it's not None, else start from 1
            value = (max_value or 0) + 1
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super().pre_save(model_instance, add)


class IssueLogEntry(models.Model):
    log_id = SequentialIntegerField()
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, verbose_name='업무')
    ACTION_CHOICES = (('Created', '등록'), ('Updated', '수정'), ('Comment', '댓글'))
    action = models.CharField('이벤트', max_length=7, choices=ACTION_CHOICES, default='Created')
    comment = models.ForeignKey(IssueComment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='댓글')
    details = models.TextField('설명', blank=True, default='')
    diff = models.TextField('차이점', blank=True, default='')
    timestamp = models.DateTimeField('로그 시간', auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='작성자')

    def __str__(self):
        return f"{self.action} - {self.timestamp}"

    class Meta:
        verbose_name = '16. 업무 로그'
        verbose_name_plural = '16. 업무 로그'
