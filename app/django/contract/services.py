"""
Contract 관련 비즈니스 로직 서비스
"""
import os
import uuid
import logging
from datetime import date, datetime, timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import serializers

logger = logging.getLogger(__name__)

from _utils.contract_price import (
    bump_payment_summary_cache_version,
    get_contract_price,
    get_sales_price_by_gt,
)
from _utils.rrn_crypto import decrypt_rrn, encrypt_rrn, hash_rrn, normalize_and_parse_rrn
from apiV1.serializers.ledger import ProjectCompositeTransactionSerializer
from contract.models import (Contract, ContractPrice, OrderGroup, ContractFile,
                             Contractor, ContractorAddress, ContractorContact,
                             ContractorSensitiveInfo, ContractorSensitiveAccessLog)
from items.models import KeyUnit, HouseUnit
from ledger.models import ProjectAccount, ProjectBankAccount
from payment.models import InstallmentPaymentOrder, SalesPriceByGT, ContractPayment
from project.models import Project

logger = logging.getLogger(__name__)


def clean_date_value(value):
    """빈 문자열을 None으로 변환하는 유틸리티 함수"""
    if value == '' or value is None:
        return None
    return value


def clean_id_value(value):
    """빈 문자열을 None으로 변환하고 정수로 변환하는 유틸리티 함수"""
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class ContractPriceBulkUpdateService:
    """
    SalesPriceByGT 변경 시 프로젝트 내 모든 계약 가격 일괄 업데이트 서비스

    주요 용도:
    - 분양가격표(SalesPriceByGT) 변경 후 기존 계약들에 새 가격 정책 반영
    - 프로젝트 전체 계약의 ContractPrice 일괄 업데이트
    """

    def __init__(self, project, order_group_for_uncontracted=None):
        self.project = project
        # order_group_for_uncontracted가 명시적으로 제공되지 않으면 프로젝트의 기본 차수 사용
        if order_group_for_uncontracted is None:
            self.order_group_for_uncontracted = OrderGroup.get_default_for_project(project)
        else:
            self.order_group_for_uncontracted = order_group_for_uncontracted

    @transaction.atomic
    def update_all_contract_prices(self):
        """
        프로젝트 내 모든 유효 계약의 가격 정보 업데이트 및 미계약 세대 ContractPrice 생성

        Returns:
            dict: 업데이트 결과 정보
                - updated_count: 업데이트된 계약 수
                - created_count: 새로 생성된 ContractPrice 수
                - updated_contracts: 업데이트된 계약 ID 목록
                - uncontracted_created_count: 미계약 세대 ContractPrice 생성 수
                - errors: 오류 발생한 계약 정보
        """
        # [M-2] 일괄 가격 업데이트 중 개별 계약 수정과의 Race Condition 방지를 위한 row-level lock
        contracts = Contract.objects.select_for_update().filter(
            project=self.project,
            is_active=True
        )

        updated_contracts = []
        created_count = 0
        updated_count = 0
        errors = []

        # Phase 1: 계약이 있는 ContractPrice 업데이트
        for contract in contracts:
            try:
                with transaction.atomic():
                    # 동호수 지정 여부 확인
                    try:
                        house_unit = contract.key_unit.houseunit if contract.key_unit else None
                    except ObjectDoesNotExist:
                        house_unit = None

                    # 1. 기준 공급가, 2. 수입 예산 평균가, 3. 타입 평균가 순 참조 공급가 가져오기
                    price = get_contract_price(contract, house_unit, True)

                    # ContractPrice 업데이트/생성 (house_unit도 함께 설정)
                    cont_price, created = self._update_or_create_contract_price(contract, price, house_unit)

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    updated_contracts.append(contract.pk)

            except Exception as e:
                errors.append({
                    'contract_id': contract.pk,
                    'serial_number': contract.serial_number,
                    'error': str(e)
                })

        # Phase 2: 미계약 세대에 대한 ContractPrice 생성
        uncontracted_created_count = 0
        if self.order_group_for_uncontracted:
            uncontracted_created_count = self._create_uncontracted_prices()

        bump_payment_summary_cache_version(self.project.pk)

        return {
            'total_processed': len(contracts),
            'updated_count': updated_count,
            'created_count': created_count,
            'updated_contracts': updated_contracts,
            'uncontracted_created_count': uncontracted_created_count,
            'errors': errors
        }

    @staticmethod
    def _update_or_create_contract_price(contract, price, house_unit=None):
        """
        개별 계약의 ContractPrice 업데이트 또는 생성 (생성/수정 분리 방식)

        Args:
            contract: Contract 인스턴스
            price: 가격 정보 튜플 (price, price_build, price_land, price_tax)
            house_unit: HouseUnit 인스턴스 (옵션)

        Returns:
            tuple: (ContractPrice 인스턴스, created 여부)
        """
        try:
            # 기존 ContractPrice 조회
            existing = ContractPrice.objects.get(contract=contract)

            # 수정: 가격 정보만 업데이트, order_group은 유지
            existing.price = price[0]
            existing.price_build = price[1]
            existing.price_land = price[2]
            existing.price_tax = price[3]

            if house_unit and existing.house_unit != house_unit:
                # 다른 ContractPrice가 해당 house_unit을 가지고 있는지 확인하고 detach
                conflicting_price = ContractPrice.objects.filter(house_unit=house_unit).exclude(pk=existing.pk).first()
                if conflicting_price:
                    conflicting_price.house_unit = None
                    conflicting_price.save()
                existing.house_unit = house_unit

            existing.save()  # order_group은 변경되지 않음 (save 메서드에서 생성시에만 설정)
            return existing, False

        except ContractPrice.DoesNotExist:
            # 생성: house_unit으로 기존 ContractPrice가 있는지 확인하여 재사용
            if house_unit:
                try:
                    existing_by_unit = ContractPrice.objects.get(house_unit=house_unit)
                    existing_by_unit.contract = contract
                    existing_by_unit.price = price[0]
                    existing_by_unit.price_build = price[1]
                    existing_by_unit.price_land = price[2]
                    existing_by_unit.price_tax = price[3]
                    existing_by_unit.save()
                    return existing_by_unit, False
                except ContractPrice.DoesNotExist:
                    pass

            defaults = {
                'price': price[0],
                'price_build': price[1],
                'price_land': price[2],
                'price_tax': price[3],
            }

            if house_unit:
                defaults['house_unit'] = house_unit

            # order_group은 save() 메서드에서 자동 설정됨
            new_contract_price = ContractPrice.objects.create(
                contract=contract,
                **defaults
            )
            return new_contract_price, True

    def get_contracts_to_update(self):
        """
        업데이트 대상 계약 목록 조회 (미리보기용)

        Returns:
            QuerySet: 업데이트 대상 계약들
        """
        return Contract.objects.filter(
            project=self.project,
            is_active=True
        ).select_related(
            'unit_type', 'order_group', 'contractor', 'contractprice', 'key_unit__houseunit'
        )

    def validate_project(self):
        """
        프로젝트 유효성 검증

        Returns:
            dict: 검증 결과
        """
        contracts_count = self.get_contracts_to_update().count()

        return {
            'project_id': self.project.pk,
            'project_name': self.project.name,
            'active_contracts_count': contracts_count,
            'is_valid': contracts_count > 0
        }

    def _create_uncontracted_prices(self):
        """
        미계약 세대에 대한 ContractPrice 생성/수정 (생성/수정 분리 방식)

        Returns:
            int: 생성/수정된 ContractPrice 수
        """
        processed_count = 0

        # 미계약 세대 조회 (key_unit이 없거나 contract가 없는 세대들)
        uncontracted_houses = HouseUnit.objects.filter(
            unit_type__project=self.project,
        ).exclude(
            key_unit__contract__isnull=False,  # 계약이 있는 세대는 제외
            key_unit__contract__is_active=True  # 활성화된 계약만 제외
        ).select_related('unit_type', 'floor_type')

        for house_unit in uncontracted_houses:
            try:
                # 기존 미계약 ContractPrice 조회
                try:
                    existing = ContractPrice.objects.get(house_unit=house_unit, contract__isnull=True)

                    # 수정: 가격만 업데이트, order_group은 유지
                    try:
                        sales_price = SalesPriceByGT.objects.get(
                            project=self.project,
                            order_group=self.order_group_for_uncontracted,
                            unit_type=house_unit.unit_type,
                            unit_floor_type=house_unit.floor_type
                        )

                        existing.price = sales_price.price
                        existing.price_build = sales_price.price_build
                        existing.price_land = sales_price.price_land
                        existing.price_tax = sales_price.price_tax
                        existing.save()  # order_group은 유지됨
                        processed_count += 1

                    except SalesPriceByGT.DoesNotExist:
                        pass

                except ContractPrice.DoesNotExist:
                    # 생성: 새로 생성 (order_group은 save()에서 자동 설정)
                    try:
                        sales_price = SalesPriceByGT.objects.get(
                            project=self.project,
                            order_group=self.order_group_for_uncontracted,
                            unit_type=house_unit.unit_type,
                            unit_floor_type=house_unit.floor_type
                        )

                        ContractPrice.objects.create(
                            contract=None,
                            house_unit=house_unit,
                            price=sales_price.price,
                            price_build=sales_price.price_build,
                            price_land=sales_price.price_land,
                            price_tax=sales_price.price_tax
                            # order_group은 save()에서 자동 설정됨
                        )
                        processed_count += 1

                    except SalesPriceByGT.DoesNotExist:
                        continue

            except Exception as e:
                # [H-8] 에러를 조용히 삼키지 않고 반드시 로깅하여 운영 중 추적 가능하게 함
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(
                    f'[ContractPriceBulkUpdateService] 미계약 세대 ContractPrice 처리 중 오류 발생 '
                    f'(house_unit_id={house_unit.pk}): {e}',
                    exc_info=True
                )
                continue

        return processed_count


