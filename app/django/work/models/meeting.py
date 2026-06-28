import magic
from django.conf import settings
from django.db import models

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_meeting_file_path
from work.models.project import IssueProject


class MeetingCategory(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트',
                                related_name='meeting_categories')
    name = models.CharField('카테고리명', max_length=100)
    color = models.CharField('색상', max_length=20, blank=True, default='')
    order = models.PositiveSmallIntegerField('정렬', default=1)

    class Meta:
        ordering = ('order', 'id')
        verbose_name = '07. 회의 카테고리'
        verbose_name_plural = '07. 회의 카테고리'

    def __str__(self):
        return self.name


class Meeting(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트',
                                related_name='meetings')
    title = models.CharField('회의 제목', max_length=255)
    category = models.ForeignKey(MeetingCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='카테고리',
                                 related_name='meetings')
    MEETING_STATUS_CHOICES = (('1', '준비'), ('2', '종료'), ('3', '취소'))
    status = models.CharField('회의 상태', max_length=1, choices=MEETING_STATUS_CHOICES, default='1')
    is_confirmed = models.BooleanField('확정 여부', default=False)
    agenda = models.TextField('회의 의제', blank=True, default='',
                              help_text='회의에서 논의할 주요 의제 (사전 공유용)')
    content = models.TextField('회의 내용', blank=True, default='')
    decisions = models.TextField('주요 결정 사항', blank=True, default='',
                                 help_text='회의를 통해 확정된 합의 내용')
    action_items = models.TextField('후속 조치 사항', blank=True, default='',
                                    help_text='누가, 언제까지, 무엇을 할 것인가?')
    meeting_date = models.DateTimeField('회의 일시', null=True, blank=True)
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='참석자', related_name='meetings_attended',
                                       blank=True)
    other_attendees = models.CharField('기타 참석자', max_length=255, blank=True, default='',
                                       help_text='사용자(멤버)가 아닌 외부 참석자 명단')

    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자',
                                related_name='created_meetings')
    updater = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='수정자', related_name='updated_meetings')

    class Meta:
        ordering = ('-meeting_date', '-created')
        verbose_name = '08. 회의록'
        verbose_name_plural = '08. 회의록'

    def __str__(self):
        return self.title


class MeetingFile(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, default=None, verbose_name='회의록',
                                related_name='files')
    file = models.FileField(upload_to=get_meeting_file_path, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=100, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    description = models.CharField('부가설명', max_length=255, blank=True, default='')
    created = models.DateTimeField('등록일', auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='작성자')

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name.split('/')[-1]
            mime = magic.Magic(mime=True)
            self.file_type = mime.from_buffer(self.file.read())
            self.file_size = self.file.size
        super().save(*args, **kwargs)


file_cleanup_signals(MeetingFile)  # 파일인스턴스 직접 삭제시
