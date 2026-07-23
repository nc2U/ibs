from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from work.models import Issue
from work.models.issue import IssueCategory, Tracker
from work.models.project import IssueProject, Module, Role, Permission, \
    Member, ProjectSubscription, ProjectBookmark, Version
from work.services.work_services import PermissionService

User = get_user_model()


class ProjectPermissionMixin:
    """
    Mixin to provide consistent project-level visibility and permission logic.
    """

    def _get_project_members(self, obj):
        cache_key = f'_members_cache_{obj.pk}'
        if not hasattr(self, cache_key):
            setattr(self, cache_key, obj.all_members())
        return getattr(self, cache_key)

    def get_visible(self, obj):
        if not obj:
            return False
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if not user.is_authenticated:
                return obj.is_public
            if user.is_superuser or getattr(user, 'work_manager', False):
                return True
            if obj.is_public:
                return True
            all_members = self._get_project_members(obj)
            members = [m['user']['pk'] for m in all_members]
            return user.pk in members
        return False

    def get_my_perms(self, obj):
        if not obj:
            return []
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if not user.is_authenticated:
                return []
            if user.is_superuser or getattr(user, 'work_manager', False):
                return list(Permission.objects.values_list('code', flat=True))
            return obj.get_user_permissions(user)
        return []

    def get_my_role(self, obj):
        if not obj:
            return {
                'assignable': False,
                'issue_visible': 'NOP',
                'user_visible': 'NOP'
            }
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.get_user_role_attributes(request.user)
        return {
            'assignable': False,
            'issue_visible': 'NOP',
            'user_visible': 'NOP'
        }

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarked_by.filter(user=request.user).exists()


# Work --------------------------------------------------------------------------
class SimpleIssueProjectSerializer(ProjectPermissionMixin, serializers.ModelSerializer):
    visible = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'name', 'slug', 'visible', 'status')


class RoleInMemberSerializer(serializers.ModelSerializer):
    inherited = serializers.BooleanField(read_only=True)

    class Meta:
        model = Role
        fields = ('pk', 'name', 'assignable', 'inherited')


class MemberInIssueProjectSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    roles = RoleInMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Member
        fields = ('pk', 'user', 'roles', 'created')


class ModuleInIssueProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('pk', 'project', 'issue', 'news', 'document',
                  'forum', 'calendar')


class RoleInIssueProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('pk', 'name')


class TrackerInIssueProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracker
        fields = ('pk', 'name', 'description')


class VersionInIssueProjectSerializer(serializers.ModelSerializer):
    status_desc = serializers.CharField(source='get_status_display', read_only=True)
    sharing_desc = serializers.CharField(source='get_sharing_display', read_only=True)
    is_default = serializers.SerializerMethodField(read_only=True)
    proj_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Version
        fields = ('pk', 'name', 'status', 'status_desc', 'sharing', 'sharing_desc',
                  'is_default', 'effective_date', 'description', 'proj_name')

    @staticmethod
    def get_is_default(obj):
        default_ver = obj.project.default_version
        return True if default_ver and default_ver.pk == obj.pk else False


class IssueCategoryInIssueProjectSerializer(serializers.ModelSerializer):
    assigned_to = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueCategory
        fields = ('pk', 'name', 'assigned_to')


class IssueProjectListSerializer(ProjectPermissionMixin, serializers.ModelSerializer):
    company = serializers.SlugRelatedField('name', read_only=True)
    module = ModuleInIssueProjectSerializer(read_only=True)
    creator = serializers.SlugRelatedField('username', read_only=True)
    visible = serializers.SerializerMethodField(read_only=True)
    my_perms = serializers.SerializerMethodField(read_only=True)
    my_role = serializers.SerializerMethodField(read_only=True)
    sub_projects = serializers.SerializerMethodField()
    all_members = MemberInIssueProjectSerializer(many=True, read_only=True)
    allowed_roles = RoleInIssueProjectSerializer(many=True, read_only=True)
    parent_visible = serializers.SerializerMethodField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'company', 'type', 'name', 'slug', 'description', 'is_public', 'parent',
                  'allowed_roles', 'status', 'slack_notifications_enabled', 'created', 'updated',
                  'creator', 'sub_projects', 'depth', 'module', 'my_role', 'my_perms', 'all_members',
                  'visible', 'parent_visible', 'is_bookmarked')

    def get_sub_projects(self, obj):
        sub_projects = obj.issueproject_set.exclude(status='9')
        return IssueProjectListSerializer(sub_projects, many=True, read_only=True, context=self.context).data

    def get_parent_visible(self, obj):
        return self.get_visible(obj.parent) if obj.parent else False


