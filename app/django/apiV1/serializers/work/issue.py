import json
import os.path

from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer, TrackerInIssueProjectSerializer
from work.models.issue import (IssueCategory, Tracker, IssueStatus, Workflow,
                               CodeIssuePriority, Issue, IssueRelation,
                               IssueFile, IssueComment, Version)
from work.models.project import IssueProject

from work.models.meeting import Meeting


class MeetingInIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = ('pk', 'title')


class IssueStatusInIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueStatus
        fields = ('pk', 'name', 'closed')


class CodePriorityInIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeIssuePriority
        fields = ('pk', 'name')


class VersionInIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ('pk', 'name')


class IssueFileInIssueSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueFile
        fields = ('pk', 'file', 'file_name', 'file_type', 'file_size', 'description', 'created', 'creator')


class IssueInIssueSerializer(serializers.ModelSerializer):
    tracker = serializers.SlugRelatedField(slug_field='name', read_only=True)
    status = serializers.SlugRelatedField(slug_field='name', read_only=True)
    assigned_to = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = ('pk', 'subject', 'tracker', 'status', 'assigned_to',
                  'start_date', 'due_date', 'done_ratio', 'closed')


class IssueRelationInIssueSerializer(serializers.ModelSerializer):
    issue = IssueInIssueSerializer(source='issue_to', read_only=True)

    class Meta:
        model = IssueRelation
        fields = ('pk', 'issue', 'delay')


class IssueRelationIncomingSerializer(serializers.ModelSerializer):
    issue = IssueInIssueSerializer(read_only=True)

    class Meta:
        model = IssueRelation
        fields = ('pk', 'issue', 'delay')


class IssueSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    tracker = TrackerInIssueProjectSerializer(read_only=True)
    status = IssueStatusInIssueSerializer(read_only=True)
    priority = CodePriorityInIssueSerializer(read_only=True)
    fixed_version = VersionInIssueSerializer(read_only=True)
    assigned_to = SimpleUserSerializer(read_only=True)
    watchers = SimpleUserSerializer(many=True, read_only=True)
    files = IssueFileInIssueSerializer(many=True, read_only=True)
    meeting_desc = MeetingInIssueSerializer(source='meeting', read_only=True)
    sub_issues = serializers.SerializerMethodField()
    outgoing_relations = serializers.SerializerMethodField()
    incoming_relation = serializers.SerializerMethodField()
    creator = SimpleUserSerializer(read_only=True)
    expected_duration_display = serializers.CharField(source='get_expected_duration_display', read_only=True)

    # updater = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'tracker', 'status', 'priority', 'subject', 'description',
                  'category', 'fixed_version', 'assigned_to', 'parent', 'watchers', 'is_private',
                  'expected_duration', 'expected_duration_display', 'start_date', 'due_date',
                  'done_ratio', 'closed', 'files', 'sub_issues', 'outgoing_relations', 'incoming_relation',
                  'creator', 'updater', 'created', 'updated', 'meeting', 'meeting_desc')

    @staticmethod
    def get_sub_issues(obj):
        return IssueInIssueSerializer(obj.issue_set.all().order_by('id'), many=True, read_only=True).data

    @staticmethod
    def get_outgoing_relations(obj):
        return IssueRelationInIssueSerializer(obj.outgoing_relations.all().order_by('id'), many=True,
                                              read_only=True).data

    @staticmethod
    def get_incoming_relation(obj):
        if hasattr(obj, 'incoming_relation'):
            return IssueRelationIncomingSerializer(obj.incoming_relation, read_only=True).data
        return None

    @transaction.atomic
    def create(self, validated_data):
        project = IssueProject.objects.get(slug=self.initial_data.get('project', None))
        tracker = Tracker.objects.get(pk=self.initial_data.get('tracker'))
        status = IssueStatus.objects.get(pk=self.initial_data.get('status'))
        priority = CodeIssuePriority.objects.get(pk=self.initial_data.get('priority'))
        fixed_version = self.initial_data.get('fixed_version')
        fixed_version = fixed_version if fixed_version else None
        assigned_to = self.initial_data.get('assigned_to', None)
        assigned_to = User.objects.get(pk=assigned_to) if assigned_to else None

        # Pop 'watchers' from validated_data to avoid KeyError
        issue = Issue.objects.create(project=project,
                                     tracker=tracker,
                                     status=status,
                                     priority=priority,
                                     fixed_version_id=fixed_version,
                                     assigned_to=assigned_to,
                                     **validated_data)
        # Set the watchers of the instance to the list of watchers
        creator = self.context['request'].user
        issue.watchers.add(creator.pk)
        watchers = self.initial_data.getlist('watchers', [])
        if watchers:
            for watcher in watchers:
                issue.watchers.add(watcher)
        # File 처리
        new_files = self.initial_data.getlist('new_files', [])
        descriptions = self.initial_data.getlist('descriptions', [])
        if new_files:
            for i, file in enumerate(new_files):
                issue_file = IssueFile(issue=issue, file=file,
                                       description=descriptions[i], creator=creator)
                issue_file.save()
        return issue

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        if self.initial_data.get('project', None):
            instance.project = IssueProject.objects.get(slug=self.initial_data.get('project', None))
        if self.initial_data.get('tracker'):
            instance.tracker = Tracker.objects.get(pk=self.initial_data.get('tracker'))
        if self.initial_data.get('status'):
            instance.status = IssueStatus.objects.get(pk=self.initial_data.get('status'))
        if instance.closed is None and instance.status.closed:
            instance.closed = timezone.localtime()
        elif instance.closed is not None and not instance.status.closed:
            instance.closed = None
        if self.initial_data.get('priority'):
            instance.priority = CodeIssuePriority.objects.get(pk=self.initial_data.get('priority'))
        if self.initial_data.get('fixed_version'):
            instance.fixed_version = Version.objects.get(pk=self.initial_data.get('fixed_version'))
        assigned_to = self.initial_data.get('assigned_to', None)
        instance.assigned_to = User.objects.get(pk=assigned_to) if assigned_to else None

        # 공유자 업데이트
        watchers = self.initial_data.getlist('watchers', [])
        if watchers:
            watcher_ids = [int(w) for w in watchers]
            valid_watchers = User.objects.filter(pk__in=watcher_ids)
            instance.watchers.add(*valid_watchers)

        del_watcher = self.initial_data.get('del_watcher', None)
        if del_watcher:
            instance.watchers.remove(del_watcher)

        # sub_issue 관계 지우기
        del_child = self.initial_data.get('del_child', None)
        if del_child:
            child = instance.issue_set.get(pk=del_child)
            child.parent = None
            child.save()

        # issue_comment logic
        comment_content = self.initial_data.get('comment_content', None)
        creator = self.context['request'].user
        if comment_content:
            IssueComment.objects.create(issue=instance, content=comment_content, creator=creator)

        # File 처리
        new_files = self.initial_data.getlist('new_files', [])
        descriptions = self.initial_data.getlist('descriptions', [])

        if new_files:
            for i, file in enumerate(new_files):
                issue_file = IssueFile(issue=instance, file=file,
                                       description=descriptions[i], creator=creator)
                issue_file.save()

        old_files = self.initial_data.getlist('files', [])
        if old_files:
            for json_file in old_files:
                file = json.loads(json_file)
                file_object = IssueFile.objects.get(pk=file.get('pk'))

                if file.get('del'):
                    file_object.delete()

        edit_file = self.initial_data.get('edit_file', None)  # pk
        cng_file = self.initial_data.get('cng_file', None)  # change file
        edit_file_desc = self.initial_data.get('edit_file_desc', None)
        if edit_file:
            file = IssueFile.objects.get(pk=edit_file)
            if cng_file:
                old_file = file.file
                if os.path.isfile(old_file.path):
                    os.remove(old_file.path)
                file.file = cng_file
            if edit_file_desc:
                file.description = edit_file_desc
            file.save()

        del_file = self.initial_data.get('del_file', None)
        if del_file:
            file = IssueFile.objects.get(pk=del_file)
            file.delete()

        return super().update(instance, validated_data)


class IssueCountByMemberSerializer(serializers.Serializer):
    open_charged = serializers.IntegerField(read_only=True)
    closed_charged = serializers.IntegerField(read_only=True)
    all_charged = serializers.IntegerField(read_only=True)
    open_created = serializers.IntegerField(read_only=True)
    closed_created = serializers.IntegerField(read_only=True)
    all_created = serializers.IntegerField(read_only=True)


