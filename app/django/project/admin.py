from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from import_export.admin import ImportExportMixin

from .models import (Project, ProjectIncBudget, ProjectOutBudget, Site, SiteInfoFile,
                     SiteOwner, SiteOwnshipRelationship, SiteContract, SiteContractFile)


class ProjectAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'issue_project', 'name', 'order', 'kind', 'num_unit', 'build_size', 'area_usage')
    list_display_links = ('name',)
    list_editable = ('issue_project', 'order', 'kind', 'num_unit', 'build_size', 'area_usage')


class ProjectIncBudgetAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'account_d2', 'account_d3', 'order_group',
                    'unit_type', 'item_name', 'average_price', 'quantity', 'budget', 'revised_budget')
    list_display_links = ('project',)
    list_editable = ('account_d2', 'account_d3', 'order_group', 'unit_type',
                     'item_name', 'average_price', 'quantity', 'budget', 'revised_budget')
    list_filter = ('project', 'order_group', 'unit_type')


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


class SiteAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        'order', 'project', '__str__', 'site_purpose', 'official_area',
        'returned_area', 'notice_price', 'dup_issue_date')
    list_display_links = ('project', '__str__',)
    list_editable = ('order', 'official_area', 'returned_area', 'notice_price', 'dup_issue_date')
    search_fields = ('district', 'lot_number',)
    list_filter = ('project', 'site_purpose')
    inlines = (InfoFileAdmin,)


class SiteOwnerAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        'id', 'owner', 'date_of_birth', 'phone1', 'phone2', 'zipcode', 'address1', 'address2', 'address3', 'own_sort')
    list_display_links = ('owner',)
    search_fields = ('owner', 'own_sort')
    list_filter = ('project', 'own_sort',)


class SiteOwnshipRelationshipAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'site', 'site_owner', 'ownership_ratio', 'owned_area', 'acquisition_date')
    list_display_links = ('site', 'site_owner')
    list_editable = ('ownership_ratio', 'owned_area', 'acquisition_date')
    list_filter = ('site__project',)


class ContFileAdmin(admin.TabularInline):
    model = SiteContractFile
    extra = 0


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


admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectIncBudget, ProjectIncBudgetAdmin)
admin.site.register(ProjectOutBudget, ProjectOutBudgetAdmin)
admin.site.register(Site, SiteAdmin)
admin.site.register(SiteOwner, SiteOwnerAdmin)
admin.site.register(SiteOwnshipRelationship, SiteOwnshipRelationshipAdmin)
admin.site.register(SiteContract, SiteContractAdmin)
