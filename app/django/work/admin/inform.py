from django.contrib import admin
from import_export.admin import ImportExportMixin

from work.models import News, NewsFile, NewsComment, CustomQuery


class NewsFileInline(admin.TabularInline):
    model = NewsFile
    extra = 1


class NewsCommentInline(admin.TabularInline):
    model = NewsComment
    extra = 1


@admin.register(News)
class NewsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'project', 'title', 'is_important', 'author', 'created')
    list_display_links = ('title',)
    list_editable = ('is_important',)
    inlines = (NewsFileInline, NewsCommentInline)


@admin.register(CustomQuery)
class CustomQueryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'target_type', 'user', 'is_public', 'created', 'updated')
    list_display_links = ('name',)
    list_filter = ('target_type', 'is_public', 'user')
    search_fields = ('name', 'description')
    readonly_fields = ('created', 'updated')
