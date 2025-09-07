from datetime import datetime
from django.db.models import Sum, F, Q, Case, When
from django.template.defaultfilters import default
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import FilterSet
from django_filters import DateFilter, BooleanFilter

from ..permission import *
from ..pagination import *
from ..serializers.cash import *

from cash.models import (BankCode, CompanyBankAccount, ProjectBankAccount,
                         CashBook, ProjectCashBook)

TODAY = datetime.today().strftime('%Y-%m-%d')


# Cash --------------------------------------------------------------------------
class BankCodeViewSet(viewsets.ModelViewSet):
    queryset = BankCode.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifty
    serializer_class = BankCodeSerializer


class ComBankAccountViewSet(viewsets.ModelViewSet):
    queryset = CompanyBankAccount.objects.all()
    serializer_class = CompanyBankAccountSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_fields = ('company', 'depart', 'is_hide', 'inactive')


class BalanceByAccFilterSet(FilterSet):
    is_balance = BooleanFilter(method='_is_balance', label='잔고 존재 여부')

    class Meta:
        model = CashBook
        fields = ('company', 'is_balance')

    @staticmethod
    def _is_balance(queryset, name, value):
        # ProjectCashBook 모델의 income과 outlay를 합산해 비교
        filtered_queryset = queryset.annotate(
            total_income=Sum('income', default=0),
            total_outlay=Sum('outlay', default=0),
            balance=F('total_income') - F('total_outlay')
        )
        if value:  # True인 경우, 잔액이 양수인 경우만 필터링
            return filtered_queryset.filter(balance__gt=0)
        else:  # False인 경우, 잔액이 0 이하인 경우만 필터링
            return filtered_queryset.filter(balance__lte=0)


class BalanceByAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BalanceByAccountSerializer
    pagination_class = PageNumberPaginationOneHundred
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_class = BalanceByAccFilterSet

    def get_queryset(self):
        date = self.request.query_params.get('date')
        date = date if date else TODAY

        queryset = CashBook.objects.all() \
            .order_by('bank_account') \
            .filter(is_separate=False, deal_date__lte=date)

        return queryset.annotate(bank_acc=F('bank_account__alias_name'),
                                 bank_num=F('bank_account__number')) \
            .values('bank_acc', 'bank_num') \
            .annotate(inc_sum=Sum('income', default=0),
                      out_sum=Sum('outlay', default=0),
                      balance=Sum('income', default=0) - Sum('outlay', default=0),
                      date_inc=Sum(Case(
                          When(deal_date=date, then=F('income')),
                          default=0
                      )),
                      date_out=Sum(Case(
                          When(deal_date=date, then=F('outlay')),
                          default=0
                      )))


class CashBookFilterSet(FilterSet):
    from_deal_date = DateFilter(field_name='deal_date', lookup_expr='gte', label='납부일자부터')
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='납부일자까지')

    class Meta:
        model = CashBook
        fields = ('company', 'from_deal_date', 'to_deal_date', 'sort', 'account_d1',
                  'account_d2', 'account_d3', 'project', 'is_return', 'bank_account')


class CashBookViewSet(viewsets.ModelViewSet):
    queryset = CashBook.objects.all()
    serializer_class = CashBookSerializer
    pagination_class = PageNumberPaginationFifteen
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_class = CashBookFilterSet
    search_fields = ('content', 'trader', 'note')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

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
        except CashBook.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
            
        # 해당 항목보다 앞에 있는 항목 개수 계산 (동일한 정렬 조건 적용)
        items_before = queryset.filter(
            Q(deal_date__gt=target_item.deal_date) |
            (Q(deal_date=target_item.deal_date) & Q(id__gt=target_item.id))
        ).count()
        
        # 페이지 크기는 15개
        page_size = 15
        page_number = (items_before // page_size) + 1
        
        return Response({'page': page_number})


class CompanyCashCalcViewSet(viewsets.ModelViewSet):
    queryset = CompanyCashBookCalculation.objects.all()
    serializer_class = CompanyCashCalcSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_fields = ('company',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class CompanyLastDealDateViewSet(viewsets.ModelViewSet):
    queryset = CashBook.objects.all()
    serializer_class = CompanyLastDealDateSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)

    def get_queryset(self):
        company = self.request.query_params.get('company')
        return CashBook.objects.filter(company_id=company).order_by('-deal_date')[:1]


class DateCashBookViewSet(CashBookViewSet):
    pagination_class = PageNumberPaginationTwoHundred

    def get_queryset(self):
        date = self.request.query_params.get('date')
        date = date if date else TODAY
        return CashBook.objects.filter(is_separate=False,
                                       deal_date__exact=date).order_by('deal_date', 'created_at', 'id')


class ProjectBankAccountViewSet(viewsets.ModelViewSet):
    queryset = ProjectBankAccount.objects.all()
    serializer_class = ProjectBankAccountSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'is_hide', 'inactive', 'directpay', 'is_imprest')


