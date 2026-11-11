import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.db.models import Sum, F, Case, When, Count, Q, ProtectedError
from django.utils import timezone
from django_filters import CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework import permissions
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error

from apiV1.permissions._utils import get_project_ids_with_permission
from apiV1.permissions.ibs_perms import IbsModulePermission, HqProjectModulePermission
from ledger.models import (
    BankCode, CompanyBankAccount, ProjectBankAccount,
    CompanyAccount, ProjectAccount, Affiliate,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    CompanyLedgerCalculation, ProjectLedgerCalculation,
)
from ledger.services.company_transaction import get_company_transactions, prefetch_company_transactions
from ledger.services.project_transaction import get_project_transactions, prefetch_project_transactions
from work.models import IssueProject
from ..pagination import PageNumberPaginationFifteen, PageNumberPaginationFifty, PageNumberPaginationThreeHundred
from ..permissions import IsProjectStaffOrReadOnly
from ..serializers.ledger import (
    CompanyAccountSerializer, ProjectAccountSerializer, AffiliateSerializer,
    AccountSearchResultSerializer, LedgerBankCodeSerializer,
    LedgerCompanyBankAccountSerializer, LedgerProjectBankAccountSerializer,
    CompanyBankTransactionSerializer, ProjectBankTransactionSerializer,
    CompanyAccountingEntrySerializer, ProjectAccountingEntrySerializer,
    CompanyCompositeTransactionSerializer, ProjectCompositeTransactionSerializer,
    CompanyLedgerCalculationSerializer, ProjectLedgerCalculationSerializer, CompanyLedgerLastDealDateSerializer,
    ProjectLedgerLastDealDateSerializer,
)


def get_today_str():
    return timezone.localdate().strftime('%Y-%m-%d')


class IsLedgerMasterManagerOrReadOnly(permissions.BasePermission):
    """은행 코드 등 공통 마스터는 인증 사용자 조회를 허용하고, 변경은 관리자/원장 관리 권한자에게만 허용"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return True
        hq_perms = HqProjectModulePermission._get_all_hq_user_permissions(request.user)
        if 'hq.ledger.manage' in hq_perms or 'ledger.com_manage' in hq_perms:
            return True
        return bool(get_project_ids_with_permission(request.user, 'ledger.manage'))


class IsProjectAccountManagerOrReadOnly(permissions.BasePermission):
    """프로젝트 계정과목 조회는 프로젝트 스태프에게 허용하고, 변경은 슈퍼유저·work_manager·ledger.manage 보유자에게만 허용"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return True
        return bool(get_project_ids_with_permission(request.user, 'ledger.manage'))


# ============================================
# Bank Account ViewSets
# ============================================

class LedgerBankCodeViewSet(viewsets.ModelViewSet):
    """은행 코드 ViewSet"""
    queryset = BankCode.objects.all()
    serializer_class = LedgerBankCodeSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IsLedgerMasterManagerOrReadOnly)
    pagination_class = PageNumberPaginationFifty
    search_fields = ('code', 'name')


class LedgerCompanyBankAccountViewSet(viewsets.ModelViewSet):
    """본사 은행 계좌 ViewSet"""
    queryset = CompanyBankAccount.objects.select_related('bankcode', 'company', 'depart').all()
    serializer_class = LedgerCompanyBankAccountSerializer
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('company', 'depart', 'bankcode', 'is_hide', 'inactive')
    search_fields = ('alias_name', 'number', 'holder')

    @property
    def required_permission(self):
        return 'hq.ledger.read' if self.action in ('list', 'retrieve') else 'hq.ledger.manage'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser:
            return qs
        return qs.filter(company_id__in=get_accessible_company_ids(user))

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError('거래 내역이 존재하는 은행 계좌는 삭제할 수 없습니다. (비활성화 또는 숨김 처리하세요.)')


def get_accessible_company_ids(user):
    """[C-1] 사용자가 접근 가능한 소속 회사 ID 목록을 반환합니다 (Staff 소속 또는 본사 워크스페이스 멤버)"""
    if not user or not user.is_authenticated:
        return []
    company_ids = set()
    staff = getattr(user, 'staff', None)
    if staff and staff.company_id:
        company_ids.add(staff.company_id)
    member_companies = IssueProject.objects.filter(
        type='1',
        members__user=user,
        company__isnull=False
    ).values_list('company_id', flat=True)
    company_ids.update(member_companies)
    return list(company_ids)


def get_accessible_project_ids(user, required_perm: str = 'ledger.read'):
    """[RLS] 사용자가 특정 권한(기본: ledger.read)을 보유한 프로젝트 ID 목록 반환"""
    return get_project_ids_with_permission(user, required_perm)



class LedgerProjectBankAccountViewSet(viewsets.ModelViewSet):
    """프로젝트 은행 계좌 ViewSet"""
    queryset = ProjectBankAccount.objects.select_related('bankcode', 'project').all()
    serializer_class = LedgerProjectBankAccountSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('project', 'bankcode', 'is_hide', 'inactive', 'directpay', 'is_imprest')
    search_fields = ('alias_name', 'number', 'holder', 'project__name')

    @property
    def required_permission(self):
        return {
            'list': 'ledger.read',
            'retrieve': 'ledger.read',
            'create': 'ledger.manage',
            'update': 'ledger.manage',
            'partial_update': 'ledger.manage',
            'destroy': 'ledger.manage',
        }.get(self.action, 'ledger.read')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError('거래 내역이 존재하는 은행 계좌는 삭제할 수 없습니다. (비활성화 또는 숨김 처리하세요.)')


# ============================================
# Account ViewSets
# ============================================

class CompanyAccountFilter(FilterSet):
    """본사 계정 과목 필터"""
    category = CharFilter(field_name='category', lookup_expr='exact')
    direction = CharFilter(field_name='direction', lookup_expr='exact')
    parent = CharFilter(field_name='parent_id', lookup_expr='exact')

    class Meta:
        model = CompanyAccount
        fields = ['category', 'direction', 'parent', 'is_category_only', 'is_active']


