from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import serializers

from _utils.file_service import FileService
from accounts.models import User
from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer, TrackerInIssueProjectSerializer
from work.models.issue import (IssueCategory, Tracker, IssueStatus,
                               Workflow, CodeIssuePriority, Issue,
                               IssueRelation, IssueFile, IssueComment)
from work.models.meeting import Meeting
from work.models.project import IssueProject, Version


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
        fields = ('pk', 'name', 'description')


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
    issue = IssueInIssueSerializer(source='target', read_only=True)

    class Meta:
        model = IssueRelation
        fields = ('pk', 'issue', 'delay')


class IssueRelationIncomingSerializer(serializers.ModelSerializer):
    issue = IssueInIssueSerializer(source='source', read_only=True)

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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        user = self.context['request'].user
        
        # 슈퍼유저나 work_manager는 패스
        if user.is_superuser or getattr(user, 'work_manager', False):
            return ret
            
        # 해당 업무와 특별한 관계가 없고, 'issue.watcher_read' 권한도 없는 경우
        user_perms = instance.project.get_user_permissions(user)
        is_related = (
            user == instance.creator or 
            user == instance.assigned_to or 
            instance.watchers.filter(pk=user.id).exists()
        )
        if not is_related and 'issue.watcher_read' not in user_perms:
            ret['watchers'] = []
            
        return ret

    def validate(self, attrs):
        user = self.context['request'].user
        
        # 이미 생성된 업무의 관람자 변경 시도(Update) 시 검증 가드 작동
        if self.instance:
            project = self.instance.project
            creator = self.instance.creator
            assigned_to = self.instance.assigned_to
            user_perms = project.get_user_permissions(user)

            # 1. 요청으로 들어온 watchers 목록과 del_watcher 파싱
            req_watchers = []
            if hasattr(self.initial_data, 'getlist'):
                req_watchers = self.initial_data.getlist('watchers')
            else:
                req_watchers = self.initial_data.get('watchers', [])
                
            del_watcher = self.initial_data.get('del_watcher', None)
            
            # ID 리스트 추출
            req_watcher_ids = [int(w) for w in req_watchers if str(w).isdigit()]
            del_watcher_id = int(del_watcher) if del_watcher and str(del_watcher).isdigit() else None

            # 2. 정밀 대조: 이미 등록되어 있는 관람자를 제외한 '진짜 신규 추가 유저' 목록만 추출
            existing_watcher_ids = set(self.instance.watchers.values_list('id', flat=True))
            new_watcher_ids = [w_id for w_id in req_watcher_ids if w_id not in existing_watcher_ids]

            # 3. 타인을 관람자로 신규 추가하려는지 여부 판별
            adding_others = False
            for w_id in new_watcher_ids:
                if w_id != user.id:
                    adding_others = True
                    break

            # 4. 타인을 관람자 목록에서 삭제하려는지 여부 판별
            removing_others = False
            if del_watcher_id and del_watcher_id != user.id:
                removing_others = True

            # 5. 권한 통제 판단
            # 슈퍼유저, work_manager, 업무 생성자(creator), 업무 담당자(assigned_to)는 무조건 프리패스
            is_responsible_user = (
                user.is_superuser or 
                getattr(user, 'work_manager', False) or 
                user == creator or 
                user == assigned_to
            )

            if not is_responsible_user:
                # (A) 타인을 추가하려고 시도할 때 ☞ watcher_create 권한 필요
                if adding_others:
                    if 'issue.watcher_create' not in user_perms:
                        from rest_framework.exceptions import ValidationError
                        raise ValidationError("다른 사용자를 관람자로 추가할 권한이 없습니다.")

                # (B) 타인을 삭제하려고 시도할 때 ☞ watcher_delete 권한 필요
                if removing_others:
                    if 'issue.watcher_delete' not in user_perms:
                        from rest_framework.exceptions import ValidationError
                        raise ValidationError("다른 사용자를 관람자에서 제거할 권한이 없습니다.")

        return attrs

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

        if hasattr(self.initial_data, 'getlist'):
            watchers = self.initial_data.getlist('watchers')
        else:
            watchers = self.initial_data.get('watchers', [])

        if watchers:
            for watcher in watchers:
                issue.watchers.add(watcher)
        # File 처리
        FileService.manage_files(
            instance=issue,
            initial_data=self.initial_data,
            creator=creator,
            file_model=IssueFile,
            related_name='issue'
        )
        return issue

    @transaction.atomic
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if self.initial_data.get('project', None):
            instance.project = IssueProject.objects.get(slug=self.initial_data.get('project', None))
        if self.initial_data.get('tracker'):
            instance.tracker = Tracker.objects.get(pk=self.initial_data.get('tracker'))
        if self.initial_data.get('status'):
            instance.status = IssueStatus.objects.get(pk=self.initial_data.get('status'))
            if instance.status.closed:
                if not instance.closed:
                    instance.closed = timezone.localtime()
            else:
                instance.closed = None
        if self.initial_data.get('priority'):
            instance.priority = CodeIssuePriority.objects.get(pk=self.initial_data.get('priority'))

        if 'fixed_version' in self.initial_data:
            fixed_version = self.initial_data.get('fixed_version')
            instance.fixed_version = Version.objects.get(pk=fixed_version) if fixed_version else None

        if 'assigned_to' in self.initial_data:
            assigned_to = self.initial_data.get('assigned_to', None)
            instance.assigned_to = User.objects.get(pk=assigned_to) if assigned_to else None

        # 공유자 업데이트
        if hasattr(self.initial_data, 'getlist'):
            watchers = self.initial_data.getlist('watchers')
        else:
            watchers = self.initial_data.get('watchers', [])

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
            child = instance.issue_set.filter(pk=del_child).first()
            if child:
                child.parent = None
                child.save()

        # issue_comment logic
        comment_content = self.initial_data.get('comment_content', None)
        creator = self.context['request'].user
        if comment_content:
            IssueComment.objects.create(issue=instance, content=comment_content, creator=creator)

        # File 처리
        FileService.manage_files(
            instance=instance,
            initial_data=self.initial_data,
            creator=creator,
            file_model=IssueFile,
            related_name='issue'
        )

        instance.save()
        return instance


