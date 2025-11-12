"""
연체료 계산 버그 수정 검증 스크립트

사용법:
    docker compose -f deploy/docker-compose.yml exec web python manage.py shell < scripts/test_penalty_calculation.py

또는 shell에서:
    exec(open('scripts/test_penalty_calculation.py').read())
"""

from datetime import date
from contract.models import Contract
from payment.models import InstallmentPaymentOrder
from cash.models import ProjectCashBook
from notice.exports.pdf import PdfExportBill
from payment.exports.pdf import PdfExportPayments

print("=" * 80)
print("연체료 계산 버그 수정 검증")
print("=" * 80)

# 1. 다중 납부 건이 있는 계약 찾기
print("\n1. 다중 납부 건이 있는 계약 찾기...")

# 회차별로 2건 이상 납부가 있는 계약 찾기
from django.db.models import Count

contracts_with_multiple_payments = ProjectCashBook.objects.payment_records().values(
    'contract_id', 'installment_order_id'
).annotate(
    payment_count=Count('id')
).filter(
    payment_count__gte=2
).order_by('-payment_count')

if not contracts_with_multiple_payments:
    print("⚠️  다중 납부 건이 있는 계약을 찾을 수 없습니다.")
    print("   단일 납부 건으로 테스트합니다 (결과가 동일해야 함).")

    # 연체료가 있는 계약 찾기
    test_contract = Contract.objects.filter(
        projectcashbook__isnull=False
    ).first()
else:
    # 가장 많은 납부 건이 있는 계약 선택
    first_multi = contracts_with_multiple_payments.first()
    test_contract = Contract.objects.get(id=first_multi['contract_id'])

    print(f"✅ 선택된 계약: ID={test_contract.id}")
    print(f"   회차별 납부 건수:")

    for item in contracts_with_multiple_payments.filter(contract_id=test_contract.id)[:5]:
        installment = InstallmentPaymentOrder.objects.get(id=item['installment_order_id'])
        print(f"   - {installment.pay_name}: {item['payment_count']}건")

if not test_contract:
    print("❌ 테스트할 계약을 찾을 수 없습니다.")
    exit()

# 2. 계약 정보 출력
print(f"\n2. 계약 정보:")
print(f"   프로젝트: {test_contract.project.name}")
print(f"   계약자: {test_contract.contractor}")
if hasattr(test_contract, 'contract_date'):
    print(f"   계약일: {test_contract.contract_date}")

# 3. 납부 내역 확인
print(f"\n3. 납부 내역:")
payments = ProjectCashBook.objects.payment_records().filter(
    contract=test_contract
).order_by('installment_order__pay_code', 'deal_date')

current_installment = None
for payment in payments[:20]:  # 최대 20건만 표시
    if payment.installment_order != current_installment:
        current_installment = payment.installment_order
        print(f"\n   [{current_installment.pay_name}] (납부기한: {current_installment.pay_due_date or '없음'})")

    print(f"      {payment.deal_date}: {payment.income:,}원")

if payments.count() > 20:
    print(f"\n   ... 외 {payments.count() - 20}건 더")

# 4. 연체료 계산 비교
print(f"\n4. 연체료 계산 비교:")
print("=" * 80)

pub_date = date.today()
payment_orders = InstallmentPaymentOrder.objects.filter(
    project=test_contract.project,
    type_sort=test_contract.unit_type.sort if test_contract.unit_type else 1
)

# 현재 도래 회차 계산
now_due_order = payment_orders.filter(
    pay_due_date__lte=pub_date
).aggregate(max_code=Count('pay_code'))['max_code'] or 1

try:
    # PdfExportBill (고지서)
    print("\n[A] PdfExportBill (고지서) 계산:")
    bill_result = PdfExportBill.calculate_late_fees_standardized(
        test_contract,
        payment_orders,
        now_due_order,
        pub_date
    )

    print(f"   총 연체료: {bill_result['total_late_fee']:,}원")
    print(f"   총 할인액: {bill_result['total_discount']:,}원")
    print(f"   연체료 발생 회차: {bill_result['penalty_count']}개")
    print(f"   할인 발생 회차: {bill_result['discount_count']}개")

    if bill_result['installment_details']:
        print(f"\n   회차별 상세:")
        for detail in bill_result['installment_details'][:5]:
            inst = detail['installment']
            print(f"      {inst.pay_name}:")
            print(f"         연체료: {detail['penalty_amount']:,}원")
            print(f"         할인: {detail['discount_amount']:,}원")
            if detail['late_days'] > 0:
                print(f"         지연일수: {detail['late_days']}일")
            if detail.get('prepay_days', 0) > 0:
                print(f"         선납일수: {detail['prepay_days']}일")

    bill_success = True
    bill_penalty = bill_result['total_late_fee']

except Exception as e:
    print(f"   ❌ 오류: {e}")
    bill_success = False
    bill_penalty = 0

try:
    # PdfExportPayments (납부확인서)
    print("\n[B] PdfExportPayments (납부확인서) 계산:")
    payments_result, paid_sum, (penalty, discount, _) = PdfExportPayments.get_paid_with_adjustment(
        test_contract,
        pub_date,
        is_calc=True
    )

    print(f"   총 연체료: {penalty:,}원")
    print(f"   총 할인액: {discount:,}원")
    print(f"   총 납부액: {paid_sum:,}원")

    payments_success = True
    payments_penalty = penalty

except Exception as e:
    print(f"   ❌ 오류: {e}")
    payments_success = False
    payments_penalty = 0

# 5. 결과 비교
print("\n5. 결과 검증:")
print("=" * 80)

if bill_success and payments_success:
    if bill_penalty == payments_penalty:
        print("✅ 두 클래스의 연체료 계산이 일치합니다!")
        print(f"   연체료: {bill_penalty:,}원")
    else:
        print("⚠️  두 클래스의 연체료 계산이 다릅니다:")
        print(f"   PdfExportBill: {bill_penalty:,}원")
        print(f"   PdfExportPayments: {payments_penalty:,}원")
        print(f"   차이: {abs(bill_penalty - payments_penalty):,}원")
else:
    print("❌ 계산 중 오류가 발생했습니다.")

# 6. 수정 내용 확인
print("\n6. 수정 내용 확인:")
print("=" * 80)

import inspect
from _utils.payment_adjustment import calculate_segmented_late_penalty

# PdfExportBill 소스 확인
bill_source = inspect.getsource(PdfExportBill.calculate_late_fees_standardized)
if 'calculate_segmented_late_penalty' in bill_source:
    print("✅ PdfExportBill이 calculate_segmented_late_penalty를 사용합니다")
else:
    print("❌ PdfExportBill이 아직 calculate_segmented_late_penalty를 사용하지 않습니다")

# PdfExportPayments 소스 확인
payments_source = inspect.getsource(PdfExportPayments.get_paid_with_adjustment)
if 'calculate_segmented_late_penalty' in payments_source:
    print("✅ PdfExportPayments가 calculate_segmented_late_penalty를 사용합니다")
else:
    print("❌ PdfExportPayments가 아직 calculate_segmented_late_penalty를 사용하지 않습니다")

print("\n" + "=" * 80)
print("검증 완료!")
print("=" * 80)
