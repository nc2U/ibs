from collections import defaultdict
from datetime import datetime
import logging

from django.db import connection
from django.db.models import Sum
from django_filters import CharFilter, BooleanFilter, DateFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets
from rest_framework.response import Response

from _utils.contract_price import get_contract_payment_plan
from contract.models import ContractPrice, OrderGroup, Contract
from items.models import KeyUnit
from items.models import UnitType, HouseUnit
from ledger.models import ProjectBankTransaction
from payment.models import InstallmentPaymentOrder, SalesPriceByGT, PaymentPerInstallment, DownPayment, OverDueRule, \
    ContractPayment
from project.models import Project
from project.models import ProjectIncBudget
from ..pagination import PageNumberPaginationTwenty, PageNumberPaginationFifty, \
    PageNumberPaginationTen, PageNumberPaginationOneHundred
from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly
from ..serializers.payment import InstallmentOrderSerializer, SalesPriceSerializer, \
    PaymentPerInstallmentSerializer, DownPaymentSerializer, OverDueRuleSerializer, \
    PaymentSummaryComponentSerializer, PaymentStatusByUnitTypeSerializer, OverallSummarySerializer, \
    ContractPaymentSerializer

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
        예: '?pay_sort__in=1,4,5,6,7'
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
    filterset_fields = ('sales_price', 'sales_price__project', 'sales_price__order_group',
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


# Helper Functions for Unit Type Payment status calculations -----------------------

def get_sales_amount_by_unit_type(project_id, order_group_id, unit_type_id):
    """ContractPrice 테이블의 유효한 모든 가격정보 합계 (계약 있는 것 + 계약 없는 것)"""
    try:
        with connection.cursor() as cursor:
            project = Project.objects.get(pk=project_id)
            default_og = OrderGroup.get_default_for_project(project)

            contract_query = """
                             SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as contract_amount
                             FROM contract_contractprice cp
                                      CROSS JOIN jsonb_each_text(cp.payment_amounts)
                                      INNER JOIN contract_contract c ON cp.contract_id = c.id
                             WHERE c.project_id = %s
                               AND c.order_group_id = %s
                               AND c.unit_type_id = %s
                               AND c.is_active = true
                               AND cp.is_cache_valid = true
                             """

            cursor.execute(contract_query, [project_id, order_group_id, unit_type_id])
            contract_result = cursor.fetchone()
            contract_amount = contract_result[0] if contract_result else 0

            # 미계약 가격 합계
            non_contract_amount = 0
            if default_og and order_group_id == default_og.pk:
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

            total_amount = contract_amount + non_contract_amount

            # 근린생활시설 특별 처리
            if total_amount == 0:
                try:
                    unit_type = UnitType.objects.get(pk=unit_type_id)
                    if unit_type.sort == '5':
                        has_house_units = HouseUnit.objects.filter(unit_type_id=unit_type_id).exists()
                        has_sales_price = SalesPriceByGT.objects.filter(
                            project_id=project_id,
                            order_group_id=order_group_id,
                            unit_type_id=unit_type_id
                        ).exists()

                        if has_house_units and not has_sales_price:
                            total_amount = get_commercial_fallback_amount(project_id, order_group_id, unit_type_id)
                except UnitType.DoesNotExist:
                    pass

            return total_amount

    except Exception as e:
        logger.error(f"Error in get_sales_amount_by_unit_type: {e}")
        return 0


def get_commercial_fallback_amount(project_id, order_group_id, unit_type_id):
    """근린생활시설 전용 fallback 로직"""
    try:
        try:
            budget = ProjectIncBudget.objects.get(
                project_id=project_id,
                order_group_id=order_group_id,
                unit_type_id=unit_type_id
            )
            if budget.budget and budget.budget > 0:
                return budget.budget
        except ProjectIncBudget.DoesNotExist:
            pass

        try:
            unit_type = UnitType.objects.get(pk=unit_type_id)
            if hasattr(unit_type, 'average_price') and unit_type.average_price and unit_type.average_price > 0:
                return unit_type.average_price
        except UnitType.DoesNotExist:
            pass

        return 0

    except Exception as e:
        logger.error(f"Error in get_commercial_fallback_amount: {e}")
        return 0


def get_contract_data_by_unit_type(project_id, order_group_id, unit_type_id):
    """계약 현황 데이터 계산"""
    try:
        with connection.cursor() as cursor:
            query = """
                    SELECT COUNT(*)                   as contract_units,
                           COALESCE(SUM(cp.price), 0) as contract_amount
                    FROM contract_contract c
                             INNER JOIN contract_contractprice cp ON cp.contract_id = c.id
                    WHERE c.project_id = %s
                      AND c.order_group_id = %s
                      AND c.unit_type_id = %s
                      AND c.is_active = true
                      AND cp.is_cache_valid = true
                    """

            cursor.execute(query, [project_id, order_group_id, unit_type_id])
            result = cursor.fetchone()
            return {
                'contract_units': result[0] if result else 0,
                'contract_amount': result[1] if result else 0
            }

    except Exception as e:
        logger.error(f"Error in get_contract_data_by_unit_type: {e}")
        return {'contract_units': 0, 'contract_amount': 0}


def get_paid_amount_by_unit_type(project_id, order_group_id, unit_type_id, date, use_ledger_join=False):
    """order_group과 unit_type별 실수납금액 계산"""
    try:
        with connection.cursor() as cursor:
            date_filter = ""
            params = [project_id, order_group_id, unit_type_id]

            if date:
                if use_ledger_join:
                    date_filter = "AND pbt.deal_date <= %s"
                else:
                    date_filter = "AND cp.deal_date <= %s"
                params.append(date)

            if use_ledger_join:
                query = f"""
                        SELECT COALESCE(SUM(pae.amount), 0) as paid_amount
                        FROM payment_contractpayment cp
                                 INNER JOIN ledger_projectaccountingentry pae ON cp.accounting_entry_id = pae.id
                                 INNER JOIN ledger_projectbanktransaction pbt ON pae.transaction_id = pbt.transaction_id
                                 INNER JOIN contract_contract c ON cp.contract_id = c.id
                                 INNER JOIN ledger_projectaccount pa ON pae.account_id = pa.id
                        WHERE cp.project_id = %s
                          AND c.order_group_id = %s
                          AND c.unit_type_id = %s
                          AND c.is_active = true
                          AND pa.is_payment = true
                          AND cp.is_payment_mismatch = false
                          {date_filter}
                        """
            else:
                query = f"""
                        SELECT COALESCE(SUM(pae.amount), 0) as paid_amount
                        FROM payment_contractpayment cp
                        INNER JOIN ledger_projectaccountingentry pae ON cp.accounting_entry_id = pae.id
                        INNER JOIN ledger_projectaccount pa ON pae.account_id = pa.id
                        INNER JOIN contract_contract c ON cp.contract_id = c.id
                        WHERE cp.project_id = %s
                          AND c.order_group_id = %s
                          AND c.unit_type_id = %s
                          AND c.is_active = true
                          AND pae.amount IS NOT NULL
                          AND pa.is_payment = true
                          AND cp.is_payment_mismatch = false
                          {date_filter}
                        """

            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0

    except Exception as e:
        logger.error(f"Error in get_paid_amount_by_unit_type: {e}")
        return 0


def get_non_contract_amount_by_unit_type(project_id, order_group_id, unit_type_id):
    """order_group과 unit_type별 미계약 금액 계산"""
    try:
        project = Project.objects.get(pk=project_id)
        default_og = OrderGroup.get_default_for_project(project)
        if not default_og:
            return 0

        if order_group_id == default_og.pk:
            with connection.cursor() as cursor:
                query = """
                        SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as non_contract_amount
                        FROM contract_contractprice cp, jsonb_each_text(cp.payment_amounts)
                        WHERE cp.contract_id IS NULL
                          AND cp.house_unit_id IN (SELECT hu.id
                                                   FROM items_houseunit hu
                                                   WHERE hu.unit_type_id = %s)
                          AND cp.is_cache_valid = true
                        """

                cursor.execute(query, [unit_type_id])
                result = cursor.fetchone()
                return result[0] if result else 0
        else:
            return 0

    except Exception as e:
        logger.error(f"Error in get_non_contract_amount_by_unit_type: {e}")
        return 0


def get_non_contract_units_by_unit_type(project_id, order_group_id, unit_type_id):
    """order_group과 unit_type별 미계약 세대수 계산"""
    try:
        project = Project.objects.get(pk=project_id)
        default_og = OrderGroup.get_default_for_project(project)
        if not default_og:
            return 0

        if order_group_id == default_og.pk:
            with connection.cursor() as cursor:
                query = """
                        SELECT COUNT(*) as non_contract_units
                        FROM contract_contractprice cp
                                 INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
                        WHERE cp.contract_id IS NULL
                          AND hu.unit_type_id = %s
                          AND cp.is_cache_valid = true
                        """

                cursor.execute(query, [unit_type_id])
                result = cursor.fetchone()
                return result[0] if result else 0
        else:
            return 0

    except Exception as e:
        logger.error(f"Error in get_non_contract_units_by_unit_type: {e}")
        return 0


def calculate_payment_status_by_unit_type_core(project_id, date=None, use_ledger_join=False):
    """PaymentStatus 요약 현황 계산 코어 로직"""
    with connection.cursor() as cursor:
        query = """
                SELECT pib.order_group_id as order_group_id,
                       og.name            as order_group_name,
                       pib.unit_type_id   as unit_type_id,
                       ut.name            as unit_type_name,
                       ut.color           as unit_type_color,
                       pib.quantity       as planned_units,
                       pib.budget         as total_budget,
                       pib.average_price  as average_price
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
            planned_units = row[5]
            total_budget = row[6]

            # 매출액 계산
            total_sales_amount = get_sales_amount_by_unit_type(project_id, order_group_id, unit_type_id)

            # 근린생활시설 특별 처리
            if total_budget == 0 and total_sales_amount > 0:
                try:
                    unit_type = UnitType.objects.get(pk=unit_type_id)
                    if unit_type.sort == '5':  # 근린생활시설
                        has_house_units = HouseUnit.objects.filter(unit_type_id=unit_type_id).exists()
                        has_sales_price = SalesPriceByGT.objects.filter(
                            project_id=project_id,
                            order_group_id=order_group_id,
                            unit_type_id=unit_type_id
                        ).exists()

                        if has_house_units and not has_sales_price:
                            total_budget = total_sales_amount
                except UnitType.DoesNotExist:
                    pass

            # 계약 현황 계산
            contract_data = get_contract_data_by_unit_type(project_id, order_group_id, unit_type_id)

            # 실수납금액 계산
            paid_amount = get_paid_amount_by_unit_type(project_id, order_group_id, unit_type_id, date, use_ledger_join)

            contract_units = contract_data['contract_units']
            contract_amount = contract_data['contract_amount']
            unpaid_amount = contract_amount - paid_amount

            # 미계약 금액
            non_contract_amount = get_non_contract_amount_by_unit_type(project_id, order_group_id, unit_type_id)

            # 미계약 세대수
            non_contract_units = get_non_contract_units_by_unit_type(project_id, order_group_id, unit_type_id)

            # 합계 = 계약금액 + 미계약금액
            total_amount = contract_amount + non_contract_amount

            # 근린생활시설 특별 처리
            if total_amount == 0:
                try:
                    unit_type = UnitType.objects.get(pk=unit_type_id)
                    if unit_type.sort == '5':  # 근린생활시설
                        has_house_units = HouseUnit.objects.filter(unit_type_id=unit_type_id).exists()
                        has_sales_price = SalesPriceByGT.objects.filter(
                            project_id=project_id,
                            order_group_id=order_group_id,
                            unit_type_id=unit_type_id
                        ).exists()

                        if has_house_units and not has_sales_price:
                            total_amount = get_commercial_fallback_amount(
                                project_id, order_group_id, unit_type_id
                            )
                except UnitType.DoesNotExist:
                    pass

            results.append({
                'order_group_id': order_group_id,
                'order_group_name': row[1],
                'unit_type_id': unit_type_id,
                'unit_type_name': row[3],
                'unit_type_color': row[4],
                'total_sales_amount': total_sales_amount,
                'planned_units': planned_units,
                'contract_units': contract_units,
                'non_contract_units': non_contract_units,
                'contract_amount': contract_amount,
                'paid_amount': paid_amount,
                'unpaid_amount': unpaid_amount,
                'non_contract_amount': non_contract_amount,
                'total_budget': total_amount
            })
    return results


def is_due_period(order, date_str):
    """납부 회차의 기간도래 여부 판단"""
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


class PaymentSummaryViewSet(viewsets.ViewSet):
    """PaymentSummary 컴포넌트용 unit_type별 요약 현황 ViewSet"""
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    @staticmethod
    def list(request):
        project_id = request.query_params.get('project')
        date = request.query_params.get('date')

        if not project_id:
            return Response({'error': 'project parameter is required'}, status=400)

        try:
            # 코어 계산 로직 호출 (use_ledger_join=False)
            payment_status_data = calculate_payment_status_by_unit_type_core(project_id, date, use_ledger_join=False)

            # unit_type별로 그룹화해서 합계 계산
            unit_type_aggregates = defaultdict(lambda: {
                'unit_type_id': 0,
                'unit_type_name': '',
                'unit_type_color': '',
                'total_budget': 0,
                'total_contract_amount': 0,
                'total_paid_amount': 0,
                'unpaid_amount': 0,
                'non_contract_amount': 0
            })

            for item in payment_status_data:
                unit_type_name = item['unit_type_name']
                unit_type_id = item['unit_type_id']
                unit_type_color = item['unit_type_color']

                agg = unit_type_aggregates[unit_type_name]
                agg['unit_type_id'] = unit_type_id
                agg['unit_type_name'] = unit_type_name
                agg['unit_type_color'] = unit_type_color
                agg['total_budget'] += item['total_budget']
                agg['total_contract_amount'] += item['contract_amount']
                agg['total_paid_amount'] += item['paid_amount']
                agg['unpaid_amount'] += item['unpaid_amount']
                agg['non_contract_amount'] += item['non_contract_amount']

            # 결과 생성
            results = []
            for unit_type_name, agg in unit_type_aggregates.items():
                unsold_amount = max(0, agg['total_budget'] - agg['total_contract_amount'])

                results.append({
                    'unit_type_id': agg['unit_type_id'],
                    'unit_type_name': agg['unit_type_name'],
                    'unit_type_color': agg['unit_type_color'],
                    'total_budget': agg['total_budget'],  # 총 매출예산(A)
                    'total_contract_amount': agg['total_contract_amount'],  # 총 분양금액(B)
                    'total_paid_amount': agg['total_paid_amount'],  # 총 수납금액(C)
                    'unpaid_amount': agg['unpaid_amount'],  # 미수납금액(B-C)
                    'unsold_amount': unsold_amount  # 미분양금액(A-B)
                })

            # unit_type_id로 정렬
            results.sort(key=lambda x: x['unit_type_id'])

            serializer = PaymentSummaryComponentSerializer(results, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in PaymentSummaryViewSet.list: {e}")
            return Response({
                'error': 'An internal server error has occurred.'
            }, status=500)


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
            results = calculate_payment_status_by_unit_type_core(project_id, date, use_ledger_join=False)
            serializer = PaymentStatusByUnitTypeSerializer(results, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in PaymentStatusByUnitTypeViewSet.list: {e}")
            return Response({
                'error': 'An internal server error has occurred.'
            }, status=500)


# will be deprecated - use ProjectCashBook
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
        not_due_unpaid_cache = self._get_not_due_unpaid_cache(project_id, date, pay_orders, payment_amounts_cache,
                                                              collection_cache)

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

            # collection_rate 계산 (회차별 계약금액 대비 실수납액)
            collection_rate = (
                    collection_data['actual_collected'] / contract_amount * 100) if contract_amount > 0 else 0
            collection_data['collection_rate'] = round(collection_rate, 2)

            # 기간도래 관련 집계 (기존 방식 사용)
            due_period_data = self._get_due_period_data_optimized(order, contract_amount, collection_data, date)

            # 기간미도래 미수금 (캐시된 데이터 사용)
            not_due_unpaid = not_due_unpaid_cache.get(order.pk, 0)

            # 총 미수금 = 해당 회차의 기간도래 미수금 + 해당 회차의 기간미도래 미수금
            due_unpaid = due_period_data['unpaid_amount']  # 해당 회차의 기간도래 미수금
            not_due_unpaid = not_due_unpaid_cache.get(order.pk, 0)  # 해당 회차의 기간미도래 미수금

            total_unpaid = due_unpaid + not_due_unpaid
            total_unpaid_rate = (total_unpaid / contract_amount * 100) if contract_amount > 0 else 0

            # 회차별 계약률 계산 (계약금액 / 총금액)
            order_total_amount = contract_amount + non_contract_amount
            order_contract_rate = (contract_amount / order_total_amount * 100) if order_total_amount > 0 else 0

            result_pay_orders.append({
                'pk': order.pk,
                'pay_name': order.pay_name,
                'pay_due_date': order.pay_due_date,
                'pay_sort': order.pay_sort,
                'pay_code': order.pay_code,
                'pay_time': order.pay_time,
                'contract_amount': contract_amount,  # 계약세대 당 회차 납부약정 총액
                'non_contract_amount': non_contract_amount,  # 미계약 세대 당 회차 납부금액 총계
                'contract_rate': round(order_contract_rate, 2),  # 회차별 계약률
                'collection': collection_data,
                'due_period': due_period_data,
                'not_due_unpaid': not_due_unpaid,
                'total_unpaid': total_unpaid,
                'total_unpaid_rate': round(total_unpaid_rate, 2)
            })

        # 전체 미수금 계산 (모든 회차의 총 미수금 합계)
        total_overall_unpaid = sum(order['total_unpaid'] for order in result_pay_orders)

        # 전체 계약금액 계산 (모든 회차)
        total_all_contract_amount = sum(
            payment_amounts_cache.get(order.pay_time, 0) for order in pay_orders
        )

        # 전체 미수율 계산
        total_overall_unpaid_rate = (
                total_overall_unpaid / total_all_contract_amount * 100) if total_all_contract_amount > 0 else 0

        # 마지막 회차에 전체 미수금 정보 추가 (표시용)
        if result_pay_orders:
            last_order = result_pay_orders[-1]
            last_order['total_overall_unpaid'] = total_overall_unpaid
            last_order['total_overall_unpaid_rate'] = round(total_overall_unpaid_rate, 2)

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
                                                AND is_active = %s)
                          AND is_cache_valid = %s
                          AND key = %s \
                        """

                cursor.execute(query, [project_id, True, True, str(order.pay_time)])

                result = cursor.fetchone()
                total_amount = result[0] if result else 0

            # 캐시 무효화된 계약이 있으면 동적 계산으로 폴백
            invalid_cache_count = ContractPrice.objects.filter(
                contract__project_id=project_id,
                contract__is_active=True,
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
        contracts = Contract.objects.filter(
            project_id=project_id,
            is_active=True
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
                                 AND is_active = %s
                               """, [project_id, True])
                total_active_contracts = cursor.fetchone()[0]

                # 캐시 유효한 계약 수 확인
                cursor.execute("""
                               SELECT COUNT(*)
                               FROM contract_contractprice cp
                                        JOIN contract_contract cc ON cp.contract_id = cc.id
                               WHERE cc.project_id = %s
                                 AND cc.is_active = %s
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
                                                    AND is_active = %s)
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
        """미계약 세대 납부 금액 캐시 생성 (pay_time 기반) - 근린생활시설 fallback 포함"""
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

                    # 근린생활시설 fallback 로직 추가 (기존 금액에 추가)
                    commercial_fallback = OverallSummaryViewSet._get_commercial_fallback_for_overall(
                        project_id, int(pay_time)
                    )
                    total_amount += commercial_fallback

                    non_contract_amounts_cache[int(pay_time)] = total_amount

        except Exception as e:
            # 실패 시 0으로 초기화
            for order in pay_orders:
                non_contract_amounts_cache[order.pay_time] = 0

        return non_contract_amounts_cache

    @staticmethod
    def _get_commercial_fallback_for_overall(project_id, pay_time):
        """
        총괄 집계용 근린생활시설 fallback 로직 - 회차별 계산
        근린생활시설이 있지만 ContractPrice 데이터가 없을 때 fallback 적용
        납부회차가 없으면 기본 납부회차(잔금 100%) 적용
        """
        try:
            # 프로젝트의 기본 order_group 가져오기
            project = Project.objects.get(pk=project_id)
            default_og = OrderGroup.get_default_for_project(project)

            if not default_og:
                return 0

            # 근린생활시설 타입 찾기 (sort='5')
            commercial_unit_types = UnitType.objects.filter(
                project_id=project_id,
                sort='5'
            )

            total_fallback_amount = 0

            for unit_type in commercial_unit_types:
                # 해당 타입의 HouseUnit이 있는지 확인
                has_house_units = HouseUnit.objects.filter(unit_type_id=unit_type.pk).exists()

                # 해당 타입의 SalesPriceByGT가 있는지 확인
                has_sales_price = SalesPriceByGT.objects.filter(
                    project_id=project_id,
                    order_group_id=default_og.pk,
                    unit_type_id=unit_type.pk
                ).exists()

                # HouseUnit은 있지만 SalesPriceByGT가 없을 때만 fallback 적용
                if has_house_units and not has_sales_price:
                    # 예산 데이터에서 기본 금액 가져오기
                    base_amount = PaymentStatusByUnitTypeViewSet._get_commercial_fallback_amount(
                        project_id, default_og.pk, unit_type.pk
                    )

                    if base_amount > 0:
                        # 프로젝트의 근린생활시설용 InstallmentPaymentOrder가 있는지 확인
                        installment_orders = InstallmentPaymentOrder.objects.filter(
                            project_id=project_id,
                            type_sort='5'  # 근린생활시설
                        )

                        if not installment_orders.exists():
                            # InstallmentPaymentOrder가 없으면 기본 납부회차 적용: 잔금 100%
                            # 잔금인지 확인 (pay_sort='3')
                            try:
                                pay_order = InstallmentPaymentOrder.objects.get(
                                    project_id=project_id,
                                    pay_time=pay_time
                                )
                                if pay_order.pay_sort == '3':  # 잔금
                                    installment_amount = base_amount
                                    total_fallback_amount += installment_amount
                            except InstallmentPaymentOrder.DoesNotExist:
                                pass
                        else:
                            # InstallmentPaymentOrder가 있으면 해당 회차에 따라 계산
                            try:
                                pay_order = InstallmentPaymentOrder.objects.get(
                                    project_id=project_id,
                                    pay_time=pay_time,
                                    type_sort='5'  # 근린생활시설용만
                                )

                                if pay_order.pay_amt:
                                    # pay_amt가 설정된 경우 그 값 사용
                                    installment_amount = pay_order.pay_amt
                                    total_fallback_amount += installment_amount
                                elif pay_order.pay_ratio:
                                    # pay_ratio가 설정된 경우 base_amount에 비율 적용
                                    installment_amount = int(base_amount * (pay_order.pay_ratio / 100))
                                    total_fallback_amount += installment_amount
                                elif pay_order.pay_name == '잔금':
                                    # 잔금의 경우 남은 비율을 자동 계산
                                    other_orders = InstallmentPaymentOrder.objects.filter(
                                        project_id=project_id,
                                        type_sort='5'
                                    ).exclude(pay_time=pay_time)
                                    used_ratio = sum(order.pay_ratio or 0 for order in other_orders)
                                    remaining_ratio = 100 - used_ratio

                                    if remaining_ratio > 0:
                                        installment_amount = int(base_amount * (remaining_ratio / 100))
                                        total_fallback_amount += installment_amount

                            except InstallmentPaymentOrder.DoesNotExist:
                                pass

            return total_fallback_amount

        except Exception as e:
            return 0

    @staticmethod
    def _get_all_collection_data(project_id, date, pay_orders):
        """표준화된 수납 데이터 배치 조회 (get_standardized_payment_sum 로직 기반)"""

        # 모든 납부 회차의 수납 데이터를 한 번에 조회 (payment_records() 사용으로 최적화)
        order_ids = [order.pk for order in pay_orders]
        payments_data = ContractPayment.objects.valid_payments().filter(
            project_id=project_id,
            installment_order__in=order_ids,
            contract__isnull=False,
            contract__is_active=True,
            deal_date__lte=date
        ).values('installment_order').annotate(
            total_collected=Sum('accounting_entry__amount')
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

            # 미수금 = 계약금액 - 수납금액 (음수 포함 - 초과납부 반영)
            not_due_unpaid = contract_amount - collected_amount
            not_due_unpaid_cache[order.pk] = not_due_unpaid

        return not_due_unpaid_cache

    @staticmethod
    def _get_due_period_data_optimized(order, contract_amount, collection_data, date):
        """최적화된 기간도래 관련 데이터 집계 (캐시된 데이터 사용) - 레거시 메서드"""

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

        # 기간도래 미수금 = 계약금액 - 수납액 (음수 포함 - 초과납부 반영)
        unpaid_amount = contract_amount - collected_amount
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
    def _get_due_period_data_with_carryover(order, contract_amount, collection_data, date, carryover_amount):
        """초과납부 이월을 포함한 기간도래 관련 데이터 집계"""

        # 기간도래 여부 확인
        is_due = OverallSummaryViewSet._is_due_period(order, date)

        if not is_due:
            # 기간미도래인 경우 모든 값을 0으로 반환하되, carryover_amount는 유지
            return {
                'contract_amount': 0,
                'unpaid_amount': 0,
                'unpaid_rate': 0,
                'overdue_fee': 0,
                'subtotal': 0,
                'carryover_amount': carryover_amount
            }

        # 기간도래인 경우 초과납부 이월 적용
        collected_amount = collection_data['collected_amount']

        # 실제 납부 필요 금액 = 계약금액 - 이월된 초과납부액
        actual_required_amount = max(0, contract_amount - carryover_amount)

        # 미수금 계산
        if collected_amount >= actual_required_amount:
            # 이번 회차 납부가 충분한 경우
            unpaid_amount = 0
            # 다음 회차로 이월할 초과납부액 = 기존 이월액 + 이번 회차 초과분 - 이번 회차에서 사용한 이월액
            new_carryover = carryover_amount + collected_amount - contract_amount
            new_carryover = max(0, new_carryover)  # 음수가 될 수는 없음
        else:
            # 이번 회차 납부가 부족한 경우
            unpaid_amount = actual_required_amount - collected_amount
            new_carryover = 0  # 초과납부액 모두 소진

        unpaid_rate = (unpaid_amount / contract_amount * 100) if contract_amount > 0 else 0

        # TODO: 기간도래분 연체료 계산 로직 구현 필요
        overdue_fee = 0
        subtotal = unpaid_amount + overdue_fee

        return {
            'contract_amount': contract_amount,
            'unpaid_amount': unpaid_amount,
            'unpaid_rate': round(unpaid_rate, 2),
            'overdue_fee': overdue_fee,
            'subtotal': subtotal,
            'carryover_amount': new_carryover
        }

    @staticmethod
    def _get_not_due_unpaid_with_carryover(order, date, payment_amounts_cache, collection_cache, carryover_amount):
        """초과납부 이월을 포함한 기간미도래 미수금 계산"""

        # 기간미도래가 아닌 경우 0
        if OverallSummaryViewSet._is_due_period(order, date):
            return 0

        # 기간미도래인 경우 계산
        contract_amount = payment_amounts_cache.get(order.pay_time, 0)
        collection_data = collection_cache.get(order.pk, {'collected_amount': 0})
        collected_amount = collection_data['collected_amount']

        # 실제 납부 필요 금액 = 계약금액 - 이월된 초과납부액
        actual_required_amount = max(0, contract_amount - carryover_amount)

        # 미수금 = 실제 필요금액 - 수납금액 (최소 0)
        not_due_unpaid = max(0, actual_required_amount - collected_amount)

        return not_due_unpaid

    def _get_collection_data(self, order, project_id, date):
        """수납 관련 데이터 집계 (레거시 메서드 - 사용하지 않음)"""
        # 이 메서드는 이제 사용하지 않지만 호환성을 위해 유지
        payments = ContractPayment.objects.valid_payments().filter(
            project_id=project_id,
            installment_order=order,
            deal_date__lte=date
        )

        collected_amount = payments.aggregate(total=Sum('accounting_entry__amount'))['total'] or 0
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

        collected_amount = ContractPayment.objects.valid_payments().filter(
            project_id=project_id,
            installment_order=order,
            deal_date__lte=date
        ).aggregate(total=Sum('accounting_entry__amount'))['total'] or 0

        unpaid_amount = contract_amount - collected_amount  # 음수 포함 - 초과납부 반영
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
        collected_amount = ContractPayment.objects.valid_payments().filter(
            project_id=project_id,
            installment_order=order,
            deal_date__lte=date
        ).aggregate(total=Sum('accounting_entry__amount'))['total'] or 0

        # 미수금 = 계약금액 - 수납금액 (음수 포함 - 초과납부 반영)
        return contract_amount - collected_amount

    @staticmethod
    def _get_aggregate_data(project_id):
        """집계 데이터 조회"""

        # 계약 세대수
        conts_num = Contract.objects.filter(
            project_id=project_id,
            is_active=True,
            contractor__status=2
        ).count()

        # 전체 세대수 (KeyUnit 기준)
        total_units = KeyUnit.objects.filter(project_id=project_id,
                                             unit_type__main_or_sub='1').count()

        # 미계약 세대수
        non_conts_num = total_units - conts_num

        # 계약률 계산 (금액 기준): 계약금액 / 총매출액
        try:
            payment_status_data = calculate_payment_status_by_unit_type_core(project_id, use_ledger_join=False)
            total_contract_amount = sum(item['contract_amount'] for item in payment_status_data)
            total_sales_amount = sum(item['total_sales_amount'] for item in payment_status_data)
            contract_rate = (total_contract_amount / total_sales_amount * 100) if total_sales_amount > 0 else 0
        except Exception as e:
            logger.error(f"Error in OverallSummaryViewSet._get_aggregate_data: {e}")
            contract_rate = 0

        return {
            'conts_num': conts_num,
            'non_conts_num': non_conts_num,
            'total_units': total_units,
            'contract_rate': round(contract_rate, 2)
        }


# --------------------------------------------------------------------
# ledger based new api
# --------------------------------------------------------------------

class ContractPaymentFilterSet(FilterSet):
    """
    ContractPayment 필터셋 (구버전 ProjectCashBookFilterSet 호환)

    지원 필터:
    - from_deal_date, to_deal_date: 거래일자 범위
    - contract__order_group, contract__unit_type: 계약 관계 필터
    - no_contract, no_install: NULL 체크 필터
    - bank_account: 은행 계좌 필터 (UUID JOIN)
    - is_payment_mismatch: 납부 불일치 플래그
    """
    from_deal_date = DateFilter(field_name='deal_date', lookup_expr='gte', label='거래일자 시작')
    to_deal_date = DateFilter(field_name='deal_date', lookup_expr='lte', label='거래일자 종료')
    no_contract = BooleanFilter(field_name='contract', lookup_expr='isnull', label='계약 미등록')
    no_install = BooleanFilter(field_name='installment_order', lookup_expr='isnull', label='회차 미등록')
    bank_account = CharFilter(method='filter_bank_account', label='은행 계좌')

    class Meta:
        model = ContractPayment
        fields = {
            'project': ['exact'],
            'contract': ['exact'],
            'contract__order_group': ['exact'],  # 계약 차수 필터 (관계 필드)
            'contract__unit_type': ['exact'],  # 계약 타입 필터 (관계 필드)
            'installment_order': ['exact'],
            'deal_date': ['exact'],
            'is_payment_mismatch': ['exact'],
        }

    @staticmethod
    def filter_bank_account(queryset, name, value):
        """
        은행 계좌 필터링 (UUID JOIN 경로: accounting_entry → related_transaction → bank_account)

        ContractPayment → accounting_entry (ProjectAccountingEntry)
                       → related_transaction (ProjectBankTransaction via UUID)
                       → bank_account
        """
        # 해당 bank_account를 가진 transaction_id 목록 조회
        transaction_ids = ProjectBankTransaction.objects.filter(
            bank_account=value
        ).values_list('transaction_id', flat=True)

        # ContractPayment에서 해당 transaction_id를 가진 accounting_entry 필터링
        return queryset.filter(
            accounting_entry__transaction_id__in=transaction_ids
        )


class ContractPaymentViewSet(viewsets.ModelViewSet):
    """
    ContractPayment 기본 CRUD ViewSet (구버전 ProjectCashBook 호환)

    계약별 납부 내역 조회, 생성, 수정, 삭제
    """
    queryset = ContractPayment.objects.select_related(
        'accounting_entry',
        'accounting_entry__account',
        'contract',
        'contract__unit_type',
        'contract__order_group',
        'contract__contractor',
        'installment_order',
        'project'
    ).all()
    serializer_class = ContractPaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = ContractPaymentFilterSet
    pagination_class = PageNumberPaginationTen
    search_fields = [
        'contract__contractor__name',  # 계약자명
        'accounting_entry__trader',  # 거래처
    ]
    ordering_fields = ['deal_date', 'created_at', 'installment_order']
    ordering = ['-deal_date', '-created_at']  # 기본 정렬

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            self._prefetch_related_transactions(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        self._prefetch_related_transactions(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def _prefetch_related_transactions(self, items):
        """related_transaction 프로퍼티 조회를 배치 쿼리로 사전 캐싱 (N+1 제거)"""
        transaction_ids = [
            item.accounting_entry.transaction_id
            for item in items
            if item.accounting_entry_id and item.accounting_entry.transaction_id
        ]
        if transaction_ids:
            transactions = ProjectBankTransaction.objects.filter(transaction_id__in=transaction_ids)
            trans_map = {t.transaction_id: t for t in transactions}
            for item in items:
                if item.accounting_entry_id:
                    entry = item.accounting_entry
                    # dynamic property cache matching the logic in AccountingEntry.related_transaction
                    entry._related_transaction = trans_map.get(entry.transaction_id)


class AllContractPaymentViewSet(ContractPaymentViewSet):
    pagination_class = PageNumberPaginationOneHundred
    ordering = ['installment_order', 'deal_date', 'created_at']


# Aggregation ViewSets ----------------------------------------------------------------

class ContractPaymentSummaryViewSet(viewsets.ViewSet):
    """
    PaymentSummary 컴포넌트용 unit_type별 요약 현황 ViewSet (Ledger 기반)

    기존 PaymentSummaryViewSet과 동일한 응답 구조 유지
    데이터 소스: ProjectCashBook → ContractPayment로 변경
    """
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    @staticmethod
    def list(request):
        project_id = request.query_params.get('project')
        date = request.query_params.get('date')

        if not project_id:
            return Response({'error': 'project parameter is required'}, status=400)

        try:
            # 코어 계산 로직 호출 (use_ledger_join=True)
            payment_status_data = calculate_payment_status_by_unit_type_core(project_id, date, use_ledger_join=True)

            # unit_type별로 그룹화해서 합계 계산
            unit_type_aggregates = defaultdict(lambda: {
                'unit_type_id': 0,
                'unit_type_name': '',
                'unit_type_color': '',
                'total_budget': 0,
                'total_contract_amount': 0,
                'total_paid_amount': 0,
                'unpaid_amount': 0,
                'non_contract_amount': 0
            })

            for item in payment_status_data:
                unit_type_name = item['unit_type_name']
                unit_type_id = item['unit_type_id']
                unit_type_color = item['unit_type_color']

                agg = unit_type_aggregates[unit_type_name]
                agg['unit_type_id'] = unit_type_id
                agg['unit_type_name'] = unit_type_name
                agg['unit_type_color'] = unit_type_color
                agg['total_budget'] += item['total_budget']
                agg['total_contract_amount'] += item['contract_amount']
                agg['total_paid_amount'] += item['paid_amount']
                agg['unpaid_amount'] += item['unpaid_amount']
                agg['non_contract_amount'] += item['non_contract_amount']

            # 결과 생성
            results = []
            for unit_type_name, agg in unit_type_aggregates.items():
                # 미분양금액 = 총예산 - 계약금액
                unsold_amount = max(0, agg['total_budget'] - agg['total_contract_amount'])

                results.append({
                    'unit_type_id': agg['unit_type_id'],
                    'unit_type_name': agg['unit_type_name'],
                    'unit_type_color': agg['unit_type_color'],
                    'total_budget': agg['total_budget'],  # 총 매출예산(A)
                    'total_contract_amount': agg['total_contract_amount'],  # 총 분양금액(B)
                    'total_paid_amount': agg['total_paid_amount'],  # 총 수납금액(C)
                    'unpaid_amount': agg['unpaid_amount'],  # 미수납금액(B-C)
                    'unsold_amount': unsold_amount  # 미분양금액(A-B)
                })

            # unit_type_id로 정렬
            results.sort(key=lambda x: x['unit_type_id'])

            serializer = PaymentSummaryComponentSerializer(results, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in ContractPaymentSummaryViewSet.list: {e}")
            return Response({
                'error': 'An internal server error has occurred.'
            }, status=500)


class ContractPaymentStatusByUnitTypeViewSet(viewsets.ViewSet):
    """
    ContractPrice 모델 기반의 unit_type별 결제 현황 ViewSet (Ledger 기반)

    기존 PaymentStatusByUnitTypeViewSet과 동일한 로직
    실수납금액 계산: ProjectCashBook → ContractPayment로 변경
    """
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    @staticmethod
    def list(request):
        project_id = request.query_params.get('project')
        date = request.query_params.get('date')

        if not project_id:
            return Response({'error': 'project parameter is required'}, status=400)

        try:
            results = calculate_payment_status_by_unit_type_core(project_id, date, use_ledger_join=True)
            serializer = PaymentStatusByUnitTypeSerializer(results, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in ContractPaymentStatusByUnitTypeViewSet.list: {e}")
            return Response({
                'error': 'An internal server error has occurred.'
            }, status=500)

    @staticmethod
    def _get_sales_amount_by_unit_type(project_id, order_group_id, unit_type_id):
        """ContractPrice 테이블의 유효한 모든 가격정보 합계"""
        try:
            with connection.cursor() as cursor:
                project = Project.objects.get(pk=project_id)
                default_og = OrderGroup.get_default_for_project(project)

                contract_query = """
                                 SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as contract_amount
                                 FROM contract_contractprice cp
                                          CROSS JOIN jsonb_each_text(cp.payment_amounts)
                                          INNER JOIN contract_contract c ON cp.contract_id = c.id
                                 WHERE c.project_id = %s
                                   AND c.order_group_id = %s
                                   AND c.unit_type_id = %s
                                   AND c.is_active = true
                                   AND cp.is_cache_valid = true \
                                 """

                cursor.execute(contract_query, [project_id, order_group_id, unit_type_id])
                contract_result = cursor.fetchone()
                contract_amount = contract_result[0] if contract_result else 0

                # 미계약 가격 합계
                non_contract_amount = 0
                if default_og and order_group_id == default_og.pk:
                    non_contract_query = """
                                         SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as non_contract_amount
                                         FROM contract_contractprice cp
                                                  CROSS JOIN jsonb_each_text(cp.payment_amounts)
                                                  INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
                                         WHERE cp.contract_id IS NULL
                                           AND hu.unit_type_id = %s
                                           AND cp.is_cache_valid = true \
                                         """

                    cursor.execute(non_contract_query, [unit_type_id])
                    non_contract_result = cursor.fetchone()
                    non_contract_amount = non_contract_result[0] if non_contract_result else 0

                total_amount = contract_amount + non_contract_amount

                # 근린생활시설 특별 처리
                if total_amount == 0:
                    try:
                        unit_type = UnitType.objects.get(pk=unit_type_id)
                        if unit_type.sort == '5':
                            has_house_units = HouseUnit.objects.filter(unit_type_id=unit_type_id).exists()
                            has_sales_price = SalesPriceByGT.objects.filter(
                                project_id=project_id,
                                order_group_id=order_group_id,
                                unit_type_id=unit_type_id
                            ).exists()

                            if has_house_units and not has_sales_price:
                                total_amount = ContractPaymentStatusByUnitTypeViewSet._get_commercial_fallback_amount(
                                    project_id, order_group_id, unit_type_id
                                )
                    except UnitType.DoesNotExist:
                        pass

                return total_amount

        except Exception as e:
            return 0

    @staticmethod
    def _get_commercial_fallback_amount(project_id, order_group_id, unit_type_id):
        """근린생활시설 전용 fallback 로직"""
        try:
            try:
                budget = ProjectIncBudget.objects.get(
                    project_id=project_id,
                    order_group_id=order_group_id,
                    unit_type_id=unit_type_id
                )
                if budget.budget and budget.budget > 0:
                    return budget.budget
            except ProjectIncBudget.DoesNotExist:
                pass

            try:
                unit_type = UnitType.objects.get(pk=unit_type_id)
                if hasattr(unit_type, 'average_price') and unit_type.average_price and unit_type.average_price > 0:
                    return unit_type.average_price
            except UnitType.DoesNotExist:
                pass

            return 0

        except Exception as e:
            return 0

    @staticmethod
    def _get_contract_data_by_unit_type(project_id, order_group_id, unit_type_id):
        """계약 현황 데이터 계산"""
        try:
            with connection.cursor() as cursor:
                query = """
                        SELECT COUNT(*)                   as contract_units,
                               COALESCE(SUM(cp.price), 0) as contract_amount
                        FROM contract_contract c
                                 INNER JOIN contract_contractprice cp ON cp.contract_id = c.id
                        WHERE c.project_id = %s
                          AND c.order_group_id = %s
                          AND c.unit_type_id = %s
                          AND c.is_active = true
                          AND cp.is_cache_valid = true
                        """

                cursor.execute(query, [project_id, order_group_id, unit_type_id])
                result = cursor.fetchone()
                return {
                    'contract_units': result[0] if result else 0,
                    'contract_amount': result[1] if result else 0
                }

        except Exception as e:
            return {'contract_units': 0, 'contract_amount': 0}

    @staticmethod
    def _get_paid_amount_by_unit_type(project_id, order_group_id, unit_type_id, date):
        """
        order_group과 unit_type별 실수납금액 계산 (Ledger 기반)

        변경점: ProjectCashBook → ContractPayment + ProjectAccountingEntry
        """
        try:
            with connection.cursor() as cursor:
                date_filter = ""
                params = [project_id, order_group_id, unit_type_id]

                if date:
                    date_filter = "AND pbt.deal_date <= %s"
                    params.append(date)

                # Ledger 기반 집계: ContractPayment → accounting_entry → related_transaction
                query = f"""
                        SELECT COALESCE(SUM(pae.amount), 0) as paid_amount
                        FROM payment_contractpayment cp
                                 INNER JOIN ledger_projectaccountingentry pae ON cp.accounting_entry_id = pae.id
                                 INNER JOIN ledger_projectbanktransaction pbt ON pae.transaction_id = pbt.transaction_id
                                 INNER JOIN contract_contract c ON cp.contract_id = c.id
                                 INNER JOIN ledger_projectaccount pa ON pae.account_id = pa.id
                        WHERE cp.project_id = %s
                          AND c.order_group_id = %s
                          AND c.unit_type_id = %s
                          AND c.is_active = true
                          AND pa.is_payment = true
                          AND cp.is_payment_mismatch = false
                          {date_filter}
                        """

                cursor.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            return 0

    @staticmethod
    def _get_non_contract_amount_by_unit_type(project_id, order_group_id, unit_type_id):
        """order_group과 unit_type별 미계약 금액 계산"""
        try:
            project = Project.objects.get(pk=project_id)
            default_og = OrderGroup.get_default_for_project(project)
            if not default_og:
                return 0

            if order_group_id == default_og.pk:
                with connection.cursor() as cursor:
                    query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as non_contract_amount
                            FROM contract_contractprice cp, jsonb_each_text(cp.payment_amounts)
                            WHERE cp.contract_id IS NULL
                              AND cp.house_unit_id IN (SELECT hu.id
                                                       FROM items_houseunit hu
                                                       WHERE hu.unit_type_id = %s)
                              AND cp.is_cache_valid = true
                            """

                    cursor.execute(query, [unit_type_id])
                    result = cursor.fetchone()
                    return result[0] if result else 0
            else:
                return 0

        except Exception as e:
            return 0

    @staticmethod
    def _get_non_contract_units_by_unit_type(project_id, order_group_id, unit_type_id):
        """order_group과 unit_type별 미계약 세대수 계산"""
        try:
            project = Project.objects.get(pk=project_id)
            default_og = OrderGroup.get_default_for_project(project)
            if not default_og:
                return 0

            if order_group_id == default_og.pk:
                with connection.cursor() as cursor:
                    query = """
                            SELECT COUNT(*) as non_contract_units
                            FROM contract_contractprice cp
                                     INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
                            WHERE cp.contract_id IS NULL
                              AND hu.unit_type_id = %s
                              AND cp.is_cache_valid = true
                            """

                    cursor.execute(query, [unit_type_id])
                    result = cursor.fetchone()
                    return result[0] if result else 0
            else:
                return 0

        except Exception as e:
            return 0


class ContractPaymentOverallSummaryViewSet(viewsets.ViewSet):
    """
    InstallmentPaymentOrder별 총괄 집계 ViewSet (Ledger 기반)

    기존 OverallSummaryViewSet과 동일한 로직
    수납 데이터: ProjectCashBook → ContractPayment로 변경
    """
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

        # 수납 데이터를 배치로 조회하여 캐시 (Ledger 기반)
        collection_cache = self._get_all_collection_data(project_id, date, pay_orders)

        # 기간미도래 미수금 캐시
        not_due_unpaid_cache = self._get_not_due_unpaid_cache(project_id, date, pay_orders, payment_amounts_cache,
                                                              collection_cache)

        result_pay_orders = []

        for order in pay_orders:
            # 캐시된 계약 금액 사용
            contract_amount = payment_amounts_cache.get(order.pay_time, 0)

            # 캐시된 미계약 금액 사용
            non_contract_amount = non_contract_amounts_cache.get(order.pay_time, 0)

            # 캐시된 수납 데이터 사용
            collection_data = collection_cache.get(order.pk, {
                'collected_amount': 0,
                'discount_amount': 0,
                'overdue_fee': 0,
                'actual_collected': 0,
                'collection_rate': 0
            })

            # collection_rate 계산
            collection_rate = (
                    collection_data['actual_collected'] / contract_amount * 100) if contract_amount > 0 else 0
            collection_data['collection_rate'] = round(collection_rate, 2)

            # 기간도래 관련 집계
            due_period_data = self._get_due_period_data_optimized(order, contract_amount, collection_data, date)

            # 기간미도래 미수금
            not_due_unpaid = not_due_unpaid_cache.get(order.pk, 0)

            # 총 미수금 = 해당 회차의 기간도래 미수금 + 해당 회차의 기간미도래 미수금
            due_unpaid = due_period_data['unpaid_amount']
            not_due_unpaid = not_due_unpaid_cache.get(order.pk, 0)

            total_unpaid = due_unpaid + not_due_unpaid
            total_unpaid_rate = (total_unpaid / contract_amount * 100) if contract_amount > 0 else 0

            # 회차별 계약률 계산
            order_total_amount = contract_amount + non_contract_amount
            order_contract_rate = (contract_amount / order_total_amount * 100) if order_total_amount > 0 else 0

            result_pay_orders.append({
                'pk': order.pk,
                'pay_name': order.pay_name,
                'pay_due_date': order.pay_due_date,
                'pay_sort': order.pay_sort,
                'pay_code': order.pay_code,
                'pay_time': order.pay_time,
                'contract_amount': contract_amount,
                'non_contract_amount': non_contract_amount,
                'contract_rate': round(order_contract_rate, 2),
                'collection': collection_data,
                'due_period': due_period_data,
                'not_due_unpaid': not_due_unpaid,
                'total_unpaid': total_unpaid,
                'total_unpaid_rate': round(total_unpaid_rate, 2)
            })

        # 전체 미수금 계산
        total_overall_unpaid = sum(order['total_unpaid'] for order in result_pay_orders)

        # 전체 계약금액 계산
        total_all_contract_amount = sum(
            payment_amounts_cache.get(order.pay_time, 0) for order in pay_orders
        )

        # 전체 미수율 계산
        total_overall_unpaid_rate = (
                total_overall_unpaid / total_all_contract_amount * 100) if total_all_contract_amount > 0 else 0

        # 마지막 회차에 전체 미수금 정보 추가
        if result_pay_orders:
            last_order = result_pay_orders[-1]
            last_order['total_overall_unpaid'] = total_overall_unpaid
            last_order['total_overall_unpaid_rate'] = round(total_overall_unpaid_rate, 2)

        # 집계 데이터 조회
        aggregate_data = self._get_aggregate_data(project_id)

        result = {
            'pay_orders': result_pay_orders,
            'aggregate': aggregate_data
        }

        serializer = OverallSummarySerializer(result)
        return Response(serializer.data)

    @staticmethod
    def _get_payment_amounts_cache(project_id, pay_orders):
        """PostgreSQL JSON 집계를 사용한 효율적인 납부 금액 캐시 생성 (pay_time 기반)"""
        pay_times = set()
        for order in pay_orders:
            pay_times.add(str(order.pay_time))

        payment_amounts_cache = {}

        try:
            with connection.cursor() as cursor:
                for pay_time in sorted(pay_times):
                    query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_amount
                            FROM contract_contractprice, jsonb_each_text(payment_amounts)
                            WHERE contract_id IN (SELECT id
                                                  FROM contract_contract
                                                  WHERE project_id = %s
                                                    AND is_active = %s)
                              AND is_cache_valid = %s
                              AND key = %s
                            """
                    cursor.execute(query, [project_id, True, True, pay_time])
                    result = cursor.fetchone()
                    payment_amounts_cache[int(pay_time)] = result[0] if result else 0

        except Exception as e:
            logger.error(f"Error in ContractPaymentOverallSummaryViewSet._get_payment_amounts_cache: {e}")
            for order in pay_orders:
                payment_amounts_cache[order.pay_time] = 0

        return payment_amounts_cache

    @staticmethod
    def _get_non_contract_amounts_cache(project_id, pay_orders):
        """미계약 세대 납부 금액 캐시 생성 (pay_time 기반) - 근린생활시설 fallback 포함"""
        pay_times = set()
        for order in pay_orders:
            pay_times.add(str(order.pay_time))

        non_contract_amounts_cache = {}

        try:
            with connection.cursor() as cursor:
                # pay_time별로 미계약 세대의 개별 금액을 집계
                for pay_time in sorted(pay_times):
                    query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as total
                            FROM contract_contractprice cp, jsonb_each_text(payment_amounts)
                            WHERE cp.contract_id IS NULL
                              AND cp.house_unit_id IN (SELECT hu.id
                                                       FROM items_houseunit hu
                                                                JOIN items_unittype ut ON hu.unit_type_id = ut.id
                                                       WHERE ut.project_id = %s)
                              AND cp.is_cache_valid = %s
                              AND key = %s
                            """
                    cursor.execute(query, [project_id, True, pay_time])
                    result = cursor.fetchone()
                    total_amount = result[0] if result else 0

                    # 근린생활시설 fallback 추가
                    commercial_fallback = ContractPaymentOverallSummaryViewSet._get_commercial_fallback_for_overall(
                        project_id, int(pay_time)
                    )
                    total_amount += commercial_fallback

                    non_contract_amounts_cache[int(pay_time)] = total_amount

        except Exception as e:
            logger.error(f"Error in ContractPaymentOverallSummaryViewSet._get_non_contract_amounts_cache: {e}")
            # 실패 시 0으로 초기화
            for order in pay_orders:
                non_contract_amounts_cache[order.pay_time] = 0

        return non_contract_amounts_cache

    @staticmethod
    def _get_commercial_fallback_for_overall(project_id, pay_time):
        """
        총괄 집계용 근린생활시설 fallback 로직 - 회차별 계산
        근린생활시설이 있지만 ContractPrice 데이터가 없을 때 fallback 적용
        납부회차가 없으면 기본 납부회차(잔금 100%) 적용
        """
        try:
            # 프로젝트의 기본 order_group 가져오기
            project = Project.objects.get(pk=project_id)
            default_og = OrderGroup.get_default_for_project(project)

            if not default_og:
                return 0

            # 근린생활시설 타입 찾기 (sort='5')
            commercial_unit_types = UnitType.objects.filter(
                project_id=project_id,
                sort='5'
            )

            total_fallback_amount = 0

            for unit_type in commercial_unit_types:
                # 해당 타입의 HouseUnit이 있는지 확인
                has_house_units = HouseUnit.objects.filter(unit_type_id=unit_type.pk).exists()

                # 해당 타입의 SalesPriceByGT가 있는지 확인
                has_sales_price = SalesPriceByGT.objects.filter(
                    project_id=project_id,
                    order_group_id=default_og.pk,
                    unit_type_id=unit_type.pk
                ).exists()

                # HouseUnit은 있지만 SalesPriceByGT가 없을 때만 fallback 적용
                if has_house_units and not has_sales_price:
                    # 예산 데이터에서 기본 금액 가져오기
                    base_amount = ContractPaymentStatusByUnitTypeViewSet._get_commercial_fallback_amount(
                        project_id, default_og.pk, unit_type.pk
                    )

                    if base_amount > 0:
                        # 프로젝트의 근린생활시설용 InstallmentPaymentOrder가 있는지 확인
                        installment_orders = InstallmentPaymentOrder.objects.filter(
                            project_id=project_id,
                            type_sort='5'  # 근린생활시설
                        )

                        if not installment_orders.exists():
                            # InstallmentPaymentOrder가 없으면 기본 납부회차 적용: 잔금 100%
                            # 잔금인지 확인 (pay_sort='3')
                            try:
                                pay_order = InstallmentPaymentOrder.objects.get(
                                    project_id=project_id,
                                    pay_time=pay_time
                                )
                                if pay_order.pay_sort == '3':  # 잔금
                                    installment_amount = base_amount
                                    total_fallback_amount += installment_amount
                            except InstallmentPaymentOrder.DoesNotExist:
                                pass
                        else:
                            # InstallmentPaymentOrder가 있으면 해당 회차에 따라 계산
                            try:
                                pay_order = InstallmentPaymentOrder.objects.get(
                                    project_id=project_id,
                                    pay_time=pay_time,
                                    type_sort='5'  # 근린생활시설용만
                                )

                                if pay_order.pay_amt:
                                    # pay_amt가 설정된 경우 그 값 사용
                                    installment_amount = pay_order.pay_amt
                                    total_fallback_amount += installment_amount
                                elif pay_order.pay_ratio:
                                    # pay_ratio가 설정된 경우 base_amount에 비율 적용
                                    installment_amount = int(base_amount * (pay_order.pay_ratio / 100))
                                    total_fallback_amount += installment_amount
                                elif pay_order.pay_name == '잔금':
                                    # 잔금의 경우 남은 비율을 자동 계산
                                    other_orders = InstallmentPaymentOrder.objects.filter(
                                        project_id=project_id,
                                        type_sort='5'
                                    ).exclude(pay_time=pay_time)
                                    used_ratio = sum(order.pay_ratio or 0 for order in other_orders)
                                    remaining_ratio = 100 - used_ratio

                                    if remaining_ratio > 0:
                                        installment_amount = int(base_amount * (remaining_ratio / 100))
                                        total_fallback_amount += installment_amount

                            except InstallmentPaymentOrder.DoesNotExist:
                                pass

            return total_fallback_amount

        except Exception as e:
            logger.error(f"Error in ContractPaymentOverallSummaryViewSet._get_commercial_fallback_for_overall: {e}")
            return 0

    @staticmethod
    def _get_all_collection_data(project_id, date, pay_orders):
        """
        회차별 수납 데이터를 배치로 조회하여 캐시 (Ledger 기반)

        변경점: ProjectCashBook → ContractPayment + ProjectAccountingEntry
        is_payment_mismatch=False: 유효한 계약자 납부 (환불/해지 제외)
        """
        collection_cache = {}

        try:
            # ORM을 사용한 안전하고 간단한 집계
            order_ids = [order.pk for order in pay_orders]

            payments_data = ContractPayment.objects.filter(
                project_id=project_id,
                installment_order__in=order_ids,
                is_payment_mismatch=False,
                deal_date__lte=date
            ).values('installment_order').annotate(
                total_collected=Sum('accounting_entry__amount')
            )

            # 결과를 딕셔너리로 변환
            payments_dict = {
                item['installment_order']: item['total_collected'] or 0
                for item in payments_data
            }

            # 각 회차별로 캐시 생성
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

        except Exception as e:
            logger.error(f"Error in ContractPaymentOverallSummaryViewSet._get_all_collection_data: {e}")
            # 오류 시 모든 회차를 0으로 초기화
            for order in pay_orders:
                collection_cache[order.pk] = {
                    'collected_amount': 0,
                    'discount_amount': 0,
                    'overdue_fee': 0,
                    'actual_collected': 0,
                    'collection_rate': 0
                }

        return collection_cache

    @staticmethod
    def _get_due_period_data_optimized(order, contract_amount, collection_data, date):
        """기간도래 관련 집계 (helper 로직 적용)"""
        is_due = is_due_period(order, date)

        if not is_due:
            # 기간미도래
            return {
                'contract_amount': 0,
                'unpaid_amount': 0,
                'unpaid_rate': 0,
                'overdue_fee': 0,
                'subtotal': 0
            }
        else:
            # 기간도래
            actual_collected = collection_data['actual_collected']
            # 기간도래 미수금 = 계약금액 - 수납액 (음수 포함 - 초과납부 반영)
            unpaid_amount = contract_amount - actual_collected
            unpaid_rate = (unpaid_amount / contract_amount * 100) if contract_amount > 0 else 0

            # TODO: 기간도래분 연체료 계산 로직 구현 필요
            overdue_fee = collection_data.get('overdue_fee', 0)
            subtotal = unpaid_amount + overdue_fee

            return {
                'contract_amount': contract_amount,
                'unpaid_amount': unpaid_amount,
                'unpaid_rate': round(unpaid_rate, 2),
                'overdue_fee': overdue_fee,
                'subtotal': subtotal
            }

    @staticmethod
    def _get_not_due_unpaid_cache(project_id, date, pay_orders, payment_amounts_cache, collection_cache):
        """기간미도래 미수금 캐시 생성 (helper 로직 적용)"""
        not_due_unpaid_cache = {}

        for order in pay_orders:
            is_due = is_due_period(order, date)

            if not is_due:
                # 기간미도래 회차
                contract_amount = payment_amounts_cache.get(order.pay_time, 0)
                actual_collected = collection_cache.get(order.pk, {}).get('actual_collected', 0)
                # 미수금 = 계약금액 - 수납액 (음수 포함 - 초과납부 반영)
                not_due_unpaid = contract_amount - actual_collected
                not_due_unpaid_cache[order.pk] = not_due_unpaid
            else:
                # 기간도래 회차
                not_due_unpaid_cache[order.pk] = 0

        return not_due_unpaid_cache

    @staticmethod
    def _get_aggregate_data(project_id):
        """집계 데이터 조회 (Ledger 기반)"""
        # 계약 세대수
        conts_num = Contract.objects.filter(
            project_id=project_id,
            is_active=True,
            contractor__status=2
        ).count()

        # 전체 세대수 (KeyUnit 기준)
        total_units = KeyUnit.objects.filter(project_id=project_id,
                                             unit_type__main_or_sub='1').count()

        # 미계약 세대수
        non_conts_num = total_units - conts_num

        # 계약률 계산 (금액 기준): 계약금액 / 총매출액
        try:
            payment_status_data = calculate_payment_status_by_unit_type_core(project_id, use_ledger_join=True)
            total_contract_amount = sum(item['contract_amount'] for item in payment_status_data)
            total_sales_amount = sum(item['total_sales_amount'] for item in payment_status_data)
            contract_rate = (total_contract_amount / total_sales_amount * 100) if total_sales_amount > 0 else 0
        except Exception as e:
            logger.error(f"Error in ContractPaymentOverallSummaryViewSet._get_aggregate_data: {e}")
            contract_rate = 0

        return {
            'conts_num': conts_num,
            'non_conts_num': non_conts_num,
            'total_units': total_units,
            'contract_rate': round(contract_rate, 2)
        }
