# Cash → Ledger 장기 리팩토링 마스터 플랜

## 🎯 프로젝트 개요

기존 cash 앱을 운영 중단 없이 ledger 앱으로 점진적 대체하여 단일 책임 원칙을 준수하는 깔끔한 아키텍처로 전환

### 목표
- **안정성**: 수년간 쌓인 운영 데이터의 무결성 보장
- **확장성**: 새로운 거래 유형과 비즈니스 로직을 쉽게 추가할 수 있는 구조
- **유지보수성**: 각 도메인의 독립적 관리를 통한 코드 품질 향상
- **성능**: 기존 성능 수준 유지 또는 개선

## 📊 현재 Cash 앱 분석

### ⚠️ 주요 문제점

#### 1. 단일 책임 원칙(SRP) 위반
- **CashBook 모델**: 은행거래 + 계정정보 + 증빙 + 프로젝트 관리 정보가 하나의 테이블에 혼재
- **ProjectCashBook 모델**: 은행거래 + 계정정보 + 계약정보 + 회차정보가 하나의 테이블에 혼재

#### 2. 복잡한 의존성
```python
# 현재 구조의 문제
CashBook:
  - 은행거래 (bank_account, income, outlay, deal_date)
  - 회계분류 (sort, account_d1/d2/d3, evidence)
  - 관리정보 (project, is_separate, separated, content)
  - 메타데이터 (creator, created, updated)
```

#### 3. 확장성 부족
- 새로운 거래 유형 추가 시 기존 모델 수정 필요
- 비즈니스 로직이 모델에 강하게 결합
- 도메인별 독립적 발전 불가

#### 4. 테스트 어려움
- 모든 관심사가 결합되어 단위 테스트 작성 복잡
- Mock 객체 생성 시 불필요한 필드까지 설정 필요
- 테스트 데이터 준비 복잡

### 🔍 기존 구조 상세 분석

#### CashBook (본사 입출금)
```python
class CashBook(models.Model):
    # 회사 정보
    company = models.ForeignKey('company.Company', ...)

    # 회계 분류
    sort = models.ForeignKey('ibs.AccountSort', ...)
    account_d1 = models.ForeignKey('ibs.AccountSubD1', ...)
    account_d2 = models.ForeignKey('ibs.AccountSubD2', ...)
    account_d3 = models.ForeignKey('ibs.AccountSubD3', ...)

    # 은행 거래
    bank_account = models.ForeignKey(CompanyBankAccount, ...)
    income = models.PositiveBigIntegerField(...)
    outlay = models.PositiveBigIntegerField(...)
    deal_date = models.DateField(...)

    # 관리 정보
    project = models.ForeignKey('project.Project', ...)
    is_separate = models.BooleanField(...)
    separated = models.ForeignKey('self', ...)
    content = models.CharField(...)
    trader = models.CharField(...)

    # 증빙
    evidence = models.CharField(...)

    # 메타데이터
    creator = models.ForeignKey(...)
    created = models.DateTimeField(...)
    updated = models.DateTimeField(...)
```

#### ProjectCashBook (프로젝트 입출금)
```python
class ProjectCashBook(models.Model):
    # 프로젝트 정보
    project = models.ForeignKey('project.Project', ...)

    # 회계 분류
    sort = models.ForeignKey('ibs.AccountSort', ...)
    project_account_d2 = models.ForeignKey('ibs.ProjectAccountD2', ...)
    project_account_d3 = models.ForeignKey('ibs.ProjectAccountD3', ...)

    # 은행 거래
    bank_account = models.ForeignKey(ProjectBankAccount, ...)
    income = models.PositiveBigIntegerField(...)
    outlay = models.PositiveBigIntegerField(...)
    deal_date = models.DateField(...)

    # 계약 관련 (분양대금 특화)
    contract = models.ForeignKey('contract.Contract', ...)
    installment_order = models.ForeignKey('payment.InstallmentPaymentOrder', ...)
    refund_contractor = models.ForeignKey('contract.Contractor', ...)

    # 관리 정보
    is_separate = models.BooleanField(...)
    separated = models.ForeignKey('self', ...)
    is_imprest = models.BooleanField(...)
    content = models.CharField(...)
    trader = models.CharField(...)

    # 증빙
    evidence = models.CharField(...)

    # 메타데이터
    creator = models.ForeignKey(...)
    created = models.DateTimeField(...)
    updated = models.DateTimeField(...)
```