class ContractPriceUpdateService:
    """
    개별 계약 가격 업데이트 서비스
    """

    @staticmethod
    def update_single_contract_price(contract):
        """
        단일 계약의 가격 정보 업데이트 (생성/수정 분리 방식)

        Args:
            contract: Contract 인스턴스

        Returns:
            tuple: (ContractPrice 인스턴스, created 여부)
        """
        try:
            house_unit = contract.key_unit.houseunit if contract.key_unit else None
        except ObjectDoesNotExist:
            house_unit = None

        price = get_contract_price(contract, house_unit, True)  # is_set=True for consistency

        try:
            # 기존 ContractPrice 조회 (contract 기준)
            existing = ContractPrice.objects.get(contract=contract)

            # 수정: 가격 정보만 업데이트, order_group은 유지
            existing.price = price[0]
            existing.price_build = price[1]
            existing.price_land = price[2]
            existing.price_tax = price[3]

            if house_unit and existing.house_unit != house_unit:
                # 다른 ContractPrice가 해당 house_unit을 가지고 있는지 확인하고 detach
                conflicting_price = ContractPrice.objects.filter(house_unit=house_unit).exclude(pk=existing.pk).first()
                if conflicting_price:
                    conflicting_price.house_unit = None
                    conflicting_price.save()
                existing.house_unit = house_unit

            existing.save()  # order_group은 변경되지 않음
            return existing, False

        except ContractPrice.DoesNotExist:
            # house_unit으로 기존 ContractPrice가 있는지 확인
            if house_unit:
                try:
                    existing_by_unit = ContractPrice.objects.get(house_unit=house_unit)
                    # 기존 레코드를 현재 contract로 업데이트
                    existing_by_unit.contract = contract
                    existing_by_unit.price = price[0]
                    existing_by_unit.price_build = price[1]
                    existing_by_unit.price_land = price[2]
                    existing_by_unit.price_tax = price[3]
                    existing_by_unit.save()
                    return existing_by_unit, False
                except ContractPrice.DoesNotExist:
                    pass

            # 생성: 새로 생성 (order_group은 save()에서 자동 설정)
            defaults = {
                'price': price[0],
                'price_build': price[1],
                'price_land': price[2],
                'price_tax': price[3],
            }

            if house_unit:
                defaults['house_unit'] = house_unit

            new_contract_price = ContractPrice.objects.create(
                contract=contract,
                **defaults
            )
            return new_contract_price, True


# 새로운 Contract 관리 서비스들
class UnitAssignmentService:
    """유닛 할당/재할당 관리 서비스"""

    @staticmethod
    def _validate_and_get_key_unit(contract, unit_pk):
        key_unit = KeyUnit.objects.select_related('unit_type').filter(pk=unit_pk).first()
        if not key_unit:
            raise serializers.ValidationError({'key_unit': '유효한 계약 유닛을 찾을 수 없습니다.'})

        key_unit_project_id = getattr(key_unit, 'project_id', None) or getattr(key_unit.unit_type, 'project_id', None)
        if contract.project_id and key_unit_project_id and key_unit_project_id != contract.project_id:
            raise serializers.ValidationError({'key_unit': '계약의 프로젝트와 유닛의 프로젝트가 일치하지 않습니다.'})

        if contract.unit_type_id and key_unit.unit_type_id != contract.unit_type_id:
            raise serializers.ValidationError('계약의 타입과 유닛의 타입이 일치하지 않습니다.')

        occupied_qs = Contract.objects.filter(key_unit=key_unit)
        if contract.pk:
            occupied_qs = occupied_qs.exclude(pk=contract.pk)
        if occupied_qs.exists():
            raise serializers.ValidationError({'key_unit': '이미 다른 계약에 할당된 계약 유닛입니다.'})

        return key_unit

    @staticmethod
    def _validate_and_get_house_unit(contract, key_unit, house_unit_pk):
        house_unit = HouseUnit.objects.select_related('unit_type').filter(pk=house_unit_pk).first()
        if not house_unit:
            raise serializers.ValidationError({'houseunit': '유효한 동호수(세대) 정보를 찾을 수 없습니다.'})

        hu_project_id = getattr(house_unit.unit_type, 'project_id', None) if house_unit.unit_type else None
        if contract.project_id and hu_project_id and hu_project_id != contract.project_id:
            raise serializers.ValidationError({'houseunit': '계약의 프로젝트와 세대(동호수)의 프로젝트가 일치하지 않습니다.'})

        if key_unit and house_unit.unit_type_id and key_unit.unit_type_id != house_unit.unit_type_id:
            raise serializers.ValidationError({'houseunit': '유닛의 타입과 세대(동호수)의 타입이 일치하지 않습니다.'})

        if house_unit.key_unit_id and (not key_unit or house_unit.key_unit_id != key_unit.pk):
            other_contract_occupied = Contract.objects.filter(key_unit_id=house_unit.key_unit_id)
            if contract.pk:
                other_contract_occupied = other_contract_occupied.exclude(pk=contract.pk)
            if other_contract_occupied.exists():
                raise serializers.ValidationError({'houseunit': '이미 다른 계약에 배정된 동호수(세대)입니다.'})

        return house_unit

    @staticmethod
    def assign_unit(contract, unit_pk, house_unit_pk=None):
        """
        계약에 유닛 할당

        Args:
            contract: Contract 인스턴스
            unit_pk: KeyUnit PK (None인 경우 유닛 할당 건너뜀)
            house_unit_pk: HouseUnit PK (선택사항)

        Returns:
            HouseUnit 인스턴스 또는 None
        """
        # unitSet=false인 경우 unit_pk가 None일 수 있음
        if not unit_pk:
            return None

        key_unit = UnitAssignmentService._validate_and_get_key_unit(contract, unit_pk)
        house_unit = (
            UnitAssignmentService._validate_and_get_house_unit(contract, key_unit, house_unit_pk)
            if house_unit_pk else None
        )

        contract.key_unit = key_unit
        contract.save()

        if house_unit:
            house_unit.key_unit = key_unit
            house_unit.save()
            return house_unit
        return None

    @staticmethod
    @transaction.atomic  # [H-1] 3개 객체(Contract, old/new HouseUnit) 저장을 원자적 트랜잭션으로 보호
    def reassign_unit(contract, new_unit_pk, new_house_unit_pk=None):
        """
        계약의 유닛 재할당 (기존 연결 해제 후 새 연결)

        Args:
            contract: Contract 인스턴스
            new_unit_pk: 새 KeyUnit PK
            new_house_unit_pk: 새 HouseUnit PK (선택사항)

        Returns:
            dict: {'old_house_unit': HouseUnit|None, 'new_house_unit': HouseUnit|None}
        """

        old_house_unit = None
        new_house_unit = None

        new_key_unit = UnitAssignmentService._validate_and_get_key_unit(contract, new_unit_pk)
        if new_house_unit_pk:
            new_house_unit = UnitAssignmentService._validate_and_get_house_unit(
                contract, new_key_unit, new_house_unit_pk
            )

        # 기존 연결 해제
        if contract.key_unit:
            try:
                old_house_unit = contract.key_unit.houseunit
                if old_house_unit and (not new_house_unit_pk or old_house_unit.pk != new_house_unit_pk):
                    old_house_unit.key_unit = None
                    old_house_unit.save()
            except ObjectDoesNotExist:
                pass

        contract.key_unit = new_key_unit
        contract.save()

        if new_house_unit:
            new_house_unit.key_unit = new_key_unit
            new_house_unit.save()

        return {
            'old_house_unit': old_house_unit,
            'new_house_unit': new_house_unit
        }


