from rest_framework import serializers

from work.models.github import Repository, Commit


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ('pk', 'project', 'is_default', 'slug', 'local_path', 'is_report')


class CommitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commit
        fields = ('pk', 'repo', 'commit_hash', 'message', 'author', 'date', 'issues')


class GitRepoApiSerializer(serializers.Serializer):
    name = serializers.CharField()
    created_at = serializers.CharField()
    pushed_at = serializers.CharField()
    default_branch = serializers.CharField()


class CommitInfoSerializer(serializers.Serializer):
    sha = serializers.CharField()
    author = serializers.CharField()
    date = serializers.CharField()
    message = serializers.CharField()


class GitBranchSerializer(serializers.Serializer):
    name = serializers.CharField()
    commit = CommitInfoSerializer()


class TreeItemSerializer(serializers.Serializer):
    path = serializers.CharField()
    name = serializers.CharField()
    mode = serializers.CharField()
    type = serializers.CharField()
    sha = serializers.CharField()
    size = serializers.IntegerField(allow_null=True)
    commit = CommitInfoSerializer()


class GitBranchAndTreeSerializer(serializers.Serializer):
    branch = GitBranchSerializer()
    trees = TreeItemSerializer(many=True)


class GitCompareCommitsSerializer(serializers.Serializer):
    base = serializers.CharField()
    head = serializers.CharField()
    commits = CommitInfoSerializer(many=True)
    diff = serializers.CharField()
    truncated = serializers.BooleanField()
