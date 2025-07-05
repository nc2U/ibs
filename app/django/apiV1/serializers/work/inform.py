import json
import os

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


class NewsCommentInSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = NewsComment
        fields = ('pk', 'content', 'parent', 'user', 'created', 'updated')


class NewsSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    author = SimpleUserSerializer(read_only=True)
    comments = NewsCommentInSerializer(read_only=True, many=True)

    class Meta:
        model = News
        fields = ('pk', 'project', 'title', 'summary', 'content',
                  'author', 'comments', 'is_new', 'created', 'updated')

    @transaction.atomic
    def create(self, validated_data):
        project__slug = self.initial_data.get('project', None)
        project = IssueProject.objects.get(slug=project__slug)
        news = News.objects.create(**validated_data, project=project)

        # Files 처리
        if self.initial_data.get('newFiles'):
            new_files = self.initial_data.getlist('newFiles')
            if new_files:
                for file in new_files:
                    NewsFile.objects.create(news=news, file=file)
        return news

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        project = self.initial_data.get('project', None)
        if instance.project.slug != project:
            instance.project = IssueProject.objects.get(slug=project)
        instance.save()

        try:
            old_files = self.initial_data.getlist('files')
            cng_pks = self.initial_data.getlist('cngPks')
            cng_files = self.initial_data.getlist('cngFiles')
            cng_maps = dict(zip(cng_pks, cng_files))

            new_files = self.initial_data.getlist('newFiles')

            with transaction.atomic():
                # 1. 기존 파일 처리
                for json_file in old_files:
                    file = json.loads(json_file)
                    file_object = NewsFile.objects.get(pk=file.get('pk'))
                    # 2. 삭제 요청 된 파일 처리
                    if file.get('del'):
                        file_object.delete()
                        continue
                    # 3. 변경 요청된 파일 처리
                    new_file = cng_maps.get(str(file.get('pk')))
                    if new_file:
                        try:
                            if os.path.isfile(file_object.file.path):
                                os.remove(file_object.file.path)
                        except Exception:
                            pass
                        file_object.file = new_file
                        file_object.save()

                # 새 파일 등록
                for file in new_files:
                    NewsFile.objects.create(news=instance, file=file)

        except Exception:
            pass

        return instance


class NewsCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsComment
        fields = '__all__'


class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = '__all__'
