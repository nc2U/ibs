from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

request = Mock()
request.query_params = {'project': '1', 'date': '2024-12-31'}

response = PaymentStatusByUnitTypeViewSet.list(request)
data = response.data

print('=== 차이가 있는 항목들 ===')
total_sales_sum = 0
contract_plus_non_contract_sum = 0

for item in data:
    total_sales = item['total_sales_amount']
    contract_amount = item['contract_amount']
    non_contract_amount = item['non_contract_amount']
    calc_sum = contract_amount + non_contract_amount

    diff = total_sales - calc_sum

    if diff != 0:
        print(f"{item['order_group_name']} | {item['unit_type_name']}:")
        print(f"  전체매출액: {total_sales:,}")
        print(f"  계약금액: {contract_amount:,}")
        print(f"  미계약금액: {non_contract_amount:,}")
        print(f"  계약+미계약: {calc_sum:,}")
        print(f"  차이: {diff:,}")
        print()

    total_sales_sum += total_sales
    contract_plus_non_contract_sum += calc_sum

print(f'전체 매출액 합계: {total_sales_sum:,}')
print(f'계약+미계약 합계: {contract_plus_non_contract_sum:,}')
print(f'총 차이: {total_sales_sum - contract_plus_non_contract_sum:,}')