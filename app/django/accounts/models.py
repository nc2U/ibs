from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail
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
    work_manager = models.BooleanField(_('업무 시스템 관리자'), default=False,
                                       help_text=_('업무(redmine) 시스템 관리자인지 여부.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('-date_joined',)

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        :: 이 유저에게 이메일 보내기
        :param subject: 제목
        :param message: 내용
        :param from_email: 보낸 사람
        :param kwargs: 기타 첨가 내용
        :return: 발송 성공 여부
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

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


class StaffAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_auth')
    company = models.ForeignKey('company.Company', on_delete=models.PROTECT, verbose_name='회사정보')
    is_hq_staff = models.BooleanField('본사 근무 직원', default=False, help_text='외부 관계자가 아닌 본사 직원(관리자)일 경우 선택')
    is_pjt_staff = models.BooleanField('프로젝트 관리자', default=False, help_text='본사 직원 외 프로젝트 관리 직원(관리자)일 경우 선택')
    allowed_projects = models.ManyToManyField('project.Project', related_name='allowed_projects',
                                              blank=True, verbose_name='허용 프로젝트',
                                              help_text='사용자가 조회 및 관리할 수 있는 프로젝트들을 선택합니다.')
    default_project = models.ForeignKey('project.Project',
                                        on_delete=models.SET_NULL, null=True,
                                        blank=True, verbose_name='담당 메인 프로젝트',
                                        help_text='선택한 프로젝트를 사용자의 각 화면에서 기본 프로젝트로 보여줍니다.')

    class AuthChoice(models.TextChoices):
        NONE = '0', '권한없음'
        READ = '1', '읽기권한'
        WRITE = '2', '쓰기권한'

    contract = models.CharField('분양 계약 관리', max_length=1, choices=AuthChoice.choices, default='0')
    payment = models.CharField('분양 수납 관리', max_length=1, choices=AuthChoice.choices, default='0')
    notice = models.CharField('고객 고지 관리', max_length=1, choices=AuthChoice.choices, default='0')
    project_ledger = models.CharField('회계 자금 관리', max_length=1, choices=AuthChoice.choices, default='0')
    project_docs = models.CharField('문서 소송 관리', max_length=1, choices=AuthChoice.choices, default='0')
    project = models.CharField('신규 프로젝트', max_length=1, choices=AuthChoice.choices, default='0')
    project_site = models.CharField('부지 정보 관리', max_length=1, choices=AuthChoice.choices, default='0')
    company_ledger = models.CharField('본사 회계 관리', max_length=1, choices=AuthChoice.choices, default='0')
    company_docs = models.CharField('본사 문서 관리', max_length=1, choices=AuthChoice.choices, default='0')
    human_resource = models.CharField('본사 인사 관리', max_length=1, choices=AuthChoice.choices, default='0')
    company_settings = models.CharField('회사 관련설정', max_length=1, choices=AuthChoice.choices, default='0')
    auth_manage = models.CharField('권한 설정 관리', max_length=1, choices=AuthChoice.choices, default='0')

    def __str__(self):
        return f'{self.user}'

    class Meta:
        ordering = ('-id',)
        verbose_name = '사용자 정의 권한'
        verbose_name_plural = '사용자 정의 권한'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField('성명', max_length=20, blank=True)
    birth_date = models.DateField('생년월일', null=True, blank=True)
    cell_phone = models.CharField('휴대폰', max_length=13, blank=True)
    image = models.ImageField(upload_to='users/', null=True, blank=True, verbose_name='프로필 이미지')

    # Notification & Watcher Preferences
    auto_watch_created = models.BooleanField('내가 생성한 업무 자동 모니터링', default=True)
    auto_watch_assigned = models.BooleanField('나에게 할당된 업무 자동 모니터링', default=True)
    meeting_notification = models.BooleanField('회의록 참석 시 알림 수신', default=True)
    #
    like_posts = models.ManyToManyField(Post, blank=True, related_name='post_likes')
    like_comments = models.ManyToManyField(Comment, blank=True, related_name='comment_likes')
    blame_posts = models.ManyToManyField(Post, blank=True, related_name='post_blames')
    blame_comments = models.ManyToManyField(Comment, blank=True, related_name='comment_blames')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-id',)
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필'


file_cleanup_signals(Profile)  # 첨부파일 삭제


class DocScrape(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    docs = models.ForeignKey(Document, on_delete=models.CASCADE)
    title = models.CharField('스크랩 타이틀', max_length=50, blank=True, default='')
    created = models.DateTimeField('보관일', auto_now_add=True)

    def __str__(self):
        return self.title if self.title else self.docs.title

    class Meta:
        verbose_name = '문서 스크랩'
        verbose_name_plural = '문서 스크랩'


class PostScrape(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    title = models.CharField('스크랩 타이틀', max_length=50, blank=True, default='')
    created = models.DateTimeField('보관일', auto_now_add=True)

    def __str__(self):
        return self.title if self.title else self.post.title

    class Meta:
        verbose_name = '게시글 스크랩'
        verbose_name_plural = '게시글 스크랩'


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
