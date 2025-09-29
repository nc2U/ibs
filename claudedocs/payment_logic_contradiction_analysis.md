# 납부액 집계 논리적 모순 분석

## 🔍 문제 상황

제약조건이 많을수록 집계 금액이 작아져야 하는데, 가장 제약이 많은 **ExportPaymentStatus**가 **가장 높은 금액**을 보여주는 논리적 모순 발생.

## 📊 집계 결과 재확인

- **ExportPayments**: 147,501,051,740원 (제약 조건 가장 적음)
- **ExportPaymentsByCont**: 147,440,605,740원 (중간 제약 조건)
- **ExportPaymentStatus**: 147,768,757,740원 (제약 조건 가장 많음) ⚠️

## 🕵️ 가능한 원인 분석

### 1. **집계 대상 데이터 차이**

#### ExportPaymentStatus 특별 조건들:
```sql
-- 더 엄격한 조인 조건
INNER JOIN payment_installmentpaymentorder ipo ON pcb.installment_order_id = ipo.id
INNER JOIN contract_contract c ON pcb.contract_id = c.id

-- 추가 조건들
AND c.activation = true
AND c.order_group_id = %s
AND c.unit_type_id = %s
```

### 2. **중복 집계 가능성**

#### PaymentStatusByUnitTypeViewSet 구조:
- **차수별(order_group) × 타입별(unit_type)** 이중 반복문
- **각 조합마다** `_get_paid_amount_by_unit_type()` 호출
- **합계에서 중복 집계** 가능성

### 3. **데이터 조인 차이로 인한 확장**

#### ExportPaymentStatus만의 특징:
- `installment_order` 기준 조인으로 **데이터 확장** 가능
- 하나의 cash 레코드가 **여러 installment_order와 매칭**될 경우
- 계약이 **여러 installment_order를 가질 경우** 중복 계산

### 4. **집계 범위 차이**

#### ExportPaymentStatus 집계 방식:
```python
# 차수×타입별 개별 집계 후 합산
for order_group_id, unit_type_id in combinations:
    paid_amount = _get_paid_amount_by_unit_type(project_id, order_group_id, unit_type_id, date)
    total += paid_amount  # 여기서 중복 가능성
```

#### 다른 클래스들:
```python
# 전체 한번에 집계
total = ProjectCashBook.objects.filter(...).aggregate(Sum('income'))
```

### 5. **installment_order 조인 효과**

#### 중복 발생 시나리오:
1. **하나의 수납액**이 **여러 납부회차**와 연결 가능
2. **차수×타입 조합**에서 **동일 수납액이 여러 번** 집계
3. **날짜 범위 내 모든 installment_order**와 조인으로 **데이터 배율 증가**

## 🔬 검증 필요 사항

### 1. **중복 집계 확인**
```sql
-- 동일한 cash 레코드가 여러 번 집계되는지 확인
SELECT pcb.id, pcb.income, COUNT(*) as count_duplicates
FROM cash_projectcashbook pcb
INNER JOIN payment_installmentpaymentorder ipo ON pcb.installment_order_id = ipo.id
INNER JOIN contract_contract c ON pcb.contract_id = c.id
WHERE ipo.project_id = %s AND c.activation = true
GROUP BY pcb.id, pcb.income
HAVING COUNT(*) > 1
```

### 2. **installment_order 연결 확인**
```sql
-- 하나의 contract가 여러 installment_order를 가지는지
SELECT c.id, COUNT(DISTINCT ipo.id) as installment_count
FROM contract_contract c
INNER JOIN cash_projectcashbook pcb ON c.id = pcb.contract_id
INNER JOIN payment_installmentpaymentorder ipo ON pcb.installment_order_id = ipo.id
WHERE c.project_id = %s
GROUP BY c.id
HAVING COUNT(DISTINCT ipo.id) > 1
```

### 3. **차수×타입 조합별 집계 검증**
```python
# 각 차수×타입별 집계 합계 vs 전체 집계 비교
sum_by_combinations = sum(각 조합별 집계)
total_direct = ProjectCashBook.objects.filter(...).aggregate(Sum('income'))
print(f"조합별 합계: {sum_by_combinations}")
print(f"직접 집계: {total_direct}")
```

## 🎯 추정 결론

**가장 가능성 높은 원인**:

**ExportPaymentStatus**의 **차수×타입별 이중 반복문 구조**에서 **동일한 수납액이 여러 번 집계**되고 있을 가능성이 높습니다.

특히 `installment_order` 조인으로 인해 **하나의 수납 레코드가 여러 납부회차와 연결**되어 **배율 효과**가 발생하는 것으로 추정됩니다.

## 🛠️ 해결 방안

1. **DISTINCT 적용**: 중복 제거 쿼리로 수정
2. **집계 방식 통일**: 다른 클래스와 동일한 방식으로 변경
3. **데이터 검증**: 실제 중복 발생 여부 확인 후 수정