class ContractorSensitiveService:
    """계약자 고유식별정보(주민등록번호) 암호화 저장·열람·파기 및 감사 로그 서비스"""

    @staticmethod
    def can_collect_rrn(contractor: Contractor) -> bool:
        """청약('1') 단계는 수집 제한 (본계약 '2' 이상만 허용)"""
        return contractor.status != '1'

    @staticmethod
    def _contractor_context_snapshot(contractor: Contractor) -> tuple[int | None, str]:
        rel_contract = getattr(contractor, 'contract', None) or getattr(contractor, 'prev_contract', None)
        if not rel_contract:
            return None, ''
        return rel_contract.project_id, rel_contract.serial_number or ''

    @staticmethod
    @transaction.atomic
    def upsert_rrn(
        contractor: Contractor,
        raw_rrn: str,
        legal_basis: str = '1',
        actor=None,
        purpose: str = '계약자 식별정보 등록/갱신',
        ip_address: str | None = None,
        retention_until=None,
    ) -> ContractorSensitiveInfo:
        if not ContractorSensitiveService.can_collect_rrn(contractor):
            raise serializers.ValidationError({
                'rrn': '청약 단계에서는 주민등록번호를 수집할 수 없습니다. 계약 전환 후 입력해 주십시오.'
            })

        try:
            digits, parsed_birth_date, parsed_gender, masked = normalize_and_parse_rrn(raw_rrn)
        except DjangoValidationError as exc:
            logger.warning("RRN validation failed in upsert_rrn", exc_info=True)
            raise serializers.ValidationError({'rrn': '주민등록번호 형식이 올바르지 않습니다.'}) from exc

        valid_bases = {choice[0] for choice in ContractorSensitiveInfo.LEGAL_BASIS_CHOICES}
        basis = legal_basis if legal_basis in valid_bases else '1'

        # 기존 birth_date / gender 와 교차 검증 및 미입력 시 자동 보완
        existing_birth = contractor.birth_date
        if isinstance(existing_birth, str) and existing_birth:
            try:
                existing_birth = date.fromisoformat(existing_birth)
            except ValueError:
                existing_birth = None

        update_fields = []
        if existing_birth and existing_birth != parsed_birth_date:
            raise serializers.ValidationError({
                'rrn': f'입력한 주민등록번호 생년월일({parsed_birth_date})이 계약자 생년월일({existing_birth})과 일치하지 않습니다.'
            })
        if not existing_birth:
            contractor.birth_date = parsed_birth_date
            update_fields.append('birth_date')

        if contractor.gender and contractor.gender != parsed_gender:
            raise serializers.ValidationError({
                'rrn': '입력한 주민등록번호의 성별이 계약자 성별과 일치하지 않습니다.'
            })
        if not contractor.gender:
            contractor.gender = parsed_gender
            update_fields.append('gender')

        if update_fields:
            contractor.save(update_fields=update_fields)

        has_existing = ContractorSensitiveInfo.objects.filter(contractor=contractor).exists()
        defaults = {
            'encrypted_rrn': encrypt_rrn(digits),
            'rrn_hash': hash_rrn(digits),
            'rrn_masked': masked,
            'legal_basis': basis,
            'updator': actor,
        }
        if retention_until is not None:
            defaults['retention_until'] = clean_date_value(retention_until)
        if not has_existing:
            defaults['creator'] = actor

        info, _ = ContractorSensitiveInfo.objects.update_or_create(
            contractor=contractor,
            defaults=defaults,
        )

        project_id, serial_number = ContractorSensitiveService._contractor_context_snapshot(contractor)
        ContractorSensitiveAccessLog.objects.create(
            contractor=contractor,
            project_id_snapshot=project_id,
            contractor_name_snapshot=(contractor.name or '')[:50],
            contract_serial_snapshot=(serial_number or '')[:30],
            actor=actor,
            action='CREATE_UPDATE',
            purpose=(purpose or '계약자 식별정보 등록/갱신')[:150],
            ip_address=ip_address,
        )
        return info

    @staticmethod
    def reveal_rrn(
        contractor: Contractor,
        actor,
        purpose: str,
        ip_address: str | None = None,
        formatted: bool = True,
    ) -> str:
        clean_purpose = str(purpose or '').strip()
        if not clean_purpose:
            raise serializers.ValidationError({'purpose': '주민등록번호 열람 사유를 입력해 주십시오.'})

        info = getattr(contractor, 'sensitive_info', None)
        if not info:
            raise serializers.ValidationError({'detail': '등록된 주민등록번호 정보가 없습니다.'})

        try:
            plain_rrn = decrypt_rrn(info.encrypted_rrn, formatted=formatted)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'detail': '주민등록번호를 복호화할 수 없습니다.'}) from exc

        project_id, serial_number = ContractorSensitiveService._contractor_context_snapshot(contractor)
        ContractorSensitiveAccessLog.objects.create(
            contractor=contractor,
            project_id_snapshot=project_id,
            contractor_name_snapshot=(contractor.name or '')[:50],
            contract_serial_snapshot=(serial_number or '')[:30],
            actor=actor,
            action='VIEW_PLAIN',
            purpose=clean_purpose[:150],
            ip_address=ip_address,
        )
        return plain_rrn

    @staticmethod
    @transaction.atomic
    def purge_rrn(
        contractor: Contractor,
        actor=None,
        purpose: str = '계약자 민감정보 파기',
        ip_address: str | None = None,
    ) -> bool:
        deleted, _ = ContractorSensitiveInfo.objects.filter(contractor=contractor).delete()
        if not deleted:
            return False

        project_id, serial_number = ContractorSensitiveService._contractor_context_snapshot(contractor)
        ContractorSensitiveAccessLog.objects.create(
            contractor=contractor,
            project_id_snapshot=project_id,
            contractor_name_snapshot=(contractor.name or '')[:50],
            contract_serial_snapshot=(serial_number or '')[:30],
            actor=actor,
            action='PURGE',
            purpose=(purpose or '계약자 민감정보 파기')[:150],
            ip_address=ip_address,
        )
        return True

    @staticmethod
    def _coerce_base_date(base_date=None) -> date:
        if isinstance(base_date, datetime):
            return base_date.date()
        if isinstance(base_date, date):
            return base_date
        if isinstance(base_date, str) and base_date.strip():
            try:
                return date.fromisoformat(base_date.strip())
            except ValueError:
                pass
        return timezone.localdate()

    @staticmethod
    def schedule_retention(contractor: Contractor, base_date=None) -> date | None:
        """계약 종결/해지 확정/승계 양도 완료 시 법정 보존기한(기본 5년) 만료일 설정"""
        if not contractor:
            return None
        retention_days = max(1, int(getattr(settings, 'RRN_RETENTION_DAYS', 365 * 5)))
        retention_until = ContractorSensitiveService._coerce_base_date(base_date) + timedelta(days=retention_days)
        updated = ContractorSensitiveInfo.objects.filter(contractor=contractor).update(
            retention_until=retention_until
        )
        return retention_until if updated else None

    @staticmethod
    def clear_retention(contractor: Contractor) -> None:
        """정상 계약 상태('2') 복원 시 보존 만료 예정일 해제"""
        if not contractor:
            return
        ContractorSensitiveInfo.objects.filter(
            contractor=contractor,
            retention_until__isnull=False,
        ).update(retention_until=None)

    @staticmethod
    @transaction.atomic
    def purge_expired_rrns(
        as_of_date: date | None = None,
        actor=None,
        purpose: str = '보존기한 만료 자동 파기',
    ) -> int:
        """보존기한(retention_until)이 도래한 주민등록번호 일괄 파기 및 감사 로그 기록"""
        target_date = ContractorSensitiveService._coerce_base_date(as_of_date)
        expired_qs = ContractorSensitiveInfo.objects.select_related(
            'contractor__contract',
            'contractor__prev_contract',
        ).filter(
            retention_until__isnull=False,
            retention_until__lte=target_date,
        )
        expired_items = list(expired_qs)
        if not expired_items:
            return 0

        logs = []
        info_ids = []
        for info in expired_items:
            info_ids.append(info.pk)
            contractor = info.contractor
            project_id, serial_number = ContractorSensitiveService._contractor_context_snapshot(contractor)
            logs.append(ContractorSensitiveAccessLog(
                contractor=contractor,
                project_id_snapshot=project_id,
                contractor_name_snapshot=(contractor.name if contractor else '')[:50],
                contract_serial_snapshot=(serial_number or '')[:30],
                actor=actor,
                action='PURGE',
                purpose=f'{purpose} (만료일: {info.retention_until})'[:150],
                ip_address=None,
            ))

        ContractorSensitiveAccessLog.objects.bulk_create(logs)
        ContractorSensitiveInfo.objects.filter(pk__in=info_ids).delete()
        return len(info_ids)