## 🏗️ Ledger 앱 목표 아키텍처

### ✅ 핵심 설계 원칙

#### 1. 단일 책임 원칙 (Single Responsibility Principle)
- 각 모델은 하나의 관심사만 담당
- 은행거래, 회계분류, 계약정보를 별도 모델로 분리

#### 2. 개방-폐쇄 원칙 (Open-Closed Principle)
- 새로운 거래 유형 추가 시 기존 코드 수정 없이 확장 가능
- 인터페이스 기반 설계로 다형성 활용

#### 3. 의존성 역전 원칙 (Dependency Inversion Principle)
- 구체적 구현이 아닌 추상화에 의존
- 도메인 로직이 데이터베이스 구현에 의존하지 않음

#### 4. 인터페이스 분리 원칙 (Interface Segregation Principle)
- 클라이언트가 사용하지 않는 메서드에 의존하지 않음
- 도메인별 최소한의 인터페이스 제공

### 🧩 분리된 모델 구조

#### 1. 은행거래 도메인 (Banking Domain)

```python
# 공통 은행거래 추상 모델
class BankTransaction(models.Model):
    """순수한 은행거래 정보만 관리"""

    # 거래 식별
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True)

    # 거래 기본 정보
    amount = models.PositiveBigIntegerField('거래금액')
    transaction_type = models.CharField('거래구분', choices=[
        ('INCOME', '입금'),
        ('OUTLAY', '출금')
    ])
    deal_date = models.DateField('거래일자')

    # 계좌 정보
    bank_account_type = models.CharField('계좌구분', choices=[
        ('COMPANY', '본사계좌'),
        ('PROJECT', '프로젝트계좌')
    ])
    bank_account_id = models.PositiveIntegerField('계좌ID')

    # 거래 상태
    status = models.CharField('상태', default='CONFIRMED')
    reference_number = models.CharField('거래번호', blank=True)

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, ...)

    class Meta:
        abstract = True

class CompanyBankTransaction(BankTransaction):
    """본사 은행거래"""
    company = models.ForeignKey('company.Company', ...)

class ProjectBankTransaction(BankTransaction):
    """프로젝트 은행거래"""
    project = models.ForeignKey('project.Project', ...)
```

#### 2. 회계분류 도메인 (Accounting Domain)

```python
class AccountingEntry(models.Model):
    """회계 분류 및 증빙 정보 관리"""

    # 연결된 거래
    transaction_id = models.UUIDField('거래ID')
    transaction_type = models.CharField('거래모델구분', choices=[
        ('COMPANY', 'CompanyBankTransaction'),
        ('PROJECT', 'ProjectBankTransaction')
    ])

    # 회계 분류
    sort = models.ForeignKey('ibs.AccountSort', ...)
    account_code = models.CharField('계정코드', max_length=10)

    # 적요 및 거래처
    content = models.CharField('적요', max_length=50)
    trader = models.CharField('거래처', max_length=25, blank=True)
    note = models.TextField('비고', blank=True)

    # 증빙
    evidence = models.CharField('증빙구분', choices=[
        ('0', '증빙 없음'),
        ('1', '세금계산서'),
        ('2', '계산서(면세)'),
        # ... 기존 choices
    ])

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CompanyAccountingEntry(AccountingEntry):
    """본사 회계분류"""
    company = models.ForeignKey('company.Company', ...)
    account_d1 = models.ForeignKey('ibs.AccountSubD1', ...)
    account_d2 = models.ForeignKey('ibs.AccountSubD2', ...)
    account_d3 = models.ForeignKey('ibs.AccountSubD3', ...)

class ProjectAccountingEntry(AccountingEntry):
    """프로젝트 회계분류"""
    project = models.ForeignKey('project.Project', ...)
    project_account_d2 = models.ForeignKey('ibs.ProjectAccountD2', ...)
    project_account_d3 = models.ForeignKey('ibs.ProjectAccountD3', ...)
```

