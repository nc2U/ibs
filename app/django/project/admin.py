from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.html import format_html
from import_export.admin import ImportExportMixin

from .models import (Project, ProjectIncBudget, ProjectOutBudget, Site, SiteInfoFile,
                     SiteOwner, SiteOwnshipRelationship, SiteOwnerConsultationLogs,
                     SiteContract, SiteContractFile)


@admin.register(Project)
class ProjectAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'issue_project', 'name', 'order', 'kind', 'num_unit',
                    'build_size', 'area_usage', 'monthly_aggr_start_date',
                    'construction_start_date', 'construction_period_months')
    list_display_links = ('name',)
    list_editable = ('issue_project', 'order', 'kind', 'num_unit', 'build_size', 'area_usage')

    fieldsets = (
        ('기본 정보', {
            'fields': ('issue_project', 'name', 'order', 'kind', 'start_year',
                       'is_direct_manage', 'is_returned_area', 'is_unit_set')
        }),
        ('사업 일정 (필수)', {
            'fields': ('monthly_aggr_start_date', 'construction_start_date',
                       'construction_period_months'),
            'description': '캐시 플로우 생성에 필요한 필수 입력 항목. 예정일 입력 후 실제 일자로 업데이트하세요.'
        }),
        ('주소 정보', {
            'fields': ('local_zipcode', 'local_address1', 'local_address2', 'local_address3'),
            'classes': ('collapse',)
        }),
        ('사업 규모', {
            'fields': ('area_usage', 'build_size', 'num_unit',
                       'buy_land_extent', 'scheme_land_extent', 'donation_land_extent',
                       'on_floor_area', 'under_floor_area', 'total_floor_area', 'build_area',
                       'floor_area_ratio', 'build_to_land_ratio',
                       'num_legal_parking', 'num_planed_parking'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectIncBudget)
class ProjectIncBudgetAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'account_d2', 'account_d3', 'order_group',
                    'unit_type', 'item_name', 'average_price', 'quantity', 'budget', 'revised_budget')
    list_display_links = ('project',)
    list_editable = ('account_d2', 'account_d3', 'order_group', 'unit_type',
                     'item_name', 'average_price', 'quantity', 'budget', 'revised_budget')
    list_filter = ('project', 'order_group', 'unit_type')


@admin.register(ProjectOutBudget)
class ProjectOutBudgetAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'order', 'account_d2', 'account_d3',
                    'account_opt', 'budget', 'revised_budget', 'basis_calc')
    list_display_links = ('project',)
    list_editable = ('order', 'account_d2', 'account_d3', 'account_opt',
                     'budget', 'revised_budget', 'basis_calc')
    list_filter = ('project', 'account_d2', 'account_d3')


class InfoFileAdmin(admin.TabularInline):
    model = SiteInfoFile
    extra = 0


@admin.register(Site)
class SiteAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        'order', 'project', '__str__', 'site_purpose', 'official_area',
        'returned_area', 'notice_price', 'dup_issue_date')
    list_display_links = ('project', '__str__',)
    list_editable = ('order', 'official_area', 'returned_area', 'notice_price', 'dup_issue_date')
    search_fields = ('district', 'lot_number',)
    list_filter = ('project', 'site_purpose')
    inlines = (InfoFileAdmin,)


@admin.register(SiteOwner)
class SiteOwnerAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        'id', 'owner', 'date_of_birth', 'phone1', 'phone2', 'zipcode', 'address1', 'address2', 'address3', 'own_sort')
    list_display_links = ('owner',)
    search_fields = ('owner', 'own_sort')
    list_filter = ('project', 'own_sort',)


@admin.register(SiteOwnshipRelationship)
class SiteOwnshipRelationshipAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'site', 'site_owner', 'ownership_ratio', 'owned_area', 'acquisition_date')
    list_display_links = ('site', 'site_owner')
    list_editable = ('ownership_ratio', 'owned_area', 'acquisition_date')
    list_filter = ('site__project',)


@admin.register(SiteOwnerConsultationLogs)
class SiteOwnerConsultationLogsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'site_owner', 'consultation_date', 'channel',
                    'title', 'consultant', 'follow_up_required', 'created')
    list_display_links = ('site_owner',)
    list_filter = ('channel', 'follow_up_required', 'consultation_date', 'site_owner__project')
    search_fields = ('site_owner__owner', 'title', 'content', 'consultant__username')
    date_hierarchy = 'consultation_date'
    readonly_fields = ('created', 'updated', 'creator', 'updator')

    fieldsets = (
        ('기본 정보', {
            'fields': ('site_owner', 'consultation_date', 'channel')
        }),
        ('상담 내용', {
            'fields': ('title', 'content', 'consultant')
        }),
        ('후속 조치', {
            'fields': ('follow_up_required', 'follow_up_note', 'completion_date')
        }),
        ('시스템 정보', {
            'fields': ('created', 'updated', 'creator', 'updator'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        obj.updator = request.user
        super().save_model(request, obj, form, change)


class ContFileAdmin(admin.TabularInline):
    model = SiteContractFile
    extra = 0


@admin.register(SiteContract)
class SiteContractAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'owner', 'formatted_price', 'contract_date', 'acc_bank',
                    'acc_number', 'acc_owner', 'remain_pay_is_paid',
                    'ownership_completion')
    list_display_links = ('owner',)
    list_filter = ('owner__project',)
    inlines = (ContFileAdmin,)

    def formatted_price(self, obj):
        price = intcomma(obj.total_price)
        return f'{price} 원'

    formatted_price.short_description = '총매매대금'
