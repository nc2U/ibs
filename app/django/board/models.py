import os
from datetime import datetime, timedelta

import magic
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver


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
    project = models.ForeignKey('work.IssueProject', on_delete=models.CASCADE,
                                verbose_name='업무 프로젝트', related_name='forums')
    BOARD_TYPES = (('notice', '공지 게시판'), ('general', '일반 게시판'))
    board_type = models.CharField(max_length=10, choices=BOARD_TYPES, default='general', verbose_name='게시판 유형')
    name = models.CharField('이름', max_length=255, db_index=True)
    order = models.PositiveSmallIntegerField('정렬 순서', default=0)
    search_able = models.BooleanField('검색 사용', default=True)
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
    name = models.CharField('이름', max_length=100, db_index=True)
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
    issue_project = models.ForeignKey('work.IssueProject', on_delete=models.SET_NULL,
                                      null=True, blank=True, verbose_name='업무 프로젝트')
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
    file = models.FileField(upload_to='post/%Y/%m/%d/', verbose_name='파일')
    file_name = models.CharField('파일명', max_length=100, blank=True, db_index=True)
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
            file_pos = self.file.tell()  # 현재 파일 커서 위치 백업
            self.file_type = mime.from_buffer(self.file.read(2048))  # 2048바이트 정도면 충분
            self.file.seek(file_pos)  # 원래 위치로 복구
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default=None, verbose_name='게시물', related_name='images')
    image = models.ImageField(upload_to='post/img/%Y/%m/%d/', verbose_name='이미지')
    image_name = models.CharField('파일명', max_length=100, blank=True, db_index=True)
    image_type = models.CharField('타입', max_length=100, blank=True)
    image_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        if self.image:
            self.image_name = self.image.name.split('/')[-1]
            mime = magic.Magic(mime=True)
            image_pos = self.image.tell()  # 현재 이미지 파일 커서 위치 백업
            self.image_type = mime.from_buffer(self.image.read(2048))  # 2048바이트 정도면 충분
            self.image.seek(image_pos)  # 원래 위치로 복구
            self.image_size = self.image.size
        super().save(*args, **kwargs)


def delete_file_field(instance, field_name):
    """Delete the file of the given field if it exists."""
    field = getattr(instance, field_name, None)
    try:
        if field and hasattr(field, 'path') and os.path.isfile(field.path):
            os.remove(field.path)
    except (FileNotFoundError, OSError):
        pass


@receiver(pre_save, sender=PostFile)
@receiver(pre_save, sender=PostImage)
def delete_old_file_on_update(sender, instance, **kwargs):
    """Generic file deletion handler for models with file/image fields."""
    if not instance.pk:  # 새 객체 생성 시는 아무 작업 안 함
        return

    try:
        # 기존 객체를 데이터베이스에서 가져옴
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    # 모델에 따라 처리할 필드 결정
    field_name = 'file' if sender == PostFile else 'image'
    old_file = getattr(old_instance, field_name, None)
    new_file = getattr(instance, field_name, None)

    # 파일이 변경되었는지 확인
    if old_file and old_file != new_file:
        delete_file_field(old_instance, field_name)


@receiver(pre_delete, sender=PostFile)
@receiver(pre_delete, sender=PostImage)
def delete_file_on_delete(sender, instance, **kwargs):
    """Generic file deletion handler for models."""
    if hasattr(instance, 'file'):
        delete_file_field(instance, 'file')
    if hasattr(instance, 'image'):
        delete_file_field(instance, 'image')


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
    name = models.CharField('태그', max_length=100, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '05. 태그 관리'
        verbose_name_plural = '05. 태그 관리'
