from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apiV1.pagination import PageNumberPaginationCustomBasic, PageNumberPaginationOneHundred
from apiV1.permissions.ibs_perms import IbsModulePermission
from apiV1.serializers.sales import (
    SalesAgencySerializer, SalesTeamSerializer, SalesPersonSerializer,
    SalesPersonDocumentSerializer, CommissionPolicySerializer,
    ContractSalesAgentSerializer, SettlementPeriodSerializer,
    CommissionPayoutSerializer, PayoutContractDetailSerializer,
    CommissionClawbackSerializer
)
from sales.models import (
    SalesAgency, SalesTeam, SalesPerson, SalesPersonDocument, CommissionPolicy,
    ContractSalesAgent, SettlementPeriod, CommissionPayout,
    PayoutContractDetail, CommissionClawback
)
from work.models import IssueProject


def get_accessible_project_ids(user):
    return IssueProject.objects.filter(members__user=user).values_list('project__id', flat=True)


class SalesAgencyViewSet(viewsets.ModelViewSet):
    """분양 대행사 ViewSet"""
    queryset = SalesAgency.objects.all()
    serializer_class = SalesAgencySerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('project', 'is_direct_managed', 'is_active')
    search_fields = ('name', 'ceo_name', 'business_number')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return 'sales.read'
        return 'sales.manage'


