from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.issue import IssueInRelatedSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from board.models import Post
from docs.models import Document
from work.models.inform import News
from work.models.issue import IssueComment
from work.models.logging import ActivityLogEntry, IssueLogEntry
from work.models.meeting import Meeting


class MeetingInActLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = ('pk', 'title')


class NewsInActLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ('title', 'summary')


class DocInActLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('pk', 'title')


class PostInActLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('pk', 'title')


class SimpleCommentInActLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueComment
        fields = ('pk', 'content')


class ActivityLogEntrySerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(read_only=True)
    issue = IssueInRelatedSerializer(read_only=True)
    comment = SimpleCommentInActLogSerializer(read_only=True)
    meeting = MeetingInActLogSerializer(read_only=True)
    news = NewsInActLogSerializer(read_only=True)
    document = DocInActLogSerializer(read_only=True)
    post = PostInActLogSerializer(read_only=True)
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ActivityLogEntry
        fields = ('pk', 'sort', 'project', 'issue', 'status_log', 'comment', 'meeting',
                  'news', 'document', 'post', 'act_date', 'timestamp', 'creator')


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
