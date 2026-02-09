from rest_framework import serializers

from contract.models import Contract, Contractor
from items.models import UnitType, UnitFloorType, KeyUnit, BuildingUnit, HouseUnit, OptionItem


# Items --------------------------------------------------------------------------
class UnitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ('pk', 'project', 'sort', 'main_or_sub', 'name', 'color',
                  'actual_area', 'supply_area', 'contract_area',
                  'average_price', 'price_setting', 'num_unit')


class SimpleUnitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ('pk', 'name', 'color', 'average_price')


class UnitFloorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitFloorType
        fields = ('pk', 'project', 'sort', 'start_floor', 'end_floor', 'extra_cond', 'alias_name')


class BuildingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingUnit
        fields = ('pk', 'project', 'name')


class KeyUnitSerializer(serializers.ModelSerializer):
    houseunit = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = KeyUnit
        fields = ('pk', 'project', 'unit_type', 'unit_code', 'houseunit', 'contract')
        read_only_fields = ('contract',)


class HouseUnitSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = HouseUnit
        fields = ('pk', 'unit_type', 'floor_type', '__str__', 'building_unit',
                  'name', 'key_unit', 'bldg_line', 'floor_no', 'is_hold', 'hold_reason',
                  'unit_code')

    def create(self, validated_data):
        unit_code = validated_data.pop('unit_code', None)
        if unit_code:
            project = validated_data['building_unit'].project
            unit_type = validated_data['unit_type']
            key_unit, _ = KeyUnit.objects.get_or_create(
                project=project,
                unit_type=unit_type,
                unit_code=unit_code,
            )
            validated_data['key_unit'] = key_unit
        return super().create(validated_data)


class ContractorInContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contractor
        fields = ('pk', 'name', 'status')


class ContractInKeyUnitSerializer(serializers.ModelSerializer):
    contractor = ContractorInContractSerializer()

    class Meta:
        model = Contract
        fields = ('pk', 'contractor')


class SortCheckUnitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ('pk', 'sort')


class KeyUnitInHouseUnitSerializer(serializers.ModelSerializer):
    contract = ContractInKeyUnitSerializer()

    class Meta:
        model = KeyUnit
        fields = ('pk', 'contract')


class AllHouseUnitSerializer(serializers.ModelSerializer):
    unit_type = SortCheckUnitTypeSerializer()
    key_unit = KeyUnitInHouseUnitSerializer()

    class Meta:
        model = HouseUnit
        fields = ('pk', 'unit_type', 'floor_type', 'building_unit',
                  'name', 'key_unit', 'bldg_line', 'floor_no', 'is_hold', 'hold_reason')


class HouseUnitSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseUnit
        fields = ('pk', 'unit_type', 'building_unit', 'name')


class OptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionItem
        fields = ('pk', 'project', 'types', 'opt_code', 'opt_name', 'opt_desc',
                  'opt_maker', 'opt_price', 'opt_deposit', 'opt_balance')
