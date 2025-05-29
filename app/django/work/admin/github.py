from django.contrib import admin
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from work.models import Repository, Commit


@admin.register(Repository)
class RepositoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'is_default', 'slug', 'local_path', 'is_report')
    list_display_links = ('project', 'slug')
    list_editable = ('is_default', 'local_path', 'is_report')
    list_filter = ('project', 'is_default', 'is_report')


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ('id', 'repo', 'commit_hash', 'author', 'date')
    list_display_links = ('commit_hash',)
    list_filter = ('repo', ('date', DateRangeFilter))