#### 3. 계약관련 도메인 (Contract Domain)

```python
class ContractPayment(models.Model):
    """계약 관련 수납/환불 정보 (프로젝트 전용)"""

    # 연결된 거래
    transaction_id = models.UUIDField('거래ID')

    # 계약 정보
    project = models.ForeignKey('project.Project', ...)
    contract = models.ForeignKey('contract.Contract', ...)
    installment_order = models.ForeignKey('payment.InstallmentPaymentOrder', ...)

    # 수납/환불 구분
    payment_type = models.CharField('구분', choices=[
        ('PAYMENT', '수납'),
        ('REFUND', '환불')
    ])

    # 환불 관련 (환불인 경우만)
    refund_contractor = models.ForeignKey('contract.Contractor', ...)

    # 특수 용도
    is_imprest = models.BooleanField('운영비 여부', default=False)

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 4. 거래분할 관리 (Transaction Split)

```python
class TransactionSplit(models.Model):
    """거래 분할 정보 관리"""

    # 원본 거래
    parent_transaction_id = models.UUIDField('원본거래ID')
    parent_transaction_type = models.CharField('원본거래모델')

    # 분할 거래 목록
    child_transactions = models.JSONField('분할거래목록')  # [{'id': uuid, 'type': str, 'amount': int}]

    # 분할 정보
    split_reason = models.CharField('분할사유', max_length=100)
    total_amount = models.PositiveBigIntegerField('총금액')

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
```

### 🔗 모델 간 관계 및 연동

#### 1. 느슨한 결합 (Loose Coupling)
- UUID 기반 연결로 물리적 외래키 의존성 최소화
- 각 도메인이 독립적으로 발전 가능
- 마이크로서비스 아키텍처 전환 시에도 용이

#### 2. 이벤트 기반 연동
```python
# 거래 생성 시 이벤트 발생
@receiver(post_save, sender=CompanyBankTransaction)
def create_accounting_entry(sender, instance, created, **kwargs):
    if created:
        # 회계 분류 자동 생성
        create_default_accounting_entry.delay(
            transaction_id=instance.transaction_id,
            transaction_type='COMPANY'
        )
```

#### 3. 서비스 레이어 패턴
```python
class TransactionService:
    """거래 관련 비즈니스 로직 통합 관리"""

    @transaction.atomic
    def create_company_transaction(self, transaction_data, accounting_data):
        # 1. 은행거래 생성
        bank_tx = CompanyBankTransaction.objects.create(**transaction_data)

        # 2. 회계분류 생성
        accounting_entry = CompanyAccountingEntry.objects.create(
            transaction_id=bank_tx.transaction_id,
            **accounting_data
        )

        return bank_tx, accounting_entry

    @transaction.atomic
    def create_contract_payment(self, transaction_data, accounting_data, contract_data):
        # 1. 은행거래 생성
        bank_tx = ProjectBankTransaction.objects.create(**transaction_data)

        # 2. 회계분류 생성
        accounting_entry = ProjectAccountingEntry.objects.create(
            transaction_id=bank_tx.transaction_id,
            **accounting_data
        )

        # 3. 계약정보 생성
        contract_payment = ContractPayment.objects.create(
            transaction_id=bank_tx.transaction_id,
            **contract_data
        )

        return bank_tx, accounting_entry, contract_payment
