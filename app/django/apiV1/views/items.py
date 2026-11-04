from django.db.models import Q, ProtectedError
from django_filters import BooleanFilter, NumberFilter, CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, serializers

from apiV1.permissions._utils import get_project_ids_with_permission
from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly
from apiV1.permissions.ibs_perms import IbsModulePermission
from items.models import UnitType, UnitFloorType, KeyUnit, BuildingUnit, HouseUnit, OptionItem
from work.models import IssueProject
from ..pagination import (
    PageNumberPaginationFifty, PageNumberPaginationOneHundred,
    PageNumberPaginationThreeHundred, PageNumberPaginationOneThousand,
    PageNumberPaginationThreeThousand
)
from ..serializers.items import (UnitTypeSerializer, UnitFloorTypeSerializer, KeyUnitSerializer,
                                 BuildingUnitSerializer, HouseUnitSerializer, AllHouseUnitSerializer,
                                 HouseUnitSummarySerializer, OptionItemSerializer)


def get_accessible_project_ids(user, required_perm: str = 'contract.read'):
    """[RLS] 사용자가 특정 권한(기본: contract.read)을 보유한 프로젝트 ID 목록 반환"""
    return get_project_ids_with_permission(user, required_perm)


# Items --------------------------------------------------------------------------
class UnitTypeViewSet(viewsets.ModelViewSet):
    queryset = UnitType.objects.select_related('project').all()
    serializer_class = UnitTypeSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('project', 'sort', 'main_or_sub')
    search_fields = ('name',)

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return None
        if self.action == 'destroy':
            return 'contract.delete'
        return 'contract.update'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError('유닛 또는 세대(호수) 데이터가 연결된 타입은 삭제할 수 없습니다.')


class UnitFloorTypeViewSet(viewsets.ModelViewSet):
    queryset = UnitFloorType.objects.select_related('project').all()
    serializer_class = UnitFloorTypeSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    filterset_fields = ('project', 'sort')
    search_fields = ('alias_name',)

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return None
        if self.action == 'destroy':
            return 'contract.delete'
        return 'contract.update'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))


class KeyUnitListFilterSet(FilterSet):
    available = BooleanFilter(field_name='contract', lookup_expr='isnull', label='계약가능유닛')

    class Meta:
        model = KeyUnit
        fields = ('project', 'unit_type', 'contract', 'available')


class KeyUnitViewSet(viewsets.ModelViewSet):
    queryset = KeyUnit.objects.select_related('houseunit', 'project', 'unit_type', 'contract').all()
    serializer_class = KeyUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_class = KeyUnitListFilterSet
    search_fields = ('unit_code',)
    ordering_fields = ('pk', 'unit_code', 'unit_type')
    ordering = ('-pk',)

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return None
        if self.action == 'destroy':
            return 'contract.delete'
        return 'contract.update'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    def perform_destroy(self, instance):
        if hasattr(instance, 'contract') and instance.contract is not None:
            raise serializers.ValidationError('계약이 체결된 계약 유닛은 삭제할 수 없습니다.')
        instance.delete()


class BuildingUnitViewSet(viewsets.ModelViewSet):
    queryset = BuildingUnit.objects.select_related('project').all()
    serializer_class = BuildingUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('project',)
    search_fields = ('name',)

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return None
        if self.action == 'destroy':
            return 'contract.delete'
        return 'contract.update'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError('호수(세대) 데이터가 연결된 동수는 삭제할 수 없습니다.')


class HouseUnitFilterSet(FilterSet):
    project = NumberFilter(field_name='building_unit__project_id', label='프로젝트')
    unit_type_sort = CharFilter(field_name='unit_type__sort', label='타입종류')

    class Meta:
        model = HouseUnit
        fields = (
            'project', 'building_unit__project', 'unit_type__sort', 'unit_type_sort',
            'unit_type', 'floor_type', 'building_unit', 'is_hold'
        )


class HouseUnitViewSet(viewsets.ModelViewSet):
    queryset = HouseUnit.objects.select_related('unit_type', 'floor_type', 'building_unit', 'key_unit').all()
    serializer_class = HouseUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_class = HouseUnitFilterSet
    search_fields = ('name', 'building_unit__name', 'hold_reason')

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return None
        if self.action == 'destroy':
            return 'contract.delete'
        return 'contract.update'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(building_unit__project_id__in=get_accessible_project_ids(user))

    def perform_destroy(self, instance):
        if instance.key_unit and hasattr(instance.key_unit, 'contract') and instance.key_unit.contract is not None:
            raise serializers.ValidationError('계약이 체결된 세대(호수)는 삭제할 수 없습니다.')
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError('계약 또는 공급가격 등 연관 데이터가 존재하는 세대는 삭제할 수 없습니다.')


class AvailableHouseUnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HouseUnit.objects.select_related('unit_type', 'floor_type', 'building_unit', 'key_unit').all()
    serializer_class = HouseUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = HouseUnitFilterSet
    search_fields = ('name', 'building_unit__name', 'hold_reason')

    @property
    def required_permission(self):
        return None

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        project = self.request.query_params.get('project', None)
        unit_type = self.request.query_params.get('unit_type', None)

        if project:
            queryset = queryset.filter(building_unit__project_id=project)
        if unit_type:
            queryset = queryset.filter(unit_type_id=unit_type)

        contract = self.request.query_params.get('contract', None)
        if contract:
            queryset = queryset.filter(
                Q(key_unit__isnull=True) | Q(key_unit__contract=contract)
            )
        else:
            queryset = queryset.filter(key_unit__isnull=True)

        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        return queryset.filter(building_unit__project_id__in=get_accessible_project_ids(user))


class AllHouseUnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HouseUnit.objects.select_related(
        'unit_type',
        'floor_type',
        'building_unit',
        'key_unit__contract__contractor',
        'key_unit__contract__contractprice',
    ).all()
    serializer_class = AllHouseUnitSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationThreeThousand
    filterset_class = HouseUnitFilterSet
    search_fields = ('name', 'building_unit__name', 'hold_reason')

    @property
    def required_permission(self):
        return None

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        return queryset.filter(building_unit__project_id__in=get_accessible_project_ids(user))


class HouseUnitSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HouseUnit.objects.select_related('unit_type', 'building_unit').all()
    serializer_class = HouseUnitSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    filterset_class = HouseUnitFilterSet
    search_fields = ('name', 'building_unit__name')

    @property
    def required_permission(self):
        return None

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(building_unit__project_id__in=get_accessible_project_ids(user))


class OptionItemViewSet(viewsets.ModelViewSet):
    queryset = OptionItem.objects.select_related('project').prefetch_related('types').all()
    serializer_class = OptionItemSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('project', 'types')
    search_fields = ('opt_code', 'opt_name', 'opt_desc', 'opt_maker')

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return None
        if self.action == 'destroy':
            return 'contract.delete'
        return 'contract.update'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs.distinct()
        return qs.filter(project_id__in=get_accessible_project_ids(user)).distinct()