class IssueRelationSerializer(serializers.ModelSerializer):
    target = IssueInIssueSerializer(read_only=True)

    class Meta:
        model = IssueRelation
        fields = ('pk', 'source', 'target', 'delay')

    @transaction.atomic
    def create(self, validated_data):
        target_pk = self.initial_data.get('target', None)
        target = Issue.objects.get(pk=target_pk) if target_pk else None
        try:
            # validated_data에 이미 source가 있다면 그 값을 사용하고,
            # 없다면 initial_data에서 가져오도록 보완
            source_pk = validated_data.get('source') or self.initial_data.get('source')
            source = Issue.objects.get(pk=source_pk.pk if hasattr(source_pk, 'pk') else source_pk)

            return IssueRelation.objects.create(
                source=source,
                target=target,
                delay=validated_data.get('delay')
            )
        except IntegrityError:
            raise serializers.ValidationError("해당 업무는 이미 등록되어 있는 연결된 업무입니다.")


class IssueInRelatedSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    tracker = serializers.SlugRelatedField(slug_field='name', read_only=True)
    status = IssueStatusInIssueSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'tracker', 'status', 'subject', 'description')


class IssueFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueFile
        fields = ('pk', 'issue', 'file', 'description', 'created')


class IssueCommentSerializer(serializers.ModelSerializer):
    issue = IssueInRelatedSerializer(read_only=True)
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueComment
        fields = ('pk', 'issue', 'content', 'is_private', 'created', 'updated', 'creator')


class TrackerSerializer(serializers.ModelSerializer):
    projects = SimpleIssueProjectSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Tracker
        fields = ('pk', 'name', 'description', 'is_in_roadmap', 'default_status',
                  'projects', 'order', 'creator', 'created', 'updated')


class IssueCategorySerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)

    class Meta:
        model = IssueCategory
        fields = ('pk', 'project', 'name', 'assigned_to')

    @transaction.atomic
    def create(self, validated_data):
        project_slug = self.initial_data.get('project')
        try:
            project = IssueProject.objects.get(slug=project_slug)
        except IssueProject.DoesNotExist:
            raise serializers.ValidationError({'project': 'Project does not exist'})

        category = IssueCategory.objects.create(**validated_data, project=project)
        return category

    @transaction.atomic
    def update(self, instance, validated_data):
        project_slug = self.initial_data.get('project')
        try:
            project = IssueProject.objects.get(slug=project_slug)
        except IssueProject.DoesNotExist:
            raise serializers.ValidationError({'project': 'Project does not exist'})

        instance.__dict__.update(**validated_data)
        instance.project = project
        instance.assigned_to = validated_data.get('assigned_to', instance.assigned_to)
        instance.save()
        return instance


class IssueCountByTrackerSerializer(serializers.ModelSerializer):
    open = serializers.SerializerMethodField()
    closed = serializers.SerializerMethodField()

    class Meta:
        model = Tracker
        fields = ['pk', 'name', 'open', 'closed']

    def get_open(self, obj):
        issues = Issue.objects.filter(tracker=obj, closed__isnull=True)
        # Access the request object from context
        request = self.context.get('request')
        issues = self.filter_project(request, issues)
        return issues.count()

    def get_closed(self, obj):
        issues = Issue.objects.filter(tracker=obj).exclude(closed__isnull=True)
        # Access the request object from context
        request = self.context.get('request')
        issues = self.filter_project(request, issues)
        return issues.count()

    def get_sub_projects(self, parent):
        sub_projects = []

        children = IssueProject.objects.filter(parent=parent)
        for child in children:
            sub_projects.append(child)
            sub_projects.extend(self.get_sub_projects(child))
        return sub_projects

    def filter_project(self, request, issues):
        project_id = request.query_params.get('projects')
        if not project_id:
            return issues  # 프로젝트 ID가 제공되지 않은 경우, 필터링 없이 반환

        try:
            project = IssueProject.objects.get(pk=project_id)
        except IssueProject.DoesNotExist:
            return issues  # 유효하지 않은 프로젝트 ID인 경우, 필터링 없이 반환

        sub_projects = self.get_sub_projects(project)
        slugs = [project.slug] + [sub.slug for sub in sub_projects]

        return issues.filter(project__slug__in=slugs)


class IssueStatusSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueStatus
        fields = ('pk', 'name', 'description', 'closed', 'order', 'creator', 'created', 'updated')


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ('pk', 'role', 'tracker', 'old_status', 'new_statuses')


class CodeIssuePrioritySerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = CodeIssuePriority
        fields = ('pk', 'name', 'active', 'default', 'order', 'creator', 'created', 'updated')
