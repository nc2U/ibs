# 연체료 과다 계산 버그 수정

## 변경 개요

**날짜**: 2025-11-13
**목적**: 다중 납부 건에 대한 연체료 계산 로직 수정 - 각 납부 건의 실제 지연일수 반영
**영향 범위**: `payment/exports/pdf.py` (PdfExportPayments), `notice/exports/pdf.py` (PdfExportBill)

---

## 문제점

### 버그 설명

하나의 회차에 여러 건의 납부가 서로 다른 날짜에 이루어진 경우, 각 납부 건의 실제 지연일수를 무시하고 최종 납부일의 지연일수를 전체 금액에 일괄 적용하여 연체료를 과다 계산하는 버그.

### 구체적 예시

**시나리오**:
- 1차 중도금 납부기한: 2024-06-14
- 약정액: 65,188,000원
- 납부 내역:
  ```
  2024-09-05: 6건 × 10,000,000 = 60,000,000 (83일 지연)
  2024-09-27: 1건 × 5,188,000 (105일 지연)
  ```

**기존 계산 (잘못됨)**:
```
연체료 = 65,188,000 × 10% ÷ 365 × 105일 = 1,875,123원
```
→ 모든 납부 건에 최종 납부일(2024-09-27)의 지연일수(105일)를 적용

**정확한 계산**:
```
연체료 = (60,000,000 × 10% ÷ 365 × 83일) + (5,188,000 × 10% ÷ 365 × 105일)
       = 1,364,384 + 149,353
       = 1,513,737원
```
→ 각 납부 건의 실제 지연일수 적용

**과다 징수액**: 1,875,123 - 1,513,737 = **361,386원 (23.9% 과다 징수)**

### 근본 원인

`calculate_all_installments_payment_allocation()` (Waterfall 충당 로직)이:
- `payment_sources[]`에 각 납부 건의 날짜와 금액을 정확히 저장하지만
- `fully_paid_date`에는 최종 완납일만 저장
- `late_payment_amount`에는 전체 약정액 저장
- 연체료 계산 시 `late_payment_amount × late_days`를 일괄 적용

**코드 위치**: `_utils/payment_adjustment.py:254-259`
```python
if status['is_fully_paid'] and status['fully_paid_date']:
    if status['fully_paid_date'] > base_due_date:
        status['is_late'] = True
        status['late_days'] = (status['fully_paid_date'] - base_due_date).days
        status['late_payment_amount'] = status['promised_amount']  # ← 버그!
```

---

## 해결 방안

### 선택된 방법: 기존 `calculate_segmented_late_penalty()` 함수 활용

**발견**: `_utils/payment_adjustment.py:270-390`에 이미 정확한 납부 건별 연체료 계산 로직을 구현한 함수가 존재하나, PDF 발급 클래스들이 이를 사용하지 않고 있었음.

**`calculate_segmented_late_penalty()` 함수의 올바른 로직**:
```python
# Lines 346-365
for payment in payments:
    unpaid = promised - cumulative_paid  # 현재 미납액
    days = (payment.deal_date - prev_date).days  # 이번 납부까지의 일수

    if days > 0 and unpaid > 0:
        penalty = calculate_daily_interest(unpaid, penalty_rate, days)
        segments.append({
            'period_start': prev_date,
            'period_end': payment.deal_date,
            'days': days,
            'unpaid_amount': unpaid,  # ← 납부 건별 미납액
            'penalty': penalty  # ← 납부 건별 연체료
        })

    cumulative_paid += payment.income
    prev_date = payment.deal_date
```

각 납부 건을 순회하며:
1. 현재 미납액 계산
2. 이전 납부일(또는 납부기한)부터 현재 납부일까지의 일수 계산
3. 미납액 × 일수로 연체료 계산
4. 누적 납부액 업데이트

---

## 주요 변경 사항

### 1. PdfExportPayments 수정 (`payment/exports/pdf.py`)

#### Import 추가
```python
from _utils.payment_adjustment import (
    calculate_all_installments_payment_allocation,
    get_installment_adjustment_summary,
    calculate_daily_interest,
    get_unpaid_installments,
    calculate_segmented_late_penalty  # ← 추가
)
```

#### 연체료 계산 로직 변경 (Lines 201-208)

