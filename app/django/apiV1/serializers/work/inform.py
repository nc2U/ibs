from django.db import transaction
from rest_framework import serializers

from _utils.file_service import FileService
from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models import NewsFile
from work.models.inform import News, NewsComment, Search
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
