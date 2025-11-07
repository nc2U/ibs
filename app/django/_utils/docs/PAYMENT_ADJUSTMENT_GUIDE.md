# 선납 할인 및 연체 가산금 계산 시스템 사용 가이드

## 개요

이 시스템은 계약별/회차별 납부 내역을 기반으로 선납 할인 및 연체 가산금을 자동 계산합니다.

### 핵심 규칙
- **완납 여부**: 약정금액 ≤ 실제 납부금액 합계 (`get_payment_amount()` 사용)
- **선납 할인**: 완납 시점 기준 일괄 계산
- **연체 가산금**: 각 납부건별 연체일수로 개별 계산

### 계정 구조
- **유효 계약자 납부** (is_payment=True): 111 (분담금), 811 (분양매출금) - **할인/가산 대상**
- **기타 모든 계정** (is_payment=False): 유효 계약자 입금을 제외한 모든 계정
  - 예: 해지 계약자 입금 (112, 812), 환불 출금 (113, 114, 813, 814), 기타 60여개 출금 계정

---

## 구현 구조

### 1. Utility 함수 (`_utils/payment_adjustment.py`)
핵심 계산 로직을 담당하는 순수 함수들

### 2. Manager/QuerySet (`cash/models.py`)
Django ORM을 활용한 효율적인 데이터 조회

---

## 사용 예시

### 예시 1: 특정 계약의 회차별 선납 할인 조회

```python
from contract.models import Contract
from payment.models import InstallmentPaymentOrder
from _utils.payment_adjustment import get_installment_adjustment_summary

# 계약 조회
contract = Contract.objects.get(pk=1)

# 해당 계약의 모든 회차 조회
installments = InstallmentPaymentOrder.objects.filter(
    project=contract.project,
    type_sort=contract.unit_type.sort
).order_by('pay_code', 'pay_time')

# 각 회차별 선납 할인 및 연체 가산금 확인
for installment in installments:
    summary = get_installment_adjustment_summary(contract, installment)

    print(f"\n회차: {summary['installment_order'].pay_name}")
    print(f"약정금액: {summary['promised_amount']:,}원")
    print(f"납부금액: {summary['paid_amount']:,}원")
    print(f"완납여부: {'완납' if summary['is_fully_paid'] else '미납'}")

    if summary['prepayment_discount']:
        discount = summary['prepayment_discount']
        print(f"✅ 선납 할인: {discount['discount_amount']:,}원")
        print(f"   - 선납일수: {discount['discount_days']}일")
        print(f"   - 할인율: {discount['discount_rate']}%")
        print(f"   - 완납일: {discount['fully_paid_date']}")

    if summary['late_penalties']:
        print(f"⚠️ 연체 가산금 총액: {summary['total_penalty']:,}원")
        for penalty in summary['late_penalties']:
            print(f"   - 납부일: {penalty['payment_date']}, "
                  f"연체일수: {penalty['late_days']}일, "
                  f"가산금: {penalty['penalty_amount']:,}원")

    print(f"순 조정금액: {summary['net_adjustment']:,}원 (할인 - 가산금)")
```

**출력 예시:**
```
회차: 계약금 1회
약정금액: 10,000,000원
납부금액: 10,000,000원
완납여부: 완납
✅ 선납 할인: 24,657원
   - 선납일수: 30일
   - 할인율: 3.0%
   - 완납일: 2025-12-01
순 조정금액: 24,657원 (할인 - 가산금)

회차: 중도금 1회
약정금액: 30,000,000원
납부금액: 30,000,000원
완납여부: 완납
⚠️ 연체 가산금 총액: 82,191원
   - 납부일: 2026-02-15, 연체일수: 15일, 가산금: 41,095원
   - 납부일: 2026-02-28, 연체일수: 28일, 가산금: 41,096원
순 조정금액: -82,191원 (할인 - 가산금)
```

---

### 예시 2: 계약별 전체 조정 금액 조회

