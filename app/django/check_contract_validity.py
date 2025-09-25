from django.db import connection

print("=== 계약 유효성 상태 확인 ===")
with connection.cursor() as cursor:
    # 계약이 있는 경우의 상태 확인
    cursor.execute("""
        SELECT
            c.activation,
            c.contracted,
            COUNT(*) as count,
            SUM(cp.price) as total_price
        FROM contract_contractprice cp
        INNER JOIN contract_contract c ON cp.contract_id = c.id
        WHERE cp.is_cache_valid = true
        GROUP BY c.activation, c.contracted
        ORDER BY c.activation, c.contracted
    """)

    print("계약 있는 경우:")
    for row in cursor.fetchall():
        activation, contracted, count, total_price = row
        print(f"  activation={activation}, contracted={contracted}: {count}건, 총금액={total_price:,}")

    print("\n=== 현재 필터 조건별 비교 ===")

    # 현재 조건 (activation=true만)
    cursor.execute("""
        SELECT SUM(cp.price) as total
        FROM contract_contractprice cp
        INNER JOIN contract_contract c ON cp.contract_id = c.id
        WHERE c.activation = true
          AND cp.is_cache_valid = true
    """)
    result = cursor.fetchone()
    current_total = result[0] if result else 0
    print(f"activation=true만: {current_total:,}")

    # 더 엄격한 조건 (activation=true AND contracted=true)
    cursor.execute("""
        SELECT SUM(cp.price) as total
        FROM contract_contractprice cp
        INNER JOIN contract_contract c ON cp.contract_id = c.id
        WHERE c.activation = true
          AND c.contracted = true
          AND cp.is_cache_valid = true
    """)
    result = cursor.fetchone()
    strict_total = result[0] if result else 0
    print(f"activation=true AND contracted=true: {strict_total:,}")

    print(f"차이: {abs(current_total - strict_total):,}")

    print("\n=== ContractPrice 테이블의 price vs payment_amounts 일치성 확인 ===")

    # price 필드와 payment_amounts 합계가 다른 경우 찾기
    cursor.execute("""
        WITH payment_sums AS (
            SELECT
                cp.id,
                cp.price,
                COALESCE(SUM(CAST(value AS INTEGER)), 0) as payment_total
            FROM contract_contractprice cp
            CROSS JOIN jsonb_each_text(cp.payment_amounts)
            WHERE cp.is_cache_valid = true
            GROUP BY cp.id, cp.price
        )
        SELECT
            COUNT(*) as total_records,
            COUNT(CASE WHEN price != payment_total THEN 1 END) as mismatched_records,
            SUM(CASE WHEN price != payment_total THEN ABS(price - payment_total) END) as total_difference
        FROM payment_sums
    """)

    result = cursor.fetchone()
    total_records, mismatched, total_diff = result
    print(f"전체 레코드: {total_records}")
    print(f"price != payment_amounts 합계인 레코드: {mismatched}")
    print(f"총 차이 금액: {total_diff:,}" if total_diff else "총 차이 금액: 0")