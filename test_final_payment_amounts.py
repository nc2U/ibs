from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

print("=== 최종 payment_amounts 적용 테스트 ===")

request = Mock()
request.query_params = {'project': '1', 'date': '2024-12-31'}

response = PaymentStatusByUnitTypeViewSet.list(request)
data = response.data

print("API 응답 데이터:")
for item in data:
    if item['unit_type_name'] == '근린생활시설':
        print(f"\n{item['order_group_name']} | {item['unit_type_name']}:")
        print(f"  전체 매출액: {item['total_sales_amount']:,}")
        print(f"  계약 세대수: {item['contract_units']}")
        print(f"  미계약 세대수: {item['non_contract_units']}")
        print(f"  계약 금액: {item['contract_amount']:,}")
        print(f"  미계약 금액: {item['non_contract_amount']:,}")
        print(f"  합계: {item['total_budget']:,}")

        print(f"\n  검증:")
        print(f"    계약금액 + 미계약금액 = {item['contract_amount']:,} + {item['non_contract_amount']:,} = {item['contract_amount'] + item['non_contract_amount']:,}")
        print(f"    전체매출액과 일치? {item['total_sales_amount'] == item['contract_amount'] + item['non_contract_amount']}")
        print(f"    합계와 일치? {item['total_sales_amount'] == item['total_budget']}")

        # payment_amounts 기반 계산 확인
        expected_per_unit = 242_266_000
        expected_total_for_12_units = expected_per_unit * 12
        print(f"\n  기본 납부회차 적용 확인:")
        print(f"    개당 가격: {expected_per_unit:,}")
        print(f"    12세대 총액: {expected_total_for_12_units:,}")
        print(f"    실제 미계약금액: {item['non_contract_amount']:,}")
        print(f"    일치여부: {item['non_contract_amount'] == expected_total_for_12_units}")

        break

print("\n=== 전체 합계 검증 ===")
total_sales = sum(item['total_sales_amount'] for item in data)
total_budget = sum(item['total_budget'] for item in data)
total_non_contract_amount = sum(item['non_contract_amount'] for item in data)

print(f"전체 매출액 합계: {total_sales:,}")
print(f"전체 예산 합계: {total_budget:,}")
print(f"전체 미계약금액 합계: {total_non_contract_amount:,}")
print(f"매출액 = 예산 일치여부: {total_sales == total_budget}")

print(f"\n근린생활시설 기본 납부회차 구조:")
print(f"  1차 (계약시 10%): 24,226,600원")
print(f"  2차 (2차계약금 10%): 24,226,600원")
print(f"  3차 (잔금 80%): 193,812,800원")
print(f"  합계: 242,266,000원 (100%)")
print(f"  12세대 총합: 2,907,192,000원")