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
        serializer.save(creator=self.request.user)


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTen
    filterset_fields = ('project__slug', 'author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NewsFileViewSet(viewsets.ModelViewSet):
    queryset = NewsFile.objects.all()
    serializer_class = None
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('news',)
    search_fields = ('file_name', 'description')


class NewsCommentViewSet(viewsets.ModelViewSet):
    queryset = NewsComment.objects.all()
    serializer_class = NewsCommentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationTen
    filterset_fields = ('news__project__slug', 'news', 'parent', 'creator')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class SearchViewSet(viewsets.ModelViewSet):
    queryset = Search.objects.all()
    serializer_class = SearchSerializer
    permission_classes = (permissions.IsAuthenticated,)
