from django.db import connection

print("=== 근린생활시설 ContractPrice 상세 분석 ===")

with connection.cursor() as cursor:
    # 근린생활시설 ContractPrice 데이터 확인
    cursor.execute("""
        SELECT
            cp.id,
            cp.contract_id,
            cp.house_unit_id,
            cp.price,
            cp.payment_amounts,
            cp.is_cache_valid,
            hu.name as house_unit_name
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE hu.unit_type_id = 4
          AND cp.is_cache_valid = true
        ORDER BY cp.id
        LIMIT 5
    """)

    print("근린생활시설 ContractPrice 레코드 (처음 5개):")
    for row in cursor.fetchall():
        cp_id, contract_id, house_unit_id, price, payment_amounts, is_cache_valid, house_unit_name = row
        print(f"  ID: {cp_id}")
        print(f"    contract_id: {contract_id}")
        print(f"    house_unit: {house_unit_name} (ID: {house_unit_id})")
        print(f"    price: {price:,}")
        print(f"    payment_amounts: {str(payment_amounts)[:100]}...")
        print(f"    is_cache_valid: {is_cache_valid}")
        print()

    # payment_amounts의 실제 값 확인
    print("미계약 근린생활시설의 payment_amounts 값:")
    cursor.execute("""
        SELECT
            cp.price,
            cp.payment_amounts,
            jsonb_each_text(cp.payment_amounts)
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
        LIMIT 3
    """)

    for row in cursor.fetchall():
        price, payment_amounts, json_values = row
        print(f"  price: {price:,}")
        print(f"  payment_amounts: {payment_amounts}")
        print(f"  json values: {json_values}")
        print()

    # payment_amounts의 총합 직접 계산
    print("payment_amounts 총합 계산:")
    cursor.execute("""
        SELECT
            SUM(cp.price) as total_price,
            COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_payment_amounts
        FROM contract_contractprice cp
        CROSS JOIN jsonb_each_text(cp.payment_amounts)
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
    """)

    result = cursor.fetchone()
    if result:
        total_price, total_payment_amounts = result
        print(f"  price 필드 합계: {total_price:,}")
        print(f"  payment_amounts 합계: {total_payment_amounts:,}")
        print(f"  차이: {total_price - total_payment_amounts:,}")

    # 근린생활시설이 올바른 order_group에 할당되고 있는지 확인
    print("\n근린생활시설의 order_group 할당 확인:")
    from project.models import Project
    from contract.models import OrderGroup

    project = Project.objects.get(pk=1)
    default_og = OrderGroup.get_default_for_project(project)

    print(f"기본 order_group: {default_og.name} (ID: {default_og.pk})")

    # API 함수 직접 테스트
    from apiV1.views.payment import PaymentStatusByUnitTypeViewSet

    non_contract_amount = PaymentStatusByUnitTypeViewSet._get_non_contract_amount_by_unit_type(
        1, default_og.pk, 4  # project_id=1, order_group_id=default_og.pk, unit_type_id=4
    )
    non_contract_units = PaymentStatusByUnitTypeViewSet._get_non_contract_units_by_unit_type(
        1, default_og.pk, 4
    )

    print(f"API 함수 직접 호출 결과:")
    print(f"  미계약 금액: {non_contract_amount:,}")
    print(f"  미계약 세대수: {non_contract_units}")