class IssueProjectSerializer(ProjectPermissionMixin, serializers.ModelSerializer):
    ancestors = SimpleIssueProjectSerializer(source='get_ancestors', many=True, read_only=True)
    module = ModuleInIssueProjectSerializer(read_only=True)
    all_members = MemberInIssueProjectSerializer(many=True, read_only=True)
    members = MemberInIssueProjectSerializer(many=True, read_only=True)
    allowed_roles = RoleInIssueProjectSerializer(many=True, read_only=True)
    trackers = TrackerInIssueProjectSerializer(many=True, read_only=True)
    versions = serializers.SerializerMethodField(read_only=True)
    categories = IssueCategoryInIssueProjectSerializer(many=True, read_only=True)
    visible = serializers.SerializerMethodField(read_only=True)
    parent_visible = serializers.SerializerMethodField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField(read_only=True)
    sub_projects = serializers.SerializerMethodField(read_only=True)
    creator = serializers.SlugRelatedField('username', read_only=True)
    my_perms = serializers.SerializerMethodField(read_only=True)
    my_role = serializers.SerializerMethodField(read_only=True)

    # 모듈 설정을 위한 필드 추가 (write_only)
    issue = serializers.BooleanField(write_only=True, default=True)
    news = serializers.BooleanField(write_only=True, default=True)
    document = serializers.BooleanField(write_only=True, default=True)
    forum = serializers.BooleanField(write_only=True, default=True)
    calendar = serializers.BooleanField(write_only=True, default=True)

    class Meta:
        model = IssueProject
        fields = IssueProjectListSerializer.Meta.fields + ('homepage', 'is_inherit_members', 'default_version',
                                                           'trackers',
                                                           'ancestors', 'members', 'versions', 'categories', 'forums',
                                                           'issue', 'news', 'document', 'forum', 'calendar')

        read_only_fields = ('status', 'is_public', 'forums')

    # 메서드 복구
    @staticmethod
    def get_versions(obj):
        # 모든 상태의 버전을 포함.
        # VersionManager의 accessible_from을 사용.
        versions = Version.objects.accessible_from(obj)
        return VersionInIssueProjectSerializer(versions, many=True).data

    def get_sub_projects(self, obj):
        sub_projects = obj.issueproject_set.exclude(status='9')
        # Create a new serializer class without the 'my_perms' field to avoid recursion bloat if needed,
        # but for now reusing ListSerializer is fine as it's meant for tree view
        return IssueProjectListSerializer(sub_projects, many=True, read_only=True, context=self.context).data

    def get_parent_visible(self, obj):
        return self.get_visible(obj.parent) if obj.parent else False

    @transaction.atomic
    def create(self, validated_data):
        # validated_data에서 추가 필드 추출
        issue = validated_data.pop('issue', True)
        news = validated_data.pop('news', True)
        document = validated_data.pop('document', True)
        forum = validated_data.pop('forum', True)
        calendar = validated_data.pop('calendar', True)

        project = IssueProject.objects.create(**validated_data)

        # 권한 검증 서비스 호출 및 모듈 생성
        module_fields = ['issue', 'news', 'document', 'forum', 'calendar']
        if any(field in self.initial_data for field in module_fields):
            request = self.context.get('request')
            if request:
                PermissionService.check_module_permission(request.user, project)

            Module.objects.create(
                project=project, issue=issue, news=news,
                document=document, forum=forum, calendar=calendar)
        else:
            # 기본값으로 모듈 생성
            Module.objects.create(project=project)

        if hasattr(self.initial_data, 'getlist'):
            allowed_roles = self.initial_data.getlist('allowed_roles')
            trackers = self.initial_data.getlist('trackers')
        else:
            allowed_roles = self.initial_data.get('allowed_roles')
            trackers = self.initial_data.get('trackers')

        if allowed_roles:
            project.allowed_roles.set(allowed_roles)
        if trackers:
            project.trackers.set(trackers)

        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        # 1. validated_data에서 모듈 필드 추출
        issue = validated_data.pop('issue', None)
        news = validated_data.pop('news', None)
        document = validated_data.pop('document', None)
        forum = validated_data.pop('forum', None)
        calendar = validated_data.pop('calendar', None)

        # 2. 모듈 업데이트 (권한 검증 포함)
        module_fields = ['issue', 'news', 'document', 'forum', 'calendar']
        if any(field in self.initial_data for field in module_fields):
            request = self.context.get('request')
            if request:
                PermissionService.check_module_permission(request.user, instance)

            try:
                module = instance.module
            except Module.DoesNotExist:
                module = Module.objects.create(project=instance)

            if issue is not None: module.issue = issue
            if news is not None: module.news = news
            if document is not None: module.document = document
            if forum is not None: module.forum = forum
            if calendar is not None: module.calendar = calendar
            module.save()

        # 3. initial_data를 사용하여 M2M 관계 업데이트
        if hasattr(self.initial_data, 'getlist'):
            allowed_roles = self.initial_data.getlist('allowed_roles')
            trackers = self.initial_data.getlist('trackers')
        else:
            allowed_roles = self.initial_data.get('allowed_roles')
            trackers = self.initial_data.get('trackers')

        if allowed_roles is not None:
            instance.allowed_roles.set(allowed_roles)
        if trackers is not None:
            instance.trackers.set(trackers)

        validated_data['status'] = self.initial_data.get('status', instance.status)

        return super().update(instance, validated_data)


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('pk', 'project', 'issue', 'news', 'document',
                  'forum', 'calendar')


