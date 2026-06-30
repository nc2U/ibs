from django.db.models import Q
from rest_framework import viewsets

from apiV1.pagination import PageNumberPaginationTen
from apiV1.permissions.auth_perms import permissions
from apiV1.permissions.work_perms import NewsPermission
from apiV1.serializers.work import NewsFileSerializer, NewsCommentSerializer, SearchSerializer
from apiV1.serializers.work.inform import NewsSerializer
from work.models import NewsFile
from work.models.inform import News, NewsComment, Search


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = (permissions.IsAuthenticated, NewsPermission)
    pagination_class = PageNumberPaginationTen
    filterset_fields = ('project__slug', 'author')

    @property
    def required_permission(self):
        mapping = {
            'list': 'news.read',
            'retrieve': 'news.read',
            'create': 'news.manage',
            'update': 'news.manage',
            'partial_update': 'news.manage',
            'destroy': 'news.manage'
        }
        return mapping.get(self.action, 'news.read')

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # 1. 슈퍼유저나 work_manager는 전체 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 공개 프로젝트 OR 사용자가 멤버인 프로젝트의 뉴스만 조회
            base_qs = queryset.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()

        # 3. 성능 최적화: N+1 쿼리 방지
        return base_qs.select_related('project', 'author').prefetch_related('files__creator', 'comments__creator')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NewsFileViewSet(viewsets.ModelViewSet):
    queryset = NewsFile.objects.all()
    serializer_class = NewsFileSerializer
    permission_classes = (permissions.IsAuthenticated, NewsPermission)
    filterset_fields = ('news',)
    search_fields = ('file_name', 'description')

    @property
    def required_permission(self):
        mapping = {
            'list': 'news.read',
            'retrieve': 'news.read',
            'create': 'news.manage',
            'update': 'news.manage',
            'partial_update': 'news.manage',
            'destroy': 'news.manage'
        }
        return mapping.get(self.action, 'news.read')

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # 1. 슈퍼유저나 work_manager는 전체 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 공개 프로젝트 OR 사용자가 멤버인 프로젝트의 뉴스 파일만 조회
            base_qs = queryset.filter(
                Q(news__project__is_public=True) | Q(news__project__members__user=user)
            ).distinct()

        # 3. 성능 최적화: N+1 쿼리 방지
        return base_qs.select_related('news__project', 'creator')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class NewsCommentViewSet(viewsets.ModelViewSet):
    queryset = NewsComment.objects.all()
    serializer_class = NewsCommentSerializer
    permission_classes = (permissions.IsAuthenticated, NewsPermission)
    pagination_class = PageNumberPaginationTen
    filterset_fields = ('news__project__slug', 'news', 'parent', 'creator')

    @property
    def required_permission(self):
        mapping = {
            'list': 'news.read',
            'retrieve': 'news.read',
            'create': 'news.comment',
            'update': 'news.comment',
            'partial_update': 'news.comment',
            'destroy': 'news.comment'
        }
        return mapping.get(self.action, 'news.read')

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # 1. 슈퍼유저나 work_manager는 전체 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 공개 프로젝트 OR 사용자가 멤버인 프로젝트의 뉴스 댓글만 조회
            base_qs = queryset.filter(
                Q(news__project__is_public=True) | Q(news__project__members__user=user)
            ).distinct()

        # 3. 성능 최적화: N+1 쿼리 방지
        return base_qs.select_related('news__project', 'creator')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class SearchViewSet(viewsets.ModelViewSet):
    queryset = Search.objects.all()
    serializer_class = SearchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        return queryset.filter(member__user=user)
