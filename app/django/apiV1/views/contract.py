from django.db.models import Count, Sum
from django_filters import ChoiceFilter, ModelChoiceFilter, DateFilter, BooleanFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from contract.models import (OrderGroup, Contract, ContractPrice, Contractor,
                             ContractorAddress, ContractorContact,
                             Succession, ContractorRelease)
from items.models import BuildingUnit
from ..pagination import PageNumberPaginationThreeThousand
from ..permission import *
from ..serializers.contract import *


# Contract --------------------------------------------------------------------------
class OrderGroupViewSet(viewsets.ModelViewSet):
    queryset = OrderGroup.objects.all()
    serializer_class = OrderGroupSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'sort')
    search_fields = ('order_group_name',)


class ContractFilter(FilterSet):
    houseunit__isnull = BooleanFilter(field_name='keyunit__houseunit', lookup_expr='isnull', label='동호미지정 여부')
    keyunit__houseunit__building_unit = ModelChoiceFilter(queryset=BuildingUnit.objects.all(), label='동(건물)')
    contractor__status = ChoiceFilter(field_name='contractor__status', choices=Contractor.STATUS_CHOICES, label='현재상태')
    contractor__qualification = ChoiceFilter(field_name='contractor__qualification',
                                             choices=Contractor.QUA_CHOICES, label='등록상태')
    from_contract_date = DateFilter(field_name='contractor__contract_date', lookup_expr='gte', label='계약일자부터')
    to_contract_date = DateFilter(field_name='contractor__contract_date', lookup_expr='lte', label='계약일자까지')

    class Meta:
        model = Contract
        fields = ('project', 'activation', 'contractor__status', 'order_group', 'unit_type',
                  'keyunit__houseunit__building_unit', 'houseunit__isnull', 'is_sup_cont',
                  'contractor__qualification', 'from_contract_date', 'to_contract_date')


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = ContractFilter
    search_fields = ('serial_number', 'contractor__name',
                     'contractor__note', 'succession__seller__name',
                     'contractor__contractoraddress__id_address1',
                     'contractor__contractoraddress__id_address2',
                     'contractor__contractoraddress__id_address3',
                     'contractor__contractoraddress__dm_address1',
                     'contractor__contractoraddress__dm_address2',
                     'contractor__contractoraddress__dm_address3',
                     'contractor__contractorcontact__cell_phone',
                     'contractor__contractorcontact__home_phone',
                     'contractor__contractorcontact__other_phone',
                     'contractor__contractorcontact__email')
    ordering_fields = ('created_at', 'contractor__contract_date',
                       'serial_number', 'contractor__name')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContractSetViewSet(ContractViewSet):
    serializer_class = ContractSetSerializer
    pagination_class = PageNumberPaginationThreeThousand


class SimpleContractViewSet(ContractViewSet):
    serializer_class = SimpleContractSerializer
    pagination_class = PageNumberPaginationThreeThousand

    def get_queryset(self):
        return Contract.objects.filter(activation=True, contractor__is_active=True)


class ContractPriceViewSet(viewsets.ModelViewSet):
    queryset = ContractPrice.objects.all()
    serializer_class = ContractPriceSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('contract__project', 'contract__order_group',
                        'contract__unit_type', 'contract__activation',
                        'contract__contractor__status')


class SubsSummaryViewSet(viewsets.ModelViewSet):
    serializer_class = SubsSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        return Contract.objects.filter(activation=True, contractor__status=1) \
            .values('unit_type') \
            .annotate(num_cont=Count('unit_type'))


class ContSumFilter(FilterSet):
    to_contract_date = DateFilter(field_name='contractor__contract_date', lookup_expr='lte', label='계약일자까지')

    class Meta:
        model = Contract
        fields = ('project', 'to_contract_date')


class ContSummaryViewSet(viewsets.ModelViewSet):
    serializer_class = ContSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = ContSumFilter

    def get_queryset(self):
        return Contract.objects.filter(activation=True, contractor__status=2) \
            .values('order_group', 'unit_type') \
            .annotate(conts_num=Count('order_group')) \
            .annotate(price_sum=Sum('contractprice__price'))


class ContractAggreateView(APIView):
    def get(self, request, project_id):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'detail': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        # 해당 프로젝트와 연결된 계약들
        contracts = Contract.objects.filter(project=project)

        # 계약 ID 목록 추출
        contract_ids = contracts.values_list('id', flat=True)

        # 계약 ID를 가진 Contractor를 기준으로 count
        contractors = Contractor.objects.filter(contract__project=project)
        subs_num = contractors.filter(contract_id__in=contract_ids, status='1').count()
        conts_num = contractors.filter(contract_id__in=contract_ids, status='2').count()
        non_conts_num = project.num_unit - conts_num if project.num_unit else 0

        data = {
            'total_units': project.num_unit or 0,
            'subs_num': subs_num,
            'conts_num': conts_num,
            'non_conts_num': non_conts_num
        }

        serializer = ContractAggregateSerializer(data)
        return Response(serializer.data)


class ContractorViewSet(viewsets.ModelViewSet):
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('contract__project', 'gender', 'qualification', 'status', 'is_active')
    search_fields = ('name', 'note', 'contract__serial_number', 'contract__succession__seller__name',
                     'contractoraddress__id_address1', 'contractoraddress__id_address2',
                     'contractoraddress__id_address3', 'contractoraddress__dm_address1',
                     'contractoraddress__dm_address2', 'contractoraddress__dm_address3',
                     'contractorcontact__cell_phone', 'contractorcontact__home_phone',
                     'contractorcontact__other_phone', 'contractorcontact__email')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class ContAddressViewSet(viewsets.ModelViewSet):
    queryset = ContractorAddress.objects.all()
    serializer_class = ContractorAddressSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class ContContactViewSet(viewsets.ModelViewSet):
    queryset = ContractorContact.objects.all()
    serializer_class = ContractorContactSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class SuccessionViewSet(viewsets.ModelViewSet):
    queryset = Succession.objects.all()
    serializer_class = SuccessionSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('contract__project',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContReleaseViewSet(viewsets.ModelViewSet):
    queryset = ContractorRelease.objects.all().order_by('-request_date', '-created_at')
    serializer_class = ContractorReleaseSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'status')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
