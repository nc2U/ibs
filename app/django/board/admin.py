from django.contrib import admin
from import_export.admin import ImportExportMixin
from .models import Group, Board, PostCategory, Post, PostLink, PostFile, PostImage, Comment, Tag


@admin.register(Group)
class GroupAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('name',)
    search_fields = ('name',)


class CategoryInline(admin.TabularInline):
    model = PostCategory
    extra = 1


@admin.register(Board)
class BoardAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'group', 'board_type', 'name', 'order', 'search_able')
    list_display_links = ('name',)
    list_editable = ('group', 'board_type', 'order', 'search_able')
    search_fields = ('name',)
    list_filter = ('group', 'board_type')
    inlines = (CategoryInline,)


@admin.register(PostCategory)
class CategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'board', 'color', 'name', 'parent', 'order')
    list_display_links = ('name',)
    list_editable = ('board', 'color', 'parent', 'order')
    search_fields = ('name',)
    list_filter = ('board',)


class LinkInline(admin.TabularInline):
    model = PostLink
    extra = 1


class FileInline(admin.TabularInline):
    model = PostFile
    extra = 1


class ImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1


@admin.register(Post)
class PostAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'board', 'issue_project', 'category', 'title', 'is_notice')
    list_display_links = ('title',)
    list_editable = ('board', 'issue_project', 'category', 'is_notice')
    search_fields = ('title', 'content')
    list_filter = ('board', 'is_notice', 'category')
    inlines = (LinkInline, FileInline, ImageInline, CommentInline)


@admin.register(Tag)
class TagAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'board', 'name')
    list_editable = ('name',)
    search_fields = ('name',)
    list_filter = ('board',)
