from django.db import transaction
from rest_framework import serializers

from _utils.file_service import FileService
from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models import NewsFile
from work.models.inform import News, NewsComment, Search, CustomQuery
from work.models.project import IssueProject


class FilesInNewsSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = NewsFile
        fields = ('pk', 'news', 'file_name', 'file', 'file_type',
                  'file_size', 'description', 'creator', 'created')


class NewsCommentInSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = NewsComment
        fields = ('pk', 'content', 'parent', 'creator', 'created', 'updated')


class NewsSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    files = FilesInNewsSerializer(many=True, read_only=True)
    comments = NewsCommentInSerializer(read_only=True, many=True)
    author = SimpleUserSerializer(read_only=True)

    class Meta:
        model = News
        fields = ('pk', 'project', 'title', 'summary', 'content', 'is_important',
                  'files', 'author', 'comments', 'is_new', 'created', 'updated')

    @staticmethod
    def _resolve_project(project_val):
        if not project_val:
            return None
        if isinstance(project_val, IssueProject):
            return project_val
        if isinstance(project_val, int) or (isinstance(project_val, str) and project_val.isdigit()):
            return IssueProject.objects.filter(pk=int(project_val)).first()
        return IssueProject.objects.filter(slug=str(project_val)).first()

    @transaction.atomic
    def create(self, validated_data):
        project_val = self.initial_data.get('project')
        resolved_project = self._resolve_project(project_val)
        if resolved_project:
            validated_data['project'] = resolved_project
        news = super().create(validated_data)

        # 파일 처리
        FileService.manage_files(
            instance=news,
            initial_data=self.initial_data,
            creator=self.context['request'].user if 'request' in self.context else None,
            file_model=NewsFile,
            related_name='news'
        )
        return news

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        project_val = self.initial_data.get('project')
        resolved_project = self._resolve_project(project_val)
        if resolved_project and resolved_project.pk != instance.project_id:
            instance.project = resolved_project
        instance.save()

        # 파일 처리
        FileService.manage_files(
            instance=instance,
            initial_data=self.initial_data,
            creator=self.context['request'].user if 'request' in self.context else None,
            file_model=NewsFile,
            related_name='news'
        )
        return instance


class NewsFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsFile
        fields = ('pk', 'news', 'file', 'file_name', 'file_type', 'file_size', 'description', 'created')


class NewsCommentSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = NewsComment
        fields = ('pk', 'news', 'content', 'parent', 'creator', 'created', 'updated')


class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = '__all__'


class CustomQuerySerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    target_type_display = serializers.CharField(source='get_target_type_display', read_only=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = CustomQuery
        fields = (
            'pk', 'name', 'description', 'target_type', 'target_type_display', 'project',
            'user', 'username', 'is_public', 'filters', 'column_names',
            'sort_criteria', 'group_by', 'created', 'updated'
        )
        read_only_fields = ('user',)

    def validate_description(self, value):
        return value or ''

    def _check_query_permissions(self, user, project, is_public):
        if user.is_superuser or getattr(user, 'work_manager', False):
            return
        if project:
            user_perms = project.get_user_permissions(user)
        else:
            from work.models.project import Role
            user_perms = list(
                Role.objects.filter(
                    projects__members__user=user
                ).filter(
                    permissions__code__in=['project.save_query', 'project.pub_query']
                ).values_list('permissions__code', flat=True)
            )
            try:
                role2 = Role.objects.prefetch_related('permissions').get(pk=2)
                user_perms.extend(role2.permissions.values_list('code', flat=True))
            except Role.DoesNotExist:
                pass

        if is_public and 'project.pub_query' not in user_perms:
            raise serializers.ValidationError({"is_public": "공용 검색양식을 생성/설정할 권한이 없습니다."})
        if not is_public and 'project.save_query' not in user_perms:
            raise serializers.ValidationError({"non_field_errors": "검색양식을 저장할 권한이 없습니다."})

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        is_public = validated_data.get('is_public', False)
        project = validated_data.get('project')
        self._check_query_permissions(user, project, is_public)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        is_public = validated_data.get('is_public', instance.is_public)
        project = validated_data.get('project', instance.project)
        if is_public != instance.is_public or 'project' in validated_data:
            self._check_query_permissions(user, project, is_public)
        return super().update(instance, validated_data)

