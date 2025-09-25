from django.db import connection

print("=== 계약 유효성 상태 확인 ===")
with connection.cursor() as cursor:
    # 계약이 있는 경우의 상태 확인
    cursor.execute("""
        SELECT
            c.activation,
            COUNT(*) as count,
            SUM(cp.price) as total_price
        FROM contract_contractprice cp
        INNER JOIN contract_contract c ON cp.contract_id = c.id
        WHERE cp.is_cache_valid = true
        GROUP BY c.activation
        ORDER BY c.activation
    """)

    print("계약 있는 경우:")
    for row in cursor.fetchall():
        activation, count, total_price = row
        print(f"  activation={activation}: {count}건, 총금액={total_price:,}")

    print("\n=== ContractPrice price vs payment_amounts 차이 확인 ===")

    # price와 payment_amounts가 다른 레코드들 찾기
    cursor.execute("""
        WITH payment_sums AS (
            SELECT
                cp.id,
                cp.contract_id,
                cp.price,
                COALESCE(SUM(CAST(value AS INTEGER)), 0) as payment_total
            FROM contract_contractprice cp
            CROSS JOIN jsonb_each_text(cp.payment_amounts)
            WHERE cp.is_cache_valid = true
            GROUP BY cp.id, cp.contract_id, cp.price
        )
        SELECT
            CASE WHEN contract_id IS NULL THEN '미계약' ELSE '계약' END as contract_type,
            COUNT(*) as total_records,
            COUNT(CASE WHEN price != payment_total THEN 1 END) as mismatched_records,
            COALESCE(SUM(CASE WHEN price != payment_total THEN ABS(price - payment_total) END), 0) as total_difference
        FROM payment_sums
        GROUP BY CASE WHEN contract_id IS NULL THEN '미계약' ELSE '계약' END
        ORDER BY contract_type
    """)

    for row in cursor.fetchall():
        contract_type, total_records, mismatched, total_diff = row
        print(f"{contract_type}:")
        print(f"  전체 레코드: {total_records}")
        print(f"  price != payment_amounts인 레코드: {mismatched}")
        print(f"  총 차이 금액: {total_diff:,}")
        print()

    print("=== 미계약 세대 세부 분석 ===")
    cursor.execute("""
        WITH payment_sums AS (
            SELECT
                cp.id,
                hu.unit_type_id,
                ut.name,
                cp.price,
                COALESCE(SUM(CAST(value AS INTEGER)), 0) as payment_total
            FROM contract_contractprice cp
            CROSS JOIN jsonb_each_text(cp.payment_amounts)
            INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
            INNER JOIN items_unittype ut ON hu.unit_type_id = ut.id
            WHERE cp.contract_id IS NULL
              AND cp.is_cache_valid = true
            GROUP BY cp.id, hu.unit_type_id, ut.name, cp.price
        )
        SELECT
            name,
            SUM(price) as total_price,
            SUM(payment_total) as total_payment,
            SUM(price) - SUM(payment_total) as difference
        FROM payment_sums
        GROUP BY unit_type_id, name
        ORDER BY unit_type_id
    """)

    for row in cursor.fetchall():
        name, total_price, total_payment, difference = row
        print(f"{name}:")
        print(f"  price 합계: {total_price:,}")
        print(f"  payment_amounts 합계: {total_payment:,}")
        print(f"  차이: {difference:,}")
        print()