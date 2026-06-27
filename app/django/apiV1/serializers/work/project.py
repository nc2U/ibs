from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from work.models.issue import IssueCategory, Issue, Tracker
from work.models.project import IssueProject, Role, Member, Module, Permission, Version
from work.services.work_services import PermissionService

User = get_user_model()


class ProjectPermissionMixin:
    """
    Mixin to provide consistent project-level visibility and permission logic.
    """

    def get_visible(self, obj):
        if not obj:
            return False
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if user.is_superuser or user.work_manager:
                return True
            all_members = obj.all_members()
            members = [m['user']['pk'] for m in all_members]
            return obj.is_public or user.pk in members
        return False

    def get_my_perms(self, obj):
        if not obj:
            return []
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if user.is_superuser or user.work_manager:
                return list(Permission.objects.values_list('code', flat=True))

            all_members = obj.all_members()
            user_member = next((m for m in all_members if m['user']['pk'] == user.pk), None)

            if user_member:
                role_pks = [role['pk'] for role in user_member['roles']]
                perms = Permission.objects.filter(roles__in=role_pks).values_list('code', flat=True).distinct()
                return list(perms)
        return []


# Work --------------------------------------------------------------------------
class SimpleIssueProjectSerializer(ProjectPermissionMixin, serializers.ModelSerializer):
    visible = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'name', 'slug', 'visible')


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

    class Meta:
        model = Version
        fields = ('pk', 'name', 'status', 'status_desc', 'sharing', 'sharing_desc',
                  'is_default', 'effective_date', 'description')

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
    sub_projects = serializers.SerializerMethodField()
    all_members = MemberInIssueProjectSerializer(many=True, read_only=True)
    parent_visible = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'company', 'sort', 'name', 'slug', 'description', 'status', 'depth', 'is_public',
                  'module', 'creator', 'visible', 'my_perms', 'sub_projects', 'all_members',
                  'parent', 'parent_visible', 'created', 'updated')

    def get_sub_projects(self, obj):
        sub_projects = obj.issueproject_set.exclude(status='9')
        return IssueProjectListSerializer(sub_projects, many=True, read_only=True, context=self.context).data

    def get_parent_visible(self, obj):
        return self.get_visible(obj.parent) if obj.parent else False


class IssueProjectSerializer(ProjectPermissionMixin, serializers.ModelSerializer):
    family_tree = SimpleIssueProjectSerializer(many=True, read_only=True)
    module = ModuleInIssueProjectSerializer(read_only=True)
    all_members = MemberInIssueProjectSerializer(many=True, read_only=True)
    members = MemberInIssueProjectSerializer(many=True, read_only=True)
    allowed_roles = RoleInIssueProjectSerializer(many=True, read_only=True)
    trackers = TrackerInIssueProjectSerializer(many=True, read_only=True)
    versions = serializers.SerializerMethodField(read_only=True)
    categories = IssueCategoryInIssueProjectSerializer(many=True, read_only=True)
    visible = serializers.SerializerMethodField(read_only=True)
    parent_visible = serializers.SerializerMethodField(read_only=True)
    sub_projects = serializers.SerializerMethodField(read_only=True)
    creator = serializers.SlugRelatedField('username', read_only=True)
    my_perms = serializers.SerializerMethodField(read_only=True)

    # 모듈 설정을 위한 필드 추가 (write_only)
    issue = serializers.BooleanField(write_only=True, default=True)
    news = serializers.BooleanField(write_only=True, default=True)
    document = serializers.BooleanField(write_only=True, default=True)
    forum = serializers.BooleanField(write_only=True, default=True)
    calendar = serializers.BooleanField(write_only=True, default=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'company', 'sort', 'name', 'slug', 'description', 'homepage', 'is_public',
                  'module', 'is_inherit_members', 'allowed_roles', 'trackers', 'forums', 'versions',
                  'default_version', 'categories', 'status', 'depth', 'all_members', 'members',
                  'visible', 'family_tree', 'parent', 'parent_visible', 'sub_projects', 'creator',
                  'my_perms', 'created', 'updated', 'issue', 'news', 'document', 'forum', 'calendar')
        read_only_fields = ('status', 'is_public', 'forums')

    # 메서드 복구
    @staticmethod
    def get_versions(obj):
        versions = obj.versions.filter(status='1')
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

            module = instance.module
            if issue is not None: module.issue = issue
            if news is not None: module.news = news
            if document is not None: module.document = document
            if forum is not None: module.forum = forum
            if calendar is not None: module.calendar = calendar
            module.save()

        # 3. initial_data를 사용하여 M2M 관계 업데이트
        allowed_roles = self.initial_data.get('allowed_roles')
        if allowed_roles is not None:
            instance.allowed_roles.set(allowed_roles)

        trackers = self.initial_data.get('trackers')
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
    class Meta:
        model = Role
        fields = ('pk', 'name', 'assignable', 'issue_visible', 'user_visible',
                  'permissions', 'order', 'creator', 'created', 'updated')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('pk', 'module', 'code', 'name', 'description')


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


class IssueInVersionSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    tracker = TrackerInIssueProjectSerializer(read_only=True)
    watchers = SimpleUserSerializer(many=True, read_only=True)
    expected_duration_display = serializers.CharField(source='get_expected_duration_display', read_only=True)

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'subject', 'status', 'tracker', 'priority',
                  'fixed_version', 'category', 'assigned_to', 'watchers',
                  'expected_duration', 'expected_duration_display', 'done_ratio', 'closed')


class VersionSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)
    sharing_desc = serializers.CharField(source='get_sharing_display', read_only=True)
    is_default = serializers.SerializerMethodField(read_only=True)
    issues = IssueInVersionSerializer(many=True, read_only=True)

    project_slug = serializers.SlugRelatedField(
        slug_field='slug', queryset=IssueProject.objects.all(),
        source='project', write_only=True, required=False)

    class Meta:
        model = Version
        fields = ('pk', 'project', 'project_slug', 'name', 'status', 'status_desc', 'sharing', 'sharing_desc',
                  'effective_date', 'description', 'issues', 'is_default')

    @staticmethod
    def get_is_default(obj):
        default_ver = obj.project.default_version
        return True if default_ver and default_ver.pk == obj.pk else False

    @transaction.atomic
    def create(self, validated_data):
        is_default = self.initial_data.get('is_default', False)
        project = validated_data.get('project')

        if not project:
            raise serializers.ValidationError({'project': 'Project is required'})

        version = Version.objects.create(**validated_data)
        if is_default:
            project.default_version = version
            project.save()
        return version

    @transaction.atomic
    def update(self, instance, validated_data):
        is_default = self.initial_data.get('is_default', False)
        project = validated_data.get('project', instance.project)

        if is_default:
            project.default_version = instance
            project.save()

        return super().update(instance, validated_data)
