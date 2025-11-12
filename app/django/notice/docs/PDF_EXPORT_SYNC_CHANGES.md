# PDF Export 할인/연체료 계산 로직 동기화

## 변경 개요

**날짜**: 2025-11-12
**목적**: PdfExportBill과 PdfExportPayments 간 할인/연체료 계산 로직 통일
**영향 범위**: `notice/exports/pdf.py` (PdfExportBill 클래스)

## 문제점

기존에는 두 PDF 클래스가 서로 다른 계산 방식을 사용하여 동일한 계약에 대해 다른 금액을 산출했습니다:

- **PdfExportBill** (고지서): `payment_adjustment.py` 기반, 납부건별 연체료 계산, 선납 할인 미계산
- **PdfExportPayments** (납부서): `simple_late_payment.py` + waterfall 기반, 회차별 집계, 선납 할인 포함

## 해결 방안

PdfExportBill을 PdfExportPayments 방식으로 통일:
- **Waterfall allocation** 기반 완납 상태 및 지연일수 계산
- **simple_late_payment** 모듈의 연체료 계산 공식 사용
- **선납 할인 계산 추가** (기존에 누락되어 있었음)

---

## 주요 변경 사항

### 1. Import 변경

**변경 전**:
```python
from _utils.payment_adjustment import (
    get_unpaid_installments,
    calculate_late_penalty,
    calculate_daily_interest
)
```

**변경 후**:
```python
from _utils.payment_adjustment import (
    calculate_all_installments_payment_allocation,
    get_installment_adjustment_summary
)
from _utils.simple_late_payment import calculate_late_penalty
```

### 2. `calculate_late_fees_standardized()` 메서드 재작성

#### 변경 전 로직:
1. 완납된 납부건의 연체료 계산 (payment_adjustment.calculate_late_penalty)
2. 미납 회차의 연체료 계산 (get_unpaid_installments + calculate_daily_interest)
3. **선납 할인 계산 없음**

#### 변경 후 로직:
1. **Waterfall allocation** (`calculate_all_installments_payment_allocation`) 으로 전체 회차 완납 상태 계산
2. 도래한 회차 필터링
3. 회차별로:
   - 연체료 계산 (`simple_late_payment.calculate_late_penalty`)
   - **선납 할인 계산** (`get_installment_adjustment_summary`)
4. 회차별 상세 정보 집계

#### 반환 데이터 구조 변경:

**변경 전**:
```python
{
    'total_late_fee': int,
    'paid_penalties': list,      # 완납 회차 연체료 목록
    'unpaid_penalties': list,    # 미납 회차 연체료 목록
    'paid_penalty_count': int,
    'unpaid_penalty_count': int
}
```

**변경 후**:
```python
{
    'total_late_fee': int,        # 총 연체료
    'total_discount': int,         # 총 선납 할인 (신규)
    'installment_details': list,   # 회차별 상세 ({installment, penalty_amount, discount_amount, ...})
    'penalty_count': int,          # 연체료 발생 건수
    'discount_count': int          # 할인 발생 건수 (신규)
}
```

### 3. `get_this_pay_info()` 메서드 업데이트

#### 선납 할인 행 추가:
```python
if total_discount > 0:
    payment_list.append({
        'order': '선납 할인',
        'due_date': '',
        'amount': 0,
        'unpaid': 0,
        'penalty': 0,
        'discount': total_discount,
        'sum_amount': -total_discount,  # 할인은 차감
        'is_discount': True
    })
```

#### 회차별 할인 정보 추가:
각 회차 딕셔너리에 `discount` 필드 추가:
```python
payment_dict = {
    'order': order,
    'due_date': get_due_date_per_order(contract, order, unpaid_orders),
    'amount': amount,
    'unpaid': unpaid,
    'penalty': penalty,
    'discount': discount,  # 신규
    'sum_amount': unpaid + penalty - discount  # 할인 반영
}
```

### 4. `this_pay_sum` 집계 업데이트