```

## 📋 단계별 리팩토링 로드맵

### Phase 1: 모델 설계 및 구현 (2-3주)

#### Week 1: 기반 모델 구현
- [ ] 추상 모델(BankTransaction, AccountingEntry) 설계
- [ ] UUID 기반 연결 시스템 구현
- [ ] 기본 마이그레이션 생성
- [ ] 모델 관계 설정

#### Week 2-3: 구체 모델 구현
- [ ] CompanyBankTransaction, ProjectBankTransaction 구현
- [ ] CompanyAccountingEntry, ProjectAccountingEntry 구현
- [ ] ContractPayment 모델 구현
- [ ] TransactionSplit 모델 구현

#### 검증 기준
- [ ] 모든 모델 단위 테스트 통과
- [ ] 데이터베이스 제약조건 검증
- [ ] 성능 테스트 (기존 대비 90% 이상)

### Phase 2: API 개발 (3-4주)

#### Week 1: 기본 API 구조
- [ ] Django REST Framework 설정
- [ ] Serializer 계층 구조 설계
- [ ] ViewSet 기본 CRUD 구현
- [ ] URL 라우팅 설정

#### Week 2: 비즈니스 로직 API
- [ ] 거래 생성 API (은행거래 + 회계분류 통합)
- [ ] 거래 분할 API
- [ ] 계약 수납 API (프로젝트 전용)
- [ ] 복합 조회 API

#### Week 3: 고급 기능
- [ ] 대량 거래 처리 API
- [ ] 거래 검증 API
- [ ] 보고서 생성 API
- [ ] 파일 업로드/다운로드 API

#### Week 4: API 최적화
- [ ] 쿼리 최적화 (select_related, prefetch_related)
- [ ] 캐싱 전략 적용
- [ ] API 문서 자동 생성 (drf-spectacular)
- [ ] 보안 검증 및 권한 시스템

#### 검증 기준
- [ ] API 통합 테스트 100% 통과
- [ ] 성능 테스트 (응답시간 < 500ms)
- [ ] 보안 테스트 통과
- [ ] API 문서 완성도 95% 이상

### Phase 3: Frontend 개발 (4-5주)

#### Week 1-2: Vue 컴포넌트 개발
- [ ] 거래 입력 폼 컴포넌트
- [ ] 거래 목록 표시 컴포넌트
- [ ] 계정 선택 컴포넌트
- [ ] 상태 관리 (Pinia store)

#### Week 3-4: 고급 UI 기능
- [ ] 대량 데이터 처리 (가상화)
- [ ] 실시간 검증 및 피드백
- [ ] 드래그 앤 드롭 파일 업로드
- [ ] 반응형 디자인 적용

#### Week 5: 사용성 및 테스트
- [ ] 사용자 경험(UX) 최적화
- [ ] 접근성(a11y) 개선
- [ ] E2E 테스트 작성
- [ ] 브라우저 호환성 테스트

#### 검증 기준
- [ ] 컴포넌트 단위 테스트 90% 커버리지
- [ ] E2E 테스트 주요 시나리오 100% 통과
- [ ] 성능 테스트 (First Contentful Paint < 2초)
- [ ] 접근성 테스트 WCAG 2.1 AA 레벨

### Phase 4: 데이터 이관 및 검증 (2-3주)

#### Week 1: 마이그레이션 도구 개발
- [ ] 데이터 추출 스크립트
- [ ] 데이터 변환 로직
- [ ] 데이터 검증 도구
- [ ] 롤백 메커니즘

#### Week 2: 실제 데이터 이관
- [ ] 단계별 데이터 이관 실행
- [ ] 데이터 무결성 검증
- [ ] 성능 비교 분석
- [ ] 문제점 식별 및 해결

#### Week 3: 병렬 운영 준비
- [ ] 실시간 동기화 시스템
- [ ] 모니터링 대시보드
- [ ] 알림 시스템 구축
- [ ] 운영 매뉴얼 작성

#### 검증 기준
- [ ] 데이터 무결성 100% 보장
- [ ] 이관 시간 < 2시간 (다운타임 최소화)
- [ ] 동기화 지연시간 < 1초
- [ ] 모든 비즈니스 로직 검증 통과

### Phase 5: 시스템 전환 (1-2주)

#### Week 1: 단계적 전환
- [ ] 읽기 트래픽 50% 전환
- [ ] 모니터링 및 성능 확인
- [ ] 쓰기 트래픽 점진적 전환
- [ ] 최종 검증

#### Week 2: 완전 전환 및 정리
- [ ] Cash 앱 비활성화
- [ ] 데이터 아카이브
- [ ] 불필요한 코드 제거
- [ ] 문서 정리

#### 검증 기준
- [ ] 서비스 중단 시간 < 30분
- [ ] 모든 기능 정상 동작 확인
- [ ] 성능 기준 만족
- [ ] 사용자 피드백 수집 및 반영

## 🔄 데이터 이관 전략

### 1. 단계별 이관 계획

#### Phase 4.1: 읽기 전용 이관
```python
# CashBook → CompanyBankTransaction + CompanyAccountingEntry
def migrate_cashbook_readonly():
    for cashbook in CashBook.objects.all():
        # 1. 은행거래 생성
        transaction = CompanyBankTransaction.objects.create(
            transaction_id=uuid.uuid4(),
            company=cashbook.company,
            amount=cashbook.income or cashbook.outlay,
            transaction_type='INCOME' if cashbook.income else 'OUTLAY',
            deal_date=cashbook.deal_date,
            # ...
        )

        # 2. 회계분류 생성
        CompanyAccountingEntry.objects.create(
            transaction_id=transaction.transaction_id,
            company=cashbook.company,
            sort=cashbook.sort,
            account_d1=cashbook.account_d1,
            # ...
        )
