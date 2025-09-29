# 입금액 집계 방식 차이점 분석

## 문제 현황

세 Excel 내보내기 클래스에서 동일한 분양계약자들의 실제 납부 금액을 집계하는데 결과가 다름:

- **ExportPayments**: 147,501,051,740원
- **ExportPaymentsByCont**: 147,440,605,740원
- **ExportPaymentStatus**: 147,768,757,740원

## 각 클래스별 집계 방식 분석

### 1. ExportPayments 클래스 - 수납건별 수납내역

**위치**: `payment/exports/excel.py:266-294`

**쿼리 방식**:

```python
obj_list = ProjectCashBook.objects.filter(
    project=project,
    income__isnull=False,
    project_account_d3__is_payment=True,
    deal_date__range=(sd, ed)  # 기간 필터
).order_by('deal_date', 'created')

# 추가 필터링: og, ut, ipo, ba, nc, ni, q 등
```

**특징**:

- `ProjectCashBook` 테이블 직접 조회
- **날짜 범위 필터** 적용 (`deal_date__range=(sd, ed)`)
- `project_account_d3__is_payment=True` 조건
- **계약 여부 구분 없음** (nc 옵션으로 선택적 필터링만)
- 거래일자 기준 필터링

### 2. ExportPaymentsByCont 클래스 - 계약자별 수납내역

**위치**: `payment/exports/excel.py:490-495`

**쿼리 방식**:

```python
paid_data = ProjectCashBook.objects.filter(
    project=project,
    income__isnull=False,
    project_account_d3__is_payment=True,
    deal_date__lte=date,  # 날짜까지
    contract__isnull=False  # 계약 연결된 것만
)

# 계약별 집계
paid_sum = sum([ps[1] for ps in paid_dict if ps[0] == row[0]])
```

**특징**:

- `ProjectCashBook` 테이블 직접 조회
- **특정 날짜까지** 필터링 (`deal_date__lte=date`)
- `contract__isnull=False` - **계약과 연결된 수납액만**
- 계약자별로 개별 집계

### 3. ExportPaymentStatus 클래스 - API 기반 집계

**위치**: `apiV1/views/payment.py:1047-1078`

**쿼리 방식**:

```sql
SELECT COALESCE(SUM(pcb.income), 0) as paid_amount
FROM cash_projectcashbook pcb
         INNER JOIN payment_installmentpaymentorder ipo ON pcb.installment_order_id = ipo.id
         INNER JOIN contract_contract c ON pcb.contract_id = c.id
WHERE ipo.project_id = %s
  AND c.order_group_id = %s
  AND c.unit_type_id = %s
  AND c.activation = true -- 활성화된 계약만
  AND pcb.income IS NOT NULL
  AND pcb.deal_date <= %s -- 날짜까지
```

**특징**:

- **installment_order 기준** 조인
- **활성화된 계약만** (`c.activation = true`)
- **납부회차별** 집계 후 합산
- 더 엄격한 조인 조건

## 주요 차이점 분석

### 1. 날짜 필터링 방식

- **ExportPayments**: 기간 범위 (`sd ~ ed`)
- **ExportPaymentsByCont**: 특정 날짜까지 (`<= date`)
- **ExportPaymentStatus**: 특정 날짜까지 (`<= date`)

### 2. 계약 연결 조건

- **ExportPayments**: 계약 연결 여부 구분 없음
- **ExportPaymentsByCont**: `contract__isnull=False`
- **ExportPaymentStatus**: `INNER JOIN contract` + `activation = true`

### 3. 조인 방식

- **ExportPayments**: 단순 ProjectCashBook 조회
- **ExportPaymentsByCont**: 단순 ProjectCashBook 조회
- **ExportPaymentStatus**: installment_order + contract 조인

### 4. 활성화 상태

- **ExportPayments**: 미고려
- **ExportPaymentsByCont**: 미고려
- **ExportPaymentStatus**: `activation = true` 필수

## 차이 발생 원인

1. **비활성화 계약**: ExportPaymentStatus만 `activation = true` 조건
2. **계약 미연결 수납액**: ExportPayments는 포함, 나머지는 제외
3. **날짜 범위**: ExportPayments는 범위, 나머지는 특정일까지
4. **조인 방식**: ExportPaymentStatus는 더 엄격한 조인

## 정확한 집계 방식 권장사항

**ExportPaymentStatus (API 방식)가 가장 정확한 이유**:

1. **비즈니스 로직 준수**: 활성화된 계약만 집계
2. **데이터 무결성**: installment_order 기준 엄격한 조인
3. **일관성**: OverallSummaryViewSet과 동일한 로직
4. **검증된 로직**: API에서 이미 검증된 집계 방식

## 일원화 방안

### 권장 통합 쿼리

```python
def get_standardized_payment_sum(project_id, date=None):
    """표준화된 납부액 집계"""
    from django.db import connection

    date_filter = ""
    params = [project_id]

    if date:
        date_filter = "AND pcb.deal_date <= %s"
        params.append(date)

    query = f"""
        SELECT COALESCE(SUM(pcb.income), 0) as total_paid
        FROM cash_projectcashbook pcb
        INNER JOIN payment_installmentpaymentorder ipo ON pcb.installment_order_id = ipo.id
        INNER JOIN contract_contract c ON pcb.contract_id = c.id
        WHERE ipo.project_id = %s
          AND c.activation = true
          AND pcb.income IS NOT NULL
          {date_filter}
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0
```

### 수정 적용 우선순위

1. **ExportPayments**: 계약 연결 + 활성화 조건 추가
2. **ExportPaymentsByCont**: 활성화 조건 추가
3. **ExportPaymentStatus**: 현재 방식 유지 (기준)

이를 통해 세 클래스 모두 동일한 집계 결과를 얻을 수 있습니다.