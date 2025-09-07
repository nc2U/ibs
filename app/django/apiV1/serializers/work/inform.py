import json

from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models import NewsFile
from work.models.inform import CodeDocsCategory, News, NewsComment, Search
from work.models.project import IssueProject


class CodeDocsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeDocsCategory
        fields = ('pk', 'name', 'active', 'default', 'order')


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
        fields = ('pk', 'project', 'title', 'summary', 'content', 'files',
                  'author', 'comments', 'is_new', 'created', 'updated')

    @transaction.atomic
    def create(self, validated_data):
        project_slug = self.initial_data.get('project')
        if project_slug:
            validated_data['project'] = IssueProject.objects.get(slug=project_slug)
        news = super().create(validated_data)
        # 파일 처리
        request = self.context.get('request')
        creator = request.user if request else None
        new_files = request.FILES.getlist('new_files')
        new_descs = request.data.getlist('new_descs')

        for file, desc in zip(new_files, new_descs):
            NewsFile.objects.create(news=news, file=file, description=desc, creator=creator)
        return news

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        project_slug = self.initial_data.get('project')
        if project_slug and project_slug != instance.project.slug:
            instance.project = IssueProject.objects.get(slug=project_slug)
        instance.save()

        try:
            request = self.context['request']
            creator = request.user

            new_files = request.FILES.getlist('new_files')
            new_descs = request.data.getlist('new_descs')

            for file, desc in zip(new_files, new_descs):
                NewsFile.objects.create(news=instance, file=file, description=desc, creator=creator)

            old_files = self.initial_data.getlist('files')
            cng_pks = self.initial_data.getlist('cngPks')
            cng_files = self.initial_data.getlist('cngFiles')
            cng_maps = dict(zip(cng_pks, cng_files))

            for json_file in old_files:
                file = json.loads(json_file)
                pk = str(file.get('pk'))
                file_obj = NewsFile.objects.get(pk=pk)

                if file.get('del'):
                    file_obj.delete()
                    continue

                cng_file = cng_maps.get(pk)
                if cng_file:
                    try:
                        if default_storage.exists(file_obj.file.name):
                            default_storage.delete(file_obj.file.name)
                    except Exception as e:
                        print(f"파일 처리 중 오류 발생: {e}")
                    file_obj.file = cng_file
                    file_obj.creator = creator
                    file_obj.save()

            del_file = self.initial_data.get('del_file', None)
            if del_file:
                file = NewsFile.objects.get(pk=del_file)
                file.delete()

        except Exception as e:
            print(f"파일 처리 중 오류 발생: {e}")

        return instance


class NewsFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsFile
        fields = ('pk', 'news', 'file', 'file_name', 'file_type', 'file_size', 'description', 'created')


class NewsCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsComment
        fields = '__all__'


class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = '__all__'