```python
from _utils.payment_adjustment import get_contract_adjustment_summary

# 특정 계약의 전체 회차 조정 금액 조회
contract = Contract.objects.get(pk=1)
contract_summary = get_contract_adjustment_summary(contract)

print(f"계약번호: {contract_summary['contract'].serial_number}")
print(f"총 약정금액: {contract_summary['total_promised_amount']:,}원")
print(f"총 납부금액: {contract_summary['total_paid_amount']:,}원")
print(f"총 선납 할인: {contract_summary['total_discount']:,}원")
print(f"총 연체 가산: {contract_summary['total_penalty']:,}원")
print(f"순 조정금액: {contract_summary['net_adjustment']:,}원")
print(f"완납 회차: {contract_summary['fully_paid_count']}/{contract_summary['total_installment_count']}회")
```

**출력 예시:**
```
계약번호: IBS-2025-001
총 약정금액: 500,000,000원
총 납부금액: 450,000,000원
총 선납 할인: 123,287원
총 연체 가산: 246,575원
순 조정금액: -123,288원
완납 회차: 3/5회
```

---

### 예시 3: Manager를 통한 납부내역 조회

```python
from cash.models import ProjectCashBook

# 특정 계약의 유효 납부내역 조회 (is_payment=True)
contract = Contract.objects.get(pk=1)
payments = ProjectCashBook.objects.payment_records().for_contract(contract)

print(f"총 납부 건수: {payments.count()}건")

# 연체 가산 대상 납부건만 조회
late_payments = payments.with_penalty_eligible()

print(f"\n연체 가산 대상 납부 건수: {late_payments.count()}건")

for payment in late_payments:
    penalty_info = payment.get_late_penalty()

    if penalty_info:
        print(f"\n납부일: {payment.deal_date}")
        print(f"납부금액: {payment.income:,}원")
        print(f"연체일수: {penalty_info['late_days']}일")
        print(f"연체가산금: {penalty_info['penalty_amount']:,}원")
```

**출력 예시:**
```
총 납부 건수: 15건

연체 가산 대상 납부 건수: 3건

납부일: 2026-02-15
납부금액: 15,000,000원
연체일수: 15일
연체가산금: 41,095원

납부일: 2026-02-28
납부금액: 15,000,000원
연체일수: 28일
연체가산금: 41,096원
```

---

### 예시 4: QuerySet 메서드 체인

```python
# 특정 프로젝트의 선납 할인 대상 납부내역 조회
from project.models import Project

project = Project.objects.get(pk=1)

discount_eligible_payments = (
    ProjectCashBook.objects
    .payment_records()  # 유효 계약자 납부내역 (is_payment=True, 이미 입금만 포함)
    .filter(project=project)  # 특정 프로젝트
    .with_discount_eligible()  # 선납 할인 대상만
    .order_by('-deal_date')  # 최신순
)

print(f"선납 할인 대상 납부 건수: {discount_eligible_payments.count()}건")
```

---

### 예시 5: 개별 납부건 조정 정보 조회

```python
# 특정 납부건의 연체 가산금 확인
payment = ProjectCashBook.objects.get(pk=100)

# 연체 가산 대상인지 확인
if payment.is_penalty_eligible():
    penalty_info = payment.get_late_penalty()

    if penalty_info:
        print(f"연체 가산금: {penalty_info['penalty_amount']:,}원")
        print(f"연체 일수: {penalty_info['late_days']}일")
        print(f"가산율: {penalty_info['penalty_rate']}%")
    else:
        print("납부일이 약정일 이내입니다. (연체 없음)")
else:
    print("이 납부건은 연체 가산 대상이 아닙니다.")

# 선납 할인 대상인지 확인
if payment.is_discount_eligible():
    print("이 납부건은 선납 할인 대상 회차입니다.")
```

---

### 예시 6: 특정 회차의 완납 여부 확인

```python
from _utils.payment_adjustment import calculate_installment_paid_status

# 특정 회차의 완납 상태 확인
contract = Contract.objects.get(pk=1)
installment = InstallmentPaymentOrder.objects.get(pk=10)

paid_status = calculate_installment_paid_status(contract, installment)

print(f"회차: {installment.pay_name}")
print(f"약정금액: {paid_status['promised_amount']:,}원")
print(f"납부금액: {paid_status['paid_amount']:,}원")
print(f"미납금액: {paid_status['remaining_amount']:,}원")
print(f"납부횟수: {paid_status['payment_count']}회")
print(f"완납여부: {'완납' if paid_status['is_fully_paid'] else '미납'}")

if paid_status['fully_paid_date']:
    print(f"완납일: {paid_status['fully_paid_date']}")
```