```

#### Phase 4.2: 실시간 동기화
```python
# Cash 앱 변경사항을 Ledger에 실시간 반영
@receiver(post_save, sender=CashBook)
def sync_to_ledger(sender, instance, **kwargs):
    # 기존 데이터 있으면 업데이트, 없으면 생성
    sync_cashbook_to_ledger.delay(instance.id)
```

#### Phase 4.3: 양방향 동기화
```python
# 테스트 기간 중 양방향 동기화로 데이터 일관성 보장
class DualWriteService:
    def create_transaction(self, data):
        with transaction.atomic():
            # 1. 기존 Cash 모델에 저장
            cashbook = CashBook.objects.create(**legacy_data)

            # 2. 신규 Ledger 모델에 저장
            bank_tx = CompanyBankTransaction.objects.create(**new_data)
            accounting = CompanyAccountingEntry.objects.create(**accounting_data)
```

### 2. 데이터 검증 전략

#### 무결성 검증
```python
def validate_migration_integrity():
    """이관된 데이터의 무결성 검증"""

    # 1. 레코드 수 일치 확인
    assert CashBook.objects.count() == CompanyBankTransaction.objects.count()

    # 2. 금액 합계 일치 확인
    old_sum = CashBook.objects.aggregate(total=Sum('income'))['total']
    new_sum = CompanyBankTransaction.objects.filter(
        transaction_type='INCOME'
    ).aggregate(total=Sum('amount'))['total']
    assert old_sum == new_sum

    # 3. 샘플 데이터 상세 비교
    for cashbook in CashBook.objects.order_by('?')[:1000]:
        transaction = CompanyBankTransaction.objects.get(
            legacy_id=cashbook.id
        )
        assert_transaction_matches(cashbook, transaction)
```

#### 비즈니스 로직 검증
```python
def validate_business_logic():
    """핵심 비즈니스 로직 동작 검증"""

    # 1. 연체 가산금 계산
    for contract in Contract.objects.filter(status='ACTIVE')[:100]:
        old_penalty = calculate_penalty_old(contract)
        new_penalty = calculate_penalty_new(contract)
        assert old_penalty == new_penalty

    # 2. 선납 할인 계산
    # 3. 잔액 계산
    # 4. 보고서 데이터 비교
```

### 3. 성능 비교 검증

```python
def performance_comparison():
    """기존 시스템과 신규 시스템 성능 비교"""

    test_cases = [
        'transaction_list_view',
        'monthly_summary_report',
        'contract_payment_history',
        'bulk_transaction_import'
    ]

    for test_case in test_cases:
        old_time = benchmark_old_system(test_case)
        new_time = benchmark_new_system(test_case)

        improvement = (old_time - new_time) / old_time * 100
        assert improvement >= -10, f"{test_case}: 성능 저하 {improvement:.1f}%"
