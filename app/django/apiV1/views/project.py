from datetime import datetime

from django.db.models import Sum, F, Case, When
from django_filters.rest_framework import FilterSet, BooleanFilter
from rest_framework import viewsets

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


class ExecAmountToBudgetViewSet(viewsets.ModelViewSet):
    serializer_class = ExecAmountToBudget
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        request_date = self.request.query_params.get('date')
        date = request_date if request_date else TODAY
        month_first = datetime(datetime.strptime(date, '%Y-%m-%d').year,
                               datetime.strptime(date, '%Y-%m-%d').month,
                               1).strftime('%Y-%m-%d')

        queryset = ProjectCashBook.objects.filter(income=None) \
            .order_by('project_account_d3') \
            .filter(is_separate=False,  # 상세 분리 기록 = False (중복 방지)
                    project_account_d3__d2__gte=8,  # 비용 계정 범위 시작
                    project_account_d3__d2__lte=15,  # 비용 계정 범위 종료
                    deal_date__lte=date)

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
        serializer.save()


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
    search_fields = ('owner', 'phone1', 'phone2', 'sites__lot_number', 'counsel_record')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


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
        serializer.save()
