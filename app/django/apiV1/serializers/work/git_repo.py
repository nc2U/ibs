from rest_framework import serializers

from work.models import Issue
from work.models.git_repo import Repository, Branch, Commit


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ('pk', 'project', 'is_default', 'slug', 'local_path', 'remote_url', 'is_report')


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ('pk', 'repo', 'name')


class IssueInCommitSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    tracker = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'tracker', 'subject')


class CommitSerializer(serializers.ModelSerializer):
    branches = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)
    parents = serializers.SlugRelatedField(slug_field='commit_hash', many=True, read_only=True)
    children = serializers.SlugRelatedField(slug_field='commit_hash', many=True, read_only=True)
    issues = IssueInCommitSerializer(many=True, read_only=True)
    prev = serializers.SerializerMethodField()
    next = serializers.SerializerMethodField()

    class Meta:
        model = Commit
        fields = ('pk', 'repo', 'commit_hash', 'author', 'date', 'message',
                  'branches', 'parents', 'children', 'issues', 'prev', 'next')

    @staticmethod
    def get_prev(obj):
        prev_obj = obj.get_prev()
        return prev_obj.commit_hash if prev_obj else None

    @staticmethod
    def get_next(obj):
        next_obj = obj.get_next()
        return next_obj.commit_hash if next_obj else None


class GitRepoApiSerializer(serializers.Serializer):
    name = serializers.CharField()
    created_at = serializers.CharField()
    pushed_at = serializers.CharField()
    default_branch = serializers.CharField()


class CommitApiSerializer(serializers.Serializer):
    sha = serializers.CharField()
    author = serializers.CharField()
    date = serializers.CharField()
    message = serializers.CharField()


class GitBranchSerializer(serializers.Serializer):
    name = serializers.CharField()
    commit = CommitApiSerializer()


class GitRefsSerializer(serializers.Serializer):
    name = serializers.CharField()
    branches = serializers.ListField(child=serializers.CharField())
    commit = CommitApiSerializer()


class TreeItemSerializer(serializers.Serializer):
    path = serializers.CharField()
    name = serializers.CharField()
    mode = serializers.CharField()
    type = serializers.CharField()
    sha = serializers.CharField()
    size = serializers.IntegerField(allow_null=True)
    commit = CommitApiSerializer()


class GitRefsAndTreeSerializer(serializers.Serializer):
    refs = GitRefsSerializer()
    trees = TreeItemSerializer(many=True)


class GitCompareCommitsSerializer(serializers.Serializer):
    base = serializers.CharField()
    head = serializers.CharField()
    commits = CommitApiSerializer(many=True)
    diff = serializers.CharField()
    truncated = serializers.BooleanField()


class ChangedInGetFileSerializer(serializers.Serializer):
    path = serializers.CharField()
    type = serializers.CharField()


class GetChangedFilesSerializer(serializers.Serializer):
    sha = serializers.CharField()
    changed = ChangedInGetFileSerializer(many=True)
