from django.conf import settings
from django.db import models


class IssueProjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('parent', 'company', 'creator')


class IssueProject(models.Model):
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name="회사")
    SORT_CHOICES = (('1', '본사관리'), ('2', '부동산개발'), ('3', '기타 프로젝트'))
    sort = models.CharField('유형', max_length=1, default='2', choices=SORT_CHOICES)
    name = models.CharField('이름', max_length=100, db_index=True)
    slug = models.CharField('식별자', max_length=100, unique=True,
                            help_text='1에서 100글자 소문자(a-z), 숫자, 대쉬(-)와 밑줄(_)만 가능합니다. 식별자는 저장 후에는 수정할 수 없습니다.')
    description = models.TextField('설명', blank=True, default='')
    homepage = models.URLField('홈페이지', max_length=255, null=True, blank=True)
    is_public = models.BooleanField('공개', default=True, help_text='공개 프로젝트는 모든 로그인한 사용자가 접속할 수 있습니다.')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='상위 프로젝트')
    is_inherit_members = models.BooleanField('상위 프로젝트 멤버 상속', default=False)
    default_version = models.ForeignKey('Version', on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name='기본 단계', help_text='기존 공유 단계에서만 작동합니다.')
    allowed_roles = models.ManyToManyField('Role', blank=True, related_name='projects', verbose_name='허용 역할')
    trackers = models.ManyToManyField('Tracker', blank=True, related_name='projects', verbose_name='허용유형')
    status = models.CharField('사용여부', max_length=1, default='1', choices=(('1', '사용'), ('9', '잠금보관(모든 접근이 차단됨)')))
    order = models.PositiveSmallIntegerField('정렬순서', default=0)
    slack_notifications_enabled = models.BooleanField(
        'Slack 알림 활성화',
        default=False,
        help_text='이 프로젝트의 Slack 알림 사용 여부. 웹훅 URL은 환경변수로 관리: 본사관리(sort=1)는 "com_slack_key", 개별 프로젝트는 "{slug}_slack_key"'
    )
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='작성자')

    objects = IssueProjectManager()

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
        멤버의 역할(Role)도 유니크하게 합치는 함수 (최적화 버전)
        """
        projects_to_fetch = [self]
        curr = self
        while curr.is_inherit_members and curr.parent:
            # Avoid infinite loop if parent is self (though unlikely with Django models)
            if curr.parent in projects_to_fetch:
                break
            projects_to_fetch.append(curr.parent)
            curr = curr.parent

        from work.models.project import Member
        # optimization: select_related('user') and prefetch_related('roles')
        all_mems = Member.objects.filter(project__in=projects_to_fetch).select_related('user').prefetch_related('roles')

        member_data = {}
        for mem in all_mems:
            is_inherited = mem.project_id != self.id
            if mem.user_id not in member_data:
                member_data[mem.user_id] = {
                    'pk': mem.pk,
                    'user': {'pk': mem.user_id, 'username': mem.user.username},
                    'roles': {role.pk: {'pk': role.pk, 'name': role.name, 'assignable': role.assignable,
                                        'inherited': is_inherited} for role in
                              mem.roles.all()},
                    'created': mem.created,
                }
            else:
                # Merge roles if user is already in member_data, but don't overwrite local roles with inherited ones
                for role in mem.roles.all():
                    if role.pk not in member_data[mem.user_id]['roles']:
                        member_data[mem.user_id]['roles'][role.pk] = {
                            'pk': role.pk,
                            'name': role.name,
                            'assignable': role.assignable,
                            'inherited': is_inherited
                        }
                    elif not is_inherited:
                        # If we found a local (non-inherited) version of an already existing role, update it
                        member_data[mem.user_id]['roles'][role.pk]['inherited'] = False

        return [
            {
                'pk': data['pk'],
                'user': data['user'],
                'roles': list(data['roles'].values()),
                'created': data['created']
            }
            for data in member_data.values()
        ]

    def get_user_permissions(self, user):
        """
        사용자의 프로젝트 내 권한 코드 세트를 계산합니다. (특정 사용자에 맞춘 최적화 쿼리 버전)
        """
        if not user or not user.is_authenticated:
            return []

        # 1. 상속 가능한 상위 프로젝트 목록 계산
        projects_to_fetch = [self]
        curr = self
        while curr.is_inherit_members and curr.parent:
            if curr.parent in projects_to_fetch:
                break
            projects_to_fetch.append(curr.parent)
            curr = curr.parent

        # 2. 해당 사용자(user)가 속한 Member 정보와 Role만 한정하여 조회
        from work.models.project import Member
        user_members = Member.objects.filter(
            project__in=projects_to_fetch,
            user=user
        ).prefetch_related('roles__permissions')

        # 3. 모든 역할에 연결된 권한 코드 추출
        permission_codes = set()
        for member in user_members:
            for role in member.roles.all():
                for perm in role.permissions.all():
                    permission_codes.add(perm.code)

        return list(permission_codes)

    class Meta:
        ordering = ('order', 'id')
        verbose_name = '01. 프로젝트(업무)'
        verbose_name_plural = '01. 프로젝트(업무)'


class Module(models.Model):
    project = models.OneToOneField(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트')
    meeting = models.BooleanField('회의', default=True)
    issue = models.BooleanField('업무', default=True)
    news = models.BooleanField('공지', default=True)
    document = models.BooleanField('문서', default=True)
    forum = models.BooleanField('게시판', default=True)
    calendar = models.BooleanField('달력', default=True)

    def __str__(self):
        return f'{self.project.name}'

    class Meta:
        verbose_name = '02. 모듈'
        verbose_name_plural = '02. 모듈'


class Role(models.Model):
    name = models.CharField('이름', max_length=20, db_index=True)
    assignable = models.BooleanField('업무 위탁 권한', default=True)
    ISSUE_VIEW_PERM = (('ALL', '모든 업무'), ('PUB', '비공개 업무 제외'), ('PRI', '직접 생성 또는 담당한 업무'), ('NOP', '없음'))
    issue_visible = models.CharField('업무 보기 권한', max_length=3, choices=ISSUE_VIEW_PERM, default='PUB')
    USER_VIEW_PERM = (('ALL', '모든 활성 사용자'), ('PRJ', '보이는 프로젝트 사용자'), ('NOP', '없음'))
    user_visible = models.CharField('사용자 보기 권한', max_length=3, choices=USER_VIEW_PERM, default='ALL')
    permissions = models.ManyToManyField('work.Permission', related_name='roles')
    order = models.PositiveSmallIntegerField('정렬', default=1)
    created = models.DateTimeField('등록일', auto_now_add=True)
    updated = models.DateTimeField('수정일', auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='작성자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        verbose_name = '03. 역할'
        verbose_name_plural = '03. 역할'


class Permission(models.Model):
    MODULE_CHOICES = (('project', '프로젝트'), ('meeting', '회의'), ('issue', '업무'),
                      ('news', '공지'), ('docs', '문서'), ('forum', '게시판'), ('calendar', '달력'))
    module = models.CharField('모듈', max_length=10, choices=MODULE_CHOICES, db_index=True)
    code = models.CharField('코드', max_length=30, unique=True)
    name = models.CharField('이름', max_length=20)
    is_default = models.BooleanField('기본 활성여부', default=False)
    description = models.CharField('설명', max_length=255, blank=True, default='')

    def __str__(self):
        return f"{self.code}({self.name})"

    class Meta:
        ordering = ('id',)
        verbose_name = '04. 권한'
        verbose_name_plural = '04. 권한'


class Member(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='구성원')
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트', related_name='members')
    roles = models.ManyToManyField(Role, verbose_name='역할')
    created = models.DateTimeField('등록일', auto_now_add=True)

    def __str__(self):
        return self.user.__str__()

    class Meta:
        verbose_name = '05. 구성원'
        verbose_name_plural = '05. 구성원'
        unique_together = ('user', 'project')  # 한 프로젝트당 한 번만 속할 수 있음


class Version(models.Model):
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트', related_name='versions')
    name = models.CharField('이름', max_length=20, db_index=True)
    status = models.CharField('상태', max_length=1, choices=(('1', '진행'), ('2', '잠김'), ('3', '닫힘')), default='1')
    SHARING_CHOICES = (('0', '공유 없음'), ('1', '하위 프로젝트'), ('2', '상위 및 하위 프로젝트'),
                       ('3', '최상위 및 모든 하위 프로젝트'), ('4', '모든 프로젝트'))
    sharing = models.CharField('공유', max_length=1, choices=SHARING_CHOICES, default='1')
    effective_date = models.DateField(verbose_name='단계 완료 기한', blank=True, null=True)
    description = models.CharField('설명', max_length=255, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('project', 'id')
        verbose_name = '06. 단계'
        verbose_name_plural = '06. 단계'