class ContractorRegistrationService:
    """계약자 등록/수정 관리 서비스"""

    @staticmethod
    def register_contractor(contract, data, user=None, ip_address=None):
        """
        새 계약자 등록 (계약 생성 시)

        Args:
            contract: Contract 인스턴스
            data: 계약자 정보 딕셔너리

        Returns:
            Contractor 인스턴스
        """

        # 차수 종류에 따른 등록상태(qualification) 기본값 처리:
        # 일반분양(sort='2')이면 무조건 일반('1'), 조합(sort='1')이면 전달값 또는 기본 미인가('2')
        if contract.order_group and contract.order_group.sort == '2':
            qualification = '1'
        else:
            qualification = data.get('qualification') or '2'

        contractor = Contractor.objects.create(
            contract=contract,
            name=data.get('name'),
            birth_date=clean_date_value(data.get('birth_date')),
            gender=data.get('gender') or '',
            qualification=qualification,
            status=data.get('status', '1'),  # 프론트에서 'status' 키로 전송
            change_type=data.get('change_type'),
            reservation_date=clean_date_value(data.get('reservation_date')),
            contract_date=clean_date_value(data.get('contract_date')),
            note=data.get('note', '')
        )

        # 계약자 연락처 등록
        ContractorContact.objects.create(
            contractor=contractor,
            cell_phone=data.get('cell_phone', ''),
            home_phone=data.get('home_phone', ''),
            other_phone=data.get('other_phone', ''),
            email=data.get('email', '')
        )

        # 계약자 주소 등록 (계약인 경우에만)
        if contractor.status == '2' and ContractorRegistrationService._has_address_data(data):
            ContractorAddress.objects.create(
                contractor=contractor,
                id_zipcode=data.get('id_zipcode', ''),
                id_address1=data.get('id_address1', ''),
                id_address2=data.get('id_address2', ''),
                id_address3=data.get('id_address3', ''),
                dm_zipcode=data.get('dm_zipcode', ''),
                dm_address1=data.get('dm_address1', ''),
                dm_address2=data.get('dm_address2', ''),
                dm_address3=data.get('dm_address3', '')
            )

        raw_rrn = str(data.get('rrn') or '').strip()
        if contractor.status == '2' and raw_rrn:
            ContractorSensitiveService.upsert_rrn(
                contractor=contractor,
                raw_rrn=raw_rrn,
                legal_basis=str(data.get('rrn_legal_basis') or '1'),
                actor=user,
                purpose='계약 등록 시 식별정보 등록',
                ip_address=ip_address,
            )

        return contractor

    @staticmethod
    @transaction.atomic  # [H-2] Contractor/Contact/Address 복합 수정을 원자적 트랜잭션으로 보호
    def update_contractor(contractor, data, user=None, ip_address=None):
        """
        기존 계약자 정보 수정

        Args:
            contractor: Contractor 인스턴스
            data: 수정할 계약자 정보 딕셔너리
        """

        # 계약자 기본 정보 수정
        if data.get('name') is not None:
            contractor.name = data.get('name')
        if data.get('gender') is not None:
            contractor.gender = data.get('gender')
        if contractor.contract and contractor.contract.order_group and contractor.contract.order_group.sort == '2':
            contractor.qualification = '1'
        else:
            contractor.qualification = data.get('qualification') or contractor.qualification or '2'
        contractor.status = data.get('status') or contractor.status or '1'  # 프론트에서 'status' 키로 전송
        if 'change_type' in data:
            contractor.change_type = data.get('change_type') or None
        if 'note' in data:
            contractor.note = data.get('note') or ''

        # 날짜 필드 처리 - 빈 문자열은 None으로, 값이 있으면 업데이트
        birth_date_value = clean_date_value(data.get('birth_date'))
        if birth_date_value is not None:
            contractor.birth_date = birth_date_value

        reservation_date_value = clean_date_value(data.get('reservation_date'))
        if reservation_date_value is not None:
            contractor.reservation_date = reservation_date_value

        contract_date_value = clean_date_value(data.get('contract_date'))
        if contract_date_value is not None:
            contractor.contract_date = contract_date_value

        contractor.save()

        if contractor.status == '4':
            ContractorSensitiveService.schedule_retention(contractor)
        elif contractor.status == '2':
            ContractorSensitiveService.clear_retention(contractor)

        # 연락처 정보 수정 (없으면 생성)
        contact, _ = ContractorContact.objects.get_or_create(contractor=contractor)
        contact.cell_phone = data.get('cell_phone', '')
        contact.home_phone = data.get('home_phone', '')
        contact.other_phone = data.get('other_phone', '')
        contact.email = data.get('email', '')
        contact.save()

        # 주소 정보 처리 (다중 주소 이력 보유 시 MultipleObjectsReturned 방지 및 현주소 갱신)
        if contractor.status == '2' and ContractorRegistrationService._has_address_data(data):
            curr_addr = (
                ContractorAddress.objects.filter(contractor=contractor, is_current=True).first()
                or ContractorAddress.objects.filter(contractor=contractor).order_by('-id').first()
            )
            if curr_addr:
                curr_addr.id_zipcode = data.get('id_zipcode', curr_addr.id_zipcode)
                curr_addr.id_address1 = data.get('id_address1', curr_addr.id_address1)
                curr_addr.id_address2 = data.get('id_address2', curr_addr.id_address2)
                curr_addr.id_address3 = data.get('id_address3', curr_addr.id_address3)
                curr_addr.dm_zipcode = data.get('dm_zipcode', curr_addr.dm_zipcode)
                curr_addr.dm_address1 = data.get('dm_address1', curr_addr.dm_address1)
                curr_addr.dm_address2 = data.get('dm_address2', curr_addr.dm_address2)
                curr_addr.dm_address3 = data.get('dm_address3', curr_addr.dm_address3)
                curr_addr.save()
            else:
                ContractorAddress.objects.create(
                    contractor=contractor,
                    id_zipcode=data.get('id_zipcode', ''),
                    id_address1=data.get('id_address1', ''),
                    id_address2=data.get('id_address2', ''),
                    id_address3=data.get('id_address3', ''),
                    dm_zipcode=data.get('dm_zipcode', ''),
                    dm_address1=data.get('dm_address1', ''),
                    dm_address2=data.get('dm_address2', ''),
                    dm_address3=data.get('dm_address3', '')
                )

        raw_rrn = str(data.get('rrn') or '').strip()
        if contractor.status == '2' and raw_rrn:
            ContractorSensitiveService.upsert_rrn(
                contractor=contractor,
                raw_rrn=raw_rrn,
                legal_basis=str(data.get('rrn_legal_basis') or '1'),
                actor=user,
                purpose='계약 정보 수정 시 식별정보 등록/갱신',
                ip_address=ip_address,
            )

    @staticmethod
    def _has_address_data(data):
        """주소 정보가 있는지 확인"""
        address_fields = [
            'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
            'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3'
        ]
        return any(data.get(field) for field in address_fields)