---

## API 엔드포인트 예시 (선택사항)

Django REST Framework를 사용하는 경우:

```python
# apiV1/views/payment_adjustment.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from _utils.payment_adjustment import (
    get_installment_adjustment_summary,
    get_contract_adjustment_summary
)

@api_view(['GET'])
def contract_adjustment_detail(request, contract_id):
    """계약별 선납 할인 및 연체 가산금 조회"""
    try:
        contract = Contract.objects.get(pk=contract_id)
        summary = get_contract_adjustment_summary(contract)

        return Response({
            'contract_id': contract.id,
            'serial_number': contract.serial_number,
            'total_promised_amount': summary['total_promised_amount'],
            'total_paid_amount': summary['total_paid_amount'],
            'total_discount': summary['total_discount'],
            'total_penalty': summary['total_penalty'],
            'net_adjustment': summary['net_adjustment'],
            'installments': [
                {
                    'pay_name': inst['installment_order'].pay_name,
                    'promised_amount': inst['promised_amount'],
                    'paid_amount': inst['paid_amount'],
                    'total_discount': inst['total_discount'],
                    'total_penalty': inst['total_penalty']
                }
                for inst in summary['installments']
            ]
        })
    except Contract.DoesNotExist:
        return Response({'error': 'Contract not found'}, status=404)
```

---

## 주요 함수 설명

### 1. `calculate_installment_paid_status(contract, installment_order, payments_qs=None)`
회차별 완납 여부 및 완납일 계산

**반환값:**
- `is_fully_paid`: 완납 여부 (bool)
- `paid_amount`: 실제 납부금액 합계 (int)
- `promised_amount`: 약정금액 (int)
- `fully_paid_date`: 완납일 (date or None)
- `remaining_amount`: 미납금액 (int)
- `payment_count`: 납부 횟수 (int)

---

### 2. `calculate_prepayment_discount(contract, installment_order, payments_qs=None)`
선납 할인 계산 (완납 시점 기준 일괄)

**조건:**
- `installment_order.is_prep_discount = True`
- 완납 여부 확인
- 완납일 < 약정일

**계산식:**
`(약정일 - 완납일) × (할인율/365) × 약정금액`

**반환값:**
- `discount_amount`: 할인 금액 (int)
- `discount_days`: 선납 일수 (int)
- `discount_rate`: 할인율 (Decimal)
- `base_amount`: 기준 금액 (int)
- `fully_paid_date`: 완납일 (date)
- `due_date`: 약정일 (date)

---

### 3. `calculate_late_penalty(payment)`
개별 납부건의 연체 가산금 계산

**조건:**
- `installment_order.is_late_penalty = True`
- 납부일 > 약정일

**계산식:**
`(납부일 - 약정일) × (가산율/365) × 납부금액`

**반환값:**
- `penalty_amount`: 가산 금액 (int)
- `late_days`: 연체 일수 (int)
- `penalty_rate`: 가산율 (Decimal)
- `payment_amount`: 납부 금액 (int)
- `payment_date`: 납부일 (date)
- `due_date`: 약정일 (date)

---

### 4. `get_installment_adjustment_summary(contract, installment_order)`
회차별 선납 할인 및 연체 가산금 종합 정보

**반환값:**
- `installment_order`: InstallmentPaymentOrder
- `promised_amount`: 약정금액
- `paid_amount`: 실제 납부금액
- `is_fully_paid`: 완납 여부
- `fully_paid_date`: 완납일
- `prepayment_discount`: 선납 할인 정보 (dict or None)
- `late_penalties`: 각 납부건별 연체 정보 (list)
- `total_discount`: 총 할인 금액
- `total_penalty`: 총 가산 금액
- `net_adjustment`: 순 조정 금액 (할인 - 가산금)

---

### 5. `get_contract_adjustment_summary(contract)`
계약별 전체 회차의 선납 할인 및 연체 가산금 종합 정보

**반환값:**
- `contract`: Contract
- `installments`: 각 회차별 조정 정보 (list)
- `total_promised_amount`: 총 약정금액
- `total_paid_amount`: 총 납부금액
- `total_discount`: 총 할인 금액
- `total_penalty`: 총 가산 금액
- `net_adjustment`: 순 조정 금액
- `fully_paid_count`: 완납 회차 수
- `total_installment_count`: 전체 회차 수

