# 납부액 집계 표준화 진행 상황

## ✅ 완료된 수정사항

### 1. ExportPaymentsByCont 기준 설정
**파일**: `payment/exports/excel.py:490-495`

**수정된 쿼리**:
```python
paid_data = ProjectCashBook.objects.filter(
    project=project,
    income__isnull=False,
    project_account_d3__is_payment=True,
    deal_date__lte=date,
    contract__isnull=False,
    contract__activation=True  # 추가된 조건
)
```

### 2. ExportPayments 표준화
**파일**: `payment/exports/excel.py:266-273`

**수정된 쿼리**:
```python
obj_list = ProjectCashBook.objects.filter(
    project=project,
    income__isnull=False,
    project_account_d3__is_payment=True,
    deal_date__range=(sd, ed),
    contract__isnull=False,     # 추가된 조건
    contract__activation=True   # 추가된 조건
)
```

### 3. 표준화 함수 추가
**파일**: `payment/exports/excel.py:26-45`

```python
def get_standardized_payment_sum(project, date=None, date_range=None):
    """표준화된 납부액 집계 - ExportPaymentsByCont 방식 기준"""
    filters = {
        'project': project,
        'income__isnull': False,
        'project_account_d3__is_payment': True,
        'contract__isnull': False,
        'contract__activation': True
    }

    if date_range:
        filters['deal_date__range'] = date_range
    elif date:
        filters['deal_date__lte'] = date

    return ProjectCashBook.objects.filter(**filters).aggregate(
        total=Sum('income')
    )['total'] or 0
```

## 🎯 기대 효과

### Before (예상 집계 결과)
- **ExportPayments**: 147,501,051,740원 (계약 미연결 + 비활성화 포함)
- **ExportPaymentsByCont**: 미지수 (activation 조건 추가 후)
- **ExportPaymentStatus**: 147,768,757,740원 (중복 집계 포함)

### After (표준화 후 예상)
- **ExportPayments**: 감소 예상 (비활성화 계약 제외)
- **ExportPaymentsByCont**: 감소 예상 (비활성화 계약 제외)
- **ExportPaymentStatus**: 수정 필요 (API 로직 중복 해결)

## 🔄 남은 작업

### 1. PaymentStatusByUnitTypeViewSet 수정
**파일**: `apiV1/views/payment.py:1047-1078`

**현재 문제**: 차수×타입별 이중 반복으로 중복 집계 가능성

**수정 방향**:
```python
# 현재: 차수×타입별 개별 집계 후 합산
for order_group, unit_type in combinations:
    paid = _get_paid_amount_by_unit_type(order_group, unit_type)
    total += paid  # 중복 위험

# 수정안: 전체 집계 후 차수×타입별 분배
total_paid = get_standardized_payment_sum(project, date)
# 각 조합별 비율로 분배 로직
```

### 2. 검증 스크립트 작성
```python
def verify_payment_consistency(project_id, date):
    """세 클래스의 집계 결과 일치 검증"""
    export_payments_total = get_export_payments_sum(project_id, date)
    export_by_cont_total = get_export_by_cont_sum(project_id, date)
    export_status_total = get_export_status_sum(project_id, date)

    print(f"ExportPayments: {export_payments_total:,}")
    print(f"ExportPaymentsByCont: {export_by_cont_total:,}")
    print(f"ExportPaymentStatus: {export_status_total:,}")

    assert export_payments_total == export_by_cont_total == export_status_total
```

## 📊 테스트 계획

1. **개별 클래스 테스트**: 각각 단독 실행하여 새로운 집계 결과 확인
2. **비교 테스트**: 세 클래스 결과 비교
3. **검증 테스트**: 표준화 함수 결과와 일치 확인
4. **회귀 테스트**: 기존 기능 정상 작동 확인

## 🎯 성공 기준

✅ **모든 클래스의 납부액 집계 결과가 동일**
✅ **비활성화 계약 제외로 더 정확한 집계**
✅ **중복 집계 문제 해결**
✅ **일관된 비즈니스 로직 적용**