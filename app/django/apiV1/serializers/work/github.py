from rest_framework import serializers

from work.models.github import Repository, Commit


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ('pk', 'project', 'is_default', 'owner', 'slug', 'github_token', 'is_report')


class CommitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commit
        fields = ('pk', 'repo', 'commit_hash', 'message', 'author', 'date', 'issues')
