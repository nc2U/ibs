from django.db.models import Count, F, Q
from django.utils import timezone
from django_filters import BooleanFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apiV1.permissions.auth_perms import permissions
from apiV1.permissions.work_perms import ForumPermission
from forum.models import Forum, PostCategory, Post, PostFile, PostImage, Comment, Tag
from ..serializers.forum import ForumSerializer, CategorySerializer, PostSerializer, PostLikeSerializer, \
    PostBlameSerializer, ImageSerializer, FileSerializer, CommentSerializer, \
    CommentLikeSerializer, CommentBlameSerializer, TagSerializer, PostInTrashSerializer


# Forum --------------------------------------------------------------------------

class ForumViewSet(viewsets.ModelViewSet):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)
    filterset_fields = ('project__slug', 'search_able', 'manager_only', 'manager')

    @property
    def required_permission(self):
        mapping = {
            'list': 'forum.read',
            'retrieve': 'forum.read',
            'create': 'forum.manage',
            'update': 'forum.manage',
            'partial_update': 'forum.manage',
            'destroy': 'forum.manage'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().annotate(
            annotated_post_count=Count(
                'post',
                filter=Q(post__deleted=None, post__is_faq=False),
                distinct=True
            ),
            annotated_all_post_count=Count(
                'post',
                filter=Q(post__deleted=None, post__is_faq=False),
                distinct=True
            ) + Count(
                'post__comments',
                filter=Q(post__deleted=None, post__is_faq=False),
                distinct=True
            )
        )
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset.select_related('project').prefetch_related('manager').order_by('id')
        # 행 보안: 사용자가 속한 워크스페이스의 게시판이거나 공개 워크스페이스의 게시판만 노출
        return queryset.filter(
            Q(project__is_public=True) | Q(project__members__user=user)
        ).distinct().select_related('project').prefetch_related('manager').order_by('id')


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)
    filterset_fields = ('forum', 'parent', 'is_manager_only')

    @property
    def required_permission(self):
        # 카테고리 관리는 게시판 설정 관리 권한(forum.manage)으로 일원화
        mapping = {
            'list': 'forum.read',
            'retrieve': 'forum.read',
            'create': 'forum.manage',
            'update': 'forum.manage',
            'partial_update': 'forum.manage',
            'destroy': 'forum.manage'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset.select_related('forum')
        # 행 보안: 사용자가 속한 워크스페이스의 게시판 카테고리 혹은 공개 워크스페이스의 카테고리만 노출
        return queryset.filter(
            Q(forum__project__is_public=True) | Q(forum__project__members__user=user)
        ).distinct().select_related('forum')


class PostFilterSet(FilterSet):
    class Meta:
        model = Post
        fields = ('forum', 'forum__project', 'forum__project__slug', 'category', 'is_notice', 'is_faq', 'is_blind', 'creator')


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.filter(deleted=None).select_related(
        'forum', 'category', 'creator__profile'
    ).prefetch_related('files')
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)
    filterset_class = PostFilterSet
    search_fields = ('title', 'content', 'files__file', 'creator__username')

    @property
    def required_permission(self):
        mapping = {
            'list': 'forum.read',
            'retrieve': 'forum.read',
            'hit': 'forum.read',
            'copy_and_create': 'forum.create',
            'create': 'forum.create',
            'update': 'forum.update',
            'partial_update': 'forum.update',
            'destroy': 'forum.delete'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().annotate(
            scrape_count=Count('postscrape', distinct=True)
        )
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        # 행 보안: 사용자가 권한을 가진 워크스페이스의 게시판 글만 조회
        return queryset.filter(
            Q(forum__project__is_public=True) | Q(forum__project__members__user=user)
        ).distinct()

    @action(detail=True, methods=['post'], url_path='hit')
    def hit(self, request, *args, **kwargs):
        instance = self.get_object()
        Post.objects.filter(pk=instance.pk).update(hit=F('hit') + 1)
        instance.refresh_from_db(fields=['hit'])
        return Response({'hit': instance.hit}, status=status.HTTP_200_OK)

    # 개선: API 라우터에 복사 액션이 정상 등록되도록 @action 데코레이터 추가
    @action(detail=True, methods=['post'], url_path='copy')
    def copy_and_create(self, request, *args, **kwargs):
        # 복사할 원본 행을 self.get_object()로 조회 (RLS 및 권한 필터를 거쳐 IDOR 차단)
        org_instance = self.get_object()
        target_forum_id = request.data.get('forum')
        if not target_forum_id:
            return Response({'detail': '대상 게시판 정보가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        target_forum = Forum.objects.select_related('project').prefetch_related('manager').filter(pk=target_forum_id).first()
        if not target_forum:
            return Response({'detail': '대상 게시판을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 대상 프로젝트에 대한 글쓰기 권한 검증 (교차 프로젝트 무인가 복사 차단)
        user = request.user
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            target_project = target_forum.project
            user_perms = target_project.get_user_permissions(user)
            if 'forum.create' not in user_perms:
                return Response({'detail': '대상 워크스페이스에 게시글을 작성할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            if target_forum.manager_only and not target_forum.manager.filter(pk=user.pk).exists():
                return Response({'detail': '대상 게시판은 관리자 전용 게시판입니다.'}, status=status.HTTP_403_FORBIDDEN)

        now_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        add_text = f'<br /><br /><p>[이 게시물은 {user.username} 님에 의해 {now_str} {org_instance.forum.name} 에서 복사됨]</p>'

        # 동일 포럼 복사 시 카테고리 유지, 타 포럼 복사 시 외래키 오염 방지를 위해 카테고리 초기화
        category_pk = None
        if org_instance.category and org_instance.category.forum_id == target_forum.pk:
            category_pk = org_instance.category.pk

        new_instance_data = {
            'forum': target_forum.pk,
            'category': category_pk,
            'title': org_instance.title,
            'content': org_instance.content + add_text,
        }

        # Serializer를 사용해 새로운 행을 생성하고 저장한다.
        serializer = PostSerializer(data=new_instance_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(creator=user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostLikeSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)
    http_method_names = ['put', 'patch', 'head', 'options']

    @property
    def required_permission(self):
        return 'forum.read'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'work_manager', False):
            return self.queryset
        return self.queryset.filter(
            Q(forum__project__is_public=True) | Q(forum__project__members__user=user)
        ).distinct()


class PostBlameViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostBlameSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)
    http_method_names = ['put', 'patch', 'head', 'options']

    @property
    def required_permission(self):
        return 'forum.read'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'work_manager', False):
            return self.queryset
        return self.queryset.filter(
            Q(forum__project__is_public=True) | Q(forum__project__members__user=user)
        ).distinct()


class PostFileViewSet(viewsets.ModelViewSet):
    queryset = PostFile.objects.all()
    serializer_class = FileSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)

    @property
    def required_permission(self):
        mapping = {
            'list': 'forum.read',
            'retrieve': 'forum.read',
            'hit': 'forum.read',
            'create': 'forum.update',
            'update': 'forum.update',
            'partial_update': 'forum.update',
            'destroy': 'forum.update'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset.select_related('post__forum__project', 'post__creator')
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs.order_by('id')
        # RLS 및 비밀글/블라인드 파일 접근 통제
        accessible_workspace = Q(post__forum__project__is_public=True) | Q(post__forum__project__members__user=user)
        accessible_secret = (
            Q(post__is_secret=False, post__is_blind=False) |
            Q(post__creator=user) |
            Q(post__forum__manager=user)
        )
        return qs.filter(accessible_workspace & accessible_secret).distinct().order_by('id')

    @action(detail=True, methods=['post'], url_path='hit')
    def hit(self, request, *args, **kwargs):
        instance = self.get_object()
        PostFile.objects.filter(pk=instance.pk).update(hit=F('hit') + 1)
        instance.refresh_from_db(fields=['hit'])
        return Response({'hit': instance.hit}, status=status.HTTP_200_OK)


class PostImageViewSet(viewsets.ModelViewSet):
    queryset = PostImage.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)

    @property
    def required_permission(self):
        mapping = {
            'list': 'forum.read',
            'retrieve': 'forum.read',
            'create': 'forum.update',
            'update': 'forum.update',
            'partial_update': 'forum.update',
            'destroy': 'forum.update'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset.select_related('post__forum__project', 'post__creator')
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs.order_by('id')
        # RLS 및 비밀글/블라인드 이미지 접근 통제
        accessible_workspace = Q(post__forum__project__is_public=True) | Q(post__forum__project__members__user=user)
        accessible_secret = (
            Q(post__is_secret=False, post__is_blind=False) |
            Q(post__creator=user) |
            Q(post__forum__manager=user)
        )
        return qs.filter(accessible_workspace & accessible_secret).distinct().order_by('id')


class CommentFilterSet(FilterSet):
    is_comment = BooleanFilter(field_name='parent', lookup_expr='isnull', label='댓글')

    class Meta:
        model = Comment
        fields = ('creator', 'post', 'is_comment')


class CommentViewSet(viewsets.ModelViewSet):
    # 개선: N+1 쿼리 방지를 위한 select_related 및 prefetch_related 적용
    queryset = Comment.objects.all().select_related(
        'creator__profile', 'post__forum__project', 'post__creator'
    ).prefetch_related('replies__creator__profile')
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)
    filterset_class = CommentFilterSet

    @property
    def required_permission(self):
        mapping = {
            'list': 'forum.read',
            'retrieve': 'forum.read',
            'create': 'forum.create',
            'update': 'forum.update',
            'partial_update': 'forum.update',
            'destroy': 'forum.delete'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        # 행 보안: 사용자가 권한을 가진 워크스페이스의 게시판 댓글만 조회
        # 비밀글/댓글숨김 격리: 일반 글이거나, 본인이 작성자/포럼매니저인 경우에만 댓글 조회 허용
        accessible_workspace = Q(post__forum__project__is_public=True) | Q(post__forum__project__members__user=user)
        authorized_user = Q(post__creator=user) | Q(post__forum__manager=user)
        secret_guard = Q(post__is_secret=False) | authorized_user
        hide_guard = Q(post__is_hide_comment=False) | authorized_user

        return queryset.filter(accessible_workspace & secret_guard & hide_guard).distinct()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class CommentLikeViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentLikeSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)
    http_method_names = ['put', 'patch', 'head', 'options']

    @property
    def required_permission(self):
        return 'forum.read'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'work_manager', False):
            return self.queryset
        return self.queryset.filter(
            Q(post__forum__project__is_public=True) | Q(post__forum__project__members__user=user)
        ).distinct()


class CommentBlameViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentBlameSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)
    http_method_names = ['put', 'patch', 'head', 'options']

    @property
    def required_permission(self):
        return 'forum.read'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'work_manager', False):
            return self.queryset
        return self.queryset.filter(
            Q(post__forum__project__is_public=True) | Q(post__forum__project__members__user=user)
        ).distinct()


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.IsAuthenticated, ForumPermission)

    @property
    def required_permission(self):
        mapping = {
            'list': 'forum.read',
            'retrieve': 'forum.read',
            'create': 'forum.manage',
            'update': 'forum.manage',
            'partial_update': 'forum.manage',
            'destroy': 'forum.manage'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset.select_related('forum__project')
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs.order_by('id')
        return qs.filter(
            Q(forum__project__is_public=True) | Q(forum__project__members__user=user)
        ).distinct().order_by('id')


class PostInTrashViewSet(PostViewSet):
    serializer_class = PostInTrashSerializer

    # 휴지통 내에서는 hit 및 복사 액션 비활성화
    @action(detail=True, methods=['post'], url_path='hit')
    def hit(self, request, *args, **kwargs):
        return Response({'detail': '휴지통 내 게시물은 조회수를 갱신할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='copy')
    def copy_and_create(self, request, *args, **kwargs):
        return Response({'detail': '휴지통 내 게시물은 복사할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.filter(deleted__isnull=False).select_related('forum', 'category', 'creator')
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        return queryset.filter(
            Q(forum__project__is_public=True) | Q(forum__project__members__user=user)
        ).distinct()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # [H-2] 휴지통에서 삭제 시 모델 기본 delete()의 소프트 삭제 대신 실제 DB 레코드 영구 삭제 수행
        Post.objects.filter(pk=instance.pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
