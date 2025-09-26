"""
Contract 관련 비즈니스 로직 서비스
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from _utils.contract_price import get_contract_price
from contract.models import Contract, ContractPrice, OrderGroup
from items.models import HouseUnit
from payment.models import SalesPriceByGT


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
        contracts = Contract.objects.filter(
            project=self.project,
            activation=True
        )

        updated_contracts = []
        created_count = 0
        updated_count = 0
        errors = []

        # Phase 1: 계약이 있는 ContractPrice 업데이트
        for contract in contracts:
            try:
                # 동호수 지정 여부 확인
                try:
                    house_unit = contract.key_unit.houseunit
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

            if house_unit:
                existing.house_unit = house_unit

            existing.save()  # order_group은 변경되지 않음 (save 메서드에서 생성시에만 설정)
            return existing, False

        except ContractPrice.DoesNotExist:
            # 생성: 모든 필드 포함하여 새로 생성
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
            activation=True
        ).select_related('unit_type', 'order_group', 'contractor')

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
            key_unit__contract__activation=True  # 활성화된 계약만 제외
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
                # 기타 오류 발생시 건너뜀 (운영시에는 적절한 로깅 필요)
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
            house_unit = contract.key_unit.houseunit
        except ObjectDoesNotExist:
            house_unit = None

        price = get_contract_price(contract, house_unit, True)  # is_set=True for consistency

        try:
            # 기존 ContractPrice 조회
            existing = ContractPrice.objects.get(contract=contract)

            # 수정: 가격 정보만 업데이트, order_group은 유지
            existing.price = price[0]
            existing.price_build = price[1]
            existing.price_land = price[2]
            existing.price_tax = price[3]

            if house_unit:
                existing.house_unit = house_unit

            existing.save()  # order_group은 변경되지 않음
            return existing, False

        except ContractPrice.DoesNotExist:
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