class PrBalanceByAccFilterSet(FilterSet):
    is_balance = BooleanFilter(method='_is_balance', label='잔고 존재 여부')

    class Meta:
        model = ProjectCashBook
        fields = ('project', 'bank_account__directpay', 'is_balance')

    @staticmethod
    def _is_balance(queryset, name, value):
        # ProjectCashBook 모델의 income과 outlay를 합산해 비교
        filtered_queryset = queryset.annotate(
            total_income=Sum('income', default=0),
            total_outlay=Sum('outlay', default=0),
            balance=F('total_income') - F('total_outlay')
        )
        if value:  # True인 경우, 잔액이 양수인 경우만 필터링
            return filtered_queryset.filter(balance__gt=0)
        else:  # False인 경우, 잔액이 0 이하인 경우만 필터링
            return filtered_queryset.filter(balance__lte=0)


class PrBalanceByAccountViewSet(viewsets.ModelViewSet):
    serializer_class = PrBalanceByAccountSerializer
    pagination_class = PageNumberPaginationOneHundred
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = PrBalanceByAccFilterSet

    def get_queryset(self):
        date = self.request.query_params.get('date')
        date = date if date else TODAY

        queryset = ProjectCashBook.objects.all() \
            .order_by('bank_account') \
            .filter(is_separate=False,
                    deal_date__lte=date)

        return queryset.annotate(bank_acc=F('bank_account__alias_name'),
                                 bank_num=F('bank_account__number')) \
            .values('bank_acc', 'bank_num') \
            .annotate(inc_sum=Sum('income', default=0),
                      out_sum=Sum('outlay', default=0),
                      balance=Sum('income', default=0) - Sum('outlay', default=0),
                      date_inc=Sum(Case(
                          When(deal_date=date, then=F('income')),
                          default=0
                      )),
                      date_out=Sum(Case(
                          When(deal_date=date, then=F('outlay')),
                          default=0
                      )))


class ProjectCashBookFilterSet(FilterSet):
    from_deal_date = DateFilter(field_name='deal_date', lookup_expr='gte', label='납부일자부터')
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='납부일자까지')
    no_contract = BooleanFilter(field_name='contract', lookup_expr='isnull', label='계약 미등록')
    no_install = BooleanFilter(field_name='installment_order', lookup_expr='isnull', label='회차 미등록')

    class Meta:
        model = ProjectCashBook
        fields = ('project', 'sort', 'project_account_d2__d1', 'project_account_d2',
                  'project_account_d3', 'is_imprest', 'from_deal_date', 'to_deal_date',
                  'deal_date', 'installment_order', 'bank_account', 'contract',
                  'contract__order_group', 'contract__unit_type', 'no_contract', 'no_install')


class ProjectCashBookViewSet(viewsets.ModelViewSet):
    queryset = ProjectCashBook.objects.all()  # filter(is_imprest=False)
    serializer_class = ProjectCashBookSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationFifteen
    filterset_class = ProjectCashBookFilterSet
    search_fields = ('contract__contractor__name', 'content', 'trader', 'note')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

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
        except ProjectCashBook.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
            
        # 해당 항목보다 앞에 있는 항목 개수 계산 (동일한 정렬 조건 적용)
        items_before = queryset.filter(
            Q(deal_date__gt=target_item.deal_date) |
            (Q(deal_date=target_item.deal_date) & Q(id__gt=target_item.id))
        ).count()
        
        # 페이지 크기는 15개
        page_size = 15
        page_number = (items_before // page_size) + 1
        
        return Response({'page': page_number})


class ProjectCashCalcViewSet(viewsets.ModelViewSet):
    queryset = ProjectCashBookCalculation.objects.all()
    serializer_class = ProjectCashCalcSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_fields = ('project',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ProjectLastDealDateViewSet(viewsets.ModelViewSet):
    queryset = ProjectCashBook.objects.all()
    serializer_class = ProjectLastDealDateSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)

    def get_queryset(self):
        project = self.request.query_params.get('project')
        return ProjectCashBook.objects.filter(project_id=project).order_by('-deal_date')[:1]


class ProjectDateCashBookViewSet(ProjectCashBookViewSet):
    pagination_class = PageNumberPaginationTwoHundred

    def get_queryset(self):
        date = self.request.query_params.get('date')
        date = date if date else TODAY
        return ProjectCashBook.objects.filter(is_separate=False,
                                              deal_date__exact=date).order_by('deal_date', 'created_at', 'id')


class ProjectImprestViewSet(ProjectCashBookViewSet):
    queryset = ProjectCashBook.objects.filter(is_imprest=True)  # .exclude(project_account_d3=63, income__isnull=True)
