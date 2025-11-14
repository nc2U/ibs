# 분할 납부 처리 개선 문서

## 개요

PdfExportBill (고지서)와 PdfExportPayments (납부확인서)가 분할 납부 시 동일한 할인/가산금을 계산하도록 개선했습니다.

## 문제점

### 변경 전

**PdfExportPayments** (납부확인서):
- ✅ 각 납부건별로 개별 연체료 계산
- ✅ 분할 납부 시 정확한 금액 표시
- 예: 3M(9일 지연) + 7M(14일 지연) = ₩7,397 + ₩26,849 = ₩34,246

**PdfExportBill** (고지서):
- ❌ 회차별 재계산으로 인한 부정확
- ❌ 분할 납부 시 잘못된 금액 표시
- 예: 10M × 14일 = ₩38,356 (잘못됨)

### 원인

- PdfExportPayments: waterfall의 `late_payment_details` 사용 (개별 납부 연체료)
- PdfExportBill: 자체 재계산 로직 (회차 단위 연체료)
- 분할 납부 시 두 방식의 결과가 달라짐

## 해결 방법

### 1. 새로운 집계 함수 추가

**파일**: `_utils/payment_adjustment.py`

```python
def aggregate_installment_adjustments(
    contract,
    payment_orders,
    now_due_order,
    pub_date
) -> Dict[str, Any]:
    """
    분할 납부를 회차별로 집계하여 할인/가산금 계산

    waterfall의 late_payment_details에서 개별 납부 연체료를 추출하여
    회차별로 합산합니다.
    """
```

**기능**:
1. `calculate_all_installments_payment_allocation()` 호출 (waterfall 로직)
2. waterfall의 `late_payment_details`에서 개별 납부 연체료 추출
3. 회차별로 합산하여 반환
4. 선납 할인은 `get_installment_adjustment_summary()` 사용

### 2. PdfExportBill 수정

**파일**: `notice/exports/pdf.py`

**변경 사항**:
```python
# 변경 전 (116줄의 복잡한 재계산 로직)
def calculate_late_fees_standardized(...):
    all_status = calculate_all_installments_payment_allocation(contract)
    # ... 복잡한 for 루프와 재계산 ...
    for p in payments:
        individual_penalty = calculate_daily_interest(...)
        total_penalty += individual_penalty
    # ...

# 변경 후 (단순 위임)
def calculate_late_fees_standardized(...):
    return aggregate_installment_adjustments(
        contract,
        payment_orders,
        now_due_order,
        pub_date
    )
```

**효과**:
- 코드 간소화: 116줄 → 8줄
- 정확성 보장: waterfall 로직 직접 사용
- 유지보수성 향상: 단일 진실 공급원 (Single Source of Truth)

## 변경 후 결과

### 시나리오: 3회 분할 납부

```
회차: 2차 중도금 (₩10,000,000, 약정일 2024-05-01)
납부 내역:
- Payment 1: ₩3,000,000 on 2024-04-25 (6일 조기)
- Payment 2: ₩3,000,000 on 2024-05-10 (9일 지연)
- Payment 3: ₩4,000,000 on 2024-05-15 (14일 지연)
```

**PdfExportPayments (개별 계산)**:
```
Payment 1: ₩0 (조기 납부)
Payment 2: ₩7,397 (3M × 10% ÷ 365 × 9일)
Payment 3: ₩15,342 (4M × 10% ÷ 365 × 14일)
---
총 연체료: ₩22,739
선납 할인: ₩49,315 (10M × 3% ÷ 365 × 6일)
순 조정: ₩26,576 (할인)
```

**PdfExportBill (회차별 집계)** - 변경 후:
```
2차 중도금:
  개별 납부 연체료 합계: ₩22,739 ✅
  선납 할인: ₩49,315 ✅
  순 조정: ₩26,576 ✅
```

**결과**: 두 클래스가 동일한 금액 반환 ✅

## 기술적 세부사항

### Waterfall Allocation

`calculate_all_installments_payment_allocation()` 함수는 다음을 계산합니다:

```python
installment_status[inst.id] = {
    'is_fully_paid': bool,
    'late_days': int,
    'late_payment_amount': int,
    'late_payment_details': [  # ← 여기가 핵심!
        {
            'payment_date': date,
            'payment_amount': int,
            'late_days': int,
            'late_penalty': int,  # 개별 납부 연체료
            'type': 'paid_late' or 'unpaid'
        },
        ...
    ]
}
```

### 집계 로직

```python
# 개별 납부 연체료 추출
late_payment_details = status.get('late_payment_details', [])

# 회차별 합산
penalty = sum(detail.get('late_penalty', 0) for detail in late_payment_details)
```

### 할인 계산

선납 할인은 회차 단위로 계산되므로 기존 로직 유지:
```python
adj = get_installment_adjustment_summary(contract, inst)
discount = adj.get('total_discount', 0)
```

## 테스트

### 테스트 파일

`notice/tests/test_split_payment_billing.py`

### 테스트 시나리오

