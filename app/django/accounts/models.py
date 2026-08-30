from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from _utils.file_cleanup import file_cleanup_signals
from docs.models import Document
from forum.models import Post, Comment
from work.models.project import IssueProject, Member


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(_('username'), max_length=150, unique=True, db_index=True,
                                help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                                validators=[username_validator],
                                error_messages={'unique': _("A user with that username already exists.")})
    email = models.EmailField(_('email address'), max_length=255, unique=True)
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as active. '
                                                'Unselect this instead of deleting accounts.'))
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'))
    is_system = models.BooleanField(_('시스템 계정'), default=False,
                                    help_text=_('시스템 공지/알림/봇 전용 계정 여부. 일반 구성원 선택 목록에서 제외됩니다.'))
    work_manager = models.BooleanField(_('업무시스템 관리자'), default=False,
                                       help_text=_('업무(redmine) 시스템 관리자인지 여부.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('01. 사용자')
        verbose_name_plural = _('01. 사용자')
        ordering = ('-date_joined',)

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def work_projects(self):
        # 1. Get project IDs where the user is directly a member
        direct_project_ids = list(
            Member.objects.filter(user=self, project__status='1').values_list('project_id', flat=True))
        assigned_ids = set(direct_project_ids)
        current_ids = set(direct_project_ids)

        # 2. Recursively find child projects that inherit members
        while current_ids:
            child_ids = set(
                IssueProject.objects.filter(
                    parent_id__in=current_ids,
                    is_inherit_members=True,
                    status='1'
                ).values_list('id', flat=True)
            )
            new_ids = child_ids - assigned_ids
            if not new_ids:
                break
            assigned_ids.update(new_ids)
            current_ids = new_ids

        return IssueProject.objects.filter(pk__in=assigned_ids)

    def member_project_ids(self):
        # work_projects가 반환하는 QuerySet에서 ID 목록만 추출
        return self.work_projects().values_list('id', flat=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField('성명', max_length=20, blank=True)
    birth_date = models.DateField('생년월일', null=True, blank=True)
    cell_phone = models.CharField('휴대폰', max_length=13, blank=True)
    image = models.ImageField(upload_to='users/', null=True, blank=True, verbose_name='프로필 이미지')

    # Notification & Watcher Preferences
    auto_watch_created = models.BooleanField('내가 생성한 업무 자동 모니터링', default=True)
    auto_watch_assigned = models.BooleanField('나에게 할당된 업무 자동 모니터링', default=True)
    meeting_created_notification = models.BooleanField('회의록 등록 시 알림 수신', default=True)
    meeting_confirmed_notification = models.BooleanField('회의록 확정 시 알림 수신', default=True)
    #
    like_posts = models.ManyToManyField(Post, blank=True, related_name='post_likes')
    like_comments = models.ManyToManyField(Comment, blank=True, related_name='comment_likes')
    blame_posts = models.ManyToManyField(Post, blank=True, related_name='post_blames')
    blame_comments = models.ManyToManyField(Comment, blank=True, related_name='comment_blames')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-id',)
        verbose_name = '02. 사용자 프로필'
        verbose_name_plural = '02. 사용자 프로필'


file_cleanup_signals(Profile)  # 첨부파일 삭제


class DocScrape(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    docs = models.ForeignKey(Document, on_delete=models.CASCADE)
    title = models.CharField('스크랩 타이틀', max_length=50, blank=True, default='')
    created = models.DateTimeField('보관일', auto_now_add=True)

    def __str__(self):
        return self.title if self.title else self.docs.title

    class Meta:
        verbose_name = '03. 문서 스크랩'
        verbose_name_plural = '03. 문서 스크랩'


class PostScrape(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    title = models.CharField('스크랩 타이틀', max_length=50, blank=True, default='')
    created = models.DateTimeField('보관일', auto_now_add=True)

    def __str__(self):
        return self.title if self.title else self.post.title

    class Meta:
        verbose_name = '04. 게시글 스크랩'
        verbose_name_plural = '04. 게시글 스크랩'


class Todo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField('할일내용', max_length=50)
    completed = models.BooleanField('완료여부', default=False)
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)
    soft_deleted = models.BooleanField('삭제여부', default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('id',)
        verbose_name = '05. 할일 목록'
        verbose_name_plural = '05. 할일 목록'


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users')
    token = models.CharField('토큰', max_length=255)
    expired = models.PositiveIntegerField('만료시간(초)', blank=True, null=True, default=600)
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def is_expired(self):
        # Check if 10 minutes have passed since creation
        time_diff = timezone.localtime() - self.created
        return time_diff.total_seconds() >= self.expired

    class Meta:
        ordering = ('-updated',)
        verbose_name = '06. 패스워드 리셋토큰'
        verbose_name_plural = '06. 패스워드 리셋토큰'


class FCMDevice(models.Model):
    """모바일 기기 푸시 알림용 FCM 토큰"""
    PLATFORM_CHOICES = (
        ('ios', 'iOS'),
        ('android', 'Android'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_devices', verbose_name='사용자')
    registration_id = models.TextField('FCM 등록 토큰', unique=True)
    device_id = models.CharField('기기 고유 식별자', max_length=255, blank=True, null=True)
    platform = models.CharField('플랫폼', max_length=10, choices=PLATFORM_CHOICES, default='android')
    is_active = models.BooleanField('활성화 여부', default=True)
    created_at = models.DateTimeField('등록일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.platform})"

    class Meta:
        ordering = ('-updated_at',)
        verbose_name = '07. FCM 기기 토큰'
        verbose_name_plural = '07. FCM 기기 토큰 목록'


class Notification(models.Model):
    """사용자 인앱 알림함 & 푸시 이력"""
    CATEGORY_CHOICES = (
        ('work', '업무'),
        ('meeting', '회의'),
        ('notice', '공지'),
        ('approval', '전자결재'),
        ('chat', '채팅'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='수신자')
    title = models.CharField('알림 제목', max_length=255)
    body = models.TextField('알림 내용')
    category = models.CharField('카테고리', max_length=20, choices=CATEGORY_CHOICES, default='work')
    target_type = models.CharField('대상 유형', max_length=50, blank=True, help_text='issue, meeting, notice 등')
    target_id = models.CharField('대상 식별자', max_length=50, blank=True)
    data = models.JSONField('추가 페이로드', default=dict, blank=True)
    is_read = models.BooleanField('읽음 여부', default=False)
    created_at = models.DateTimeField('발생일시', auto_now_add=True)

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title} -> {self.user.username}"

    class Meta:
        ordering = ('-created_at',)
        verbose_name = '08. 사용자 알림'
        verbose_name_plural = '08. 사용자 알림 목록'
