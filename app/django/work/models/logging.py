from django.conf import settings
from django.db import models

from work.models.issue import IssueComment, TimeEntry, Issue
from work.models.project import IssueProject


class ActivityLogEntry(models.Model):
    SORT_CHOICES = (('1', '업무'), ('2', '댓글'), ('3', '변경묶음'), ('4', '공지'), ('5', '문서'),
                    ('6', '파일'), ('7', '위키편집'), ('8', '글'), ('9', '작업시간'))
    sort = models.CharField('구분', max_length=1, choices=SORT_CHOICES, default='1')
    project = models.ForeignKey(IssueProject, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='프로젝트')
    issue = models.ForeignKey(Issue, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='업무')
    comment = models.ForeignKey(IssueComment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='댓글')
    status_log = models.CharField('상태 기록', max_length=30, blank=True, default='')
    # change_sets = models.TextField('변경 묶음', blank=True, default='')
    # news = models.TextField('공지', blank=True, default='')
    # document = models.TextField('문서', blank=True, default='')
    # file = models.TextField('파일', blank=True, default='')
    # wiki = models.TextField('위키 편집', blank=True, default='')
    # message = models.TextField('글', blank=True, default='')
    spent_time = models.ForeignKey(TimeEntry, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='소요시간')
    act_date = models.DateField('로그 일자', auto_now_add=True)
    timestamp = models.DateTimeField('로그 시간', auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='작성자')

    def __str__(self):
        return f"{self.user.__str__()} - {self.timestamp}"

    class Meta:
        ordering = ('-id',)
        verbose_name = '16. 작업 내역'
        verbose_name_plural = '16. 작업 내역'


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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='작성자')

    def __str__(self):
        return f"{self.action} - {self.timestamp}"

    class Meta:
        verbose_name = '17. 업무 로그'
        verbose_name_plural = '17. 업무 로그'
