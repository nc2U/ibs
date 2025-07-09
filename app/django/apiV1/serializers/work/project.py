from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from work.models.issue import (IssueCategory, Tracker, CodeActivity, Issue)
from work.models.project import IssueProject, Role, Member, Module, Version


# from work.models.project import IssueProject, Role, Permission, Member, Module, Version


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
                  'file', 'wiki', 'repository', 'forum', 'calendar', 'gantt')


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
                  'is_default', 'effective_date', 'description', 'wiki_page_title')

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
    user = serializers.SlugRelatedField('username', read_only=True)
    my_perms = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'company', 'sort', 'name', 'slug', 'description', 'homepage', 'is_public',
                  'module', 'is_inherit_members', 'allowed_roles', 'trackers', 'forums', 'versions',
                  'default_version', 'categories', 'status', 'depth', 'all_members', 'members',
                  'activities', 'visible', 'total_estimated_hours', 'total_time_spent', 'family_tree',
                  'parent', 'parent_visible', 'sub_projects', 'user', 'my_perms', 'created', 'updated')
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
        return []

    #     mems = obj.all_members()
    #     request = self.context.get('request')
    #     user = request.user
    #     roles = next((item['roles'] for item in mems if item['user']['pk'] == user.pk), [])
    #     role_pks = [r['pk'] for r in roles]
    #     perms = Permission.objects.filter(role_id__in=role_pks)
    #
    #     combined = {
    #         # 프로젝트
    #         'project_update': False,
    #         'project_close': False,
    #         'project_delete': False,
    #         'project_public': False,
    #         'project_module': False,
    #         'project_member': False,
    #         'project_version': False,
    #         'project_create_sub': False,
    #         'project_pub_query': False,
    #         'project_save_query': False,
    #         # 게시판
    #         'forum_read': False,
    #         'forum_create': False,
    #         'forum_update': False,
    #         'forum_own_update': False,
    #         'forum_delete': False,
    #         'forum_own_delete': False,
    #         'forum_watcher_read': False,
    #         'forum_watcher_create': False,
    #         'forum_watcher_delete': False,
    #         'forum_manage': False,
    #         # 달력
    #         'calendar_read': False,
    #         # 문서
    #         'document_read': False,
    #         'document_create': False,
    #         'document_update': False,
    #         'document_delete': False,
    #         # 파일
    #         'file_read': False,
    #         'file_manage': False,
    #         # 간트차트
    #         'gantt_read': False,
    #         # 업무
    #         'issue_read': False,
    #         'issue_create': False,
    #         'issue_update': False,
    #         'issue_own_update': False,
    #         'issue_copy': False,
    #         'issue_rel_manage': False,
    #         'issue_sub_manage': False,
    #         'issue_public': False,
    #         'issue_own_public': False,
    #         'issue_comment_create': False,
    #         'issue_comment_update': False,
    #         'issue_comment_own_update': False,
    #         'issue_private_comment_read': False,
    #         'issue_private_comment_set': False,
    #         'issue_delete': False,
    #         'issue_watcher_read': False,
    #         'issue_watcher_create': False,
    #         'issue_watcher_delete': False,
    #         'issue_import': False,
    #         'issue_category_manage': False,
    #         # 공지(뉴스)
    #         'news_read': False,
    #         'news_manage': False,
    #         'news_comment': False,
    #         # 저장소(레파지토리)
    #         'repo_changesets_read': False,
    #         'repo_read': False,
    #         'repo_commit_access': False,
    #         'repo_rel_issue_manage': False,
    #         'repo_manage': False,
    #         # 시간추적
    #         'time_read': False,
    #         'time_create': False,
    #         'time_update': False,
    #         'time_own_update': False,
    #         'time_pro_act_manage': False,
    #         'time_other_user_log': False,
    #         'time_entries_import': False,
    #         # 위키
    #         'wiki_read': False,
    #         'wiki_history_read': False,
    #         'wiki_page_export': False,
    #         'wiki_page_update': False,
    #         'wiki_page_rename': False,
    #         'wiki_page_delete': False,
    #         'wiki_attachment_delete': False,
    #         'wiki_watcher_read': False,
    #         'wiki_watcher_create': False,
    #         'wiki_watcher_delete': False,
    #         'wiki_page_project': False,
    #         'wiki_manage': False
    #     }

    # # Combine permissions
    # for perm in perms:
    #     # 프로젝트
    #     combined['project_update'] = combined['project_update'] or perm.project_update  # 프로젝트 편집
    #     combined['project_close'] = combined['project_close'] or perm.project_close  # 프로젝트 닫기/열기
    #     combined['project_delete'] = combined['project_delete'] or perm.project_delete  # 프로젝트 삭제
    #     combined['project_public'] = combined['project_public'] or perm.project_public  # 프로젝트 공개/비공개 설정
    #     combined['project_module'] = combined['project_module'] or perm.project_module  # 프로젝트 모듈 선택
    #     combined['project_member'] = combined['project_member'] or perm.project_member  # 구성원 관리
    #     combined['project_version'] = combined['project_version'] or perm.project_version  # 버전 관리
    #     combined['project_create_sub'] = combined['project_create_sub'] or perm.project_create_sub  # 하위 프로젝트 생성
    #     combined['project_pub_query'] = combined['project_pub_query'] or perm.project_pub_query  # 공용 검색 폼 관리
    #     combined['project_save_query'] = combined['project_save_query'] or perm.project_save_query  # 검색 폼 관리
    #     # 게시물
    #     combined['forum_read'] = combined['forum_read'] or perm.forum_read  # 게시물 보기
    #     combined['forum_create'] = combined['forum_create'] or perm.forum_create  # 게시물 생성
    #     combined['forum_update'] = combined['forum_update'] or perm.forum_update  # 게시물 편집
    #     combined['forum_own_update'] = combined['forum_own_update'] or perm.forum_own_update  # 내 게시물 편집
    #     combined['forum_delete'] = combined['forum_delete'] or perm.forum_delete  # 게시물 삭제
    #     combined['forum_own_delete'] = combined['forum_own_delete'] or perm.forum_own_delete  # 내 게시물 삭제
    #     combined['forum_watcher_read'] = combined['forum_watcher_read'] or perm.forum_watcher_read  # 게시물 관람자 보기
    #     combined['forum_watcher_create'] = combined['forum_watcher_create'] or perm.forum_watcher_create
    #     combined['forum_watcher_delete'] = combined['forum_watcher_delete'] or perm.forum_watcher_delete
    #     combined['forum_manage'] = combined['forum_manage'] or perm.forum_manage  # 게시물 관리
    #     # 달력
    #     combined['calendar_read'] = combined['calendar_read'] or perm.calendar_read  # 달력 보기
    #     # 문서
    #     combined['document_read'] = combined['document_read'] or perm.document_read  # 문서 보기
    #     combined['document_create'] = combined['document_create'] or perm.document_create  # 문서 생성
    #     combined['document_update'] = combined['document_update'] or perm.document_update  # 문서 편집
    #     combined['document_delete'] = combined['document_delete'] or perm.document_delete  # 문서 삭제
    #     # 파일
    #     combined['file_read'] = combined['file_read'] or perm.file_read  # 파일 보기
    #     combined['file_manage'] = combined['file_manage'] or perm.file_manage  # 파일 관리
    #     # 간트 차트
    #     combined['gantt_read'] = combined['gantt_read'] or perm.gantt_read  # 간트 차트 보기
    #     # 업무
    #     combined['issue_read'] = combined['issue_read'] or perm.issue_read  # 업무 보기
    #     combined['issue_create'] = combined['issue_create'] or perm.issue_create  # 업무 생성
    #     combined['issue_update'] = combined['issue_update'] or perm.issue_update  # 업무 편집
    #     combined['issue_own_update'] = combined['issue_own_update'] or perm.issue_own_update  # 내 업무 편집
    #     combined['issue_copy'] = combined['issue_copy'] or perm.issue_copy  # 업무 복사
    #     combined['issue_rel_manage'] = combined['issue_rel_manage'] or perm.issue_rel_manage  # 업무 관계 관리
    #     combined['issue_sub_manage'] = combined['issue_sub_manage'] or perm.issue_sub_manage  # 하위 업무 관리
    #     combined['issue_public'] = combined['issue_public'] or perm.issue_public  # 업무 공개/비공개 설정
    #     combined['issue_own_public'] = combined['issue_own_public'] or perm.issue_own_public  # 내 업무 공개/비공개 설정
    #     combined['issue_comment_create'] = combined['issue_comment_create'] or perm.issue_comment_create  # 댓글 추가
    #     combined['issue_comment_update'] = combined['issue_comment_update'] or perm.issue_comment_update  # 댓글 편집
    #     combined['issue_comment_own_update'] = \
    #         combined['issue_comment_own_update'] or perm.issue_comment_own_update  # 내 댓글 편집
    #     combined['issue_private_comment_read'] = \
    #         combined['issue_private_comment_read'] or perm.issue_private_comment_read  # 비공개 댓글 보기
    #     combined['issue_private_comment_set'] = \
    #         combined['issue_private_comment_set'] or perm.issue_private_comment_set  # 댓글 비공개 설정
    #     combined['issue_delete'] = combined['issue_delete'] or perm.issue_delete  # 업무 삭제
    #     combined['issue_watcher_read'] = combined['issue_watcher_read'] or perm.issue_watcher_read  # 업무 관람자 보기
    #     combined['issue_watcher_create'] = \
    #         combined['issue_watcher_create'] or perm.issue_watcher_create  # 업무 관람자 생성
    #     combined['issue_watcher_delete'] = \
    #         combined['issue_watcher_delete'] or perm.issue_watcher_delete  # 업무 관람자 삭제
    #     combined['issue_import'] = combined['issue_import'] or perm.issue_import  # 업무 가져 오기
    #     combined['issue_category_manage'] = \
    #         combined['issue_category_manage'] or perm.issue_category_manage  # 업무 범주 관리
    #     # 공지(뉴스)
    #     combined['news_read'] = combined['news_read'] or perm.news_read  # 공지 보기
    #     combined['news_manage'] = combined['news_manage'] or perm.news_manage  # 공지 관리
    #     combined['news_comment'] = combined['news_comment'] or perm.news_comment  # 공지 댓글 달기
    #     # 저장소(레파지토리)
    #     combined['repo_changesets_read'] = combined['repo_changesets_read'] or perm.repo_changesets_read  # 변경 묶음 보기
    #     combined['repo_read'] = combined['repo_read'] or perm.repo_read  # 저장소 보기
    #     combined['repo_commit_access'] = combined['repo_commit_access'] or perm.repo_commit_access  # 변경 로그 보기
    #     combined['repo_rel_issue_manage'] = \
    #         combined['repo_rel_issue_manage'] or perm.repo_rel_issue_manage  # 연결된 업무 관리
    #     combined['repo_manage'] = combined['repo_manage'] or perm.repo_manage  # 저장소 관리
    #     # 시간추적
    #     combined['time_read'] = combined['time_read'] or perm.time_read  # 소요 시간 보기
    #     combined['time_create'] = combined['time_create'] or perm.time_create  # 소요 시간 기록
    #     combined['time_update'] = combined['time_update'] or perm.time_update  # 소요 시간 편집
    #     combined['time_own_update'] = combined['time_own_update'] or perm.time_own_update  # 소요 시간 편집
    #     combined['time_pro_act_manage'] = \
    #         combined['time_pro_act_manage'] or perm.time_pro_act_manage  # 프로젝트 작업 내역 관리
    #     combined['time_other_user_log'] = \
    #         combined['time_other_user_log'] or perm.time_other_user_log  # 다른 사용자 소요 시간 입력
    #     combined['time_entries_import'] = \
    #         combined['time_entries_import'] or perm.time_entries_import  # 소요 시간 가져 오기
    #     # 위키
    #     combined['wiki_read'] = combined['wiki_read'] or perm.wiki_read  # 위키 보기
    #     combined['wiki_history_read'] = combined['wiki_history_read'] or perm.wiki_history_read  # 위키 기록 보기
    #     combined['wiki_page_export'] = combined['wiki_page_export'] or perm.wiki_page_export  # 위키 페이지 내보내기
    #     combined['wiki_page_update'] = combined['wiki_page_update'] or perm.wiki_page_update  # 위키 페이지 편집
    #     combined['wiki_page_rename'] = combined['wiki_page_rename'] or perm.wiki_page_rename  # 위키 페이지 이름 변경
    #     combined['wiki_page_delete'] = combined['wiki_page_delete'] or perm.wiki_page_delete  # 위키 페이지 삭제
    #     combined['wiki_attachment_delete'] = \
    #         combined['wiki_attachment_delete'] or perm.wiki_attachment_delete  # 첨부파일 삭제
    #     combined['wiki_watcher_read'] = combined['wiki_watcher_read'] or perm.wiki_watcher_read  # 위키 관람자 보기
    #     combined['wiki_watcher_create'] = combined['wiki_watcher_create'] or perm.wiki_watcher_create  # 위키 관람자 추가
    #     combined['wiki_watcher_delete'] = combined['wiki_watcher_delete'] or perm.wiki_watcher_delete  # 위키 관람자 삭제
    #     combined['wiki_page_project'] = combined['wiki_page_project'] or perm.wiki_page_project  # 프로젝트 위키 페이지
    #     combined['wiki_manage'] = combined['wiki_manage'] or perm.wiki_manage  # 위키 관리
    #
    # return combined

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
                              file=self.initial_data.get('file', True),
                              wiki=self.initial_data.get('wiki', True),
                              repository=self.initial_data.get('repository', False),
                              forum=self.initial_data.get('forum', True),
                              calendar=self.initial_data.get('calendar', True),
                              gantt=self.initial_data.get('gantt', True))
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
        for field in ['issue', 'time', 'news', 'document', 'file', 'wiki', 'repository', 'forum', 'calendar', 'gantt']:
            if field in self.initial_data:
                setattr(module, field, self.initial_data[field])
        module.save()

        # user에 대응하는 member 모델 생성
        users = self.initial_data.get('users', [])
        roles = self.initial_data.get('roles', [])
        del_mem = self.initial_data.get('del_mem')

        members = []

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


