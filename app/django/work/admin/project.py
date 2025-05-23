from django.contrib import admin
from import_export.admin import ImportExportMixin

from work.models.github import Repository
from work.models.issue import IssueCategory
from work.models.project import IssueProject, Module, Role, Permission, Member, Version


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0


class VersionInline(admin.TabularInline):
    model = Version
    extra = 0


class IssueCategoryInline(admin.TabularInline):
    model = IssueCategory
    extra = 0


class RepositoryInline(admin.TabularInline):
    model = Repository
    extra = 0


@admin.register(IssueProject)
class IssueProjectAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'company', 'sort', 'name', 'homepage', 'is_public', 'parent', 'slug', 'status', 'order')
    list_display_links = ('name',)
    list_editable = ('company', 'sort', 'order')
    inlines = (ModuleInline, MemberInline, VersionInline, IssueCategoryInline, RepositoryInline)


class PermissionInline(admin.StackedInline):
    model = Permission
    extra = 1
    max_num = 1
    can_delete = False


@admin.register(Role)
class RoleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'issue_visible', 'time_entry_visible',
                    'user_visible', 'default_time_activity')
    list_display_links = ('name',)
    inlines = (PermissionInline,)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Permission이 없으면 자동 생성
        if not hasattr(obj, 'permission'):
            Permission.objects.create(role=obj)

    def save_formset(self, request, form, formset, change):
        if formset.model == Permission:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.role = form.instance
                instance.save()
        else:
            formset.save()


@admin.register(Member)
class MemberAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'user', 'project', 'get_roles', 'created')
    list_display_links = ('user',)
    list_editable = ('project',)

    def get_roles(self, obj):
        return ", ".join([role.name for role in obj.roles.all()]) if obj.roles.all() else '-'

    get_roles.short_description = '역할'


@admin.register(Version)
class VersionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'project', 'status', 'get_sharing_display', 'effective_date', 'wiki_page_title')
    list_display_links = ('name',)
