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
    CommissionClawbackSerializer, AgencyPayoutSerializer,
    AgencyPayoutContractDetailSerializer,
)
from sales.models import (
    SalesAgency, SalesTeam, SalesPerson, SalesPersonDocument, CommissionPolicy,
    ContractSalesAgent, SettlementPeriod, CommissionPayout,
    PayoutContractDetail, CommissionClawback, AgencyPayout, AgencyPayoutContractDetail,
)
from sales.services import generate_period_payouts
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
        'contract__contractor', 'contract__key_unit__houseunit__building_unit',
        'sales_person', 'team', 'policy'
    )
    serializer_class = ContractSalesAgentSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationCustomBasic
    filterset_fields = (
        'team__agency__project', 'contract__project', 'sales_person', 'team',
        'contract', 'is_settlement_approved'
    )
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

    @action(detail=True, methods=['post'], url_path='toggle-approval')
    def toggle_approval(self, request, pk=None):
        """수수료 정산 승인 / 보류 토글 또는 지정 액션"""
        agent_mapping = self.get_object()
        explicit_state = request.data.get('is_settlement_approved')
        if explicit_state is not None:
            new_state = bool(explicit_state)
        else:
            new_state = not agent_mapping.is_settlement_approved

        agent_mapping.is_settlement_approved = new_state
        if new_state:
            agent_mapping.approved_by = request.user
            agent_mapping.approved_at = timezone.now()
        else:
            note = request.data.get('approval_note')
            if note is not None:
                agent_mapping.approval_note = note.strip()
        agent_mapping.save()

        status_text = '승인' if new_state else '보류'
        return Response({
            'detail': f'정산 {status_text} 상태로 변경되었습니다.',
            'is_settlement_approved': agent_mapping.is_settlement_approved,
            'approval_note': agent_mapping.approval_note,
        }, status=status.HTTP_200_OK)


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
        정산 대상 기간 내 계약 실적을 집계하여 수수료 지급 명세를 자동 생성/갱신합니다.

        직영 대행사: CommissionPayout (개인별, 계층 수수료 자동 배분)
        외주 대행사: AgencyPayout    (대행사 단위, VAT 10% 자동 계산)
        """
        period = self.get_object()

        with transaction.atomic():
            result = generate_period_payouts(period)

        if result['total_contracts'] == 0:
            return Response({
                'detail': '해당 기간 내 정산 대상 계약 실적이 없습니다.',
                'total_contracts': 0,
            }, status=status.HTTP_200_OK)

        return Response({
            'detail': (
                f"직영 {result['direct_person_count']}명 / "
                f"외주 {result['agency_count']}개 대행사 — "
                f"총 {result['total_contracts']}건 정산 완료."
            ),
            'direct_person_count': result['direct_person_count'],
            'agency_count': result['agency_count'],
            'total_contracts': result['total_contracts'],
            'total_gross_amount': result['total_gross_amount'],
            'total_agency_amount': result['total_agency_amount'],
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

            # 회차 내 모든 지급 대상의 완료 여부에 따라 회차 상태 자동 동기화
            period = payout.period
            if period.status in ('2', '3'):
                remaining = period.payouts.exclude(pay_status='3').exists()
                if not remaining and period.status == '2':
                    period.status = '3'  # 전원 지급 완료
                    period.save()
                elif remaining and period.status == '3':
                    period.status = '2'  # 일부 보류/대기 시 확정 상태 복귀
                    period.save()

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


class AgencyPayoutViewSet(viewsets.ModelViewSet):
    """외주 대행사 수수료 지급 명세 ViewSet (시행사 → 대행사 지급)"""
    queryset = AgencyPayout.objects.all().select_related(
        'period__project', 'agency'
    ).prefetch_related('contract_details__contract')
    serializer_class = AgencyPayoutSerializer
    permission_classes = (IsAuthenticated, IbsModulePermission)
    pagination_class = PageNumberPaginationCustomBasic
    filterset_fields = ('period', 'period__project', 'agency', 'pay_status')
    search_fields = ('agency__name', 'account_holder', 'business_number')

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
        """대행사 지급 상태 업데이트 (승인 / 지급완료 / 보류)"""
        payout = self.get_object()
        pay_status = request.data.get('pay_status')
        if pay_status in ('1', '2', '3', '4'):
            payout.pay_status = pay_status
            if pay_status == '3' and not payout.paid_date:
                payout.paid_date = timezone.localdate()
            payout.save()
            return Response({'detail': '지급 상태가 업데이트되었습니다.', 'pay_status': pay_status})
        return Response({'detail': '올바르지 않은 상태값입니다.'}, status=status.HTTP_400_BAD_REQUEST)
