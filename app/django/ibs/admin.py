from django.contrib import admin
from import_export.admin import ImportExportMixin

from .models import (AccountSort, AccountSubD1, AccountSubD2, AccountSubD3,
                     ProjectAccountD2, ProjectAccountD3, UserWidgetConfig,
                     CalendarSchedule, WiseSaying)


@admin.register(AccountSort)
class AccountSortAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('name',)


class AccountSubD2Inline(admin.TabularInline):
    model = AccountSubD2
    extra = 2


@admin.register(AccountSubD1)
class AccountSubD1Admin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'description')
    list_display_links = ('name',)
    search_fields = ('name', 'description')
    inlines = (AccountSubD2Inline,)


class AccountSubD3Inline(admin.TabularInline):
    model = AccountSubD3
    extra = 2


@admin.register(AccountSubD2)
class AccountSubD2Admin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'd1', 'name', 'code', 'description')
    list_display_links = ('name',)
    list_select_related = ('d1',)
    search_fields = ('name', 'description')
    list_filter = ('d1',)
    inlines = (AccountSubD3Inline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('d1')


@admin.register(AccountSubD3)
class AccountSubD3Admin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'sort', 'd2', 'name', 'code', 'description', 'is_hide', 'is_special')
    list_display_links = ('sort', 'd2', 'name')
    list_select_related = ('sort', 'd2')
    list_editable = ('is_hide', 'is_special')
    search_fields = ('name', 'description')
    list_filter = ('d2__d1', 'd2')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sort', 'd2')


class ProjectAccountD3Inline(admin.TabularInline):
    model = ProjectAccountD3


@admin.register(ProjectAccountD2)
class ProjectAccountD2Admin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'd1', 'code', 'name', 'description')
    list_display_links = ('code', 'name')
    list_select_related = ('d1',)
    list_filter = ('d1', 'd1__sorts')
    search_fields = ('name', 'description')
    inlines = (ProjectAccountD3Inline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('d1')


@admin.register(ProjectAccountD3)
class ProjectAccountD3Admin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'sort', 'd2', 'code', 'is_payment', 'is_related_contract', 'name', 'description')
    list_display_links = ('code', 'name')
    list_select_related = ('sort', 'd2')
    list_editable = ('is_payment', 'is_related_contract', 'description')
    list_filter = ('d2__d1', 'sort', 'd2')
    search_fields = ('name', 'description')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sort', 'd2')


@admin.register(UserWidgetConfig)
class UserWidgetConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'version', 'created', 'updated')
    list_display_links = ('user',)
    list_select_related = ('user',)
    search_fields = ('user__username', 'user__email', 'user__profile__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user')
        if request.user and (request.user.is_superuser or getattr(request.user, 'work_manager', False)):
            return qs
        return qs.filter(user=request.user)


@admin.register(CalendarSchedule)
class CalendarScheduleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'all_day', 'start_date', 'end_date', 'creator', 'created')
    list_display_links = ('title',)
    list_select_related = ('creator',)
    list_filter = ('all_day', 'start_date', 'created')
    search_fields = ('title', 'creator__username', 'creator__email', 'creator__profile__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('creator')
        if request.user and (request.user.is_superuser or getattr(request.user, 'work_manager', False)):
            return qs
        return qs.filter(creator=request.user)


@admin.register(WiseSaying)
class WiseSayingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'saying_ko', 'spoked_by')
    list_display_links = ('saying_ko',)
