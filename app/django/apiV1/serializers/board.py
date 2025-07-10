import json
import os.path
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from accounts.models import Profile
from apiV1.serializers.accounts import SimpleUserSerializer
from board.models import Board, PostCategory, Post, PostLink, PostFile, PostImage, Comment, Tag


# Board --------------------------------------------------------------------------
class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ('pk', 'project', 'name', 'description', 'parent', 'search_able', 'manager')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = ('pk', 'board', 'color', 'name', 'parent', 'order')


class LinksInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLink
        fields = ('pk', 'post', 'link', 'hit')


class FilesInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFile
        fields = ('pk', 'post', 'file', 'hit')


class PostSerializer(serializers.ModelSerializer):
    board_name = serializers.SlugField(source='board', read_only=True)
    cate_name = serializers.SlugField(source='category', read_only=True)
    links = LinksInPostSerializer(many=True, read_only=True)
    files = FilesInPostSerializer(many=True, read_only=True)
    user = SimpleUserSerializer(read_only=True)
    my_like = serializers.SerializerMethodField(read_only=True)
    scrape = serializers.SerializerMethodField(read_only=True)
    my_scrape = serializers.SerializerMethodField(read_only=True)
    my_blame = serializers.SerializerMethodField(read_only=True)
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'board', 'board_name', 'category', 'cate_name', 'title',
                  'content', 'hit', 'like', 'my_like', 'scrape', 'my_scrape', 'blame',
                  'my_blame', 'ip', 'device', 'is_secret', 'password', 'is_hide_comment',
                  'is_notice', 'is_blind', 'deleted', 'links', 'files', 'comments', 'user',
                  'created', 'updated', 'is_new', 'prev_pk', 'next_pk')
        read_only_fields = ('ip', 'comments')

    def get_collection(self):
        queryset = Post.objects.all()
        query = self.context['request'].query_params
        board = query.get('board')
        is_notice = True if query.get('is_notice') == 'true' else False
        category = query.get('category')
        search = query.get('search')

        queryset = queryset.filter(board_id=board) if board else queryset
        queryset = queryset.filter(is_notice=True) if is_notice == 'true' else queryset
        queryset = queryset.filter(is_notice=False) if is_notice == 'false' else queryset
        queryset = queryset.filter(category_id=category) if category else queryset
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(links__link__icontains=search) |
            Q(files__file__icontains=search) |
            Q(user__username__icontains=search)
        ) if search else queryset

        return queryset

    @staticmethod
    def get_scrape(obj):
        return len(obj.postscrape_set.all())

    def get_my_scrape(self, obj):
        user = self.context['request'].user
        scrapes = obj.postscrape_set.all()
        users = [s.user for s in scrapes]
        return user in users

    def get_my_like(self, obj):
        user = self.context['request'].user
        likes = user.profile.like_posts.all()
        likes = [p.pk for p in likes]
        return obj.pk in likes

    def get_my_blame(self, obj):
        user = self.context['request'].user
        blames = user.profile.blame_posts.all()
        blames = [p.pk for p in blames]
        return obj.pk in blames

    def get_prev_pk(self, obj):
        prev_obj = self.get_collection().filter(created__lt=obj.created).first()
        return prev_obj.pk if prev_obj else None

    def get_next_pk(self, obj):
        next_obj = self.get_collection().filter(created__gt=obj.created).order_by('created').first()
        return next_obj.pk if next_obj else None

    def to_python(self, value):

        def split_url(url):
            """
            Return a list of url parts via urlparse.urlsplit(), or raise
            ValidationError for some malformed URLs.
            """
            try:
                return list(urlsplit(url))
            except ValueError:
                # urlparse.urlsplit can raise a ValueError with some
                # misformatted URLs.
                raise ValidationError(self.error_messages['invalid'], code='invalid')

        if value:
            url_fields = split_url(value)
            if not url_fields[0]:
                # If no URL scheme given, assume http://
                url_fields[0] = 'http'
            if not url_fields[1]:
                # Assume that if no domain is provided, that the path segment
                # contains the domain.
                url_fields[1] = url_fields[2]
                url_fields[2] = ''
                # Rebuild the url_fields list, since the domain segment may now
                # contain the path too.
                url_fields = split_url(urlunsplit(url_fields))
            value = urlunsplit(url_fields)
        return value

    @transaction.atomic
    def create(self, validated_data):
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        validated_data['device'] = self.context.get('request').META.get('HTTP_USER_AGENT')
        post = Post.objects.create(**validated_data)

        # Links 처리
        if self.initial_data.get('newLinks'):
            new_links = self.initial_data.getlist('newLinks')
            if new_links:
                for link in new_links:
                    PostLink.objects.create(post=post, link=self.to_python(link))

        # Files 처리
        if self.initial_data.get('newFiles'):
            new_files = self.initial_data.getlist('newFiles')
            if new_files:
                for file in new_files:
                    PostFile.objects.create(post=post, file=file)

        return post

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        validated_data['device'] = self.context.get('request').META.get('HTTP_USER_AGENT')
        instance.__dict__.update(**validated_data)
        instance.board = validated_data.get('board', instance.board)
        instance.category = validated_data.get('category', instance.category)
        instance.save()

        try:
            # Links 처리
            old_links = self.initial_data.getlist('links')
            if old_links:
                for json_link in old_links:
                    link = json.loads(json_link)
                    link_object = PostLink.objects.get(pk=link.get('pk'))
                    if link.get('del'):
                        link_object.delete()
                    else:
                        link_object.link = self.to_python(link.get('link'))
                        link_object.save()

            new_links = self.initial_data.getlist('newLinks')
            if new_links:
                for link in new_links:
                    PostLink.objects.create(post=instance, link=self.to_python(link))

            # Files 처리
            old_files = self.initial_data.getlist('files')
            if old_files:
                cng_pks = self.initial_data.getlist('cngPks')
                cng_files = self.initial_data.getlist('cngFiles')
                cng_maps = [(pk, cng_files[i]) for i, pk in enumerate(cng_pks)]

                for json_file in old_files:
                    file = json.loads(json_file)
                    file_object = PostFile.objects.get(pk=file.get('pk'))

                    if file.get('del'):
                        file_object.delete()

                    for cng_map in cng_maps:
                        if int(file.get('pk')) == int(cng_map[0]):
                            old_file = file_object.file
                            if os.path.isfile(old_file.path):
                                os.remove(old_file.path)
                            file_object.file = cng_map[1]
                            file_object.save()

            new_files = self.initial_data.getlist('newFiles')
            if new_files:
                for file in new_files:
                    PostFile.objects.create(post=instance, file=file)
        except AttributeError:
            pass

        return instance


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('pk', 'like')

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile = Profile.objects.get(user=user)

        if profile.like_posts.filter(pk=instance.pk).exists():
            if instance.like > 0:
                instance.like -= 1
                profile.like_posts.remove(instance)
        else:
            instance.like += 1
            profile.like_posts.add(instance)
        instance.save()
        return instance


class PostBlameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('pk', 'blame')

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile = Profile.objects.get(user=user)

        if profile.blame_posts.filter(pk=instance.pk).exists():
            if instance.blame > 0:
                instance.blame -= 1
                profile.blame_posts.remove(instance)
        else:
            instance.blame += 1
            profile.blame_posts.add(instance)
        instance.save()
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
        fields = ('pk', 'board')


class CommentSerializer(serializers.ModelSerializer):
    post = SimplePostInCommentSerializer(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    my_like = serializers.SerializerMethodField(read_only=True)
    my_blame = serializers.SerializerMethodField(read_only=True)
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('pk', 'post', 'content', 'parent', 'replies', 'like', 'my_like',
                  'blame', 'my_blame', 'ip', 'device', 'secret', 'user', 'created')
        read_only_fields = ('ip',)

    def get_replies(self, instance):
        serializer = self.__class__(instance.replies, many=True)
        serializer.bind('', self)
        return serializer.data

    def get_my_like(self, obj):
        user = self.context['request'].user
        likes = user.profile.like_comments.all()
        likes = [c.pk for c in likes]
        return obj.pk in likes

    def get_my_blame(self, obj):
        user = self.context['request'].user
        blames = user.profile.blame_comments.all()
        blames = [c.pk for c in blames]
        return obj.pk in blames

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
        instance.__dict__.update(**validated_data)
        instance.post = validated_data.get('post', instance.post)
        instance.save()
        return instance


class CommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('pk', 'like')

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile = Profile.objects.get(user=user)

        if profile.like_comments.filter(pk=instance.pk).exists():
            if instance.like > 0:
                instance.like -= 1
                profile.like_comments.remove(instance)
        else:
            instance.like += 1
            profile.like_comments.add(instance)
        instance.save()
        return instance


class CommentBlameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('pk', 'blame')

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context['request'].user
        profile = Profile.objects.get(user=user)

        if profile.blame_comments.filter(pk=instance.pk).exists():
            if instance.blame > 0:
                instance.blame -= 1
                profile.blame_comments.remove(instance)
        else:
            instance.blame += 1
            profile.blame_comments.add(instance)
        instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('pk', 'board', 'name', 'post')


class PostInTrashSerializer(serializers.ModelSerializer):
    board_name = serializers.SlugField(source='board', read_only=True)
    cate_name = serializers.SlugField(source='category', read_only=True)
    user = serializers.SlugField(read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'board_name', 'cate_name', 'title', 'content', 'user', 'created', 'deleted')

    def update(self, instance, validated_data):
        instance.restore()
        return instance