할인 합계 추가:
```python
bill_data['this_pay_sum'] = {
    'amount_sum': sum([pi["amount"] for pi in bill_data['this_pay_info']]),
    'unpaid_sum': sum([pi["unpaid"] for pi in bill_data['this_pay_info']]),
    'penalty_sum': sum([pi["penalty"] for pi in bill_data['this_pay_info']]),
    'discount_sum': sum([pi.get("discount", 0) for pi in bill_data['this_pay_info']]),  # 신규
    'amount_total': sum([pi["sum_amount"] for pi in bill_data['this_pay_info']]),
}
```

### 5. `get_due_orders()` 메서드 업데이트

기존 `paid_penalties`/`unpaid_penalties` 구조에서 `installment_details` 구조로 변경:

```python
# late_fee_details에서 회차별 정보 추출
adjustment_by_order = {}
if late_fee_details and late_fee_details.get('installment_details'):
    for detail in late_fee_details['installment_details']:
        installment = detail['installment']
        adjustment_by_order[installment.pay_code] = {
            'late_amount': detail.get('late_amount', 0),
            'late_days': detail.get('late_days', 0),
            'penalty_amount': detail.get('penalty_amount', 0),
            'discount_amount': detail.get('discount_amount', 0)  # 신규
        }

# 각 회차에 penalty와 discount 분리하여 추가
paid_dict['penalty'] = adjustment.get('penalty_amount', 0)
paid_dict['discount'] = adjustment.get('discount_amount', 0)
paid_dict['unpaid_result'] = paid_dict['penalty'] - paid_dict['discount']
```

### 6. `discount_sum` 필드 추가

bill_data에 할인 합계 필드 추가:
```python
bill_data['late_fee_sum'] = bill_data['this_pay_sum']['penalty_sum']
bill_data['discount_sum'] = bill_data['this_pay_sum']['discount_sum']  # 신규
```

### 7. PDF 템플릿 업데이트 (`_pdf/templates/pdf/partials/bill_page.html`)

#### 헤더 변경 (3열 구조 유지, 일수에 부호 표시):
**변경 전**:
```html
<td colspan="3">선납연체(할인가산)</td>
<td>적용금액</td>
<td>일수</td>
<td>할인(-)/가산금</td>
```

**변경 후**:
```html
<td colspan="3">선납할인 / 연체가산</td>
<td>적용금액</td>
<td>일수</td>                      <!-- 선납: 음수(-), 연체: 양수(+) -->
<td>할인(-)/가산(+)</td>           <!-- penalty - discount -->
```

#### 데이터 행 변경:
**변경 전**:
```html
<td>{{ paid_order.unpaid_amt|default:"-"|intcomma }}</td>
<td>{{ paid_order.unpaid_days|default:"-"|intcomma }}</td>
<td>{{ paid_order.unpaid_result|default:"-"|intcomma }}</td>
```

**변경 후** (로직 변경):
```html
<td>{{ paid_order.unpaid_amt|default:"-"|intcomma }}</td>      <!-- 적용금액 -->
<td>{{ paid_order.unpaid_days|default:"-"|intcomma }}</td>     <!-- 일수: 선납(-), 연체(+) -->
<td>{{ paid_order.unpaid_result|default:"-"|intcomma }}</td>   <!-- penalty - discount -->
```

**Python 로직**:
```python
# 일수: 선납은 음수(-), 연체는 양수(+)
if discount > 0 and penalty == 0:
    paid_dict['unpaid_days'] = -prepay_days  # 선납일수를 음수로
elif penalty > 0:
    paid_dict['unpaid_days'] = late_days     # 연체일수를 양수로
else:
    paid_dict['unpaid_days'] = 0

# 최종 금액: penalty - discount (양수면 가산, 음수면 할인)
paid_dict['unpaid_result'] = penalty - discount
```

#### 합계 행 변경:
**변경 전**:
```html
<td>{{ 0|default:"-"|intcomma }}</td>
<td>{{ 0|default:"-"|intcomma }}</td>
<td>{{ data.late_fee_sum|default:"-"|intcomma }}</td>
```

