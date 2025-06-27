from django.contrib import admin
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from work.models import Repository, Commit, Branch


@admin.register(Repository)
class RepositoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'is_default', 'slug', 'local_path', 'remote_url', 'is_report')
    list_display_links = ('project', 'slug')
    list_editable = ('is_default', 'local_path', 'remote_url', 'is_report')
    list_filter = ('project', 'is_default', 'is_report')


@admin.register(Branch)
class BranchAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'repo', 'name')
    list_display_links = ('repo', 'name')
    list_filter = ('repo',)


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ('id', 'repo', 'commit_hash', 'author', 'date')
    list_display_links = ('commit_hash',)
    list_filter = ('repo', 'branches', ('date', DateRangeFilter))
    search_fields = ('commit_hash',)
