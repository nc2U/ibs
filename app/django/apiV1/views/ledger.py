from collections import defaultdict
from datetime import datetime

from django.db import transaction as db_transaction
from django.db.models import Sum, F, Case, When
from django_filters import DateFilter, CharFilter, NumberFilter, BooleanFilter
from django_filters.rest_framework import FilterSet
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ledger.models import (
    BankCode, CompanyBankAccount, ProjectBankAccount,
    CompanyAccount, ProjectAccount, Affiliate,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    CompanyLedgerCalculation, ProjectLedgerCalculation,
)
from ledger.services.company_transaction import get_company_transactions
from ..pagination import PageNumberPaginationFifteen, PageNumberPaginationFifty, PageNumberPaginationThreeHundred
from ..permission import IsStaffOrReadOnly
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

TODAY = datetime.today().strftime('%Y-%m-%d')


# ============================================
# Bank Account ViewSets
# ============================================

class LedgerBankCodeViewSet(viewsets.ModelViewSet):
    """은행 코드 ViewSet"""
    queryset = BankCode.objects.all()
    serializer_class = LedgerBankCodeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifty
    search_fields = ('code', 'name')


class LedgerCompanyBankAccountViewSet(viewsets.ModelViewSet):
    """본사 은행 계좌 ViewSet"""
    queryset = CompanyBankAccount.objects.select_related('bankcode', 'company', 'depart').all()
    serializer_class = LedgerCompanyBankAccountSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('company', 'depart', 'bankcode', 'is_hide', 'inactive')
    search_fields = ('alias_name', 'number', 'holder')


class LedgerProjectBankAccountViewSet(viewsets.ModelViewSet):
    """프로젝트 은행 계좌 ViewSet"""
    queryset = ProjectBankAccount.objects.select_related('bankcode', 'project').all()
    serializer_class = LedgerProjectBankAccountSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifty
    filterset_fields = ('project', 'bankcode', 'is_hide', 'inactive', 'directpay', 'is_imprest')
    search_fields = ('alias_name', 'number', 'holder', 'project__name')


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
    queryset = CompanyAccount.objects.select_related('parent').all()
    serializer_class = CompanyAccountSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = CompanyAccountFilter
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
        fields = ['category', 'direction', 'parent', 'is_category_only', 'is_active',
                  'is_payment', 'is_related_contract']


class ProjectAccountViewSet(viewsets.ModelViewSet):
    """프로젝트 계정 과목 ViewSet"""
    queryset = ProjectAccount.objects.select_related('parent').all()
    serializer_class = ProjectAccountSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
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
        is_related_contract = request.query_params.get('is_related_contract')

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

        if is_related_contract is not None:
            is_related_contract_bool = is_related_contract.lower() in ('true', '1', 'yes')
            matched_accounts = matched_accounts.filter(is_related_contract=is_related_contract_bool)

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
                'is_related_contract': account.is_related_contract,
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
                'is_related_contract': parent.is_related_contract,
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
            is_related_contract=True,
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
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationThreeHundred
    filterset_class = AffiliateFilter
    search_fields = ('description', 'company__name', 'project__name')


# ============================================
# Bank Transaction ViewSets
# ============================================


