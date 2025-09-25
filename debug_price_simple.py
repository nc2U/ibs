from django.db import connection

print("=== 미계약 가격 비교 (price vs payment_amounts) ===")
with connection.cursor() as cursor:
    # price 필드 기준
    cursor.execute("""
        SELECT
            hu.unit_type_id,
            ut.name,
            COALESCE(SUM(cp.price), 0) as total_price
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        INNER JOIN items_unittype ut ON hu.unit_type_id = ut.id
        WHERE cp.contract_id IS NULL
          AND cp.is_cache_valid = true
        GROUP BY hu.unit_type_id, ut.name
        ORDER BY hu.unit_type_id
    """)

    print("price 필드 기준:")
    for row in cursor.fetchall():
        unit_type_id, name, total_price = row
        print(f"  {name} (ID: {unit_type_id}): {total_price:,}")

    print("\npayment_amounts 필드 기준:")
    # payment_amounts JSON 필드 기준
    cursor.execute("""
        SELECT
            hu.unit_type_id,
            ut.name,
            COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_payment_amounts
        FROM contract_contractprice cp
        CROSS JOIN jsonb_each_text(cp.payment_amounts)
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        INNER JOIN items_unittype ut ON hu.unit_type_id = ut.id
        WHERE cp.contract_id IS NULL
          AND cp.is_cache_valid = true
        GROUP BY hu.unit_type_id, ut.name
        ORDER BY hu.unit_type_id
    """)

    for row in cursor.fetchall():
        unit_type_id, name, total_payment_amounts = row
        print(f"  {name} (ID: {unit_type_id}): {total_payment_amounts:,}")