class RoleSerializer(serializers.ModelSerializer):
    issue_visible_desc = serializers.CharField(source='get_issue_visible_display', read_only=True)
    user_visible_desc = serializers.CharField(source='get_user_visible_display', read_only=True)

    class Meta:
        model = Role
        fields = ('pk', 'name', 'assignable', 'issue_visible', 'issue_visible_desc', 'user_visible',
                  'user_visible_desc', 'permissions', 'category', 'order', 'creator', 'created', 'updated')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('pk', 'module', 'category', 'code', 'name', 'description')


class MemberSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    project = SimpleIssueProjectSerializer(read_only=True)
    roles = RoleInMemberSerializer(many=True, read_only=True)

    # 업데이트용 쓰기 전용 필드
    user_id = serializers.PrimaryKeyRelatedField(source='user', queryset=User.objects.all(),
                                                 write_only=True, required=False)
    slug = serializers.SlugField(write_only=True, required=False)
    role_ids = serializers.PrimaryKeyRelatedField(source='roles', queryset=Role.objects.all(),
                                                  many=True, write_only=True, required=False)

    class Meta:
        model = Member
        fields = ('pk', 'user', 'project', 'roles', 'created', 'user_id', 'slug', 'role_ids')

    def create(self, validated_data):
        slug = validated_data.pop('slug')
        roles = validated_data.pop('roles', [])

        project = IssueProject.objects.get(slug=slug)
        member = Member.objects.create(project=project, **validated_data)

        if roles:
            member.roles.set(roles)
        return member

    def update(self, instance, validated_data):
        roles = validated_data.pop('roles', None)

        # 유저 업데이트가 필요한 경우 처리
        if 'user' in validated_data:
            instance.user = validated_data['user']

        if roles is not None:
            instance.roles.set(roles)

        instance.save()
        return instance


class ProjectMemberUserSerializer(serializers.Serializer):
    """프로젝트 멤버 유저 정보 반환 (담당자 선택 드롭다운용)"""
    pk = serializers.IntegerField()  # Member pk
    user_id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    is_assignable = serializers.SerializerMethodField()

    @staticmethod
    def get_user_id(obj):
        return obj['user']['pk']

    @staticmethod
    def get_username(obj):
        return obj['user']['username']

    @staticmethod
    def get_roles(obj):
        return obj['roles']

    @staticmethod
    def get_is_assignable(obj):
        return any(role.get('assignable', False) for role in obj.get('roles', []))


class ProjectSubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = ProjectSubscription
        fields = ('pk', 'user', 'project', 'created_at')

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            target_user = validated_data.get('user')
            if not target_user or not (request.user.is_superuser or request.user.work_manager):
                validated_data['user'] = request.user
        return super().create(validated_data)


class VersionListSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)
    sharing_desc = serializers.CharField(source='get_sharing_display', read_only=True)
    is_default = serializers.SerializerMethodField(read_only=True)

    open_num = serializers.SerializerMethodField(read_only=True)
    closed_num = serializers.SerializerMethodField(read_only=True)
    total_num = serializers.SerializerMethodField(read_only=True)
    done_ratio = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Version
        fields = ('pk', 'project', 'name', 'status', 'status_desc', 'sharing',
                  'sharing_desc', 'effective_date', 'description', 'is_default',
                  'open_num', 'closed_num', 'total_num', 'done_ratio')

    @staticmethod
    def get_is_default(obj):
        default_ver = obj.project.default_version
        return True if default_ver and default_ver.pk == obj.pk else False

    @staticmethod
    def get_closed_num(obj):
        return obj.issues.filter(status__closed=True).count()

    @staticmethod
    def get_open_num(obj):
        return obj.issues.filter(status__closed=False).count()

    @staticmethod
    def get_total_num(obj):
        return obj.issues.count()

    def get_done_ratio(self, obj):
        # 1. 이슈가 아예 없는 경우
        total_num = self.get_total_num(obj)
        if total_num == 0:
            return 0
        # 2. 종료된 업무가 없는 경우
        closed_num = self.get_closed_num(obj)
        if closed_num == 0:
            return 0
        else:
            return round(closed_num / total_num * 100, 2)


class SimpleIssueSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    tracker = TrackerInIssueProjectSerializer(read_only=True)
    watchers = SimpleUserSerializer(many=True, read_only=True)
    expected_duration_display = serializers.CharField(source='get_expected_duration_display', read_only=True)

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'subject', 'status', 'tracker', 'priority',
                  'fixed_version', 'category', 'assigned_to', 'watchers',
                  'expected_duration', 'expected_duration_display', 'done_ratio', 'closed')


class VersionSerializer(VersionListSerializer):
    issues = SimpleIssueSerializer(many=True, read_only=True)

    class Meta(VersionListSerializer.Meta):
        fields = VersionListSerializer.Meta.fields + ('issues',)

    @transaction.atomic
    def create(self, validated_data):
        project = validated_data.get('project')
        if not project:
            project_slug = self.initial_data.get('project')
            if project_slug:
                try:
                    project = IssueProject.objects.get(slug=project_slug)
                    validated_data['project'] = project
                except IssueProject.DoesNotExist:
                    raise serializers.ValidationError({'project': 'Invalid project slug'})

        if not project:
            raise serializers.ValidationError({'project': 'Project is required'})

        is_default = self.initial_data.get('is_default', False)
        if isinstance(is_default, str):
            is_default = is_default.lower() in ['true', '1']

        version = Version.objects.create(**validated_data)
        if is_default:
            project.default_version = version
            project.save()
        return version

    @transaction.atomic
    def update(self, instance, validated_data):
        is_default = self.initial_data.get('is_default', False)
        if isinstance(is_default, str):
            is_default = is_default.lower() in ['true', '1']
        project = validated_data.get('project', instance.project)

        if is_default:
            project.default_version = instance
            project.save()

        return super().update(instance, validated_data)


class ProjectBookmarkSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_slug = serializers.CharField(source='project.slug', read_only=True)

    class Meta:
        model = ProjectBookmark
        fields = ('pk', 'user', 'project', 'project_name', 'project_slug', 'order', 'created')

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            if not validated_data.get('user') or not (
                    request.user.is_superuser or request.user.work_manager
            ):
                validated_data['user'] = request.user
        return super().create(validated_data)