class CompanyBankTransactionViewSet(viewsets.ModelViewSet):
    """본사 은행 거래 ViewSet"""
    queryset = CompanyBankTransaction.objects.all()
    serializer_class = CompanyBankTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifteen

    def get_queryset(self):
        """
        요청 action에 따라 쿼리셋을 분기합니다.
        - list: 서비스 함수를 통해 필터링된 쿼리셋 반환
        - retrieve, update 등: 기본 쿼리셋 반환
        """
        if self.action == 'list':
            return get_company_transactions(self.request.query_params)
        # 상세 조회 등에서는 필터링 없이 전체에서 pk로 조회
        return super().get_queryset().select_related(
            'company', 'bank_account', 'sort', 'creator'
        )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['get'])
    def validate_balance(self, request, pk=None):
        """거래 금액 균형 검증"""
        instance = self.get_object()
        result = instance.validate_accounting_entries()
        return Response(result)

    @action(detail=False, methods=['get'])
    def balance_by_account(self, request):
        """계좌별 잔액 조회 (누적 + 당일 입출금)"""
        date = request.query_params.get('date', TODAY)
        company = request.query_params.get('company')
        is_balance = request.query_params.get('is_balance', '')

        queryset = CompanyBankTransaction.objects.filter(deal_date__lte=date).order_by('bank_account')
        if company:
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
        date = request.query_params.get('date', TODAY)
        company = request.query_params.get('company')

        if not company:
            return Response(
                {'error': 'company parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. 기본 쿼리셋 (잘못된 prefetch 제거)
        transactions = self.get_queryset().filter(
            company_id=company,
            deal_date=date
        ).select_related(
            'bank_account', 'sort', 'creator'
        ).order_by('sort_id', 'created_at')

        # 2. 수동으로 prefetch 하기
        transaction_ids = [t.transaction_id for t in transactions]

        if transaction_ids:
            # 관련된 모든 회계 분개를 한 번의 쿼리로 가져오기
            accounting_entries = CompanyAccountingEntry.objects.filter(
                transaction_id__in=transaction_ids
            ).select_related('account')

            # transaction_id를 키로 하는 딕셔너리 생성
            entries_map = defaultdict(list)
            for entry in accounting_entries:
                entries_map[entry.transaction_id].append(entry)

            # 각 거래 객체에 미리 가져온 분개 리스트를 할당
            for transaction in transactions:
                transaction.prefetched_accounting_entries = entries_map.get(transaction.transaction_id, [])
        else:
            for transaction in transactions:
                transaction.prefetched_accounting_entries = []

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

        last_transaction = CompanyBankTransaction.objects.filter(
            company_id=company
        ).order_by('-deal_date', '-created_at').first()

        if last_transaction:
            return Response({'results': [{'deal_date': last_transaction.deal_date}]})
        return Response({'results': []})


class ProjectBankTransactionFilterSet(FilterSet):
    """프로젝트 은행 거래 필터셋"""
    from_deal_date = DateFilter(field_name='deal_date', lookup_expr='gte', label='거래일자부터')
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='거래일자까지')
    account = NumberFilter(method='filter_by_account', label='계정 과목')
    account_category = CharFilter(method='filter_by_category', label='계정 카테고리')
    account_name = CharFilter(method='filter_by_name', label='계정 이름')

    class Meta:
        model = ProjectBankTransaction
        fields = ('project', 'bank_account', 'sort', 'is_imprest', 'from_deal_date',
                  'to_deal_date', 'account', 'account_category', 'account_name')

    @staticmethod
    def filter_by_account(queryset, name, value):
        """계정 및 모든 하위 계정으로 필터링"""
        try:
            # 1. 요청된 계정 조회
            account = ProjectAccount.objects.get(pk=value)

            # 2. 계정 + 모든 하위 계정 추출 (활성 계정만)
            descendants = account.get_descendants(include_self=True)
            active_accounts = [acc for acc in descendants if acc.is_active]
            account_ids = [acc.pk for acc in active_accounts]

            # 3. 해당 계정들을 사용하는 회계분개의 transaction_id
            transaction_ids = ProjectAccountingEntry.objects.filter(
                account_id__in=account_ids
            ).values_list('transaction_id', flat=True)

            # 4. BankTransaction 필터링
            return queryset.filter(transaction_id__in=transaction_ids)
        except ProjectAccount.DoesNotExist:
            return queryset.none()

    @staticmethod
    def filter_by_category(queryset, name, value):
        """카테고리별 필터링 (asset, liability, equity, revenue, expense, transfer, cancel)"""
        # 1. 해당 카테고리의 활성 계정 조회
        account_ids = ProjectAccount.objects.filter(
            category=value,
            is_active=True
        ).values_list('pk', flat=True)

        # 2. 해당 계정들의 transaction_id
        transaction_ids = ProjectAccountingEntry.objects.filter(
            account_id__in=account_ids
        ).values_list('transaction_id', flat=True)

        # 3. 필터링
        return queryset.filter(transaction_id__in=transaction_ids)

    @staticmethod
    def filter_by_name(queryset, name, value):
        """계정 이름으로 부분 일치 검색"""
        # 1. 이름에 검색어 포함된 활성 계정 조회
        accounts = ProjectAccount.objects.filter(
            name__icontains=value,
            is_active=True
        )

        # 2. 각 계정의 하위 계정도 모두 포함
        all_account_ids = []
        for account in accounts:
            descendants = account.get_descendants(include_self=True)
            active_descendants = [acc.pk for acc in descendants if acc.is_active]
            all_account_ids.extend(active_descendants)

        # 중복 제거
        account_ids = list(set(all_account_ids))

        # 3. transaction_id 조회 및 필터링
        transaction_ids = ProjectAccountingEntry.objects.filter(
            account_id__in=account_ids
        ).values_list('transaction_id', flat=True)

        return queryset.filter(transaction_id__in=transaction_ids)


class ProjectBankTransactionViewSet(viewsets.ModelViewSet):
    """프로젝트 은행 거래 ViewSet"""
    queryset = ProjectBankTransaction.objects.select_related(
        'project', 'bank_account', 'sort', 'creator'
    ).all()
    serializer_class = ProjectBankTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifteen
    filterset_class = ProjectBankTransactionFilterSet
    search_fields = ('transaction_id', 'content', 'note', 'project__name')
    ordering = ['-deal_date', '-created_at']

    def get_queryset(self):
        """
        검색 쿼리셋 반환

        search 파라미터가 있으면 거래 내용, 메모, 프로젝트명, 계정 이름을 모두 검색
        """
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')

        if search:
            # 1. 계정 이름에 검색어가 포함된 활성 계정 조회
            accounts = ProjectAccount.objects.filter(
                name__icontains=search,
                is_active=True
            )

            # 2. 각 계정의 하위 계정도 모두 포함
            all_account_ids = []
            for account in accounts:
                descendants = account.get_descendants(include_self=True)
                active_descendants = [acc.pk for acc in descendants if acc.is_active]
                all_account_ids.extend(active_descendants)

            # 중복 제거
            account_ids = list(set(all_account_ids))

            # 3. 해당 계정들의 transaction_id
            transaction_ids = ProjectAccountingEntry.objects.filter(
                account_id__in=account_ids
            ).values_list('transaction_id', flat=True)

            # 4. 기본 search_fields 검색 결과와 계정 검색 결과를 OR로 결합
            from django.db.models import Q
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(content__icontains=search) |
                Q(note__icontains=search) |
                Q(project__name__icontains=search) |
                Q(transaction_id__in=transaction_ids)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['get'])
    def validate_balance(self, request, pk=None):
        """거래 금액 균형 검증"""
        instance = self.get_object()
        result = instance.validate_accounting_entries()
        return Response(result)

    @action(detail=False, methods=['get'])
    def balance_by_account(self, request):
        """계좌별 잔액 조회"""
        date = request.query_params.get('date', TODAY)
        project = request.query_params.get('project')

        queryset = ProjectBankTransaction.objects.filter(deal_date__lte=date)
        if project:
            queryset = queryset.filter(project_id=project)

        result = queryset.values(
            bank_acc=F('bank_account__alias_name'),
            bank_num=F('bank_account__number')
        ).annotate(
            income_sum=Sum(Case(
                When(sort_id=1, then=F('amount')),  # 1 = 입금
                default=0
            )),
            outlay_sum=Sum(Case(
                When(sort_id=2, then=F('amount')),  # 2 = 출금
                default=0
            )),
        ).annotate(
            balance=F('income_sum') - F('outlay_sum')
        )

        return Response(list(result))

    @action(detail=False, methods=['get'])
    def daily_transactions(self, request):
        """특정일 거래 내역 조회"""

        date = request.query_params.get('date', TODAY)
        project = request.query_params.get('project')

        if not project:
            return Response(
                {'error': 'project parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. 기본 쿼리셋 (잘못된 prefetch 제거)
        transactions = self.get_queryset().filter(
            project_id=project,
            deal_date=date
        ).select_related(
            'bank_account', 'sort', 'creator'
        ).order_by('sort_id', 'created_at')

        # 2. 수동으로 prefetch 하기
        transaction_ids = [t.transaction_id for t in transactions]

        if transaction_ids:
            # 관련된 모든 회계 분개를 한 번의 쿼리로 가져오기
            accounting_entries = ProjectAccountingEntry.objects.filter(
                transaction_id__in=transaction_ids
            ).select_related('account')

            # transaction_id를 키로 하는 딕셔너리 생성
            entries_map = defaultdict(list)
            for entry in accounting_entries:
                entries_map[entry.transaction_id].append(entry)

            # 각 거래 객체에 미리 가져온 분개 리스트를 할당
            for transaction in transactions:
                transaction.prefetched_accounting_entries = entries_map.get(transaction.transaction_id, [])
        else:
            for transaction in transactions:
                transaction.prefetched_accounting_entries = []

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

        last_transaction = ProjectBankTransaction.objects.filter(
            project_id=project
        ).order_by('-deal_date', '-created_at').first()

        if last_transaction:
            return Response({'results': [{'deal_date': last_transaction.deal_date}]})
        return Response({'results': []})


# ============================================
# Accounting Entry ViewSets
# ============================================

class CompanyAccountingEntryFilterSet(FilterSet):
    """본사 회계 분개 필터셋"""
    transaction_id = CharFilter(field_name='transaction_id', lookup_expr='exact')

    class Meta:
        model = CompanyAccountingEntry
        fields = ('company', 'account', 'affiliate',
                  'evidence_type', 'transaction_id')


class CompanyAccountingEntryViewSet(viewsets.ModelViewSet):
    """본사 회계 분개 ViewSet"""
    queryset = CompanyAccountingEntry.objects.select_related(
        'company', 'account', 'affiliate', 'affiliate__company', 'affiliate__project'
    ).all()
    serializer_class = CompanyAccountingEntrySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifteen
    filterset_class = CompanyAccountingEntryFilterSet
    search_fields = ('transaction_id', 'account_code', 'trader')
    ordering = ['-created_at']


class ProjectAccountingEntryFilterSet(FilterSet):
    """프로젝트 회계 분개 필터셋"""
    transaction_id = CharFilter(field_name='transaction_id', lookup_expr='exact')

    class Meta:
        model = ProjectAccountingEntry
        fields = ('project', 'account', 'contract', 'evidence_type', 'transaction_id')


class ProjectAccountingEntryViewSet(viewsets.ModelViewSet):
    """프로젝트 회계 분개 ViewSet"""
    queryset = ProjectAccountingEntry.objects.select_related(
        'project', 'account', 'contract'
    ).all()
    serializer_class = ProjectAccountingEntrySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifteen
    filterset_class = ProjectAccountingEntryFilterSet
    search_fields = ('transaction_id', 'account_code', 'trader', 'project__name')
    ordering = ['-created_at']


# ============================================
# Composite Transaction ViewSets
# ============================================

class CompanyCompositeTransactionViewSet(viewsets.ViewSet):
    """
    본사 복합 거래 ViewSet

    은행 거래와 회계 분개를 한 번에 생성/수정/관리합니다.
    프론트엔드 거래 관리 UI에서 사용합니다.
    """
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)

    @staticmethod
    def create(request):
        """본사 거래 생성 (은행거래 + 회계분개)"""
        serializer = CompanyCompositeTransactionSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save(creator=request.user)  # creator를 serializer.save()로 전달
            return Response({
                'bank_transaction': CompanyBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': CompanyAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def update(request, pk=None):
        """본사 거래 수정 (은행거래 + 회계분개)"""
        try:
            bank_transaction = CompanyBankTransaction.objects.get(pk=pk)
        except CompanyBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CompanyCompositeTransactionSerializer(
            instance=bank_transaction,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                'bank_transaction': CompanyBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': CompanyAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def partial_update(request, pk=None):
        """본사 거래 부분 수정 (은행거래 + 회계분개)"""
        try:
            bank_transaction = CompanyBankTransaction.objects.get(pk=pk)
        except CompanyBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CompanyCompositeTransactionSerializer(
            instance=bank_transaction,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                'bank_transaction': CompanyBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': CompanyAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def destroy(request, pk=None):
        """본사 거래 삭제 (은행거래 + 회계분개 일괄 삭제)"""
        try:
            bank_transaction = CompanyBankTransaction.objects.get(pk=pk)
        except CompanyBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 삭제 전 정보 저장 (로깅용)
        transaction_id = bank_transaction.transaction_id

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
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)

    @staticmethod
    def create(request):
        """프로젝트 거래 생성 (은행거래 + 회계분개 + 계약결제)"""
        serializer = ProjectCompositeTransactionSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save()
            response_data = {
                'bank_transaction': ProjectBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': ProjectAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }
            # 계약 결제 정보가 있는 경우 포함
            if 'contract_payments' in result:
                response_data['contract_payments'] = [
                    {
                        'pk': cp.pk,
                        'contract': cp.contract_id,
                        'installment_order': cp.installment_order_id,
                        'payment_type': cp.payment_type,
                    }
                    for cp in result['contract_payments']
                ]
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def update(request, pk=None):
        """프로젝트 거래 수정 (은행거래 + 회계분개 + 계약결제)"""
        try:
            bank_transaction = ProjectBankTransaction.objects.get(pk=pk)
        except ProjectBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectCompositeTransactionSerializer(
            instance=bank_transaction,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save()
            response_data = {
                'bank_transaction': ProjectBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': ProjectAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }
            # 계약 결제 정보가 있는 경우 포함
            if 'contract_payments' in result:
                response_data['contract_payments'] = [
                    {
                        'pk': cp.pk,
                        'contract': cp.contract_id,
                        'installment_order': cp.installment_order_id,
                        'payment_type': cp.payment_type,
                    }
                    for cp in result['contract_payments']
                ]
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def partial_update(request, pk=None):
        """프로젝트 거래 부분 수정 (은행거래 + 회계분개 + 계약결제)"""
        try:
            bank_transaction = ProjectBankTransaction.objects.get(pk=pk)
        except ProjectBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectCompositeTransactionSerializer(
            instance=bank_transaction,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save()
            response_data = {
                'bank_transaction': ProjectBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': ProjectAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }
            # 계약 결제 정보가 있는 경우 포함
            if 'contract_payments' in result:
                response_data['contract_payments'] = [
                    {
                        'pk': cp.pk,
                        'contract': cp.contract_id,
                        'installment_order': cp.installment_order_id,
                        'payment_type': cp.payment_type,
                    }
                    for cp in result['contract_payments']
                ]
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def destroy(request, pk=None):
        """프로젝트 거래 삭제 (은행거래 + 회계분개 + 계약결제 일괄 삭제)"""
        try:
            bank_transaction = ProjectBankTransaction.objects.get(pk=pk)
        except ProjectBankTransaction.DoesNotExist:
            return Response({'error': '거래를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 삭제 전 정보 저장 (로깅용)
        transaction_id = bank_transaction.transaction_id

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
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('company',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class CompanyLedgerLastDealDateViewSet(viewsets.ModelViewSet):
    queryset = CompanyBankTransaction.objects.all()
    serializer_class = CompanyLedgerLastDealDateSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)

    def get_queryset(self):
        company = self.request.query_params.get('company')
        return CompanyBankTransaction.objects.filter(company_id=company).order_by('-deal_date')[:1]


class ProjectLedgerCalculationViewSet(viewsets.ModelViewSet):
    """본사 원장 정산 ViewSet"""
    queryset = ProjectLedgerCalculation.objects.select_related('project', 'creator')
    serializer_class = ProjectLedgerCalculationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('project',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ProjectLedgerLastDealDateViewSet(viewsets.ModelViewSet):
    queryset = ProjectBankTransaction.objects.all()
    serializer_class = ProjectLedgerLastDealDateSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)

    def get_queryset(self):
        project = self.request.query_params.get('project')
        return ProjectBankTransaction.objects.filter(project_id=project).order_by('-deal_date')[:1]
