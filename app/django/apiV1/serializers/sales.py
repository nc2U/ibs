from rest_framework import serializers
from sales.models import (
    SalesAgency, SalesTeam, SalesPerson, SalesPersonDocument, CommissionPolicy,
    ContractSalesAgent, SettlementPeriod, CommissionPayout,
    PayoutContractDetail, CommissionClawback
)


class SalesAgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAgency
        fields = (
            'id', 'project', 'name', 'is_direct_managed',
            'business_number', 'ceo_name', 'phone', 'order',
            'is_active', 'created_at', 'updated_at'
        )


class SalesTeamSerializer(serializers.ModelSerializer):
    agency_name = serializers.ReadOnlyField(source='agency.name')
    parent_name = serializers.ReadOnlyField(source='parent.name')
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = SalesTeam
        fields = (
            'id', 'agency', 'agency_name', 'parent', 'parent_name',
            'name', 'order', 'is_active', 'members_count', 'created_at'
        )

    def get_members_count(self, obj):
        return obj.members.filter(status='1').count()


class SalesPersonDocumentSerializer(serializers.ModelSerializer):
    sales_person_name = serializers.ReadOnlyField(source='sales_person.name')
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    verified_by_name = serializers.ReadOnlyField(source='verified_by.username')
    uploader_name = serializers.ReadOnlyField(source='uploader.username')

    class Meta:
        model = SalesPersonDocument
        fields = (
            'id', 'sales_person', 'sales_person_name', 'doc_type', 'doc_type_display',
            'title', 'file', 'file_name', 'file_type', 'file_size',
            'is_verified', 'verified_at', 'verified_by', 'verified_by_name',
            'uploader', 'uploader_name', 'created_at', 'updated_at'
        )
        read_only_fields = ('file_name', 'file_type', 'file_size', 'uploader', 'created_at', 'updated_at')


class SalesPersonSerializer(serializers.ModelSerializer):
    team_name = serializers.ReadOnlyField(source='team.name')
    agency_name = serializers.ReadOnlyField(source='team.agency.name')
    duty_display = serializers.CharField(source='get_duty_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tax_type_display = serializers.CharField(source='get_tax_type_display', read_only=True)
    documents_count = serializers.SerializerMethodField()
    documents = SalesPersonDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = SalesPerson
        fields = (
            'id', 'team', 'team_name', 'agency_name', 'user',
            'name', 'duty', 'duty_display', 'status', 'status_display',
            'phone', 'id_number', 'tax_type', 'tax_type_display',
            'bank_name', 'account_number', 'account_holder',
            'join_date', 'quit_date', 'notes', 'documents_count', 'documents',
            'created_at', 'updated_at'
        )

    def get_documents_count(self, obj):
        return obj.documents.count()


class CommissionPolicySerializer(serializers.ModelSerializer):
    unit_type_name = serializers.ReadOnlyField(source='unit_type.name')
    order_group_name = serializers.ReadOnlyField(source='order_group.name')
    pay_condition_display = serializers.CharField(source='get_pay_condition_display', read_only=True)

    class Meta:
        model = CommissionPolicy
        fields = (
            'id', 'project', 'order_group', 'order_group_name',
            'unit_type', 'unit_type_name', 'name',
            'agent_fee', 'leader_fee', 'director_fee', 'agency_fee',
            'pay_condition', 'pay_condition_display',
            'start_date', 'end_date', 'is_active',
            'created_at', 'updated_at'
        )


class ContractSalesAgentSerializer(serializers.ModelSerializer):
    contract_serial = serializers.ReadOnlyField(source='contract.serial_number')
    contractor_name = serializers.ReadOnlyField(source='contract.contractor.name')
    order_group_name = serializers.ReadOnlyField(source='contract.order_group.name')
    unit_type_name = serializers.ReadOnlyField(source='contract.unit_type.name')
    unit_info = serializers.SerializerMethodField()
    sales_person_name = serializers.ReadOnlyField(source='sales_person.name')
    team_name = serializers.ReadOnlyField(source='team.name')
    policy_name = serializers.ReadOnlyField(source='policy.name')

    class Meta:
        model = ContractSalesAgent
        fields = (
            'id', 'contract', 'contract_serial', 'contractor_name',
            'order_group_name', 'unit_type_name', 'unit_info',
            'sales_person', 'sales_person_name', 'team', 'team_name',
            'policy', 'policy_name', 'contract_date',
            'mgm_name', 'mgm_phone', 'mgm_fee', 'note',
            'created_at', 'updated_at'
        )

    def get_unit_info(self, obj):
        if obj.contract and obj.contract.key_unit and hasattr(obj.contract.key_unit, 'houseunit'):
            hu = obj.contract.key_unit.houseunit
            return f'{hu.building_unit.name}동 {hu.name}호'
        return ''


class PayoutContractDetailSerializer(serializers.ModelSerializer):
    contract_serial = serializers.ReadOnlyField(source='contract.serial_number')
    contractor_name = serializers.ReadOnlyField(source='contract.contractor.name')
    role_type_display = serializers.CharField(source='get_role_type_display', read_only=True)

    class Meta:
        model = PayoutContractDetail
        fields = (
            'id', 'payout', 'contract', 'contract_serial',
            'contractor_name', 'role_type', 'role_type_display', 'unit_fee'
        )


class CommissionPayoutSerializer(serializers.ModelSerializer):
    sales_person_name = serializers.ReadOnlyField(source='sales_person.name')
    duty_display = serializers.CharField(source='sales_person.get_duty_display', read_only=True)
    team_name = serializers.ReadOnlyField(source='sales_person.team.name')
    pay_status_display = serializers.CharField(source='get_pay_status_display', read_only=True)
    contract_details = PayoutContractDetailSerializer(many=True, read_only=True)

    class Meta:
        model = CommissionPayout
        fields = (
            'id', 'period', 'sales_person', 'sales_person_name', 'duty_display', 'team_name',
            'base_pay', 'contract_count', 'commission_amount', 'bonus_amount',
            'deduction_amount', 'gross_amount', 'income_tax', 'local_income_tax',
            'total_tax', 'net_amount', 'pay_status', 'pay_status_display',
            'paid_date', 'bank_name', 'account_number', 'account_holder',
            'note', 'contract_details', 'created_at', 'updated_at'
        )


class SettlementPeriodSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payout_count = serializers.SerializerMethodField()

    class Meta:
        model = SettlementPeriod
        fields = (
            'id', 'project', 'title', 'start_date', 'end_date', 'payout_date',
            'status', 'status_display', 'total_contracts',
            'total_gross_amount', 'total_tax_amount', 'total_net_amount',
            'payout_count', 'created_by', 'created_at', 'updated_at'
        )

    def get_payout_count(self, obj):
        return obj.payouts.count()


class CommissionClawbackSerializer(serializers.ModelSerializer):
    contract_serial = serializers.ReadOnlyField(source='contract.serial_number')
    sales_person_name = serializers.ReadOnlyField(source='sales_person.name')

    class Meta:
        model = CommissionClawback
        fields = (
            'id', 'contract', 'contract_serial', 'sales_person', 'sales_person_name',
            'amount', 'reason', 'is_settled', 'settled_payout', 'created_at'
        )
