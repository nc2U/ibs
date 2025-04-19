from datetime import datetime

from django.db.models import Sum, F
from django_filters import DateFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets

from cash.models import ProjectCashBook
from payment.models import SalesPriceByGT, InstallmentPaymentOrder, DownPayment, OverDueRule
from .cash import ProjectCashBookViewSet
from ..pagination import *
from ..permission import *
from ..serializers.payment import *

TODAY = datetime.today().strftime('%Y-%m-%d')


# Payment --------------------------------------------------------------------------


class InstallmentOrderViewSet(viewsets.ModelViewSet):
    queryset = InstallmentPaymentOrder.objects.all()
    serializer_class = InstallmentOrderSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('project', 'pay_sort', 'is_pm_cost')
    search_fields = ('pay_name', 'alias_name')


class SalesPriceViewSet(viewsets.ModelViewSet):
    queryset = SalesPriceByGT.objects.all()
    serializer_class = SalesPriceSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'order_group', 'unit_type')


class DownPaymentViewSet(viewsets.ModelViewSet):
    queryset = DownPayment.objects.all()
    serializer_class = DownPaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('project', 'order_group', 'unit_type')


class OverDueRuleViewSet(viewsets.ModelViewSet):
    queryset = OverDueRule.objects.all()
    serializer_class = OverDueRuleSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class PaymentViewSet(ProjectCashBookViewSet):
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationTen

    def get_queryset(self):
        return ProjectCashBook.objects.filter(income__isnull=False,
                                              project_account_d3__in=(1, 4))


class AllPaymentViewSet(PaymentViewSet):
    pagination_class = PageNumberPaginationOneHundred


class PaymentSumFilterSet(FilterSet):
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='납부일자까지')

    class Meta:
        model = ProjectCashBook
        fields = ('project', 'to_deal_date')


class PaymentSummaryViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = PaymentSumFilterSet

    def get_queryset(self):
        return ProjectCashBook.objects.filter(income__isnull=False,
                                              project_account_d3__in=(1, 4),
                                              contract__activation=True,
                                              contract__contractor__status=2) \
            .order_by('contract__order_group', 'contract__unit_type') \
            .annotate(order_group=F('contract__order_group')) \
            .annotate(unit_type=F('contract__unit_type')) \
            .values('order_group', 'unit_type') \
            .annotate(paid_sum=Sum('income'))

# class ContNumByTypeViewSet(viewsets.ModelViewSet):
#     """
#     타입별 계약 건수
#     """
#     serializer_class = ContNumByTypeSerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#     filterset_fields = ('project',)
#
#     def get_queryset(self):
#         return Contract.objects.filter(activation=True, contractor__status=2) \
#             .values('order_group', 'unit_type') \
#             .annotate(num_cont=Count('unit_type'))


# class PaidByContSummaryViewSet(viewsets.ModelViewSet):
#     """
#     계약건 및 회차별 완납자 수, 통계
#     """
#     serializer_class = PaidByContSummarySerializer
#     permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
#     filterset_fields = ('project',)
#
#     def get_queryset(self):
#         return Contract.objects.filter(activation=True, contractor__status=2) \
#             .values('order_group', 'unit_type') \
#             .annotate(num_cont=Count('unit_type'))
