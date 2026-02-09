from datetime import datetime
from django.db.models import Q
from rest_framework import viewsets
from django_filters.rest_framework import FilterSet
from django_filters import BooleanFilter

from ..permission import *
from ..pagination import *
from ..serializers.items import *

from items.models import UnitType, UnitFloorType, KeyUnit, BuildingUnit, HouseUnit

TODAY = datetime.today().strftime('%Y-%m-%d')


# Items --------------------------------------------------------------------------
class UnitTypeViewSet(viewsets.ModelViewSet):
    queryset = UnitType.objects.all()
    serializer_class = UnitTypeSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'sort', 'main_or_sub')
    search_fields = ('name',)


class UnitFloorTypeViewSet(viewsets.ModelViewSet):
    queryset = UnitFloorType.objects.all()
    serializer_class = UnitFloorTypeSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'sort')
    search_fields = ('alias_name',)


class KeyUnitListFilterSet(FilterSet):
    available = BooleanFilter(field_name='contract', lookup_expr='isnull', label='계약가능유닛')

    class Meta:
        model = KeyUnit
        fields = ('project', 'unit_type', 'contract', 'available')


class KeyUnitViewSet(viewsets.ModelViewSet):
    queryset = KeyUnit.objects.all()
    serializer_class = KeyUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = KeyUnitListFilterSet
    ordering_fields = ('pk', 'unit_code', 'unit_type')
    ordering = ('-pk',)


class BuildingUnitViewSet(viewsets.ModelViewSet):
    queryset = BuildingUnit.objects.all()
    serializer_class = BuildingUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)
    search_fields = ('name',)


class HouseUnitViewSet(viewsets.ModelViewSet):
    queryset = HouseUnit.objects.all()
    serializer_class = HouseUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('building_unit__project', 'unit_type__sort', 'unit_type',
                        'floor_type', 'building_unit', 'is_hold')
    search_fields = ('hold_reason',)


class AvailableHouseUnitViewSet(HouseUnitViewSet):
    pagination_class = PageNumberPaginationThreeHundred

    def get_queryset(self):
        houseunit = HouseUnit.objects.all()
        queryset = houseunit

        project = self.request.query_params.get('project', None)
        unit_type = self.request.query_params.get('unit_type', None)

        if project and unit_type:
            queryset = houseunit.filter(building_unit__project=project, unit_type=unit_type, key_unit__isnull=True)

        contract = self.request.query_params.get('contract', None)
        if contract is not None:
            queryset = houseunit.filter(
                Q(building_unit__project=project, unit_type=unit_type, key_unit__isnull=True) |
                Q(key_unit__contract=contract))
        return queryset


class AllHouseUnitViewSet(HouseUnitViewSet):
    serializer_class = AllHouseUnitSerializer
    pagination_class = PageNumberPaginationThreeThousand


class HouseUnitSummaryViewSet(viewsets.ModelViewSet):
    queryset = HouseUnit.objects.all()
    serializer_class = HouseUnitSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('building_unit__project', 'unit_type',
                        'floor_type', 'building_unit', 'is_hold')


class OptionItemViewSet(viewsets.ModelViewSet):
    queryset = OptionItem.objects.all()
    serializer_class = OptionItemSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'types')
    search_fields = ('opt_code', 'opt_name', 'opt_desc', 'opt_maker')
