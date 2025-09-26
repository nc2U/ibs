from django.db import connection
from project.models import Project
from contract.models import OrderGroup

print("=== 근린생활시설 전체매출액 디버깅 ===")

project = Project.objects.get(pk=1)
default_og = OrderGroup.get_default_for_project(project)

print(f"기본 order_group: {default_og.name} (ID: {default_og.pk})")

with connection.cursor() as cursor:
    # 근린생활시설의 계약 가격 확인 (price 기준)
    print("\n1. 근린생활시설 계약 가격 확인:")
    cursor.execute("""
        SELECT COALESCE(SUM(cp.price), 0) as contract_amount
        FROM contract_contractprice cp
        INNER JOIN contract_contract c ON cp.contract_id = c.id
        WHERE c.project_id = %s
          AND c.order_group_id = %s
          AND c.unit_type_id = 4
          AND c.activation = true
          AND cp.is_cache_valid = true
    """, [1, default_og.pk])

    result = cursor.fetchone()
    contract_amount = result[0] if result else 0
    print(f"  계약 금액: {contract_amount:,}")

    # 근린생활시설의 미계약 가격 확인 (price 기준)
    print("\n2. 근린생활시설 미계약 가격 확인:")
    cursor.execute("""
        SELECT COALESCE(SUM(cp.price), 0) as non_contract_amount
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
    """, [])

    result = cursor.fetchone()
    non_contract_amount = result[0] if result else 0
    print(f"  미계약 금액: {non_contract_amount:,}")

    print(f"\n3. 전체 매출액 계산:")
    total_sales = contract_amount + non_contract_amount
    print(f"  계약 금액 + 미계약 금액 = {contract_amount:,} + {non_contract_amount:,} = {total_sales:,}")

# API 함수 직접 호출
print("\n4. API 함수 직접 호출:")
from apiV1.views.payment import PaymentStatusByUnitTypeViewSet

sales_amount = PaymentStatusByUnitTypeViewSet._get_sales_amount_by_unit_type(
    1, default_og.pk, 4  # project_id=1, order_group_id=default_og.pk, unit_type_id=4
)
print(f"  _get_sales_amount_by_unit_type 결과: {sales_amount:,}")

# 근린생활시설 전체 데이터 확인
print("\n5. 근린생활시설 ContractPrice 전체 데이터:")
cursor.execute("""
    SELECT
        cp.id,
        cp.contract_id,
        cp.price,
        c.order_group_id
    FROM contract_contractprice cp
    INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
    LEFT JOIN contract_contract c ON cp.contract_id = c.id
    WHERE hu.unit_type_id = 4
      AND cp.is_cache_valid = true
    LIMIT 10
""")

for row in cursor.fetchall():
    cp_id, contract_id, price, order_group_id = row
    print(f"  ID: {cp_id}, contract_id: {contract_id}, price: {price:,}, order_group_id: {order_group_id}")