class CompanyAccountViewSet(viewsets.ModelViewSet):
    """본사 계정 과목 ViewSet"""
    queryset = CompanyAccount.objects.select_related('parent').annotate(
        children_count_annotated=Count('children', filter=Q(children__is_active=True))
    ).all()
    serializer_class = CompanyAccountSerializer
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = CompanyAccountFilter
    search_fields = ('code', 'name', 'description')
    ordering_fields = ('code', 'name', 'order', 'created_at')
    ordering = ('code', 'order')

    @property
    def required_permission(self):
        return 'hq.ledger.read' if self.action in ('list', 'retrieve', 'search_with_parents', 'tree') else 'hq.ledger.manage'

    @action(detail=False, methods=['get'])
    def search_with_parents(self, request):
        """
        계정 검색 (부모 계정 포함)

        하위 계정이 검색 결과에 포함되면 해당 부모 계정들도 결과에 포함시킵니다.
        분류 전용 계정의 경우 동적으로 computed_direction을 계산하여 표시합니다.
        """
        query = request.query_params.get('q', '')
        direction = request.query_params.get('direction', '')

        if not query:
            return Response({'results': []})

        # 1. 직접 매치되는 계정들 검색
        matched_accounts = CompanyAccount.objects.filter(
            name__icontains=query,
            is_active=True
        ).select_related('parent')

        # 2. direction 필터링 (computed_direction 기반)
        if direction:
            filtered_accounts = []
            for account in matched_accounts:
                computed = account.get_computed_direction()
                if direction == 'both' or computed == direction or computed == 'both':
                    filtered_accounts.append(account)
            matched_accounts = filtered_accounts

        # 3. 매치된 계정들의 모든 부모 계정들 수집
        parent_accounts = set()
        for account in matched_accounts:
            parents = account.get_ancestors()
            parent_accounts.update(parents)

        # 4. 결과 조합 및 직렬화
        results = []

        # 직접 매치된 계정들
        for account in matched_accounts:
            results.append({
                'pk': account.pk,
                'code': account.code,
                'name': account.name,
                'full_path': account.get_full_path(),
                'computed_direction': account.get_computed_direction(),
                'computed_direction_display': account.get_direction_display_computed(),
                'is_category_only': account.is_category_only,
                'is_parent_of_matches': False,
                'match_reason': '직접 매치'
            })

        # 부모 계정들
        for parent in parent_accounts:
            # direction 필터링 적용
            if direction:
                computed = parent.get_computed_direction()
                if not (direction == 'both' or computed == direction or computed == 'both'):
                    continue

            results.append({
                'pk': parent.pk,
                'code': parent.code,
                'name': parent.name,
                'full_path': parent.get_full_path(),
                'computed_direction': parent.get_computed_direction(),
                'computed_direction_display': parent.get_direction_display_computed(),
                'is_category_only': parent.is_category_only,
                'is_parent_of_matches': True,
                'match_reason': '상위 계정'
            })

        # 중복 제거 (pk 기준)
        unique_results = {}
        for result in results:
            unique_results[result['pk']] = result

        # code 순으로 정렬
        final_results = sorted(unique_results.values(), key=lambda x: x['code'])

        return Response({
            'results': AccountSearchResultSerializer(final_results, many=True).data,
            'count': len(final_results)
        })

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """계정 트리 구조 조회"""
        category = request.query_params.get('category')

        queryset = CompanyAccount.objects.select_related('parent').filter(is_active=True)
        if category:
            queryset = queryset.filter(category=category)

        accounts = queryset.order_by('code', 'order')
        return Response(self.get_serializer(accounts, many=True).data)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError('하위 계정 또는 거래 분개가 연결된 계정과목은 삭제할 수 없습니다. (비활성화 처리하세요.)')


class ProjectAccountFilter(FilterSet):
    """프로젝트 계정 과목 필터"""
    category = CharFilter(field_name='category', lookup_expr='exact')
    direction = CharFilter(field_name='direction', lookup_expr='exact')
    parent = CharFilter(field_name='parent_id', lookup_expr='exact')

    class Meta:
        model = ProjectAccount
        fields = ('category', 'direction', 'parent', 'is_category_only', 'is_active',
                  'is_payment', 'requires_contract', 'is_related_contractor')