```

## 🎛️ 모니터링 및 운영

### 1. 실시간 모니터링

#### 시스템 메트릭
- **응답시간**: API 응답시간 < 500ms 유지
- **처리량**: 초당 거래 처리 건수
- **오류율**: 전체 요청 대비 오류 비율 < 0.1%
- **데이터 동기화**: 지연시간 < 1초

#### 비즈니스 메트릭
- **데이터 무결성**: 일일 무결성 체크 통과율 100%
- **사용자 만족도**: 응답시간 및 오류 기반 점수
- **기능 사용률**: 신규 기능별 사용 통계

### 2. 알림 시스템

#### 임계 상황 알림
```python
# 데이터 동기화 지연 알림
if sync_delay > 30:  # 30초
    send_alert("데이터 동기화 지연 발생", level="WARNING")

# 오류율 급증 알림
if error_rate > 1:  # 1%
    send_alert("오류율 임계치 초과", level="CRITICAL")

# 성능 저하 알림
if avg_response_time > 1000:  # 1초
    send_alert("응답시간 저하", level="WARNING")
```

### 3. 운영 대시보드

#### 실시간 현황판
- 시스템 상태 (정상/경고/장애)
- 실시간 트래픽 현황
- 데이터 동기화 상태
- 최근 오류 로그

#### 일일/주간 리포트
- 처리량 통계
- 성능 추이
- 오류 분석
- 사용자 피드백 요약

## 🎯 성공 지표 및 KPI

### 기술적 지표

#### 코드 품질
- **순환 복잡도**: < 10 (Cyclomatic Complexity)
- **코드 커버리지**: > 90%
- **중복 코드율**: < 5%
- **기술 부채 지수**: 매월 5% 개선

#### 성능 지표
- **응답시간**: 95%ile < 500ms
- **처리량**: 기존 대비 100% 이상 유지
- **메모리 사용량**: 기존 대비 110% 이하
- **DB 쿼리 수**: 주요 화면별 10개 이하

#### 안정성 지표
- **가용성**: 99.9% (월 다운타임 < 45분)
- **데이터 무결성**: 100% (오차 0건)
- **복구 시간**: MTTR < 30분
- **오류율**: < 0.1%

### 비즈니스 지표

#### 사용자 경험
- **페이지 로딩 시간**: < 2초
- **사용자 만족도**: 4.5/5.0 이상
- **기능 완성도**: 기존 기능 100% 호환
- **학습 곡선**: 기존 사용자 재교육 불필요

#### 운영 효율성
- **개발 생산성**: 새 기능 개발 시간 50% 단축
- **장애 대응 시간**: 30% 단축
- **코드 리뷰 시간**: 40% 단축
- **배포 빈도**: 주 1회 → 일 1회

### 달성 목표

#### 3개월 후 (Phase 1-2 완료)
- [ ] 신규 아키텍처 기반 모델 및 API 완성
- [ ] 단위 테스트 커버리지 90% 달성
- [ ] 성능 벤치마크 기준 만족

#### 6개월 후 (Phase 3-4 완료)
- [ ] Frontend 완전 교체 완료
- [ ] 데이터 이관 및 검증 완료
- [ ] 병렬 운영 시스템 안정화

#### 9개월 후 (Phase 5 완료)
- [ ] Cash 앱 완전 폐기 완료
- [ ] 모든 성공 지표 달성
- [ ] 신규 기능 개발 속도 50% 향상

## 📖 관련 문서

1. **[아키텍처 설계 가이드](02_architecture_design.md)**: 상세 모델 구조 및 관계
2. **[API 설계 명세서](03_api_specification.md)**: REST API 상세 스펙
3. **[데이터 이관 가이드](04_data_migration_guide.md)**: 단계별 이관 절차
4. **[테스트 전략](05_testing_strategy.md)**: 품질 보증 방법론
5. **[운영 가이드](06_operation_guide.md)**: 모니터링 및 장애 대응
6. **[개발자 가이드](07_developer_guide.md)**: 신규 기능 개발 가이드라인

## 📞 담당자 및 연락처

- **프로젝트 매니저**: [이름] ([이메일])
- **백엔드 리드**: [이름] ([이메일])
- **프론트엔드 리드**: [이름] ([이메일])
- **DevOps 엔지니어**: [이름] ([이메일])
- **QA 엔지니어**: [이름] ([이메일])

---

**문서 버전**: 1.0
**최종 수정일**: 2025-01-20
**다음 검토일**: 2025-02-01