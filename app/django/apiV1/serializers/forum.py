import json
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from rest_framework import serializers

from _utils.file_service import FileService
from accounts.models import Profile
from apiV1.serializers.accounts import SimpleUserSerializer
from forum.models import Forum, PostCategory, Post, PostFile, PostImage, Comment, Tag


# Forum --------------------------------------------------------------------------
class ForumSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField(read_only=True)
    all_post_count = serializers.SerializerMethodField(read_only=True)
    last_post = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Forum
        fields = ('pk', 'project', 'name', 'description', 'parent',
                  'search_able', 'manager_only', 'manager', 'post_count', 'all_post_count', 'last_post')

    @staticmethod
    def get_post_count(obj):
        if hasattr(obj, 'annotated_post_count'):
            return obj.annotated_post_count
        if not hasattr(obj, '_cached_post_count'):
            obj._cached_post_count = obj.post_set.filter(deleted=None, is_faq=False).count()
        return obj._cached_post_count

    def get_all_post_count(self, obj):
        if hasattr(obj, 'annotated_all_post_count'):
            return obj.annotated_all_post_count
        post_count = self.get_post_count(obj)
        comment_count = Comment.objects.filter(post__forum=obj, post__deleted=None, post__is_faq=False).count()
        return post_count + comment_count

    def get_last_post(self, obj):
        last_post = obj.post_set.filter(deleted=None, is_faq=False).select_related('creator').order_by('-created').first()
        if last_post:
            request = self.context.get('request')
            user = request.user if request else None
            title = last_post.title

            # 비밀글 / 블라인드글 제목 마스킹
            if last_post.is_secret or last_post.is_blind:
                is_authorized = False
                if user and user.is_authenticated:
                    if user.is_superuser or getattr(user, 'work_manager', False):
                        is_authorized = True
                    elif last_post.creator_id and last_post.creator_id == user.pk:
                        is_authorized = True
                    elif obj.manager.filter(pk=user.pk).exists():
                        is_authorized = True
                if not is_authorized:
                    title = '비밀글입니다.' if last_post.is_secret else '블라인드 처리된 게시물입니다.'

            return {
                'pk': last_post.pk,
                'is_notice': last_post.is_notice,
                'title': title,
                'creator': last_post.creator.username if last_post.creator else None,
                'created': last_post.created,
            }
        return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = ('pk', 'forum', 'color', 'name', 'parent', 'order', 'is_manager_only')


class FilesInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFile
        fields = ('pk', 'post', 'file', 'file_name', 'file_size', 'file_type', 'hit')


