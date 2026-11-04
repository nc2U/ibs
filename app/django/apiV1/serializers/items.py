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

    def validate(self, attrs):
        project = attrs.get('project') or (self.instance.project if self.instance else None)
        name = attrs.get('name') or (self.instance.name if self.instance else '')
        if project and name:
            qs = UnitType.objects.filter(project=project, name=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'name': f'해당 프로젝트에 이미 동일한 타입 명칭({name})이 등록되어 있습니다.'})

        actual_area = attrs.get('actual_area', getattr(self.instance, 'actual_area', None))
        supply_area = attrs.get('supply_area', getattr(self.instance, 'supply_area', None))
        contract_area = attrs.get('contract_area', getattr(self.instance, 'contract_area', None))
        if actual_area is not None and supply_area is not None and actual_area > supply_area:
            raise serializers.ValidationError({'supply_area': '공급면적은 전용면적보다 크거나 같아야 합니다.'})
        if supply_area is not None and contract_area is not None and supply_area > contract_area:
            raise serializers.ValidationError({'contract_area': '계약면적은 공급면적보다 크거나 같아야 합니다.'})
        return attrs


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

    def validate(self, attrs):
        project = attrs.get('project') or (self.instance.project if self.instance else None)
        name = attrs.get('name') or (self.instance.name if self.instance else '')
        if project and name:
            qs = BuildingUnit.objects.filter(project=project, name=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'name': f'해당 프로젝트에 이미 동일한 동({name})이 등록되어 있습니다.'})
        return attrs


class KeyUnitSerializer(serializers.ModelSerializer):
    houseunit = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = KeyUnit
        fields = ('pk', 'project', 'unit_type', 'unit_code', 'houseunit', 'contract')
        read_only_fields = ('contract',)

    def validate(self, attrs):
        project = attrs.get('project') or (self.instance.project if self.instance else None)
        unit_type = attrs.get('unit_type') or (self.instance.unit_type if self.instance else None)
        if project and unit_type and project.id != unit_type.project_id:
            raise serializers.ValidationError(
                {'unit_type': '계약 유닛의 프로젝트와 타입의 프로젝트가 일치하지 않습니다.'}
            )
        return attrs


class HouseUnitSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(write_only=True, required=False, max_length=8)

    class Meta:
        model = HouseUnit
        fields = ('pk', 'unit_type', 'floor_type', '__str__', 'building_unit',
                  'name', 'key_unit', 'bldg_line', 'floor_no', 'is_hold', 'hold_reason',
                  'unit_code')
        read_only_fields = ('__str__',)

    def validate(self, attrs):
        building_unit = attrs.get('building_unit') or (self.instance.building_unit if self.instance else None)
        unit_type = attrs.get('unit_type') or (self.instance.unit_type if self.instance else None)
        floor_type = attrs.get('floor_type') or (self.instance.floor_type if self.instance else None)
        key_unit = attrs.get('key_unit') or (self.instance.key_unit if self.instance else None)

        errors = {}

        if building_unit and unit_type and building_unit.project_id != unit_type.project_id:
            errors['unit_type'] = '동수와 타입의 프로젝트가 일치하지 않습니다.'
        if building_unit and floor_type and floor_type.project_id != building_unit.project_id:
            errors['floor_type'] = '동수와 층범위 타입의 프로젝트가 일치하지 않습니다.'
        if building_unit and key_unit and key_unit.project_id != building_unit.project_id:
            errors['key_unit'] = '동수와 계약유닛의 프로젝트가 일치하지 않습니다.'
        if unit_type and key_unit and key_unit.unit_type_id != unit_type.id:
            errors['key_unit'] = '호수의 타입과 계약유닛의 타입이 일치하지 않습니다.'
        if key_unit and hasattr(key_unit, 'houseunit') and key_unit.houseunit is not None:
            if self.instance is None or key_unit.houseunit.pk != self.instance.pk:
                errors['key_unit'] = f'해당 유닛 코드({key_unit.unit_code})는 이미 다른 세대({key_unit.houseunit})에 배정되어 있습니다.'

        # [P0-보안] 계약이 체결된 세대의 주요 식별 필드(key_unit, unit_type, building_unit) 변경 차단
        has_contract = (
            self.instance is not None
            and self.instance.key_unit is not None
            and hasattr(self.instance.key_unit, 'contract')
            and self.instance.key_unit.contract is not None
        )
        if has_contract:
            if 'key_unit' in attrs and attrs['key_unit'] != self.instance.key_unit:
                errors['key_unit'] = '이미 계약이 체결된 세대의 계약 유닛은 변경할 수 없습니다.'
            if 'unit_type' in attrs and attrs['unit_type'] != self.instance.unit_type:
                errors['unit_type'] = '이미 계약이 체결된 세대의 타입은 변경할 수 없습니다.'
            if 'building_unit' in attrs and attrs['building_unit'] != self.instance.building_unit:
                errors['building_unit'] = '이미 계약이 체결된 세대의 동수는 변경할 수 없습니다.'

        # [P1-정합성] 동일 동 내 (floor_no, bldg_line) 및 호수명(name) 중복 방어
        floor_no = attrs.get('floor_no') if 'floor_no' in attrs else (self.instance.floor_no if self.instance else None)
        bldg_line = attrs.get('bldg_line') if 'bldg_line' in attrs else (self.instance.bldg_line if self.instance else None)
        name = attrs.get('name') if 'name' in attrs else (self.instance.name if self.instance else '')

        if building_unit and floor_no is not None and bldg_line is not None:
            qs_line = HouseUnit.objects.filter(building_unit=building_unit, floor_no=floor_no, bldg_line=bldg_line)
            if self.instance:
                qs_line = qs_line.exclude(pk=self.instance.pk)
            if qs_line.exists():
                errors['bldg_line'] = f'해당 동({building_unit.name}) {floor_no}층 {bldg_line}라인에 이미 등록된 세대가 존재합니다.'

        if building_unit and name:
            qs_name = HouseUnit.objects.filter(building_unit=building_unit, name=name)
            if self.instance:
                qs_name = qs_name.exclude(pk=self.instance.pk)
            if qs_name.exists():
                errors['name'] = f'해당 동({building_unit.name})에 이미 동일한 호수({name})가 등록되어 있습니다.'

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    @classmethod
    def _resolve_key_unit(cls, validated_data, instance=None):
        unit_code = validated_data.pop('unit_code', None)
        if unit_code:
            # [P0-보안] 계약이 체결된 세대의 unit_code 교체 방어
            if (
                instance is not None
                and instance.key_unit is not None
                and hasattr(instance.key_unit, 'contract')
                and instance.key_unit.contract is not None
            ):
                if unit_code != instance.key_unit.unit_code:
                    raise serializers.ValidationError({'unit_code': '이미 계약이 체결된 세대의 유닛 코드는 변경할 수 없습니다.'})

            building_unit = validated_data.get('building_unit') or (instance.building_unit if instance else None)
            unit_type = validated_data.get('unit_type') or (instance.unit_type if instance else None)
            if not building_unit or not unit_type:
                raise serializers.ValidationError(
                    {'unit_code': '유닛 코드를 배정하려면 동수(building_unit)와 타입(unit_type) 정보가 필요합니다.'}
                )
            if building_unit.project_id != unit_type.project_id:
                raise serializers.ValidationError(
                    {'unit_type': '동수와 타입의 프로젝트가 일치하지 않습니다.'}
                )
            # [C-2] transaction.atomic + select_for_update 으로 Race Condition 차단
            # get_or_create 시 다른 타입과의 unique_together 충돌(500)을 방어하기 위해 filter 후 검증
            with transaction.atomic():
                key_unit = KeyUnit.objects.select_for_update().filter(
                    project=building_unit.project,
                    unit_code=unit_code,
                ).first()
                if key_unit:
                    if key_unit.unit_type_id != unit_type.pk:
                        raise serializers.ValidationError(
                            {'unit_code': f'해당 유닛 코드({unit_code})는 이미 다른 타입({key_unit.unit_type})으로 등록되어 있습니다.'}
                        )
                else:
                    key_unit = KeyUnit.objects.create(
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

        if opt_price is not None:
            if opt_deposit is not None and opt_balance is None:
                if opt_deposit > opt_price:
                    raise serializers.ValidationError({'opt_deposit': '계약금은 옵션가격을 초과할 수 없습니다.'})
                attrs['opt_balance'] = opt_price - opt_deposit
            elif opt_deposit is None and opt_balance is not None:
                if opt_balance > opt_price:
                    raise serializers.ValidationError({'opt_balance': '잔금은 옵션가격을 초과할 수 없습니다.'})
                attrs['opt_deposit'] = opt_price - opt_balance
            elif opt_deposit is not None and opt_balance is not None:
                if opt_deposit + opt_balance != opt_price:
                    raise serializers.ValidationError(
                        {'opt_deposit': '계약금 + 잔금의 합계가 옵션가격과 일치해야 합니다.'}
                    )

        types = attrs.get('types')
        project = attrs.get('project') or (self.instance.project if self.instance else None)
        if types and project:
            invalid_types = [t for t in types if t.project_id != project.id]
            if invalid_types:
                raise serializers.ValidationError(
                    {'types': '옵션 품목의 프로젝트와 타입 구분의 프로젝트가 일치해야 합니다.'}
                )
        return attrs
