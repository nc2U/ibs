import json
import os.path

from django.db import transaction, IntegrityError
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.issue import IssueInRelatedSerializer, IssueCommentSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models.project import IssueProject, Role, Permission, Member, Module, Version
from work.models.github import Repository, Commit
from work.models.logging import ActivityLogEntry, IssueLogEntry
from work.models.inform import CodeDocsCategory, News, Search
from work.models.issue import (IssueCategory, Tracker, IssueStatus, Workflow,
                               CodeActivity, CodeIssuePriority, Issue, IssueRelation,
                               IssueFile, IssueComment, TimeEntry)


class TimeEntryInActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeEntry
        fields = ('pk', 'hours', 'comment')


class ActivityLogEntrySerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    issue = IssueInRelatedSerializer(read_only=True)
    comment = IssueCommentSerializer(read_only=True)
    spent_time = TimeEntryInActivityLogSerializer(read_only=True)
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ActivityLogEntry
        fields = ('pk', 'sort', 'project', 'issue', 'status_log', 'comment',
                  'spent_time', 'act_date', 'timestamp', 'user')
        # 'change_sets', 'news', 'document', 'file', 'wiki', 'message',


class SimpleCommentInIssueLogEntrySerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueComment
        fields = ('pk', 'content', 'user')


class IssueLogEntrySerializer(serializers.ModelSerializer):
    issue = IssueInRelatedSerializer(read_only=True)
    comment = SimpleCommentInIssueLogEntrySerializer(read_only=True)
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueLogEntry
        fields = ('pk', 'log_id', 'issue', 'action', 'comment', 'details', 'diff', 'timestamp', 'user')
