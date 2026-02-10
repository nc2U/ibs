import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from _utils.contract_price import get_contract_payment_plan
from contract.models import (OrderGroup, DocumentType, RequiredDocument, Contract, ContractPrice,
                             Contractor, ContractFile, ContractDocument, ContractDocumentFile,
                             ContractorAddress, ContractorContact, ContractorConsultationLogs,
                             Succession, ContractorRelease)
from contract.services import (ContractPriceUpdateService, ContractCreationService,
                               ContractUpdateService, ContractorReleaseService)
from items.models import HouseUnit, KeyUnit, UnitType
from payment.models import InstallmentPaymentOrder
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


class ContractPaymentInContractSerializer(serializers.Serializer):
    """계약 납부 정보 Serializer (ContractPayment 기반)"""
    pk = serializers.IntegerField(read_only=True)
    installment_order = SimpleInstallmentOrderSerializer(read_only=True)
    amount = serializers.SerializerMethodField()
    deal_date = serializers.SerializerMethodField()
    bank_account = serializers.SerializerMethodField()
    trader = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    @staticmethod
    def get_amount(obj):
        """금액 (accounting_entry.amount)"""
        return obj.accounting_entry.amount if obj.accounting_entry else None

    @staticmethod
    def get_deal_date(obj):
        """거래일자 (related_transaction.deal_date)"""
        if obj.accounting_entry:
            trans = obj.accounting_entry.related_transaction
            return trans.deal_date if trans else None
        return None

    @staticmethod
    def get_bank_account(obj):
        """은행 계좌 ID (related_transaction.bank_account_id)"""
        if obj.accounting_entry:
            trans = obj.accounting_entry.related_transaction
            return trans.bank_account_id if trans else None
        return None

    @staticmethod
    def get_trader(obj):
        """거래처 (accounting_entry.trader)"""
        return obj.accounting_entry.trader if obj.accounting_entry else None


class ContractFileInContractSetSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ContractFile
        fields = ('pk', 'file', 'file_name', 'file_size', 'created', 'creator')


class ContractSetSerializer(serializers.ModelSerializer):
    order_group_sort = serializers.SerializerMethodField(read_only=True)
    unit_type_desc = SimpleUnitTypeSerializer(source='unit_type', read_only=True)
    serial_number = serializers.CharField(required=False, allow_blank=True)
    unit_type = serializers.PrimaryKeyRelatedField(
        queryset=UnitType.objects.all(), required=False, allow_null=True,
    )
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
        """납부 내역 조회 (거래일자 기준 정렬)"""
        return instance.payments.order_by('deal_date', 'created_at')

    def get_payments(self, instance):  # 납부 분담금/분양대금 리스트
        payments = self.get_payment_list(instance).select_related(
            'accounting_entry',
            'installment_order'
        )
        return ContractPaymentInContractSerializer(payments, many=True, read_only=True).data

    def get_total_paid(self, instance):
        """총 납부액 계산 (ContractPayment.amount property 사용)"""
        payments = self.get_payment_list(instance).select_related('accounting_entry')
        return sum([payment.amount for payment in payments])

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
        """간소화된 계약 생성 - 서비스 레이어 위임"""

        service = ContractCreationService()
        return service.create_contract(self.initial_data, self.context['request'].user)

    @transaction.atomic
    def update(self, instance, validated_data):
        """간소화된 계약 수정 - 서비스 레이어 위임"""

        service = ContractUpdateService()
        return service.update_contract(instance, self.context['request'].data, self.context['request'].user)


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
    """
    계약자 해지 정보 Serializer

    비즈니스 로직은 ContractorReleaseService로 분리되어 있습니다.
    """

    class Meta:
        model = ContractorRelease
        fields = ('pk', 'project', 'contractor', '__str__', 'status', 'refund_amount',
                  'refund_account_bank', 'refund_account_number', 'refund_account_depositor',
                  'request_date', 'completion_date', 'note', 'updator')

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        계약자 해지 정보 업데이트

        해지 최종 완결 처리(status 4 또는 5)는 ContractorReleaseService에 위임
        """

        released_done = instance.status in ('4', '5')  # 이미 해지 완결 여부
        new_status = validated_data.get('status')

        # 미완료 → 최종 완결 (처리완료:4 또는 자격상실:5)로 변경
        if not released_done and new_status in ('4', '5'):
            completion_date = self.initial_data.get('completion_date')

            # Service로 해지 처리 위임
            result = ContractorReleaseService.process_release_completion(
                contractor_release=instance,
                completion_date=completion_date
            )

            # 처리 결과 로깅 (선택사항)
            if not all(result.values()):
                logger = logging.getLogger(__name__)
                logger.warning(f"ContractorRelease {instance.pk} 일부 처리 실패: {result}")

        # 해지정보 테이블 업데이트
        instance.__dict__.update(**validated_data)
        instance.updator = self.context['request'].user
        instance.save()

        return instance
