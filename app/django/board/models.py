import os
import magic

from django.db import models
from datetime import datetime, timedelta
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_delete


class Group(models.Model):
    name = models.CharField('이름', max_length=255)
    manager = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name='관리자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '01. 그룹 관리'
        verbose_name_plural = '01. 그룹 관리'


class Board(models.Model):
    group = models.ForeignKey(Group, on_delete=models.PROTECT, verbose_name='그룹')
    issue_project = models.ForeignKey('work.IssueProject', on_delete=models.SET_NULL,
                                      null=True, blank=True, verbose_name='업무 프로젝트')
    name = models.CharField('이름', max_length=255)
    is_notice = models.BooleanField('공지 게시판', default=False)
    order = models.PositiveSmallIntegerField('정렬 순서', default=0)
    search_able = models.BooleanField('검색사용', default=True)
    manager = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name='관리자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '02. 게시판 관리'
        verbose_name_plural = '02. 게시판 관리'


class PostCategory(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, verbose_name='게시판')
    color = models.CharField('색상', max_length=21, null=True, blank=True)
    name = models.CharField('이름', max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='상위 카테고리')
    order = models.PositiveSmallIntegerField('정렬 순서', default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '03. 카테고리 관리'
        verbose_name_plural = '03. 카테고리 관리'


class Post(models.Model):
    board = models.ForeignKey(Board, on_delete=models.PROTECT, verbose_name='게시판')
    category = models.ForeignKey(PostCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='카테고리')
    title = models.CharField('제목', max_length=255)
    content = models.TextField('내용', blank=True, default='')
    hit = models.PositiveIntegerField('조회수', default=0)
    like = models.PositiveIntegerField('좋아요', default=0)
    blame = models.PositiveSmallIntegerField('신고', default=0)
    ip = models.GenericIPAddressField('아이피', null=True, blank=True)
    device = models.CharField('등록기기', max_length=255, blank=True, default='')
    is_secret = models.BooleanField('비밀글', default=False)
    password = models.CharField('패스워드', max_length=255, blank=True, default='')
    is_hide_comment = models.BooleanField('댓글숨기기', default=False)
    is_notice = models.BooleanField('공지', default=False)
    is_blind = models.BooleanField('숨김', default=False)
    deleted = models.DateTimeField('휴지통', null=True, blank=True, default=None)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_new(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M')
        new_period = self.created + timedelta(days=3)
        return today < new_period.strftime('%Y-%m-%d %H:%M')

    class Meta:
        ordering = ['-created']
        verbose_name = '04. 게시물 관리'
        verbose_name_plural = '04. 게시물 관리'

    def delete(self, using=None, keep_parents=False):
        self.deleted = datetime.now()
        self.save(update_fields=['deleted'])

    def restore(self):
        self.deleted = None
        self.save(update_fields=['deleted'])


class PostLink(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default=None, verbose_name='게시물', related_name='links')
    link = models.URLField(max_length=500, verbose_name='링크')
    hit = models.PositiveIntegerField('클릭수', default=0)

    def __str__(self):
        return self.link


class PostFile(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default=None, verbose_name='게시물', related_name='files')
    file = models.FileField(upload_to='post/file/%Y/%m/%d/', verbose_name='파일')
    file_name = models.CharField('파일명', max_length=100, blank=True)
    file_type = models.CharField('타입', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    hit = models.PositiveIntegerField('다운로드수', default=0)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name.split('/')[-1]
            mime = magic.Magic(mime=True)
            self.file_type = mime.from_buffer(self.file.read())
            self.file_size = self.file.size
        super().save(*args, **kwargs)


@receiver(pre_delete, sender=PostFile)
def delete_file_on_delete(sender, instance, **kwargs):
    # Check if the file exists before attempting to delete it
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default=None, verbose_name='게시물', related_name='images')
    image = models.ImageField(upload_to='post/img/%Y/%m/%d/', verbose_name='이미지')
    image_name = models.CharField('파일명', max_length=100, blank=True)
    image_type = models.CharField('타입', max_length=100, blank=True)
    image_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        if self.image:
            self.image_name = self.image.name.split('/')[-1]
            mime = magic.Magic(mime=True)
            self.image_type = mime.from_buffer(self.image.read())
            self.image_size = self.image.size
        super().save(*args, **kwargs)


@receiver(pre_delete, sender=PostImage)
def delete_file_on_delete(sender, instance, **kwargs):
    # Check if the file exists before attempting to delete it
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='게시물', related_name='comments')
    content = models.TextField('내용')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    like = models.PositiveIntegerField('좋아요', default=0)
    blame = models.PositiveSmallIntegerField('신고', default=0)
    ip = models.GenericIPAddressField('아이피', null=True, blank=True)
    device = models.CharField('등록기기', max_length=255, blank=True)
    secret = models.BooleanField('비밀글', default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='등록자')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.post} -> {self.content}"

    class Meta:
        ordering = ['-created']


class Tag(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, verbose_name='게시판')
    post = models.ManyToManyField(Post, blank=True, verbose_name='게시물')
    name = models.CharField('태그', max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '05. 태그 관리'
        verbose_name_plural = '05. 태그 관리'
