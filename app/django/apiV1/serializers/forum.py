import json
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from rest_framework import serializers

from _utils.file_service import FileService
from accounts.models import Profile
from apiV1.serializers.accounts import SimpleUserSerializer
from forum.models import Forum, PostCategory, Post, PostLink, PostFile, PostImage, Comment, Tag


# Forum --------------------------------------------------------------------------
class ForumSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField(read_only=True)
    all_post_count = serializers.SerializerMethodField(read_only=True)
    last_post = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Forum
        fields = ('pk', 'project', 'name', 'description', 'parent',
                  'search_able', 'manager', 'post_count', 'all_post_count', 'last_post')

    @staticmethod
    def get_post_count(obj):
        return obj.post_set.count()

    @staticmethod
    def get_all_post_count(obj):
        comment_count = Comment.objects.filter(post__forum=obj).count()
        return obj.post_set.count() + comment_count

    @staticmethod
    def get_last_post(obj):
        last_post = obj.post_set.select_related('creator').order_by('-created').first()
        if last_post:
            return {
                'pk': last_post.pk,
                'title': last_post.title,
                'creator': last_post.creator.username if last_post.creator else None,
                'created': last_post.created,
            }
        return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = ('pk', 'forum', 'color', 'name', 'parent', 'order')


class LinksInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLink
        fields = ('pk', 'post', 'link', 'hit')


class FilesInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFile
        fields = ('pk', 'post', 'file', 'file_name', 'file_size', 'file_type', 'hit')


class PostSerializer(serializers.ModelSerializer):
    forum_name = serializers.SlugField(source='forum', read_only=True)
    cate_name = serializers.SlugField(source='category', read_only=True)
    links = LinksInPostSerializer(many=True, read_only=True)
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
                  'is_notice', 'is_blind', 'deleted', 'links', 'files', 'comments', 'creator',
                  'created', 'updated', 'is_new', 'prev_pk', 'next_pk')
        read_only_fields = ('ip', 'comments')

    def _get_filtered_queryset(self):
        """prev_pk / next_pk 계산용 필터된 쿼리셋 (View 레이어와 필터 조건 동기화 필요)"""
        queryset = Post.objects.all()
        query = self.context['request'].query_params
        forum = query.get('forum')
        is_notice_param = query.get('is_notice')
        category = query.get('category')
        search = query.get('search')

        if forum:
            queryset = queryset.filter(forum_id=forum)
        if is_notice_param == 'true':
            queryset = queryset.filter(is_notice=True)
        elif is_notice_param == 'false':
            queryset = queryset.filter(is_notice=False)
        if category:
            queryset = queryset.filter(category_id=category)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(links__link__icontains=search) |
                Q(files__file__icontains=search) |
                Q(creator__username__icontains=search)
            )
        return queryset

    @staticmethod
    def get_scrape(obj):
        return obj.postscrape_set.count()

    def get_my_scrape(self, obj):
        user = self.context['request'].user
        return obj.postscrape_set.filter(user=user).exists()

    def get_my_like(self, obj):
        user = self.context['request'].user
        return user.profile.like_posts.filter(pk=obj.pk).exists()

    def get_my_blame(self, obj):
        user = self.context['request'].user
        return user.profile.blame_posts.filter(pk=obj.pk).exists()

    def get_prev_pk(self, obj):
        prev_obj = self._get_filtered_queryset().filter(created__lt=obj.created).first()
        return prev_obj.pk if prev_obj else None

    def get_next_pk(self, obj):
        next_obj = self._get_filtered_queryset().filter(created__gt=obj.created).order_by('created').first()
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

    @transaction.atomic
    def create(self, validated_data):
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        validated_data['device'] = self.context.get('request').META.get('HTTP_USER_AGENT')
        post = Post.objects.create(**validated_data)

        # Links 처리
        for link in self.initial_data.getlist('newLinks'):
            PostLink.objects.create(post=post, link=self._normalize_url(link))

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
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        validated_data['device'] = self.context.get('request').META.get('HTTP_USER_AGENT')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Links 처리
        for json_link in self.initial_data.getlist('links'):
            link = json.loads(json_link)
            link_object = PostLink.objects.get(pk=link.get('pk'))
            if link.get('del'):
                link_object.delete()
            else:
                link_object.link = self._normalize_url(link.get('link'))
                link_object.save()

        for link in self.initial_data.getlist('newLinks'):
            PostLink.objects.create(post=instance, link=self._normalize_url(link))

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


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLink
        fields = ('pk', 'post', 'link', 'hit')


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFile
        fields = ('pk', 'post', 'file', 'hit')


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ('pk', 'post', 'image')


class SimplePostInCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('pk', 'forum')


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

    def get_replies(self, instance):
        serializer = self.__class__(instance.replies, many=True)
        serializer.bind('', self)
        return serializer.data

    def get_my_like(self, obj):
        user = self.context['request'].user
        return user.profile.like_comments.filter(pk=obj.pk).exists()

    def get_my_blame(self, obj):
        user = self.context['request'].user
        return user.profile.blame_comments.filter(pk=obj.pk).exists()

    @transaction.atomic
    def create(self, validated_data):
        validated_data['post_id'] = self.initial_data.get('post')
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
