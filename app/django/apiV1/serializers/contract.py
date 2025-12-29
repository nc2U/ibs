import os

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from _utils.contract_price import get_sales_price_by_gt, get_contract_price, get_contract_payment_plan
from cash.models import ProjectBankAccount, ProjectCashBook
from contract.models import (OrderGroup, DocumentType, RequiredDocument, Contract, ContractPrice,
                             Contractor, ContractFile, ContractDocument, ContractDocumentFile,
                             ContractorAddress, ContractorContact, ContractorConsultationLogs,
                             Succession, ContractorRelease)
from contract.services import ContractPriceUpdateService
from ibs.models import AccountSort, ProjectAccountD2, ProjectAccountD3
from items.models import HouseUnit, KeyUnit
from payment.models import InstallmentPaymentOrder
from project.models import Project
from .accounts import SimpleUserSerializer
from .items import SimpleUnitTypeSerializer
from .payment import SimpleInstallmentOrderSerializer, SimpleOrderGroupSerializer


# Payment Summary Serializers -------------------------------------------------------
class PaymentSummaryInstallmentSerializer(serializers.Serializer):
    installment_order = SimpleInstallmentOrderSerializer(read_only=True)
    total_amount = serializers.IntegerField(read_only=True)
    contract_count = serializers.IntegerField(read_only=True)
    average_amount = serializers.IntegerField(read_only=True)
    source_breakdown = serializers.DictField(read_only=True)


class PaymentSummarySerializer(serializers.Serializer):
    installment_summaries = PaymentSummaryInstallmentSerializer(many=True, read_only=True)
    grand_total = serializers.IntegerField(read_only=True)
    total_contracts = serializers.IntegerField(read_only=True)
    project = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    order_group = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    unit_type = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)


class MultiProjectPaymentSummarySerializer(serializers.Serializer):
    installment_summaries = PaymentSummaryInstallmentSerializer(many=True, read_only=True)
    grand_total = serializers.IntegerField(read_only=True)
    total_contracts = serializers.IntegerField(read_only=True)
    projects = serializers.ListField(child=serializers.IntegerField(), read_only=True)
    order_group = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    unit_type = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)


# Contract --------------------------------------------------------------------------
class OrderGroupSerializer(serializers.ModelSerializer):
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)

    class Meta:
        model = OrderGroup
        fields = ('pk', 'project', 'order_number', 'sort', 'sort_desc',
                  'name', 'is_default_for_uncontracted')


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ('pk', 'name')


class RequiredDocumentSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source='document_type.name', read_only=True)
    required = serializers.CharField(source='get_require_type_display', read_only=True)

    class Meta:
        model = RequiredDocument
        fields = ('pk', 'project', 'sort', 'document_type', 'document_name', 'quantity',
                  'require_type', 'required', 'description', 'display_order')


class HouseUnitInKeyUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseUnit
        fields = ('pk', '__str__', 'floor_type')


class KeyUnitInContractSerializer(serializers.ModelSerializer):
    houseunit = HouseUnitInKeyUnitSerializer()

    class Meta:
        model = KeyUnit
        fields = ('pk', 'unit_code', 'houseunit')


class AddressInContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorAddress
        fields = ('pk', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
                  'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3')


class ContactInContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorContact
        fields = ('pk', 'cell_phone', 'home_phone', 'other_phone', 'email')


class ContPriceInContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractPrice
        fields = ('pk', 'price', 'price_build', 'price_land', 'price_tax')


class ContractPriceWithPaymentPlanSerializer(serializers.ModelSerializer):
    payment_plan = serializers.SerializerMethodField()

    class Meta:
        model = ContractPrice
        fields = ('pk', 'price', 'price_build', 'price_land', 'price_tax',
                  'payment_amounts', 'is_cache_valid', 'calculated', 'payment_plan')

    @staticmethod
    def get_payment_plan(obj):
        """JSON payment_amounts를 납부 계획 형태로 변환"""
        if not obj.payment_amounts or not obj.contract:
            return []

        result = []
        for pay_time_str, amount in obj.payment_amounts.items():
            try:
                installment = InstallmentPaymentOrder.objects.get(
                    project=obj.contract.project,
                    pay_time=int(pay_time_str)
                )
                result.append({
                    'installment_order': {
                        'pk': installment.pk,
                        'pay_sort': installment.pay_sort,
                        'pay_code': installment.pay_code,
                        'pay_time': installment.pay_time,
                        'pay_name': installment.pay_name,
                        'alias_name': installment.alias_name,
                        'pay_due_date': installment.pay_due_date,
                    },
                    'amount': amount,
                    'source': 'cached'  # JSON 캐시에서 가져온 데이터임을 표시
                })
            except InstallmentPaymentOrder.DoesNotExist:
                continue

        # pay_time 순으로 정렬
        return sorted(result, key=lambda x: x['installment_order']['pay_time'])


class ContractorInContractSerializer(serializers.ModelSerializer):
    qualifi_display = serializers.CharField(source='get_qualification_display', read_only=True)
    contractoraddress = AddressInContractorSerializer(read_only=True)
    contractorcontact = ContactInContractorSerializer()

    class Meta:
        model = Contractor
        fields = ('pk', 'name', 'birth_date', 'gender', 'qualification', 'qualifi_display',
                  'contractoraddress', 'contractorcontact', 'status',
                  'reservation_date', 'contract_date', 'is_active', 'note')


