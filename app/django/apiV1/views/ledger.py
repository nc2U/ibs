from datetime import datetime

from django.db.models import Sum, F, Case, When
from django_filters import DateFilter, CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ledger.models import (
    BankCode,
    CompanyBankAccount, ProjectBankAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
)
from ..pagination import PageNumberPaginationFifteen, PageNumberPaginationFifty
from ..permission import IsStaffOrReadOnly
from ..serializers.ledger import (
    LedgerBankCodeSerializer,
    LedgerCompanyBankAccountSerializer, LedgerProjectBankAccountSerializer,
    CompanyBankTransactionSerializer, ProjectBankTransactionSerializer,
    CompanyAccountingEntrySerializer, ProjectAccountingEntrySerializer,
    CompanyCompositeTransactionSerializer, ProjectCompositeTransactionSerializer,
)

TODAY = datetime.today().strftime('%Y-%m-%d')


# ============================================
# Bank Code ViewSet
# ============================================

class LedgerBankCodeViewSet(viewsets.ModelViewSet):
    """은행 코드 ViewSet"""
    queryset = BankCode.objects.all()
    serializer_class = LedgerBankCodeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifty
    search_fields = ('code', 'name')


# ============================================
# Bank Account ViewSets
# ============================================

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
# Bank Transaction ViewSets
# ============================================

class CompanyBankTransactionFilterSet(FilterSet):
    """본사 은행 거래 필터셋"""
    from_deal_date = DateFilter(field_name='deal_date', lookup_expr='gte', label='거래일자부터')
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='거래일자까지')

    class Meta:
        model = CompanyBankTransaction
        fields = ('company', 'bank_account', 'transaction_type', 'from_deal_date', 'to_deal_date')


class CompanyBankTransactionViewSet(viewsets.ModelViewSet):
    """본사 은행 거래 ViewSet"""
    queryset = CompanyBankTransaction.objects.select_related(
        'company', 'bank_account', 'creator'
    ).all()
    serializer_class = CompanyBankTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifteen
    filterset_class = CompanyBankTransactionFilterSet
    search_fields = ('transaction_id', 'content', 'note')
    ordering = ['-deal_date', '-created_at']

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
        company = request.query_params.get('company')

        queryset = CompanyBankTransaction.objects.filter(deal_date__lte=date)
        if company:
            queryset = queryset.filter(company_id=company)

        result = queryset.values(
            bank_acc=F('bank_account__alias_name'),
            bank_num=F('bank_account__number')
        ).annotate(
            income_sum=Sum(Case(
                When(transaction_type='INCOME', then=F('amount')),
                default=0
            )),
            outlay_sum=Sum(Case(
                When(transaction_type='OUTLAY', then=F('amount')),
                default=0
            )),
        ).annotate(
            balance=F('income_sum') - F('outlay_sum')
        )

        return Response(list(result))


class ProjectBankTransactionFilterSet(FilterSet):
    """프로젝트 은행 거래 필터셋"""
    from_deal_date = DateFilter(field_name='deal_date', lookup_expr='gte', label='거래일자부터')
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='거래일자까지')

    class Meta:
        model = ProjectBankTransaction
        fields = ('project', 'bank_account', 'transaction_type', 'is_imprest',
                  'from_deal_date', 'to_deal_date')


class ProjectBankTransactionViewSet(viewsets.ModelViewSet):
    """프로젝트 은행 거래 ViewSet"""
    queryset = ProjectBankTransaction.objects.select_related(
        'project', 'bank_account', 'creator'
    ).all()
    serializer_class = ProjectBankTransactionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifteen
    filterset_class = ProjectBankTransactionFilterSet
    search_fields = ('transaction_id', 'content', 'note', 'project__name')
    ordering = ['-deal_date', '-created_at']

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
                When(transaction_type='INCOME', then=F('amount')),
                default=0
            )),
            outlay_sum=Sum(Case(
                When(transaction_type='OUTLAY', then=F('amount')),
                default=0
            )),
        ).annotate(
            balance=F('income_sum') - F('outlay_sum')
        )

        return Response(list(result))


# ============================================
# Accounting Entry ViewSets
# ============================================

class CompanyAccountingEntryFilterSet(FilterSet):
    """본사 회계 분개 필터셋"""
    transaction_id = CharFilter(field_name='transaction_id', lookup_expr='exact')

    class Meta:
        model = CompanyAccountingEntry
        fields = ('company', 'sort', 'account_d1', 'account_d2', 'account_d3',
                  'evidence_type', 'transaction_id')


class CompanyAccountingEntryViewSet(viewsets.ModelViewSet):
    """본사 회계 분개 ViewSet"""
    queryset = CompanyAccountingEntry.objects.select_related(
        'company', 'sort', 'account_d1', 'account_d2', 'account_d3'
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
        fields = ('project', 'sort', 'project_account_d2', 'project_account_d3',
                  'evidence_type', 'transaction_id')


class ProjectAccountingEntryViewSet(viewsets.ModelViewSet):
    """프로젝트 회계 분개 ViewSet"""
    queryset = ProjectAccountingEntry.objects.select_related(
        'project', 'sort', 'project_account_d2', 'project_account_d3'
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

    def create(self, request):
        """본사 거래 생성 (은행거래 + 회계분개)"""
        serializer = CompanyCompositeTransactionSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                'bank_transaction': CompanyBankTransactionSerializer(result['bank_transaction']).data,
                'accounting_entries': CompanyAccountingEntrySerializer(result['accounting_entries'], many=True).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
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

    def partial_update(self, request, pk=None):
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


class ProjectCompositeTransactionViewSet(viewsets.ViewSet):
    """
    프로젝트 복합 거래 ViewSet

    은행 거래, 회계 분개, 계약 결제를 한 번에 생성/수정/관리합니다.
    프론트엔드 거래 관리 UI에서 사용합니다.
    """
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)

    def create(self, request):
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

    def update(self, request, pk=None):
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

    def partial_update(self, request, pk=None):
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
