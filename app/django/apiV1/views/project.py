from datetime import datetime

from django.db.models import Sum, F, Case, When
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets
from rest_framework.decorators import action

from ledger.models import ProjectAccountingEntry

from ..pagination import *
from ..permission import *
from ..serializers.project import *

TODAY = datetime.today().strftime('%Y-%m-%d')


# Project --------------------------------------------------------------------------
class ProjectFilterSet(FilterSet):
    class Meta:
        model = Project
        fields = ('kind', 'start_year', 'is_direct_manage', 'is_returned_area',
                  'is_unit_set', 'issue_project__status')


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = ProjectFilterSet


class ProjectIncBudgetViewSet(viewsets.ModelViewSet):
    queryset = ProjectIncBudget.objects.all()
    serializer_class = ProjectIncBudgetSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'unit_type__sort')


class ProjectOutBudgetViewSet(viewsets.ModelViewSet):
    queryset = ProjectOutBudget.objects.all()
    serializer_class = ProjectOutBudgetSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)


class StatusOutBudgetViewSet(ProjectOutBudgetViewSet):
    serializer_class = StatusOutBudgetSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        use_ledger = self.request.query_params.get('use_ledger', 'false').lower() == 'true'

        if use_ledger:
            # ledger 기반: account가 있고, depth=2, is_category_only=False인 예산만
            queryset = queryset.select_related('account', 'account__parent').filter(
                account__isnull=False,
                account__depth=2,
                account__category='expense',
                account__is_category_only=False
            )
        return queryset


class ExecAmountToBudgetViewSet(viewsets.ModelViewSet):
    serializer_class = ExecAmountToBudget
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_serializer_class(self):
        use_ledger = self.request.query_params.get('use_ledger', 'false').lower() == 'true'
        if use_ledger:
            return LedgerExecAmountToBudgetSerializer
        return ExecAmountToBudget

    def get_queryset(self):
        use_ledger = self.request.query_params.get('use_ledger', 'false').lower() == 'true'
        project = self.request.query_params.get('project')
        request_date = self.request.query_params.get('date')
        date = request_date if request_date else TODAY
        month_first = datetime(datetime.strptime(date, '%Y-%m-%d').year,
                               datetime.strptime(date, '%Y-%m-%d').month,
                               1).strftime('%Y-%m-%d')

        if use_ledger:
            # ledger 기반: ProjectAccountingEntry에서 집계
            from ledger.models import ProjectBankTransaction

            queryset = ProjectAccountingEntry.objects.filter(
                account__depth=2,
                account__is_category_only=False,
                account__category='expense',
            ).select_related('account')

            if project:
                queryset = queryset.filter(project_id=project)

            # 출금 거래만 (sort_id=2)
            valid_transaction_ids = ProjectBankTransaction.objects.filter(
                sort_id=2,
                deal_date__lte=date
            ).values_list('transaction_id', flat=True)

            queryset = queryset.filter(transaction_id__in=valid_transaction_ids)

            # 당월 거래 ID
            month_transaction_ids = list(ProjectBankTransaction.objects.filter(
                sort_id=2,
                deal_date__gte=month_first,
                deal_date__lte=date
            ).values_list('transaction_id', flat=True))

            return queryset.values('account').annotate(
                all_sum=Sum('amount'),
                month_sum=Sum(Case(
                    When(transaction_id__in=month_transaction_ids, then=F('amount')),
                    default=0
                ))
            )
        else:
            # ibs 기반: ProjectCashBook에서 집계 (기존 로직)
            queryset = ProjectCashBook.objects.filter(income=None) \
                .order_by('project_account_d3') \
                .filter(is_separate=False,
                        project_account_d3__d2__gte=8,
                        project_account_d3__d2__lte=15,
                        deal_date__lte=date)

            if project:
                queryset = queryset.filter(project_id=project)

            return queryset.annotate(acc_d3=F('project_account_d3')) \
                .values('acc_d3') \
                .annotate(all_sum=Sum('outlay'),
                          month_sum=Sum(Case(
                              When(deal_date__gte=month_first, then=F('outlay')),
                              default=0
                          )))


class TotalSiteAreaViewSet(viewsets.ModelViewSet):
    serializer_class = TotalSiteAreaSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        return Site.objects.values('project') \
            .annotate(official=Sum('official_area'),
                      returned=Sum('returned_area'))


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('project',)
    search_fields = ('district', 'lot_number', 'site_purpose', 'owners__owner')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class AllSiteViewSet(SiteViewSet):
    serializer_class = AllSiteSerializer
    pagination_class = PageNumberPaginationFiveHundred


class TotalOwnerAreaViewSet(viewsets.ModelViewSet):
    serializer_class = TotalOwnerAreaSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        return Site.objects.values('project') \
            .annotate(owned_area=Sum('siteownshiprelationship__owned_area'))


class SiteOwnerViewSet(viewsets.ModelViewSet):
    queryset = SiteOwner.objects.all()
    serializer_class = SiteOwnerSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('project', 'own_sort', 'use_consent')
    search_fields = ('owner', 'phone1', 'phone2', 'sites__lot_number', 'note')

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
        except SiteOwner.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        # SiteOwner 모델의 기본 정렬이 -id 순(최신순)이므로 해당 항목보다 앞에 있는 항목 개수 계산
        items_before = queryset.filter(id__gt=target_item.id).count()

        # 페이지 크기 파라미터 읽기 (기본값: 10)
        page_size = request.query_params.get('limit', '10')
        try:
            page_size = int(page_size) if page_size else 10
        except ValueError:
            page_size = 10

        # 동적 페이지 크기로 계산
        page_number = (items_before // page_size) + 1

        return Response({'page': page_number})


class AllOwnerViewSet(SiteOwnerViewSet):
    queryset = SiteOwner.objects.all().order_by('id')
    serializer_class = AllOwnerSerializer
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('project',)


class SiteRelationViewSet(viewsets.ModelViewSet):
    queryset = SiteOwnshipRelationship.objects.all()
    serializer_class = SiteOwnshipRelationshipSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class TotalContractedAreaViewSet(viewsets.ModelViewSet):
    serializer_class = TotalContractedAreaSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        return SiteContract.objects.values('project') \
            .annotate(contracted_area=Sum('contract_area'))


class SiteContractViewSet(viewsets.ModelViewSet):
    queryset = SiteContract.objects.all()
    serializer_class = SiteContractSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('project', 'owner__own_sort')
    search_fields = ('owner__owner', 'owner__phone1', 'acc_bank', 'acc_owner', 'note')

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
        except SiteContract.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        # SiteContract 모델의 기본 정렬이 -id 순(최신순)이므로 해당 항목보다 앞에 있는 항목 개수 계산
        items_before = queryset.filter(id__gt=target_item.id).count()

        # 페이지 크기 파라미터 읽기 (기본값: 10)
        page_size = request.query_params.get('limit', '10')
        try:
            page_size = int(page_size) if page_size else 10
        except ValueError:
            page_size = 10

        # 동적 페이지 크기로 계산
        page_number = (items_before // page_size) + 1

        return Response({'page': page_number})