---

## Manager/QuerySet 메서드

### QuerySet 메서드 (체이닝 가능)

#### `payment_records()`
**유효 계약자의 납부내역 (선납 할인 및 연체 가산금 계산 대상)**
- is_payment=True 필터링
- 계정: 111 (분담금), 811 (분양매출금)
- 이미 입금만 포함 (추가 income 필터 불필요)
- select_related로 관련 정보 자동 조회 (N+1 쿼리 방지)

#### `for_contract(contract)`
특정 계약의 전체 내역 필터

#### `for_installment(installment_order)`
특정 회차의 전체 내역 필터

#### `with_discount_eligible()`
선납 할인 대상 회차 필터 (is_prep_discount=True)

#### `with_penalty_eligible()`
연체 가산 대상 회차 필터 (is_late_penalty=True)

---

### Manager 메서드 (편의 메서드)

#### `ProjectCashBook.objects.payment_records()`
유효 계약자 납부내역 조회 (선납 할인 및 연체 가산금 계산 대상)

#### `ProjectCashBook.objects.for_contract(contract)`
특정 계약의 전체 내역

#### `ProjectCashBook.objects.for_installment(installment_order)`
특정 회차의 전체 내역

---

## 인스턴스 메서드

### `payment.get_late_penalty()`
개별 납부건의 연체 가산금 조회

### `payment.is_discount_eligible()`
선납 할인 대상 여부 (회차 기준)

### `payment.is_penalty_eligible()`
연체 가산 대상 여부 (회차 기준)

---

## 성능 최적화 팁

### 1. 쿼리 최적화
```python
# ❌ N+1 문제 발생
for payment in ProjectCashBook.objects.filter(contract=contract):
    penalty = payment.get_late_penalty()

# ✅ select_related로 최적화
payments = ProjectCashBook.objects.payment_records().for_contract(contract)
for payment in payments:
    penalty = payment.get_late_penalty()
```

### 2. 대량 조회 시
```python
# 여러 계약의 조정 정보 조회
contracts = Contract.objects.filter(project=project).select_related(
    'project', 'unit_type', 'order_group'
)

for contract in contracts:
    summary = get_contract_adjustment_summary(contract)
    # ... 처리
```

---

## 주의사항

1. **약정금액 계산**: `_utils.contract_price.get_payment_amount()` 함수 사용
2. **OverDueRule 모델**: 폐기 예정이므로 사용하지 않음
3. **계정 구조**:
   - `is_payment=True`: 유효 계약자 입금만 (111, 811) - **할인/가산 대상**
   - `is_payment=False`: 유효 계약자 입금을 제외한 모든 계정 (해지 입금, 환불 출금, 기타 출금 등 60여개)
4. **날짜 기준**:
   - 선납 기준일: `prep_ref_date` 우선, 없으면 `pay_due_date`
   - 연체 기준일: `extra_due_date` 우선, 없으면 `pay_due_date`
5. **완납 판단**: 약정금액 ≤ 실제 납부금액 합계
6. **선납 할인**: 완납 시점 기준 일괄 계산
7. **연체 가산**: 각 납부건별 연체일수로 개별 계산

---

## 문제 해결

### Q1: 선납 할인이 계산되지 않아요
- `installment_order.is_prep_discount = True` 확인
- `installment_order.prep_discount_ratio` 값 확인
- 완납 여부 확인 (`is_fully_paid = True`)
- 완납일 < 약정일 확인

### Q2: 연체 가산금이 계산되지 않아요
- `installment_order.is_late_penalty = True` 확인
- `installment_order.late_penalty_ratio` 값 확인
- 납부일 > 약정일 확인

### Q3: 완납일이 None으로 나와요
- 실제 납부금액이 약정금액 이상인지 확인
- `project_account_d3.is_payment = True`인 납부내역만 집계됨 (111, 811 계정만)
- is_payment=False인 모든 계정 (해지 입금, 환불, 기타 출금 등)은 집계에서 제외됨
- `income` 필드 값 확인

---

## 추가 자료

- 계산 로직 소스: `_utils/payment_adjustment.py`
- 모델 정의: `cash/models.py` (ProjectCashBook)
- 약정금액 계산: `_utils/contract_price.py`
