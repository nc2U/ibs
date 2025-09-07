from datetime import datetime

from django_filters import BooleanFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.response import Response

from ..permission import *
from ..serializers.board import *


# Board --------------------------------------------------------------------------

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project__slug', 'search_able', 'manager')


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('board', 'parent')


class PostFilterSet(FilterSet):
    class Meta:
        model = Post
        fields = ('board', 'board__project', 'category', 'is_notice', 'is_blind', 'creator')


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.filter(deleted=None)
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = PostFilterSet
    search_fields = ('title', 'content', 'links__link', 'files__file', 'creator__username')

    def copy_and_create(self, request, *args, **kwargs):
        # 복사할 행의 ID를 저장한다.
        origin_pk = kwargs.get('pk')
        project = request.data.get('project')
        board = request.data.get('board')

        try:
            # 기존 행을 가져와서 복사한다.
            org_instance = Post.objects.get(pk=origin_pk)

            add_text = f'<br /><br /><p>[이 게시물은 {self.request.user.username} 님에 의해 {datetime.now()} {org_instance.board.name} 에서 복사됨]</p>'

            # 기존 행의 정보를 사용하여 새로운 행을 생성한다.
            new_instance_data = {
                'project': project if project else None,
                'board': board,
                'category': org_instance.category.pk if org_instance.category else None,
                'lawsuit': org_instance.lawsuit.pk if org_instance.lawsuit else None,
                'title': org_instance.title,
                'execution_date': org_instance.execution_date if org_instance.execution_date else None,
                'content': org_instance.content + add_text,
            }

            # Serializer를 사용해 새로운 행을 생성하고 저장한다.
            serializer = PostSerializer(data=new_instance_data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()

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
    queryset = Comment.objects.all()
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
    queryset = Post.objects.filter(deleted__isnull=False)
    serializer_class = PostInTrashSerializer
