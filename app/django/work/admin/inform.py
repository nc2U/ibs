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
    pass
