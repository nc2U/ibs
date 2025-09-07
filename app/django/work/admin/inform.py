from django.contrib import admin
from import_export.admin import ImportExportMixin

from work.models import CodeDocsCategory, News, NewsFile, NewsComment


@admin.register(CodeDocsCategory)
class CodeDocsCategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'active', 'default', 'order', 'creator')
    list_display_links = ('name',)
    list_editable = ('active', 'default', 'order')
    list_filter = ('active', 'default')


class NewsFileInline(admin.TabularInline):
    model = NewsFile
    extra = 1


class NewsCommentInline(admin.TabularInline):
    model = NewsComment
    extra = 1


@admin.register(News)
class NewsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'project', 'title', 'summary', 'author')
    list_display_links = ('title',)
    inlines = (NewsFileInline, NewsCommentInline)
