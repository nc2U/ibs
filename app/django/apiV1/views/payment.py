from datetime import datetime

from django.db.models import Sum, F
from django_filters import DateFilter, CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets

from items.models import KeyUnit
from .cash import ProjectCashBookViewSet
from ..pagination import *
from ..permission import *
from ..serializers.payment import *

TODAY = datetime.today().strftime('%Y-%m-%d')


# Payment --------------------------------------------------------------------------


class InstallmentOrderFilterSet(FilterSet):
    pay_sort__in = CharFilter(method='filter_pay_sort_in', label='납부 종류 다중 선택')

    class Meta:
        model = InstallmentPaymentOrder
        fields = ['project', 'pay_sort']

    def filter_pay_sort_in(self, queryset, name, value):
        """
        pay_sort__in 파라미터로 다중 선택 필터링
        예: ?pay_sort__in=1,4,5,6,7
        """
        if value:
            # 쉼표로 구분된 값들을 리스트로 변환
            pay_sorts = [sort.strip() for sort in value.split(',') if sort.strip()]
            if pay_sorts:
                return queryset.filter(pay_sort__in=pay_sorts)
        return queryset


class InstallmentOrderViewSet(viewsets.ModelViewSet):
    queryset = InstallmentPaymentOrder.objects.all()
    serializer_class = InstallmentOrderSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwenty
    filterset_class = InstallmentOrderFilterSet
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


class OverallSummaryViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def list(self, request):
        project_id = request.query_params.get('project')
        date = request.query_params.get('date', datetime.today().strftime('%Y-%m-%d'))

        if not project_id:
            return Response({'error': 'project parameter is required'}, status=400)

        # 납부 회차 데이터 조회
        pay_orders = InstallmentPaymentOrder.objects.filter(project_id=project_id).order_by('pay_code', 'pay_time')

        result_pay_orders = []

        for order in pay_orders:
            # 해당 회차의 계약 금액 합계
            contract_amount = self._get_contract_amount(order, project_id)

            # 수납 관련 집계
            collection_data = self._get_collection_data(order, project_id, date)

            # 기간도래 관련 집계
            due_period_data = self._get_due_period_data(order, project_id, date)

            # 기간미도래 미수금
            not_due_unpaid = self._get_not_due_unpaid(order, project_id, date)

            # 총 미수금 및 비율
            total_unpaid = due_period_data['unpaid_amount'] + not_due_unpaid
            total_unpaid_rate = (total_unpaid / contract_amount * 100) if contract_amount > 0 else 0

            result_pay_orders.append({
                'pk': order.pk,
                'pay_name': order.pay_name,
                'pay_due_date': order.pay_due_date,
                'pay_sort': order.pay_sort,
                'contract_amount': contract_amount,
                'collection': collection_data,
                'due_period': due_period_data,
                'not_due_unpaid': not_due_unpaid,
                'total_unpaid': total_unpaid,
                'total_unpaid_rate': round(total_unpaid_rate, 2)
            })

        # 집계 데이터 조회
        aggregate_data = self._get_aggregate_data(project_id)

        result = {
            'pay_orders': result_pay_orders,
            'aggregate': aggregate_data
        }

        serializer = OverallSummarySerializer(result)
        return Response(serializer.data)

    @staticmethod
    def _get_contract_amount(order, project_id):
        """해당 회차의 계약 금액 합계 계산"""

        # pay_sort에 따라 계약 금액 계산
        if order.pay_sort == '1':  # 계약금
            amount = SalesPriceByGT.objects.filter(
                project_id=project_id
            ).aggregate(total=Sum('down_pay'))['total'] or 0
        elif order.pay_sort == '2':  # 중도금
            amount = SalesPriceByGT.objects.filter(
                project_id=project_id
            ).aggregate(total=Sum('middle_pay'))['total'] or 0
        elif order.pay_sort == '3':  # 잔금
            amount = SalesPriceByGT.objects.filter(
                project_id=project_id
            ).aggregate(total=Sum('remain_pay'))['total'] or 0
        else:  # 기타
            amount = 0

        return amount

    def _get_collection_data(self, order, project_id, date):
        """수납 관련 데이터 집계"""
        payments = ProjectCashBook.objects.filter(
            project_id=project_id,
            installment_order=order,
            income__isnull=False,
            deal_date__lte=date
        )

        collected_amount = payments.aggregate(total=Sum('income'))['total'] or 0
        # TODO: 실제 할인료, 연체료 계산 로직 구현 필요
        discount_amount = 0
        overdue_fee = 0
        actual_collected = collected_amount + overdue_fee - discount_amount

        contract_amount = self._get_contract_amount(order, project_id)
        collection_rate = (actual_collected / contract_amount * 100) if contract_amount > 0 else 0

        return {
            'collected_amount': collected_amount,
            'discount_amount': discount_amount,
            'overdue_fee': overdue_fee,
            'actual_collected': actual_collected,
            'collection_rate': round(collection_rate, 2)
        }

    def _get_due_period_data(self, order, project_id, date):
        """기간도래 관련 데이터 집계"""
        # 기준일 기준으로 기간이 도래한 계약 금액
        contract_amount = self._get_contract_amount(order, project_id)

        # 기간도래분 중 실제 수납된 금액
        collected_amount = ProjectCashBook.objects.filter(
            project_id=project_id,
            installment_order=order,
            income__isnull=False,
            deal_date__lte=date
        ).aggregate(total=Sum('income'))['total'] or 0

        # 기간도래 미수금 = 계약금액 - 수납액
        unpaid_amount = max(0, contract_amount - collected_amount)
        unpaid_rate = (unpaid_amount / contract_amount * 100) if contract_amount > 0 else 0

        # TODO: 기간도래분 연체료 계산 로직 구현 필요
        overdue_fee = 0
        subtotal = unpaid_amount + overdue_fee

        return {
            'contract_amount': contract_amount,
            'unpaid_amount': unpaid_amount,
            'unpaid_rate': round(unpaid_rate, 2),
            'overdue_fee': overdue_fee,
            'subtotal': subtotal
        }

    @staticmethod
    def _get_not_due_unpaid(order, project_id, date):
        """기간미도래 미수금 계산"""
        # TODO: 실제 기간미도래 로직 구현 필요
        # 현재는 0으로 반환
        return 0

    @staticmethod
    def _get_aggregate_data(project_id):
        """집계 데이터 조회"""

        # 계약 세대수
        conts_num = Contract.objects.filter(
            project_id=project_id,
            activation=True,
            contractor__status=2
        ).count()

        # 전체 세대수 (KeyUnit 기준)
        total_units = KeyUnit.objects.filter(project_id=project_id,
                                             unit_type__main_or_sub='1').count()

        # 미계약 세대수
        non_conts_num = total_units - conts_num

        # 계약률
        contract_rate = (conts_num / total_units * 100) if total_units > 0 else 0

        return {
            'conts_num': conts_num,
            'non_conts_num': non_conts_num,
            'total_units': total_units,
            'contract_rate': round(contract_rate, 2)
        }