class SalesTeamViewSet(viewsets.ModelViewSet):
    """영업 조직 (본부/팀) ViewSet"""
    queryset = SalesTeam.objects.all().select_related('agency', 'parent')
    serializer_class = SalesTeamSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('agency', 'agency__project', 'parent', 'is_active')
    search_fields = ('name',)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(agency__project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return 'sales.read'
        return 'sales.manage'


class SalesPersonViewSet(viewsets.ModelViewSet):
    """영업 인력 (분양상담사/팀장/본부장) ViewSet"""
    queryset = SalesPerson.objects.all().select_related('team__agency', 'user').prefetch_related('documents')
    serializer_class = SalesPersonSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('team', 'team__agency__project', 'duty', 'status', 'tax_type')
    search_fields = ('name', 'phone', 'id_number', 'account_holder')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(team__agency__project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return 'sales.read'
        return 'sales.manage'


class CommissionPolicyViewSet(viewsets.ModelViewSet):
    """수수료 정책 ViewSet"""
    queryset = CommissionPolicy.objects.all().select_related('project', 'order_group', 'unit_type')
    serializer_class = CommissionPolicySerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('project', 'order_group', 'unit_type', 'pay_condition', 'is_active')
    search_fields = ('name',)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        return 'sales.policy'


class ContractSalesAgentViewSet(viewsets.ModelViewSet):
    """계약 영업 담당자 매핑 ViewSet"""
    queryset = ContractSalesAgent.objects.all().select_related(
        'contract__contractor', 'contract__key_unit__houseunit__building',
        'sales_person', 'team', 'policy'
    )
    serializer_class = ContractSalesAgentSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationCustomBasic
    filterset_fields = ('team__agency__project', 'contract__project', 'sales_person', 'team', 'contract')
    search_fields = ('contract__serial_number', 'sales_person__name', 'mgm_name')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(contract__project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return 'sales.read'
        return 'sales.manage'


class SettlementPeriodViewSet(viewsets.ModelViewSet):
    """수수료 정산 회차 ViewSet"""
    queryset = SettlementPeriod.objects.all().select_related('project', 'created_by')
    serializer_class = SettlementPeriodSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationCustomBasic
    filterset_fields = ('project', 'status')
    search_fields = ('title',)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return 'sales.read'
        return 'sales.settle'

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='generate-payouts')
    def generate_payouts(self, request, pk=None):
        """
        정산 대상 기간 내의 계약 실적을 자동 집계하여
        개인별 수수료 지급 명세(CommissionPayout) 및 계약 상세를 자동 생성/갱신합니다.
        """
        period = self.get_object()

        with transaction.atomic():
            # 1. 정산 대상 기간 내의 계약 매핑 조회 (해당 프로젝트)
            mappings = ContractSalesAgent.objects.filter(
                contract__project=period.project,
                contract_date__gte=period.start_date,
                contract_date__lte=period.end_date,
            ).select_related('contract', 'sales_person', 'policy', 'contract__unit_type')

            if not mappings.exists():
                return Response({
                    'detail': '해당 기간 내 정산 대상 계약 실적이 없습니다.',
                    'count': 0
                }, status=status.HTTP_200_OK)

            # 2. 영업직원별 계약 그룹화
            person_contracts = {}
            for m in mappings:
                agent = m.sales_person
                if agent.pk not in person_contracts:
                    person_contracts[agent.pk] = {
                        'agent': agent,
                        'contracts': []
                    }

                # 적용할 수수료 정책 산출
                policy = m.policy
                if not policy:
                    # 유니트 타입에 맞는 활성 정책 검색
                    policy = CommissionPolicy.objects.filter(
                        project=period.project,
                        unit_type=m.contract.unit_type,
                        is_active=True
                    ).first() or CommissionPolicy.objects.filter(
                        project=period.project,
                        unit_type__isnull=True,
                        is_active=True
                    ).first()

                fee = 0
                if policy:
                    if agent.duty == '1':  # 상담사
                        fee = policy.agent_fee
                    elif agent.duty == '2':  # 팀장
                        fee = policy.leader_fee
                    elif agent.duty in ('3', '4'):  # 본부장
                        fee = policy.director_fee
                    else:
                        fee = policy.agent_fee

                person_contracts[agent.pk]['contracts'].append({
                    'contract': m.contract,
                    'role_type': 'agent' if agent.duty == '1' else ('leader' if agent.duty == '2' else 'director'),
                    'fee': fee
                })

            # 3. 개인별 Payout 및 PayoutContractDetail 생성/업데이트
            total_contracts = 0
            created_count = 0

            for agent_id, data in person_contracts.items():
                agent = data['agent']
                c_list = data['contracts']
                comm_sum = sum(c['fee'] for c in c_list)
                c_count = len(c_list)
                total_contracts += c_count

                # 미상계된 환수금(Clawback) 확인
                clawbacks = CommissionClawback.objects.filter(
                    sales_person=agent,
                    is_settled=False
                )
                clawback_sum = clawbacks.aggregate(total=Sum('amount'))['total'] or 0

                payout, created = CommissionPayout.objects.get_or_create(
                    period=period,
                    sales_person=agent,
                    defaults={
                        'contract_count': c_count,
                        'commission_amount': comm_sum,
                        'deduction_amount': clawback_sum,
                        'bank_name': agent.bank_name,
                        'account_number': agent.account_number,
                        'account_holder': agent.account_holder,
                    }
                )

                if not created:
                    payout.contract_count = c_count
                    payout.commission_amount = comm_sum
                    payout.deduction_amount = clawback_sum
                    payout.save()

                # 기존 계약 상세 삭제 후 재생성
                payout.contract_details.all().delete()
                for c in c_list:
                    PayoutContractDetail.objects.create(
                        payout=payout,
                        contract=c['contract'],
                        role_type=c['role_type'],
                        unit_fee=c['fee']
                    )

                # 환수금 상계 처리 연결
                if clawback_sum > 0:
                    clawbacks.update(is_settled=True, settled_payout=payout)

                created_count += 1

            # 4. 회차 전체 합계 갱신
            payouts = period.payouts.all()
            period.total_contracts = total_contracts
            period.total_gross_amount = payouts.aggregate(total=Sum('gross_amount'))['total'] or 0
            period.total_tax_amount = payouts.aggregate(total=Sum('total_tax'))['total'] or 0
            period.total_net_amount = payouts.aggregate(total=Sum('net_amount'))['total'] or 0
            period.save()

            return Response({
                'detail': f'{created_count}명의 영업 인력에 대해 {total_contracts}건의 계약 정산이 완료되었습니다.',
                'total_contracts': total_contracts,
                'total_gross_amount': period.total_gross_amount,
                'total_net_amount': period.total_net_amount,
            }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='confirm-settlement')
    def confirm_settlement(self, request, pk=None):
        """정산 회차 확정 (상태: 정산 확정)"""
        period = self.get_object()
        period.status = '2'  # 확정
        period.save()
        return Response({'detail': f'[{period.title}] 정산이 확정되었습니다.'})


class CommissionPayoutViewSet(viewsets.ModelViewSet):
    """개인별 수수료 지급 명세 ViewSet"""
    queryset = CommissionPayout.objects.all().select_related(
        'period__project', 'sales_person__team'
    ).prefetch_related('contract_details__contract')
    serializer_class = CommissionPayoutSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationCustomBasic
    filterset_fields = ('period', 'period__project', 'sales_person', 'pay_status')
    search_fields = ('sales_person__name', 'account_holder')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(period__project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        if self.action == 'update_pay_status':
            return 'sales.payout'
        if self.action in ('list', 'retrieve'):
            return 'sales.read'
        return 'sales.settle'

    @action(detail=True, methods=['post'], url_path='update-pay-status')
    def update_pay_status(self, request, pk=None):
        """지급 상태 업데이트 (승인 / 지급완료 / 보류)"""
        payout = self.get_object()
        pay_status = request.data.get('pay_status')
        if pay_status in ('1', '2', '3', '4'):
            payout.pay_status = pay_status
            if pay_status == '3' and not payout.paid_date:
                payout.paid_date = timezone.localdate()
            payout.save()
            return Response({'detail': '지급 상태가 업데이트되었습니다.', 'pay_status': pay_status})
        return Response({'detail': '올바르지 않은 상태값입니다.'}, status=status.HTTP_400_BAD_REQUEST)


class CommissionClawbackViewSet(viewsets.ModelViewSet):
    """수수료 환수 관리 ViewSet"""
    queryset = CommissionClawback.objects.all().select_related('contract', 'sales_person')
    serializer_class = CommissionClawbackSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationCustomBasic
    filterset_fields = ('contract', 'sales_person', 'is_settled')
    search_fields = ('sales_person__name', 'contract__serial_number')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(contract__project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return 'sales.read'
        return 'sales.settle'


class SalesPersonDocumentViewSet(viewsets.ModelViewSet):
    """영업 인력 제출 서류 ViewSet"""
    queryset = SalesPersonDocument.objects.all().select_related(
        'sales_person__team__agency__project', 'verified_by', 'uploader'
    )
    serializer_class = SalesPersonDocumentSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationCustomBasic
    filterset_fields = (
        'sales_person', 'sales_person__team__agency__project',
        'doc_type', 'is_verified'
    )
    search_fields = ('title', 'file_name', 'sales_person__name')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(sales_person__team__agency__project_id__in=get_accessible_project_ids(user))

    @property
    def required_permission(self):
        if self.action in ('list', 'retrieve'):
            return 'sales.read'
        return 'sales.manage'

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

    @action(detail=True, methods=['post'], url_path='verify')
    def verify_document(self, request, pk=None):
        """서류 진위 검증 처리 (토글 또는 검증 확정)"""
        doc = self.get_object()
        is_verified = request.data.get('is_verified', True)
        if isinstance(is_verified, str):
            is_verified = is_verified.lower() in ('true', '1', 'yes')

        doc.is_verified = is_verified
        if is_verified:
            doc.verified_at = timezone.now()
            doc.verified_by = request.user
        else:
            doc.verified_at = None
            doc.verified_by = None
        doc.save()

        status_str = '검증 완료' if is_verified else '검증 취소'
        return Response({
            'detail': f'[{doc.title}] 서류가 {status_str} 상태로 변경되었습니다.',
            'is_verified': doc.is_verified,
            'verified_at': doc.verified_at,
            'verified_by_name': request.user.username if is_verified else None
        }, status=status.HTTP_200_OK)

