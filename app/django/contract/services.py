"""
Contract 관련 비즈니스 로직 서비스
"""
import os

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from _utils.contract_price import get_contract_price, get_sales_price_by_gt
from contract.models import (Contract, ContractPrice, OrderGroup, ContractFile,
                             Contractor, ContractorAddress, ContractorContact)
from items.models import KeyUnit, HouseUnit
from ledger.models import ProjectAccount, ProjectBankAccount, ProjectBankTransaction, ProjectAccountingEntry
from payment.models import InstallmentPaymentOrder, SalesPriceByGT, ContractPayment
from project.models import Project


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


# 새로운 Contract 관리 서비스들
class UnitAssignmentService:
    """유닛 할당/재할당 관리 서비스"""

    @staticmethod
    def assign_unit(contract, unit_pk, house_unit_pk=None):
        """
        계약에 유닛 할당

        Args:
            contract: Contract 인스턴스
            unit_pk: KeyUnit PK
            house_unit_pk: HouseUnit PK (선택사항)

        Returns:
            HouseUnit 인스턴스 또는 None
        """

        key_unit = KeyUnit.objects.get(pk=unit_pk)
        contract.key_unit = key_unit
        contract.save()

        if house_unit_pk:
            house_unit = HouseUnit.objects.get(pk=house_unit_pk)
            house_unit.key_unit = key_unit
            house_unit.save()
            return house_unit
        return None

    @staticmethod
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

        # 기존 연결 해제
        if contract.key_unit:
            try:
                old_house_unit = contract.key_unit.houseunit
                if old_house_unit and (not new_house_unit_pk or old_house_unit.pk != new_house_unit_pk):
                    old_house_unit.key_unit = None
                    old_house_unit.save()
            except ObjectDoesNotExist:
                pass

        # 새 연결 설정
        new_key_unit = KeyUnit.objects.get(pk=new_unit_pk)
        contract.key_unit = new_key_unit
        contract.save()

        if new_house_unit_pk:
            new_house_unit = HouseUnit.objects.get(pk=new_house_unit_pk)
            new_house_unit.key_unit = new_key_unit
            new_house_unit.save()

        return {
            'old_house_unit': old_house_unit,
            'new_house_unit': new_house_unit
        }


