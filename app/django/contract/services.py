"""
Contract 관련 비즈니스 로직 서비스
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from _utils.contract_price import get_contract_price
from contract.models import Contract, ContractPrice


class ContractPriceBulkUpdateService:
    """
    SalesPriceByGT 변경 시 프로젝트 내 모든 계약 가격 일괄 업데이트 서비스

    주요 용도:
    - 분양가격표(SalesPriceByGT) 변경 후 기존 계약들에 새 가격 정책 반영
    - 프로젝트 전체 계약의 ContractPrice 일괄 업데이트
    """

    def __init__(self, project):
        self.project = project

    @transaction.atomic
    def update_all_contract_prices(self):
        """
        프로젝트 내 모든 유효 계약의 가격 정보 업데이트

        Returns:
            dict: 업데이트 결과 정보
                - updated_count: 업데이트된 계약 수
                - created_count: 새로 생성된 ContractPrice 수
                - updated_contracts: 업데이트된 계약 ID 목록
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

        for contract in contracts:
            try:
                # 동호수 지정 여부 확인
                try:
                    house_unit = contract.key_unit.houseunit
                except ObjectDoesNotExist:
                    house_unit = None

                # 1. 기준 공급가, 2. 수입 예산 평균가, 3. 타입 평균가 순 참조 공급가 가져오기
                price = get_contract_price(contract, house_unit, True)

                # ContractPrice 업데이트/생성
                cont_price, created = self._update_or_create_contract_price(contract, price)

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

        return {
            'total_processed': len(contracts),
            'updated_count': updated_count,
            'created_count': created_count,
            'updated_contracts': updated_contracts,
            'errors': errors
        }

    @staticmethod
    def _update_or_create_contract_price(contract, price):
        """
        개별 계약의 ContractPrice 업데이트 또는 생성

        Args:
            contract: Contract 인스턴스
            price: 가격 정보 튜플 (price, price_build, price_land, price_tax)

        Returns:
            tuple: (ContractPrice 인스턴스, created 여부)
        """
        cont_price, created = ContractPrice.objects.update_or_create(
            contract=contract,
            defaults={
                'price': price[0],
                'price_build': price[1],
                'price_land': price[2],
                'price_tax': price[3],
                # 납부 금액들은 property로 계산되므로 임시값으로 설정
                'down_pay': 0,
                'biz_agency_fee': 0,
                'is_included_baf': False,
                'middle_pay': 0,
                'remain_pay': 0
            }
        )
        return cont_price, created

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


class ContractPriceUpdateService:
    """
    개별 계약 가격 업데이트 서비스
    """

    @staticmethod
    def update_single_contract_price(contract):
        """
        단일 계약의 가격 정보 업데이트

        Args:
            contract: Contract 인스턴스

        Returns:
            tuple: (ContractPrice 인스턴스, created 여부)
        """
        try:
            house_unit = contract.key_unit.houseunit
        except ObjectDoesNotExist:
            house_unit = None

        price = get_contract_price(contract, house_unit)

        cont_price, created = ContractPrice.objects.update_or_create(
            contract=contract,
            defaults={
                'price': price[0],
                'price_build': price[1],
                'price_land': price[2],
                'price_tax': price[3],
                'down_pay': 0,
                'biz_agency_fee': 0,
                'is_included_baf': False,
                'middle_pay': 0,
                'remain_pay': 0
            }
        )
        return cont_price, created
