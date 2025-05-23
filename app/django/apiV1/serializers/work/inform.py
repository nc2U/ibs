import json
import os.path

from django.db import transaction, IntegrityError
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models.project import IssueProject, Role, Permission, Member, Module, Version
from work.models.github import Repository, Commit
from work.models.logging import ActivityLogEntry, IssueLogEntry
from work.models.inform import CodeDocsCategory, News, Search
from work.models.issue import (IssueCategory, Tracker, IssueStatus, Workflow,
                               CodeActivity, CodeIssuePriority, Issue, IssueRelation,
                               IssueFile, IssueComment, TimeEntry)


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