class ContractorRegistrationService:
    """계약자 등록/수정 관리 서비스"""

    @staticmethod
    def register_contractor(contract, data):
        """
        새 계약자 등록 (계약 생성 시)

        Args:
            contract: Contract 인스턴스
            data: 계약자 정보 딕셔너리

        Returns:
            Contractor 인스턴스
        """

        contractor = Contractor.objects.create(
            contract=contract,
            name=data.get('name'),
            birth_date=data.get('birth_date') or None,
            gender=data.get('gender'),
            qualification=data.get('qualification') or '1',
            status=data.get('status'),
            reservation_date=data.get('reservation_date') or None,
            contract_date=data.get('contract_date') or None,
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

        return contractor

    @staticmethod
    def update_contractor(contractor, data):
        """
        기존 계약자 정보 수정

        Args:
            contractor: Contractor 인스턴스
            data: 수정할 계약자 정보 딕셔너리
        """

        # 계약자 기본 정보 수정
        contractor.name = data.get('name')
        contractor.birth_date = data.get('birth_date') or contractor.birth_date
        contractor.gender = data.get('gender')
        contractor.qualification = data.get('qualification') or '1'
        contractor.status = data.get('status')
        contractor.reservation_date = data.get('reservation_date') or contractor.reservation_date
        contractor.contract_date = data.get('contract_date') or contractor.contract_date
        contractor.note = data.get('note', '')
        contractor.save()

        # 연락처 정보 수정
        contact = ContractorContact.objects.get(contractor=contractor)
        contact.cell_phone = data.get('cell_phone', '')
        contact.home_phone = data.get('home_phone', '')
        contact.other_phone = data.get('other_phone', '')
        contact.email = data.get('email', '')
        contact.save()

        # 주소 정보 처리 (청약→계약 전환 시에만 새로 생성)
        if contractor.status == '2' and ContractorRegistrationService._has_address_data(data):
            try:
                ContractorAddress.objects.get(contractor=contractor)
            except ContractorAddress.DoesNotExist:
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

    @staticmethod
    def handle_new_file(contractor, file, user):
        """새 파일 업로드 처리"""
        if file:
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
            try:
                file_to_edit = ContractFile.objects.get(pk=edit_file_pk)
                old_file_path = file_to_edit.file.path
                if os.path.isfile(old_file_path):
                    os.remove(old_file_path)
                file_to_edit.file = change_file
                file_to_edit.save()
            except ContractFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {edit_file_pk} does not exist.")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error while replacing file: {str(e)}')
                raise serializers.ValidationError('An error occurred while replacing the file.')

        # 파일 삭제
        del_file_pk = data.get('delFile')
        if del_file_pk:
            try:
                file_to_delete = ContractFile.objects.get(pk=del_file_pk)
                file_to_delete.delete()
            except ContractFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {del_file_pk} does not exist.")


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
    def process_initial_payment(contract, data):
        """
        초기 계약금 납부 처리

        Args:
            contract: Contract 인스턴스
            data: 납부 정보 딕셔너리
                - deal_date: 거래일
                - income: 입금액
                - project: 프로젝트 PK
                - order_group_sort: 차수 sort (1 또는 2)
                - installment_order: 납부회차 PK
                - bank_account: 은행계좌 PK
                - trader: 거래처 (선택)
                - serial_number: 계약번호
        """
        if not data.get('deal_date'):
            return

        # 기본 정보 조회
        project = Project.objects.get(pk=data.get('project'))
        contractor = Contractor.objects.get(contract=contract)
        order_group_sort = int(data.get('order_group_sort'))

        # is_payment=True인 계정 선택 (order_group_sort 에 따라 출자금 / 매출금=분양대금)
        index = order_group_sort - 1
        category = ('equity', 'revenue')
        payment_accounts = ProjectAccount.objects.filter(is_payment=True)
        account = payment_accounts.get(category=category[index]) or payment_accounts[index]

        # 납부 정보
        installment_order = InstallmentPaymentOrder.objects.get(pk=data.get('installment_order'))
        bank_account = ProjectBankAccount.objects.get(pk=data.get('bank_account'))

        # 1. 은행 거래 생성 (ProjectCompositeTransactionSerializer 패턴)
        bank_tx = ProjectBankTransaction.objects.create(
            project=project,
            bank_account=bank_account,
            deal_date=data.get('deal_date'),
            amount=data.get('income'),
            sort_id=1,  # 입금
            content=f'{contractor.name}[{data.get("serial_number")}] 대금납부',
            note='',
        )

        # 2. 회계 분개 생성 (ContractPayment는 자동으로 생성됨)
        ProjectAccountingEntry.objects.create(
            transaction_id=bank_tx.transaction_id,
            project=project,
            account=account,
            contract=contract,
            contractor=contractor,
            installment_order=installment_order,
            amount=data.get('income'),
            trader=data.get('trader', ''),
            evidence_type=None,  # 입금은 지출증빙 불필요
        )

    @staticmethod
    @transaction.atomic
    def process_payment_update(contract, data):
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

        payment_id = data.get('payment')

        if payment_id:
            # 기존 납부 수정
            try:
                # ContractPayment를 통해 ProjectAccountingEntry 찾기
                contract_payment = ContractPayment.objects.get(pk=payment_id)
                accounting_entry = contract_payment.accounting_entry
                bank_tx = accounting_entry.related_transaction

                # 기본 정보 조회
                contractor = Contractor.objects.get(contract=contract)
                order_group_sort = int(data.get('order_group_sort'))

                # 계정 선택
                payment_accounts = ProjectAccount.objects.filter(is_payment=True)
                account = payment_accounts.first() if order_group_sort == 1 else payment_accounts.last()

                # 납부 정보
                installment_order = InstallmentPaymentOrder.objects.get(pk=data.get('installment_order'))
                bank_account = ProjectBankAccount.objects.get(pk=data.get('bank_account'))

                # 은행 거래 업데이트
                bank_tx.bank_account = bank_account
                bank_tx.amount = data.get('income')
                bank_tx.deal_date = data.get('deal_date')
                bank_tx.content = f'{contractor.name}[{data.get("serial_number")}] 대금납부'
                bank_tx.save()

                # 회계 분개 업데이트 (save()에서 ContractPayment 자동 업데이트)
                accounting_entry.account = account
                accounting_entry.amount = data.get('income')
                accounting_entry.trader = data.get('trader', '')
                accounting_entry.installment_order = installment_order
                accounting_entry.save()

            except ContractPayment.DoesNotExist:
                # payment_id가 잘못되었거나 삭제된 경우 - 새로 생성
                PaymentProcessingService.process_initial_payment(contract, data)
        else:
            # 새 납부 생성
            PaymentProcessingService.process_initial_payment(contract, data)


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
            data.get('key_unit'),
            data.get('houseunit')
        )

        # 3. 계약 가격 설정
        self.price_service.update_single_contract_price(contract)

        # 4. 계약자 등록
        contractor = self.contractor_service.register_contractor(contract, data)

        # 5. 파일 처리
        self.file_service.handle_new_file(contractor, data.get('newFile'), user)

        # 6. 초기 납부 처리
        self.payment_service.process_initial_payment(contract, data)

        return contract

    @staticmethod
    def _create_base_contract(data):
        """기본 계약 객체 생성"""
        return Contract.objects.create(
            project_id=data.get('project'),
            order_group_id=data.get('order_group'),
            unit_type_id=data.get('unit_type'),
            serial_number=data.get('serial_number'),
            activation=data.get('activation', True)
        )


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
        instance.order_group_id = data.get('order_group', instance.order_group_id)
        instance.unit_type_id = data.get('unit_type', instance.unit_type_id)
        instance.updator = user
        instance.save()

        # 2. 유닛 재할당 (필요한 경우)
        current_unit_pk = instance.key_unit.pk if instance.key_unit else None
        new_unit_pk = data.get('key_unit')

        if current_unit_pk != new_unit_pk:
            self.unit_service.reassign_unit(
                instance,
                new_unit_pk,
                data.get('houseunit')
            )
        elif data.get('houseunit'):
            # 유닛은 같지만 동호수만 변경된 경우
            try:
                current_house_unit = instance.key_unit.houseunit
                if not current_house_unit or current_house_unit.pk != data.get('houseunit'):
                    self.unit_service.reassign_unit(
                        instance,
                        new_unit_pk,
                        data.get('houseunit')
                    )
            except ObjectDoesNotExist:
                self.unit_service.reassign_unit(
                    instance,
                    new_unit_pk,
                    data.get('houseunit')
                )

        # 3. 계약 가격 재계산
        self.price_service.update_single_contract_price(instance)

        # 4. 계약자 정보 수정
        contractor = instance.contractor
        self.contractor_service.update_contractor(contractor, data)

        # 5. 파일 관리
        self.file_service.handle_file_operations(data, contractor, user)

        # 6. 납부 정보 처리
        self.payment_service.process_payment_update(instance, data)

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

        result = {
            'contract_updated': False,
            'unit_detached': False,
            'price_reset': False,
            'payments_refunded': 0,
            'contractor_updated': False,
        }

        # 1. 계약 상태 변경
        contract.serial_number = f"{contract.serial_number}-terminated-{completion_date}"
        contract.activation = False
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
        ContractorReleaseService._update_contractor_status(contractor, contract)
        result['contractor_updated'] = True

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
        payments = ContractPayment.objects.filter(contract=contract).select_related(
            'accounting_entry__account'
        )

        refund_count = 0
        for payment in payments:
            entry = payment.accounting_entry

            # 회계 분개의 계정을 환불 계정으로 변경
            if ContractorReleaseService._change_to_refund_account(entry):
                refund_count += 1

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
        1. 같은 parent 하위의 입금(deposit) + 계약자 관련 계정
        2. Fallback: account.pk + 1 계정
        """
        # 1순위: 더 정확한 환불 계정 찾기
        refund_account = ProjectAccount.objects.filter(
            parent=accounting_entry.account.parent,
            direction='deposit',
            is_related_contractor=True
        ).first()

        # 2순위: Fallback - pk + 1 방식
        if not refund_account:
            try:
                refund_account_pk = accounting_entry.account.pk + 1
                refund_account = ProjectAccount.objects.get(pk=refund_account_pk)
            except ProjectAccount.DoesNotExist:
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
    def _update_contractor_status(contractor, contract):
        """계약자 최종 해지 상태로 변경"""
        contractor.prev_contract = contract
        contractor.contract = None

        if contractor.qualification == '3':
            contractor.qualification = '2'  # 인가 등록 취소

        contractor.is_active = False  # 비활성 상태로 변경
        contractor.status = '4'  # 해지 상태로 변경
        contractor.save()
