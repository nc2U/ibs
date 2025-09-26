from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

request = Mock()
request.query_params = {'project': '1', 'date': '2024-12-31'}

response = PaymentStatusByUnitTypeViewSet.list(request)
data = response.data

print("=== 최종 API 테스트 결과 ===")
total_non_contract_units = 0

for item in data:
    non_contract_units = item.get('non_contract_units', 0)
    total_non_contract_units += non_contract_units

    print(f"{item['order_group_name']} | {item['unit_type_name']}:")
    print(f"  계약 세대수: {item['contract_units']}")
    print(f"  미계약 세대수: {non_contract_units}")
    print(f"  미계약 금액: {item['non_contract_amount']:,}")
    print()

print(f"총 미계약 세대수: {total_non_contract_units}")

# Vue에서 봐야 할 데이터 확인
print("\n=== Vue에서 표시될 데이터 (미계약 세대수 > 0인 항목들) ===")
for item in data:
    if item.get('non_contract_units', 0) > 0:
        print(f"{item['order_group_name']} | {item['unit_type_name']}: {item['non_contract_units']}세대")