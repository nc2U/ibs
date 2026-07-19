from django.conf import settings
from django.db import models
from django.db.models import Q
from tree_queries.query import TreeQuerySet


class IssueProjectManager(models.Manager.from_queryset(TreeQuerySet)):
    def get_queryset(self):
        return super().get_queryset().select_related('parent', 'company', 'creator')


class IssueProject(models.Model):
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, verbose_name="회사")
    TYPE_CHOICES = (('1', '본사관리'), ('2', '부동산개발'), ('3', '기타 프로젝트'))
    type = models.CharField('유형', max_length=1, default='2', choices=TYPE_CHOICES)
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
    STATUS_CHOICES = ('1', '사용중'), ('2', '닫힘'), ('9', '잠금보관(모든 접근이 차단됨)')
    status = models.CharField('사용여부', max_length=1, default='1', choices=STATUS_CHOICES,
                              help_text='사용중: 활성화 상태, 닫힘: 읽기 전용 상태, 잠금보관: 관리자외 접근 제한')
    order = models.PositiveSmallIntegerField('정렬순서', default=10)
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

    def get_ancestors(self, **kwargs):
        """django-tree-queries를 사용하여 모든 조상 노드를 반환합니다."""
        return self.__class__._default_manager.ancestors(self, **kwargs)

    def get_descendants(self, **kwargs):
        """django-tree-queries를 사용하여 모든 자손 노드를 반환합니다."""
        return self.__class__._default_manager.descendants(self, **kwargs)

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
        로그인하지 않은 경우 '익명' 역할(pk=1)의 권한,
        로그인했으나 멤버가 아닌 '회원' 역할(pk=2)의 권한을 반환합니다.
        """
        if not hasattr(self, '_user_permission_cache'):
            self._user_permission_cache = {}
        user_key = user.pk if user and user.is_authenticated else 'anonymous'
        if user_key in self._user_permission_cache:
            return self._user_permission_cache[user_key]

        permission_codes = set()

        if not user or not user.is_authenticated:
            try:
                role = Role.objects.prefetch_related('permissions').get(pk=1)
                for perm in role.permissions.all():
                    permission_codes.add(perm.code)
            except Role.DoesNotExist:
                pass
            result = list(permission_codes)
            self._user_permission_cache[user_key] = result
            return result

        # 1. 상속 가능한 상위 프로젝트 목록 계산 (PK 리스트 사용)
        project_ids = [self.pk]
        curr = self
        while curr.is_inherit_members and curr.parent:
            if curr.parent.pk in project_ids:
                break
            project_ids.append(curr.parent.pk)
            curr = curr.parent

        # 2. 해당 사용자(user)가 속한 Member 정보와 Role만 한정하여 조회 (user_id 및 project_id__in 사용)
        from work.models.project import Member
        user_members = Member.objects.filter(
            project_id__in=project_ids,
            user_id=user.pk
        ).prefetch_related('roles__permissions')

        # 3. 모든 역할에 연결된 권한 코드 추출
        if user_members.exists():
            for member in user_members:
                for role in member.roles.all():
                    for perm in role.permissions.all():
                        permission_codes.add(perm.code)
        else:
            # 멤버가 아닌 경우 -> '비회원' 역할(pk=2)의 권한 추출
            try:
                role = Role.objects.prefetch_related('permissions').get(pk=2)
                for perm in role.permissions.all():
                    permission_codes.add(perm.code)
            except Role.DoesNotExist:
                pass

        result = list(permission_codes)
        self._user_permission_cache[user_key] = result
        return result

    def get_user_role_attributes(self, user):
        """
        사용자의 프로젝트 내 종합 역할(Role) 속성을 계산합니다.
        반환 딕셔너리: {'assignable': bool, 'issue_visible': str, 'user_visible': str}
        """
        default_attrs = {
            'assignable': False,
            'issue_visible': 'NOP',
            'user_visible': 'NOP'
        }

        if not user:
            return default_attrs

        # 1. 슈퍼유저 / work_manager 이면 최대 권한 반환
        if user.is_superuser or getattr(user, 'work_manager', False):
            return {
                'assignable': True,
                'issue_visible': 'ALL',
                'user_visible': 'ALL'
            }

        # 2. 로그인하지 않은 익명 사용자인 경우 -> '익명(pk=1)' 역할의 속성 반환
        if not user.is_authenticated:
            try:
                role = Role.objects.get(pk=1)
                return {
                    'assignable': role.assignable,
                    'issue_visible': role.issue_visible,
                    'user_visible': role.user_visible
                }
            except Role.DoesNotExist:
                return default_attrs

        # 3. 로그인된 사용자
        # 3-A. 상속 가능한 상위 프로젝트 목록 계산
        projects_to_fetch = [self]
        curr = self
        while curr.is_inherit_members and curr.parent:
            if curr.parent in projects_to_fetch:
                break
            projects_to_fetch.append(curr.parent)
            curr = curr.parent

        # 3-B. 해당 사용자(user)가 속한 Member 정보 조회
        from work.models.project import Member
        user_members = Member.objects.filter(
            project__in=projects_to_fetch,
            user=user
        ).prefetch_related('roles')

        # 우선순위 정의 헬퍼
        issue_visibility_order = {'ALL': 3, 'PUB': 2, 'PRI': 1, 'NOP': 0}
        user_visibility_order = {'ALL': 2, 'PRJ': 1, 'NOP': 0}

        if user_members.exists():
            # 멤버인 경우 -> 멤버의 역할들을 수집하여 병합
            assignable = False
            best_issue_visible = 'NOP'
            best_user_visible = 'NOP'

            for member in user_members:
                for role in member.roles.all():
                    if role.assignable:
                        assignable = True
                    # issue_visible 우선순위 병합
                    if issue_visibility_order.get(role.issue_visible,
                                                  0) > issue_visibility_order.get(best_issue_visible, 0):
                        best_issue_visible = role.issue_visible
                    # user_visible 우선순위 병합
                    if user_visibility_order.get(role.user_visible,
                                                 0) > user_visibility_order.get(best_user_visible, 0):
                        best_user_visible = role.user_visible

            return {
                'assignable': assignable,
                'issue_visible': best_issue_visible,
                'user_visible': best_user_visible
            }
        else:
            # 멤버가 아닌 로그인 회원 -> '비회원(pk=2)' 역할의 속성 반환
            try:
                role = Role.objects.get(pk=2)
                return {
                    'assignable': role.assignable,
                    'issue_visible': role.issue_visible,
                    'user_visible': role.user_visible
                }
            except Role.DoesNotExist:
                return default_attrs

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
    calendar = models.BooleanField('캘린더', default=True)

    def __str__(self):
        return f'{self.project.name}'

    class Meta:
        verbose_name = '02. 모듈'
        verbose_name_plural = '02. 모듈'


class Role(models.Model):
    name = models.CharField('이름', max_length=20, db_index=True)
    assignable = models.BooleanField('업무할당 가능 여부', default=True)
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
        ordering = ('order', '-id',)
        verbose_name = '03. 역할'
        verbose_name_plural = '03. 역할'


class Permission(models.Model):
    MODULE_CHOICES = (('project', '프로젝트'), ('meeting', '회의'), ('issue', '업무'),
                      ('news', '공지'), ('docs', '문서'), ('forum', '게시판'), ('calendar', '캘린더'))
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='구성원')
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name='프로젝트', related_name='members')
    roles = models.ManyToManyField(Role, verbose_name='역할')
    created = models.DateTimeField('등록일', auto_now_add=True)

    def __str__(self):
        return self.user.__str__()

    class Meta:
        verbose_name = '05. 구성원'
        verbose_name_plural = '05. 구성원'
        unique_together = ('user', 'project')  # 한 프로젝트당 한 번만 속할 수 있음


class ProjectSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="사용자")
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE, verbose_name="업무 프로젝트")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')
        verbose_name = "프로젝트 알림 구독"
        verbose_name_plural = "프로젝트 알림 구독"


class ProjectBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             verbose_name="사용자", related_name='bookmarked_projects')
    project = models.ForeignKey(IssueProject, on_delete=models.CASCADE,
                                verbose_name="업무 프로젝트", related_name='bookmarked_by')
    order = models.PositiveSmallIntegerField('정렬순서', default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')
        ordering = ('order', 'created')
        verbose_name = "프로젝트 북마크"
        verbose_name_plural = "프로젝트 북마크"

    def __str__(self):
        return f'{self.user} - {self.project.name}'


class VersionManager(models.Manager):

    def accessible_from(self, project):
        ancestors = project.get_ancestors()
        descendants = project.get_descendants()

        ancestor_ids = ancestors.values('id')
        descendant_ids = descendants.values('id')

        # 프로젝트 트리의 루트를 찾습니다 (ancestors는 루트부터 정렬됨)
        root = ancestors.first() or project
        root_descendants = root.get_descendants(include_self=True).values('id')

        # sharing: 0:없음, 1:하위, 2:상위/하위, 3:최상위 및 모든 하위, 4:전체
        return self.filter(
            # 0. 공유 없음
            # -> 내 프로젝트에 속한 버전만 보여줌
            Q(project=project) |
            # 1. 하위 프로젝트
            # -> 직계 하위 프로젝트의 버전이라면 [2, 3, 4] 인 버전을 보여줌
            Q(project_id__in=descendant_ids, sharing__in=['2', '3', '4']) |
            # 2. 상위 및 하위 프로젝트
            # -> 직계 상위 프로젝트의 버전이라면 [1, 2, 3, 4] 인 버전을 보여줌
            Q(project_id__in=ancestor_ids, sharing__in=['1', '2', '3', '4']) |
            # 3. 최상위 및 모든 하위 프로젝트
            # -> 내 프로젝트의 루트 프로젝트의 버전이라면 [3] 인 버전을 보여줌
            Q(project_id__in=root_descendants, sharing='3') |
            # 4. 모든 프로젝트
            # -> 내 위치와 상관없이 무조건 보여줌.
            Q(sharing='4')
        )


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

    objects = VersionManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = '06. 단계'
        verbose_name_plural = '06. 단계'
