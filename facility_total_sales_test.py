from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

request = Mock()
request.query_params = {'project': '1', 'date': '2024-12-31'}

response = PaymentStatusByUnitTypeViewSet.list(request)
data = response.data

print("=== 근린생활시설 전체 매출액 확인 ===")

for item in data:
    if item['unit_type_name'] == '근린생활시설':
        print(f"{item['order_group_name']} | {item['unit_type_name']}:")
        print(f"  전체 매출액: {item['total_sales_amount']:,}")
        print(f"  계약 세대수: {item['contract_units']}")
        print(f"  미계약 세대수: {item['non_contract_units']}")
        print(f"  계약 금액: {item['contract_amount']:,}")
        print(f"  미계약 금액: {item['non_contract_amount']:,}")
        print(f"  합계: {item['total_budget']:,}")
        print()

        # 검증
        expected_total = item['contract_amount'] + item['non_contract_amount']
        print(f"검증: 계약금액({item['contract_amount']:,}) + 미계약금액({item['non_contract_amount']:,}) = {expected_total:,}")
        print(f"전체매출액과 일치? {item['total_sales_amount'] == expected_total}")
        print(f"합계와 일치? {item['total_sales_amount'] == item['total_budget']}")
        break
else:
    print("근린생활시설 데이터를 찾을 수 없습니다.")