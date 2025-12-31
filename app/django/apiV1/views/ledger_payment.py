"""
Ledger-based payment API views

Payment aggregation ViewSets using ContractPayment and ProjectAccountingEntry
from the ledger app, replacing the legacy ProjectCashBook-based approach.

Data Flow:
    ProjectBankTransaction (은행 거래)
        → ProjectAccountingEntry (회계 분개, account.is_payment=True)
            → ContractPayment (계약 납부, 1:1)
"""
from collections import defaultdict
from datetime import datetime

from django.db import connection
from django.db.models import Q, F
from django_filters import CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, permissions
from rest_framework.response import Response

from _utils.contract_price import get_contract_payment_plan
from contract.models import ContractPrice, Contract, OrderGroup
from items.models import UnitType, HouseUnit
from payment.models import ContractPayment, InstallmentPaymentOrder
from project.models import Project, ProjectIncBudget, SalesPriceByGT
from ..pagination import PageNumberPaginationOneHundred
from ..permission import IsProjectStaffOrReadOnly
from ..serializers.payment import (
    PaymentSummaryComponentSerializer,
    PaymentStatusByUnitTypeSerializer,
    OverallSummarySerializer
)
from ..serializers.ledger_payment import ContractPaymentSerializer, ContractPaymentListSerializer

TODAY = datetime.today().strftime('%Y-%m-%d')


# ContractPayment CRUD ViewSet --------------------------------------------------------

class ContractPaymentFilterSet(FilterSet):
    """ContractPayment 필터셋"""
    deal_date__gte = CharFilter(method='filter_deal_date_gte', label='거래일자 시작')
    deal_date__lte = CharFilter(method='filter_deal_date_lte', label='거래일자 종료')

    class Meta:
        model = ContractPayment
        fields = ['project', 'contract', 'installment_order']

    @staticmethod
    def filter_deal_date_gte(queryset, name, value):
        """거래일자 >= value 필터링"""
        if value:
            # ContractPayment → accounting_entry → related_transaction.deal_date
            return queryset.filter(accounting_entry__related_transaction__deal_date__gte=value)
        return queryset

    @staticmethod
    def filter_deal_date_lte(queryset, name, value):
        """거래일자 <= value 필터링"""
        if value:
            return queryset.filter(accounting_entry__related_transaction__deal_date__lte=value)
        return queryset


