from django.db import transaction
from rest_framework import serializers

from contract.models import Contract, Contractor, ContractPrice
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

    def validate(self, attrs):
        start_floor = attrs.get('start_floor') if 'start_floor' in attrs else (self.instance.start_floor if self.instance else None)
        end_floor = attrs.get('end_floor') if 'end_floor' in attrs else (self.instance.end_floor if self.instance else None)
        if start_floor is not None and end_floor is not None and start_floor > end_floor:
            raise serializers.ValidationError(
                {'end_floor': '종료 층은 시작 층보다 크거나 같아야 합니다.'}
            )
        return attrs


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
    unit_code = serializers.CharField(write_only=True, required=False, max_length=8)

    class Meta:
        model = HouseUnit
        fields = ('pk', 'unit_type', 'floor_type', '__str__', 'building_unit',
                  'name', 'key_unit', 'bldg_line', 'floor_no', 'is_hold', 'hold_reason',
                  'unit_code')
        read_only_fields = ('__str__',)

    @classmethod
    def _resolve_key_unit(cls, validated_data, instance=None):
        unit_code = validated_data.pop('unit_code', None)
        if unit_code:
            building_unit = validated_data.get('building_unit') or (instance.building_unit if instance else None)
            unit_type = validated_data.get('unit_type') or (instance.unit_type if instance else None)
            if not building_unit or not unit_type:
                raise serializers.ValidationError(
                    {'unit_code': '유닛 코드를 배정하려면 동수(building_unit)와 타입(unit_type) 정보가 필요합니다.'}
                )
            # [C-2] transaction.atomic + select_for_update 으로 Race Condition 차단
            # get_or_create 이후 행 락을 즉시 획득하여 동시 요청의 이중 배정을 원천 방지
            with transaction.atomic():
                key_unit, _ = KeyUnit.objects.select_for_update().get_or_create(
                    project=building_unit.project,
                    unit_type=unit_type,
                    unit_code=unit_code,
                )
                if hasattr(key_unit, 'houseunit') and key_unit.houseunit is not None:
                    if instance is None or key_unit.houseunit.pk != instance.pk:
                        raise serializers.ValidationError(
                            {'unit_code': f'해당 유닛 코드({unit_code})는 이미 다른 세대({key_unit.houseunit})에 배정되어 있습니다.'}
                        )
                validated_data['key_unit'] = key_unit
        return validated_data

    def create(self, validated_data):
        return super().create(self._resolve_key_unit(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._resolve_key_unit(validated_data, instance=instance))



class ContractorInContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contractor
        fields = ('pk', 'name', 'status')


class _ContPriceInKeyUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractPrice
        fields = ('pk', 'price', 'price_build', 'price_land', 'price_tax')


class ContractInKeyUnitSerializer(serializers.ModelSerializer):
    contractor = ContractorInContractSerializer()
    contractprice = _ContPriceInKeyUnitSerializer(read_only=True)

    class Meta:
        model = Contract
        fields = ('pk', 'serial_number', 'contractor', 'contractprice')


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
        opt_price = attrs.get('opt_price') if 'opt_price' in attrs else (self.instance.opt_price if self.instance else None)
        opt_deposit = attrs.get('opt_deposit') if 'opt_deposit' in attrs else (self.instance.opt_deposit if self.instance else None)
        opt_balance = attrs.get('opt_balance') if 'opt_balance' in attrs else (self.instance.opt_balance if self.instance else None)

        if opt_price is not None and opt_deposit is not None and opt_balance is not None:
            if opt_deposit + opt_balance != opt_price:
                raise serializers.ValidationError(
                    {'opt_deposit': '계약금 + 잔금의 합계가 옵션가격과 일치해야 합니다.'}
                )
        return attrs
