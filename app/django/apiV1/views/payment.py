from datetime import datetime

from django.db.models import Sum, F
from django_filters import DateFilter, CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets

from _utils.contract_price import get_project_payment_summary
from items.models import KeyUnit
from project.models import Project
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


class PaymentPerInstallmentViewSet(viewsets.ModelViewSet):
    queryset = PaymentPerInstallment.objects.all()
    serializer_class = PaymentPerInstallmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('sales_price__project', 'sales_price__order_group',
                        'sales_price__unit_type', 'pay_order')


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
                                              project_account_d3__is_payment=True)


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
                                              project_account_d3__is_payment=True,
                                              contract__activation=True,
                                              contract__contractor__status=2) \
            .order_by('contract__order_group', 'contract__unit_type') \
            .annotate(order_group=F('contract__order_group')) \
            .annotate(unit_type=F('contract__unit_type')) \
            .values('order_group', 'unit_type') \
            .annotate(paid_sum=Sum('income'))


class OverallSummaryViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def list(self, request):
        project_id = request.query_params.get('project')
        date = request.query_params.get('date', datetime.today().strftime('%Y-%m-%d'))

        if not project_id:
            return Response({'error': 'project parameter is required'}, status=400)

        # 프로젝트 및 납부 회차 데이터 조회
        project = Project.objects.get(id=project_id)
        pay_orders = InstallmentPaymentOrder.objects.filter(project_id=project_id).order_by('pay_code', 'pay_time')

        # 핵심 최적화: PostgreSQL JSON 집계를 사용한 효율적인 납부 금액 캐시
        payment_amounts_cache = self._get_payment_amounts_cache(project_id, pay_orders)

        # 수납 데이터를 배치로 조회하여 캐시
        collection_cache = self._get_all_collection_data(project_id, date, pay_orders)

        result_pay_orders = []

        for order in pay_orders:
            # 캐시된 계약 금액 사용
            contract_amount = payment_amounts_cache.get(order.pay_sort, 0)

            # 캐시된 수납 데이터 사용
            collection_data = collection_cache.get(order.pk, {
                'collected_amount': 0,
                'discount_amount': 0,
                'overdue_fee': 0,
                'actual_collected': 0,
                'collection_rate': 0
            })

            # 기간도래 관련 집계 (최적화된 계산)
            due_period_data = self._get_due_period_data_optimized(order, contract_amount, collection_data, date)

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
        """해당 회차의 계약 금액 합계 계산 (JSON 필드 기반 집계, pay_time 사용)"""
        from contract.models import ContractPrice
        from django.db.models import Sum
        from payment.models import InstallmentPaymentOrder

        try:
            # 해당 pay_sort에 속하는 모든 pay_time들 조회
            pay_times = InstallmentPaymentOrder.objects.filter(
                project_id=project_id,
                pay_sort=order.pay_sort
            ).values_list('pay_time', flat=True)

            if not pay_times:
                return 0

            # PostgreSQL JSON 집계를 사용한 효율적인 계산
            from django.db import connection
            with connection.cursor() as cursor:
                placeholders = ','.join(['%s'] * len(pay_times))
                cursor.execute(f"""
                    SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_amount
                    FROM contract_contractprice,
                         jsonb_each_text(payment_amounts)
                    WHERE contract_id IN (
                        SELECT id FROM contract_contract WHERE project_id = %s
                    ) AND is_cache_valid = true
                    AND key IN ({placeholders})
                """, [project_id] + [str(pt) for pt in pay_times])

                result = cursor.fetchone()
                total_amount = result[0] if result else 0

            # 캐시 무효화된 계약이 있으면 동적 계산으로 폴백
            invalid_cache_count = ContractPrice.objects.filter(
                contract__project_id=project_id,
                is_cache_valid=False
            ).count()

            if invalid_cache_count > 0:
                # 일부 캐시가 무효화된 경우 동적 계산과 병합
                fallback_amount = OverallSummaryViewSet._get_contract_amount_fallback(order, project_id)
                return total_amount + fallback_amount

            return total_amount

        except Exception as e:
            # 완전 실패 시 동적 계산으로 폴백
            return OverallSummaryViewSet._get_contract_amount_fallback(order, project_id)

    @staticmethod
    def _get_contract_amount_fallback(order, project_id):
        """캐시 실패 시 동적 계산 폴백"""
        from contract.models import Contract
        from _utils.contract_price import get_contract_payment_plan

        contracts = Contract.objects.filter(
            project_id=project_id
        ).select_related('contractprice').filter(
            contractprice__is_cache_valid=False
        )

        total_amount = 0

        for contract in contracts:
            try:
                payment_plan = get_contract_payment_plan(contract)
                for plan_item in payment_plan:
                    if plan_item['installment_order'].pay_sort == order.pay_sort:
                        total_amount += plan_item['amount']
            except Exception:
                continue

        return total_amount

    def _get_payment_amounts_cache(self, project_id, pay_orders):
        """PostgreSQL JSON 집계를 사용한 효율적인 납부 금액 캐시 생성 (pay_time 기반)"""
        from django.db import connection

        # pay_sort별로 해당하는 pay_time들을 매핑
        pay_sort_to_times = {}
        for order in pay_orders:
            if order.pay_sort not in pay_sort_to_times:
                pay_sort_to_times[order.pay_sort] = []
            pay_sort_to_times[order.pay_sort].append(str(order.pay_time))

        payment_amounts_cache = {}

        try:
            with connection.cursor() as cursor:
                # pay_sort별로 해당하는 pay_time들의 금액을 집계
                for pay_sort, pay_times in pay_sort_to_times.items():
                    placeholders = ','.join(['%s'] * len(pay_times))
                    cursor.execute(f"""
                        SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_amount
                        FROM contract_contractprice,
                             jsonb_each_text(payment_amounts)
                        WHERE contract_id IN (
                            SELECT id FROM contract_contract WHERE project_id = %s
                        ) AND is_cache_valid = true
                        AND key IN ({placeholders})
                    """, [project_id] + pay_times)

                    result = cursor.fetchone()
                    payment_amounts_cache[pay_sort] = result[0] if result else 0

        except Exception as e:
            # 실패 시 기존 방식으로 폴백
            print(f"JSON aggregation failed: {e}")
            for order in pay_orders:
                payment_amounts_cache[order.pay_sort] = self._get_contract_amount(order, project_id)

        return payment_amounts_cache

    def _get_all_collection_data(self, project_id, date, pay_orders):
        """모든 납부 회차의 수납 데이터를 배치로 조회하여 캐시 생성"""
        from django.db.models import Q

        # 모든 납부 회차의 수납 데이터를 한 번에 조회
        order_ids = [order.pk for order in pay_orders]
        payments_data = ProjectCashBook.objects.filter(
            project_id=project_id,
            installment_order__in=order_ids,
            income__isnull=False,
            deal_date__lte=date
        ).values('installment_order').annotate(
            total_collected=Sum('income')
        )

        # 수납 데이터를 딕셔너리로 변환
        payments_dict = {item['installment_order']: item['total_collected'] for item in payments_data}

        collection_cache = {}

        for order in pay_orders:
            collected_amount = payments_dict.get(order.pk, 0)

            # TODO: 실제 할인료, 연체료 계산 로직 구현 필요
            discount_amount = 0
            overdue_fee = 0
            actual_collected = collected_amount + overdue_fee - discount_amount

            collection_cache[order.pk] = {
                'collected_amount': collected_amount,
                'discount_amount': discount_amount,
                'overdue_fee': overdue_fee,
                'actual_collected': actual_collected,
                'collection_rate': 0  # 나중에 계산
            }

        return collection_cache

    def _get_due_period_data_optimized(self, order, contract_amount, collection_data, date):
        """최적화된 기간도래 관련 데이터 집계 (캐시된 데이터 사용)"""

        # 캐시된 수납 데이터 사용
        collected_amount = collection_data['collected_amount']

        # 기간도래 미수금 = 계약금액 - 수납액
        unpaid_amount = max(0, contract_amount - collected_amount)
        unpaid_rate = (unpaid_amount / contract_amount * 100) if contract_amount > 0 else 0

        # TODO: 기간도래분 연체료 계산 로직 구현 필요
        overdue_fee = 0
        subtotal = unpaid_amount + overdue_fee

        # collection_rate 계산 및 업데이트
        collection_rate = (collection_data['actual_collected'] / contract_amount * 100) if contract_amount > 0 else 0
        collection_data['collection_rate'] = round(collection_rate, 2)

        return {
            'contract_amount': contract_amount,
            'unpaid_amount': unpaid_amount,
            'unpaid_rate': round(unpaid_rate, 2),
            'overdue_fee': overdue_fee,
            'subtotal': subtotal
        }

    def _get_collection_data(self, order, project_id, date):
        """수납 관련 데이터 집계 (레거시 메서드 - 사용하지 않음)"""
        # 이 메서드는 이제 사용하지 않지만 호환성을 위해 유지
        payments = ProjectCashBook.objects.filter(
            project_id=project_id,
            installment_order=order,
            income__isnull=False,
            deal_date__lte=date
        )

        collected_amount = payments.aggregate(total=Sum('income'))['total'] or 0
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
        """기간도래 관련 데이터 집계 (레거시 메서드 - 사용하지 않음)"""
        # 이 메서드는 이제 사용하지 않지만 호환성을 위해 유지
        contract_amount = self._get_contract_amount(order, project_id)

        collected_amount = ProjectCashBook.objects.filter(
            project_id=project_id,
            installment_order=order,
            income__isnull=False,
            deal_date__lte=date
        ).aggregate(total=Sum('income'))['total'] or 0

        unpaid_amount = max(0, contract_amount - collected_amount)
        unpaid_rate = (unpaid_amount / contract_amount * 100) if contract_amount > 0 else 0

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
