from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

# API 테스트
request = Mock()
request.query_params = {'project': '1', 'date': '2024-12-31'}

response = PaymentStatusByUnitTypeViewSet.list(request)
data = response.data

print("=== 미계약 세대수 확인 ===")
total_non_contract_units = 0

for item in data:
    non_contract_units = item.get('non_contract_units', 0)
    total_non_contract_units += non_contract_units

    if non_contract_units > 0 or item['non_contract_amount'] > 0:
        print(f"{item['order_group_name']} | {item['unit_type_name']}:")
        print(f"  미계약 세대수: {non_contract_units}")
        print(f"  미계약 금액: {item['non_contract_amount']:,}")
        print()

print(f"총 미계약 세대수: {total_non_contract_units}")

# 미계약 세대 실제 데이터 직접 확인
print("\n=== ContractPrice 테이블 직접 확인 ===")
from django.db import connection

with connection.cursor() as cursor:
    # 미계약 세대 수 확인
    cursor.execute("""
        SELECT
            hu.unit_type_id,
            ut.name,
            COUNT(*) as units_count
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        INNER JOIN items_unittype ut ON hu.unit_type_id = ut.id
        WHERE cp.contract_id IS NULL
          AND cp.is_cache_valid = true
        GROUP BY hu.unit_type_id, ut.name
        ORDER BY hu.unit_type_id
    """)

    print("ContractPrice에서 contract_id IS NULL인 세대:")
    total_direct_count = 0
    for row in cursor.fetchall():
        unit_type_id, name, count = row
        total_direct_count += count
        print(f"  {name} (ID: {unit_type_id}): {count}세대")

    print(f"총 미계약 세대 (직접 조회): {total_direct_count}")

    # 기본 order_group 확인
    print("\n=== 기본 order_group 확인 ===")
    from project.models import Project
    from contract.models import OrderGroup

    project = Project.objects.get(pk=1)
    default_og = OrderGroup.get_default_for_project(project)

    if default_og:
        print(f"기본 order_group: {default_og.name} (ID: {default_og.pk})")
        print(f"is_default_for_uncontracted: {default_og.is_default_for_uncontracted}")
    else:
        print("기본 order_group을 찾을 수 없습니다!")