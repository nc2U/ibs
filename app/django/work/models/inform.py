from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.contrib.postgres.indexes import GinIndex

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_news_file_path, populate_file_meta
from work.models.project import IssueProject, Member


class News(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트')
    title = models.CharField('제목', max_length=255, db_index=True)
    summary = models.CharField('요약', max_length=255, blank=True, default='')
    content = models.TextField('내용', blank=True, default='')
    is_important = models.BooleanField('중요 공지', default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='저자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def __str__(self):
        return self.title

    def is_new(self):
        today = datetime.today().strftime('%Y-%m-%d %H:%M')
        new_period = self.created + timedelta(days=3)
        return today < new_period.strftime('%Y-%m-%d %H:%M')

    class Meta:
        ordering = ('-is_important', '-created',)
        verbose_name = '15. 공지'
        verbose_name_plural = '15. 공지'
        indexes = [
            GinIndex(fields=['title'], opclasses=['gin_trgm_ops'], name='work_news_title_trgm'),
            GinIndex(fields=['summary'], opclasses=['gin_trgm_ops'], name='work_news_summary_trgm'),
            GinIndex(fields=['content'], opclasses=['gin_trgm_ops'], name='work_news_content_trgm'),
        ]


class NewsFile(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, default=None, verbose_name='공지', related_name='files')
    file = models.FileField(upload_to=get_news_file_path, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=255, blank=True, db_index=True)
    file_type = models.CharField('타입', max_length=80, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    description = models.CharField('부가설명', max_length=255, blank=True, default='')
    created = models.DateTimeField('등록일', auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='등록자')

    def __str__(self):
        return settings.MEDIA_URL

    def save(self, *args, **kwargs):
        populate_file_meta(self)
        super().save(*args, **kwargs)


file_cleanup_signals(NewsFile)  # 파일인스턴스 직접 삭제시


class NewsComment(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, verbose_name='공지', related_name='comments')
    content = models.TextField('내용')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='등록자')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.news} -> {self.content}"

    class Meta:
        ordering = ['-created']


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
    forum = models.BooleanField('게시판 포함 여부', default=False)
    project = models.BooleanField('프로젝트 포함 여부', default=False)
    open_issue = models.BooleanField('미해결 업무 검색', default=False)
    attachment = models.CharField('설명 및 첨부파일 검색', max_length=1,
                                  choices=(('0', '설명 및 첨부파일 검색'), ('1', '설명에서만 검색'), ('2', '첨부파일에서만 검색')), default='0')

    def __str__(self):
        return f'#{self.pk}. {self.member.user} - 검색조건'


class CustomQuery(models.Model):
    TARGET_TYPE_CHOICES = (
        ('project', '프로젝트'),
        ('meeting', '회의록'),
        ('issue', '업무'),
        ('calendar', '캘린더'),
    )
    name = models.CharField('검색양식 이름', max_length=100)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    target_type = models.CharField(
        '대상 모듈',
        max_length=20,
        choices=TARGET_TYPE_CHOICES,
        db_index=True
    )
    project = models.ForeignKey(
        IssueProject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='프로젝트 범위',
        related_name='custom_queries'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='작성자',
        related_name='custom_queries'
    )
    is_public = models.BooleanField(
        '공용 여부',
        default=False,
        help_text='체크 시 프로젝트 멤버 전원이 사용할 수 있습니다.'
    )

    # JSON 형식 필드들
    filters = models.JSONField(
        '필터 조건',
        default=dict,
        blank=True,
        help_text='필터 정보 JSON (예: {"status": 1, "is_confirmed": true})'
    )
    column_names = models.JSONField(
        '표시할 열',
        default=list,
        blank=True,
        help_text='테이블 그리드에 표시할 필드 목록 JSON (주로 issue, project, meeting)'
    )
    sort_criteria = models.JSONField(
        '정렬 기준',
        default=list,
        blank=True,
        help_text='정렬 옵션 JSON (예: [["priority", "desc"], ["created", "desc"]])'
    )
    group_by = models.CharField(
        '그룹화 기준',
        max_length=50,
        blank=True,
        default='',
        help_text='데이터 그룹핑 필드명'
    )

    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        ordering = ('target_type', 'name', '-created')
        verbose_name = '16. 검색 양식'
        verbose_name_plural = '16. 검색 양식'

    def __str__(self):
        scope = "공용" if self.is_public else "개인"
        return f"[{self.get_target_type_display()} - {scope}] {self.name} ({self.user.username})"
