import os
import magic

from datetime import datetime
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_delete


class IssueProject(models.Model):
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name="회사")
    is_com_manage = models.BooleanField('본사관리', default=False)
    is_real_dev = models.BooleanField('부동산 개발 프로젝트', default=False)
    SORT_CHOICES = (('1', '본사관리'), ('2', '부동산개발'), ('3', '기타 프로젝트'))
    sort = models.CharField('유형', max_length=1, default='2', choices=SORT_CHOICES)
    name = models.CharField('이름', max_length=100)
    slug = models.CharField('식별자', max_length=100, unique=True,
                            help_text='1에서 100글자 소문자(a-z), 숫자, 대쉬(-)와 밑줄(_)만 가능합니다. 식별자는 저장 후에는 수정할 수 없습니다.')
    description = models.TextField('설명', blank=True, default='')
    homepage = models.URLField('홈페이지', max_length=255, null=True, blank=True)
    is_public = models.BooleanField('공개', default=True, help_text='공개 프로젝트는 모든 로그인한 사용자가 접속할 수 있습니다.')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='상위 프로젝트')
    is_inherit_members = models.BooleanField('상위 프로젝트 멤버 상속', default=False)
    default_version = models.ForeignKey('Version', on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name='기본 버전', help_text='기존 공유 버전에서만 작동합니다.')
    allowed_roles = models.ManyToManyField('Role', blank=True, related_name='projects', verbose_name='허용 역할')
    trackers = models.ManyToManyField('Tracker', blank=True, related_name='projects', verbose_name='허용유형')
    activities = models.ManyToManyField('CodeActivity', blank=True, verbose_name='작업분류(시간추적)')
    status = models.CharField('사용여부', max_length=1, default='1', choices=(('1', '사용'), ('9', '잠금보관(모든 접근이 차단됨)')))
    order = models.PositiveSmallIntegerField('정렬순서', default=0)
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('편집', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    def depth(self):
        if self.parent is None:
            return 0
        else:
            return self.parent.depth() + 1

    def family_tree(self, parents=None):
        if parents is None:
            parents = []

        if self.parent:
            parents.insert(0, self.parent)
            return self.parent.family_tree(parents)
        return parents

    def all_members(self):
        """
        멤버와 조상 멤버를 user 기준으로 유니크하게 합치고,
        멤버의 역할(Role)도 유니크하게 합치는 함수
        """
        members = self.members.all()  # 자신의 모든 멤버

        # 부모 프로젝트의 멤버를 재귀적으로 가져옴
        def get_all_parent_members(project):
            p_members = {}
            if project.is_inherit_members and project.parent:
                p_members.update(get_all_parent_members(project.parent))
            for member in project.members.all():
                if member.user.pk not in p_members:
                    p_members[member.user.pk] = {
                        'pk': member.pk,
                        'user': {'pk': member.user.pk, 'username': member.user.username},
                        'roles': {role.pk: {'pk': role.pk, 'name': role.name, 'inherited': True} for role in
                                  member.roles.all()},
                        'created': member.created,
                    }
                else:
                    p_members[member.user.pk]['roles'] \
                        .update(
                        {role.pk: {'pk': role.pk, 'name': role.name, 'inherited': True} for role in member.roles.all()})
            return p_members

        parent_members = get_all_parent_members(self)

        # 현재 프로젝트의 멤버와 부모 프로젝트의 멤버를 합침
        for mem in members:
            if mem.user.pk in parent_members:
                parent_roles = parent_members[mem.user.pk]['roles']
                union_roles = parent_roles.copy()
                union_roles.update(
                    {role.pk: {'pk': role.pk, 'name': role.name, 'inherited': False} for role in mem.roles.all()})
                parent_members[mem.user.pk]['roles'] = union_roles
            else:
                parent_members[mem.user.pk] = {
                    'pk': mem.pk,
                    'user': {'pk': mem.user.pk, 'username': mem.user.username},
                    'roles': {role.pk: {'pk': role.pk, 'name': role.name, 'inherited': False} for role in
                              mem.roles.all()},
                    'created': mem.created,
                }

        all_members = [
            {
                'pk': mem['pk'],
                'user': mem['user'],
                'roles': list(mem['roles'].values()),
                'created': mem['created']
            }
            for mem in parent_members.values()
        ]

        return all_members

    class Meta:
        ordering = ('order', 'id')
        verbose_name = '01. 프로젝트(업무)'
        verbose_name_plural = '01. 프로젝트(업무)'


class Module(models.Model):
    project = models.OneToOneField(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트')
    issue = models.BooleanField('업무관리', default=True)
    time = models.BooleanField('시간추적', default=True)
    news = models.BooleanField('공지', default=True)
    document = models.BooleanField('문서', default=True)
    file = models.BooleanField('파일', default=True)
    wiki = models.BooleanField('위키', default=True)
    repository = models.BooleanField('저장소', default=False)
    forum = models.BooleanField('게시판', default=True)
    calendar = models.BooleanField('달력', default=True)
    gantt = models.BooleanField('Gantt 차트', default=True)

    def __str__(self):
        return f'{self.project.name}'


class Role(models.Model):
    name = models.CharField('이름', max_length=20)
    assignable = models.BooleanField('업무 위탁 권한', default=True)
    ISSUE_VIEW_PERM = (('ALL', '모든 업무'), ('PUB', '비공개 업무 제외'), ('PRI', '직접 생성 또는 담당한 업무'))
    issue_visible = models.CharField('업무 보기 권한', max_length=3, choices=ISSUE_VIEW_PERM, default='PUB')
    TIME_VIEW_PERM = (('ALL', '모든 시간기록'), ('PRI', '직접 생성한 시간기록'))
    time_entry_visible = models.CharField('시간기록 보기 권한', max_length=3, choices=TIME_VIEW_PERM, default='ALL')
    USER_VIEW_PERM = (('ALL', '모든 활성 사용자'), ('PRJ', '보이는 프로젝트 사용자'))
    user_visible = models.CharField('사용자 보기 권한', max_length=3, choices=USER_VIEW_PERM, default='ALL')
    default_time_activity = models.ForeignKey('CodeActivity', on_delete=models.SET_NULL, null=True, blank=True,
                                              verbose_name='기본 활동')
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('편집', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '02. 역할 및 권한'
        verbose_name_plural = '02. 역할 및 권한'


class Permission(models.Model):
    role = models.OneToOneField(Role, on_delete=models.CASCADE)
    # 프로젝트
    # project_create = models.BooleanField('프로젝트 생성', default=False)  # 관라지(work_manager)만 생성 가능
    project_update = models.BooleanField('프로젝트 편집', default=False)
    project_close = models.BooleanField('프로젝트 닫기/열기', default=False)
    project_delete = models.BooleanField('프로젝트 삭제', default=False)
    project_public = models.BooleanField('프로젝트 공개/비공개 설정', default=False)
    project_module = models.BooleanField('프로젝트 모듈 선택', default=False)
    project_member = models.BooleanField('구성원 관리', default=False)
    project_version = models.BooleanField('버전 관리', default=False)
    project_create_sub = models.BooleanField('하위 프로젝트 생성', default=False)
    project_pub_query = models.BooleanField('공용 검색 양식 관리', default=False)
    project_save_query = models.BooleanField('검색 양식 저장', default=True)
    # 게시물
    forum_read = models.BooleanField('게시물 보기', default=True)
    forum_create = models.BooleanField('게시물 추가', default=True)
    forum_update = models.BooleanField('게시물 편집', default=False)
    forum_own_update = models.BooleanField('내 게시물 편집', default=True)
    forum_delete = models.BooleanField('게시물 삭제', default=False)
    forum_own_delete = models.BooleanField('내 게시물 삭제', default=True)
    forum_watcher_read = models.BooleanField('게시물 관람자 보기', default=False)
    forum_watcher_create = models.BooleanField('게시물 관람자 추가', default=False)
    forum_watcher_delete = models.BooleanField('게시물 관람자 삭제', default=False)
    forum_manage = models.BooleanField('게시판 관리', default=False)
    # 달력
    calendar_read = models.BooleanField('달력 보기', default=True)
    # 문서
    document_read = models.BooleanField('문서 보기', default=True)
    document_create = models.BooleanField('문서 추가', default=False)
    document_update = models.BooleanField('문서 편집', default=False)
    document_delete = models.BooleanField('문서 삭제', default=False)
    # 파일
    file_read = models.BooleanField('파일 보기', default=True)
    file_manage = models.BooleanField('파일 관리', default=False)
    # 간트차트
    gantt_read = models.BooleanField('간트 차트 보기', default=True)
    # 업무
    issue_read = models.BooleanField('업무 보기', default=True)
    issue_create = models.BooleanField('업무 추가', default=True)
    issue_update = models.BooleanField('업무 편집', default=False)
    issue_own_update = models.BooleanField('내 업무 편집', default=True)
    issue_copy = models.BooleanField('업무 복사', default=True)
    issue_rel_manage = models.BooleanField('업무 관계 관리', default=True)
    issue_sub_manage = models.BooleanField('하위 업무 관리', default=True)
    issue_public = models.BooleanField('업무 공개/비공개 설정', default=False)
    issue_own_public = models.BooleanField('내 업무 공개/비공개 설정', default=True)
    issue_comment_create = models.BooleanField('댓글 추가', default=True)
    issue_comment_update = models.BooleanField('댓글 편집', default=False)
    issue_comment_own_update = models.BooleanField('내 댓글 편집', default=True)
    issue_private_comment_read = models.BooleanField('비공개 댓글 보기', default=False)
    issue_private_comment_set = models.BooleanField('댓글 비공개 설정', default=False)
    issue_delete = models.BooleanField('업무 삭제', default=False)
    issue_watcher_read = models.BooleanField('업무 관람자 보기', default=False)
    issue_watcher_create = models.BooleanField('업무 관람자 추가', default=False)
    issue_watcher_delete = models.BooleanField('업무 관람자 삭제', default=False)
    issue_import = models.BooleanField('업무 가져 오기', default=False)
    issue_category_manage = models.BooleanField('업무 범주 관리', default=False)
    # 공지(뉴스)
    news_read = models.BooleanField('공지 보기', default=True)
    news_manage = models.BooleanField('공지 관리', default=False)
    news_comment = models.BooleanField('공지 댓글 달기', default=True)
    # 저장소(레파지토리)
    repo_changesets_read = models.BooleanField('변경 묶음 보기', default=False)
    repo_read = models.BooleanField('저장소 보기', default=False)
    repo_commit_access = models.BooleanField('변경 로그 보기', default=False)
    repo_rel_issue_manage = models.BooleanField('연결된 업무 관리', default=False)
    repo_manage = models.BooleanField('저장소 관리', default=False)
    # 시간추적
    time_read = models.BooleanField('소요 시간 보기', default=True)
    time_create = models.BooleanField('소요 시간 기록', default=True)
    time_update = models.BooleanField('소요 시간 편집', default=False)
    time_own_update = models.BooleanField('내 소요 시간 편집', default=True)
    time_pro_act_manage = models.BooleanField('프로젝트 작업 내역 관리', default=False)
    time_other_user_log = models.BooleanField('다른 사용자 소요 시간 입력', default=False)
    time_entries_import = models.BooleanField('소요 시간 가져오기', default=False)
    # 위키
    wiki_read = models.BooleanField('위키 보기', default=True)
    wiki_history_read = models.BooleanField('위키 기록 보기', default=True)
    wiki_page_export = models.BooleanField('위키 페이지 내보내기', default=False)
    wiki_page_update = models.BooleanField('위키 페이지 편집', default=False)
    wiki_page_rename = models.BooleanField('위키 페이지 이름 변경', default=False)
    wiki_page_delete = models.BooleanField('위키 페이지 삭제', default=False)
    wiki_attachment_delete = models.BooleanField('첨부파일 삭제', default=False)
    wiki_watcher_read = models.BooleanField('위키 관람자 보기', default=False)
    wiki_watcher_create = models.BooleanField('위키 관람자 추가', default=False)
    wiki_watcher_delete = models.BooleanField('위키 관람자 삭제', default=False)
    wiki_page_project = models.BooleanField('프로젝트 위키 페이지', default=False)
    wiki_manage = models.BooleanField('위키 관리', default=False)

    def __str__(self):
        return f'{self.role.name} - 권한'


class Member(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='구성원')
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트', related_name='members')
    roles = models.ManyToManyField(Role, verbose_name='역할')
    created = models.DateTimeField('추가', auto_now_add=True)

    def __str__(self):
        return self.user.__str__()

    class Meta:
        verbose_name = '03. 구성원'
        verbose_name_plural = '03. 구성원'


class Version(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트', related_name='versions')
    name = models.CharField('이름', max_length=20)
    status = models.CharField('상태', max_length=1, choices=(('1', '진행'), ('2', '잠김'), ('3', '닫힘')), default='1')
    SHARING_CHOICES = (
        ('0', '공유 없음'), ('1', '하위 프로젝트'), ('2', '상위 및 하위 프로젝트'), ('3', '최상위 및 모든 하위 프로젝트'), ('4', '모든 프로젝트'))
    sharing = models.CharField('공유', max_length=1, choices=SHARING_CHOICES, default='1')
    effective_date = models.DateField(verbose_name='버전 출시 기한', blank=True, null=True)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    wiki_page_title = models.CharField('위키 페이지', max_length=200, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('project', 'id')
        verbose_name = '04. 버전'
        verbose_name_plural = '04. 버전'


class Tracker(models.Model):
    name = models.CharField('이름', max_length=100)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    is_in_roadmap = models.BooleanField('로드맵에 표시', default=True)
    default_status = models.ForeignKey('IssueStatus', on_delete=models.PROTECT, verbose_name='초기 상태')
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('편집', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id')
        verbose_name = '05. 업무 유형'
        verbose_name_plural = '05. 업무 유형'


class IssueCategory(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트', related_name='categories')
    name = models.CharField('범주', max_length=100)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='담당자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-project', 'id',)
        verbose_name = '06. 업무 범주'
        verbose_name_plural = '06. 업무 범주'


class IssueStatus(models.Model):
    name = models.CharField('이름', max_length=20)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    closed = models.BooleanField('완료 상태', default=False)
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('편집', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '07. 업무 상태'
        verbose_name_plural = '07. 업무 상태'


class Workflow(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='역할')
    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE, verbose_name='업무 유형')
    old_status = models.OneToOneField(IssueStatus, on_delete=models.CASCADE, verbose_name='업무 상태',
                                      related_name='each_status')
    new_statuses = models.ManyToManyField(IssueStatus, verbose_name='허용 업무 상태', blank=True)

    def __str__(self):
        return f'{self.role} - {self.tracker}'

    class Meta:
        verbose_name = '08. 업무 흐름'
        verbose_name_plural = '08. 업무 흐름'


class Repository(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트')
    SCM_CHOICES = (('1', 'Git'),)
    scm = models.CharField('종류', max_length=10, choices=SCM_CHOICES, default='1')
    is_default = models.BooleanField('주저장소', default=True)
    slug = models.CharField('식별자', max_length=20, unique=True, blank=True, null=True,
                            help_text='1 에서 255 글자 소문자(a-z),숫자,대쉬(-)와 밑줄(_)만 가능합니다. 식별자는 저장후에는 수정할 수 없습니다.')
    path = models.CharField('저장소 경로', max_length=255, help_text='로컬의 bare 저장소 (예: //gitrepo, c:\\gitrepo)')
    path_encoding = models.CharField('경로 인코딩', max_length=20, default='UTF-8', help_text='기본: UTF-8')
    is_report = models.BooleanField('파일이나 폴더의 마지막 커밋을 보고', default=False)

    def __str__(self):
        return self.scm

    class Meta:
        ordering = ('id',)
        verbose_name = '09. 저장소'
        verbose_name_plural = '09. 저장소'


class CodeActivity(models.Model):
    name = models.CharField('이름', max_length=50)
    active = models.BooleanField('사용중', default=True)
    default = models.BooleanField('기본값', default=False)
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('수정', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '10. 작업분류(시간추적)'
        verbose_name_plural = '10. 작업분류(시간추적)'


class CodeIssuePriority(models.Model):
    name = models.CharField('이름', max_length=20)
    active = models.BooleanField('사용중', default=True)
    default = models.BooleanField('기본값', default=False)
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('수정', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '11. 업무 우선순위'
        verbose_name_plural = '11. 업무 우선순위'


class CodeDocsCategory(models.Model):
    name = models.CharField('이름', max_length=20)
    active = models.BooleanField('사용중', default=True)
    default = models.BooleanField('기본값', default=False)
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('수정', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '12. 문서 범주'
        verbose_name_plural = '12. 문서 범주'


class Issue(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.PROTECT, verbose_name='프로젝트')
    tracker = models.ForeignKey(Tracker, on_delete=models.PROTECT, verbose_name='유형')
    status = models.ForeignKey(IssueStatus, on_delete=models.PROTECT, verbose_name='상태')
    priority = models.ForeignKey(CodeIssuePriority, on_delete=models.PROTECT, verbose_name='우선순위')
    subject = models.CharField(max_length=100, verbose_name='제목')
    description = models.TextField(verbose_name='설명', blank=True, default='')
    category = models.ForeignKey(IssueCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='범주')
    fixed_version = models.ForeignKey(Version, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='목표 버전',
                                      related_name='issues')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='담당자', related_name='assignees')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='상위 업무')
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name='업무 관람자',
                                      related_name='watchers')
    is_private = models.BooleanField('비공개', default=False)
    estimated_hours = models.DecimalField('추정 소요시간', max_digits=5, decimal_places=2, null=True, blank=True)
    start_date = models.DateField('시작 일자')
    due_date = models.DateField('완료 기한', null=True, blank=True)
    done_ratio = models.PositiveSmallIntegerField('진척도', default=0)
    closed = models.DateTimeField('완료', null=True, blank=True, help_text='상태가 완료로 입력된 시간. 한 번 완료하면 다시 진행으로 변경해도 남아있음.')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자',
                                related_name='creator', null=True, blank=True)
    updater = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='수정자',
                                related_name='updater', null=True, blank=True)
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('편집', auto_now=True)

    def __str__(self):
        return self.subject

    class Meta:
        ordering = ('-id',)
        verbose_name = '13. 업무(작업)'
        verbose_name_plural = '13. 업무(작업)'


class IssueRelation(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, verbose_name='업무', related_name='relation_issues')
    issue_to = models.OneToOneField(Issue, on_delete=models.CASCADE, verbose_name='연결된 업무',
                                    related_name='relation_issue_to')
    RELATION_CHOICES = (
        ('relates', '다음 업무와 관련됨'),
        ('duplicates', '다음 업무에 중복됨'),
        ('duplicated', '중복된 업무'),
        ('blocks', '다음 업무의 해결을 막고 있음'),
        ('blocked', '다음 업무에게 막혀 있음'),
        ('precedes', '다음에 진행할 업무'),
        ('follows', '다음 업무를 우선 진행'),
        ('copied_to', '다음 업무로 복사됨'),
        ('copied_from', '다음 업무로부터 복사됨'))
    relation_type = models.CharField('관계 유형', max_length=20, choices=RELATION_CHOICES, default='relates')
    delay = models.PositiveSmallIntegerField('지연일수', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True, blank=True, verbose_name='작성자')

    def __str__(self):
        return f'{self.issue.subject}-{self.relation_type}-{self.issue_to.subject}'


def get_issue_file_path(instance, filename):
    today = datetime.today()
    date_path = today.strftime('%Y/%m/%d')
    return os.path.join('work', f'{instance.issue.project.slug}/issue/{date_path}/', filename)


class IssueFile(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, default=None, verbose_name='업무', related_name='files')
    file = models.FileField(upload_to=get_issue_file_path, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=100, blank=True)
    file_type = models.CharField('타입', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    description = models.CharField('부가설명', max_length=255, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
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


@receiver(pre_delete, sender=IssueFile)
def delete_file_on_delete(sender, instance, **kwargs):
    # Check if the file exists before attempting to delete it
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, verbose_name='업무', related_name='comments')
    content = models.TextField('내용')
    is_private = models.BooleanField('비공개 댓글', default=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('편집', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='작성자')

    def __str__(self):
        return self.content


class TimeEntry(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, verbose_name='업무')
    spent_on = models.DateField('작업일자', auto_now_add=True)
    hours = models.DecimalField('시간', max_digits=5, decimal_places=2)
    activity = models.ForeignKey(CodeActivity, on_delete=models.PROTECT, verbose_name='작업분류(시간추적)')
    comment = models.CharField('설명', max_length=255, blank=True, default='')
    created = models.DateTimeField('추가', auto_now_add=True)
    updated = models.DateTimeField('편집', auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    def __str__(self):
        return f'{self.issue} - {self.hours}'

    class Meta:
        ordering = ('-id',)


class News(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트')
    title = models.CharField('제목', max_length=255)
    summary = models.CharField('요약', max_length=255, blank=True, default='')
    description = models.TextField('설명', blank=True, default='')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='저자')
    created = models.DateTimeField('추가', auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '14. 공지'
        verbose_name_plural = '14. 공지'


def get_news_file_path(instance, filename):
    today = datetime.today()
    date_path = today.strftime('%Y/%m/%d')
    return os.path.join('work', f'{instance.issue.project.slug}/news/{date_path}/', filename)


class NewsFile(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, default=None, verbose_name='공지', related_name='files')
    file = models.FileField(upload_to=get_news_file_path, verbose_name='파일')
    file_name = models.CharField('파일명', max_length=100, blank=True)
    file_type = models.CharField('타입', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('사이즈', blank=True, null=True)
    description = models.CharField('부가설명', max_length=255, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
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
        verbose_name = '15. 작업 내역'
        verbose_name_plural = '15. 작업 내역'


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
    ACTION_CHOICES = (('Created', '추가'), ('Updated', '편집'), ('Comment', '댓글'))
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
        verbose_name = '16. 업무 로그'
        verbose_name_plural = '16. 업무 로그'


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
