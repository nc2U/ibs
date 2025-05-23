from rest_framework import viewsets

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.inform import *


class CodeDocsCategoryViewSet(viewsets.ModelViewSet):
    queryset = CodeDocsCategory.objects.all()
    serializer_class = CodeDocsCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTwenty
    search_fields = ('id',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTen
    filterset_fields = ('project__slug', 'author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SearchViewSet(viewsets.ModelViewSet):
    queryset = Search.objects.all()
    serializer_class = SearchSerializer
    permission_classes = (permissions.IsAuthenticated,)