class FileManagementService:
    """계약 파일 관리 서비스"""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    @classmethod
    def _validate_file_size(cls, file):
        if file and getattr(file, 'size', 0) > cls.MAX_FILE_SIZE:
            raise serializers.ValidationError({'file': '첨부파일 크기는 최대 50MB를 초과할 수 없습니다.'})

    @staticmethod
    def handle_new_file(contractor, file, user):
        """새 파일 업로드 처리"""
        if file:
            FileManagementService._validate_file_size(file)
            ContractFile.objects.create(
                contractor=contractor,
                file=file,
                creator=user
            )

    @staticmethod
    def handle_file_operations(data, contractor, user):
        """파일 수정/삭제/생성 일괄 처리"""

        # 새 파일 업로드
        new_file = data.get('newFile')
        if new_file:
            FileManagementService.handle_new_file(contractor, new_file, user)

        # 파일 수정
        edit_file_pk = data.get('editFile')
        change_file = data.get('cngFile')
        if edit_file_pk and change_file:
            FileManagementService._validate_file_size(change_file)
            try:
                file_to_edit = ContractFile.objects.get(pk=edit_file_pk, contractor=contractor)
                old_storage = file_to_edit.file.storage if file_to_edit.file else None
                old_name = file_to_edit.file.name if file_to_edit.file else None
                file_to_edit.file = change_file
                file_to_edit.save()
                if old_storage and old_name and old_name != file_to_edit.file.name:
                    transaction.on_commit(lambda s=old_storage, n=old_name: s.delete(n))
            except ContractFile.DoesNotExist:
                raise serializers.ValidationError({'editFile': f'수정할 계약서 파일(ID: {edit_file_pk})을 찾을 수 없습니다.'})
            except Exception as e:
                logger.error('Error while replacing file (pk=%s): %s', edit_file_pk, e)
                raise serializers.ValidationError({'editFile': '계약서 파일 교체 중 오류가 발생했습니다.'})

        # 파일 삭제
        del_file_pk = data.get('delFile')
        if del_file_pk:
            try:
                file_to_delete = ContractFile.objects.get(pk=del_file_pk, contractor=contractor)
                file_to_delete.delete()
            except ContractFile.DoesNotExist:
                raise serializers.ValidationError({'delFile': f'삭제할 계약서 파일(ID: {del_file_pk})을 찾을 수 없습니다.'})