class ContractPaymentViewSet(viewsets.ModelViewSet):
    """
    ContractPayment 기본 CRUD ViewSet

    계약별 납부 내역 조회, 생성, 수정, 삭제
    """
    queryset = ContractPayment.objects.select_related(
        'accounting_entry',
        'accounting_entry__related_transaction',
        'accounting_entry__account',
        'contract',
        'contract__unit_type',
        'contract__order_group',
        'installment_order',
        'project'
    ).all()
    serializer_class = ContractPaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = ContractPaymentFilterSet
    pagination_class = PageNumberPaginationOneHundred
    search_fields = ['contract__contractor__name']  # 계약자명 검색

    def get_serializer_class(self):
        """목록 조회 시 최적화된 직렬화 사용"""
        if self.action == 'list':
            return ContractPaymentListSerializer
        return ContractPaymentSerializer


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
            # ContractPaymentStatusByUnitTypeViewSet 사용하여 정확한 계산
            payment_status_viewset = ContractPaymentStatusByUnitTypeViewSet()
            payment_status_request = type('MockRequest', (), {
                'query_params': {'project': project_id}
            })()
            if date:
                payment_status_request.query_params['date'] = date

            payment_status_response = payment_status_viewset.list(payment_status_request)

            if payment_status_response.status_code != 200:
                return Response({'error': 'Failed to fetch payment status data'}, status=500)

            payment_status_data = payment_status_response.data

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
            with connection.cursor() as cursor:
                # 기존 budgetList와 같은 구조로 데이터 조회
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

                    # 각종 데이터 계산
                    planned_units = row[5]
                    total_budget = row[6]
                    average_price = row[7] or 0

                    # 매출액 계산
                    total_sales_amount = ContractPaymentStatusByUnitTypeViewSet._get_sales_amount_by_unit_type(
                        project_id, order_group_id, unit_type_id
                    )

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
                    contract_data = ContractPaymentStatusByUnitTypeViewSet._get_contract_data_by_unit_type(
                        project_id, order_group_id, unit_type_id
                    )

                    # 실수납금액 계산 (Ledger 기반)
                    paid_amount = ContractPaymentStatusByUnitTypeViewSet._get_paid_amount_by_unit_type(
                        project_id, order_group_id, unit_type_id, date
                    )

                    contract_units = contract_data['contract_units']
                    contract_amount = contract_data['contract_amount']
                    unpaid_amount = contract_amount - paid_amount

                    # 미계약 금액
                    non_contract_amount = ContractPaymentStatusByUnitTypeViewSet._get_non_contract_amount_by_unit_type(
                        project_id, order_group_id, unit_type_id
                    )

                    # 미계약 세대수
                    non_contract_units = ContractPaymentStatusByUnitTypeViewSet._get_non_contract_units_by_unit_type(
                        project_id, order_group_id, unit_type_id
                    )

                    # 합계 = 계약금액 + 미계약금액
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

                serializer = PaymentStatusByUnitTypeSerializer(results, many=True)
                return Response(serializer.data)

        except Exception as e:
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
                                   AND c.activation = true
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
                                 INNER JOIN ledger_projectaccountingentry pae ON cp.accounting_entry_id = pae.accountingentry_ptr_id
                                 INNER JOIN ledger_projectbanktransaction pbt ON pae.transaction_id = pbt.transaction_id
                                 INNER JOIN contract_contract c ON cp.contract_id = c.id
                        WHERE cp.project_id = %s
                          AND c.order_group_id = %s
                          AND c.unit_type_id = %s
                          AND c.activation = true
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

    def _get_payment_amounts_cache(self, project_id, pay_orders):
        """PostgreSQL JSON 집계를 사용한 효율적인 납부 금액 캐시 생성"""
        pay_times = set()
        for order in pay_orders:
            pay_times.add(str(order.pay_time))

        payment_amounts_cache = {}

        try:
            with connection.cursor() as cursor:
                # 전체 활성 계약 수 확인
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

                # 전체 캐시가 유효한 경우 빠른 집계
                if total_active_contracts == valid_cache_contracts:
                    for pay_time_str in pay_times:
                        query = """
                                SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_amount
                                FROM contract_contractprice, jsonb_each_text(payment_amounts)
                                WHERE contract_id IN (SELECT id
                                                      FROM contract_contract
                                                      WHERE project_id = %s
                                                        AND activation = %s)
                                  AND is_cache_valid = %s
                                  AND key = %s
                                """
                        cursor.execute(query, [project_id, True, True, pay_time_str])
                        result = cursor.fetchone()
                        pay_time = int(pay_time_str)
                        payment_amounts_cache[pay_time] = result[0] if result else 0
                else:
                    # 일부 캐시가 무효화된 경우 fallback
                    for order in pay_orders:
                        amount = self._get_contract_amount(order, project_id)
                        payment_amounts_cache[order.pay_time] = amount

        except Exception as e:
            # 오류 시 fallback
            for order in pay_orders:
                amount = self._get_contract_amount(order, project_id)
                payment_amounts_cache[order.pay_time] = amount

        return payment_amounts_cache

    @staticmethod
    def _get_contract_amount(order, project_id):
        """특정 pay_time의 계약 금액 합계 계산"""
        try:
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
                fallback_amount = ContractPaymentOverallSummaryViewSet._get_contract_amount_fallback(order, project_id)
                return total_amount + fallback_amount

            return total_amount

        except (ValueError, TypeError) as e:
            return ContractPaymentOverallSummaryViewSet._get_contract_amount_fallback(order, project_id)
        except Exception as e:
            return ContractPaymentOverallSummaryViewSet._get_contract_amount_fallback(order, project_id)

    @staticmethod
    def _get_contract_amount_fallback(order, project_id):
        """캐시 실패 시 동적 계산 폴백"""
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

    def _get_non_contract_amounts_cache(self, project_id, pay_orders):
        """미계약 세대 납부 금액 캐시 (pay_time별)"""
        pay_times = set()
        for order in pay_orders:
            pay_times.add(str(order.pay_time))

        non_contract_amounts_cache = {}

        try:
            with connection.cursor() as cursor:
                for pay_time_str in pay_times:
                    query = """
                            SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as non_contract_amount
                            FROM contract_contractprice, jsonb_each_text(payment_amounts)
                            WHERE contract_id IS NULL
                              AND is_cache_valid = %s
                              AND key = %s
                            """
                    cursor.execute(query, [True, pay_time_str])
                    result = cursor.fetchone()
                    pay_time = int(pay_time_str)
                    non_contract_amounts_cache[pay_time] = result[0] if result else 0

        except Exception as e:
            for order in pay_orders:
                non_contract_amounts_cache[order.pay_time] = 0

        return non_contract_amounts_cache

    def _get_all_collection_data(self, project_id, date, pay_orders):
        """
        회차별 수납 데이터를 배치로 조회하여 캐시 (Ledger 기반)

        변경점: ProjectCashBook → ContractPayment + ProjectAccountingEntry
        """
        collection_cache = {}

        try:
            with connection.cursor() as cursor:
                for order in pay_orders:
                    query = """
                            WITH payment_data AS (SELECT pae.amount,
                                                         0 AS discount,
                                                         0 AS overdue_fee
                                                  FROM payment_contractpayment cp
                                                           INNER JOIN ledger_projectaccountingentry pae
                                                               ON cp.accounting_entry_id = pae.accountingentry_ptr_id
                                                           INNER JOIN ledger_projectbanktransaction pbt
                                                               ON pae.transaction_id = pbt.transaction_id
                                                  WHERE cp.project_id = %s
                                                    AND cp.installment_order_id = %s
                                                    AND pbt.deal_date <= %s)
                            SELECT COALESCE(SUM(amount), 0)       AS collected_amount,
                                   COALESCE(SUM(discount), 0)     AS discount_amount,
                                   COALESCE(SUM(overdue_fee), 0)  AS overdue_fee,
                                   COALESCE(SUM(amount), 0) +
                                   COALESCE(SUM(discount), 0) +
                                   COALESCE(SUM(overdue_fee), 0)  AS actual_collected
                            FROM payment_data
                            """

                    cursor.execute(query, [project_id, order.pk, date])
                    result = cursor.fetchone()

                    if result:
                        collection_cache[order.pk] = {
                            'collected_amount': result[0] or 0,
                            'discount_amount': result[1] or 0,
                            'overdue_fee': result[2] or 0,
                            'actual_collected': result[3] or 0,
                            'collection_rate': 0
                        }
                    else:
                        collection_cache[order.pk] = {
                            'collected_amount': 0,
                            'discount_amount': 0,
                            'overdue_fee': 0,
                            'actual_collected': 0,
                            'collection_rate': 0
                        }

        except Exception as e:
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
        """기간도래 관련 집계"""
        # 기간도래 여부 판정
        if not order.pay_due_date or date < order.pay_due_date.strftime('%Y-%m-%d'):
            # 기간미도래
            return {
                'due_amount': 0,
                'actual_collected': 0,
                'unpaid_amount': 0,
                'unpaid_rate': 0,
                'collection_rate': 0
            }
        else:
            # 기간도래
            due_amount = contract_amount
            actual_collected = collection_data['actual_collected']
            unpaid_amount = max(0, due_amount - actual_collected)
            unpaid_rate = (unpaid_amount / due_amount * 100) if due_amount > 0 else 0
            collection_rate = collection_data['collection_rate']

            return {
                'due_amount': due_amount,
                'actual_collected': actual_collected,
                'unpaid_amount': unpaid_amount,
                'unpaid_rate': round(unpaid_rate, 2),
                'collection_rate': collection_rate
            }

    def _get_not_due_unpaid_cache(self, project_id, date, pay_orders, payment_amounts_cache, collection_cache):
        """기간미도래 미수금 캐시 생성"""
        not_due_unpaid_cache = {}

        for order in pay_orders:
            if not order.pay_due_date or date < order.pay_due_date.strftime('%Y-%m-%d'):
                # 기간미도래 회차
                contract_amount = payment_amounts_cache.get(order.pay_time, 0)
                actual_collected = collection_cache.get(order.pk, {}).get('actual_collected', 0)
                not_due_unpaid = max(0, contract_amount - actual_collected)
                not_due_unpaid_cache[order.pk] = not_due_unpaid
            else:
                # 기간도래 회차
                not_due_unpaid_cache[order.pk] = 0

        return not_due_unpaid_cache

    @staticmethod
    def _get_aggregate_data(project_id):
        """집계 데이터 조회 (Ledger 기반)"""
        try:
            with connection.cursor() as cursor:
                query = """
                        SELECT COALESCE(SUM(cp.price), 0)                                   AS total_contract_amount,
                               COUNT(DISTINCT c.id)                                         AS total_contracts,
                               COALESCE(SUM(pae.amount), 0)                                 AS total_paid_amount
                        FROM contract_contract c
                                 INNER JOIN contract_contractprice cp ON c.id = cp.contract_id
                                 LEFT JOIN payment_contractpayment pcp ON c.id = pcp.contract_id
                                 LEFT JOIN ledger_projectaccountingentry pae
                                     ON pcp.accounting_entry_id = pae.accountingentry_ptr_id
                        WHERE c.project_id = %s
                          AND c.activation = TRUE
                          AND cp.is_cache_valid = TRUE
                        """

                cursor.execute(query, [project_id])
                result = cursor.fetchone()

                total_contract_amount = result[0] or 0
                total_contracts = result[1] or 0
                total_paid_amount = result[2] or 0
                total_unpaid_amount = total_contract_amount - total_paid_amount

                return {
                    'total_contract_amount': total_contract_amount,
                    'total_contracts': total_contracts,
                    'total_paid_amount': total_paid_amount,
                    'total_unpaid_amount': total_unpaid_amount
                }

        except Exception as e:
            return {
                'total_contract_amount': 0,
                'total_contracts': 0,
                'total_paid_amount': 0,
                'total_unpaid_amount': 0
            }
