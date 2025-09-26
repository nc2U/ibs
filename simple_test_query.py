from django.db import connection

print("=== 서브쿼리 테스트 ===")

with connection.cursor() as cursor:
    # 서브쿼리 없이 간단하게 테스트
    cursor.execute("""
        SELECT
            COALESCE(SUM(cp.price), 0) as total_price
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
    """)

    result = cursor.fetchone()
    print(f"간단한 price 합계: {result[0]:,}")

    # payment_amounts가 있는 데이터가 있는지 확인
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
          AND cp.payment_amounts != '{}'::jsonb
          AND cp.payment_amounts IS NOT NULL
    """)

    result = cursor.fetchone()
    print(f"payment_amounts가 있는 근린생활시설 수: {result[0]}")

    # 서브쿼리를 간소화해서 테스트
    cursor.execute("""
        SELECT
            SUM(
                CASE
                    WHEN cp.payment_amounts = '{}'::jsonb OR cp.payment_amounts IS NULL THEN cp.price
                    ELSE 0  -- 일단 서브쿼리 없이 0으로 설정
                END
            ) as total_amount
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
    """)

    result = cursor.fetchone()
    print(f"CASE 문 테스트 (서브쿼리 없음): {result[0]:,}")