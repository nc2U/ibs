from django.db import connection

# 근린생활시설 unit_type_id 확인
print("=== 근린생활시설 unit_type_id 확인 ===")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT id, name
        FROM items_unittype
        WHERE name LIKE '%근린%' OR name LIKE '%시설%'
    """)
    for row in cursor.fetchall():
        print(f"unit_type_id: {row[0]}, name: {row[1]}")

print("\n=== 미계약 가격 비교 (price vs payment_amounts) ===")
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

    price_results = {}
    for row in cursor.fetchall():
        unit_type_id, name, total_price = row
        price_results[unit_type_id] = {
            'name': name,
            'price_total': total_price
        }

    # payment_amounts JSON 필드 기준
    cursor.execute("""
        SELECT
            hu.unit_type_id,
            ut.name,
            COALESCE(SUM(CAST(value AS INTEGER)), 0) as total_payment_amounts
        FROM contract_contractprice cp,
             jsonb_each_text(cp.payment_amounts)
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        INNER JOIN items_unittype ut ON hu.unit_type_id = ut.id
        WHERE cp.contract_id IS NULL
          AND cp.is_cache_valid = true
        GROUP BY hu.unit_type_id, ut.name
        ORDER BY hu.unit_type_id
    """)

    payment_results = {}
    for row in cursor.fetchall():
        unit_type_id, name, total_payment_amounts = row
        payment_results[unit_type_id] = total_payment_amounts

    # 비교 결과
    all_unit_types = set(price_results.keys()) | set(payment_results.keys())
    for unit_type_id in sorted(all_unit_types):
        price_data = price_results.get(unit_type_id, {'name': 'Unknown', 'price_total': 0})
        payment_total = payment_results.get(unit_type_id, 0)

        name = price_data['name']
        price_total = price_data['price_total']

        diff = price_total - payment_total

        print(f"{name} (ID: {unit_type_id}):")
        print(f"  price 필드 합계: {price_total:,}")
        print(f"  payment_amounts 합계: {payment_total:,}")
        print(f"  차이: {diff:,}")
        print()