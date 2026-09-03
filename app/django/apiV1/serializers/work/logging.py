from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.issue import IssueInRelatedSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from forum.models import Post
from docs.models import Document
from work.models.inform import News
from work.models.issue import IssueComment
from work.models.logging import ActivityLogEntry, IssueLogEntry
from work.models.meeting import Meeting


class ActivityLogEntrySerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ActivityLogEntry
        fields = ('pk', 'sort', 'project', 'target_id', 'parent_id', 'title', 'summary',
                  'status_log', 'act_date', 'timestamp', 'creator')


class SimpleCommentInIssueLogEntrySerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueComment
        fields = ('pk', 'content', 'is_private', 'is_blocked', 'creator')


class IssueLogEntrySerializer(serializers.ModelSerializer):
    issue = IssueInRelatedSerializer(read_only=True)
    comment = SimpleCommentInIssueLogEntrySerializer(read_only=True)
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = IssueLogEntry
        fields = ('pk', 'log_id', 'issue', 'action', 'comment', 'details', 'diff', 'timestamp', 'creator')