class IssueCountByMemberSerializer(serializers.Serializer):
    open_charged = serializers.IntegerField(read_only=True)
    closed_charged = serializers.IntegerField(read_only=True)
    all_charged = serializers.IntegerField(read_only=True)
    open_created = serializers.IntegerField(read_only=True)
    closed_created = serializers.IntegerField(read_only=True)
    all_created = serializers.IntegerField(read_only=True)


class IssueRelationSerializer(serializers.ModelSerializer):
    target = IssueInIssueSerializer(read_only=True)
    source = IssueInIssueSerializer(read_only=True)

    class Meta:
        model = IssueRelation
        fields = ('pk', 'source', 'target', 'delay')

    @transaction.atomic
    def create(self, validated_data):
        target_pk = self.initial_data.get('target', None)
        try:
            target = Issue.objects.get(pk=target_pk) if target_pk else None
        except Issue.DoesNotExist:
            raise serializers.ValidationError({'target': '존재하지 않는 업무입니다.'})

        source_pk = self.initial_data.get('source', None)
        try:
            source = Issue.objects.get(pk=source_pk) if source_pk else None
        except Issue.DoesNotExist:
            raise serializers.ValidationError({'source': '존재하지 않는 업무입니다.'})

        if not source:
            raise serializers.ValidationError({'source': '이 필드는 필수입니다.'})
        if not target:
            raise serializers.ValidationError({'target': '이 필드는 필수입니다.'})

        if source == target:
            raise serializers.ValidationError("자기 자신과는 연결 관계를 맺을 수 없습니다.")

        try:
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
            if isinstance(project_slug, int) or (isinstance(project_slug, str) and project_slug.isdigit()):
                project = IssueProject.objects.get(pk=int(project_slug))
            else:
                project = IssueProject.objects.get(slug=project_slug)
        except IssueProject.DoesNotExist:
            raise serializers.ValidationError({'project': 'Project does not exist'})

        category = IssueCategory.objects.create(**validated_data, project=project)
        return category

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        project_slug = self.initial_data.get('project')
        if project_slug:
            try:
                if isinstance(project_slug, int) or (isinstance(project_slug, str) and project_slug.isdigit()):
                    project = IssueProject.objects.get(pk=int(project_slug))
                else:
                    project = IssueProject.objects.get(slug=project_slug)
                instance.project = project
                instance.save()
            except IssueProject.DoesNotExist:
                raise serializers.ValidationError({'project': 'Project does not exist'})
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

    def filter_project(self, request, issues):
        project_id = request.query_params.get('projects')
        if not project_id:
            return issues  # 프로젝트 ID가 제공되지 않은 경우, 필터링 없이 반환

        # 1. 이미 이전 루프에서 모아둔 캐시가 있다면 재사용
        if hasattr(self, '_project_slugs_cache'):
            return issues.filter(project__slug__in=self._project_slugs_cache)

        try:
            project = IssueProject.objects.get(pk=project_id)
        except IssueProject.DoesNotExist:
            return issues  # 유효하지 않은 프로젝트 ID인 경우, 필터링 없이 반환

        # 2. 단 한 번의 쿼리로 모든 프로젝트를 메모리에 로드
        all_projects = list(IssueProject.objects.all())

        # 3. DB 히트 없이 메모리에서 자식 노드 재귀 수집
        sub_projects_slugs = []
        def collect_children(parent_obj):
            for p in all_projects:
                if p.parent_id == parent_obj.id:
                    sub_projects_slugs.append(p.slug)
                    collect_children(p)

        collect_children(project)
        slugs = [project.slug] + sub_projects_slugs

        # 4. 캐싱 처리
        self._project_slugs_cache = slugs

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
