from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apiV1.pagination import PageNumberPaginationTen
from apiV1.permissions.auth_perms import permissions
from apiV1.permissions.work_perms import NewsPermission, QueryPermission
from apiV1.serializers.work import NewsFileSerializer, NewsCommentSerializer, SearchSerializer
from apiV1.serializers.work.inform import NewsSerializer, CustomQuerySerializer
from apiV1.serializers.work.search import (CommentSearchSerializer)
from work.models import NewsFile
from work.models.inform import News, NewsComment, Search, CustomQuery
from work.models.issue import IssueComment


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

    @action(detail=False, methods=['get'], url_path='run')
    def run(self, request):
        """
        통합 검색 실행 엔드포인트
        GET /api/v1/issue-search/run/?q=키워드&scope=all&t=issues&t=comments&t=meetings&t=news
        파라미터:
          q          : 검색어 (필수, 2자 이상)
          scope      : 'all' | 'project' (기본: 'all')
          slug       : 프로젝트 slug (scope='project'일 때)
          t          : 검색 대상 (복수 가능) - issues, comments, meetings, news
          title_only : '1'이면 제목만 검색 (기본: '0')
        """
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'error': '검색어는 2자 이상 입력하세요.'}, status=400)

        scope = request.query_params.get('scope', 'all')
        slug = request.query_params.get('slug', '')
        targets = (set(request.query_params.getlist('t')) or
                   {'issues', 'comments', 'meetings', 'news', 'documents', 'posts'})
        title_only = request.query_params.get('title_only', '0') == '1'
        opened_only = request.query_params.get('opened_only', '0') == '1'
        attach_mode = request.query_params.get('attach_mode', '1')

        results = {}
        if 'issues' in targets:
            results['issues'] = self._search_issues(request.user, q, scope, slug, title_only, opened_only, attach_mode)
        if 'comments' in targets:
            results['comments'] = self._search_comments(request.user, q, scope, slug)
        if 'meetings' in targets:
            results['meetings'] = self._search_meetings(request.user, q, scope, slug, title_only, attach_mode)
        if 'news' in targets:
            results['news'] = self._search_news(request.user, q, scope, slug, title_only, attach_mode)
        if 'documents' in targets:
            results['documents'] = self._search_documents(request.user, q, scope, slug, title_only, attach_mode)
        if 'posts' in targets:
            results['posts'] = self._search_posts(request.user, q, scope, slug, title_only, attach_mode)

        return Response(results)

    @staticmethod
    def _search_issues(user, q, scope, slug, title_only, opened_only, attach_mode):
        from apiV1.views.work.issue import build_issue_queryset
        from apiV1.serializers.work.search import IssueSearchSerializer

        qs = build_issue_queryset(user)
        if opened_only:
            qs = qs.filter(closed__isnull=True)
        if title_only:
            qs = qs.filter(subject__icontains=q)
        else:
            if attach_mode == '1':
                qs = qs.filter(Q(subject__icontains=q) | Q(description__icontains=q))
            elif attach_mode == '2':
                qs = qs.filter(
                    Q(subject__icontains=q) |
                    Q(description__icontains=q) |
                    Q(files__file_name__icontains=q) |
                    Q(files__description__icontains=q)
                ).distinct()
            elif attach_mode == '3':
                qs = qs.filter(
                    Q(files__file_name__icontains=q) |
                    Q(files__description__icontains=q)
                ).distinct()
        if scope == 'project' and slug:
            qs = qs.filter(project__slug=slug)
        elif scope == 'my':
            qs = qs.filter(project__members__user=user)
        return IssueSearchSerializer(qs[:25], many=True).data

    @staticmethod
    def _search_comments(user, q, scope, slug):
        qs = IssueComment.objects.filter(
            content__icontains=q,
            is_private=False,
            issue__project__status='1',
        ).select_related('issue__project', 'creator')

        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            qs = qs.filter(
                Q(issue__project__is_public=True) | Q(issue__project__members__user=user)
            ).distinct()

        if scope == 'project' and slug:
            qs = qs.filter(issue__project__slug=slug)
        elif scope == 'my':
            qs = qs.filter(issue__project__members__user=user)
        return CommentSearchSerializer(qs[:25], many=True).data

    @staticmethod
    def _search_meetings(user, q, scope, slug, title_only, attach_mode):
        from apiV1.serializers.work.search import MeetingSearchSerializer
        from work.models.meeting import Meeting

        if title_only:
            q_expr = Q(title__icontains=q)
        else:
            if attach_mode == '1':
                q_expr = Q(title__icontains=q) | Q(agenda__icontains=q) | Q(decisions__icontains=q)
            elif attach_mode == '2':
                q_expr = (
                        Q(title__icontains=q) |
                        Q(agenda__icontains=q) |
                        Q(decisions__icontains=q) |
                        Q(files__file_name__icontains=q) |
                        Q(files__description__icontains=q)
                )
            elif attach_mode == '3':
                q_expr = Q(files__file_name__icontains=q) | Q(files__description__icontains=q)

        qs = Meeting.objects.filter(q_expr).select_related('project', 'creator')
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            qs = qs.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()
        if scope == 'project' and slug:
            qs = qs.filter(project__slug=slug)
        elif scope == 'my':
            qs = qs.filter(project__members__user=user)
        return MeetingSearchSerializer(qs[:25], many=True).data

    @staticmethod
    def _search_news(user, q, scope, slug, title_only, attach_mode):
        from apiV1.serializers.work.search import NewsSearchSerializer
        from work.models.inform import News

        if title_only:
            q_expr = Q(title__icontains=q)
        else:
            if attach_mode == '1':
                q_expr = Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q)
            elif attach_mode == '2':
                q_expr = (
                        Q(title__icontains=q) |
                        Q(summary__icontains=q) |
                        Q(content__icontains=q) |
                        Q(files__file_name__icontains=q) |
                        Q(files__description__icontains=q)
                )
            elif attach_mode == '3':
                q_expr = Q(files__file_name__icontains=q) | Q(files__description__icontains=q)

        qs = News.objects.filter(q_expr).select_related('project', 'author')
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            qs = qs.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()
        if scope == 'project' and slug:
            qs = qs.filter(project__slug=slug)
        elif scope == 'my':
            qs = qs.filter(project__members__user=user)
        return NewsSearchSerializer(qs[:25], many=True).data

    @staticmethod
    def _search_documents(user, q, scope, slug, title_only, attach_mode):
        from apiV1.serializers.work.search import DocumentSearchSerializer
        from docs.models import Document

        if title_only:
            q_expr = Q(title__icontains=q)
        else:
            if attach_mode == '1':
                q_expr = Q(title__icontains=q) | Q(description__icontains=q)
            elif attach_mode == '2':
                q_expr = (
                        Q(title__icontains=q) |
                        Q(description__icontains=q) |
                        Q(files__file_name__icontains=q) |
                        Q(files__description__icontains=q) |
                        Q(images__image_name__icontains=q) |
                        Q(links__link__icontains=q) |
                        Q(links__description__icontains=q)
                )
            elif attach_mode == '3':
                q_expr = (
                        Q(files__file_name__icontains=q) |
                        Q(images__image_name__icontains=q) |
                        Q(links__link__icontains=q)
                )

        # 소프트 딜리트 필터: deleted=None (SoftDeleteManager가 적용되어 있으므로 기본 objects 사용 가능)
        qs = Document.objects.filter(q_expr, issue_project__status='1').select_related('issue_project', 'creator')

        # 권한 제어: 사용자가 관리자가 아닌 경우 공개 프로젝트 혹은 멤버십 프로젝트 문서만 허용
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            qs = qs.filter(
                Q(issue_project__is_public=True) | Q(issue_project__members__user=user)
            ).distinct()

        if scope == 'project' and slug:
            qs = qs.filter(issue_project__slug=slug)
        elif scope == 'my':
            qs = qs.filter(issue_project__members__user=user)
        return DocumentSearchSerializer(qs[:25], many=True).data

    @staticmethod
    def _search_posts(user, q, scope, slug, title_only, attach_mode):
        from apiV1.serializers.work.search import PostSearchSerializer
        from forum.models import Post

        if title_only:
            q_expr = Q(title__icontains=q)
        else:
            if attach_mode == '1':
                q_expr = Q(title__icontains=q) | Q(content__icontains=q)
            elif attach_mode == '2':
                q_expr = (
                        Q(title__icontains=q) |
                        Q(content__icontains=q) |
                        Q(files__file_name__icontains=q) |
                        Q(images__image_name__icontains=q)
                )
            elif attach_mode == '3':
                q_expr = Q(files__file_name__icontains=q) | Q(images__image_name__icontains=q)

        # 소프트 딜리트 필터: deleted=None 및 프로젝트 활성 상태(status='1')
        qs = Post.objects.filter(q_expr, deleted__isnull=True,
                                 forum__project__status='1').select_related('forum__project', 'creator')

        # 권한 제어: 공개 프로젝트 혹은 멤버십 프로젝트 내 게시판 게시글만 허용
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            qs = qs.filter(
                Q(forum__project__is_public=True) | Q(forum__project__members__user=user)
            ).distinct()

        if scope == 'project' and slug:
            qs = qs.filter(forum__project__slug=slug)
        elif scope == 'my':
            qs = qs.filter(forum__project__members__user=user)
        return PostSearchSerializer(qs[:25], many=True).data


class CustomQueryViewSet(viewsets.ModelViewSet):
    queryset = CustomQuery.objects.all()
    serializer_class = CustomQuerySerializer
    permission_classes = (permissions.IsAuthenticated, QueryPermission)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = ('project__slug', 'target_type', 'is_public')
    search_fields = ('name',)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs

        # 본인의 개인/공용 양식 OR 타인의 공용 양식
        from django.db.models import Q
        return qs.filter(
            Q(user=user) | Q(is_public=True)
        ).distinct()

