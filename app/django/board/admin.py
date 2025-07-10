from django.contrib import admin
from import_export.admin import ImportExportMixin
from .models import Board, PostCategory, Post, PostLink, PostFile, PostImage, Comment, Tag


class CategoryInline(admin.TabularInline):
    model = PostCategory
    extra = 1


@admin.register(Board)
class BoardAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'description', 'search_able')
    list_display_links = ('project', 'name',)
    list_editable = ('description', 'search_able')
    search_fields = ('name',)
    list_filter = ('project',)
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
    list_display = ('id', 'board', 'category', 'title', 'is_notice')
    list_display_links = ('title',)
    list_editable = ('board', 'category', 'is_notice')
    search_fields = ('title', 'content')
    list_filter = ('board', 'is_notice', 'category')
    inlines = (LinkInline, FileInline, ImageInline, CommentInline)


@admin.register(Tag)
class TagAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'board', 'name')
    list_editable = ('name',)
    search_fields = ('name',)
    list_filter = ('board',)
