from contract.models import ContractPrice

print("=== 근린생활시설 payment_amounts 업데이트 ===")

# 근린생활시설의 빈 payment_amounts를 가진 ContractPrice 조회
facility_contract_prices = ContractPrice.objects.filter(
    house_unit__unit_type__name='근린생활시설',
    payment_amounts={},  # 빈 JSON
    is_cache_valid=True
)

print(f"업데이트할 근린생활시설 ContractPrice 개수: {facility_contract_prices.count()}")

updated_count = 0
for cp in facility_contract_prices:
    print(f"\nContractPrice ID: {cp.id}, price: {cp.price:,}")
    print(f"이전 payment_amounts: {cp.payment_amounts}")

    # calculate_uncontracted_payments 재실행 (수정된 로직 적용)
    cp.calculate_uncontracted_payments()
    cp.save()

    print(f"이후 payment_amounts: {cp.payment_amounts}")

    # 금액 검증
    total_payment = sum(cp.payment_amounts.values())
    print(f"합계 검증: {total_payment:,} = {cp.price:,} ? {total_payment == cp.price}")

    updated_count += 1

print(f"\n총 {updated_count}개 ContractPrice가 업데이트되었습니다.")

# 최종 검증
print("\n=== 최종 검증 ===")
facility_with_payments = ContractPrice.objects.filter(
    house_unit__unit_type__name='근린생활시설',
    is_cache_valid=True
).exclude(payment_amounts={})

print(f"payment_amounts가 설정된 근린생활시설 ContractPrice: {facility_with_payments.count()}")

# 샘플 확인
for cp in facility_with_payments[:3]:
    print(f"  ID: {cp.id}, payment_amounts: {cp.payment_amounts}")
    total = sum(cp.payment_amounts.values())
    print(f"    합계: {total:,}, price: {cp.price:,}, 일치: {total == cp.price}")