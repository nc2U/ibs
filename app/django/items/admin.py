from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from import_export.admin import ImportExportMixin

from apiV1.permissions._utils import get_project_ids_with_permission
from .models import UnitType, UnitFloorType, KeyUnit, BuildingUnit, HouseUnit, OptionItem


def _filter_items_admin_queryset(qs, request, project_lookup: str = 'project_id'):
    user = getattr(request, 'user', None)
    if not user or user.is_superuser or getattr(user, 'work_manager', False):
        return qs
    accessible_ids = get_project_ids_with_permission(user, 'contract.read')
    return qs.filter(**{f'{project_lookup}__in': accessible_ids})


class UnitTypeAdmin(ImportExportMixin, admin.ModelAdmin):
    # form = UnitTypeForm
    list_display = (
        'id', 'project', 'main_or_sub', 'name', 'sort', 'styled_color',
        'actual_area', 'supply_area', 'contract_area', 'average_price', 'num_unit')
    list_display_links = ('project', 'name',)
    list_editable = ('main_or_sub', 'sort', 'actual_area', 'supply_area',
                     'contract_area', 'average_price', 'num_unit')
    list_filter = ('project',)
    search_fields = ('name',)
    list_select_related = ('project',)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('project')
        return _filter_items_admin_queryset(qs, request)

    def styled_color(self, obj):
        return format_html('<div style="width:15px; background:{};">&nbsp;</div>', obj.color)

    styled_color.short_description = '타입색상'


class UnitFloorTypeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'sort', 'start_floor', 'end_floor', 'extra_cond', 'alias_name')
    list_display_links = ('project',)
    list_editable = ('sort', 'start_floor', 'end_floor', 'extra_cond', 'alias_name')
    list_filter = ('project',)
    search_fields = ('alias_name',)
    list_select_related = ('project',)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('project')
        return _filter_items_admin_queryset(qs, request)


class HasContractFilter(SimpleListFilter):
    title = 'contract 연결 여부'
    parameter_name = 'contract_isnull'

    def lookups(self, request, model_admin):
        return (
            ('ok', 'contract 있음'),
            ('no', 'contract 없음'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'ok':
            return queryset.filter(contract__isnull=False)
        elif value == 'no':
            return queryset.filter(contract__isnull=True)
        return queryset


class KeyUnitAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'unit_code', 'unit_type', 'contract')
    search_fields = ('unit_code',)
    list_display_links = ('project', 'unit_code',)
    list_filter = ('project', 'unit_type', HasContractFilter)
    list_select_related = ('project', 'unit_type', 'contract')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('project', 'unit_type', 'contract')
        return _filter_items_admin_queryset(qs, request)


class BuildingUnitAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'name')
    list_display_links = ('project',)
    list_editable = ('name',)
    list_filter = ('project',)
    search_fields = ('name',)
    list_select_related = ('project',)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('project')
        return _filter_items_admin_queryset(qs, request)


class HouseUnitAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'key_unit', 'unit_type', 'building_unit', 'name',
                    'floor_type', 'bldg_line', 'floor_no', 'is_hold', 'hold_reason')
    search_fields = ('name', 'building_unit__name', 'key_unit__unit_code', 'hold_reason')
    list_display_links = ('building_unit', 'name')
    list_filter = ('building_unit__project', 'unit_type', 'building_unit',
                   'bldg_line', 'floor_type', 'is_hold')
    list_select_related = ('building_unit__project', 'unit_type', 'building_unit', 'floor_type', 'key_unit')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            'building_unit__project', 'unit_type', 'building_unit', 'floor_type', 'key_unit'
        )
        return _filter_items_admin_queryset(qs, request, project_lookup='building_unit__project_id')


class OptionItemAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'project', 'opt_code', 'opt_name', 'opt_desc',
                    'opt_maker', 'opt_price', 'opt_deposit', 'opt_balance')
    search_fields = ('opt_code', 'opt_name', 'opt_desc', 'opt_maker')
    list_display_links = ('opt_code', 'opt_name')
    list_editable = ('opt_desc', 'opt_maker', 'opt_price', 'opt_deposit', 'opt_balance')
    list_filter = ('project', 'types')
    filter_horizontal = ('types',)
    list_select_related = ('project',)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('project').prefetch_related('types')
        return _filter_items_admin_queryset(qs, request)


admin.site.register(UnitType, UnitTypeAdmin)
admin.site.register(UnitFloorType, UnitFloorTypeAdmin)
admin.site.register(KeyUnit, KeyUnitAdmin)
admin.site.register(BuildingUnit, BuildingUnitAdmin)
admin.site.register(HouseUnit, HouseUnitAdmin)
admin.site.register(OptionItem, OptionItemAdmin)
