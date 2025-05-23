import os
from datetime import datetime

import magic
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from work.models.project import IssueProject, Member


class CodeDocsCategory(models.Model):
    name = models.CharField('이름', max_length=20, db_index=True)
    active = models.BooleanField('사용중', default=True)
    default = models.BooleanField('기본값', default=False)
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '13. 문서 범주'
        verbose_name_plural = '13. 문서 범주'


class News(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트')
    title = models.CharField('제목', max_length=255, db_index=True)
    summary = models.CharField('요약', max_length=255, blank=True, default='')
    description = models.TextField('설명', blank=True, default='')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='저자')
    created = models.DateTimeField('등록일', auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '15. 공지'
        verbose_name_plural = '15. 공지'


def get_news_file_path(instance, filename):
    today = datetime.today()
    date_path = today.strftime('%Y/%m/%d')
    return os.path.join('work', f'{instance.issue.project.slug}/news/{date_path}/', filename)


class NewsFile(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, default=None, verbose_name='공지', related_name='files')
    file = models.FileField(upload_to=get_news_file_path, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=100, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    description = models.CharField('부가설명', max_length=255, blank=True, default='')
    created = models.DateTimeField('등록일', auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
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


@receiver(pre_delete, sender=NewsFile)
def delete_file_on_delete(sender, instance, **kwargs):
    # Check if the file exists before attempting to delete it
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


class Search(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name='내 검색어')
    offset = models.BigIntegerField('오프셋', default=False)  # 응답에서 이 결과 수를 건너뜁니다.(선택사항)
    limit = models.PositiveIntegerField('응답결과 수', blank=True, null=True)  # 응답 결과 수 (선택사항)
    q = models.CharField('검색어', max_length=255, blank=True, default='', help_text='공백으로 구분된 여러 값을 지정할 수 있습니다.')
    scope = models.CharField('검색 범위 조건', max_length=1, choices=(('0', '모두'), ('1', '프로젝트 내'), ('2', '하위 프로젝트 포함')))
    all_words = models.BooleanField('모든 검색어가 일치하는지 여부', default=False)
    title_only = models.BooleanField('제목 검색', default=False)
    issue = models.BooleanField('업무 포함 여부', default=False)
    news = models.BooleanField('공지 포함 여부', default=False)
    document = models.BooleanField('문서 포함 여부', default=False)
    changeset = models.BooleanField('변경 집합 포함 여부', default=False)
    wiki = models.BooleanField('위키 포함 여부', default=False)
    forum = models.BooleanField('게시판 포함 여부', default=False)
    project = models.BooleanField('프로젝트 포함 여부', default=False)
    open_issue = models.BooleanField('미해결 업무 검색', default=False)
    attachment = models.CharField('설명 및 첨부파일 검색', max_length=1,
                                  choices=(('0', '설명 및 첨부파일 검색'), ('1', '설명에서만 검색'), ('2', '첨부파일에서만 검색')), default='0')

    def __str__(self):
        return f'#{self.pk}. {self.member.user} - 검색조건'
