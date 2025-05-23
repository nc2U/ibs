from django.contrib import admin
from import_export.admin import ImportExportMixin

from work.models.inform import CodeDocsCategory, News, NewsFile


@admin.register(CodeDocsCategory)
class CodeDocsCategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'active', 'default', 'order', 'user')
    list_display_links = ('name',)
    list_editable = ('active', 'default', 'order')


class NewsFileInline(admin.TabularInline):
    model = NewsFile
    extra = 1


@admin.register(News)
class NewsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'title', 'project', 'summary', 'author')
    list_display_links = ('title',)
    inlines = (NewsFileInline,)
