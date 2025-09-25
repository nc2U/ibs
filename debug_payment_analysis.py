#!/usr/bin/env python
import os
import sys
import django

# Django 설정
sys.path.append('/Users/austinkho/Git/Pro/ibs/app/django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_config.settings')
django.setup()

from apiV1.views.payment import PaymentStatusByUnitTypeViewSet
from unittest.mock import Mock

def analyze_payment_discrepancy():
    request = Mock()
    request.query_params = {'project': '1', 'date': '2024-12-31'}

    response = PaymentStatusByUnitTypeViewSet.list(request)
    data = response.data

    print('=== 상세 분석 ===')
    total_sales_sum = 0
    contract_plus_non_contract_sum = 0

    discrepancy_items = []

    for item in data:
        total_sales = item['total_sales_amount']
        contract_amount = item['contract_amount']
        non_contract_amount = item['non_contract_amount']
        calc_sum = contract_amount + non_contract_amount

        diff = total_sales - calc_sum

        if diff != 0:
            discrepancy_items.append({
                'name': f"{item['order_group_name']} | {item['unit_type_name']}",
                'total_sales': total_sales,
                'contract_amount': contract_amount,
                'non_contract_amount': non_contract_amount,
                'calc_sum': calc_sum,
                'diff': diff
            })

        total_sales_sum += total_sales
        contract_plus_non_contract_sum += calc_sum

    # 차이가 있는 항목들 출력
    for item in discrepancy_items:
        print(f"{item['name']}:")
        print(f"  전체매출액: {item['total_sales']:,}")
        print(f"  계약금액: {item['contract_amount']:,}")
        print(f"  미계약금액: {item['non_contract_amount']:,}")
        print(f"  계약+미계약: {item['calc_sum']:,}")
        print(f"  차이: {item['diff']:,}")
        print()

    print(f'전체 매출액 합계: {total_sales_sum:,}')
    print(f'계약+미계약 합계: {contract_plus_non_contract_sum:,}')
    print(f'총 차이: {total_sales_sum - contract_plus_non_contract_sum:,}')

    return discrepancy_items

if __name__ == '__main__':
    analyze_payment_discrepancy()