from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from work.models.issue import IssueCategory, Issue, Tracker
from work.models.project import IssueProject, Role, Member, Module, Permission, Version


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
    # ... (기존 필드들)
    
    # 모듈 설정을 위한 필드 추가 (write_only)
    issue = serializers.BooleanField(write_only=True, default=True)
    news = serializers.BooleanField(write_only=True, default=True)
    document = serializers.BooleanField(write_only=True, default=True)
    forum = serializers.BooleanField(write_only=True, default=True)
    calendar = serializers.BooleanField(write_only=True, default=True)
    
    # m2m 필드 명시 (write_only로 처리)
    allowed_roles = serializers.PrimaryKeyRelatedField(many=True, queryset=Role.objects.all(), required=False)
    trackers = serializers.PrimaryKeyRelatedField(many=True, queryset=Tracker.objects.all(), required=False)

    class Meta:
        model = IssueProject
        # ... (기존 필드들)
        fields = ('pk', 'company', 'sort', 'name', 'slug', 'description', 'homepage', 'is_public',
                  'module', 'is_inherit_members', 'allowed_roles', 'trackers', 'forums', 'versions',
                  'default_version', 'categories', 'status', 'depth', 'all_members', 'members',
                  'visible', 'family_tree',
                  'parent', 'parent_visible', 'sub_projects', 'creator', 'my_perms', 'created', 'updated',
                  'issue', 'news', 'document', 'forum', 'calendar')
        read_only_fields = ('status', 'is_public', 'forums')

    # ... (나머지 메서드들)

    @transaction.atomic
    def create(self, validated_data):
        # validated_data에서 추가 필드 추출
        issue = validated_data.pop('issue', True)
        news = validated_data.pop('news', True)
        document = validated_data.pop('document', True)
        forum = validated_data.pop('forum', True)
        calendar = validated_data.pop('calendar', True)
        
        allowed_roles = validated_data.pop('allowed_roles', [])
        trackers = validated_data.pop('trackers', [])

        project = IssueProject.objects.create(**validated_data)

        if allowed_roles:
            project.allowed_roles.set(allowed_roles)
        if trackers:
            project.trackers.set(trackers)

        Module.objects.create(
            project=project,
            issue=issue,
            news=news,
            document=document,
            forum=forum,
            calendar=calendar
        )
        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        # validated_data에서 필드 추출
        issue = validated_data.pop('issue', None)
        news = validated_data.pop('news', None)
        document = validated_data.pop('document', None)
        forum = validated_data.pop('forum', None)
        calendar = validated_data.pop('calendar', None)
        
        allowed_roles = validated_data.pop('allowed_roles', None)
        trackers = validated_data.pop('trackers', None)

        # M2M 필드 업데이트
        if allowed_roles is not None:
            instance.allowed_roles.set(allowed_roles)
        if trackers is not None:
            instance.trackers.set(trackers)

        # 모듈 업데이트
        module = instance.module
        module_fields = {
            'issue': issue,
            'news': news,
            'document': document,
            'forum': forum,
            'calendar': calendar
        }
        for field, value in module_fields.items():
            if value is not None:
                setattr(module, field, value)
        module.save()

        # 멤버 및 상태 처리는 아직 분리되지 않았으므로 유지하되, 
        # 가능한 부분은 validated_data를 사용하도록 개선 (기존 로직 유지)
        users = self.initial_data.get('users', [])
        roles = self.initial_data.get('roles', [])
        del_mem = self.initial_data.get('del_mem')

        if users:
            for user_id in users:
                member, _ = Member.objects.get_or_create(user_id=user_id, project=instance)
                if roles:
                    member.roles.set(roles)
                member.save()
        elif del_mem is not None:
            Member.objects.filter(pk=del_mem).delete()

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

    class Meta:
        model = Member
        fields = ('pk', 'user', 'project', 'roles', 'created')

    def create(self, validated_data):
        user = self.initial_data.get('user', None)
        slug = self.initial_data.get('slug', None)
        project = IssueProject.objects.get(slug=slug)
        member = Member(user_id=user, project=project)
        member.save()
        roles = self.initial_data.get('roles', [])
        member.roles.set(roles)
        return member

    def update(self, instance, validated_data):
        user = self.initial_data.get('user', None)
        roles = self.initial_data.get('roles', [])
        instance.user_id = user if user else instance.user.id
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

    class Meta:
        model = Version
        fields = ('pk', 'project', 'name', 'status', 'status_desc', 'sharing', 'sharing_desc',
                  'effective_date', 'description', 'issues', 'is_default')

    @staticmethod
    def get_is_default(obj):
        default_ver = obj.project.default_version
        return True if default_ver and default_ver.pk == obj.pk else False

    @transaction.atomic
    def create(self, validated_data):
        project_slug = self.initial_data.get('project')
        try:
            project = IssueProject.objects.get(slug=project_slug)
        except IssueProject.DoesNotExist:
            raise serializers.ValidationError({'project': 'Project does not exist'})

        version = Version.objects.create(**validated_data, project=project)
        is_default = self.initial_data.get('is_default', False)
        if is_default:
            project.default_version = version
            project.save()
        return version

    @transaction.atomic
    def update(self, instance, validated_data):
        project_slug = self.initial_data.get('project')
        try:
            project = IssueProject.objects.get(slug=project_slug)
            is_default = self.initial_data.get('is_default', False)
            default_version = instance if is_default else None
            project.default_version = default_version
            project.save()
        except IssueProject.DoesNotExist:
            raise serializers.ValidationError({'project': 'Project does not exist'})

        instance.__dict__.update(validated_data)
        instance.project = project
        instance.save()
        return instance
