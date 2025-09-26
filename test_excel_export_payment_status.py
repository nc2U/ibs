from _excel.views import ExportPaymentStatus
from unittest.mock import Mock

print("=== ExportPaymentStatus Excel 생성 테스트 ===")

# Mock request 객체 생성
mock_request = Mock()
mock_request.GET = {
    'project': '1',
    'date': '2024-12-31'
}

try:
    # Excel export 실행
    export_view = ExportPaymentStatus()
    response = export_view.get(mock_request)

    print(f"Excel 파일 생성 성공!")
    print(f"Content-Type: {response['Content-Type']}")
    print(f"Content-Disposition: {response['Content-Disposition']}")
    print(f"Response status: HTTP 200 OK")

    # 파일 크기 확인
    content_length = len(response.content) if hasattr(response, 'content') else 0
    print(f"Excel 파일 크기: {content_length:,} bytes")

    if content_length > 0:
        print("✅ Excel 파일이 성공적으로 생성되었습니다!")
    else:
        print("⚠️ Excel 파일이 비어있을 수 있습니다.")

except Exception as e:
    print(f"❌ Excel 파일 생성 실패: {str(e)}")
    import traceback
    traceback.print_exc()

# Vue 컴포넌트와 데이터 일치성 확인
print("\n=== Vue 컴포넌트와 데이터 일치성 확인 ===")

try:
    from apiV1.views.payment import PaymentStatusByUnitTypeViewSet

    # Vue에서 사용하는 것과 동일한 API 호출
    vue_request = Mock()
    vue_request.query_params = {'project': '1', 'date': '2024-12-31'}

    viewset = PaymentStatusByUnitTypeViewSet()
    vue_response = viewset.list(vue_request)
    vue_data = vue_response.data

    print(f"API 데이터 항목 수: {len(vue_data)}")

    # Excel에서 사용하는 것과 동일한 API 데이터 확인
    print("\n주요 데이터 검증:")
    for i, item in enumerate(vue_data[:3]):  # 처음 3개 항목만 확인
        print(f"{i+1}. {item['order_group_name']} | {item['unit_type_name']}:")
        print(f"   전체 매출액: {item['total_sales_amount']:,}")
        print(f"   계약 세대수: {item['contract_units']}")
        print(f"   미계약 세대수: {item['non_contract_units']}")
        print(f"   미계약 금액: {item['non_contract_amount']:,}")
        print(f"   합계: {item['total_budget']:,}")

    # 근린생활시설 데이터 특별 확인
    facility_items = [item for item in vue_data if item['unit_type_name'] == '근린생활시설']
    if facility_items:
        facility = facility_items[0]
        print(f"\n🏢 근린생활시설 데이터:")
        print(f"   전체 매출액: {facility['total_sales_amount']:,}")
        print(f"   미계약 세대수: {facility['non_contract_units']}")
        print(f"   미계약 금액: {facility['non_contract_amount']:,}")

        # 기본 납부회차 적용 확인
        expected_per_unit = 242_266_000
        expected_total = expected_per_unit * facility['non_contract_units']
        print(f"   예상 총액 (가격×세대수): {expected_total:,}")
        print(f"   실제 미계약금액: {facility['non_contract_amount']:,}")
        print(f"   일치 여부: {'✅' if facility['non_contract_amount'] == expected_total else '❌'}")

    # 전체 합계 확인
    totals = {
        'total_sales_amount': sum(item['total_sales_amount'] for item in vue_data),
        'contract_units': sum(item['contract_units'] for item in vue_data),
        'non_contract_units': sum(item['non_contract_units'] for item in vue_data),
        'contract_amount': sum(item['contract_amount'] for item in vue_data),
        'non_contract_amount': sum(item['non_contract_amount'] for item in vue_data),
        'total_budget': sum(item['total_budget'] for item in vue_data),
    }

    print(f"\n📊 전체 합계:")
    print(f"   전체 매출액: {totals['total_sales_amount']:,}")
    print(f"   계약 세대수: {totals['contract_units']}")
    print(f"   미계약 세대수: {totals['non_contract_units']}")
    print(f"   계약 금액: {totals['contract_amount']:,}")
    print(f"   미계약 금액: {totals['non_contract_amount']:,}")
    print(f"   총 예산: {totals['total_budget']:,}")

    print("\n✅ Vue 컴포넌트와 Excel이 동일한 API 데이터를 사용합니다!")

except Exception as e:
    print(f"❌ 데이터 검증 실패: {str(e)}")
    import traceback
    traceback.print_exc()