class IssueProjectForGanttSerializer(serializers.ModelSerializer):
    start_first = serializers.SerializerMethodField()
    due_last = serializers.SerializerMethodField()
    sub_projects = serializers.SerializerMethodField()
    issues = serializers.SerializerMethodField()

    class Meta:
        model = IssueProject
        fields = ('pk', 'company', 'name', 'slug', 'start_first',
                  'due_last', 'depth', 'sub_projects', 'issues')

    @staticmethod
    def get_start_first(obj):
        start = obj.issue_set.filter(closed=None).order_by('start_date').first()
        return start.start_date if start else None

    @staticmethod
    def get_due_last(obj):
        due = obj.issue_set.filter(closed=None).order_by('due_date').last()
        return due.due_date if due else None

    def get_sub_projects(self, obj):
        sub_projects = obj.issueproject_set.exclude(status='9')
        request = self.context.get('request')

        # Create a new serializer class without the 'my_perms' field
        class SubProjectSerializer(self.__class__):
            class Meta(self.__class__.Meta):
                fields = tuple(
                    f for f in self.__class__.Meta.fields if
                    f not in ('company',))

        return SubProjectSerializer(sub_projects, many=True, read_only=True, context=self.context).data

    def get_issues(self, obj):
        issues = obj.issue_set.filter(closed=None)

        class IssuesSerializer(serializers.ModelSerializer):
            tracker = serializers.SlugRelatedField(slug_field='name', read_only=True)

            class Meta:
                model = Issue
                fields = ('pk', 'tracker', 'subject', 'start_date', 'due_date', 'done_ratio')

        return IssuesSerializer(issues, many=True, read_only=True, context=self.context).data