**변경 후**:
```html
<td>-</td>                                                      <!-- 적용금액 합계 -->
<td>-</td>                                                      <!-- 일수 합계 -->
<td>{{ data.late_fee_sum|default:"-"|intcomma }}</td>          <!-- 연체료 합계 (할인은 음수로 표시됨) -->
```

---

## 계산 로직 상세

### Waterfall Allocation 방식

`calculate_all_installments_payment_allocation(contract)` 함수가 반환하는 회차별 상태 정보:

```python
{
    installment_id: {
        'is_fully_paid': bool,          # 완납 여부
        'fully_paid_date': date,        # 완납 일자
        'paid_amount': int,             # 납부액
        'remaining_amount': int,        # 잔액
        'promised_amount': int,         # 약정액
        'late_days': int,               # 지연일수 (이미 계산됨)
        'late_payment_amount': int      # 지연 납부액
    },
    ...
}
```

### 연체료 계산 공식

`simple_late_payment.calculate_late_penalty()`:
```python
penalty = late_payment_amount * (late_penalty_ratio / 100 / 365) * late_days
return int(penalty)  # 소수점 절사
```

### 선납 할인 계산

`get_installment_adjustment_summary()` 내부의 `calculate_prepayment_discount()`:
- 완납 여부 확인
- 완납일 < 납부기한 확인
- 선납 일수 계산
- 할인액 = 약정액 * (할인율 / 100 / 365) * 선납일수

---

## 호환성 및 영향

### 기존 코드와의 호환성

✅ **데이터 구조 변경**:
- `late_fee_details` 파라미터 구조가 변경되었으므로, 이를 사용하는 모든 코드 확인 필요
- 특히 고지서 템플릿에서 `late_fee_details`를 참조하는 부분 업데이트 필요

✅ **금액 변경 가능성**:
- 선납 할인이 새로 계산되므로, 기존 고지서와 금액이 달라질 수 있음
- 변경은 **정확한** 계산 결과이므로, 기존이 틀린 것임

### 테스트 커버리지

`tests/test_pdf_export_sync.py` 파일에서 다음 시나리오 테스트:

1. **단위 테스트**:
   - `calculate_late_penalty` 함수 정확성
   - Waterfall allocation 기본 동작
   - 선납 할인 계산
   - 연체료 계산
   - 부분 납부 시 연체료

2. **통합 테스트**:
   - PdfExportBill과 PdfExportPayments 결과 비교
   - 동일한 계약에 대한 연체료/할인 일치성 검증

---

## 마이그레이션 가이드

### 고지서 템플릿 업데이트 (해당 시)

템플릿에서 `bill_data['late_fee_details']` 사용 시:

**변경 전**:
```django
{% for penalty in late_fee_details.paid_penalties %}
    {{ penalty.penalty_amount }}
{% endfor %}
```

**변경 후**:
```django
{% for detail in late_fee_details.installment_details %}
    {% if detail.penalty_amount > 0 %}
        {{ detail.penalty_amount }}
    {% endif %}
{% endfor %}
```

### 선납 할인 표시

`this_pay_info`에 할인 행이 추가됨:
```django
{% for item in this_pay_info %}
    {% if item.is_discount %}
        <tr class="discount-row">
            <td>{{ item.order }}</td>  <!-- "선납 할인" -->
            <td>{{ item.discount|intcomma }}원</td>
            <td>-{{ item.sum_amount|intcomma }}원</td>  <!-- 음수 -->
        </tr>
    {% endif %}
{% endfor %}
```

### discount_sum 활용

총 할인액이 `this_pay_sum`에 추가됨:
```django
<tr>
    <td>선납 할인 합계</td>
    <td>{{ bill_data.this_pay_sum.discount_sum|intcomma }}원</td>
</tr>
```

---

## 검증 방법

### 1. 단위 테스트 실행