class PaymentProcessingService:
    """
    계약 관련 납부 처리 서비스

    ProjectCompositeTransactionSerializer 패턴 기반으로 리팩토링:
    - ProjectBankTransaction 생성 (은행 거래)
    - ProjectAccountingEntry 생성 (회계 분개)
    - ContractPayment는 ProjectAccountingEntry.save()에서 자동 생성
    """

    @staticmethod
    @transaction.atomic
    def process_initial_payment(contract, contractor, data, user):
        """
        초기 계약금 납부 처리

        Args:
            contract: Contract 인스턴스
            contractor: Contractor 인스턴스
            data: 납부 정보 딕셔너리
                - deal_date: 거래일
                - amount: 입금액
                - project: 프로젝트 PK
                - order_group_sort: 차수 sort (1 또는 2)
                - installment_order: 납부회차 PK
                - bank_account: 은행계좌 PK
                - trader: 거래처 (선택)
                - serial_number: 계약번호
            user: request.user
        """
        if not data.get('deal_date'):
            return

        # 기본 정보 조회
        project_id = clean_id_value(data.get('project')) or getattr(contract, 'project_id', None)
        project = Project.objects.filter(pk=project_id).first() if project_id else getattr(contract, 'project', None)
        if not project:
            raise serializers.ValidationError({'project': '유효한 프로젝트 정보가 필요합니다.'})

        raw_sort = data.get('order_group_sort') or getattr(getattr(contract, 'order_group', None), 'sort', None) or '1'
        try:
            order_group_sort = int(raw_sort)
        except (TypeError, ValueError):
            order_group_sort = 1

        # is_payment=True인 계정 선택 (order_group_sort 에 따라 출자금 / 매출금=분양대금)
        category = ('equity', 'revenue')
        target_category = category[0] if order_group_sort == 1 else category[1]
        payment_accounts = ProjectAccount.objects.filter(is_payment=True)
        account = payment_accounts.filter(category=target_category).first()
        if not account and payment_accounts.exists():
            account = payment_accounts.first() if order_group_sort == 1 else payment_accounts.last()
        if not account:
            raise serializers.ValidationError({'account': '수납 처리용 프로젝트 회계 계정(is_payment=True)이 설정되어 있지 않습니다.'})

        # 납부 정보 (해당 프로젝트 소속 계좌인지 함께 검증)
        bank_acc_id = clean_id_value(data.get('bank_account'))
        bank_account = (
            ProjectBankAccount.objects.filter(pk=bank_acc_id, project=project).first()
            if bank_acc_id else None
        )
        if not bank_account:
            raise serializers.ValidationError({'bank_account': '해당 프로젝트의 유효한 입금 계좌를 선택해 주십시오.'})

        # deal_date 유효성 검사 및 조정 (미래 날짜 방지)
        deal_date_input = data.get('deal_date')
        if deal_date_input:
            # 문자열 날짜를 date 객체로 변환
            if isinstance(deal_date_input, str):
                try:
                    deal_date_obj = date.fromisoformat(deal_date_input)
                except ValueError as exc:
                    raise serializers.ValidationError({'deal_date': '유효한 거래일자(YYYY-MM-DD) 형식이 아닙니다.'}) from exc
            else:
                deal_date_obj = deal_date_input

            # 현재 로컬 날짜와 비교
            today_local = timezone.localdate()
            if deal_date_obj > today_local:
                adjusted_deal_date = today_local.isoformat()  # ISO 8601 형식 문자열로 변환
            else:
                adjusted_deal_date = deal_date_input
        else:
            adjusted_deal_date = None

        # 1. ProjectCompositeTransactionSerializer가 요구하는 validated_data 형식 구성
        composite_data = {
            'project': project.pk,
            'bank_account': bank_account.pk,
            'deal_date': adjusted_deal_date,
            'amount': data.get('amount'),
            'sort': 1,  # 입금 (sort_id=1)
            'content': f'{contractor.name}[{data.get("serial_number")}] 대금납부',
            'note': '',
            'accounting_entries': [
                {
                    'account': account.pk,
                    'amount': data.get('amount'),
                    'trader': data.get('trader', ''),
                    'evidence_type': None,  # 입금은 지출증빙 불필요
                    'contract': contract.pk,
                    'installment_order': data.get('installment_order'),
                }
            ]
        }

        # 2. ProjectCompositeTransactionSerializer를 사용하여 거래 생성
        serializer = ProjectCompositeTransactionSerializer(data=composite_data)
        serializer.is_valid(raise_exception=True)
        serializer.create(serializer.validated_data, creator=user)

    @staticmethod
    @transaction.atomic
    def process_payment_update(contract, data, user):
        """
        기존 납부 정보 수정 또는 새 납부 생성

        Args:
            contract: Contract 인스턴스
            data: 납부 정보 딕셔너리
                - payment: ContractPayment PK (기존 납부 수정 시)
                - 기타 필드는 process_initial_payment와 동일
        """
        if not data.get('deal_date'):
            return

        payment_id = clean_id_value(data.get('payment'))

        contractor = Contractor.objects.using('default').get(contract=contract)

        if payment_id:
            if ContractPayment.objects.filter(pk=payment_id).exclude(contract=contract).exists():
                raise serializers.ValidationError({'payment': '다른 계약의 납부 내역은 수정할 수 없습니다.'})

            # 기존 납부 수정
            try:
                # ContractPayment를 통해 ProjectAccountingEntry 찾기
                contract_payment = ContractPayment.objects.get(pk=payment_id, contract=contract)
                accounting_entry = contract_payment.accounting_entry
                bank_tx = accounting_entry.related_transaction

                # 기본 정보 조회
                order_group_sort = int(data.get('order_group_sort') or contract.order_group.sort)

                # 계정 선택 (order_group_sort 에 따라 출자금 / 매출금=분양대금)
                category = ('equity', 'revenue')
                target_category = category[0] if order_group_sort == 1 else category[1]
                payment_accounts = ProjectAccount.objects.filter(is_payment=True)
                account = payment_accounts.filter(category=target_category).first()
                if not account and payment_accounts.exists():
                    account = payment_accounts.first() if order_group_sort == 1 else payment_accounts.last()
                if not account:
                    raise serializers.ValidationError({'account': '수납 처리용 프로젝트 회계 계정(is_payment=True)이 설정되어 있지 않습니다.'})

                # 납부 정보 (해당 계약의 프로젝트 소속 회차·계좌인지 함께 검증)
                inst_id = clean_id_value(data.get('installment_order'))
                installment_order = (
                    InstallmentPaymentOrder.objects.filter(pk=inst_id, project=contract.project).first()
                    if inst_id else None
                )
                if not installment_order:
                    raise serializers.ValidationError({'installment_order': '해당 프로젝트의 유효한 납부 회차를 선택해 주십시오.'})

                bank_acc_id = clean_id_value(data.get('bank_account'))
                bank_account = (
                    ProjectBankAccount.objects.filter(pk=bank_acc_id, project=contract.project).first()
                    if bank_acc_id else None
                )
                if not bank_account:
                    raise serializers.ValidationError({'bank_account': '해당 프로젝트의 유효한 입금 계좌를 선택해 주십시오.'})

                # 은행 거래 업데이트
                bank_tx.bank_account = bank_account
                bank_tx.amount = data.get('amount')
                bank_tx.deal_date = data.get('deal_date')
                bank_tx.content = f'{contractor.name}[{data.get("serial_number")}] 대금납부'
                bank_tx.save()

                # 회계 분개 업데이트 (save()에서 ContractPayment 자동 업데이트)
                accounting_entry.account = account
                accounting_entry.amount = data.get('amount')
                accounting_entry.trader = data.get('trader', '')
                accounting_entry.installment_order = installment_order
                accounting_entry.save()

            except ContractPayment.DoesNotExist:
                # payment_id가 잘못되었거나 삭제된 경우 - 새로 생성
                PaymentProcessingService.process_initial_payment(contract, contractor, data, user)
        else:
            # 새 납부 생성
            PaymentProcessingService.process_initial_payment(contract, contractor, data, user)


