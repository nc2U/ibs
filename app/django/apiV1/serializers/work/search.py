from rest_framework import serializers

from work.models.issue import Issue, IssueComment
from work.models.meeting import Meeting
from work.models.inform import News
from docs.models import Document
from forum.models import Post


class IssueSearchSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()
    tracker = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'tracker', 'status', 'subject', 'created', 'creator', 'is_private')

    def get_project(self, obj):
        return {'slug': obj.project.slug, 'name': obj.project.name}

    def get_tracker(self, obj):
        return {'pk': obj.tracker.pk, 'name': obj.tracker.name}

    def get_status(self, obj):
        return {'name': obj.status.name, 'closed': obj.status.closed}

    def get_creator(self, obj):
        if obj.creator:
            return {'pk': obj.creator.pk, 'username': obj.creator.username}
        return None


class CommentSearchSerializer(serializers.ModelSerializer):
    issue = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()

    class Meta:
        model = IssueComment
        fields = ('pk', 'issue', 'content', 'created', 'creator')

    def get_issue(self, obj):
        return {
            'pk': obj.issue.pk,
            'subject': obj.issue.subject,
            'project': {'slug': obj.issue.project.slug, 'name': obj.issue.project.name},
        }

    def get_creator(self, obj):
        return {'pk': obj.creator.pk, 'username': obj.creator.username}


class MeetingSearchSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = ('pk', 'project', 'title', 'meeting_date', 'status', 'creator')

    def get_project(self, obj):
        return {'slug': obj.project.slug, 'name': obj.project.name}

    def get_creator(self, obj):
        return {'pk': obj.creator.pk, 'username': obj.creator.username}


class NewsSearchSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ('pk', 'project', 'title', 'summary', 'created', 'author')

    def get_project(self, obj):
        return {'slug': obj.project.slug, 'name': obj.project.name}

    def get_author(self, obj):
        return {'pk': obj.author.pk, 'username': obj.author.username}


class DocumentSearchSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ('pk', 'project', 'title', 'description', 'created', 'creator')

    def get_project(self, obj):
        return {'slug': obj.issue_project.slug, 'name': obj.issue_project.name}

    def get_creator(self, obj):
        return {'pk': obj.creator.pk, 'username': obj.creator.username} if obj.creator else None


class PostSearchSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('pk', 'project', 'title', 'created', 'creator')

    def get_project(self, obj):
        return {'slug': obj.forum.project.slug, 'name': obj.forum.project.name}

    def get_creator(self, obj):
        return {'pk': obj.creator.pk, 'username': obj.creator.username} if obj.creator else None

