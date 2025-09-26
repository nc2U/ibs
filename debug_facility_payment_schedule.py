from django.db import connection

print("=== 근린생활시설 납부회차 데이터 분석 ===")

with connection.cursor() as cursor:
    # 근린생활시설 ContractPrice의 payment_amounts 현황 확인
    cursor.execute("""
        SELECT
            cp.id,
            cp.contract_id,
            cp.house_unit_id,
            cp.price,
            cp.payment_amounts,
            hu.name as house_unit_name
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE hu.unit_type_id = 4
          AND cp.is_cache_valid = true
        ORDER BY cp.id
        LIMIT 10
    """)

    print("근린생활시설 ContractPrice 데이터:")
    for row in cursor.fetchall():
        cp_id, contract_id, house_unit_id, price, payment_amounts, house_unit_name = row
        print(f"  ID: {cp_id}")
        print(f"    contract_id: {contract_id}")
        print(f"    house_unit: {house_unit_name} (ID: {house_unit_id})")
        print(f"    price: {price:,}")
        print(f"    payment_amounts: {payment_amounts}")
        print(f"    payment_amounts empty? {payment_amounts == {} or payment_amounts is None}")
        print()

    # 기본 납부회차 계산 예시
    print("\n=== 기본 납부회차 적용 예시 ===")
    cursor.execute("""
        SELECT
            cp.id,
            cp.price,
            cp.payment_amounts
        FROM contract_contractprice cp
        INNER JOIN items_houseunit hu ON cp.house_unit_id = hu.id
        WHERE hu.unit_type_id = 4
          AND cp.is_cache_valid = true
        LIMIT 3
    """)

    for row in cursor.fetchall():
        cp_id, price, payment_amounts = row
        print(f"ContractPrice ID: {cp_id}, Price: {price:,}")

        if payment_amounts == {} or payment_amounts is None:
            # 기본 납부회차 적용: 계약시 10%, 2차계약금 10%, 잔금 80%
            contract_payment = int(price * 0.1)  # 계약시 10%
            second_payment = int(price * 0.1)    # 2차계약금 10%
            final_payment = price - contract_payment - second_payment  # 잔금 80%

            default_schedule = {
                "계약시": contract_payment,
                "2차계약금": second_payment,
                "잔금": final_payment
            }

            print(f"  현재 payment_amounts: {payment_amounts}")
            print(f"  기본 납부회차 적용:")
            print(f"    계약시 (10%): {contract_payment:,}")
            print(f"    2차계약금 (10%): {second_payment:,}")
            print(f"    잔금 (80%): {final_payment:,}")
            print(f"    합계: {sum(default_schedule.values()):,}")
            print(f"  제안된 payment_amounts: {default_schedule}")
        else:
            print(f"  기존 payment_amounts 사용: {payment_amounts}")
        print()