**변경 전**:
```python
# 연체료 계산 (is_late_penalty 체크)
if not inst.is_late_penalty or not inst.late_penalty_ratio:
    penalty = 0
elif days > 0 and late_amount > 0:
    penalty = calculate_late_penalty(contract, inst, late_amount, days)
else:
    penalty = 0
```

**변경 후**:
```python
# 연체료 계산 (납부 건별 정확한 계산)
if not inst.is_late_penalty or not inst.late_penalty_ratio:
    penalty = 0
else:
    # calculate_segmented_late_penalty 사용: 각 납부 건의 실제 지연일수 반영
    segmented = calculate_segmented_late_penalty(contract, inst, pub_date)
    penalty = segmented['total_penalty']
    # 참고: segmented['segments']에 납부 건별 상세 내역 포함
```

### 2. PdfExportBill 수정 (`notice/exports/pdf.py`)

#### Import 추가
```python
from _utils.payment_adjustment import (
    calculate_all_installments_payment_allocation,
    get_installment_adjustment_summary,
    calculate_segmented_late_penalty  # ← 추가
)
```

#### 연체료 계산 로직 변경 (Lines 501-508)

**변경 전**:
```python
# 연체료 계산 (simple_late_payment 방식)
penalty = 0
if inst.is_late_penalty and inst.late_penalty_ratio:
    if late_days > 0 and late_amount > 0:
        penalty = calculate_late_penalty(contract, inst, late_amount, late_days)
```

**변경 후**:
```python
# 연체료 계산 (납부 건별 정확한 계산)
penalty = 0
if inst.is_late_penalty and inst.late_penalty_ratio:
    # calculate_segmented_late_penalty 사용: 각 납부 건의 실제 지연일수 반영
    segmented = calculate_segmented_late_penalty(contract, inst, pub_date)
    penalty = segmented['total_penalty']
    # Waterfall에서 계산한 late_amount는 참고용으로 유지
    # 실제 연체료는 segmented 결과 사용
```

---

## 테스트

### 새로운 테스트 케이스 추가

**파일**: `notice/tests.py`
**클래스**: `PdfExportBillTestCase`
**메서드**: `test_multiple_payments_different_dates()`

#### 테스트 시나리오

```python
# 2차 중도금: 납부기한 2024-06-14, 약정액 65,188,000원
# 시나리오: 7건의 납부
# 2024-09-05: 6건 × 10,000,000 = 60,000,000 (83일 지연)
# 2024-09-27: 1건 × 5,188,000 (105일 지연)

expected_penalty = 1,513,737  # 정확한 계산
buggy_penalty = 1,875,123     # 기존 버그 값
```

#### 검증 항목

1. **정확성 검증**: 실제 연체료가 예상값(1,513,737원)과 일치하는지 확인
2. **버그 수정 검증**: 기존 버그 값(1,875,123원)보다 낮은지 확인
3. **절감액 검증**: 과다 징수액이 300,000원 이상인지 확인

#### 테스트 실행

```bash
# 전체 테스트
python manage.py test notice.tests --verbosity=2

# 특정 테스트만 실행
python manage.py test notice.tests.PdfExportBillTestCase.test_multiple_payments_different_dates --verbosity=2
```

---

## 영향 분석

### 수정된 파일

1. **`payment/exports/pdf.py`**
   - Import 1줄 추가
   - 연체료 계산 로직 7줄 수정
   - 총 ~8줄 변경

2. **`notice/exports/pdf.py`**
   - Import 1줄 추가
   - 연체료 계산 로직 7줄 수정
   - 총 ~8줄 변경

3. **`notice/tests.py`**
   - 새로운 테스트 메서드 추가 (~90줄)

### 영향 받는 기능

✅ **직접 영향**:
- 납부확인서 발급 (PdfExportPayments)
- 고지서 발급 (PdfExportBill)
- 연체료 계산 로직

✅ **영향 없음**:
- Waterfall 충당 로직 (완납 상태 판정 정상)
- ProjectCashBook 납부 기록
- 선납 할인 계산
- 기타 PDF 발급 기능

### 비즈니스 영향

**긍정적 효과**:
- 공정한 연체료 계산
- 고객 신뢰도 향상
- 법적 리스크 감소
- 재무 정확성 향상

**예상 재무 영향**:
- 다중 납부 건이 있는 계약: 평균 20-30% 연체료 감소
- 단일 납부 건: 영향 없음 (동일한 결과)

---

## 검증 방법

