from django_filters.rest_framework import FilterSet, BooleanFilter, DateFilter, CharFilter
from rest_framework import viewsets
from rest_framework.views import APIView

from apiV1.pagination import *
from apiV1.permission import *
from apiV1.serializers.work.inform import *


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
