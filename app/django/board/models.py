import os
from datetime import datetime, timedelta

import magic
from django.conf import settings
from django.db import models
from django.utils import timezone

from _utils.file_cleanup import file_cleanup_signals, related_file_cleanup
from _utils.file_upload import get_board_file_path, get_board_image_path


class Board(models.Model):
    project = models.ForeignKey('work.IssueProject', on_delete=models.CASCADE,
                                verbose_name='업무 프로젝트', related_name='forums')
    name = models.CharField('이름', max_length=255, db_index=True)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    search_able = models.BooleanField('검색 사용', default=True)
    manager = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name='관리자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '01. 게시판 관리'
        verbose_name_plural = '01. 게시판 관리'


class PostCategory(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, verbose_name='게시판')
    color = models.CharField('색상', max_length=21, null=True, blank=True)
    name = models.CharField('이름', max_length=100, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='상위 카테고리')
    order = models.PositiveSmallIntegerField('정렬 순서', default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '02. 카테고리 관리'
        verbose_name_plural = '02. 카테고리 관리'


class Post(models.Model):
    board = models.ForeignKey(Board, on_delete=models.PROTECT, verbose_name='게시판')
    category = models.ForeignKey(PostCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='카테고리')
    title = models.CharField('제목', max_length=255, db_index=True)
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
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
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
        verbose_name = '03. 게시물 관리'
        verbose_name_plural = '03. 게시물 관리'

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


def get_post_file_path(instance, filename):
    return get_board_file_path(instance, filename)


class PostFile(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default=None, verbose_name='게시물', related_name='files')
    file = models.FileField(upload_to=get_post_file_path, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    hit = models.PositiveIntegerField('다운로드수', default=0)
    created = models.DateTimeField(auto_now_add=True)

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


file_cleanup_signals(PostFile)  # 파일인스턴스 직접 삭제시
related_file_cleanup(Post, related_name='files', file_field_name='file')  # 연관 모델 삭제 시


def get_post_img_path(instance, filename):
    return get_board_image_path(instance, filename)


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default=None, verbose_name='게시물', related_name='images')
    image = models.ImageField(upload_to=get_post_img_path, verbose_name='이미지')
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


file_cleanup_signals(PostImage)  # 파일인스턴스 직접 삭제시
related_file_cleanup(Post, related_name='images', file_field_name='image')  # 연관 모델 삭제 시


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='게시물', related_name='comments')
    content = models.TextField('내용')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    like = models.PositiveIntegerField('좋아요', default=0)
    blame = models.PositiveSmallIntegerField('신고', default=0)
    ip = models.GenericIPAddressField('아이피', null=True, blank=True)
    device = models.CharField('등록기기', max_length=255, blank=True)
    secret = models.BooleanField('비밀글', default=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='등록자')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.post} -> {self.content}"

    class Meta:
        ordering = ['-created']


class Tag(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, verbose_name='게시판')
    post = models.ManyToManyField(Post, blank=True, verbose_name='게시물')
    name = models.CharField('태그', max_length=100, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '04. 태그 관리'
        verbose_name_plural = '04. 태그 관리'
