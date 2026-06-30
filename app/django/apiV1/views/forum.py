from django.utils import timezone
from django_filters import BooleanFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly
from forum.models import Forum, PostCategory, Post, PostLink, PostFile, PostImage, Comment, Tag
from ..serializers.forum import ForumSerializer, CategorySerializer, PostSerializer, PostLikeSerializer, \
    PostBlameSerializer, ImageSerializer, LinkSerializer, FileSerializer, CommentSerializer, \
    CommentLikeSerializer, CommentBlameSerializer, TagSerializer, PostInTrashSerializer


# Forum --------------------------------------------------------------------------

class ForumViewSet(viewsets.ModelViewSet):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('project__slug', 'search_able', 'manager')


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('forum', 'parent')


class PostFilterSet(FilterSet):
    class Meta:
        model = Post
        fields = ('forum', 'forum__project', 'category', 'is_notice', 'is_blind', 'creator')


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.filter(deleted=None).select_related(
        'forum', 'category', 'creator'
    ).prefetch_related('links', 'files')
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = PostFilterSet
    search_fields = ('title', 'content', 'links__link', 'files__file', 'creator__username')

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

    # 개선: API 라우터에 복사 액션이 정상 등록되도록 @action 데코레이터 추가
    @action(detail=True, methods=['post'], url_path='copy')
    def copy_and_create(self, request, *args, **kwargs):
        # 복사할 행의 ID를 저장한다.
        origin_pk = kwargs.get('pk')
        forum = request.data.get('forum')

        try:
            # 기존 행을 가져와서 복사한다.
            org_instance = Post.objects.get(pk=origin_pk)

            # 개선: timezone을 사용하여 로컬 타임존 일관성 유지
            now_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
            add_text = f'<br /><br /><p>[이 게시물은 {self.request.user.username} 님에 의해 {now_str} {org_instance.forum.name} 에서 복사됨]</p>'

            # 개선: Post 모델에 존재하지 않는 project, lawsuit, execution_date 필드 제거 및 정합성 매핑
            new_instance_data = {
                'forum': forum,
                'category': org_instance.category.pk if org_instance.category else None,
                'title': org_instance.title,
                'content': org_instance.content + add_text,
            }

            # Serializer를 사용해 새로운 행을 생성하고 저장한다.
            serializer = PostSerializer(data=new_instance_data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            # 개선: creator를 명시적으로 저장해 복사한 사용자가 작성자가 되도록 지정
            serializer.save(creator=self.request.user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Post.DoesNotExist:
            return Response({'detail': 'Original Post object does not exist'}, status=status.HTTP_404_NOT_FOUND)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostLikeSerializer
    permission_classes = (permissions.IsAuthenticated,)


class PostBlameViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostBlameSerializer
    permission_classes = (permissions.IsAuthenticated,)


class PostLinkViewSet(viewsets.ModelViewSet):
    queryset = PostLink.objects.all()
    serializer_class = LinkSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class PostFileViewSet(viewsets.ModelViewSet):
    queryset = PostFile.objects.all()
    serializer_class = FileSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class PostImageViewSet(viewsets.ModelViewSet):
    queryset = PostImage.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class CommentFilterSet(FilterSet):
    is_comment = BooleanFilter(field_name='parent', lookup_expr='isnull', label='댓글')

    class Meta:
        model = Comment
        fields = ('creator', 'post', 'is_comment', 'creator')


class CommentViewSet(viewsets.ModelViewSet):
    # 개선: N+1 쿼리 방지를 위한 select_related 및 prefetch_related 적용
    queryset = Comment.objects.all().select_related('creator', 'post__forum').prefetch_related('replies')
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = CommentFilterSet

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class CommentLikeViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentLikeSerializer
    permission_classes = (permissions.IsAuthenticated,)


class CommentBlameViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentBlameSerializer
    permission_classes = (permissions.IsAuthenticated,)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class PostInTrashViewSet(PostViewSet):
    serializer_class = PostInTrashSerializer

    # 개선: 쿼리셋 정적 재정의 대신 get_queryset() 오버라이딩 적용
    def get_queryset(self):
        return Post.objects.filter(deleted__isnull=False).select_related('forum', 'category', 'creator')
