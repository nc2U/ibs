from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from work.models.issue import (IssueCategory, Tracker, CodeActivity, Issue)
from work.models.project import IssueProject, Role, Member, Module, Version


# Work --------------------------------------------------------------------------
class SimpleIssueProjectSerializer(serializers.ModelSerializer):
    visible = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'name', 'slug', 'visible')

    def get_visible(self, obj):
        request = self.context.get('request')

        if request and hasattr(request, 'user'):
            user = request.user
            visible_auth = user.work_manager or user.is_superuser
            all_members = obj.all_members()
            members = [m['user']['pk'] for m in all_members]
            return obj.is_public or user.pk in members or visible_auth
        else:
            return False


class RoleInMemberSerializer(serializers.ModelSerializer):
    inherited = serializers.BooleanField(read_only=True)

    class Meta:
        model = Role
        fields = ('pk', 'name', 'inherited')


class MemberInIssueProjectSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    roles = RoleInMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Member
        fields = ('pk', 'user', 'roles', 'created')


class ModuleInIssueProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('pk', 'project', 'issue', 'time', 'news', 'document',
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


class CodeActivityInIssueProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeActivity
        fields = ('pk', 'name', 'active', 'default', 'order')


class IssueProjectSerializer(serializers.ModelSerializer):
    family_tree = SimpleIssueProjectSerializer(many=True, read_only=True)
    module = ModuleInIssueProjectSerializer(read_only=True)
    all_members = MemberInIssueProjectSerializer(many=True, read_only=True)
    members = MemberInIssueProjectSerializer(many=True, read_only=True)
    allowed_roles = RoleInIssueProjectSerializer(many=True, read_only=True)
    trackers = TrackerInIssueProjectSerializer(many=True, read_only=True)
    versions = serializers.SerializerMethodField(read_only=True)
    categories = IssueCategoryInIssueProjectSerializer(many=True, read_only=True)
    activities = CodeActivityInIssueProjectSerializer(many=True, read_only=True)
    visible = serializers.SerializerMethodField(read_only=True)
    total_estimated_hours = serializers.SerializerMethodField(read_only=True)
    total_time_spent = serializers.SerializerMethodField(read_only=True)
    parent_visible = serializers.SerializerMethodField(read_only=True)
    sub_projects = serializers.SerializerMethodField()
    creator = serializers.SlugRelatedField('username', read_only=True)
    my_perms = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'company', 'sort', 'name', 'slug', 'description', 'homepage', 'is_public',
                  'module', 'is_inherit_members', 'allowed_roles', 'trackers', 'forums', 'versions',
                  'default_version', 'categories', 'status', 'depth', 'all_members', 'members',
                  'activities', 'visible', 'total_estimated_hours', 'total_time_spent', 'family_tree',
                  'parent', 'parent_visible', 'sub_projects', 'creator', 'my_perms', 'created', 'updated')
        read_only_fields = ('forums',)

    @staticmethod
    def get_versions(obj):
        versions = obj.versions.filter(status='1')
        return VersionInIssueProjectSerializer(versions, many=True).data

    def get_sub_projects(self, obj):
        sub_projects = obj.issueproject_set.exclude(status='9')
        request = self.context.get('request')

        # Create a new serializer class without the 'my_perms' field
        class SubProjectSerializer(self.__class__):
            class Meta(self.__class__.Meta):
                fields = tuple(
                    f for f in self.__class__.Meta.fields if
                    f not in ('company', 'module', 'allowed_roles', 'my_perms'))

        return SubProjectSerializer(sub_projects, many=True, read_only=True, context=self.context).data

    def get_visible(self, obj):
        request = self.context.get('request')

        if request and hasattr(request, 'user'):
            user = request.user
            visible_auth = user.work_manager or user.is_superuser
            all_members = obj.all_members()
            members = [m['user']['pk'] for m in all_members]
            return obj.is_public or user.pk in members or visible_auth
        else:
            return False

    def get_parent_visible(self, obj):
        return self.get_visible(obj.parent) if obj.parent else False

    def get_total_estimated_hours(self, obj):
        return self.recursive_estimated_hours(obj)

    def recursive_estimated_hours(self, project):
        total_hours = project.issue_set.aggregate(total=Sum('estimated_hours'))['total'] or 0
        sub_projects = project.issueproject_set.exclude(status='9')
        for sub_project in sub_projects:
            total_hours += self.recursive_estimated_hours(sub_project)
        return total_hours

    def get_total_time_spent(self, obj):
        return self.recursive_time_spent(obj)

    def recursive_time_spent(self, project):
        total_hours = project.timeentry_set.aggregate(total=Sum('hours'))['total'] or 0
        sub_projects = project.issueproject_set.exclude(status='9')
        for sub_project in sub_projects:
            total_hours += self.recursive_time_spent(sub_project)
        return total_hours

    def get_my_perms(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if user.is_superuser or user.work_manager:
                return list(Permission.objects.values_list('code', flat=True))

            # Find user in all members (including inherited)
            all_members = obj.all_members()
            user_member = next((m for m in all_members if m['user']['pk'] == user.pk), None)
            
            if user_member:
                # Extract role PKs from user_member
                role_pks = [role['pk'] for role in user_member['roles']]
                # Get unique permission codes associated with these roles
                perms = Permission.objects.filter(roles__in=role_pks).values_list('code', flat=True).distinct()
                return list(perms)
        return []

    @transaction.atomic
    def create(self, validated_data):
        # M2M 필드 분리
        allowed_roles = self.initial_data.get('allowed_roles', [])
        trackers = self.initial_data.get('trackers', [])
        activities = self.initial_data.get('activities', [])

        # 프로젝트 생성
        project = IssueProject.objects.create(**validated_data)

        # M2M 연결 (프로젝트 생성시 설정된 기본 역할 및 유형 추가)
        if allowed_roles:
            project.allowed_roles.set(allowed_roles)
        if trackers:
            project.trackers.set(trackers)
        if activities:
            project.activities.set(activities)

        Module.objects.create(project=project,
                              issue=self.initial_data.get('issue', True),
                              time=self.initial_data.get('time', True),
                              news=self.initial_data.get('news', True),
                              document=self.initial_data.get('document', True),
                              forum=self.initial_data.get('forum', True),
                              calendar=self.initial_data.get('calendar', True))
        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        def ids_differ(qs, incoming):
            return set(qs.values_list('pk', flat=True)) != set(map(int, incoming))

        # M2M 업데이트 (역할 및 유형이 있는 경우 업데이트 로직)
        allowed_roles = self.initial_data.get('allowed_roles', [])
        if allowed_roles and ids_differ(instance.allowed_roles, allowed_roles):
            instance.allowed_roles.set(allowed_roles)

        trackers = self.initial_data.get('trackers', [])
        if trackers and ids_differ(instance.trackers, trackers):
            instance.trackers.set(trackers)

        activities = self.initial_data.get('activities', [])
        if activities and ids_differ(instance.activities, activities):
            instance.activities.set(activities)

        # 모듈 필드 업데이트
        module = instance.module
        for field in ['issue', 'time', 'news', 'document', 'forum', 'calendar']:
            if field in self.initial_data:
                setattr(module, field, self.initial_data[field])
        module.save()

        # user에 대응하는 member 모델 생성
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

        # 상태 업데이트
        validated_data['status'] = self.initial_data.get('status', '1')

        return super().update(instance, validated_data)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('pk', 'name', 'assignable', 'issue_visible', 'time_entry_visible', 'user_visible',
                  'default_time_activity', 'order', 'creator', 'created', 'updated')


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
        fields = ('pk', 'project', 'issue', 'time', 'news', 'document',
                  'forum', 'calendar')


class IssueInVersionSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    tracker = TrackerInIssueProjectSerializer(read_only=True)
    watchers = SimpleUserSerializer(many=True, read_only=True)
    spent_times = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'subject', 'status', 'tracker', 'priority',
                  'fixed_version', 'category', 'assigned_to', 'watchers',
                  'estimated_hours', 'spent_times', 'done_ratio', 'closed')

    @staticmethod
    def get_spent_times(obj):
        return obj.timeentry_set.aggregate(total=Sum('hours'))['total'] or 0


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
