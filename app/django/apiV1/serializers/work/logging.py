from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.issue import IssueInRelatedSerializer, IssueCommentSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models.inform import News
from work.models.issue import (IssueComment, TimeEntry)
from work.models.logging import ActivityLogEntry, IssueLogEntry


class NewsInActLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ('title', 'summary')


class TimeEntryInActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeEntry
        fields = ('pk', 'hours', 'comment')


class ActivityLogEntrySerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    issue = IssueInRelatedSerializer(read_only=True)
    comment = IssueCommentSerializer(read_only=True)
    news = NewsInActLogSerializer(read_only=True)
    spent_time = TimeEntryInActivityLogSerializer(read_only=True)
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ActivityLogEntry
        fields = ('pk', 'sort', 'project', 'issue', 'status_log', 'comment',
                  'news', 'spent_time', 'act_date', 'timestamp', 'creator')
        # 'change_sets', 'news', 'document', 'file', 'wiki', 'message',


class SimpleCommentInIssueLogEntrySerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueComment
        fields = ('pk', 'content', 'creator')


class IssueLogEntrySerializer(serializers.ModelSerializer):
    issue = IssueInRelatedSerializer(read_only=True)
    comment = SimpleCommentInIssueLogEntrySerializer(read_only=True)
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueLogEntry
        fields = ('pk', 'log_id', 'issue', 'action', 'comment', 'details', 'diff', 'timestamp', 'creator')
