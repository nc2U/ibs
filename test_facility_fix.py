from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

request = Mock()
request.query_params = {'project': '1', 'date': '2024-12-31'}

response = PaymentStatusByUnitTypeViewSet.list(request)
data = response.data

print("=== 수정된 API 테스트 결과 ===")
total_sales = 0
total_contract_units = 0
total_non_contract_units = 0
total_contract_amount = 0
total_non_contract_amount = 0
total_budget = 0

for item in data:
    total_sales += item['total_sales_amount']
    total_contract_units += item['contract_units']
    total_non_contract_units += item['non_contract_units']
    total_contract_amount += item['contract_amount']
    total_non_contract_amount += item['non_contract_amount']
    total_budget += item['total_budget']

    if item['unit_type_name'] == '근린생활시설' or item['non_contract_units'] > 0:
        print(f"{item['order_group_name']} | {item['unit_type_name']}:")
        print(f"  전체 매출액: {item['total_sales_amount']:,}")
        print(f"  계약 세대수: {item['contract_units']}")
        print(f"  미계약 세대수: {item['non_contract_units']}")
        print(f"  계약 금액: {item['contract_amount']:,}")
        print(f"  미계약 금액: {item['non_contract_amount']:,}")
        print(f"  합계: {item['total_budget']:,}")
        print()

print("=== 전체 합계 ===")
print(f"전체 매출액 합계: {total_sales:,}")
print(f"계약 세대수 합계: {total_contract_units}")
print(f"미계약 세대수 합계: {total_non_contract_units}")
print(f"계약 금액 합계: {total_contract_amount:,}")
print(f"미계약 금액 합계: {total_non_contract_amount:,}")
print(f"합계 (계약+미계약): {total_budget:,}")

# 검증
print(f"\n=== 검증 ===")
print(f"전체 매출액 = 합계? {total_sales == total_budget} ({total_sales:,} = {total_budget:,})")
print(f"세대수 합계: 계약 {total_contract_units} + 미계약 {total_non_contract_units} = {total_contract_units + total_non_contract_units}")