```bash
python manage.py test notice.tests --verbosity=2

# 특정 테스트 클래스만 실행
python manage.py test notice.tests.PdfExportBillTestCase --verbosity=2
```

### 2. 실제 데이터 검증

동일한 계약에 대해 두 PDF를 생성하여 금액 비교:

```python
# 고지서
from notice.exports.pdf import PdfExportBill
bill_result = PdfExportBill.calculate_late_fees_standardized(contract, orders, now_due, pub_date)

# 납부서
from payment.exports.pdf import PdfExportPayments
payments_result, _, (penalty, discount, _) = PdfExportPayments.get_paid_with_adjustment(contract, pub_date)

# 비교
assert bill_result['total_late_fee'] == penalty
assert bill_result['total_discount'] == discount
```

### 3. 수동 검증 체크리스트

- [ ] 정상 납부 계약의 고지서 생성 확인
- [ ] 연체 납부 계약의 연체료 계산 확인
- [ ] 선납 할인 적용 계약의 할인 계산 확인
- [ ] 부분 납부 계약의 잔액 및 연체료 확인
- [ ] PDF 출력 형식 및 레이아웃 확인

---

## 향후 계획

### 단기 (완료 후 즉시)
- [x] PdfExportBill 계산 로직 변경
- [x] this_pay_info 할인 행 추가
- [x] 테스트 케이스 작성
- [x] get_due_orders() 메서드 업데이트 (penalty/discount 분리)
- [x] discount_sum 필드 추가
- [x] 고지서 템플릿 업데이트 (bill_page.html - 4열 구조)
- [ ] 실제 데이터로 검증

### 중기 (1-2주 내)
- [ ] 다른 PDF 클래스에도 동일한 로직 적용 (해당 시)
- [ ] 성능 최적화 (대량 계약 처리 시)
- [ ] 사용자 문서 업데이트

### 장기 (추후 고려)
- [ ] `simple_late_payment.py`를 표준으로 확정하고 `payment_adjustment.py` 통합
- [ ] 통합 계산 유틸리티 함수 생성 (`calculate_comprehensive_adjustment`)
- [ ] 모든 PDF 클래스에서 동일한 함수 호출하도록 리팩토링

---

## 관련 파일

### 수정된 파일
- `app/django/notice/exports/pdf.py` - PdfExportBill 클래스 (calculate_late_fees_standardized, get_this_pay_info, get_due_orders 메서드)
- `app/django/_pdf/templates/pdf/partials/bill_page.html` - 고지서 템플릿 (4열 구조로 변경)

### 신규 파일
- `app/django/notice/docs/PDF_EXPORT_SYNC_CHANGES.md` - 이 문서

### 수정된 파일 (테스트)
- `app/django/notice/tests.py` - PdfExportBill 테스트 추가

### 참조 파일
- `app/django/payment/exports/pdf.py` - PdfExportPayments (표준 로직)
- `app/django/_utils/simple_late_payment.py` - 연체료 계산
- `app/django/_utils/payment_adjustment.py` - Waterfall allocation, 선납 할인

---

## 문의 및 지원

변경 사항에 대한 문의나 이슈 발견 시:
1. `tests/test_pdf_export_sync.py`에 재현 가능한 테스트 케이스 작성
2. 이 문서의 "검증 방법" 섹션 참고
3. 실제 계약 데이터로 검증 후 보고

---

## 변경 이력

| 날짜 | 작성자 | 변경 내용 |
|------|--------|-----------|
| 2025-11-12 | Claude | 최초 작성 - PdfExportBill 로직 동기화 |
| 2025-11-12 | Claude | get_due_orders() 메서드 업데이트 - penalty/discount 분리 |
| 2025-11-12 | Claude | bill_page.html 템플릿 업데이트 - 4열 구조 시도 후 3열 구조로 회귀 |
| 2025-11-12 | Claude | 최종 구조 확정: 일수에 부호 표시 (선납: 음수, 연체: 양수) |
| 2025-11-12 | Claude | prepay_days 필드 추가 및 일수 계산 로직 개선 |
