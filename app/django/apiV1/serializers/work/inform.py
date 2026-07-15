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

    @transaction.atomic
    def create(self, validated_data):
        project_slug = self.initial_data.get('project')
        if project_slug:
            validated_data['project'] = IssueProject.objects.get(slug=project_slug)
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
        project_slug = self.initial_data.get('project')
        if project_slug and project_slug != instance.project.slug:
            instance.project = IssueProject.objects.get(slug=project_slug)
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

    class Meta:
        model = CustomQuery
        fields = (
            'pk', 'name', 'description', 'target_type', 'target_type_display', 'project',
            'user', 'username', 'is_public', 'filters', 'column_names',
            'sort_criteria', 'group_by', 'created', 'updated'
        )
        read_only_fields = ('user',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user

        # 공용 생성 검증: is_public이 True인 경우 권한 검사
        is_public = validated_data.get('is_public', False)
        project = validated_data.get('project')
        user = self.context['request'].user

        if not (user.is_superuser or getattr(user, 'work_manager', False)):
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
                raise serializers.ValidationError({"is_public": "공용 검색양식을 생성할 권한이 없습니다."})
            if not is_public and 'project.save_query' not in user_perms:
                raise serializers.ValidationError({"non_field_errors": "검색양식을 저장할 권한이 없습니다."})

        return super().create(validated_data)