class ProjectAccountViewSet(viewsets.ModelViewSet):
    """프로젝트 계정 과목 ViewSet"""
    queryset = ProjectAccount.objects.select_related('parent').annotate(
        children_count_annotated=Count('children', filter=Q(children__is_active=True))
    ).all()
    serializer_class = ProjectAccountSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IsProjectAccountManagerOrReadOnly)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = ProjectAccountFilter
    search_fields = ('code', 'name', 'description')
    ordering_fields = ('code', 'name', 'order', 'created_at')
    ordering = ('code', 'order')

    @action(detail=False, methods=['get'])
    def search_with_parents(self, request):
        """
        계정 검색 (부모 계정 포함)

        하위 계정이 검색 결과에 포함되면 해당 부모 계정들도 결과에 포함시킵니다.
        분류 전용 계정의 경우 동적으로 computed_direction을 계산하여 표시합니다.
        """
        query = request.query_params.get('q', '')
        direction = request.query_params.get('direction', '')
        is_payment = request.query_params.get('is_payment')
        requires_contract = request.query_params.get('requires_contract')

        if not query:
            return Response({'results': []})

        # 1. 직접 매치되는 계정들 검색
        matched_accounts = ProjectAccount.objects.filter(
            name__icontains=query,
            is_active=True
        ).select_related('parent')

        # 2. 프로젝트 특수 필터링
        if is_payment is not None:
            is_payment_bool = is_payment.lower() in ('true', '1', 'yes')
            matched_accounts = matched_accounts.filter(is_payment=is_payment_bool)

        if requires_contract is not None:
            requires_contract_bool = requires_contract.lower() in ('true', '1', 'yes')
            matched_accounts = matched_accounts.filter(requires_contract=requires_contract_bool)

        # 3. direction 필터링 (computed_direction 기반)
        if direction:
            filtered_accounts = []
            for account in matched_accounts:
                computed = account.get_computed_direction()
                if direction == 'both' or computed == direction or computed == 'both':
                    filtered_accounts.append(account)
            matched_accounts = filtered_accounts

        # 4. 매치된 계정들의 모든 부모 계정들 수집
        parent_accounts = set()
        for account in matched_accounts:
            parents = account.get_ancestors()
            parent_accounts.update(parents)

        # 5. 결과 조합 및 직렬화
        results = []

        # 직접 매치된 계정들
        for account in matched_accounts:
            results.append({
                'pk': account.pk,
                'code': account.code,
                'name': account.name,
                'full_path': account.get_full_path(),
                'computed_direction': account.get_computed_direction(),
                'computed_direction_display': account.get_direction_display_computed(),
                'is_category_only': account.is_category_only,
                'is_parent_of_matches': False,
                'match_reason': '직접 매치',
                'is_payment': account.is_payment,
                'requires_contract': account.requires_contract,
            })

        # 부모 계정들
        for parent in parent_accounts:
            # direction 필터링 적용
            if direction:
                computed = parent.get_computed_direction()
                if not (direction == 'both' or computed == direction or computed == 'both'):
                    continue

            results.append({
                'pk': parent.pk,
                'code': parent.code,
                'name': parent.name,
                'full_path': parent.get_full_path(),
                'computed_direction': parent.get_computed_direction(),
                'computed_direction_display': parent.get_direction_display_computed(),
                'is_category_only': parent.is_category_only,
                'is_parent_of_matches': True,
                'match_reason': '상위 계정',
                'is_payment': parent.is_payment,
                'requires_contract': parent.requires_contract,
            })

        # 중복 제거 (pk 기준)
        unique_results = {}
        for result in results:
            unique_results[result['pk']] = result

        # code 순으로 정렬
        final_results = sorted(unique_results.values(), key=lambda x: x['code'])

        return Response({
            'results': AccountSearchResultSerializer(final_results, many=True).data,
            'count': len(final_results)
        })

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """계정 트리 구조 조회"""
        category = request.query_params.get('category')

        queryset = ProjectAccount.objects.select_related('parent').filter(is_active=True)
        if category:
            queryset = queryset.filter(category=category)

        accounts = queryset.order_by('code', 'order')
        return Response(self.get_serializer(accounts, many=True).data)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError('하위 계정 또는 거래 분개가 연결된 계정과목은 삭제할 수 없습니다. (비활성화 처리하세요.)')

    @action(detail=False, methods=['get'])
    def payment_accounts(self, request):
        """분양대금 관련 계정만 조회"""
        accounts = ProjectAccount.objects.filter(
            is_payment=True,
            is_active=True
        ).select_related('parent').order_by('code', 'order')

        return Response(self.get_serializer(accounts, many=True).data)

    @action(detail=False, methods=['get'])
    def contract_accounts(self, request):
        """공급계약 관련 계정만 조회"""
        accounts = ProjectAccount.objects.filter(
            requires_contract=True,
            is_active=True
        ).select_related('parent').order_by('code', 'order')

        return Response(self.get_serializer(accounts, many=True).data)


# ============================================
# Affiliate ViewSet
# ============================================

class AffiliateFilter(FilterSet):
    """관계회사/프로젝트 필터"""
    sort = CharFilter(field_name='sort', lookup_expr='exact')

    class Meta:
        model = Affiliate
        fields = ['sort', 'company', 'project']


class AffiliateViewSet(viewsets.ModelViewSet):
    """관계회사/프로젝트 ViewSet"""
    queryset = Affiliate.objects.select_related('company', 'project').all()
    serializer_class = AffiliateSerializer
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = AffiliateFilter
    search_fields = ('description', 'company__name', 'project__name')

    @property
    def required_permission(self):
        return 'hq.ledger.read' if self.action in ('list', 'retrieve') else 'hq.ledger.manage'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser:
            return qs
        company_ids = get_accessible_company_ids(user)
        project_ids = get_accessible_project_ids(user)
        return qs.filter(
            Q(sort='company', company_id__in=company_ids) |
            Q(sort='project', project_id__in=project_ids)
        )

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError('회계 분개에 사용 중인 관계회사/프로젝트 항목은 삭제할 수 없습니다.')


# ============================================
# Bank Transaction ViewSets
# ============================================


