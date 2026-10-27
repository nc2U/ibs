import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.db.models import Sum, F, Case, When, Count, Q
from django.utils import timezone
from django_filters import CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from apiV1.permissions._utils import get_project_ids_with_permission
from apiV1.permissions.ibs_perms import IbsModulePermission, HqProjectModulePermission
from ledger.models import (
    BankCode, CompanyBankAccount, ProjectBankAccount,
    CompanyAccount, ProjectAccount, Affiliate,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    CompanyLedgerCalculation, ProjectLedgerCalculation,
    BankApiCredential, RawBankTransaction,
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
    BankApiCredentialSerializer, RawBankTransactionSerializer,
    RawBankTransactionConfirmSerializer, RawBankTransactionBulkConfirmSerializer,
    BankCertificateRegisterSerializer, BankCredentialBatchLinkSerializer,
)


def get_today_str():
    return timezone.localdate().strftime('%Y-%m-%d')


TODAY = get_today_str()


# ============================================
# Bank Account ViewSets
# ============================================

class LedgerBankCodeViewSet(viewsets.ModelViewSet):
    """은행 코드 ViewSet"""
    queryset = BankCode.objects.all()
    serializer_class = LedgerBankCodeSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
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
        return 'hq.ledger.read' if self.action in ('list', 'retrieve', 'search_with_parents') else 'hq.ledger.manage'

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
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
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

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

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

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

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
                return Response(
                    e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
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
                return Response(
                    e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
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
                return Response(
                    e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
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
                return Response(
                    e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
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
                return Response(
                    e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
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
                return Response(
                    e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
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


class CompanyLedgerLastDealDateViewSet(viewsets.ModelViewSet):
    queryset = CompanyBankTransaction.objects.all()
    serializer_class = CompanyLedgerLastDealDateSerializer
    permission_classes = (permissions.IsAuthenticated, HqProjectModulePermission)

    @property
    def required_permission(self):
        return 'hq.ledger.read'

    def get_queryset(self):
        user = self.request.user
        company = self.request.query_params.get('company')
        if not user.is_superuser and company:
            try:
                c_id = int(company)
            except (ValueError, TypeError):
                c_id = None
            if c_id not in get_accessible_company_ids(user):
                return CompanyBankTransaction.objects.none()
        return CompanyBankTransaction.objects.filter(company_id=company).order_by('-deal_date')[:1]


class ProjectLedgerCalculationViewSet(viewsets.ModelViewSet):
    """프로젝트 원장 정산 ViewSet"""
    queryset = ProjectLedgerCalculation.objects.select_related('project', 'creator')
    serializer_class = ProjectLedgerCalculationSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
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


class ProjectLedgerLastDealDateViewSet(viewsets.ModelViewSet):
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


# ============================================
# Bank Scraping ViewSets
# ============================================

class BankApiCredentialViewSet(viewsets.ModelViewSet):
    """은행 API 연동 계좌 ViewSet"""
    queryset = BankApiCredential.objects.all().select_related(
        'company_bank_account__company', 'project_bank_account__project'
    )
    serializer_class = BankApiCredentialSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationFifty

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            c_ids = get_accessible_company_ids(user)
            p_ids = get_accessible_project_ids(user)
            qs = qs.filter(
                Q(company_bank_account__company_id__in=c_ids) |
                Q(project_bank_account__project_id__in=p_ids)
            )

        company = self.request.query_params.get('company')
        project = self.request.query_params.get('project')
        is_imprest = self.request.query_params.get('is_imprest')
        is_active = self.request.query_params.get('is_active')

        if company:
            qs = qs.filter(company_bank_account__company_id=company)
        if project:
            qs = qs.filter(project_bank_account__project_id=project)
        if is_imprest is not None:
            val = is_imprest.lower() in ('true', '1')
            qs = qs.filter(project_bank_account__is_imprest=val)
        if is_active is not None:
            val = is_active.lower() in ('true', '1')
            qs = qs.filter(is_active=val)
        return qs

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """특정 계좌의 거래내역 즉시 동기화"""
        from ledger.services.bank_scraping import sync_credential_transactions
        cred = self.get_object()
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        result = sync_credential_transactions(cred, start_date=start_date, end_date=end_date)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """활성화된 은행 연동 계좌 거래내역 일괄 동기화 (특정 credential_ids 지정 가능)"""
        from ledger.services.bank_scraping import sync_all_active_credentials
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        credential_ids = request.data.get('credential_ids')

        summary = sync_all_active_credentials(start_date=start_date, end_date=end_date, credential_ids=credential_ids)
        return Response(summary, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def register_certificate(self, request):
        """
        공동인증서(또는 ID/PW) 등록 -> CODEF connectedId 발급 -> 은행 보유 계좌 목록 조회
        """
        import base64
        import re
        from ledger.services.codef_client import CodefClient, CodefException

        serializer = BankCertificateRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bank_code = serializer.validated_data['bank_code']
        login_type = serializer.validated_data['login_type']
        raw_id = serializer.validated_data.get('id', '')
        password = serializer.validated_data['password']
        cert_file = serializer.validated_data.get('cert_file')
        der_file = serializer.validated_data.get('der_file')
        key_file = serializer.validated_data.get('key_file')

        client = CodefClient(is_sandbox=False)

        account_item = {
            "countryCode": "KR",
            "businessType": "BK",
            "organization": bank_code,
            "clientType": "B",  # 기본 기업(법인)
            "loginType": login_type,
        }

        try:
            if login_type == '0':  # 공동인증서
                if cert_file:  # 통합 인증서 포맷 (.pfx, .p12, .pt2 등)
                    cert_b64 = base64.b64encode(cert_file.read()).decode('utf-8')
                    account_item['certType'] = 'pfx'
                    account_item['certFile'] = cert_b64
                    account_item['password'] = client.encrypt_rsa(password)
                elif der_file and key_file:  # der + key 분리 포맷
                    der_b64 = base64.b64encode(der_file.read()).decode('utf-8')
                    key_b64 = base64.b64encode(key_file.read()).decode('utf-8')
                    account_item['certType'] = '1'
                    account_item['derFile'] = der_b64
                    account_item['keyFile'] = key_b64
                    account_item['password'] = client.encrypt_rsa(password)
                else:
                    return Response(
                        {'error': '통합 인증서 파일(.pfx, .p12, .pt2) 또는 der/key 파일 쌍을 업로드해야 합니다.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:  # 아이디/비밀번호
                if not raw_id:
                    return Response({'error': '인터넷뱅킹 아이디를 입력해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
                account_item['id'] = raw_id
                account_item['password'] = client.encrypt_rsa(password)

            connected_id = client.create_account([account_item])
        except CodefException as ce:
            msg = f"CODEF 계정 등록 실패 [{ce.code}]: {ce.message}"
            if ce.extra_message:
                msg += f" ({ce.extra_message})"
            logger.warning("CODEF 계정 등록 실패: %s", msg)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as ve:
            logger.warning("CODEF 설정 오류: %s", str(ve))
            return Response({'error': "CODEF 설정 정보가 올바르지 않습니다. 시스템 관리자에게 문의하세요."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("계정 등록 처리 중 예외 발생")
            return Response({'error': "계정 등록 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."}, status=status.HTTP_400_BAD_REQUEST)


        # 즉시 해당 은행의 보유 계좌 목록 조회
        try:
            raw_accounts = client.fetch_account_list(connected_id=connected_id, organization=bank_code, is_business=True)
        except Exception as e:
            logger.warning("보유 계좌 목록 조회 실패 (connected_id=%s, bank_code=%s): %s", connected_id, bank_code, str(e))
            raw_accounts = []

        # 기존 시스템의 CompanyBankAccount 및 ProjectBankAccount 조회하여 매칭
        com_accounts = list(CompanyBankAccount.objects.all().select_related('company', 'bankcode'))
        proj_accounts = list(ProjectBankAccount.objects.all().select_related('project', 'bankcode'))

        def clean_num(n):
            return re.sub(r'[^0-9]', '', str(n or ''))

        results = []
        for raw_acc in raw_accounts:
            acc_num = raw_acc.get('resAccount') or raw_acc.get('account') or raw_acc.get('accountNo') or ''
            acc_name = raw_acc.get('resAccountName') or raw_acc.get('accountName') or raw_acc.get('resAccountNickName') or ''
            holder = raw_acc.get('resAccountHolder') or raw_acc.get('holder') or ''
            balance = raw_acc.get('resAccountBalance') or raw_acc.get('balance') or raw_acc.get('resAccountDeposit') or None

            clean_acc = clean_num(acc_num)
            matched_type = None
            matched_account_id = None
            matched_account_alias = None
            company_id = None
            project_id = None
            is_imprest = False

            # 본사 계좌 매칭 시도
            for ca in com_accounts:
                if clean_num(ca.number) == clean_acc:
                    matched_type = 'company'
                    matched_account_id = ca.id
                    matched_account_alias = ca.alias_name
                    company_id = ca.company_id
                    break

            # 프로젝트 계좌 매칭 시도 (본사에 없으면)
            if not matched_type:
                for pa in proj_accounts:
                    if clean_num(pa.number) == clean_acc:
                        matched_type = 'project'
                        matched_account_id = pa.id
                        matched_account_alias = pa.alias_name
                        project_id = pa.project_id
                        is_imprest = pa.is_imprest
                        break

            # 이미 BankApiCredential에 등록되어 있는지 여부
            is_already_registered = BankApiCredential.objects.filter(
                bank_code=bank_code,
                account_number=acc_num
            ).exists()

            results.append({
                'account_number': acc_num,
                'account_name': acc_name,
                'holder': holder,
                'balance': balance,
                'matched_type': matched_type,
                'matched_account_id': matched_account_id,
                'matched_account_alias': matched_account_alias,
                'company_id': company_id,
                'project_id': project_id,
                'is_imprest': is_imprest,
                'is_already_registered': is_already_registered
            })

        return Response({
            'connected_id': connected_id,
            'bank_code': bank_code,
            'accounts': results
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def batch_link(self, request):
        """
        보유 계좌 목록 중 사용자가 선택한 계좌들을 BankApiCredential 및 계좌 모델과 일괄 연동/생성
        """
        serializer = BankCredentialBatchLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connected_id = serializer.validated_data['connected_id']
        bank_code_str = serializer.validated_data['bank_code']
        items = serializer.validated_data['items']

        bank_obj = BankCode.objects.filter(code=bank_code_str[-3:]).first() or BankCode.objects.filter(code=bank_code_str).first()
        if not bank_obj:
            bank_obj = BankCode.objects.first()

        created_credentials = []

        with db_transaction.atomic():
            for item in items:
                acc_num = item['account_number']
                target_type = item['target_type']
                company_id = item.get('company_id')
                project_id = item.get('project_id')
                is_imprest = item.get('is_imprest', False)
                existing_id = item.get('existing_account_id')
                alias_name = item.get('alias_name') or item.get('account_name') or f"계좌 {acc_num[-4:]}"
                holder = item.get('holder', '')

                com_bank_acc = None
                proj_bank_acc = None

                if target_type == 'company':
                    if existing_id:
                        com_bank_acc = CompanyBankAccount.objects.filter(id=existing_id).first()
                    elif company_id:
                        com_bank_acc, _ = CompanyBankAccount.objects.get_or_create(
                            company_id=company_id,
                            number=acc_num,
                            defaults={
                                'bankcode': bank_obj,
                                'alias_name': alias_name,
                                'holder': holder,
                            }
                        )
                    if not com_bank_acc:
                        continue
                else:  # project
                    if existing_id:
                        proj_bank_acc = ProjectBankAccount.objects.filter(id=existing_id).first()
                    elif project_id:
                        proj_bank_acc, _ = ProjectBankAccount.objects.get_or_create(
                            project_id=project_id,
                            number=acc_num,
                            defaults={
                                'bankcode': bank_obj,
                                'alias_name': alias_name,
                                'holder': holder,
                                'is_imprest': is_imprest
                            }
                        )
                    if not proj_bank_acc:
                        continue

                cred_defaults = {
                    'auth_type': 'cert',
                    'connected_id': connected_id,
                    'bank_code': bank_code_str,
                    'account_number': acc_num,
                    'is_active': True,
                    'last_status': 'ready'
                }
                if com_bank_acc:
                    cred, _ = BankApiCredential.objects.update_or_create(
                        company_bank_account=com_bank_acc,
                        defaults=cred_defaults
                    )
                else:
                    cred, _ = BankApiCredential.objects.update_or_create(
                        project_bank_account=proj_bank_acc,
                        defaults=cred_defaults
                    )
                created_credentials.append(cred.pk)

        return Response({
            'success': True,
            'linked_count': len(created_credentials),
            'credential_ids': created_credentials
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def register_fast_account(self, request):
        """
        신탁사/조합 빠른조회 계좌 직접 연동
        공동인증서/connectedId 없이 사업자번호 + 계좌비밀번호로 즉시 연동 및 초기 테스트
        """
        from apiV1.serializers.ledger import BankFastAccountRegisterSerializer
        serializer = BankFastAccountRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bank_code_str = serializer.validated_data['bank_code']
        acc_num = serializer.validated_data['account_number']
        biz_num = serializer.validated_data['business_number']
        acc_pwd = serializer.validated_data['account_password']
        target_type = serializer.validated_data['target_type']
        project_id = serializer.validated_data.get('project_id')
        company_id = serializer.validated_data.get('company_id')
        existing_id = serializer.validated_data.get('existing_account_id')
        alias_name = serializer.validated_data.get('alias_name') or f"신탁/빠른조회 ({acc_num[-4:]})"
        holder = serializer.validated_data.get('holder', '')
        is_imprest = serializer.validated_data.get('is_imprest', False)

        bank_obj = BankCode.objects.filter(code=bank_code_str[-3:]).first() or BankCode.objects.filter(code=bank_code_str).first()
        if not bank_obj:
            bank_obj = BankCode.objects.first()

        com_bank_acc = None
        proj_bank_acc = None

        with db_transaction.atomic():
            if target_type == 'project':
                if not project_id and not existing_id:
                    return Response({'error': '프로젝트를 선택해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
                if existing_id:
                    proj_bank_acc = ProjectBankAccount.objects.filter(id=existing_id).first()
                elif project_id:
                    proj_bank_acc, _ = ProjectBankAccount.objects.get_or_create(
                        project_id=project_id,
                        number=acc_num,
                        defaults={
                            'bankcode': bank_obj,
                            'alias_name': alias_name,
                            'holder': holder,
                            'is_imprest': is_imprest,
                        }
                    )
            else:
                if not company_id and not existing_id:
                    return Response({'error': '회사를 선택해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
                if existing_id:
                    com_bank_acc = CompanyBankAccount.objects.filter(id=existing_id).first()
                elif company_id:
                    com_bank_acc, _ = CompanyBankAccount.objects.get_or_create(
                        company_id=company_id,
                        number=acc_num,
                        defaults={
                            'bankcode': bank_obj,
                            'alias_name': alias_name,
                            'holder': holder,
                        }
                    )

            target_acc = proj_bank_acc or com_bank_acc
            if not target_acc:
                return Response({'error': '계좌 생성 또는 조회가 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            cred_defaults = {
                'auth_type': 'fast',
                'connected_id': '',
                'bank_code': bank_code_str,
                'account_number': acc_num,
                'fast_business_number': biz_num.replace('-', '').strip(),
                'fast_password': acc_pwd,
                'is_active': True,
                'last_status': 'ready'
            }

            if proj_bank_acc:
                cred, _ = BankApiCredential.objects.update_or_create(
                    project_bank_account=proj_bank_acc,
                    defaults=cred_defaults
                )
            else:
                cred, _ = BankApiCredential.objects.update_or_create(
                    company_bank_account=com_bank_acc,
                    defaults=cred_defaults
                )

        # 연동 완료 후 즉시 1회 거래내역 수집 시도 (테스트 및 초기 데이터 로드)
        try:
            from ledger.services.bank_scraping import sync_credential_transactions
            sync_credential_transactions(cred)
        except Exception as e:
            logger.warning("신탁/빠른조회 초기 수집 실패 (등록은 완료됨): %s", str(e))

        return Response({
            'success': True,
            'credential_id': cred.pk,
            'message': f"신탁/빠른조회 계좌({alias_name})가 성공적으로 연동되었습니다."
        }, status=status.HTTP_200_OK)



class RawBankTransactionViewSet(viewsets.ModelViewSet):
    """수집 원시 거래내역 ViewSet"""
    queryset = RawBankTransaction.objects.all().select_related(
        'credential__company_bank_account__company',
        'credential__project_bank_account__project',
        'suggested_company_account',
        'suggested_project_account',
        'suggested_contract__contractor',
        'suggested_contract__key_unit',
        'confirmed_by'
    )
    serializer_class = RawBankTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('status', 'credential', 'deal_date', 'sort_type')
    search_fields = ('client_name', 'content')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            c_ids = get_accessible_company_ids(user)
            p_ids = get_accessible_project_ids(user)
            qs = qs.filter(
                Q(credential__company_bank_account__company_id__in=c_ids) |
                Q(credential__project_bank_account__project_id__in=p_ids)
            )

        company = self.request.query_params.get('company')
        project = self.request.query_params.get('project')
        is_imprest = self.request.query_params.get('is_imprest')

        if company:
            qs = qs.filter(credential__company_bank_account__company_id=company)
        if project:
            qs = qs.filter(credential__project_bank_account__project_id=project)
        if is_imprest is not None:
            val = is_imprest.lower() in ('true', '1')
            qs = qs.filter(credential__project_bank_account__is_imprest=val)
        return qs

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """단건 승인 및 원장 반영 (단일 계정 및 복수 분개 분할 지원)"""
        from ledger.services.transaction_confirm import confirm_raw_transaction
        from ledger.models import CompanyAccount, ProjectAccount
        from contract.models import Contract

        raw_tx = self.get_object()
        user = request.user
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            if raw_tx.credential.is_project:
                manage_projects = get_accessible_project_ids(user, 'ledger.manage')
                if raw_tx.credential.project_bank_account.project_id not in manage_projects:
                    return Response(
                        {'error': '해당 프로젝트의 거래 승인(ledger.manage) 권한이 없습니다.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                manage_companies = get_accessible_company_ids(user)
                if raw_tx.credential.company_bank_account.company_id not in manage_companies:
                    return Response(
                        {'error': '해당 회사의 거래 승인 권한이 없습니다.'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        serializer = RawBankTransactionConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        custom_account_id = serializer.validated_data.get('custom_account_id')
        custom_contract_id = serializer.validated_data.get('custom_contract_id')
        entries_data = serializer.validated_data.get('entries')

        custom_account = None
        if custom_account_id:
            if raw_tx.credential.is_project:
                custom_account = ProjectAccount.objects.filter(id=custom_account_id).first()
            else:
                custom_account = CompanyAccount.objects.filter(id=custom_account_id).first()

        custom_contract = None
        if custom_contract_id and raw_tx.credential.is_project:
            custom_contract = Contract.objects.filter(id=custom_contract_id).first()

        resolved_entries = None
        if entries_data and len(entries_data) > 0:
            resolved_entries = []
            for item in entries_data:
                acc_id = item['account_id']
                if raw_tx.credential.is_project:
                    acc_obj = ProjectAccount.objects.filter(id=acc_id).first()
                else:
                    acc_obj = CompanyAccount.objects.filter(id=acc_id).first()
                if not acc_obj:
                    return Response({'error': f"존재하지 않는 회계계정 ID ({acc_id})입니다."}, status=status.HTTP_400_BAD_REQUEST)

                c_obj = None
                c_id = item.get('contract_id')
                if c_id and raw_tx.credential.is_project:
                    c_obj = Contract.objects.filter(id=c_id).first()

                resolved_entries.append({
                    'account': acc_obj,
                    'amount': item['amount'],
                    'trader': item.get('trader', ''),
                    'contract': c_obj
                })

        if raw_tx.status == 'confirmed':
            return Response({'error': '이미 승인 완료된 거래입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        if resolved_entries:
            total_entry_amount = sum(item['amount'] for item in resolved_entries)
            if total_entry_amount != raw_tx.amount:
                return Response(
                    {'error': '분개 금액 합계가 통장 거래금액과 일치하지 않습니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            default_account = custom_account or (
                raw_tx.suggested_project_account if raw_tx.credential.is_project else raw_tx.suggested_company_account
            )
            if not default_account:
                return Response(
                    {'error': '회계 계정과목이 지정되지 않았습니다. 계정을 선택해 주세요.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            result = confirm_raw_transaction(
                raw_tx=raw_tx,
                user=request.user,
                custom_account=custom_account,
                custom_contract=custom_contract,
                entries_data=resolved_entries
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as ve:
            logger.warning("거래 승인 유효성 검증 실패 (#%s): %s", raw_tx.pk, ve)
            return Response(
                {'error': "유효하지 않은 거래 승인 요청입니다. 입력 정보를 확인해 주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("거래 승인 처리 중 예외 발생 (#%s)", raw_tx.pk)
            return Response({'error': "거래 승인 처리 중 오류가 발생했습니다."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='bulk-confirm')
    def bulk_confirm(self, request):
        """고신뢰도 거래 일괄 승인"""
        from ledger.services.transaction_confirm import bulk_confirm_high_confidence

        serializer = RawBankTransactionBulkConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        min_confidence = serializer.validated_data.get('min_confidence', 90)

        base_qs = None
        if not (request.user.is_superuser or getattr(request.user, 'work_manager', False)):
            c_ids = get_accessible_company_ids(request.user)
            p_ids = get_accessible_project_ids(request.user, 'ledger.manage')
            base_qs = RawBankTransaction.objects.filter(
                Q(credential__company_bank_account__company_id__in=c_ids) |
                Q(credential__project_bank_account__project_id__in=p_ids)
            )

        result = bulk_confirm_high_confidence(user=request.user, min_confidence=min_confidence, base_qs=base_qs)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='bulk_confirm')
    def bulk_confirm_legacy(self, request):
        """고신뢰도 거래 일괄 승인 (언더스코어 URL 호환)"""
        return self.bulk_confirm(request)

