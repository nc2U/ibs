from django.db import connection
from payment.models import InstallmentPaymentOrder
from items.models import UnitType

print("=== InstallmentPaymentOrder 데이터 확인 ===")

# 근린생활시설 UnitType 확인
try:
    facility_unit_type = UnitType.objects.get(pk=4, name='근린생활시설')
    print(f"근린생활시설 UnitType: {facility_unit_type.name} (ID: {facility_unit_type.pk}, sort: {facility_unit_type.sort})")
    print(f"프로젝트: {facility_unit_type.project}")
except UnitType.DoesNotExist:
    print("근린생활시설 UnitType을 찾을 수 없습니다.")
    exit()

# 근린생활시설의 InstallmentPaymentOrder 확인
print(f"\n근린생활시설의 InstallmentPaymentOrder (type_sort={facility_unit_type.sort}):")
installments = InstallmentPaymentOrder.objects.filter(
    project=facility_unit_type.project,
    type_sort=facility_unit_type.sort
).order_by('pay_code', 'pay_time')

if installments.exists():
    for installment in installments:
        print(f"  pay_code: {installment.pay_code}, pay_time: {installment.pay_time}")
        print(f"  pay_name: {installment.pay_name}")
        print(f"  pay_ratio: {installment.pay_ratio}")
        print(f"  extra_amount: {installment.extra_amount}")
        print()
else:
    print("  근린생활시설에 대한 InstallmentPaymentOrder가 없습니다!")

# 전체 InstallmentPaymentOrder 확인
print("\n전체 InstallmentPaymentOrder (프로젝트 ID=1):")
all_installments = InstallmentPaymentOrder.objects.filter(project_id=1).order_by('type_sort', 'pay_time')

for installment in all_installments:
    print(f"  type_sort: {installment.type_sort}, pay_time: {installment.pay_time}, pay_name: {installment.pay_name}")

# 근린생활시설 ContractPrice 재계산 테스트
print("\n근린생활시설 ContractPrice 재계산 테스트:")
from contract.models import ContractPrice

facility_contract_price = ContractPrice.objects.filter(
    house_unit__unit_type_id=4,
    contract_id__isnull=True,
    is_cache_valid=True
).first()

if facility_contract_price:
    print(f"ContractPrice ID: {facility_contract_price.id}")
    print(f"현재 payment_amounts: {facility_contract_price.payment_amounts}")
    print("재계산 실행...")

    # 재계산 실행
    facility_contract_price.calculate_uncontracted_payments()
    print(f"재계산 후 payment_amounts: {facility_contract_price.payment_amounts}")
    print(f"is_cache_valid: {facility_contract_price.is_cache_valid}")
else:
    print("근린생활시설 ContractPrice를 찾을 수 없습니다.")