class CompanyBankTransactionViewSet(viewsets.ModelViewSet):
    """본사 은행 거래 ViewSet"""
    queryset = CompanyBankTransaction.objects.all()
    serializer_class = CompanyBankTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)
    pagination_class = PageNumberPaginationFifteen

    @property
    def required_permission(self):
        return {
            'list': 'hq.ledger.read',
            'retrieve': 'hq.ledger.read',
            'create': 'hq.ledger.create',
            'update': 'hq.ledger.update',
            'partial_update': 'hq.ledger.update',
            'destroy': 'hq.ledger.delete',
        }.get(self.action, 'hq.ledger.read')

    def get_queryset(self):
        """
        [C-1] 요청 action에 따라 쿼리셋을 분기하되, 항상 소속 회사 RLS 필터를 적용하여 IDOR 차단
        """
        user = self.request.user
        qs = super().get_queryset().select_related(
            'company', 'bank_account', 'sort', 'creator'
        )
        if not user.is_superuser:
            qs = qs.filter(company_id__in=get_accessible_company_ids(user))

        if self.action == 'list':
            return get_company_transactions(self.request.query_params, base_qs=qs)
        return qs

    def _has_hq_manage_perm(self, user):
        if user.is_superuser or getattr(user, 'work_manager', False):
            return True
        user_perms = HqProjectModulePermission._get_all_hq_user_permissions(user)
        return 'hq.ledger.manage' in user_perms or 'ledger.com_manage' in user_perms

    def _validate_company_settlement_lock(self, company_id, deal_date, action_label):
        if not company_id or not deal_date:
            return
        try:
            cal = CompanyLedgerCalculation.objects.get(company_id=company_id)
            if cal.calculated and deal_date <= cal.calculated and not self._has_hq_manage_perm(self.request.user):
                raise serializers.ValidationError(f'정산 마감일({cal.calculated}) 이전의 거래는 {action_label}할 수 없습니다.')
        except CompanyLedgerCalculation.DoesNotExist:
            pass

    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        company_id = company.pk if hasattr(company, 'pk') else company
        deal_date = serializer.validated_data.get('deal_date')
        self._validate_company_settlement_lock(company_id, deal_date, '생성')
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.instance
        self._validate_company_settlement_lock(instance.company_id, instance.deal_date, '수정')
        new_deal_date = serializer.validated_data.get('deal_date', instance.deal_date)
        self._validate_company_settlement_lock(instance.company_id, new_deal_date, '수정')
        serializer.save(updator=self.request.user)

    def perform_destroy(self, instance):
        self._validate_company_settlement_lock(instance.company_id, instance.deal_date, '삭제')
        instance.delete()

    def list(self, request, *args, **kwargs):
        """accounting_entries N+1 방지를 위한 수동 prefetch"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        instances = page if page is not None else list(queryset)

        prefetch_company_transactions(instances)

        serializer = self.get_serializer(instances, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def validate_balance(self, request, pk=None):
        """거래 금액 균형 검증"""
        instance = self.get_object()
        result = instance.validate_accounting_entries()
        return Response(result)

    @action(detail=False, methods=['get'])
    def balance_by_account(self, request):
        """계좌별 잔액 조회 (누적 + 당일 입출금)"""
        date = request.query_params.get('date', get_today_str())
        company = request.query_params.get('company')
        is_balance = request.query_params.get('is_balance', '')

        queryset = CompanyBankTransaction.objects.filter(deal_date__lte=date).order_by('bank_account')
        user = request.user
        if not user.is_superuser:
            accessible = get_accessible_company_ids(user)
            if company:
                try:
                    c_id = int(company)
                    if c_id not in accessible:
                        queryset = queryset.none()
                    else:
                        queryset = queryset.filter(company_id=c_id)
                except (ValueError, TypeError):
                    queryset = queryset.none()
            else:
                queryset = queryset.filter(company_id__in=accessible)
        elif company:
            queryset = queryset.filter(company_id=company)

        result = queryset.values(
            bank_acc=F('bank_account__alias_name'),
            bank_num=F('bank_account__number')
        ).annotate(
            # 누적 합계
            inc_sum=Sum(Case(
                When(sort_id=1, then=F('amount')),  # 1 = 입금
                default=0
            )),
            out_sum=Sum(Case(
                When(sort_id=2, then=F('amount')),  # 2 = 출금
                default=0
            )),
            # 당일 합계
            date_inc=Sum(Case(
                When(sort_id=1, deal_date=date, then=F('amount')),
                default=0
            )),
            date_out=Sum(Case(
                When(sort_id=2, deal_date=date, then=F('amount')),
                default=0
            ))
        ).annotate(
            balance=F('inc_sum') - F('out_sum')
        )

        if is_balance == 'true':
            result = result.exclude(balance=0)

        return Response(list(result))

    @action(detail=False, methods=['get'])
    def daily_transactions(self, request):
        """특정일 거래 내역 조회"""
        date = request.query_params.get('date', get_today_str())
        company = request.query_params.get('company')

        if not company:
            return Response(
                {'error': 'company parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transactions = list(self.get_queryset().filter(
            company_id=company,
            deal_date=date
        ).select_related(
            'bank_account', 'sort', 'creator'
        ).order_by('sort_id', 'created_at'))

        prefetch_company_transactions(transactions)

        serializer = CompanyBankTransactionSerializer(transactions, many=True)
        return Response({'results': serializer.data})

    @action(detail=False, methods=['get'])
    def last_deal(self, request):
        """최종 거래 일자 조회"""
        company = request.query_params.get('company')

        if not company:
            return Response(
                {'error': 'company parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        last_transaction = self.get_queryset().filter(
            company_id=company
        ).order_by('-deal_date', '-created_at').first()

        if last_transaction:
            return Response({'results': [{'deal_date': last_transaction.deal_date}]})
        return Response({'results': []})


class ProjectBankTransactionViewSet(viewsets.ModelViewSet):
    """프로젝트 거래 내역 ViewSet"""
    queryset = ProjectBankTransaction.objects.all()
    serializer_class = ProjectBankTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationFifteen

    @property
    def required_permission(self):
        return {
            'list': 'ledger.read',
            'retrieve': 'ledger.read',
            'create': 'ledger.create',
            'update': 'ledger.update',
            'partial_update': 'ledger.update',
            'destroy': 'ledger.delete',
            'validate_balance': 'ledger.read',
            'balance_by_account': 'ledger.read',
        }.get(self.action, 'ledger.read')

    def get_queryset(self):
        """기본 상세 조회 및 생성/수정용 쿼리셋 반환"""
        user = self.request.user
        qs = super().get_queryset().select_related(
            'project', 'bank_account', 'sort', 'creator'
        )
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    def _has_project_manage_perm(self, user, project_id):
        if user.is_superuser or getattr(user, 'work_manager', False):
            return True
        try:
            from project.models import Project
            prj = Project.objects.select_related('issue_project').get(pk=project_id)
            if hasattr(prj, 'issue_project') and prj.issue_project:
                user_perms = set(prj.issue_project.get_user_permissions(user))
                return 'ledger.manage' in user_perms
        except Exception:
            pass
        return False

    def _validate_project_settlement_lock(self, project_id, deal_date, action_label):
        if not project_id or not deal_date:
            return
        try:
            cal = ProjectLedgerCalculation.objects.get(project_id=project_id)
            if cal.calculated and deal_date <= cal.calculated and not self._has_project_manage_perm(self.request.user, project_id):
                raise serializers.ValidationError(f'정산 마감일({cal.calculated}) 이전의 거래는 {action_label}할 수 없습니다.')
        except ProjectLedgerCalculation.DoesNotExist:
            pass

    def perform_create(self, serializer):
        project = serializer.validated_data.get('project')
        project_id = project.pk if hasattr(project, 'pk') else project
        deal_date = serializer.validated_data.get('deal_date')
        self._validate_project_settlement_lock(project_id, deal_date, '생성')
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.instance
        self._validate_project_settlement_lock(instance.project_id, instance.deal_date, '수정')
        new_deal_date = serializer.validated_data.get('deal_date', instance.deal_date)
        self._validate_project_settlement_lock(instance.project_id, new_deal_date, '수정')
        serializer.save(updator=self.request.user)

    def perform_destroy(self, instance):
        self._validate_project_settlement_lock(instance.project_id, instance.deal_date, '삭제')
        instance.delete()

    def list(self, request, *args, **kwargs):
        """get_project_transactions 서비스가 필터링한 쿼리셋에 대해 페이징 처리된 instances만 prefetch 맵핑 후 직렬화합니다"""
        queryset = get_project_transactions(request.query_params, user=request.user)
        page = self.paginate_queryset(queryset)
        instances = page if page is not None else list(queryset)

        # 페이징 완료된 15건(instances)에 대해서만 분개 prefetch 결합 수행 (성능 극대화)
        prefetch_project_transactions(instances, request.query_params)

        serializer = self.get_serializer(instances, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def validate_balance(self, request, pk=None):
        """거래 금액 균형 검증"""
        instance = self.get_object()
        result = instance.validate_accounting_entries()
        return Response(result)

    @action(detail=False, methods=['get'])
    def balance_by_account(self, request):
        """계좌별 잔액 조회"""
        date = request.query_params.get('date', get_today_str())
        project = request.query_params.get('project')
        is_balance = request.query_params.get('is_balance', '')

        queryset = ProjectBankTransaction.objects.filter(deal_date__lte=date).order_by('bank_account')
        user = request.user
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            accessible = list(get_accessible_project_ids(user))
            if project:
                try:
                    p_id = int(project)
                    if p_id not in accessible:
                        queryset = queryset.none()
                    else:
                        queryset = queryset.filter(project_id=p_id)
                except (ValueError, TypeError):
                    queryset = queryset.none()
            else:
                queryset = queryset.filter(project_id__in=accessible)
        elif project:
            queryset = queryset.filter(project_id=project)

        result = queryset.values(
            bank_id=F('bank_account_id'),
            bank_acc=F('bank_account__alias_name'),
            bank_num=F('bank_account__number'),
            is_imprest=F('bank_account__is_imprest'),
        ).annotate(
            inc_sum=Sum(Case(
                When(sort_id=1, then=F('amount')),  # 1 = 입금
                default=0
            )),
            out_sum=Sum(Case(
                When(sort_id=2, then=F('amount')),  # 2 = 출금
                default=0
            )),
            # 당일 합계
            date_inc=Sum(Case(
                When(sort_id=1, deal_date=date, then=F('amount')),
                default=0
            )),
            date_out=Sum(Case(
                When(sort_id=2, deal_date=date, then=F('amount')),
                default=0
            ))
        ).annotate(
            balance=F('inc_sum') - F('out_sum')
        )

        if is_balance == 'true':
            result = result.exclude(balance=0)

        return Response(list(result))

    @action(detail=False, methods=['get'])
    def daily_transactions(self, request):
        """특정일 거래 내역 조회"""

        date = request.query_params.get('date', get_today_str())
        project = request.query_params.get('project')

        if not project:
            return Response(
                {'error': 'project parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transactions = list(self.get_queryset().filter(
            project_id=project,
            deal_date=date
        ).select_related(
            'bank_account', 'sort', 'creator'
        ).order_by('sort_id', 'created_at'))

        prefetch_project_transactions(transactions)

        serializer = ProjectBankTransactionSerializer(transactions, many=True)
        return Response({'results': serializer.data})

    @action(detail=False, methods=['get'])
    def last_deal(self, request):
        """최종 거래 일자 조회"""
        project = request.query_params.get('project')

        if not project:
            return Response(
                {'error': 'project parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        last_transaction = self.get_queryset().filter(
            project_id=project
        ).order_by('-deal_date', '-created_at').first()

        if last_transaction:
            return Response({'results': [{'deal_date': last_transaction.deal_date}]})
        return Response({'results': []})


# ============================================
# Accounting Entry ViewSets
# ============================================


class BankTransactionPreloadMixin:
    """
    AccountingEntry 목록 조회 시 related BankTransaction을 단일 쿼리로 preload합니다.

    AccountingEntry는 transaction_id(UUID)로 BankTransaction과 느슨하게 연결되어 있어
    Django의 prefetch_related를 사용할 수 없으므로 수동 매핑 방식을 사용합니다.
    """
    bank_transaction_model = None  # 하위 클래스에서 지정

    def preload_bank_transactions(self, instances):
        if not self.bank_transaction_model:
            return
        tx_ids = [inst.transaction_id for inst in instances if inst.transaction_id]
        if not tx_ids:
            return
        db = self.get_queryset().db or 'default'
        tx_map = {
            tx.transaction_id: tx
            for tx in self.bank_transaction_model.objects.using(db)
            .filter(transaction_id__in=tx_ids)
            .select_related('sort')
        }
        for inst in instances:
            inst._related_transaction = tx_map.get(inst.transaction_id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            self.preload_bank_transactions(page)
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        instances = list(queryset)
        self.preload_bank_transactions(instances)
        return Response(self.get_serializer(instances, many=True).data)


class CompanyAccountingEntryFilterSet(FilterSet):
    """본사 회계 분개 필터셋"""
    transaction_id = CharFilter(field_name='transaction_id', lookup_expr='exact')

    class Meta:
        model = CompanyAccountingEntry
        fields = ('company', 'account', 'affiliate',
                  'evidence_type', 'transaction_id')


class CompanyAccountingEntryViewSet(BankTransactionPreloadMixin, viewsets.ModelViewSet):
    """본사 회계 분개 ViewSet"""
    queryset = CompanyAccountingEntry.objects.select_related(
        'company', 'account', 'affiliate', 'affiliate__company', 'affiliate__project'
    ).all()
    serializer_class = CompanyAccountingEntrySerializer
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)
    pagination_class = PageNumberPaginationFifteen
    filterset_class = CompanyAccountingEntryFilterSet
    search_fields = ('transaction_id', 'account_code', 'trader')
    ordering = ['-created_at']
    bank_transaction_model = CompanyBankTransaction

    @property
    def required_permission(self):
        return {
            'list': 'hq.ledger.read',
            'retrieve': 'hq.ledger.read',
            'create': 'hq.ledger.create',
            'update': 'hq.ledger.update',
            'partial_update': 'hq.ledger.update',
            'destroy': 'hq.ledger.delete',
        }.get(self.action, 'hq.ledger.read')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser:
            return qs
        return qs.filter(company_id__in=get_accessible_company_ids(user))

    def _check_company_entry_settlement_lock(self, company_id, deal_date, action_label, is_only_account_change=False):
        if is_only_account_change or not company_id or not deal_date:
            return
        try:
            cal = CompanyLedgerCalculation.objects.get(company_id=company_id)
            if cal.calculated and deal_date <= cal.calculated:
                user = self.request.user
                has_manage = user.is_superuser or getattr(user, 'work_manager', False)
                if not has_manage:
                    user_perms = HqProjectModulePermission._get_all_hq_user_permissions(user)
                    if 'hq.ledger.manage' in user_perms or 'ledger.com_manage' in user_perms:
                        has_manage = True
                if not has_manage:
                    raise serializers.ValidationError(f'정산 마감일({cal.calculated}) 이전의 분개는 {action_label}할 수 없습니다.')
        except CompanyLedgerCalculation.DoesNotExist:
            pass

    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        company_id = company.pk if hasattr(company, 'pk') else company
        tx_id = serializer.validated_data.get('transaction_id')
        tx = CompanyBankTransaction.objects.filter(transaction_id=tx_id).first() if tx_id else None
        deal_date = tx.deal_date if tx else None
        self._check_company_entry_settlement_lock(company_id, deal_date, '생성')
        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.instance
        deal_date = instance.related_transaction.deal_date if instance.related_transaction else None
        vdata = serializer.validated_data
        important_changed = any(
            (k in vdata and getattr(instance, k) != vdata[k])
            for k in ('amount', 'trader', 'evidence_type', 'affiliate', 'transaction_id', 'company')
        )
        account_changed = 'account' in vdata and instance.account != vdata['account']
        is_only_account_change = (not important_changed) and account_changed
        self._check_company_entry_settlement_lock(
            instance.company_id, deal_date, '수정', is_only_account_change=is_only_account_change
        )
        serializer.save()

    def perform_destroy(self, instance):
        deal_date = instance.related_transaction.deal_date if instance.related_transaction else None
        self._check_company_entry_settlement_lock(instance.company_id, deal_date, '삭제')
        instance.delete()


class ProjectAccountingEntryFilterSet(FilterSet):
    """프로젝트 회계 분개 필터셋"""
    transaction_id = CharFilter(field_name='transaction_id', lookup_expr='exact')

    class Meta:
        model = ProjectAccountingEntry
        fields = ('project', 'account', 'contract', 'contractor', 'evidence_type', 'transaction_id')


class ProjectAccountingEntryViewSet(BankTransactionPreloadMixin, viewsets.ModelViewSet):
    """프로젝트 회계 분개 ViewSet"""
    queryset = ProjectAccountingEntry.objects.select_related(
        'project', 'account', 'contract', 'contractor'
    ).all()
    serializer_class = ProjectAccountingEntrySerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationFifteen
    filterset_class = ProjectAccountingEntryFilterSet
    search_fields = ('transaction_id', 'account_code', 'trader', 'project__name')
    ordering = ['-created_at']
    bank_transaction_model = ProjectBankTransaction

    @property
    def required_permission(self):
        return {
            'list': 'ledger.read',
            'retrieve': 'ledger.read',
            'create': 'ledger.create',
            'update': 'ledger.update',
            'partial_update': 'ledger.update',
            'destroy': 'ledger.delete',
        }.get(self.action, 'ledger.read')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    def _check_project_entry_settlement_lock(self, project_id, deal_date, action_label, is_only_account_change=False):
        if is_only_account_change or not project_id or not deal_date:
            return
        try:
            cal = ProjectLedgerCalculation.objects.get(project_id=project_id)
            if cal.calculated and deal_date <= cal.calculated:
                user = self.request.user
                has_manage = user.is_superuser or getattr(user, 'work_manager', False)
                if not has_manage:
                    try:
                        from project.models import Project
                        prj = Project.objects.select_related('issue_project').get(pk=project_id)
                        if hasattr(prj, 'issue_project') and prj.issue_project:
                            user_perms = set(prj.issue_project.get_user_permissions(user))
                            if 'ledger.manage' in user_perms:
                                has_manage = True
                    except Exception:
                        pass
                if not has_manage:
                    raise serializers.ValidationError(f'정산 마감일({cal.calculated}) 이전의 분개는 {action_label}할 수 없습니다.')
        except ProjectLedgerCalculation.DoesNotExist:
            pass

    def perform_create(self, serializer):
        project = serializer.validated_data.get('project')
        project_id = project.pk if hasattr(project, 'pk') else project
        tx_id = serializer.validated_data.get('transaction_id')
        tx = ProjectBankTransaction.objects.filter(transaction_id=tx_id).first() if tx_id else None
        deal_date = tx.deal_date if tx else None
        self._check_project_entry_settlement_lock(project_id, deal_date, '생성')
        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.instance
        deal_date = instance.related_transaction.deal_date if instance.related_transaction else None
        vdata = serializer.validated_data
        important_changed = any(
            (k in vdata and getattr(instance, k) != vdata[k])
            for k in ('amount', 'trader', 'evidence_type', 'contract', 'contractor', 'transaction_id', 'project')
        )
        account_changed = 'account' in vdata and instance.account != vdata['account']
        is_only_account_change = (not important_changed) and account_changed
        self._check_project_entry_settlement_lock(
            instance.project_id, deal_date, '수정', is_only_account_change=is_only_account_change
        )
        serializer.save()

    def perform_destroy(self, instance):
        deal_date = instance.related_transaction.deal_date if instance.related_transaction else None
        self._check_project_entry_settlement_lock(instance.project_id, deal_date, '삭제')
        instance.delete()


# ============================================
# Composite Transaction ViewSets
# ============================================

class CompanyCompositeTransactionViewSet(viewsets.ViewSet):
    """
    본사 복합 거래 ViewSet

    은행 거래와 회계 분개를 한 번에 생성/수정/관리합니다.
    프론트엔드 거래 관리 UI에서 사용합니다.
    """
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)

    @property
    def required_permission(self):
        return {
            'create': 'hq.ledger.create',
            'update': 'hq.ledger.update',
            'partial_update': 'hq.ledger.update',
            'destroy': 'hq.ledger.delete',
        }.get(self.action, 'hq.ledger.read')

    def _get_bank_transaction(self, request, pk):
        """[C-1] 소속 회사 RLS가 적용된 은행 거래 조회 (IDOR 방지)"""
        qs = CompanyBankTransaction.objects.all()
        if not request.user.is_superuser:
            qs = qs.filter(company_id__in=get_accessible_company_ids(request.user))
        try:
            return qs.get(pk=pk)
        except CompanyBankTransaction.DoesNotExist:
            return None

    def create(self, request):
        """본사 거래 생성 (은행거래 + 회계분개)"""
        company_id = request.data.get('company')
        if not request.user.is_superuser and company_id:
            try:
                c_id_int = int(company_id)
            except (ValueError, TypeError):
                c_id_int = None
            if c_id_int not in get_accessible_company_ids(request.user):
                return Response({'detail': '해당 회사의 거래를 생성할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CompanyCompositeTransactionSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            try:
                result = serializer.save(creator=request.user)  # creator를 serializer.save()로 전달
            except DjangoValidationError as e:
                return Response(as_serializer_error(e), status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'bank_transaction': CompanyBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': CompanyAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """본사 거래 수정 (은행거래 + 회계분개)"""
        bank_transaction = self._get_bank_transaction(request, pk)
        if not bank_transaction:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, bank_transaction)

        serializer = CompanyCompositeTransactionSerializer(
            instance=bank_transaction,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            try:
                result = serializer.save()
            except DjangoValidationError as e:
                return Response(as_serializer_error(e), status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'bank_transaction': CompanyBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': CompanyAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """본사 거래 부분 수정 (은행거래 + 회계분개)"""
        bank_transaction = self._get_bank_transaction(request, pk)
        if not bank_transaction:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, bank_transaction)

        serializer = CompanyCompositeTransactionSerializer(
            instance=bank_transaction,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            try:
                result = serializer.save()
            except DjangoValidationError as e:
                return Response(as_serializer_error(e), status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'bank_transaction': CompanyBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': CompanyAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """본사 거래 삭제 (은행거래 + 회계분개 일괄 삭제)"""
        bank_transaction = self._get_bank_transaction(request, pk)
        if not bank_transaction:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, bank_transaction)

        # 삭제 전 정보 저장 (로깅용)
        transaction_id = bank_transaction.transaction_id

        # 정산 마감일 검증
        try:
            cal = CompanyLedgerCalculation.objects.get(company_id=bank_transaction.company_id)
            if cal.calculated and bank_transaction.deal_date <= cal.calculated:
                user = request.user
                has_manage_perm = user.is_superuser or getattr(user, 'work_manager', False)
                if not has_manage_perm:
                    from apiV1.permissions.ibs_perms import HqProjectModulePermission
                    user_perms = HqProjectModulePermission._get_all_hq_user_permissions(user)
                    if 'hq.ledger.manage' in user_perms:
                        has_manage_perm = True

                if not has_manage_perm:
                    return Response({'detail': f'정산 마감일({cal.calculated}) 이전의 거래는 삭제할 수 없습니다.'},
                                    status=status.HTTP_400_BAD_REQUEST)
        except CompanyLedgerCalculation.DoesNotExist:
            pass

        # 트랜잭션으로 묶어서 원자적으로 삭제
        with db_transaction.atomic():
            # 1. 연결된 회계분개 먼저 삭제
            deleted_entries_count, _ = CompanyAccountingEntry.objects.filter(
                transaction_id=transaction_id
            ).delete()

            # 2. 은행거래 삭제
            bank_transaction.delete()

        return Response({
            'message': '거래가 삭제되었습니다.',
            'transaction_id': str(transaction_id),
            'deleted_entries': deleted_entries_count
        }, status=status.HTTP_204_NO_CONTENT)


class ProjectCompositeTransactionViewSet(viewsets.ViewSet):
    """
    프로젝트 복합 거래 ViewSet

    은행 거래, 회계 분개, 계약 결제를 한 번에 생성/수정/관리합니다.
    프론트엔드 거래 관리 UI에서 사용합니다.
    """
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)

    @property
    def required_permission(self):
        return {
            'create': 'ledger.create',
            'update': 'ledger.update',
            'partial_update': 'ledger.update',
            'destroy': 'ledger.delete',
        }.get(self.action, 'ledger.read')

    def create(self, request):
        """프로젝트 거래 생성 (은행거래 + 회계분개 + 계약결제)"""
        project_id = request.data.get('project')
        if project_id and not (request.user.is_superuser or getattr(request.user, 'work_manager', False)):
            try:
                p_id = int(project_id)
                if p_id not in get_accessible_project_ids(request.user):
                    return Response({'detail': '해당 프로젝트에 대한 접근 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            except (ValueError, TypeError):
                return Response({'detail': '유효하지 않은 프로젝트 식별자입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProjectCompositeTransactionSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            try:
                result = serializer.save(creator=request.user)  # creator를 serializer.save()로 전달
            except DjangoValidationError as e:
                return Response(as_serializer_error(e), status=status.HTTP_400_BAD_REQUEST)
            response_data = {
                'bank_transaction': ProjectBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': ProjectAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }
            # 계약 결제 정보가 있는 경우 포함
            if 'contract_payments' in result:
                response_data['contract_payments'] = [
                    {'pk': cp.pk, 'contract': cp.contract_id, 'installment_order': cp.installment_order_id, }
                    for cp in result['contract_payments']]
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """프로젝트 거래 수정 (은행거래 + 회계분개 + 계약결제)"""
        qs = ProjectBankTransaction.objects.all()
        if not (request.user.is_superuser or getattr(request.user, 'work_manager', False)):
            qs = qs.filter(project_id__in=get_accessible_project_ids(request.user))
        try:
            bank_transaction = qs.get(pk=pk)
        except ProjectBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, bank_transaction)

        serializer = ProjectCompositeTransactionSerializer(
            instance=bank_transaction,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            try:
                result = serializer.save()
            except DjangoValidationError as e:
                return Response(as_serializer_error(e), status=status.HTTP_400_BAD_REQUEST)
            response_data = {
                'bank_transaction': ProjectBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': ProjectAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }
            # 계약 결제 정보가 있는 경우 포함
            if 'contract_payments' in result:
                response_data['contract_payments'] = [
                    {'pk': cp.pk, 'contract': cp.contract_id, 'installment_order': cp.installment_order_id, } for cp in
                    result['contract_payments']]
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """프로젝트 거래 부분 수정 (은행거래 + 회계분개 + 계약결제)"""
        qs = ProjectBankTransaction.objects.all()
        if not (request.user.is_superuser or getattr(request.user, 'work_manager', False)):
            qs = qs.filter(project_id__in=get_accessible_project_ids(request.user))
        try:
            bank_transaction = qs.get(pk=pk)
        except ProjectBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, bank_transaction)

        serializer = ProjectCompositeTransactionSerializer(
            instance=bank_transaction,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            try:
                result = serializer.save()
            except DjangoValidationError as e:
                return Response(as_serializer_error(e), status=status.HTTP_400_BAD_REQUEST)
            response_data = {
                'bank_transaction': ProjectBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': ProjectAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }
            # 계약 결제 정보가 있는 경우 포함
            if 'contract_payments' in result:
                response_data['contract_payments'] = [
                    {'pk': cp.pk, 'contract': cp.contract_id, 'installment_order': cp.installment_order_id, } for cp in
                    result['contract_payments']]
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """프로젝트 거래 삭제 (은행거래 + 회계분개 + 계약결제 일괄 삭제)"""
        qs = ProjectBankTransaction.objects.all()
        if not (request.user.is_superuser or getattr(request.user, 'work_manager', False)):
            qs = qs.filter(project_id__in=get_accessible_project_ids(request.user))
        try:
            bank_transaction = qs.get(pk=pk)
        except ProjectBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, bank_transaction)

        # 삭제 전 정보 저장 (로깅용)
        transaction_id = bank_transaction.transaction_id

        # 정산 마감일 검증
        try:
            cal = ProjectLedgerCalculation.objects.get(project_id=bank_transaction.project_id)
            if cal.calculated and bank_transaction.deal_date <= cal.calculated:
                user = request.user
                has_manage_perm = user.is_superuser or getattr(user, 'work_manager', False)
                if not has_manage_perm:
                    try:
                        from project.models import Project
                        prj = Project.objects.select_related('issue_project').get(pk=bank_transaction.project_id)
                        if hasattr(prj, 'issue_project') and prj.issue_project:
                            user_perms = set(prj.issue_project.get_user_permissions(user))
                            if 'ledger.manage' in user_perms:
                                has_manage_perm = True
                    except Exception:
                        pass

                if not has_manage_perm:
                    return Response({'detail': f'정산 마감일({cal.calculated}) 이전의 거래는 삭제할 수 없습니다.'},
                                    status=status.HTTP_400_BAD_REQUEST)
        except ProjectLedgerCalculation.DoesNotExist:
            pass

        # 트랜잭션으로 묶어서 원자적으로 삭제
        with db_transaction.atomic():
            # 1. 연결된 회계분개 삭제 (CASCADE로 ContractPayment도 자동 삭제됨)
            deleted_entries_count, _ = ProjectAccountingEntry.objects.filter(
                transaction_id=transaction_id
            ).delete()

            # 2. 은행거래 삭제
            bank_transaction.delete()

        return Response({
            'message': '거래가 삭제되었습니다.',
            'transaction_id': str(transaction_id),
            'deleted_entries': deleted_entries_count
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================
# Calculation ViewSets
# ============================================


class CompanyLedgerCalculationViewSet(viewsets.ModelViewSet):
    """본사 원장 정산 ViewSet"""
    queryset = CompanyLedgerCalculation.objects.select_related('company', 'creator')
    serializer_class = CompanyLedgerCalculationSerializer
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('company',)

    @property
    def required_permission(self):
        return 'hq.ledger.read' if self.action in ('list', 'retrieve') else 'hq.ledger.manage'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser:
            return qs
        return qs.filter(company_id__in=get_accessible_company_ids(user))

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class CompanyLedgerLastDealDateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CompanyBankTransaction.objects.all()
    serializer_class = CompanyLedgerLastDealDateSerializer
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)

    @property
    def required_permission(self):
        return 'hq.ledger.read'

    def get_queryset(self):
        user = self.request.user
        company = self.request.query_params.get('company')
        qs = CompanyBankTransaction.objects.all()
        if not user.is_superuser:
            qs = qs.filter(company_id__in=get_accessible_company_ids(user))
        if company:
            qs = qs.filter(company_id=company)
        return qs.order_by('-deal_date')[:1]


class ProjectLedgerCalculationViewSet(viewsets.ModelViewSet):
    """프로젝트 원장 정산 ViewSet"""
    queryset = ProjectLedgerCalculation.objects.select_related('project', 'creator')
    serializer_class = ProjectLedgerCalculationSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('project',)

    @property
    def required_permission(self):
        return 'ledger.read' if self.action in ('list', 'retrieve') else 'ledger.manage'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ProjectLedgerLastDealDateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProjectBankTransaction.objects.all()
    serializer_class = ProjectLedgerLastDealDateSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)

    @property
    def required_permission(self):
        return 'ledger.read'

    def get_queryset(self):
        user = self.request.user
        project = self.request.query_params.get('project')
        qs = ProjectBankTransaction.objects.all()
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            qs = qs.filter(project_id__in=get_accessible_project_ids(user))
        if project:
            qs = qs.filter(project_id=project)
        return qs.order_by('-deal_date')[:1]


