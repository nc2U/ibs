from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.contrib.postgres.indexes import GinIndex

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_forum_file_path, get_forum_image_path, populate_file_meta


class Forum(models.Model):
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
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, verbose_name='게시판')
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
    forum = models.ForeignKey(Forum, on_delete=models.PROTECT, verbose_name='게시판')
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
        ordering = ['-is_notice', '-created']
        verbose_name = '03. 게시물 관리'
        verbose_name_plural = '03. 게시물 관리'
        indexes = [
            GinIndex(fields=['title'], opclasses=['gin_trgm_ops'], name='forum_post_title_trgm'),
            GinIndex(fields=['content'], opclasses=['gin_trgm_ops'], name='forum_post_content_trgm'),
        ]

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
    file = models.FileField(upload_to=get_forum_file_path, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    hit = models.PositiveIntegerField('다운로드수', default=0)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            populate_file_meta(self)
        super().save(*args, **kwargs)


file_cleanup_signals(PostFile)  # 파일인스턴스 직접 삭제시


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default=None, verbose_name='게시물', related_name='images')
    image = models.ImageField(upload_to=get_forum_image_path, verbose_name='이미지')
    image_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    image_type = models.CharField('타입', max_length=30, blank=True)
    image_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        if self.image and not self.image_name:
            populate_file_meta(self, file_field='image', name_field='image_name', type_field='image_type',
                               size_field='image_size')
        super().save(*args, **kwargs)


file_cleanup_signals(PostImage)  # 파일인스턴스 직접 삭제시


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
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, verbose_name='게시판')
    post = models.ManyToManyField(Post, blank=True, verbose_name='게시물')
    name = models.CharField('태그', max_length=100, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '04. 태그 관리'
        verbose_name_plural = '04. 태그 관리'