def get_installments(project):
    return InstallmentPaymentOrder.objects.filter(project=project)


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ('pk', 'project', 'order_group', 'unit_type', 'serial_number', 'activation')

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        개별 계약 정보 업데이트

        Note: 프로젝트 전체 계약 가격 일괄 업데이트는 ContractPriceBulkUpdateService 사용
        """
        # 기본 계약 정보 업데이트
        instance = super().update(instance, validated_data)

        # 해당 계약의 가격 정보만 업데이트
        ContractPriceUpdateService.update_single_contract_price(instance)

        return instance


class ProjectCashBookInContractSerializer(serializers.ModelSerializer):
    installment_order = SimpleInstallmentOrderSerializer()

    class Meta:
        model = ProjectCashBook
        fields = ('pk', 'deal_date', 'income', 'bank_account', 'trader', 'installment_order')


class ProjectCashBookOrderInContractSerializer(serializers.ModelSerializer):
    installment_order = SimpleInstallmentOrderSerializer()

    class Meta:
        model = ProjectCashBook
        fields = ('installment_order',)


class ProjectCashBookIncsInContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCashBook
        fields = ('income',)


class ContractFileInContractSetSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ContractFile
        fields = ('pk', 'file', 'file_name', 'file_size', 'created', 'creator')


class ContractSetSerializer(serializers.ModelSerializer):
    order_group_sort = serializers.SerializerMethodField(read_only=True)
    unit_type_desc = SimpleUnitTypeSerializer(source='unit_type', read_only=True)
    key_unit = KeyUnitInContractSerializer(read_only=True)
    contractprice = ContPriceInContractSerializer(read_only=True)
    contractor = ContractorInContractSerializer(read_only=True)
    payments = serializers.SerializerMethodField(read_only=True)
    last_paid_order = serializers.SerializerMethodField(read_only=True)
    total_paid = serializers.SerializerMethodField(read_only=True)
    order_group_desc = SimpleOrderGroupSerializer(source='order_group', read_only=True)
    contract_files = ContractFileInContractSetSerializer(many=True, read_only=True)

    class Meta:
        model = Contract
        fields = ('pk', 'project', 'order_group_sort', 'order_group', 'unit_type', 'unit_type_desc',
                  'serial_number', 'activation', 'is_sup_cont', 'sup_cont_date', 'key_unit', 'contractprice',
                  'contractor', 'payments', 'last_paid_order', 'total_paid', 'order_group_desc', 'contract_files',
                  'updator')

    def _has_address_data(self):
        """주소 정보가 있는지 확인하는 헬퍼 메서드"""
        address_fields = [
            'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
            'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3'
        ]
        return any(self.initial_data.get(field) for field in address_fields)

    @staticmethod
    def get_order_group_sort(obj):  # '1': 조합모집 or '2': 일반분양
        return obj.order_group.sort

    @staticmethod
    def get_payment_list(instance):
        return instance.payments.filter(project_account_d3__is_payment=True)

    def get_payments(self, instance):  # 납부 분담금/분양대금 리스트
        payments = self.get_payment_list(instance).order_by('deal_date', 'id')
        return ProjectCashBookInContractSerializer(payments, many=True, read_only=True).data

    def get_total_paid(self, instance):
        inc_data = ProjectCashBookIncsInContractSerializer(self.get_payment_list(instance),
                                                           many=True,
                                                           read_only=True).data
        return sum([inc.get('income') for inc in inc_data])

    def get_last_paid_order(self, instance):  # 완납 회차 구하기
        """
        해당 계약자가 납부 완료한 마지막 회차를 반환

        Returns:
            Serialized InstallmentPaymentOrder data or None
        """

        # 1. 해당 계약의 정확한 납부 계획 조회
        payment_plan = get_contract_payment_plan(instance)
        if not payment_plan:
            return None

        # 2. 총 납부액 조회
        total_paid = self.get_total_paid(instance)
        if total_paid <= 0:
            return None

        # 3. 순차적으로 누적 약정 금액 계산하여 완납 회차 찾기
        # (get_contract_payment_plan에서 이미 pay_code, pay_time 순으로 정렬됨)
        cumulative_amount = 0
        last_paid_installment = None

        for plan_item in payment_plan:
            installment_order = plan_item['installment_order']
            amount = plan_item['amount']
            cumulative_amount += amount

            # 총 납부액이 누적 약정 금액 이상이면 해당 회차까지 완납
            if total_paid >= cumulative_amount:
                last_paid_installment = installment_order
            else:
                # 납부액이 부족하면 중단
                break

        # 5. 결과를 JSON 직렬화 가능한 형태로 반환
        if last_paid_installment:
            return SimpleInstallmentOrderSerializer(last_paid_installment).data
        return None

    @transaction.atomic
    def create(self, validated_data):
        # 1. 계약정보 테이블 입력
        contract = Contract.objects.create(**validated_data)
        request = self.context['request']

        # 2. 계약 유닛 연결
        unit_pk = self.initial_data.get('key_unit')
        key_unit = KeyUnit.objects.get(pk=unit_pk)
        contract.key_unit = key_unit
        contract.save()

        # 3. 동호수 연결
        house_unit = None
        if self.initial_data.get('houseunit'):
            house_unit_data = self.initial_data.get('houseunit')
            house_unit = HouseUnit.objects.get(pk=house_unit_data)
            house_unit.key_unit = key_unit
            house_unit.save()

            # 분양가격 설정 데이터 불러오기
            price = get_contract_price(contract, house_unit, True)  # is_set=True for consistency
        else:
            # 분양가격 설정 데이터 불러오기
            price = get_contract_price(contract, None, True)  # is_set=True for consistency

        # 4. 계약 가격 정보 등록 (price 정보만 저장, 납부 금액은 property로 계산)
        # house_unit이 이미 ContractPrice와 연결되어 있으면 업데이트, 없으면 생성
        if house_unit:
            cont_price, created = ContractPrice.objects.update_or_create(
                house_unit=house_unit,
                defaults={
                    'contract': contract,
                    'price': price[0],
                    'price_build': price[1],
                    'price_land': price[2],
                    'price_tax': price[3],
                }
            )
        else:
            # house_unit이 없는 경우 새로 생성
            cont_price = ContractPrice.objects.create(
                contract=contract,
                house_unit=None,
                price=price[0],
                price_build=price[1],
                price_land=price[2],
                price_tax=price[3]
            )

        # 5. 계약자 정보 테이블 입력
        contractor_name = self.initial_data.get('name')
        birth_date = self.initial_data.get('birth_date', None)
        contractor_gender = self.initial_data.get('gender')
        qualification = self.initial_data.get('qualification', None)
        contractor_status = self.initial_data.get('status')
        reservation_date = self.initial_data.get('reservation_date', None)
        contract_date = self.initial_data.get('contract_date', None)
        contractor_note = self.initial_data.get('note')

        contractor = Contractor.objects.create(contract=contract,
                                               name=contractor_name,
                                               birth_date=birth_date if birth_date else None,
                                               gender=contractor_gender,
                                               qualification=qualification if qualification else '1',
                                               status=contractor_status,
                                               reservation_date=reservation_date if reservation_date else None,
                                               contract_date=contract_date if contract_date else None,
                                               note=contractor_note)
        contractor.save()

        # 6. 계약자 주소 테이블 입력 (계약인 경우에만)
        if contractor_status == '2' and self._has_address_data():
            address_id_zipcode = self.initial_data.get('id_zipcode')
            address_id_address1 = self.initial_data.get('id_address1')
            address_id_address2 = self.initial_data.get('id_address2')
            address_id_address3 = self.initial_data.get('id_address3')
            address_dm_zipcode = self.initial_data.get('dm_zipcode')
            address_dm_address1 = self.initial_data.get('dm_address1')
            address_dm_address2 = self.initial_data.get('dm_address2')
            address_dm_address3 = self.initial_data.get('dm_address3')

            contractor_address = ContractorAddress.objects.create(contractor=contractor,
                                                                  id_zipcode=address_id_zipcode,
                                                                  id_address1=address_id_address1,
                                                                  id_address2=address_id_address2,
                                                                  id_address3=address_id_address3,
                                                                  dm_zipcode=address_dm_zipcode,
                                                                  dm_address1=address_dm_address1,
                                                                  dm_address2=address_dm_address2,
                                                                  dm_address3=address_dm_address3)
            contractor_address.save()

        # 7. 계약자 연락처 테이블 입력
        contact_cell_phone = self.initial_data.get('cell_phone')
        contact_home_phone = self.initial_data.get('home_phone')
        contact_other_phone = self.initial_data.get('other_phone')
        contact_email = self.initial_data.get('email')

        contractor_contact = ContractorContact.objects.create(contractor=contractor,
                                                              cell_phone=contact_cell_phone,
                                                              home_phone=contact_home_phone,
                                                              other_phone=contact_other_phone,
                                                              email=contact_email)
        contractor_contact.save()

        # 7-1. 계약서 파일 업로드 처리 (contractor 생성 후)
        new_file = request.data.get('newFile', None)
        if new_file:
            ContractFile.objects.create(contractor=contractor, file=new_file, creator=request.user)

        # 8. 계약금 -- 수납 정보 테이블 입력
        if self.initial_data.get('deal_date'):
            project = self.initial_data.get('project')
            payment_project = Project.objects.get(pk=project)
            order_group_sort = int(self.initial_data.get('order_group_sort'))
            payment_account_d2 = ProjectAccountD2.objects.get(pk=order_group_sort)
            acc_d3 = 1 if order_group_sort == 1 else 4  # 분담금일 경우 1, 분양대금일 경우 4
            payment_account_d3 = ProjectAccountD3.objects.get(pk=acc_d3)
            ins_order = self.initial_data.get('installment_order')
            payment_installment_order = InstallmentPaymentOrder.objects.get(pk=ins_order)
            payment_serial_number = self.initial_data.get('serial_number')
            payment_trader = self.initial_data.get('trader')
            bank_account = self.initial_data.get('bank_account')
            payment_bank_account = ProjectBankAccount.objects.get(pk=bank_account)
            payment_income = self.initial_data.get('income')
            payment_deal_date = self.initial_data.get('deal_date')

            down_payment = ProjectCashBook.objects.create(project=payment_project,
                                                          sort=AccountSort.objects.get(pk=1),
                                                          project_account_d2=payment_account_d2,
                                                          project_account_d3=payment_account_d3,
                                                          contract=contract,
                                                          installment_order=payment_installment_order,
                                                          content=f'{contractor_name}[{payment_serial_number}] 대금납부',
                                                          trader=payment_trader,
                                                          bank_account=payment_bank_account,
                                                          income=payment_income,
                                                          deal_date=payment_deal_date)
            down_payment.save()

        return contract

    @transaction.atomic
    def update(self, instance, validated_data):
        # 1. 계약정보 테이블 입력
        instance.__dict__.update(**validated_data)
        instance.order_group = validated_data.get('order_group', instance.order_group)
        instance.unit_type = validated_data.get('unit_type', instance.unit_type)

        # updator 설정
        instance.updator = self.context['request'].user

        data = self.context['request'].data
        user = self.context['request'].user

        new_file = data.get('newFile', None)
        if new_file:
            contractor = Contractor.objects.get(contract=instance)
            ContractFile.objects.create(contractor=contractor, file=new_file, creator=user)

        edit_file = data.get('editFile', None)  # pk of file to edit
        cng_file = data.get('cngFile', None)  # change file

        if edit_file and cng_file:
            try:
                file_to_edit = ContractFile.objects.get(pk=edit_file)
                old_file_path = file_to_edit.file.path
                # Remove an old file if it exists
                if os.path.isfile(old_file_path):
                    os.remove(old_file_path)
                # Save new file
                file_to_edit.file = cng_file
                file_to_edit.save()
            except ContractFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {edit_file} does not exist.")
            except Exception as e:
                # Log the detailed error message
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error while replacing file: {str(e)}')
                # Raise a generic error message
                raise serializers.ValidationError('An error occurred while replacing the file.')

        del_file = data.get('delFile', None)
        if del_file:
            try:
                file_to_delete = ContractFile.objects.get(pk=del_file)
                file_to_delete.delete()
            except ContractFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {del_file} does not exist.")

        # 1-2. 동호수 변경 여부 확인 및 변경 사항 적용
        unit_pk = data.get('key_unit')  # key_unit => pk
        houseunit_pk = data.get('houseunit')  # house_unit => pk

        key_unit = KeyUnit.objects.get(pk=unit_pk)
        house_unit = HouseUnit.objects.get(pk=houseunit_pk) if houseunit_pk else None

        same_unit_exist = False  # 동호가 있고 수정되지 않았는지 여부

        if instance.key_unit.pk != unit_pk:  # 계약유닛(key_unit)이 수정된 경우
            try:  # 종전 동호수가 있는 경우
                old_houseunit = instance.key_unit.houseunit
                if old_houseunit != houseunit_pk:  # 동호수가 수정된 경우
                    old_houseunit.key_unit = None  # 해당 동호수를 삭제
                    old_houseunit.save()
                else:
                    same_unit_exist = True
            except ObjectDoesNotExist:  # 종전 동호수가 없는 경우
                pass

            # 2. 계약 유닛 연결
            instance.key_unit = key_unit

            # 3. 동호수 연결
            if houseunit_pk:
                house_unit.key_unit = key_unit  # 동호수를 계약유닛과 연결
                house_unit.save()
        else:  # 계약유닛(key_unit)이 수정되지 않은 경우
            try:  # 종전 동호수가 있는 경우
                old_houseunit = instance.key_unit.houseunit
                if old_houseunit != houseunit_pk:  # 동호수가 수정된 경우
                    old_houseunit.key_unit = None  # 먼저 종전 동호수 삭제
                    old_houseunit.save()

                    # 3. 동호수 연결
                    if houseunit_pk:
                        house_unit.key_unit = key_unit  # 변경 동호수를 기존 계약유닛과 연결
                        house_unit.save()
            except ObjectDoesNotExist:  # 종전 동호수가 없는 경우
                # 3. 동호수 연결
                if houseunit_pk:
                    house_unit.key_unit = key_unit  # 동호수를 계약유닛과 연결
                    house_unit.save()

        # 4. 계약가격 정보 등록
        price = get_contract_price(instance, house_unit, True)  # is_set=True for consistency

        try:  # 계약가격 정보 존재 여부 확인
            cont_price = instance.contractprice
        except ContractPrice.DoesNotExist:
            cont_price = None

        if cont_price:  # 계약가격 데이터가 존재하는 경우
            if not same_unit_exist:  # 동호수가 생성 또는 변경 된 경우
                # 계약 가격 정보 업데이트 (price 정보만 저장, 납부 금액은 property로 계산)
                cont_price.house_unit = house_unit  # house_unit 필드 업데이트
                cont_price.price = price[0]
                cont_price.price_build = price[1]
                cont_price.price_land = price[2]
                cont_price.price_tax = price[3]
                cont_price.save()

        else:  # 계약가격 데이터가 존재하지 않는 경우 계약 가격 정보 생성
            cont_price = ContractPrice(contract=instance,
                                       house_unit=house_unit,  # house_unit 필드 추가
                                       price=price[0],
                                       price_build=price[1],
                                       price_land=price[2],
                                       price_tax=price[3])
            cont_price.save()

        # 5. 계약자 정보 테이블 입력
        contractor_name = data.get('name')
        birth_date = data.get('birth_date', None)
        contractor_gender = data.get('gender')
        qualification = data.get('qualification', None)
        contractor_status = data.get('status')
        reservation_date = data.get('reservation_date', None)
        contract_date = data.get('contract_date', None)
        contractor_note = data.get('note')

        contractor = Contractor.objects.get(contract=instance)
        contractor.name = contractor_name
        contractor.birth_date = birth_date if birth_date else contractor.birth_date
        contractor.gender = contractor_gender
        contractor.qualification = qualification if qualification else '1'
        contractor.status = contractor_status
        contractor.reservation_date = reservation_date if reservation_date else contractor.reservation_date
        contractor.contract_date = contract_date if contract_date else contractor.contract_date
        contractor.note = contractor_note
        contractor.save()

        # 6. 계약자 주소 테이블 처리
        # 청약→계약 전환 시 주소 생성, 기존 주소가 있는 경우 주소관리에서 직접 이력 관리
        if contractor_status == '2' and self._has_address_data():
            # 기존 주소가 없는 경우에만 새로 생성 (청약→계약 전환 시)
            try:
                existing_address = ContractorAddress.objects.get(contractor=contractor)
            except ContractorAddress.DoesNotExist:
                # 기존 주소가 없으면 새로 생성
                address_id_zipcode = data.get('id_zipcode')
                address_id_address1 = data.get('id_address1')
                address_id_address2 = data.get('id_address2')
                address_id_address3 = data.get('id_address3')
                address_dm_zipcode = data.get('dm_zipcode')
                address_dm_address1 = data.get('dm_address1')
                address_dm_address2 = data.get('dm_address2')
                address_dm_address3 = data.get('dm_address3')

                contractor_address = ContractorAddress.objects.create(contractor=contractor,
                                                                      id_zipcode=address_id_zipcode,
                                                                      id_address1=address_id_address1,
                                                                      id_address2=address_id_address2,
                                                                      id_address3=address_id_address3,
                                                                      dm_zipcode=address_dm_zipcode,
                                                                      dm_address1=address_dm_address1,
                                                                      dm_address2=address_dm_address2,
                                                                      dm_address3=address_dm_address3)
                contractor_address.save()

        # 7. 계약자 연락처 테이블 입력
        contact_cell_phone = data.get('cell_phone')
        contact_home_phone = data.get('home_phone')
        contact_other_phone = data.get('other_phone')
        contact_email = data.get('email')

        contractor_contact = ContractorContact.objects.get(contractor=contractor)
        contractor_contact.cell_phone = contact_cell_phone
        contractor_contact.home_phone = contact_home_phone
        contractor_contact.other_phone = contact_other_phone
        contractor_contact.email = contact_email
        contractor_contact.save()

        # 8. 계약금 -- 수납 정보 테이블 입력
        if data.get('deal_date'):
            payment_id = data.get('payment')
            project = data.get('project')
            payment_project = Project.objects.get(pk=project)
            order_group_sort = int(data.get('order_group_sort'))
            payment_account_d2 = ProjectAccountD2.objects.get(pk=order_group_sort)
            acc_d3 = 1 if order_group_sort == 1 else 4  # 분담금일 경우 1, 분양대금일 경우 4
            payment_account_d3 = ProjectAccountD3.objects.get(pk=acc_d3)
            ins_order = data.get('installment_order')
            payment_installment_order = InstallmentPaymentOrder.objects.get(pk=ins_order)
            payment_serial_number = data.get('serial_number')
            payment_trader = data.get('trader')
            bank_account = data.get('bank_account')
            payment_bank_account = ProjectBankAccount.objects.get(pk=bank_account)
            payment_income = data.get('income')
            payment_deal_date = data.get('deal_date')

            if payment_id:
                update_payment = ProjectCashBook.objects.get(pk=payment_id)
                update_payment.trader = payment_trader
                update_payment.bank_account = payment_bank_account
                update_payment.income = payment_income
                update_payment.deal_date = payment_deal_date
                update_payment.save()
            else:
                create_payment = ProjectCashBook.objects.create(project=payment_project,
                                                                sort=AccountSort.objects.get(pk=1),
                                                                project_account_d2=payment_account_d2,
                                                                project_account_d3=payment_account_d3,
                                                                contract=instance,
                                                                installment_order=payment_installment_order,
                                                                content=f'{contractor_name}[{payment_serial_number}] 대금납부',
                                                                trader=payment_trader,
                                                                bank_account=payment_bank_account,
                                                                income=payment_income,
                                                                deal_date=payment_deal_date)
                create_payment.save()
        instance.save()
        return instance


class SimpleContractSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = ('value', 'label')

    def get_value(self, obj):
        return obj.pk

    @staticmethod
    def get_label(obj):
        return str(obj.contractor)


class ContractPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractPrice
        fields = ('pk', 'contract', 'price', 'price_build', 'price_land', 'price_tax')


class SubsSummarySerializer(serializers.ModelSerializer):
    unit_type = serializers.IntegerField()
    num_cont = serializers.IntegerField()

    class Meta:
        model = Contract
        fields = ('unit_type', 'num_cont')


class ContSummarySerializer(serializers.ModelSerializer):
    order_group = serializers.IntegerField()
    unit_type = serializers.IntegerField()
    conts_num = serializers.IntegerField()
    price_sum = serializers.IntegerField()

    class Meta:
        model = Contract
        fields = ('order_group', 'unit_type', 'conts_num', 'price_sum')


class ContractAggregateSerializer(serializers.Serializer):
    total_units = serializers.IntegerField()
    subs_num = serializers.IntegerField()
    conts_num = serializers.IntegerField()
    non_conts_num = serializers.IntegerField()


class ContractInContractorSerializer(serializers.ModelSerializer):
    key_unit = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Contract
        fields = ('pk', 'serial_number', 'key_unit')


class SuccessionInContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Succession
        fields = ('pk', 'is_approval')


class ContractorSerializer(serializers.ModelSerializer):
    qualifi_display = serializers.CharField(source='get_qualification_display', read_only=True)
    succession = SuccessionInContractorSerializer(source='curr_contractor', read_only=True)
    contractorrelease = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Contractor
        fields = ('pk', 'contract', 'name', '__str__', 'birth_date', 'gender',
                  'qualification', 'qualifi_display', 'status', 'reservation_date',
                  'contract_date', 'is_active', 'note', 'succession', 'contractorrelease')


class SimpleContractorSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Contractor
        fields = ('value', 'label', 'contract')

    def get_value(self, obj):
        return obj.pk

    @staticmethod
    def get_label(obj):
        return str(obj)


class ContractFileSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ContractFile
        fields = ('pk', 'contractor', 'file', 'file_name', 'file_type', 'file_size', 'created', 'creator')
        read_only_fields = ('file_name', 'file_type', 'file_size', 'created', 'creator')


class ContractDocumentFileSerializer(serializers.ModelSerializer):
    """계약자 제출 서류 첨부 파일 Serializer"""
    uploader = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ContractDocumentFile
        fields = ('pk', 'contract_document', 'file', 'file_name', 'file_type', 'file_size',
                  'uploaded_date', 'uploader')
        read_only_fields = ('file_name', 'file_type', 'file_size', 'uploaded_date', 'uploader')


class ContractDocumentSerializer(serializers.ModelSerializer):
    """계약자 제출 서류 Serializer"""
    sort = serializers.CharField(source='required_document.sort', read_only=True)
    document_name = serializers.CharField(source='document_type.name', read_only=True)
    required_quantity = serializers.IntegerField(source='required_document.quantity', read_only=True)
    require_type = serializers.CharField(source='required_document.require_type', read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    files = ContractDocumentFileSerializer(many=True, read_only=True)

    class Meta:
        model = ContractDocument
        fields = ('pk', 'contractor', 'sort', 'required_document', 'submitted_quantity',
                  'document_name', 'required_quantity', 'require_type', 'is_complete', 'files')


class ContractorAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorAddress
        fields = ('pk', 'contractor', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
                  'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3', 'is_current', 'created')

    @transaction.atomic
    def create(self, validated_data):
        contractor = validated_data.get('contractor')

        # 동일 계약자의 기존 현재 주소를 False로 변경
        if contractor:
            ContractorAddress.objects.filter(
                contractor=contractor,
                is_current=True
            ).update(is_current=False)

        # 새 주소 인스턴스 생성
        instance = ContractorAddress.objects.create(**validated_data)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        # is_current 값이 True로 변경되는 경우 처리
        if validated_data.get('is_current', False) and not instance.is_current:
            # 동일 contractor의 다른 모든 주소를 is_current=False로 변경
            ContractorAddress.objects.filter(
                contractor=instance.contractor,
                is_current=True
            ).exclude(pk=instance.pk).update(is_current=False)

        # 인스턴스 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class ContractorContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorContact
        fields = ('pk', 'contractor', 'cell_phone', 'home_phone', 'other_phone', 'email')


class ContractorConsultationLogsSerializer(serializers.ModelSerializer):
    """계약자 상담 내역 Serializer"""
    consultant = SimpleUserSerializer(read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = ContractorConsultationLogs
        fields = ('pk', 'contractor', 'consultation_date', 'channel', 'channel_display',
                  'category', 'category_display', 'title', 'content', 'status', 'status_display',
                  'priority', 'priority_display', 'consultant', 'follow_up_required', 'follow_up_note',
                  'completion_date', 'is_important', 'created', 'updated')
        read_only_fields = ('created', 'updated')


class ContractInSuccessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ('pk', 'serial_number')


class SellerInSuccessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contractor
        fields = ('pk', 'name')


class BuyerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorAddress
        fields = ('pk', 'id_zipcode', 'id_address1', 'id_address2', 'id_address3',
                  'dm_zipcode', 'dm_address1', 'dm_address2', 'dm_address3')


class BuyerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorContact
        fields = ('pk', 'cell_phone', 'home_phone', 'other_phone', 'email')


class BuyerInSuccessionSerializer(serializers.ModelSerializer):
    contractoraddress = BuyerAddressSerializer(read_only=True)
    contractorcontact = BuyerContactSerializer(read_only=True)

    class Meta:
        model = Contractor
        fields = ('pk', 'name', 'birth_date', 'gender', 'contractoraddress', 'contractorcontact')


class SuccessionSerializer(serializers.ModelSerializer):
    contract = ContractInSuccessionSerializer(read_only=True)
    seller = SellerInSuccessionSerializer(read_only=True)
    buyer = BuyerInSuccessionSerializer(read_only=True)

    class Meta:
        model = Succession
        fields = ('pk', 'contract', 'seller', 'buyer', 'apply_date',
                  'trading_date', 'is_approval', 'approval_date', 'note', 'updator')

    @transaction.atomic
    def create(self, validated_data):
        # 1. contract 데이터 추출
        validated_data['contract_id'] = self.initial_data.get('contract')
        contract = Contract.objects.get(pk=validated_data['contract_id'])

        # 2. 기존 계약자(양도인) 처리 (해지 신청 중인 경우 신청 취소 처리)
        seller = contract.contractor
        seller.contract = None
        seller.prev_contract = contract
        seller.status = '5'
        seller.is_active = False
        seller.save()

        # 해지신청 계약자인지 확인
        try:
            release = seller.contractorrelease
            if release:
                release.status = '0'
                release.save()
        except ObjectDoesNotExist:
            pass

        # 3. 양수계약자 데이터 생성
        qualification = '1' if contract.order_group.sort == '2' else '2'  # 일반분양이면 일반('1') 조합이면 미인가('2')

        buyer = Contractor(contract=contract,
                           name=self.initial_data.get('name'),
                           birth_date=self.initial_data.get('birth_date'),
                           gender=self.initial_data.get('gender'),
                           qualification=qualification,
                           status='2',
                           contract_date=validated_data.get('apply_date'),  # 승계신청일을 계약일자로 기록
                           note=validated_data.get('note'))
        buyer.save()

        # 4. 양수계약자 주소정보 입력
        buyer_addr = ContractorAddress(contractor=buyer,
                                       id_zipcode=self.initial_data.get('id_zipcode'),
                                       id_address1=self.initial_data.get('id_address1'),
                                       id_address2=self.initial_data.get('id_address2'),
                                       id_address3=self.initial_data.get('id_address3'),
                                       dm_zipcode=self.initial_data.get('dm_zipcode'),
                                       dm_address1=self.initial_data.get('dm_address1'),
                                       dm_address2=self.initial_data.get('dm_address2'),
                                       dm_address3=self.initial_data.get('dm_address3'))
        buyer_addr.save()

        # 5. 양수계약자 연락처정보 입력
        buyer_contact = ContractorContact(contractor=buyer,
                                          cell_phone=self.initial_data.get('cell_phone'),
                                          home_phone=self.initial_data.get('home_phone'),
                                          other_phone=self.initial_data.get('other_phone'),
                                          email=self.initial_data.get('email'))
        buyer_contact.save()

        # 6. 권리 의무 승계 정보 입력
        validated_data['seller_id'] = self.initial_data.get('seller')
        validated_data['buyer'] = buyer
        succession = Succession.objects.create(**validated_data)
        succession.save()

        return succession

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        # updator 설정
        instance.updator = self.context['request'].user
        instance.save()

        # 2. 양수계약자 데이터 저장
        buyer = instance.buyer  # 양수계약자 정보
        buyer.name = self.initial_data.get('name')
        buyer.birth_date = self.initial_data.get('birth_date')
        buyer.gender = self.initial_data.get('gender')
        buyer.contract_date = validated_data.get('apply_date')  # 승계신청일을 계약일자로 기록
        buyer.note = f"{buyer.note + '\n' if buyer.note else ''}{validated_data.get('note')}"
        buyer.save()

        buyer_addr = buyer.contractoraddress
        buyer_addr.id_zipcode = self.initial_data.get('id_zipcode')
        buyer_addr.id_address1 = self.initial_data.get('id_address1')
        buyer_addr.id_address2 = self.initial_data.get('id_address2')
        buyer_addr.id_address3 = self.initial_data.get('id_address3')
        buyer_addr.dm_zipcode = self.initial_data.get('dm_zipcode')
        buyer_addr.dm_address1 = self.initial_data.get('dm_address1')
        buyer_addr.dm_address2 = self.initial_data.get('dm_address2')
        buyer_addr.dm_address3 = self.initial_data.get('dm_address3')
        buyer_addr.save()

        buyer_contact = buyer.contractorcontact
        buyer_contact.cell_phone = self.initial_data.get('cell_phone')
        buyer_contact.home_phone = self.initial_data.get('home_phone')
        buyer_contact.other_phone = self.initial_data.get('other_phone')
        buyer_contact.email = self.initial_data.get('email')
        buyer_contact.save()

        # 3. 변경인가완료 처리 여부 확인

        contract = instance.contract
        qua_true = '1' if contract.order_group.sort == '2' else '3'  # 일반분양이면 일반('1') 조합이면 인가('3')
        qua_false = '1' if contract.order_group.sort == '2' else '2'  # 일반분양이면 일반('1') 조합이면 미인가('2')

        # 최초 변경인가 처리 변경 시 (조합원이면 인가/미인가 상태 적용)
        seller = instance.seller
        if instance.is_approval is True:  # 변경인가 완료로 변경 시
            buyer.qualification = qua_true
            seller.qualification = qua_false
        else:  # 변경인가 진행중으로 변경 시
            buyer.qualification = qua_false
            seller.qualification = qua_true
        buyer.save()
        seller.save()

        return instance


class ContractorReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorRelease
        fields = ('pk', 'project', 'contractor', '__str__', 'status', 'refund_amount',
                  'refund_account_bank', 'refund_account_number', 'refund_account_depositor',
                  'request_date', 'completion_date', 'note', 'updator')

    @transaction.atomic
    def update(self, instance, validated_data):
        contractor = instance.contractor  # 계약자 오브젝트
        released_done = True if instance.status in ('4', '5') else False  # 해지완결 여부

        # 미완료인 상태에서 4 -> 처리완료, 5 -> 자격상실 :: 최초의 최종 해지 확정 처리 1회 실행
        if not released_done and validated_data.get('status') in ('4', '5'):
            # 1. 계약 상태 변경
            completion_date = self.initial_data.get('completion_date')
            contract = contractor.contract
            contract.serial_number = f"{contract.serial_number}-terminated-{completion_date}"
            contract.activation = False  # 일련번호 활성 해제

            # 2. 동호수 연결 해제
            unit = None
            try:  # 동호수 존재 여부 확인
                unit = contract.key_unit.houseunit
            except ObjectDoesNotExist:
                pass
            if unit:  # 동호수 존재 시 삭제
                unit.key_unit = None
                unit.save()

            # 3. 키유닛과 계약 간 연결 해제
            contract.key_unit = None
            contract.save()

            # 3-1. 계약가격 정보 해지 처리 - 미계약 상태로 전환
            try:
                contract_price = contract.contractprice
                # contract를 None으로 설정하여 미계약 상태로 전환
                contract_price.contract = None

                # house_unit이 있고 미계약용 기본 차수가 설정된 경우 SalesPriceByGT 기준 가격으로 업데이트
                default_order_group = OrderGroup.get_default_for_project(contract.project)
                if unit and default_order_group:
                    # 임시 계약 객체 생성 (미계약용 기본 차수와 프로젝트 정보로)
                    # get_sales_price_by_gt 함수에서 필요한 contract 속성들을 제공
                    class TempContract:
                        def __init__(self, project, order_group, unit_type):
                            self.project = project
                            self.order_group = order_group
                            self.unit_type = unit_type

                    temp_contract = TempContract(
                        contract.project,
                        default_order_group,
                        unit.unit_type
                    )

                    # get_sales_price_by_gt 함수로 기준 가격 조회
                    sales_price = get_sales_price_by_gt(temp_contract, unit)

                    if sales_price:
                        # 미계약 기준 가격으로 업데이트
                        contract_price.price = sales_price.price
                        contract_price.price_build = sales_price.price_build
                        contract_price.price_land = sales_price.price_land
                        contract_price.price_tax = sales_price.price_tax

                contract_price.save()

            except ContractPrice.DoesNotExist:
                # ContractPrice가 없는 경우 무시
                pass

            # 4. 해당 납부분담금 환불처리
            sort = AccountSort.objects.get(pk=1)  # 입금 종류 선택(1=입금, 2=출금)
            payments = ProjectCashBook.objects.filter(sort=sort, contract=contract)  # 해당 계약 입금건 전체
            for payment in payments:
                if not released_done:  # 해지 확정 전일 때만 실행
                    refund_d3 = int(payment.project_account_d3.id) + 1  # 분양대금 or 분담금 환불처리 건으로 계정
                    payment.project_account_d3 = ProjectAccountD3.objects.get(pk=refund_d3)  # 환불처리 계정으로 변경
                    payment.refund_contractor = contractor  # 환불 계약자 등록
                if completion_date:  # 최종 해지(환불)처리일 정보가 있으면
                    msg = f'환불 계약 건 - {payment.contract.serial_number[:13]} ({completion_date} {contractor.name} 환불완료)'
                    append_note = ', ' + msg if payment.note else msg
                    payment.note = payment.note + append_note  # 비고란 최종 메시지 입력
                payment.save()

            # 5.  계약자 정보 최종 해지상태로 변경
            contractor.prev_contract = contract
            contractor.contract = None
            if contractor.qualification == '3':
                contractor.qualification = '2'  # 인가 등록 취소
            contractor.is_active = False  # 비활성 상태로 변경
            contractor.status = '4'  # 해지 상태로 변경
            contractor.save()

        # 1. 해지정보 테이블 입력
        instance.__dict__.update(**validated_data)
        # updator 설정
        instance.updator = self.context['request'].user
        instance.save()

        return instance
