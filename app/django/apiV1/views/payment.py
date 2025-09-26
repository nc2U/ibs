from datetime import datetime, date

from django.db import connection
from django.db.models import Sum, F
from django_filters import DateFilter, CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets

import logging
from contract.models import ContractPrice
from items.models import KeyUnit
from .cash import ProjectCashBookViewSet
from ..pagination import *
from ..permission import *
from ..serializers.payment import *

logger = logging.getLogger(__name__)

TODAY = datetime.today().strftime('%Y-%m-%d')


# Payment --------------------------------------------------------------------------


class InstallmentOrderFilterSet(FilterSet):
    pay_sort__in = CharFilter(method='filter_pay_sort_in', label='납부 종류 다중 선택')

    class Meta:
        model = InstallmentPaymentOrder
        fields = ['project', 'pay_sort']

    @staticmethod
    def filter_pay_sort_in(queryset, name, value):
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
        pay_orders = InstallmentPaymentOrder.objects.filter(project_id=project_id).order_by('pay_code', 'pay_time')

        # 핵심 최적화: PostgreSQL JSON 집계를 사용한 효율적인 납부 금액 캐시
        payment_amounts_cache = self._get_payment_amounts_cache(project_id, pay_orders)

        # 미계약 세대 납부 금액 캐시
        non_contract_amounts_cache = self._get_non_contract_amounts_cache(project_id, pay_orders)

        # 수납 데이터를 배치로 조회하여 캐시
        collection_cache = self._get_all_collection_data(project_id, date, pay_orders)

        # 기간미도래 미수금 캐시 (성능 최적화)
        not_due_unpaid_cache = self._get_not_due_unpaid_cache(project_id, date, pay_orders, payment_amounts_cache, collection_cache)

        result_pay_orders = []

        for order in pay_orders:
            # 캐시된 계약 금액 사용 (pay_time 기준)
            contract_amount = payment_amounts_cache.get(order.pay_time, 0)

            # 캐시된 미계약 금액 사용 (pay_time 기준)
            non_contract_amount = non_contract_amounts_cache.get(order.pay_time, 0)

            # 캐시된 수납 데이터 사용
            collection_data = collection_cache.get(order.pk, {
                'collected_amount': 0,
                'discount_amount': 0,
                'overdue_fee': 0,
                'actual_collected': 0,
                'collection_rate': 0
            })

            # collection_rate 먼저 계산 (전체 계약금액 대비 실수납액)
            collection_rate = (collection_data['actual_collected'] / contract_amount * 100) if contract_amount > 0 else 0
            collection_data['collection_rate'] = round(collection_rate, 2)

            # 기간도래 관련 집계 (최적화된 계산)
            due_period_data = self._get_due_period_data_optimized(order, contract_amount, collection_data, date)

            # 기간미도래 미수금 (캐시된 데이터 사용)
            not_due_unpaid = not_due_unpaid_cache.get(order.pk, 0)

            # 총 미수금 및 비율
            total_unpaid = due_period_data['unpaid_amount'] + not_due_unpaid
            total_unpaid_rate = (total_unpaid / contract_amount * 100) if contract_amount > 0 else 0

            result_pay_orders.append({
                'pk': order.pk,
                'pay_name': order.pay_name,
                'pay_due_date': order.pay_due_date,
                'pay_sort': order.pay_sort,
                'pay_code': order.pay_code,
                'pay_time': order.pay_time,
                'contract_amount': contract_amount,  # 계약세대 당 회차 납부약정 총액
                'non_contract_amount': non_contract_amount,  # 미계약 세대 당 회차 납부금액 총계
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
        """특정 pay_time의 계약 금액 합계 계산 (JSON 필드 기반 집계, pay_time 사용)"""
        try:
            # PostgreSQL JSON 집계를 사용한 효율적인 계산 (보안 개선된 parameterized query)
            with connection.cursor() as cursor:
                query = """
                        SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_amount
                        FROM contract_contractprice, jsonb_each_text(payment_amounts)
                        WHERE contract_id IN (SELECT id
                                              FROM contract_contract
                                              WHERE project_id = %s
                                                AND activation = %s)
                          AND is_cache_valid = %s
                          AND key = %s \
                        """

                cursor.execute(query, [project_id, True, True, str(order.pay_time)])

                result = cursor.fetchone()
                total_amount = result[0] if result else 0

            # 캐시 무효화된 계약이 있으면 동적 계산으로 폴백
            invalid_cache_count = ContractPrice.objects.filter(
                contract__project_id=project_id,
                contract__activation=True,
                is_cache_valid=False
            ).count()

            if invalid_cache_count > 0:
                # 일부 캐시가 무효화된 경우 동적 계산과 병합
                fallback_amount = OverallSummaryViewSet._get_contract_amount_fallback(order, project_id)
                return total_amount + fallback_amount

            return total_amount

        except (ValueError, TypeError) as e:
            # 데이터 타입 관련 오류
            return OverallSummaryViewSet._get_contract_amount_fallback(order, project_id)
        except Exception as e:
            # 기타 모든 예외 - 완전 실패 시 동적 계산으로 폴백
            return OverallSummaryViewSet._get_contract_amount_fallback(order, project_id)

    @staticmethod
    def _get_contract_amount_fallback(order, project_id):
        """캐시 실패 시 동적 계산 폴백"""
        from _utils.contract_price import get_contract_payment_plan

        contracts = Contract.objects.filter(
            project_id=project_id,
            activation=True
        ).select_related('contractprice').filter(
            contractprice__is_cache_valid=False
        )

        total_amount = 0

        for contract in contracts:
            try:
                payment_plan = get_contract_payment_plan(contract)
                for plan_item in payment_plan:
                    if plan_item['installment_order'].pay_time == order.pay_time:
                        total_amount += plan_item['amount']
            except Exception:
                continue

        return total_amount

    def _get_payment_amounts_cache(self, project_id, pay_orders):
        """PostgreSQL JSON 집계를 사용한 효율적인 납부 금액 캐시 생성 (pay_time 기반)"""
        # pay_time별로 개별 캐시 생성
        pay_times = set()
        for order in pay_orders:
            pay_times.add(str(order.pay_time))

        payment_amounts_cache = {}

        try:
            with connection.cursor() as cursor:
                # 먼저 전체 활성 계약 수 확인
                cursor.execute("""
                               SELECT COUNT(*)
                               FROM contract_contract
                               WHERE project_id = %s
                                 AND activation = %s
                               """, [project_id, True])
                total_active_contracts = cursor.fetchone()[0]

                # 캐시 유효한 계약 수 확인
                cursor.execute("""
                               SELECT COUNT(*)
                               FROM contract_contractprice cp
                                        JOIN contract_contract cc ON cp.contract_id = cc.id
                               WHERE cc.project_id = %s
                                 AND cc.activation = %s
                                 AND cp.is_cache_valid = %s
                               """, [project_id, True, True])
                valid_cache_contracts = cursor.fetchone()[0]

                # pay_time별로 개별 금액을 집계 (보안 개선된 parameterized query)
                for pay_time in sorted(pay_times):
                    query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_amount,
                                   COUNT(*)                                 as contract_count
                            FROM contract_contractprice, jsonb_each_text(payment_amounts)
                            WHERE contract_id IN (SELECT id
                                                  FROM contract_contract
                                                  WHERE project_id = %s
                                                    AND activation = %s)
                              AND is_cache_valid = %s
                              AND key = %s \
                            """

                    cursor.execute(query, [project_id, True, True, pay_time])

                    result = cursor.fetchone()
                    total_amount = result[0] if result else 0
                    contract_count = result[1] if result else 0

                    payment_amounts_cache[int(pay_time)] = total_amount

                # pay_sort=1인 경우 동일성 검증
                pay_sort_1_times = [pt for pt in pay_times if int(pt) in [1, 2, 3]]
                if len(pay_sort_1_times) > 1:
                    amounts = [payment_amounts_cache[int(pt)] for pt in pay_sort_1_times]

        except Exception as e:
            # 실패 시 기존 방식으로 폴백
            for order in pay_orders:
                payment_amounts_cache[order.pay_time] = self._get_contract_amount(order, project_id)

        return payment_amounts_cache

    @staticmethod
    def _get_non_contract_amounts_cache(project_id, pay_orders):
        """미계약 세대 납부 금액 캐시 생성 (pay_time 기반)"""
        # pay_time별로 개별 캐시 생성
        pay_times = set()
        for order in pay_orders:
            pay_times.add(str(order.pay_time))

        non_contract_amounts_cache = {}

        try:
            with connection.cursor() as cursor:
                # pay_time별로 미계약 세대의 개별 금액을 집계
                for pay_time in sorted(pay_times):
                    query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_amount
                            FROM contract_contractprice, jsonb_each_text(payment_amounts)
                            WHERE contract_id IS NULL
                              AND house_unit_id IN (SELECT hu.id
                                                    FROM items_houseunit hu
                                                             JOIN items_unittype ut ON hu.unit_type_id = ut.id
                                                    WHERE ut.project_id = %s)
                              AND is_cache_valid = %s
                              AND key = %s
                            """

                    cursor.execute(query, [project_id, True, pay_time])

                    result = cursor.fetchone()
                    total_amount = result[0] if result else 0

                    non_contract_amounts_cache[int(pay_time)] = total_amount

        except Exception as e:
            # 실패 시 0으로 초기화
            for order in pay_orders:
                non_contract_amounts_cache[order.pay_time] = 0

        return non_contract_amounts_cache

    @staticmethod
    def _get_all_collection_data(project_id, date, pay_orders):
        """모든 납부 회차의 수납 데이터를 배치로 조회하여 캐시 생성 (contract 연결된 것만)"""

        # 모든 납부 회차의 수납 데이터를 한 번에 조회 (활성화된 contract와 연결된 것만)
        order_ids = [order.pk for order in pay_orders]
        payments_data = ProjectCashBook.objects.filter(
            project_id=project_id,
            installment_order__in=order_ids,
            contract__isnull=False,  # contract와 연결된 수납액만
            contract__activation=True,  # 활성화된 계약만
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

    @staticmethod
    def _get_not_due_unpaid_cache(project_id, date, pay_orders, payment_amounts_cache, collection_cache):
        """기간미도래 미수금 캐시 생성 (성능 최적화)"""
        not_due_unpaid_cache = {}

        for order in pay_orders:
            # 기간미도래가 아닌 경우 0
            if OverallSummaryViewSet._is_due_period(order, date):
                not_due_unpaid_cache[order.pk] = 0
                continue

            # 기간미도래인 경우 계산
            contract_amount = payment_amounts_cache.get(order.pay_time, 0)
            collection_data = collection_cache.get(order.pk, {'collected_amount': 0})
            collected_amount = collection_data['collected_amount']

            # 미수금 = 계약금액 - 수납금액 (최소 0)
            not_due_unpaid = max(0, contract_amount - collected_amount)
            not_due_unpaid_cache[order.pk] = not_due_unpaid

        return not_due_unpaid_cache

    @staticmethod
    def _get_due_period_data_optimized(order, contract_amount, collection_data, date):
        """최적화된 기간도래 관련 데이터 집계 (캐시된 데이터 사용)"""

        # 기간도래 여부 확인
        is_due = OverallSummaryViewSet._is_due_period(order, date)

        if not is_due:
            # 기간미도래인 경우 모든 값을 0으로 반환
            return {
                'contract_amount': 0,
                'unpaid_amount': 0,
                'unpaid_rate': 0,
                'overdue_fee': 0,
                'subtotal': 0
            }

        # 기간도래인 경우 기존 로직 적용
        # 캐시된 수납 데이터 사용
        collected_amount = collection_data['collected_amount']

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
    def _is_due_period(order, date_str):
        """납부 회차의 기간도래 여부 판단

        Args:
            order: InstallmentPaymentOrder 인스턴스
            date_str: 기준 날짜 문자열 (YYYY-MM-DD)

        Returns:
            bool: 기간도래 여부
        """
        # 날짜 문자열을 datetime.date 객체로 변환
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        if order.pay_sort == '1':  # 계약금
            # 계약금은 pay_due_date가 None이면 항상 기간도래
            if order.pay_due_date is None:
                return True
            return order.pay_due_date <= current_date
        else:  # 기타 항목 (중도금, 잔금 등)
            # 기타 항목은 pay_due_date가 None이면 항상 기간미도래
            if order.pay_due_date is None:
                return False
            return order.pay_due_date <= current_date

    @staticmethod
    def _get_not_due_unpaid(order, project_id, date):
        """기간미도래 미수금 계산 (레거시 메서드 - 사용하지 않음)"""
        # 이 메서드는 이제 사용하지 않지만 호환성을 위해 유지
        # 기간미도래가 아닌 경우 0 반환
        if OverallSummaryViewSet._is_due_period(order, date):
            return 0

        # 기간미도래인 경우 해당 회차의 계약금액에서 수납금액을 차감
        contract_amount = OverallSummaryViewSet._get_contract_amount(order, project_id)

        # 수납금액 조회
        collected_amount = ProjectCashBook.objects.filter(
            project_id=project_id,
            installment_order=order,
            income__isnull=False,
            deal_date__lte=date
        ).aggregate(total=Sum('income'))['total'] or 0

        # 미수금 = 계약금액 - 수납금액 (최소 0)
        return max(0, contract_amount - collected_amount)

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


class SalesSummaryByGroupTypeViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    @staticmethod
    def list(request):
        project_id = request.query_params.get('project')

        if not project_id:
            return Response({'error': 'project parameter is required'}, status=400)

        # ContractPrice에서 house_unit을 통해 order_group, unit_type별로 집계
        try:
            with connection.cursor() as cursor:
                query = """
                        SELECT COALESCE(c.order_group_id, og.id)                                  as order_group,
                               hu.unit_type_id                                                    as unit_type,
                               SUM(cp.price)                                                      as total_sales_amount,
                               SUM(CASE WHEN cp.contract_id IS NOT NULL THEN cp.price ELSE 0 END) as contract_amount,
                               SUM(CASE WHEN cp.contract_id IS NULL THEN cp.price ELSE 0 END)     as non_contract_amount
                        FROM contract_contractprice cp
                                 INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
                                 INNER JOIN items_unittype ut ON hu.unit_type_id = ut.id
                                 LEFT JOIN contract_contract c ON cp.contract_id = c.id
                                 INNER JOIN contract_ordergroup og ON (
                            CASE
                                WHEN cp.contract_id IS NOT NULL THEN c.order_group_id = og.id
                                ELSE og.project_id = ut.project_id AND og.is_default_for_uncontracted = true
                                END
                            )
                        WHERE ut.project_id = %s
                          AND cp.is_cache_valid = true
                        GROUP BY COALESCE(c.order_group_id, og.id),
                                 hu.unit_type_id
                        ORDER BY COALESCE(c.order_group_id, og.id),
                                 hu.unit_type_id \
                        """

                cursor.execute(query, [project_id])

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'order_group': row[0],
                        'unit_type': row[1],
                        'total_sales_amount': row[2],
                        'contract_amount': row[3],
                        'non_contract_amount': row[4]
                    })

                serializer = SalesSummaryByGroupTypeSerializer(results, many=True)
                return Response(serializer.data)

        except Exception as e:
            logger.exception(e)
            return Response({'error': 'An internal server error occurred.'}, status=500)


class PaymentStatusByUnitTypeViewSet(viewsets.ViewSet):
    """ContractPrice 모델 기반의 unit_type별 결제 현황 ViewSet"""
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    @staticmethod
    def list(request):
        project_id = request.query_params.get('project')
        date = request.query_params.get('date')

        if not project_id:
            return Response({'error': 'project parameter is required'}, status=400)

        try:
            with connection.cursor() as cursor:
                # 기존 budgetList와 같은 구조로 데이터 조회
                query = """
                        SELECT
                            pib.order_group_id as order_group_id,
                            og.name as order_group_name,
                            pib.unit_type_id as unit_type_id,
                            ut.name as unit_type_name,
                            ut.color as unit_type_color,
                            pib.quantity as planned_units,
                            pib.budget as total_budget,
                            pib.average_price as average_price

                        FROM project_projectincbudget pib
                        INNER JOIN items_unittype ut ON pib.unit_type_id = ut.id
                        INNER JOIN contract_ordergroup og ON pib.order_group_id = og.id
                        WHERE pib.project_id = %s
                        ORDER BY order_group_id, unit_type_id
                        """

                cursor.execute(query, [project_id])

                results = []
                for row in cursor.fetchall():
                    order_group_id = row[0]
                    unit_type_id = row[2]

                    # 각종 데이터 계산
                    planned_units = row[5]
                    total_budget = row[6]
                    average_price = row[7] or 0

                    # 매출액 계산 (기존 SalesSummaryByGroupType API 활용)
                    total_sales_amount = PaymentStatusByUnitTypeViewSet._get_sales_amount_by_unit_type(
                        project_id, order_group_id, unit_type_id
                    )

                    # 계약 현황 계산
                    contract_data = PaymentStatusByUnitTypeViewSet._get_contract_data_by_unit_type(
                        project_id, order_group_id, unit_type_id
                    )

                    # 실수납금액 계산
                    paid_amount = PaymentStatusByUnitTypeViewSet._get_paid_amount_by_unit_type(
                        project_id, order_group_id, unit_type_id, date
                    )

                    contract_units = contract_data['contract_units']
                    contract_amount = contract_data['contract_amount']
                    unpaid_amount = max(0, contract_amount - paid_amount)

                    # 미계약 금액: contract_contractprice에서 contract_id IS NULL인 것들의 합계 (총괄집계와 동일)
                    non_contract_amount = PaymentStatusByUnitTypeViewSet._get_non_contract_amount_by_unit_type(
                        project_id, order_group_id, unit_type_id
                    )

                    # 합계 = 계약금액 + 미계약금액 (total_budget 대신 계산)
                    total_amount = contract_amount + non_contract_amount

                    results.append({
                        'order_group_id': order_group_id,
                        'order_group_name': row[1],
                        'unit_type_id': unit_type_id,
                        'unit_type_name': row[3],
                        'unit_type_color': row[4],
                        'total_sales_amount': total_sales_amount,
                        'planned_units': planned_units,
                        'contract_units': contract_units,
                        'contract_amount': contract_amount,
                        'paid_amount': paid_amount,
                        'unpaid_amount': unpaid_amount,
                        'non_contract_amount': non_contract_amount,
                        'total_budget': total_amount  # 계약금액 + 미계약금액
                    })

                serializer = PaymentStatusByUnitTypeSerializer(results, many=True)
                return Response(serializer.data)

        except Exception as e:
            logger.exception(f"PaymentStatusByUnitType API error: {str(e)}")
            return Response({
                'error': 'An internal server error has occurred.'
            }, status=500)

    @staticmethod
    def _get_sales_amount_by_unit_type(project_id, order_group_id, unit_type_id):
        """ContractPrice 테이블의 유효한 모든 가격정보 합계 (계약 있는 것 + 계약 없는 것)"""
        try:
            from project.models import Project
            from contract.models import OrderGroup

            with connection.cursor() as cursor:
                # 프로젝트 인스턴스와 기본 order_group 가져오기
                project = Project.objects.get(pk=project_id)
                default_og = OrderGroup.get_default_for_project(project)

                # 해당 order_group과 unit_type의 계약 있는 가격 합계 (payment_amounts 기준)
                contract_query = """
                        SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as contract_amount
                        FROM contract_contractprice cp
                        CROSS JOIN jsonb_each_text(cp.payment_amounts)
                        INNER JOIN contract_contract c ON cp.contract_id = c.id
                        WHERE c.project_id = %s
                          AND c.order_group_id = %s
                          AND c.unit_type_id = %s
                          AND c.activation = true
                          AND cp.is_cache_valid = true
                        """

                cursor.execute(contract_query, [project_id, order_group_id, unit_type_id])
                contract_result = cursor.fetchone()
                contract_amount = contract_result[0] if contract_result else 0

                # 미계약 가격 합계 (기본 order_group에만 해당, payment_amounts 기준)
                non_contract_amount = 0
                if default_og and order_group_id == default_og.pk:
                    # 모든 unit_type의 미계약 가격을 합산 (payment_amounts 기준)
                    non_contract_query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as non_contract_amount
                            FROM contract_contractprice cp
                            CROSS JOIN jsonb_each_text(cp.payment_amounts)
                            INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
                            WHERE cp.contract_id IS NULL
                              AND hu.unit_type_id = %s
                              AND cp.is_cache_valid = true
                            """

                    cursor.execute(non_contract_query, [unit_type_id])
                    non_contract_result = cursor.fetchone()
                    non_contract_amount = non_contract_result[0] if non_contract_result else 0

                # 근린생활시설의 경우 별도 처리 (payment_amounts 기준)
                elif unit_type_id == 4:  # 근린생활시설 unit_type_id = 4
                    # 근린생활시설의 미계약 가격 (payment_amounts 기준)
                    non_contract_query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as non_contract_amount
                            FROM contract_contractprice cp
                            CROSS JOIN jsonb_each_text(cp.payment_amounts)
                            INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
                            WHERE cp.contract_id IS NULL
                              AND hu.unit_type_id = %s
                              AND cp.is_cache_valid = true
                            """

                    cursor.execute(non_contract_query, [unit_type_id])
                    non_contract_result = cursor.fetchone()
                    non_contract_amount = non_contract_result[0] if non_contract_result else 0

                return contract_amount + non_contract_amount

        except Exception as e:
            logger.error(f"_get_sales_amount_by_unit_type error: {str(e)}")
            return 0

    @staticmethod
    def _get_contract_data_by_unit_type(project_id, order_group_id, unit_type_id):
        """계약 현황 데이터 계산"""
        try:
            with connection.cursor() as cursor:
                query = """
                        SELECT
                            COUNT(*) as contract_units,
                            COALESCE(SUM(cp.price), 0) as contract_amount
                        FROM contract_contract c
                        INNER JOIN contract_contractprice cp ON cp.contract_id = c.id
                        WHERE c.project_id = %s
                          AND c.order_group_id = %s
                          AND c.unit_type_id = %s
                          AND c.activation = true
                          AND cp.is_cache_valid = true
                        """

                cursor.execute(query, [project_id, order_group_id, unit_type_id])
                result = cursor.fetchone()
                return {
                    'contract_units': result[0] if result else 0,
                    'contract_amount': result[1] if result else 0
                }

        except Exception as e:
            logger.error(f"_get_contract_data_by_unit_type error: {str(e)}")
            return {'contract_units': 0, 'contract_amount': 0}

    @staticmethod
    def _get_paid_amount_by_unit_type(project_id, order_group_id, unit_type_id, date):
        """order_group과 unit_type별 실수납금액 계산 (OverallSummary와 일치하도록 installment_order 기준)"""
        try:
            with connection.cursor() as cursor:
                date_filter = ""
                params = [project_id, order_group_id, unit_type_id]

                if date:
                    date_filter = "AND pcb.deal_date <= %s"
                    params.append(date)

                # OverallSummary와 동일한 방식: installment_order 기준으로 수납액 집계 (활성화된 계약만)
                query = f"""
                        SELECT COALESCE(SUM(pcb.income), 0) as paid_amount
                        FROM cash_projectcashbook pcb
                        INNER JOIN payment_installmentpaymentorder ipo ON pcb.installment_order_id = ipo.id
                        INNER JOIN contract_contract c ON pcb.contract_id = c.id
                        WHERE ipo.project_id = %s
                          AND c.order_group_id = %s
                          AND c.unit_type_id = %s
                          AND c.activation = true
                          AND pcb.income IS NOT NULL
                          {date_filter}
                        """

                cursor.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"_get_paid_amount_by_unit_type error: {str(e)}")
            return 0

    @staticmethod
    def _get_non_contract_amount_by_unit_type(project_id, order_group_id, unit_type_id):
        """order_group과 unit_type별 미계약 금액 계산 (get_default_for_project 활용)"""
        try:
            from project.models import Project
            from contract.models import OrderGroup

            # 프로젝트 인스턴스 가져오기
            project = Project.objects.get(pk=project_id)

            # 미계약 기본 order_group 가져오기
            default_og = OrderGroup.get_default_for_project(project)
            if not default_og:
                return 0

            # 미계약 기본 order_group에 해당하는 경우만 미계약 금액 계산
            if order_group_id == default_og.pk:
                with connection.cursor() as cursor:
                    # 해당 unit_type의 미계약 금액 계산
                    query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as non_contract_amount
                            FROM contract_contractprice cp,
                                 jsonb_each_text(cp.payment_amounts)
                            WHERE cp.contract_id IS NULL
                              AND cp.house_unit_id IN (
                                  SELECT hu.id
                                  FROM items_houseunit hu
                                  WHERE hu.unit_type_id = %s
                              )
                              AND cp.is_cache_valid = true
                            """

                    cursor.execute(query, [unit_type_id])
                    result = cursor.fetchone()
                    return result[0] if result else 0
            else:
                # 미계약 기본 order_group이 아닌 경우 0
                return 0

        except Exception as e:
            logger.error(f"_get_non_contract_amount_by_unit_type error: {str(e)}")
            return 0