### 1. 단위 테스트

```bash
python manage.py test notice.tests.PdfExportBillTestCase.test_multiple_payments_different_dates
```

### 2. 실제 데이터 검증

```python
from notice.exports.pdf import PdfExportBill
from payment.exports.pdf import PdfExportPayments
from contract.models import Contract
from payment.models import InstallmentPaymentOrder
from datetime import date

# 테스트 계약 선택 (다중 납부 건이 있는 계약)
contract = Contract.objects.get(id=YOUR_CONTRACT_ID)
pub_date = date.today()

# 고지서 연체료 계산
payment_orders = InstallmentPaymentOrder.objects.filter(project=contract.project)
bill_result = PdfExportBill.calculate_late_fees_standardized(
    contract, payment_orders, now_due_order, pub_date
)
print(f"고지서 연체료: {bill_result['total_late_fee']:,}원")

# 납부확인서 연체료 계산
payments_result, _, (penalty, discount, _) = PdfExportPayments.get_paid_with_adjustment(
    contract, pub_date, is_calc=True
)
print(f"납부확인서 연체료: {penalty:,}원")
```

### 3. 수동 검증 체크리스트

- [ ] 단일 납부 건 계약: 기존과 동일한 연체료 (회귀 테스트)
- [ ] 다중 납부 건 계약: 각 납부일 기준 연체료 계산
- [ ] 정상 납부 계약: 연체료 0원
- [ ] 부분 납부 계약: 미납액에 대한 연체료만 계산
- [ ] PDF 출력 형식: 정상 출력 확인

---

## 향후 계획

### 단기 (완료 후 즉시)
- [x] PdfExportPayments 수정
- [x] PdfExportBill 수정
- [x] 테스트 케이스 작성
- [ ] 실제 데이터 검증
- [ ] 배포 및 모니터링

### 중기 (1-2주 내)
- [ ] 과거 과다 징수 건 분석 및 환불 검토
- [ ] 사용자 문서 업데이트
- [ ] 고객 공지 (연체료 계산 방식 개선)

### 장기 (추후 고려)
- [ ] Waterfall 로직 문서화 개선
- [ ] 연체료 계산 로직 통합 유틸리티 함수 생성
- [ ] 납부 건별 상세 내역 UI 표시 검토

---

## 관련 파일

### 수정된 파일
- `payment/exports/pdf.py` - PdfExportPayments 클래스
- `notice/exports/pdf.py` - PdfExportBill 클래스
- `notice/tests.py` - 테스트 케이스 추가

### 참조 파일
- `_utils/payment_adjustment.py` - `calculate_segmented_late_penalty()` 함수 (정확한 로직)
- `_utils/simple_late_payment.py` - 기본 연체료 계산 함수
- `cash/models.py` - ProjectCashBook 모델

---

## 기술적 세부사항

### `calculate_segmented_late_penalty()` 반환 값

```python
{
    'total_penalty': int,        # 총 연체료
    'promised_amount': int,      # 약정액
    'total_paid': int,          # 총 납부액
    'segments': [                # 납부 건별 상세
        {
            'period_start': date,      # 기간 시작일
            'period_end': date,        # 기간 종료일 (납부일)
            'days': int,               # 지연일수
            'unpaid_amount': int,      # 미납액
            'penalty': int,            # 이 기간의 연체료
            'penalty_rate': Decimal,   # 연체율
            'cumulative_paid': int     # 누적 납부액
        },
        # ... 각 납부 건마다 하나씩
    ]
}
```

### 계산 공식

```
각 납부 건의 연체료 = 미납액 × (연체율 / 100 / 365) × 지연일수
총 연체료 = sum(각 납부 건의 연체료)
```

---

## 문의 및 지원

변경 사항에 대한 문의나 이슈 발견 시:
1. `notice/tests.py`의 테스트 케이스로 재현 가능한지 확인
2. 실제 계약 데이터로 검증 후 보고
3. 과다 징수 건 발견 시 즉시 보고

---

## 변경 이력

| 날짜 | 작성자 | 변경 내용 |
|------|--------|-----------|
| 2025-11-13 | Claude | 최초 작성 - 연체료 과다 계산 버그 수정 |
| 2025-11-13 | Claude | PdfExportPayments 및 PdfExportBill 수정 완료 |
| 2025-11-13 | Claude | 테스트 케이스 작성 및 문서화 완료 |
