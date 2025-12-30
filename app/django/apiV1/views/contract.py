from django.core.cache import cache
from django.db.models import Count, Sum, Q
from django.shortcuts import get_object_or_404
from django_filters import ChoiceFilter, ModelChoiceFilter, DateFilter, BooleanFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from _utils.contract_price import get_project_payment_summary, get_multiple_projects_payment_summary, get_contract_price
from contract.services import ContractPriceBulkUpdateService
from items.models import BuildingUnit, UnitType
from project.models import Project
from ..pagination import PageNumberPaginationThreeThousand, PageNumberPaginationFifteen, PageNumberPaginationFifty
from ..permission import *
from ..serializers.contract import *


# Contract --------------------------------------------------------------------------
class OrderGroupViewSet(viewsets.ModelViewSet):
    queryset = OrderGroup.objects.all()
    serializer_class = OrderGroupSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'sort')
    search_fields = ('name',)


class DocumentTypeViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifty

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class RequiredDocumentFilter(FilterSet):
    class Meta:
        model = RequiredDocument
        fields = ('project', 'sort')


class RequiredDocumentViewSet(viewsets.ModelViewSet):
    queryset = RequiredDocument.objects.all()
    serializer_class = RequiredDocumentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifty
    filterset_class = RequiredDocumentFilter

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


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
    pagination_class = PageNumberPaginationFifteen
    filterset_class = ContractFilter
    search_fields = ('serial_number', 'contractor__name',
                     'contractor__note', 'succession__seller__name',
                     'contractor__addresses__id_address1',
                     'contractor__addresses__id_address2',
                     'contractor__addresses__id_address3',
                     'contractor__addresses__dm_address1',
                     'contractor__addresses__dm_address2',
                     'contractor__addresses__dm_address3',
                     'contractor__contractorcontact__cell_phone',
                     'contractor__contractorcontact__home_phone',
                     'contractor__contractorcontact__other_phone',
                     'contractor__contractorcontact__email')
    ordering_fields = ('created', 'contractor__contract_date',
                       'serial_number', 'contractor__name')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        # from_page 정보를 임시로 저장
        from_page = self.request.data.get('from_page')
        instance = serializer.save(creator=self.request.user)

        # 인스턴스에 from_page 정보 임시 저장 (슬랙 알림에서 사용)
        if from_page:
            setattr(instance, '_from_page', from_page)

        return instance

    @action(detail=False, methods=['get'])
    def find_page(self, request):
        """특정 ID의 항목이 몇 번째 페이지에 있는지 찾기"""
        highlight_id = request.query_params.get('highlight_id')
        if not highlight_id:
            return Response({'error': 'highlight_id parameter required'}, status=400)

        try:
            highlight_id = int(highlight_id)
        except ValueError:
            return Response({'error': 'highlight_id must be integer'}, status=400)

        # 현재 필터 조건을 적용한 queryset 가져오기
        queryset = self.filter_queryset(self.get_queryset())

        # 해당 ID가 존재하는지 확인
        try:
            target_item = queryset.get(pk=highlight_id)
        except Contract.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        # Contract 모델의 기본 정렬이 없으므로 ID 역순으로 정렬
        # 해당 항목보다 앞에 있는 항목 개수 계산
        items_before = queryset.filter(id__gt=target_item.id).count()

        # 페이지 크기는 15개
        page_size = 15
        page_number = (items_before // page_size) + 1

        return Response({'page': page_number})

    @action(detail=False, methods=['get'], url_path='payment-summary')
    def payment_summary(self, request):
        """
        Get a payment summary for contracts with installment-wise totals.

        Query Parameters:
            - project: Project ID (required)
            - order_group: OrderGroup ID (optional)
            - unit_type: UnitType ID (optional)
            - use_cache: Boolean (default: true)
        """
        project_id = request.query_params.get('project')
        order_group_id = request.query_params.get('order_group')
        unit_type_id = request.query_params.get('unit_type')
        use_cache = request.query_params.get('use_cache', 'true').lower() == 'true'

        if not project_id:
            return Response(
                {'error': 'project parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = Project.objects.get(id=project_id)
            order_group = OrderGroup.objects.get(id=order_group_id) if order_group_id else None
            unit_type = UnitType.objects.get(id=unit_type_id) if unit_type_id else None

        except (Project.DoesNotExist, OrderGroup.DoesNotExist, UnitType.DoesNotExist):
            return Response(
                {'error': 'Invalid ID provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate cache key
        cache_key = f'payment_summary_{project_id}_{order_group_id}_{unit_type_id}'

        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)

        # Get payment summary
        summary_data = get_project_payment_summary(project, order_group, unit_type)
        summary_data['project'] = project
        summary_data['order_group'] = order_group
        summary_data['unit_type'] = unit_type

        # Serialize result
        serializer = PaymentSummarySerializer(summary_data)
        result = serializer.data

        if use_cache:
            cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour

        return Response(result)

    @action(detail=True, methods=['get'], url_path='payment-plan')
    def payment_plan(self, request, pk=None):
        """
        Get a payment plan for a specific contract using get_contract_payment_plan.

        Returns:
            List of installment orders with calculated amounts for the contract.
        """
        try:
            contract = self.get_object()
            payment_plan = get_contract_payment_plan(contract)

            # Serialize the data
            result = []
            for plan_item in payment_plan:
                installment_order = plan_item['installment_order']
                result.append({
                    'installment_order': {
                        'pk': installment_order.pk,
                        'pay_sort': installment_order.pay_sort,
                        'pay_code': installment_order.pay_code,
                        'pay_time': installment_order.pay_time,
                        'pay_name': installment_order.pay_name,
                        'alias_name': installment_order.alias_name,
                        'pay_amt': installment_order.pay_amt,
                        'pay_ratio': installment_order.pay_ratio,
                        'pay_due_date': installment_order.pay_due_date,
                        'days_since_prev': installment_order.days_since_prev,
                        'is_except_price': installment_order.is_except_price,
                    },
                    'amount': plan_item['amount'],
                    'source': plan_item['source']
                })

            return Response(result)

        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception:
            return Response(
                {'error': 'Failed to get payment plan due to an internal error.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='price-payment-plan')
    def price_payment_plan(self, request, pk=None):
        """
        Contract의 ContractPrice JSON 기반 납부 계획 조회 (고성능)
        기존 get_contract_payment_plan 함수 대비 6.7x 성능 향상 (0.004164s vs 0.027694s)
        """
        try:
            contract = self.get_object()

            # Contract의 ContractPrice 조회
            try:
                contract_price = contract.contractprice
            except ObjectDoesNotExist:
                return Response(
                    {'error': 'ContractPrice not found for this contract'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # JSON 방식으로 빠른 응답
            serializer = ContractPriceWithPaymentPlanSerializer(contract_price)
            return Response(serializer.data)

        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to get payment plan due to an internal error.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='multi-project-payment-summary')
    def multi_project_payment_summary(self, request):
        """
        Get a payment summary for multiple projects.

        Query Parameters:
            - projects: Comma-separated project IDs (required)
            - order_group: OrderGroup ID (optional)
            - unit_type: UnitType ID (optional)
        """
        project_ids_str = request.query_params.get('projects', '')
        order_group_id = request.query_params.get('order_group')
        unit_type_id = request.query_params.get('unit_type')

        if not project_ids_str:
            return Response(
                {'error': 'projects parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project_ids = [int(pid.strip()) for pid in project_ids_str.split(',') if pid.strip()]
            if not project_ids:
                return Response(
                    {'error': 'projects parameter must contain valid project IDs'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            projects = list(Project.objects.filter(id__in=project_ids))
            order_group = OrderGroup.objects.get(id=order_group_id) if order_group_id else None
            unit_type = UnitType.objects.get(id=unit_type_id) if unit_type_id else None

            if len(projects) != len(project_ids):
                return Response(
                    {'error': 'Some project IDs are invalid'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except (ValueError, OrderGroup.DoesNotExist, UnitType.DoesNotExist) as e:
            return Response(
                {'error': 'Invalid parameter provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get combined payment summary
        summary_data = get_multiple_projects_payment_summary(projects, order_group, unit_type)
        summary_data['projects'] = [p.id for p in projects]
        summary_data['order_group'] = order_group
        summary_data['unit_type'] = unit_type

        # Serialize result
        serializer = MultiProjectPaymentSummarySerializer(summary_data)
        return Response(serializer.data)


class ContractSetViewSet(ContractViewSet):
    serializer_class = ContractSetSerializer

    def perform_update(self, serializer):
        # from_page 정보를 임시로 저장
        from_page = self.request.data.get('from_page')
        instance = serializer.save(updator=self.request.user)

        # 인스턴스에 from_page 정보 임시 저장 (슬랙 알림에서 사용)
        if from_page:
            setattr(instance, '_from_page', from_page)

        return instance

    @action(detail=False, methods=['get'])
    def find_page(self, request):
        """특정 ID의 항목이 몇 번째 페이지에 있는지 찾기"""
        highlight_id = request.query_params.get('highlight_id')
        if not highlight_id:
            return Response({'error': 'highlight_id parameter required'}, status=400)

        try:
            highlight_id = int(highlight_id)
        except ValueError:
            return Response({'error': 'highlight_id must be integer'}, status=400)

        # 현재 필터 조건을 적용한 queryset 가져오기
        queryset = self.filter_queryset(self.get_queryset())

        # 해당 ID가 존재하는지 확인
        try:
            target_item = queryset.get(pk=highlight_id)
        except Contract.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        # limit 파라미터 가져오기 (기본값은 10)
        limit = int(request.query_params.get('limit', 10))

        # Contract 모델의 기본 정렬이 없으므로 ordering 파라미터 확인
        ordering = request.query_params.get('ordering', '-created')

        if ordering.startswith('-'):
            # 내림차순 정렬
            field = ordering[1:]
            if field == 'created':
                items_before = queryset.filter(created__gt=target_item.created).count()
            else:
                items_before = queryset.filter(id__gt=target_item.id).count()
        else:
            # 오름차순 정렬
            if ordering == 'created':
                items_before = queryset.filter(created__lt=target_item.created).count()
            else:
                items_before = queryset.filter(id__lt=target_item.id).count()

        page_number = (items_before // limit) + 1
        return Response({'page': page_number})


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
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

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
                     'addresses__id_address1', 'addresses__id_address2',
                     'addresses__id_address3', 'addresses__dm_address1',
                     'addresses__dm_address2', 'addresses__dm_address3',
                     'contractorcontact__cell_phone', 'contractorcontact__home_phone',
                     'contractorcontact__other_phone', 'contractorcontact__email')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    # def perform_update(self, serializer):
    #     serializer.save(creator=self.request.user)


class SimpleContractorViewSet(ContractorViewSet):
    serializer_class = SimpleContractorSerializer
    pagination_class = PageNumberPaginationThreeThousand


class ContractFileViewSet(viewsets.ModelViewSet):
    """계약서 파일 업로드 관리"""
    queryset = ContractFile.objects.all()
    serializer_class = ContractFileSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ('contractor',)

    def get_queryset(self):
        queryset = super().get_queryset()
        contractor_id = self.request.query_params.get('contractor', None)
        if contractor_id:
            queryset = queryset.filter(contractor_id=contractor_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        # 파일 업데이트 시 creator는 유지하고 기타 필요한 로직 수행
        serializer.save()

    @action(detail=False, methods=['post'], url_path='upload/(?P<contractor_id>[^/.]+)')
    def upload_file(self, request, contractor_id=None):
        """특정 계약자에 대한 파일 업로드"""
        contractor = get_object_or_404(Contractor, pk=contractor_id)

        if 'file' not in request.FILES:
            return Response(
                {'error': '파일이 제공되지 않았습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(contractor=contractor, creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractDocumentViewSet(viewsets.ModelViewSet):
    """계약자 제출 서류 관리"""
    queryset = ContractDocument.objects.all()
    serializer_class = ContractDocumentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('contractor', 'required_document__sort', 'required_document', 'contractor__contract__project')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class ContractDocumentFileViewSet(viewsets.ModelViewSet):
    """계약자 제출 서류 첨부 파일 관리"""
    queryset = ContractDocumentFile.objects.all()
    serializer_class = ContractDocumentFileSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ('contract_document',)

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

    @action(detail=False, methods=['post'], url_path='upload/(?P<contract_document_id>[^/.]+)')
    def upload_file(self, request, contract_document_id=None):
        """특정 제출 서류에 대한 파일 업로드"""
        contract_document = get_object_or_404(ContractDocument, pk=contract_document_id)

        if 'file' not in request.FILES:
            return Response(
                {'error': '파일이 제공되지 않았습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(contract_document=contract_document, uploader=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContAddressViewSet(viewsets.ModelViewSet):
    queryset = ContractorAddress.objects.all()
    serializer_class = ContractorAddressSerializer
    filterset_fields = ('contractor', 'is_current')
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(creator=self.request.user)


class ContContactViewSet(viewsets.ModelViewSet):
    queryset = ContractorContact.objects.all()
    serializer_class = ContractorContactSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(creator=self.request.user)


class ContractorConsultationLogsViewSet(viewsets.ModelViewSet):
    """계약자 상담 내역 관리"""
    queryset = ContractorConsultationLogs.objects.select_related('consultant').all()
    serializer_class = ContractorConsultationLogsSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('contractor', 'status', 'category', 'channel')
    ordering = ['-consultation_date', '-created']

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user, consultant=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class SuccessionViewSet(viewsets.ModelViewSet):
    queryset = Succession.objects.all()
    serializer_class = SuccessionSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('contract__project',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

    @action(detail=False, methods=['get'], url_path='find-page')
    def find_page(self, request):
        """특정 ID의 Succession 항목이 몇 번째 페이지에 있는지 찾기"""
        highlight_id = request.query_params.get('highlight_id')
        project_id = request.query_params.get('project')

        if not highlight_id:
            return Response({'error': 'highlight_id parameter required'}, status=400)
        if not project_id:
            return Response({'error': 'project parameter required'}, status=400)

        try:
            highlight_id = int(highlight_id)
            project_id = int(project_id)
        except ValueError:
            return Response({'error': 'highlight_id and project must be integers'}, status=400)

        # 프로젝트별 전체 Succession 목록 가져오기
        queryset = Succession.objects.filter(contract__project_id=project_id)

        # 해당 ID가 존재하는지 확인
        try:
            target_item = queryset.get(pk=highlight_id)
        except Succession.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        # limit 파라미터 가져오기 (기본값은 10)
        limit = int(request.query_params.get('limit', 10))

        # Succession 모델의 정확한 ordering: ['-apply_date', '-trading_date', '-id']
        # 프로젝트별 전체 목록에서 target_item보다 앞에 있는 항목들의 개수 계산
        from django.db.models import Q

        items_before = queryset.filter(
            Q(apply_date__gt=target_item.apply_date) |
            Q(apply_date=target_item.apply_date, trading_date__gt=target_item.trading_date) |
            Q(apply_date=target_item.apply_date, trading_date=target_item.trading_date, id__gt=target_item.id)
        ).count()

        page_number = (items_before // limit) + 1

        return Response({'page': page_number})


class ContReleaseViewSet(viewsets.ModelViewSet):
    queryset = ContractorRelease.objects.all().order_by('-request_date', '-created')
    serializer_class = ContractorReleaseSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'status')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

    @action(detail=False, methods=['get'], url_path='find-page')
    def find_page(self, request):
        """특정 ID의 ContractorRelease 항목이 몇 번째 페이지에 있는지 찾기"""
        highlight_id = request.query_params.get('highlight_id')
        project_id = request.query_params.get('project')

        if not highlight_id:
            return Response({'error': 'highlight_id parameter required'}, status=400)
        if not project_id:
            return Response({'error': 'project parameter required'}, status=400)

        try:
            highlight_id = int(highlight_id)
            project_id = int(project_id)
        except ValueError:
            return Response({'error': 'highlight_id and project must be integers'}, status=400)

        # 프로젝트별 전체 ContractorRelease 목록 가져오기
        queryset = ContractorRelease.objects.filter(project_id=project_id)

        # 해당 ID가 존재하는지 확인
        try:
            target_item = queryset.get(pk=highlight_id)
        except ContractorRelease.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        # limit 파라미터 가져오기 (기본값은 10)
        limit = int(request.query_params.get('limit', 10))

        # ContractorRelease 모델의 정확한 ordering: ['-request_date', '-created']
        # 프로젝트별 전체 목록에서 target_item보다 앞에 있는 항목들의 개수 계산
        items_before = queryset.filter(
            Q(request_date__gt=target_item.request_date) |
            Q(request_date=target_item.request_date, created__gt=target_item.created)
        ).count()

        page_number = (items_before // limit) + 1

        return Response({'page': page_number})


# Contract Price Bulk Update API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_contract_prices(request):
    """
    프로젝트 내 모든 계약 가격 일괄 업데이트

    SalesPriceByGT 변경 후 기존 계약들에 새 가격 정책을 반영할 때 사용

    Request Body:
        {
            "project": <project_id>,
            "dry_run": <boolean, optional>,  // true일 경우 실제 업데이트 없이 미리보기만
            "uncontracted_order_group": <order_group_id, optional>  // 미계약 세대용 차수 ID
        }

    Response:
        {
            "success": true,
            "message": "업데이트 완료",
            "data": {
                "total_processed": 50,
                "updated_count": 45,
                "created_count": 5,
                "uncontracted_created_count": 20,  // 미계약 세대 ContractPrice 생성 수
                "updated_contracts": [1, 2, 3, ...],
                "errors": []
            }
        }
    """
    project_id = request.data.get('project')
    dry_run = request.data.get('dry_run', False)
    uncontracted_order_group_id = request.data.get('uncontracted_order_group')

    if not project_id:
        return Response({
            'success': False,
            'message': 'project parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Project with ID {project_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # 미계약 세대용 차수 검증
    order_group_for_uncontracted = None
    if uncontracted_order_group_id:
        try:
            order_group_for_uncontracted = OrderGroup.objects.get(
                pk=uncontracted_order_group_id,
                project=project
            )
        except OrderGroup.DoesNotExist:
            return Response({
                'success': False,
                'message': f'OrderGroup with ID {uncontracted_order_group_id} not found for project {project.name}'
            }, status=status.HTTP_404_NOT_FOUND)

    # ContractPriceBulkUpdateService는 이제 자동으로 프로젝트 기본 차수를 참조합니다
    service = ContractPriceBulkUpdateService(project, order_group_for_uncontracted)

    try:
        # 프로젝트 유효성 검증
        validation_result = service.validate_project()
        if not validation_result['is_valid']:
            return Response({
                'success': False,
                'message': '업데이트할 유효한 계약이 없습니다',
                'data': validation_result
            }, status=status.HTTP_400_BAD_REQUEST)

        if dry_run:
            # 미리보기 모드: 실제 업데이트 없이 대상 계약만 조회
            contracts = service.get_contracts_to_update()
            contract_list = [
                {
                    'id': contract.pk,
                    'serial_number': contract.serial_number,
                    'contractor_name': contract.contractor.name if hasattr(contract, 'contractor') else None,
                    'unit_type': contract.unit_type.name if contract.unit_type else None
                }
                for contract in contracts
            ]

            return Response({
                'success': True,
                'message': f'{len(contract_list)}개 계약이 업데이트 대상입니다 (미리보기)',
                'data': {
                    'total_contracts': len(contract_list),
                    'contracts': contract_list,
                    'project_info': validation_result
                }
            })

        else:
            # 실제 업데이트 실행
            result = service.update_all_contract_prices()

            # payment_amounts는 ContractPriceBulkUpdateService의 save() 호출로 이미 계산됨
            if result['errors']:
                return Response({
                    'success': True,
                    'message': f"부분적으로 완료됨. {result['updated_count'] + result['created_count']}개 성공, {len(result['errors'])}개 실패",
                    'data': result
                }, status=status.HTTP_206_PARTIAL_CONTENT)

            total_success = result['updated_count'] + result['created_count'] + result.get('uncontracted_created_count',
                                                                                           0)
            message_parts = [f"{result['updated_count'] + result['created_count']}개 계약가격 정보가 성공적으로 업데이트되었습니다"]

            if result.get('uncontracted_created_count', 0) > 0:
                message_parts.append(f"{result['uncontracted_created_count']}개 미계약 세대 계약가격 정보가 생성(수정) 되었습니다")

            return Response({
                'success': True,
                'message': ', '.join(message_parts),
                'data': result
            })

    except Exception as e:
        return Response({
            'success': False,
            'message': '업데이트 중 서버에 오류가 발생했습니다. 관리자에게 문의하세요.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contract_price_update_preview(request):
    """
    계약 가격 업데이트 미리보기

    Query Parameters:
        project: 프로젝트 ID
        uncontracted_order_group: 미계약 세대용 차수 ID (옵션)

    Response:
        프로젝트 정보와 업데이트 대상 계약 목록
    """
    project_id = request.GET.get('project')
    uncontracted_order_group_id = request.GET.get('uncontracted_order_group')

    if not project_id:
        return Response({
            'success': False,
            'message': 'project parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        project = Project.objects.get(pk=project_id)

        # 미계약 세대용 차수 검증
        order_group_for_uncontracted = None
        if uncontracted_order_group_id:
            try:
                order_group_for_uncontracted = OrderGroup.objects.get(
                    pk=uncontracted_order_group_id,
                    project=project
                )
            except OrderGroup.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'OrderGroup with ID {uncontracted_order_group_id} not found for project {project.name}'
                }, status=status.HTTP_404_NOT_FOUND)

        # ContractPriceBulkUpdateService는 이제 자동으로 프로젝트 기본 차수를 참조합니다
        service = ContractPriceBulkUpdateService(project, order_group_for_uncontracted)

        validation_result = service.validate_project()
        contracts = service.get_contracts_to_update()

        contract_list = []
        for contract in contracts[:10]:  # 최대 10개만 미리보기
            # 기존 가격
            current_price = getattr(contract.contractprice, 'price', None) \
                if hasattr(contract, 'contractprice') else None

            # 업데이트될 예정인 새로운 가격 계산
            try:
                house_unit = contract.key_unit.houseunit
            except (AttributeError, ObjectDoesNotExist):
                house_unit = None

            new_price_data = get_contract_price(contract, house_unit, True)
            new_price = new_price_data[0] if new_price_data else None

            contract_list.append({
                'id': contract.pk,
                'serial_number': contract.serial_number,
                'contractor_name': contract.contractor.name if hasattr(contract, 'contractor') else None,
                'unit_type': contract.unit_type.name if contract.unit_type else None,
                'current_price': current_price,
                'new_price': new_price,
                'price_changed': current_price != new_price if current_price and new_price else True
            })

        # 미계약 세대 정보
        uncontracted_info = {}
        # service.order_group_for_uncontracted를 사용하여 실제 사용될 차수 정보 표시
        if service.order_group_for_uncontracted:
            from items.models import HouseUnit
            uncontracted_houses = HouseUnit.objects.filter(
                unit_type__project=project,
            ).exclude(
                key_unit__contract__isnull=False,
                key_unit__contract__activation=True
            ).count()

            uncontracted_info = {
                'order_group_name': service.order_group_for_uncontracted.name,
                'order_group_id': service.order_group_for_uncontracted.pk,
                'estimated_uncontracted_count': uncontracted_houses,
                'is_project_default': order_group_for_uncontracted is None  # 프로젝트 기본 차수 사용 여부
            }

        return Response({
            'success': True,
            'message': '미리보기 조회 완료',
            'data': {
                'project_info': validation_result,
                'sample_contracts': contract_list,
                'total_contracts': contracts.count(),
                'showing_sample': len(contract_list),
                'uncontracted_info': uncontracted_info
            }
        })

    except Project.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Project with ID {project_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': '내부 서버 오류가 발생했습니다.'  # "An internal server error occurred." in Korean
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
