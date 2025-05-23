from rest_framework import viewsets

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.github import *


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('project', 'is_default', 'is_report')


class CommitViewSet(viewsets.ModelViewSet):
    queryset = Commit.objects.all()
    serializer_class = CommitSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwentyFive
    filterset_fields = ('repo__project', 'repo', 'commit_hash', 'issues')