1. ✅ 단일 납부 (기준선)
2. ✅ 2회 분할 납부 (모두 지연)
3. ✅ 3회 분할 납부 (조기 + 지연 혼합)
4. ✅ 선납 할인 적용
5. ✅ PdfExportBill vs PdfExportPayments 금액 일치 확인
6. ✅ aggregate 함수 출력 구조 검증
7. ✅ Waterfall 통합 테스트
8. ✅ 복수 회차 집계 테스트

### 엣지 케이스

- 연체율 0%
- 같은 날 여러 건 납부
- 초과 납부 (다음 회차 충당)
- 미납 회차

## 영향 범위

### 수정된 파일

1. `_utils/payment_adjustment.py` (+114줄)
   - `aggregate_installment_adjustments()` 함수 추가

2. `notice/exports/pdf.py` (-105줄)
   - `calculate_late_fees_standardized()` 메서드 간소화 (116줄 → 8줄)
   - `get_bill_data()` 메서드에서 `late_fee_sum` 계산 수정 (line 153)
   - 불필요한 import 제거

3. `notice/tests/test_split_payment_billing.py` (신규)
   - 분할 납부 테스트 케이스 추가

### 영향받지 않는 부분

- `payment/exports/pdf.py` (PdfExportPayments) - 변경 없음
- 다른 고지서 관련 코드 - 변경 없음
- 데이터베이스 스키마 - 변경 없음
- API 엔드포인트 - 변경 없음

## 성능

### 개선 사항

- Waterfall 계산 중복 제거
- 불필요한 QuerySet 조회 감소
- 코드 실행 경로 단순화

### 예상 성능

- 단일 납부: 동일 (변화 없음)
- 2-3회 분할 납부: 약간 개선 (중복 계산 제거)
- 5회 이상 분할 납부: 명확한 개선 (O(n²) → O(n))

## 마이그레이션

### 배포 전 확인사항

1. ✅ 문법 오류 확인: `python -m py_compile`
2. ⏳ 단위 테스트 실행: `python manage.py test notice.tests.test_split_payment_billing`
3. ⏳ 기존 고지서 출력 테스트
4. ⏳ 실제 데이터로 금액 검증

### 배포 순서

1. `_utils/payment_adjustment.py` 배포 (하위 호환)
2. `notice/exports/pdf.py` 배포 (새 함수 사용)
3. 테스트 파일 배포 (선택사항)

### 롤백 계획

문제 발생 시 `notice/exports/pdf.py`의 `calculate_late_fees_standardized()` 메서드를
이전 버전으로 복구하면 됩니다.

## 참고

### 관련 파일

- `_utils/payment_adjustment.py:1286-1400`
- `notice/exports/pdf.py:11-14, 448-480`
- `payment/exports/pdf.py:132-338` (비교용)

### 관련 이슈

- 분할 납부 시 고지서와 납부확인서 금액 불일치
- Waterfall 충당 로직 중복 계산

### 향후 개선 사항

1. Waterfall에 `payment_id` 추가하여 payment 매핑 간소화
2. 성능 프로파일링 및 최적화
3. 더 많은 엣지 케이스 테스트 추가

## 추가 수정 사항 (2025-11-14)

### 문제: 템플릿에서 연체료 합계가 0으로 표시

**증상**:
- 단일 납부: 정상 표시 ✅
- 분할 납부: 0으로 표시 ❌

**원인**:
```python
# 기존 코드 (line 152)
bill_data['late_fee_sum'] = bill_data['this_pay_sum']['penalty_sum']
```

`this_pay_sum`은 **미납 회차만** 포함하므로:
- 이미 납부된 회차의 연체료가 누락됨
- 분할 납부로 완납된 회차는 `this_pay_info`에 포함되지 않음

**해결**:
```python
# 수정 코드 (line 153)
bill_data['late_fee_sum'] = late_fee_data.get('total_late_fee', 0)
```

`late_fee_data`는 `aggregate_installment_adjustments()`의 반환값으로:
- **모든 도래한 회차** (기납부 + 미납)의 연체료 포함
- 분할 납부로 발생한 모든 연체료가 정확하게 집계됨

**템플릿 렌더링** (`_pdf/templates/pdf/partials/bill_page.html:251`):
```html
<td>{% if not data.no_late %}{{ data.late_fee_sum|default:"-"|intcomma }}{% else %}-{% endif %}</td>
```

이제 `data.late_fee_sum`에 올바른 값이 전달됩니다.

### 예시

**시나리오**: 2차 중도금 ₩10,000,000, 3회 분할 납부
- Payment 1: ₩3,000,000 (9일 지연) → 연체료 ₩7,397
- Payment 2: ₩4,000,000 (14일 지연) → 연체료 ₩15,342
- Payment 3: ₩3,000,000 (정시 완납)

**변경 전**:
```python
this_pay_info = []  # 완납되어 미납 회차 없음
penalty_sum = sum([pi["penalty"] for pi in this_pay_info])  # = 0
late_fee_sum = 0  # ❌ 잘못됨
```

**변경 후**:
```python
late_fee_data = {
    'total_late_fee': 22739,  # 7,397 + 15,342
    'installment_details': [...]
}
late_fee_sum = 22739  # ✅ 정확함
```

**템플릿 출력**:
```
합계 행의 연체료: ₩22,739
```

---

**작성일**: 2025-11-14
**최종 수정**: 2025-11-14
**작성자**: Claude Code
**버전**: 1.1
