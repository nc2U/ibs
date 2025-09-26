from django.db import connection

print("=== SQL 쿼리 직접 테스트 ===")

with connection.cursor() as cursor:
    # 간단한 근린생활시설 데이터 확인
    cursor.execute("""
        SELECT
            cp.id,
            cp.price,
            cp.payment_amounts,
            (cp.payment_amounts = '{}'::jsonb) as is_empty_json,
            (cp.payment_amounts IS NULL) as is_null
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE hu.unit_type_id = 4
          AND cp.is_cache_valid = true
        LIMIT 3
    """)

    print("근린생활시설 데이터:")
    for row in cursor.fetchall():
        cp_id, price, payment_amounts, is_empty, is_null = row
        print(f"  ID: {cp_id}, price: {price:,}, payment_amounts: {payment_amounts}")
        print(f"    is_empty_json: {is_empty}, is_null: {is_null}")

    # 더 간단한 CASE 문으로 테스트
    print("\n간단한 CASE 문 테스트:")
    cursor.execute("""
        SELECT
            COUNT(*) as count,
            SUM(CASE
                WHEN cp.payment_amounts = '{}'::jsonb OR cp.payment_amounts IS NULL THEN cp.price
                ELSE 0
            END) as price_sum
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE cp.contract_id IS NULL
          AND hu.unit_type_id = 4
          AND cp.is_cache_valid = true
    """)

    result = cursor.fetchone()
    count, price_sum = result
    print(f"  미계약 근린생활시설 개수: {count}")
    print(f"  price 기준 총합: {price_sum:,}")