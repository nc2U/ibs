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

    def get_queryset(self):
        """list action일 때만 부모 레코드만 반환"""
        queryset = super().get_queryset()
        # list action일 때만 부모 레코드만 반환 (자식 레코드는 제외)
        # retrieve/update/delete 등 detail action에서는 자식 레코드도 접근 가능
        if self.action == 'list':
            return queryset.filter(separated__isnull=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """
        특정 부모 거래의 분리 항목 조회 (페이지네이션 적용)

        사용법:
            GET /api/v1/cashbook/{pk}/children/
            GET /api/v1/cashbook/{pk}/children/?page=2

        페이지네이션: 페이지당 15개 항목 (부모 목록과 동일)
        """
        parent = self.get_object()
        children = CashBook.objects.filter(
            separated=parent
        ).select_related(
            'account_d1', 'account_d2', 'account_d3', 'updator'
        ).order_by('id')

        # 페이지네이션 적용
        paginator = PageNumberPaginationFifteen()
        page = paginator.paginate_queryset(children, request)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

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

        # 프론트엔드에서 사용하는 페이지 크기 (동적으로 가져오기)
        page_size = int(request.query_params.get('limit', '15'))
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
                                       deal_date__exact=date).order_by('deal_date', 'created', 'id')


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
    parents_only = BooleanFilter(method='filter_parents_only', label='부모 레코드만')

    class Meta:
        model = ProjectCashBook
        fields = ('project', 'sort', 'project_account_d2__d1', 'project_account_d2',
                  'project_account_d3', 'is_imprest', 'from_deal_date', 'to_deal_date', 'deal_date',
                  'installment_order', 'bank_account', 'contract', 'contract__order_group',
                  'contract__unit_type', 'no_contract', 'no_install', 'parents_only')

    @staticmethod
    def filter_parents_only(queryset, name, value):
        """
        부모 레코드만 필터링 (은행 거래 내역만)
        parents_only=true: separated가 NULL인 레코드만 (자식 레코드 제외)
        parents_only=false: 모든 레코드 (기본 동작)

        참고:
        - 부모 레코드: separated=NULL (자식 유무와 관계없이)
        - 자식 레코드: separated가 부모 PK를 참조
        """
        if value:
            return queryset.filter(separated__isnull=True)
        return queryset


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

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """
        특정 부모 거래의 분리 항목 조회 (페이지네이션 적용)

        사용법:
            GET /api/v1/project-cashbook/{pk}/children/
            GET /api/v1/project-cashbook/{pk}/children/?page=2
            GET /api/v1/project-cashbook/{pk}/children/?search=검색어

        페이지네이션: 페이지당 15개 항목 (부모 목록과 동일)
        검색 지원: content, trader, note 필드 검색
        """
        parent = self.get_object()
        children = ProjectCashBook.objects.filter(
            separated=parent
        ).select_related(
            'project_account_d2', 'project_account_d3', 'updator'
        ).order_by('id')

        # 검색 필터링 적용
        search_query = request.query_params.get('search')
        if search_query:
            children = children.filter(
                Q(content__icontains=search_query) |
                Q(trader__icontains=search_query) |
                Q(note__icontains=search_query)
            )

        # 페이지네이션 적용 (부모와 동일한 15개)
        page = self.paginate_queryset(children)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # 페이지네이션이 없는 경우 (fallback)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_with_children(self, request):
        """
        계약자 이름으로 검색 시 자식 레코드까지 포함한 통합 검색

        사용법:
            GET /api/v1/project-cashbook/search_with_children/?project=1&search=홍길동

        응답:
            {
                "parents_with_children": [
                    {
                        "parent": {...부모 레코드},
                        "matching_children": [...검색에 해당하는 자식 레코드들]
                    }
                ]
            }
        """
        project = request.query_params.get('project')
        search_query = request.query_params.get('search')

        if not project:
            return Response({'error': 'project parameter required'}, status=400)

        if not search_query:
            return Response({'error': 'search parameter required'}, status=400)

        # 검색 조건에 맞는 부모 레코드들 찾기
        parent_queryset = ProjectCashBook.objects.filter(
            project=project,
            separated__isnull=True
        ).filter(
            Q(contract__contractor__name__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(trader__icontains=search_query) |
            Q(note__icontains=search_query)
        )

        # 검색 조건에 맞는 자식 레코드의 부모들도 포함
        child_parent_ids = ProjectCashBook.objects.filter(
            project=project,
            separated__isnull=False
        ).filter(
            Q(content__icontains=search_query) |
            Q(trader__icontains=search_query) |
            Q(note__icontains=search_query)
        ).values_list('separated', flat=True).distinct()

        # 부모 레코드와 관련 자식 레코드가 있는 부모들을 합치기
        all_parent_ids = list(parent_queryset.values_list('pk', flat=True)) + list(child_parent_ids)
        all_parent_ids = list(set(all_parent_ids))  # 중복 제거

        final_parents = ProjectCashBook.objects.filter(
            pk__in=all_parent_ids
        ).select_related(
            'project_account_d2', 'project_account_d3', 'contract', 'contract__contractor'
        )

        results = []
        for parent in final_parents:
            # 해당 부모의 자식들 중 검색 조건에 맞는 것들만
            matching_children = ProjectCashBook.objects.filter(
                separated=parent
            ).filter(
                Q(content__icontains=search_query) |
                Q(trader__icontains=search_query) |
                Q(note__icontains=search_query)
            ).select_related(
                'project_account_d2', 'project_account_d3'
            )

            parent_serializer = self.get_serializer(parent)
            children_serializer = self.get_serializer(matching_children, many=True)

            results.append({
                'parent': parent_serializer.data,
                'matching_children': children_serializer.data
            })

        return Response({'parents_with_children': results})

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

        # 프론트엔드에서 사용하는 페이지 크기 (동적으로 가져오기)
        page_size = int(request.query_params.get('limit', '15'))
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
                                              deal_date__exact=date).order_by('deal_date', 'created', 'id')


class ProjectImprestViewSet(ProjectCashBookViewSet):
    queryset = ProjectCashBook.objects.filter(is_imprest=True)  # .exclude(project_account_d3=63, income__isnull=True)
