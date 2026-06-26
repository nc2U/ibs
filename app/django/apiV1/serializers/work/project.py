from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from work.models.issue import (IssueCategory, Tracker, Issue, Version)
from work.models.project import IssueProject, Role, Member, Module, Permission


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
    sub_projects = serializers.SerializerMethodField()
    creator = serializers.SlugRelatedField('username', read_only=True)
    my_perms = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'company', 'sort', 'name', 'slug', 'description', 'homepage', 'is_public',
                  'module', 'is_inherit_members', 'allowed_roles', 'trackers', 'forums', 'versions',
                  'default_version', 'categories', 'status', 'depth', 'all_members', 'members',
                  'visible', 'family_tree',
                  'parent', 'parent_visible', 'sub_projects', 'creator', 'my_perms', 'created', 'updated')
        read_only_fields = ('status', 'is_public', 'forums')

    @staticmethod
    def get_versions(obj):
        versions = obj.versions.filter(status='1')
        return VersionInIssueProjectSerializer(versions, many=True).data

    def get_sub_projects(self, obj):
        sub_projects = obj.issueproject_set.exclude(status='9')
        # Create a new serializer class without the 'my_perms' field to avoid recursion bloat if needed
        # but for now reusing ListSerializer is fine as it's meant for tree view
        return IssueProjectListSerializer(sub_projects, many=True, read_only=True, context=self.context).data

    def get_parent_visible(self, obj):
        return self.get_visible(obj.parent) if obj.parent else False

    @transaction.atomic
    def create(self, validated_data):
        allowed_roles = self.initial_data.get('allowed_roles', [])
        trackers = self.initial_data.get('trackers', [])

        project = IssueProject.objects.create(**validated_data)

        if allowed_roles:
            project.allowed_roles.set(allowed_roles)
        if trackers:
            project.trackers.set(trackers)

        Module.objects.create(project=project,
                              issue=self.initial_data.get('issue', True),
                              news=self.initial_data.get('news', True),
                              document=self.initial_data.get('document', True),
                              forum=self.initial_data.get('forum', True),
                              calendar=self.initial_data.get('calendar', True))
        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        def ids_differ(qs, incoming):
            return set(qs.values_list('pk', flat=True)) != set(map(int, incoming))

        allowed_roles = self.initial_data.get('allowed_roles', [])
        if allowed_roles and ids_differ(instance.allowed_roles, allowed_roles):
            instance.allowed_roles.set(allowed_roles)

        trackers = self.initial_data.get('trackers', [])
        if trackers and ids_differ(instance.trackers, trackers):
            instance.trackers.set(trackers)

        module = instance.module
        for field in ['issue', 'news', 'document', 'forum', 'calendar']:
            if field in self.initial_data:
                setattr(module, field, self.initial_data[field])
        module.save()

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

        validated_data['status'] = self.initial_data.get('status', '1')

        return super().update(instance, validated_data)


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('pk', 'module', 'code', 'name', 'description')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('pk', 'name', 'assignable', 'issue_visible', 'user_visible',
                  'permissions', 'order', 'creator', 'created', 'updated')


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


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('pk', 'project', 'issue', 'news', 'document',
                  'forum', 'calendar')
