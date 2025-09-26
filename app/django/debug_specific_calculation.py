from apiV1.views.payment import PaymentStatusByUnitTypeViewSet

# 특정 order_group과 unit_type에 대한 미계약 세대수 계산 테스트
project_id = 1
order_group_id = 4  # 일반분양
unit_type_id = 1    # 74

print("=== 개별 함수 테스트 ===")
print(f"project_id: {project_id}, order_group_id: {order_group_id}, unit_type_id: {unit_type_id}")

# _get_non_contract_units_by_unit_type 함수 직접 호출
result = PaymentStatusByUnitTypeViewSet._get_non_contract_units_by_unit_type(
    project_id, order_group_id, unit_type_id
)

print(f"_get_non_contract_units_by_unit_type 결과: {result}")

# 각 unit_type별로 테스트
unit_types = [
    (1, '74'),
    (2, '84A'),
    (3, '84B'),
    (4, '근린생활시설')
]

print("\n=== 각 unit_type별 미계약 세대수 ===")
for unit_type_id, name in unit_types:
    result = PaymentStatusByUnitTypeViewSet._get_non_contract_units_by_unit_type(
        project_id, order_group_id, unit_type_id
    )
    print(f"{name} (unit_type_id: {unit_type_id}): {result}세대")

print("\n=== SQL 쿼리 직접 실행 ===")
from django.db import connection

with connection.cursor() as cursor:
    # 일반분양 order_group에 대해 각 unit_type별 미계약 세대수 확인
    for unit_type_id, name in unit_types:
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
        count = result[0] if result else 0
        print(f"{name} (unit_type_id: {unit_type_id}): {count}세대 (직접 SQL)")