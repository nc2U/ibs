from django.db import connection

print("=== 근린생활시설 데이터 분석 ===")

# 1. 근린생활시설의 ProjectIncBudget 데이터 확인
print("1. ProjectIncBudget에서 근린생활시설 데이터:")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT
            pib.order_group_id,
            og.name as order_group_name,
            pib.unit_type_id,
            ut.name as unit_type_name,
            pib.quantity as planned_units,
            pib.budget as total_budget,
            pib.average_price
        FROM project_projectincbudget pib
        INNER JOIN items_unittype ut ON pib.unit_type_id = ut.id
        INNER JOIN contract_ordergroup og ON pib.order_group_id = og.id
        WHERE pib.project_id = %s
          AND ut.name = '근린생활시설'
        ORDER BY order_group_id
    """, [1])

    for row in cursor.fetchall():
        print(f"  {row[1]} (ID: {row[0]}) | {row[3]} (ID: {row[2]})")
        print(f"    계획 세대수: {row[4]}")
        print(f"    예산: {row[5]:,}")
        print(f"    평균 단가: {row[6]:,}" if row[6] else "    평균 단가: None")

# 2. 근린생활시설의 계약 데이터 확인
print("\n2. 근린생활시설 계약 데이터:")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT
            c.order_group_id,
            og.name,
            COUNT(*) as contract_count,
            SUM(cp.price) as contract_amount
        FROM contract_contract c
        INNER JOIN contract_contractprice cp ON cp.contract_id = c.id
        INNER JOIN contract_ordergroup og ON c.order_group_id = og.id
        WHERE c.project_id = %s
          AND c.unit_type_id = 4
          AND c.activation = true
          AND cp.is_cache_valid = true
        GROUP BY c.order_group_id, og.name
        ORDER BY c.order_group_id
    """, [1])

    for row in cursor.fetchall():
        print(f"  {row[1]} (ID: {row[0]}): {row[2]}세대, 계약금액 {row[3]:,}")

# 3. 근린생활시설의 미계약 데이터 확인
print("\n3. 근린생활시설 미계약 데이터:")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) as units_count
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
    """)

    count = cursor.fetchone()[0]
    print(f"  미계약 세대수: {count}")

    # 미계약 금액도 확인
    cursor.execute("""
        SELECT COALESCE(SUM(CAST(value AS INTEGER)), 0) as non_contract_amount
        FROM contract_contractprice cp
        CROSS JOIN jsonb_each_text(cp.payment_amounts)
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
    """)

    amount = cursor.fetchone()[0]
    print(f"  미계약 금액: {amount:,}")

# 4. 현재 API 결과와 비교
print("\n4. 현재 API 결과 확인:")
from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

request = Mock()
request.query_params = {'project': '1'}

response = PaymentStatusByUnitTypeViewSet.list(request)
data = response.data

for item in data:
    if item['unit_type_name'] == '근린생활시설':
        print(f"  {item['order_group_name']} | {item['unit_type_name']}:")
        print(f"    전체 매출액: {item['total_sales_amount']:,}")
        print(f"    계약 세대수: {item['contract_units']}")
        print(f"    미계약 세대수: {item['non_contract_units']}")
        print(f"    계약 금액: {item['contract_amount']:,}")
        print(f"    미계약 금액: {item['non_contract_amount']:,}")
        print(f"    합계: {item['total_budget']:,}")
        break