# 메인 Contract 관리 서비스
class ContractCreationService:
    """계약 생성 전체 프로세스 관리 서비스"""

    def __init__(self):
        self.unit_service = UnitAssignmentService()
        self.price_service = ContractPriceUpdateService()
        self.contractor_service = ContractorRegistrationService()
        self.file_service = FileManagementService()
        self.payment_service = PaymentProcessingService()

    @transaction.atomic
    def create_contract(self, data, user):
        """
        계약 전체 생성 프로세스 실행

        Args:
            data: 계약 생성 데이터 딕셔너리
            user: 요청 사용자

        Returns:
            Contract 인스턴스
        """
        # 1. 기본 계약 생성
        contract = self._create_base_contract(data)

        # 2. 유닛 할당
        self.unit_service.assign_unit(
            contract,
            clean_id_value(data.get('key_unit')),
            clean_id_value(data.get('houseunit'))
        )

        # 3. 계약 가격 설정 (unit_type이 없는 청약은 가격 로직 스킵)
        if contract.unit_type_id:
            self.price_service.update_single_contract_price(contract)

        # 4. 계약자 등록
        contractor = self.contractor_service.register_contractor(contract, data, user=user)

        # 5. 파일 처리
        self.file_service.handle_new_file(contractor, data.get('newFile'), user)

        # 6. 초기 납부 처리
        self.payment_service.process_initial_payment(contract, contractor, data, user)

        bump_payment_summary_cache_version(contract.project_id)

        return contract

    @staticmethod
    def _create_base_contract(data):
        """기본 계약 객체 생성"""
        # Convert string 'true'/'false' to boolean
        is_active_value = data.get('is_active', True)
        if isinstance(is_active_value, str):
            is_active_value = is_active_value.lower() == 'true'

        # Convert string 'true'/'false' to boolean for is_sup_cont
        is_sup_cont_value = data.get('is_sup_cont', False)
        if isinstance(is_sup_cont_value, str):
            is_sup_cont_value = is_sup_cont_value.lower() == 'true'

        # Convert string to date for sup_cont_date
        sup_cont_date_value = clean_date_value(data.get('sup_cont_date'))
        if isinstance(sup_cont_date_value, str) and sup_cont_date_value:
            try:
                sup_cont_date_value = datetime.strptime(sup_cont_date_value, '%Y-%m-%d').date()
            except ValueError:
                sup_cont_date_value = None

        # Handle case where serial_number might be empty or missing
        serial_number = data.get('serial_number')
        if not serial_number or serial_number.startswith('TEMP-'):
            # Generate a temporary serial number if none provided or temporary format
            project_id = clean_id_value(data.get('project'))
            order_group_id = clean_id_value(data.get('order_group'))
            short_id = uuid.uuid4().hex[:6]
            serial_number = f'TEMP-{project_id}-{order_group_id}-{short_id}'

        # Handle case where unit_type might be empty string from FormData
        unit_type_id = clean_id_value(data.get('unit_type'))

        if serial_number and not serial_number.startswith('TEMP-'):
            if Contract.objects.filter(serial_number=serial_number).exists():
                raise serializers.ValidationError({
                    'serial_number': f'이미 등록된 계약 일련번호({serial_number})입니다. 유닛 또는 차수 정보를 확인해 주세요.'
                })

        try:
            return Contract.objects.create(
                project_id=clean_id_value(data.get('project')),
                serial_number=serial_number,
                order_group_id=clean_id_value(data.get('order_group')),
                unit_type_id=unit_type_id,
                is_active=is_active_value,
                is_sup_cont=is_sup_cont_value,
                sup_cont_date=sup_cont_date_value
            )
        except IntegrityError as e:
            if 'serial_number' in str(e):
                raise serializers.ValidationError({
                    'serial_number': f'이미 등록된 계약 일련번호({serial_number})입니다. 유닛 또는 차수 정보를 확인해 주세요.'
                })
            raise


class ContractUpdateService:
    """계약 수정 전체 프로세스 관리 서비스"""

    def __init__(self):
        self.unit_service = UnitAssignmentService()
        self.price_service = ContractPriceUpdateService()
        self.contractor_service = ContractorRegistrationService()
        self.file_service = FileManagementService()
        self.payment_service = PaymentProcessingService()

    @transaction.atomic
    def update_contract(self, instance, data, user):
        """
        계약 전체 수정 프로세스 실행

        Args:
            instance: 수정할 Contract 인스턴스
            data: 수정 데이터 딕셔너리
            user: 요청 사용자

        Returns:
            Contract 인스턴스
        """
        # 1. 기본 계약 정보 업데이트
        instance.order_group_id = clean_id_value(data.get('order_group')) or instance.order_group_id
        instance.unit_type_id = clean_id_value(data.get('unit_type'))

        # serial_number 동기화 (유닛 변경 등에 따른 일련번호 갱신)
        new_serial_number = data.get('serial_number')
        if new_serial_number and new_serial_number != instance.serial_number and not new_serial_number.startswith(
                'TEMP-'):
            if Contract.objects.filter(serial_number=new_serial_number).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({
                    'serial_number': f'이미 등록된 계약 일련번호({new_serial_number})입니다. 유닛 또는 차수 정보를 확인해 주세요.'
                })
            instance.serial_number = new_serial_number

        # unit_type 일관성 검증: key_unit이 변경되지 않는 경우 기존 key_unit과 비교
        new_unit_pk = clean_id_value(data.get('key_unit'))
        current_unit_pk = instance.key_unit_id

        # 유닛이 변경되지 않고(유지되고), 유닛이 존재하며, 타입이 지정된 경우에만 검증
        if new_unit_pk == current_unit_pk and current_unit_pk and instance.unit_type_id:
            if instance.key_unit.unit_type_id != instance.unit_type_id:
                raise serializers.ValidationError(
                    '계약의 타입과 유닛의 타입이 일치하지 않습니다.'
                )

        # is_sup_cont와 sup_cont_date 필드 처리
        if 'is_sup_cont' in data:
            is_sup_cont_value = data.get('is_sup_cont')
            if isinstance(is_sup_cont_value, str):
                is_sup_cont_value = is_sup_cont_value.lower() == 'true'
            instance.is_sup_cont = is_sup_cont_value

        if 'sup_cont_date' in data:
            sup_cont_date_value = clean_date_value(data.get('sup_cont_date'))
            if isinstance(sup_cont_date_value, str) and sup_cont_date_value:
                try:
                    sup_cont_date_value = datetime.strptime(sup_cont_date_value, '%Y-%m-%d').date()
                except ValueError:
                    sup_cont_date_value = None
            instance.sup_cont_date = sup_cont_date_value

        instance.updator = user
        instance.save()

        # 2. 유닛 재할당 (필요한 경우)
        # new_unit_pk / current_unit_pk 는 Step 1에서 이미 계산된 값 재사용
        house_unit_pk = clean_id_value(data.get('houseunit'))

        if current_unit_pk != new_unit_pk:
            if new_unit_pk:  # 새 유닛이 있는 경우에만 재할당
                self.unit_service.reassign_unit(
                    instance,
                    new_unit_pk,
                    house_unit_pk
                )
            elif current_unit_pk:  # 기존 유닛을 제거하는 경우
                # 기존 연결 해제만 수행
                if instance.key_unit:
                    try:
                        old_house_unit = instance.key_unit.houseunit
                        if old_house_unit:
                            old_house_unit.key_unit = None
                            old_house_unit.save()
                    except ObjectDoesNotExist:
                        pass
                instance.key_unit = None
                instance.save()
        elif house_unit_pk and new_unit_pk:
            # 유닛은 같지만 동호수만 변경된 경우
            try:
                current_house_unit = instance.key_unit.houseunit
                if not current_house_unit or current_house_unit.pk != house_unit_pk:
                    self.unit_service.reassign_unit(
                        instance,
                        new_unit_pk,
                        house_unit_pk
                    )
            except ObjectDoesNotExist:
                self.unit_service.reassign_unit(
                    instance,
                    new_unit_pk,
                    house_unit_pk
                )

        # 3. 계약 가격 재계산 (unit_type이 없는 청약은 가격 로직 스킵)
        if instance.unit_type_id:
            self.price_service.update_single_contract_price(instance)

        # 4. 계약자 정보 수정
        contractor = instance.contractor
        self.contractor_service.update_contractor(contractor, data, user=user)

        # 5. 파일 관리
        self.file_service.handle_file_operations(data, contractor, user)

        # 6. 납부 정보 처리
        self.payment_service.process_payment_update(instance, data, user)

        bump_payment_summary_cache_version(instance.project_id)

        return instance


