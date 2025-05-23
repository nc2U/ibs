from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models.inform import News, Search
from work.models.project import IssueProject


class NewsSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    author = SimpleUserSerializer(read_only=True)

    class Meta:
        model = News
        fields = ('pk', 'project', 'title', 'summary', 'description', 'author', 'created')

    @transaction.atomic
    def create(self, validated_data):
        project__slug = self.initial_data.get('project__slug', None)
        project = IssueProject.objects.get(slug=project__slug)
        news = News.objects.create(**validated_data, project=project)
        return news

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        project = self.initial_data.get('project__slug', None)
        if instance.project.slug != project:
            instance.project = IssueProject.objects.get(slug=project)
        instance.save()
        return instance


class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = '__all__'