class PostSerializer(serializers.ModelSerializer):
    forum_name = serializers.SlugField(source='forum', read_only=True)
    cate_name = serializers.SlugField(source='category', read_only=True)
    files = FilesInPostSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    my_like = serializers.SerializerMethodField(read_only=True)
    scrape = serializers.SerializerMethodField(read_only=True)
    my_scrape = serializers.SerializerMethodField(read_only=True)
    my_blame = serializers.SerializerMethodField(read_only=True)
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'forum', 'forum_name', 'category', 'cate_name', 'title',
                  'content', 'hit', 'like', 'my_like', 'scrape', 'my_scrape', 'blame',
                  'my_blame', 'ip', 'device', 'is_secret', 'password', 'is_hide_comment',
                  'is_notice', 'is_faq', 'is_blind', 'deleted', 'files', 'comments', 'creator',
                  'created', 'updated', 'is_new', 'prev_pk', 'next_pk')
        read_only_fields = ('ip', 'comments')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        user = request.user if request else None

        # 비밀글(is_secret) 본문 및 파일 마스킹
        if instance.is_secret:
            is_authorized = False
            if user and user.is_authenticated:
                if user.is_superuser or getattr(user, 'work_manager', False):
                    is_authorized = True
                elif instance.creator_id and instance.creator_id == user.pk:
                    is_authorized = True
                elif instance.forum and instance.forum.manager.filter(pk=user.pk).exists():
                    is_authorized = True

            if not is_authorized:
                data['content'] = '비밀글입니다.'
                data['files'] = []

        # 블라인드(is_blind) 마스킹 (제목 및 본문 모두 은닉)
        if instance.is_blind:
            is_manager = False
            if user and user.is_authenticated:
                if user.is_superuser or getattr(user, 'work_manager', False):
                    is_manager = True
                elif instance.forum and instance.forum.manager.filter(pk=user.pk).exists():
                    is_manager = True
            if not is_manager:
                data['title'] = '블라인드 처리된 게시물입니다.'
                data['content'] = '블라인드 처리된 게시물입니다.'
                data['files'] = []

        # IP 및 기기(device) 정보 일반 사용자 비노출 (관리자/포럼 매니저/작성자 본인만 노출)
        is_admin_or_author = False
        if user and user.is_authenticated:
            if user.is_superuser or getattr(user, 'work_manager', False):
                is_admin_or_author = True
            elif instance.creator_id and instance.creator_id == user.pk:
                is_admin_or_author = True
            elif instance.forum and instance.forum.manager.filter(pk=user.pk).exists():
                is_admin_or_author = True
        if not is_admin_or_author:
            data.pop('ip', None)
            data.pop('device', None)

        return data

    def _get_user_cache(self, user):
        """context를 활용하여 동일 요청 내 Profile/Like/Blame/Scrape 재조회 방지 캐시"""
        if not user or not user.is_authenticated:
            return None
        if '_post_user_cache' not in self.context:
            profile, _ = Profile.objects.get_or_create(user=user)
            self.context['_post_user_cache'] = {
                'profile': profile,
                'liked_ids': set(profile.like_posts.values_list('pk', flat=True)),
                'blamed_ids': set(profile.blame_posts.values_list('pk', flat=True)),
                'scraped_ids': set(user.postscrape_set.values_list('post_id', flat=True)),
            }
        return self.context['_post_user_cache']

    def _get_filtered_queryset(self, obj=None):
        """prev_pk / next_pk 계산용 필터된 쿼리셋 (동일 포럼 및 삭제 제외 강제)"""
        queryset = Post.objects.filter(deleted=None)
        query = self.context['request'].query_params
        forum = query.get('forum')
        is_notice_param = query.get('is_notice')
        is_faq_param = query.get('is_faq')
        category = query.get('category')
        search = query.get('search')

        if forum:
            queryset = queryset.filter(forum_id=forum)
        elif obj and obj.forum_id:
            queryset = queryset.filter(forum_id=obj.forum_id)

        if is_notice_param == 'true':
            queryset = queryset.filter(is_notice=True)
        elif is_notice_param == 'false':
            queryset = queryset.filter(is_notice=False)
        if is_faq_param == 'true':
            queryset = queryset.filter(is_faq=True)
        elif is_faq_param == 'false':
            queryset = queryset.filter(is_faq=False)
        if category:
            queryset = queryset.filter(category_id=category)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(files__file__icontains=search) |
                Q(creator__username__icontains=search)
            ).distinct()
        return queryset

    @staticmethod
    def get_scrape(obj):
        if hasattr(obj, 'scrape_count'):
            return obj.scrape_count
        return obj.postscrape_set.count()

    def get_my_scrape(self, obj):
        user = self.context['request'].user
        cache = self._get_user_cache(user)
        if not cache:
            return False
        return obj.pk in cache['scraped_ids']

    def get_my_like(self, obj):
        user = self.context['request'].user
        cache = self._get_user_cache(user)
        if not cache:
            return False
        return obj.pk in cache['liked_ids']

    def get_my_blame(self, obj):
        user = self.context['request'].user
        cache = self._get_user_cache(user)
        if not cache:
            return False
        return obj.pk in cache['blamed_ids']

    def get_prev_pk(self, obj):
        view = self.context.get('view')
        if view and view.action != 'retrieve':
            return None
        prev_obj = self._get_filtered_queryset(obj).filter(created__lt=obj.created).first()
        return prev_obj.pk if prev_obj else None

    def get_next_pk(self, obj):
        view = self.context.get('view')
        if view and view.action != 'retrieve':
            return None
        next_obj = self._get_filtered_queryset(obj).filter(created__gt=obj.created).order_by('created').first()
        return next_obj.pk if next_obj else None

    @staticmethod
    def _normalize_url(url):
        """URL 정규화 헬퍼. 스킴이 없으면 http:// 를 기본으로 추가."""

        def split_url(u):
            try:
                return list(urlsplit(u))
            except ValueError:
                raise ValidationError('올바른 URL 형식이 아닙니다.', code='invalid')

        if url:
            url_fields = split_url(url)
            if not url_fields[0]:
                url_fields[0] = 'http'
            if not url_fields[1]:
                url_fields[1] = url_fields[2]
                url_fields[2] = ''
                url_fields = split_url(urlunsplit(url_fields))
            url = urlunsplit(url_fields)
        return url

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None
        category = attrs.get('category') or (self.instance.category if self.instance else None)
        forum = attrs.get('forum') or (self.instance.forum if self.instance else None)

        # 0. 카테고리가 해당 포럼에 속하는지 검증
        if category and forum and category.forum_id != forum.pk:
            raise serializers.ValidationError({
                'category': '선택한 카테고리가 해당 게시판에 속하지 않습니다.'
            })

        # 1. 포럼 단위 관리자 전용 검사
        if forum and getattr(forum, 'manager_only', False):
            if user and not user.is_superuser:
                is_manager = forum.manager.filter(pk=user.pk).exists()
                if not is_manager:
                    raise serializers.ValidationError({
                        'forum': '해당 게시판은 게시판 담당 관리자만 작성할 수 있습니다.'
                    })

        # 2. 카테고리 단위 관리자 전용 검사
        if category and getattr(category, 'is_manager_only', False):
            # superuser는 manager 체크 통과
            if user and not user.is_superuser:
                is_manager = forum and forum.manager.filter(pk=user.pk).exists()
                if not is_manager:
                    raise serializers.ValidationError({
                        'category': '해당 카테고리는 게시판 담당 관리자만 작성할 수 있습니다.'
                    })

        # 3. FAQ 지정 권한 검사
        is_faq = attrs.get('is_faq')
        if is_faq and user and not user.is_superuser:
            is_manager = forum and forum.manager.filter(pk=user.pk).exists()
            if not is_manager:
                raise serializers.ValidationError({
                    'is_faq': 'FAQ 지정은 게시판 담당 관리자만 설정할 수 있습니다.'
                })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['ip'] = request.META.get('REMOTE_ADDR') if request else None
        validated_data['device'] = (request.META.get('HTTP_USER_AGENT') if request else None) or ''
        post = Post.objects.create(**validated_data)

        # Files 처리
        FileService.manage_files(
            instance=post,
            initial_data=self.initial_data,
            file_model=PostFile,
            related_name='post',
            new_files_key='newFiles',
        )

        return post

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request:
            if request.META.get('REMOTE_ADDR'):
                validated_data['ip'] = request.META.get('REMOTE_ADDR')
            if request.META.get('HTTP_USER_AGENT'):
                validated_data['device'] = request.META.get('HTTP_USER_AGENT')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Files 처리
        FileService.manage_files(
            instance=instance,
            initial_data=self.initial_data,
            file_model=PostFile,
            related_name='post',
            new_files_key='newFiles',
        )

        return instance


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('pk', 'like')

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        # 개선: get() → get_or_create() (DoesNotExist 방어)
        profile, _ = Profile.objects.get_or_create(user=user)

        if profile.like_posts.filter(pk=instance.pk).exists():
            # 개선: F() 표현식으로 원자적 감소 (Race Condition 방지)
            Post.objects.filter(pk=instance.pk, like__gt=0).update(like=F('like') - 1)
            profile.like_posts.remove(instance)
        else:
            Post.objects.filter(pk=instance.pk).update(like=F('like') + 1)
            profile.like_posts.add(instance)

        instance.refresh_from_db()
        return instance


class PostBlameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('pk', 'blame')

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile, _ = Profile.objects.get_or_create(user=user)

        if profile.blame_posts.filter(pk=instance.pk).exists():
            Post.objects.filter(pk=instance.pk, blame__gt=0).update(blame=F('blame') - 1)
            profile.blame_posts.remove(instance)
        else:
            Post.objects.filter(pk=instance.pk).update(blame=F('blame') + 1)
            profile.blame_posts.add(instance)

        instance.refresh_from_db()
        return instance


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFile
        fields = ('pk', 'post', 'file', 'file_name', 'file_size', 'file_type', 'hit', 'created')


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ('pk', 'post', 'image')


class SimplePostInCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('pk', 'forum', 'is_secret', 'creator')


class CommentSerializer(serializers.ModelSerializer):
    post = SimplePostInCommentSerializer(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    my_like = serializers.SerializerMethodField(read_only=True)
    my_blame = serializers.SerializerMethodField(read_only=True)
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('pk', 'post', 'content', 'parent', 'replies', 'like', 'my_like',
                  'blame', 'my_blame', 'ip', 'device', 'secret', 'creator', 'created')
        read_only_fields = ('ip',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        user = request.user if request else None

        # 비밀 댓글(secret=True) 혹은 비밀글의 댓글 마스킹
        is_post_secret = bool(instance.post and getattr(instance.post, 'is_secret', False))
        if instance.secret or is_post_secret:
            is_authorized = False
            if user and user.is_authenticated:
                if user.is_superuser or getattr(user, 'work_manager', False):
                    is_authorized = True
                elif instance.creator_id and instance.creator_id == user.pk:
                    is_authorized = True
                elif instance.post and instance.post.creator_id and instance.post.creator_id == user.pk:
                    is_authorized = True
                elif (instance.post and instance.post.forum and
                      instance.post.forum.manager.filter(pk=user.pk).exists()):
                    is_authorized = True

            if not is_authorized:
                data['content'] = '비밀 댓글입니다.'

        # IP 및 기기(device) 정보 일반 사용자 비노출 (관리자/포럼 매니저/작성자 본인만 노출)
        is_admin_or_author = False
        if user and user.is_authenticated:
            if user.is_superuser or getattr(user, 'work_manager', False):
                is_admin_or_author = True
            elif instance.creator_id and instance.creator_id == user.pk:
                is_admin_or_author = True
            elif (instance.post and instance.post.forum and
                  instance.post.forum.manager.filter(pk=user.pk).exists()):
                is_admin_or_author = True
        if not is_admin_or_author:
            data.pop('ip', None)
            data.pop('device', None)

        return data

    def get_replies(self, instance):
        # 개선: bind 대신 인스턴스화 시 context를 직접 넘겨주어 DRF context 유실 예방
        serializer = self.__class__(instance.replies, many=True, context=self.context)
        return serializer.data

    def _get_comment_cache(self, user):
        """context를 활용하여 동일 요청 내 Profile/Like/Blame 재조회 방지 캐시"""
        if not user or not user.is_authenticated:
            return None
        if '_comment_user_cache' not in self.context:
            profile, _ = Profile.objects.get_or_create(user=user)
            self.context['_comment_user_cache'] = {
                'profile': profile,
                'liked_ids': set(profile.like_comments.values_list('pk', flat=True)),
                'blamed_ids': set(profile.blame_comments.values_list('pk', flat=True)),
            }
        return self.context['_comment_user_cache']

    def get_my_like(self, obj):
        user = self.context['request'].user
        cache = self._get_comment_cache(user)
        if not cache:
            return False
        return obj.pk in cache['liked_ids']

    def get_my_blame(self, obj):
        user = self.context['request'].user
        cache = self._get_comment_cache(user)
        if not cache:
            return False
        return obj.pk in cache['blamed_ids']

    @transaction.atomic
    def create(self, validated_data):
        post_id = self.initial_data.get('post')
        # 개선: post_id 데이터 부재 시 500 에러 방지를 위한 밸리데이션 추가
        if not post_id:
            raise serializers.ValidationError({'post': '게시글 정보가 누락되었습니다.'})
        validated_data['post_id'] = post_id
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        validated_data['device'] = self.context.get('request').META.get('HTTP_USER_AGENT')
        comment = Comment.objects.create(**validated_data)
        return comment

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        validated_data['device'] = self.context.get('request').META.get('HTTP_USER_AGENT')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('pk', 'like')

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile, _ = Profile.objects.get_or_create(user=user)

        if profile.like_comments.filter(pk=instance.pk).exists():
            Comment.objects.filter(pk=instance.pk, like__gt=0).update(like=F('like') - 1)
            profile.like_comments.remove(instance)
        else:
            Comment.objects.filter(pk=instance.pk).update(like=F('like') + 1)
            profile.like_comments.add(instance)

        instance.refresh_from_db()
        return instance


class CommentBlameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('pk', 'blame')

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile, _ = Profile.objects.get_or_create(user=user)

        if profile.blame_comments.filter(pk=instance.pk).exists():
            Comment.objects.filter(pk=instance.pk, blame__gt=0).update(blame=F('blame') - 1)
            profile.blame_comments.remove(instance)
        else:
            Comment.objects.filter(pk=instance.pk).update(blame=F('blame') + 1)
            profile.blame_comments.add(instance)

        instance.refresh_from_db()
        return instance


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('pk', 'forum', 'name', 'post')


class PostInTrashSerializer(serializers.ModelSerializer):
    forum_name = serializers.SlugField(source='forum', read_only=True)
    cate_name = serializers.SlugField(source='category', read_only=True)
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'forum_name', 'cate_name', 'title', 'content', 'creator', 'created', 'deleted')

    def update(self, instance, validated_data):
        instance.restore()
        return instance