class ContractorReleaseService:
    """
    계약자 해지 처리 서비스

    계약자 해지 시 필요한 모든 비즈니스 로직을 처리합니다:
    - 계약 상태 변경 및 비활성화
    - 동호수/키유닛 연결 해제
    - 계약가격 미계약 상태로 전환
    - 납부분담금 환불 처리
    - 계약자 정보 해지 상태로 변경
    """

    @staticmethod
    @transaction.atomic
    def process_release_completion(contractor_release, completion_date):
        """
        계약자 해지 최종 완결 처리

        Args:
            contractor_release: ContractorRelease 인스턴스
            completion_date: 해지 완료 일자

        Returns:
            dict: 처리 결과 정보
        """
        contractor = contractor_release.contractor
        contract = contractor.contract
        if not contract:
            raise serializers.ValidationError({'contractor': '해지 처리할 활성 계약 정보가 존재하지 않습니다.'})

        result = {
            'contract_updated': False,
            'unit_detached': False,
            'price_reset': False,
            'payments_refunded': 0,
            'contractor_updated': False,
        }

        # 1. 계약 상태 변경 (max_length=30 초과 방지 및 고유성 보장)
        date_str = str(completion_date).replace('-', '')[-6:] if completion_date else timezone.now().strftime('%y%m%d')
        suffix = f"-T{date_str}"
        base_sn = contract.serial_number[:(30 - len(suffix))]
        new_sn = f"{base_sn}{suffix}"
        if Contract.objects.filter(serial_number=new_sn).exclude(pk=contract.pk).exists():
            short_uid = uuid.uuid4().hex[:4]
            suffix = f"-T{date_str}-{short_uid}"
            base_sn = contract.serial_number[:(30 - len(suffix))]
            new_sn = f"{base_sn}{suffix}"
        contract.serial_number = new_sn
        contract.is_active = False
        result['contract_updated'] = True

        # 2. 동호수 연결 해제
        unit = ContractorReleaseService._detach_house_unit(contract)
        if unit:
            result['unit_detached'] = True

        # 3. 키유닛 연결 해제
        contract.key_unit = None
        contract.save()

        # 4. 계약가격 미계약 상태로 전환
        if ContractorReleaseService._reset_contract_price(contract, unit):
            result['price_reset'] = True

        # 5. 납부분담금 환불 처리
        refund_count = ContractorReleaseService._process_payment_refunds(
            contract,
            contractor,
            completion_date
        )
        result['payments_refunded'] = refund_count

        # 6. 계약자 최종 해지 상태로 변경
        ContractorReleaseService._update_contractor_status(contractor, contract, contractor_release)
        result['contractor_updated'] = True

        bump_payment_summary_cache_version(contract.project_id)

        return result

    @staticmethod
    def _detach_house_unit(contract):
        """동호수 연결 해제"""
        try:
            unit = contract.key_unit.houseunit
            unit.key_unit = None
            unit.save()
            return unit
        except (ObjectDoesNotExist, AttributeError):
            return None

    @staticmethod
    def _reset_contract_price(contract, unit):
        """계약가격 미계약 상태로 전환"""
        try:
            contract_price = contract.contractprice
            contract_price.contract = None

            # 미계약용 기본 차수가 설정된 경우 SalesPriceByGT 기준 가격으로 업데이트
            default_order_group = OrderGroup.get_default_for_project(contract.project)

            if unit and default_order_group:
                sales_price = ContractorReleaseService._get_sales_price_for_uncontracted(
                    contract.project,
                    default_order_group,
                    unit
                )

                if sales_price:
                    contract_price.price = sales_price.price
                    contract_price.price_build = sales_price.price_build
                    contract_price.price_land = sales_price.price_land
                    contract_price.price_tax = sales_price.price_tax

            contract_price.save()
            return True

        except ContractPrice.DoesNotExist:
            return False

    @staticmethod
    def _get_sales_price_for_uncontracted(project, order_group, unit):
        """미계약 세대의 기준 가격 조회"""

        # 임시 계약 객체 생성 (미계약용 기본 차수와 프로젝트 정보로)
        class TempContract:
            def __init__(self, proj, ord_grp, u_type):
                self.project = proj
                self.order_group = ord_grp
                self.unit_type = u_type

        temp_contract = TempContract(project, order_group, unit.unit_type)
        return get_sales_price_by_gt(temp_contract, unit)

    @staticmethod
    def _process_payment_refunds(contract, contractor, completion_date):
        """납부분담금 환불 처리"""
        payments = list(ContractPayment.objects.filter(contract=contract).select_related(
            'accounting_entry__account'
        ))

        refund_count = 0
        for payment in payments:
            entry = payment.accounting_entry

            # 회계 분개에서 계약정보는 삭제하고 계약자 정보는 남겨둠
            entry.contract = None
            entry.contractor = contractor

            # 회계 분개의 계정을 환불 계정으로 변경
            if ContractorReleaseService._change_to_refund_account(entry):
                refund_count += 1
            else:
                # 계정 변경이 이루어지지 않은 경우에도 entry 객체의 변경사항을 저장
                entry.save()

            # 은행 거래 note에 환불 정보 추가
            if completion_date:
                ContractorReleaseService._add_refund_note_to_bank_transaction(
                    entry,
                    contract,
                    contractor,
                    completion_date
                )

        return refund_count

    @staticmethod
    def _change_to_refund_account(accounting_entry):
        """
        회계 분개의 계정을 환불 계정으로 변경

        우선순위:
        1. 같은 parent 하위의 입금(deposit) + 계약자 관련 + 해지자 계정
        2. 같은 parent 하위의 입금(deposit) + 계약자 관련 계정
        3. 동일 category의 계약자 관련 + 해지자 계정
        """
        # 1순위: 같은 parent 하위의 입금 + 해지자 계정 찾기
        refund_account = ProjectAccount.objects.filter(
            parent=accounting_entry.account.parent,
            direction='deposit',
            is_related_contractor=True,
            name__contains='해지자'
        ).first()

        # 2순위: 같은 parent 하위의 입금 + 계약자 관련 계정
        if not refund_account:
            refund_account = ProjectAccount.objects.filter(
                parent=accounting_entry.account.parent,
                direction='deposit',
                is_related_contractor=True
            ).first()

        # 3순위: 동일 카테고리의 해지자 계정
        if not refund_account:
            refund_account = ProjectAccount.objects.filter(
                category=accounting_entry.account.category,
                direction='deposit',
                is_related_contractor=True,
                name__contains='해지자'
            ).first()

        if not refund_account:
            return False

        # 환불 계정 적용
        accounting_entry.account = refund_account
        accounting_entry.save()
        return True

    @staticmethod
    def _add_refund_note_to_bank_transaction(entry, contract, contractor, completion_date):
        """은행 거래 note에 환불 정보 추가"""
        bank_tx = entry.related_transaction
        if bank_tx:
            msg = f'환불 계약 건 - {contract.serial_number[:13]} ({completion_date} {contractor.name} 환불완료)'
            append_note = ', ' + msg if bank_tx.note else msg
            bank_tx.note = bank_tx.note + append_note
            bank_tx.save()

    @staticmethod
    def _update_contractor_status(contractor, contract, contractor_release):
        """계약자 최종 해지 상태로 변경"""
        contractor.prev_contract = contract
        contractor.contract = None

        if contractor.qualification == '3':
            contractor.qualification = '2'  # 인가 등록 취소

        contractor.is_active = False  # 비활성 상태로 변경
        contractor.status = '4'  # 계약종결로 변경
        contractor.change_type = contractor_release.release_type  # ContractorRelease의 해지유형으로 대입
        contractor.save()

        # 해지 확정 시 법정 보존기간(기본 5년) 후 자동 파기되도록 보존 만료일 설정
        ContractorSensitiveService.schedule_retention(
            contractor,
            base_date=contractor_release.completion_date or contractor_release.refund_completion_date,
        )
