from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

print("=== 기본 납부회차 적용 테스트 ===")

request = Mock()
request.query_params = {'project': '1', 'date': '2024-12-31'}

response = PaymentStatusByUnitTypeViewSet.list(request)
data = response.data

print("수정된 API 응답 데이터:")
for item in data:
    if item['unit_type_name'] == '근린생활시설':
        print(f"{item['order_group_name']} | {item['unit_type_name']}:")
        print(f"  전체 매출액: {item['total_sales_amount']:,}")
        print(f"  계약 세대수: {item['contract_units']}")
        print(f"  미계약 세대수: {item['non_contract_units']}")
        print(f"  계약 금액: {item['contract_amount']:,}")
        print(f"  미계약 금액: {item['non_contract_amount']:,}")
        print(f"  합계: {item['total_budget']:,}")

        # 기본 납부회차 계산 확인
        # 근린생활시설 가격: 242,266,000 * 12세대 = 2,907,192,000
        expected_total = 242_266_000 * 12
        print(f"  예상 총액: {expected_total:,}")
        print(f"  실제 총액과 일치? {item['total_sales_amount'] == expected_total}")

        print(f"\n  기본 납부회차 적용 확인:")
        print(f"    - payment_amounts가 비어있는 경우 price 필드(100%) 사용")
        print(f"    - 실제로는 계약시 10% + 2차계약금 10% + 잔금 80% = 100%")
        print(f"    - 현재 구현: payment_amounts 비어있으면 전체 price 반환")
        break
else:
    print("근린생활시설 데이터를 찾을 수 없습니다.")

print("\n=== 전체 합계 검증 ===")
total_sales = sum(item['total_sales_amount'] for item in data)
total_budget = sum(item['total_budget'] for item in data)
print(f"전체 매출액 합계: {total_sales:,}")
print(f"전체 예산 합계: {total_budget:,}")
print(f"일치여부: {total_sales == total_budget}")