# class PermissionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Permission
#         fields = ('pk', 'project_update', 'project_close', 'project_delete',
#                   'project_public', 'project_module', 'project_member', 'project_version',
#                   'project_create_sub', 'project_pub_query', 'project_save_query',
#                   'forum_read', 'forum_create', 'forum_update', 'forum_own_update',
#                   'forum_delete', 'forum_own_delete', 'forum_watcher_read',
#                   'forum_watcher_create', 'forum_watcher_delete', 'forum_manage',
#                   'calendar_read',
#                   'document_read', 'document_create', 'document_update', 'document_delete',
#                   'file_read', 'file_manage',
#                   'gantt_read',
#                   'issue_read', 'issue_create', 'issue_update', 'issue_own_update', 'issue_copy',
#                   'issue_rel_manage', 'issue_sub_manage', 'issue_public', 'issue_own_public',
#                   'issue_comment_create', 'issue_comment_update', 'issue_comment_own_update',
#                   'issue_private_comment_read', 'issue_private_comment_set', 'issue_delete',
#                   'issue_watcher_read', 'issue_watcher_create', 'issue_watcher_delete', 'issue_import',
#                   'issue_category_manage',
#                   'news_read', 'news_manage', 'news_manage', 'news_comment',
#                   'repo_changesets_read', 'repo_read', 'repo_commit_access', 'repo_rel_issue_manage', 'repo_manage',
#                   'time_read', 'time_create', 'time_update', 'time_own_update',
#                   'time_pro_act_manage', 'time_other_user_log', 'time_entries_import',
#                   'wiki_read', 'wiki_history_read', 'wiki_page_export', 'wiki_page_update',
#                   'wiki_page_rename', 'wiki_page_delete', 'wiki_attachment_delete', 'wiki_watcher_read',
#                   'wiki_watcher_create', 'wiki_watcher_delete', 'wiki_page_project', 'wiki_manage')


class RoleSerializer(serializers.ModelSerializer):
    # permission = PermissionSerializer(read_only=True)

    class Meta:
        model = Role
        fields = ('pk', 'name', 'assignable', 'issue_visible', 'time_entry_visible', 'user_visible',
                  'default_time_activity', 'order', 'user', 'created', 'updated')  # , 'permission'


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
                  'file', 'wiki', 'repository', 'forum', 'calendar', 'gantt')


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
                  'effective_date', 'description', 'wiki_page_title', 'issues', 'is_default')

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
