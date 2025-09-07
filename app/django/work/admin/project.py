from django.contrib import admin
from import_export.admin import ImportExportMixin

from work.models import IssueProject, Module, Role, Permission, Member, Version
from work.models.git_repo import Repository
from work.models.issue import IssueCategory


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
    list_display = ('pk', 'company', 'sort', 'name', 'homepage', 'is_public', 'parent', 'slug', 'status', 'slack_notifications_enabled', 'order')
    list_display_links = ('name',)
    list_editable = ('company', 'sort', 'slack_notifications_enabled', 'order')
    inlines = (ModuleInline, MemberInline, VersionInline, IssueCategoryInline, RepositoryInline)
    list_filter = ('company', 'sort', 'is_public', 'status', 'slack_notifications_enabled')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('company', 'sort', 'name', 'slug', 'description', 'homepage', 'is_public', 'parent', 'is_inherit_members')
        }),
        ('프로젝트 설정', {
            'fields': ('default_version', 'allowed_roles', 'trackers', 'activities', 'status', 'order')
        }),
        ('Slack 알림 설정', {
            'fields': ('slack_webhook_url', 'slack_notifications_enabled'),
            'classes': ('collapse',),
            'description': '이 프로젝트의 데이터 변동을 실시간으로 Slack에 알림받을 수 있습니다.'
        }),
        ('생성 정보', {
            'fields': ('creator', 'created', 'updated'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created', 'updated')
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # 기존 객체 수정 시
            readonly.append('slug')  # slug는 수정 불가
        return readonly


@admin.register(Role)
class RoleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'issue_visible', 'time_entry_visible',
                    'user_visible', 'default_time_activity')
    list_display_links = ('name',)
    filter_horizontal = ('permissions',)  # ✅ 이렇게 하면 UI에서 다중 선택 가능

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # 새 Role 생성 시
            default_perms = Permission.objects.filter(is_default=True)
            form.base_fields['permissions'].initial = default_perms
        return form

    # def save_model(self, request, obj, form, change):
    #     super().save_model(request, obj, form, change)
    #     if not change:
    #         default_perms = Permission.objects.filter(is_default=True)
    #         obj.permissions.add(*default_perms)


@admin.register(Permission)
class PermissionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'sort', 'code', 'name', 'is_default')
    list_display_links = ('pk', 'sort')
    list_editable = ('code', 'name', 'is_default')
    list_filter = ('sort', 'is_default',)
    search_fields = ('code', 'name')


@admin.register(Member)
class MemberAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'user', 'project', 'get_roles', 'created')
    list_display_links = ('user',)
    list_editable = ('project',)
    list_filter = ('project', 'roles')

    def get_roles(self, obj):
        return ", ".join([role.name for role in obj.roles.all()]) if obj.roles.all() else '-'

    get_roles.short_description = '역할'


@admin.register(Version)
class VersionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'name', 'project', 'status', 'get_sharing_display', 'effective_date', 'wiki_page_title')
    list_display_links = ('name',)
    list_filter = ('project', 'status', 'sharing')
