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
    """contract 시리얼라이저에서 unit_type 간략 표시용으로 사용."""

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
        read_only_fields = ('__str__',)

    @staticmethod
    def _resolve_key_unit(validated_data):
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
        return validated_data

    def create(self, validated_data):
        return super().create(self._resolve_key_unit(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._resolve_key_unit(validated_data))


class ContractorInContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contractor
        fields = ('pk', 'name', 'status')


class ContractInKeyUnitSerializer(serializers.ModelSerializer):
    contractor = ContractorInContractSerializer()

    class Meta:
        model = Contract
        fields = ('pk', 'contractor')


class _SortCheckUnitTypeSerializer(serializers.ModelSerializer):
    """AllHouseUnitSerializer 내부 전용 — sort 필드만 노출."""

    class Meta:
        model = UnitType
        fields = ('pk', 'sort')


class KeyUnitInHouseUnitSerializer(serializers.ModelSerializer):
    contract = ContractInKeyUnitSerializer()

    class Meta:
        model = KeyUnit
        fields = ('pk', 'contract')


class AllHouseUnitSerializer(serializers.ModelSerializer):
    unit_type = _SortCheckUnitTypeSerializer()
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
        read_only_fields = ('pk',)

    def validate(self, attrs):
        opt_price = attrs.get('opt_price')
        opt_deposit = attrs.get('opt_deposit')
        opt_balance = attrs.get('opt_balance')

        if opt_price is not None and opt_deposit is not None and opt_balance is not None:
            if opt_deposit + opt_balance != opt_price:
                raise serializers.ValidationError(
                    {'opt_deposit': '계약금 + 잔금의 합계가 옵션가격과 일치해야 합니다.'}
                )
        return attrs
