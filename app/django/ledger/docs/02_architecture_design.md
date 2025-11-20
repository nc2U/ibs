# Ledger 앱 아키텍처 설계 가이드

## 🏗️ 전체 아키텍처 개요

### 설계 철학

#### 도메인 주도 설계 (Domain-Driven Design)
- **도메인 분리**: 은행거래, 회계분류, 계약관리를 독립된 도메인으로 분리
- **보편 언어**: 비즈니스 용어를 코드에 직접 반영
- **경계 컨텍스트**: 각 도메인의 명확한 경계 정의

#### 클린 아키텍처 원칙
- **의존성 역전**: 외부 레이어가 내부 레이어에 의존
- **관심사 분리**: UI, 비즈니스 로직, 데이터 계층 분리
- **테스트 용이성**: 각 계층의 독립적 테스트 가능

### 계층 구조

```
┌─────────────────────────────────────────┐
│             Presentation Layer           │
│     (Django Views, Serializers)         │
├─────────────────────────────────────────┤
│             Application Layer            │
│          (Services, Use Cases)          │
├─────────────────────────────────────────┤
│              Domain Layer                │
│     (Models, Business Logic)            │
├─────────────────────────────────────────┤
│           Infrastructure Layer           │
│    (Database, External Services)        │
└─────────────────────────────────────────┘
```

## 📋 도메인 모델 설계

### 1. 은행거래 도메인 (Banking Domain)

#### 핵심 개념
- **거래(Transaction)**: 은행계좌에서 발생하는 모든 입출금
- **계좌(Account)**: 거래가 발생하는 은행계좌
- **거래유형(TransactionType)**: 입금, 출금, 이체 등

#### 모델 구조

```python
# banking/models.py

class BankTransaction(models.Model):
    """은행거래 기본 추상 모델"""

    # 고유 식별자
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='거래ID'
    )

    # 거래 기본 정보
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        validators=[MinValueValidator(1)],
        verbose_name='거래금액'
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=[
            ('INCOME', '입금'),
            ('OUTLAY', '출금'),
            ('TRANSFER', '이체')
        ],
        verbose_name='거래구분'
    )

    deal_date = models.DateField(verbose_name='거래일자')

    # 거래 상세 정보
    bank_account_type = models.CharField(
        max_length=10,
        choices=[
            ('COMPANY', '본사계좌'),
            ('PROJECT', '프로젝트계좌')
        ],
        verbose_name='계좌구분'
    )

    bank_account_id = models.PositiveIntegerField(verbose_name='계좌ID')

    # 거래 상태 및 참조
    status = models.CharField(
        max_length=10,
        choices=[
            ('PENDING', '대기'),
            ('CONFIRMED', '확정'),
            ('CANCELLED', '취소')
        ],
        default='CONFIRMED',
        verbose_name='거래상태'
    )

    reference_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='거래번호',
        help_text='은행 거래번호 또는 참조번호'
    )

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='등록자'
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['deal_date', 'transaction_type']),
            models.Index(fields=['status', 'created_at']),
        ]

    def clean(self):
        """모델 수준 검증"""
        if self.amount <= 0:
            raise ValidationError('거래금액은 0보다 커야 합니다.')

        if self.deal_date > timezone.now().date():
            raise ValidationError('미래 날짜로 거래를 등록할 수 없습니다.')

    def __str__(self):
        return f'{self.get_transaction_type_display()} {self.amount:,}원 ({self.deal_date})'


class CompanyBankTransaction(BankTransaction):
    """본사 은행거래"""

    company = models.ForeignKey(
        'company.Company',
        on_delete=models.PROTECT,
        verbose_name='회사'
    )

    # 본사 특화 필드
    department = models.ForeignKey(
        'company.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='관리부서'
    )

    class Meta:
        verbose_name = '본사 은행거래'
        verbose_name_plural = '본사 은행거래'
        ordering = ['-deal_date', '-created_at']


class ProjectBankTransaction(BankTransaction):
    """프로젝트 은행거래"""

    project = models.ForeignKey(
        'project.Project',
        on_delete=models.PROTECT,
        verbose_name='프로젝트'
    )

    # 프로젝트 특화 필드
    is_imprest = models.BooleanField(
        default=False,
        verbose_name='운영비 여부',
        help_text='프로젝트 운영비 계좌 거래 여부'
    )

    class Meta:
        verbose_name = '프로젝트 은행거래'
        verbose_name_plural = '프로젝트 은행거래'
        ordering = ['-deal_date', '-created_at']
```

#### 비즈니스 로직

```python
# banking/services.py

class BankingService:
    """은행거래 관련 비즈니스 로직"""

    @staticmethod
    def create_company_transaction(company_id, account_id, amount,
                                 transaction_type, deal_date, creator):
        """본사 거래 생성"""

        # 비즈니스 규칙 검증
        if not Company.objects.filter(id=company_id, is_active=True).exists():
            raise ValidationError('활성화된 회사를 찾을 수 없습니다.')

        if not CompanyBankAccount.objects.filter(
            id=account_id,
            company_id=company_id,
            inactive=False
        ).exists():
            raise ValidationError('유효한 계좌를 찾을 수 없습니다.')

        # 거래 생성
        transaction = CompanyBankTransaction.objects.create(
            company_id=company_id,
            bank_account_type='COMPANY',
            bank_account_id=account_id,
            amount=amount,
            transaction_type=transaction_type,
            deal_date=deal_date,
            creator=creator
        )

        return transaction

    @staticmethod
    def get_account_balance(account_type, account_id, as_of_date=None):
        """계좌 잔액 조회"""

        if as_of_date is None:
            as_of_date = timezone.now().date()

        if account_type == 'COMPANY':
            transactions = CompanyBankTransaction.objects.filter(
                bank_account_id=account_id,
                deal_date__lte=as_of_date,
                status='CONFIRMED'
            )
        else:  # PROJECT
            transactions = ProjectBankTransaction.objects.filter(
                bank_account_id=account_id,
                deal_date__lte=as_of_date,
                status='CONFIRMED'
            )

        # 잔액 계산
        balance = 0
        for tx in transactions:
            if tx.transaction_type == 'INCOME':
                balance += tx.amount
            else:  # OUTLAY
                balance -= tx.amount

        return balance
```

### 2. 회계분류 도메인 (Accounting Domain)

#### 핵심 개념
- **회계항목(AccountingEntry)**: 거래의 회계적 분류 정보
- **계정(Account)**: 회계 과목 및 세부 분류
- **증빙(Evidence)**: 거래의 증빙 유형

#### 모델 구조

```python
# accounting/models.py

class AccountingEntry(models.Model):
    """회계분류 기본 추상 모델"""

    # 연결된 거래 (Polymorphic 관계)
    transaction_id = models.UUIDField(verbose_name='거래ID')
    transaction_type = models.CharField(
        max_length=10,
        choices=[
            ('COMPANY', 'CompanyBankTransaction'),
            ('PROJECT', 'ProjectBankTransaction')
        ],
        verbose_name='거래모델구분'
    )

    # 회계 분류
    sort = models.ForeignKey(
        'ibs.AccountSort',
        on_delete=models.PROTECT,
        verbose_name='구분'
    )

    account_code = models.CharField(
        max_length=10,
        verbose_name='계정코드'
    )

    # 거래 설명
    content = models.CharField(
        max_length=100,
        verbose_name='적요',
        help_text='거래 내용 설명'
    )

    trader = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='거래처'
    )

    note = models.TextField(
        blank=True,
        verbose_name='비고'
    )

    # 증빙 정보
    evidence_type = models.CharField(
        max_length=2,
        choices=[
            ('0', '증빙없음'),
            ('1', '세금계산서'),
            ('2', '계산서(면세)'),
            ('3', '카드전표/현금영수증'),
            ('4', '간이영수증'),
            ('5', '거래명세서'),
            ('6', '입금표'),
            ('7', '지출결의서'),
        ],
        default='0',
        verbose_name='증빙구분'
    )

    evidence_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='증빙번호'
    )

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['account_code', 'created_at']),
            models.Index(fields=['sort', 'evidence_type']),
        ]

    @property
    def related_transaction(self):
        """연결된 거래 객체 반환"""
        if self.transaction_type == 'COMPANY':
            return CompanyBankTransaction.objects.filter(
                transaction_id=self.transaction_id
            ).first()
        else:
            return ProjectBankTransaction.objects.filter(
                transaction_id=self.transaction_id
            ).first()

    def clean(self):
        """모델 수준 검증"""
        # 거래 존재 여부 확인
        transaction = self.related_transaction
        if not transaction:
            raise ValidationError('연결된 거래를 찾을 수 없습니다.')

        # 계정코드 유효성 확인
        if not self.account_code:
            raise ValidationError('계정코드는 필수입니다.')


class CompanyAccountingEntry(AccountingEntry):
    """본사 회계분류"""

    company = models.ForeignKey(
        'company.Company',
        on_delete=models.PROTECT,
        verbose_name='회사'
    )

    # 본사 계정 체계
    account_d1 = models.ForeignKey(
        'ibs.AccountSubD1',
        on_delete=models.PROTECT,
        verbose_name='계정대분류'
    )

    account_d2 = models.ForeignKey(
        'ibs.AccountSubD2',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='계정중분류'
    )

    account_d3 = models.ForeignKey(
        'ibs.AccountSubD3',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='계정소분류'
    )

    class Meta:
        verbose_name = '본사 회계분류'
        verbose_name_plural = '본사 회계분류'


class ProjectAccountingEntry(AccountingEntry):
    """프로젝트 회계분류"""

    project = models.ForeignKey(
        'project.Project',
        on_delete=models.PROTECT,
        verbose_name='프로젝트'
    )

    # 프로젝트 계정 체계
    project_account_d2 = models.ForeignKey(
        'ibs.ProjectAccountD2',
        on_delete=models.PROTECT,
        verbose_name='프로젝트계정'
    )

    project_account_d3 = models.ForeignKey(
        'ibs.ProjectAccountD3',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='프로젝트세부계정'
    )

    class Meta:
        verbose_name = '프로젝트 회계분류'
        verbose_name_plural = '프로젝트 회계분류'
```

### 3. 계약관련 도메인 (Contract Domain)

#### 핵심 개념
- **계약수납(ContractPayment)**: 계약과 관련된 분양대금 수납
- **회차정보(InstallmentOrder)**: 분할납부 회차
- **환불정보(RefundInfo)**: 계약 해지 시 환불 처리

#### 모델 구조

```python
# contract_payment/models.py

class ContractPayment(models.Model):
    """계약 관련 수납/환불 정보 (프로젝트 전용)"""

    # 연결된 거래
    transaction_id = models.UUIDField(
        verbose_name='거래ID',
        help_text='ProjectBankTransaction의 transaction_id와 연결'
    )

    # 프로젝트 및 계약 정보
    project = models.ForeignKey(
        'project.Project',
        on_delete=models.PROTECT,
        verbose_name='프로젝트'
    )

    contract = models.ForeignKey(
        'contract.Contract',
        on_delete=models.PROTECT,
        verbose_name='계약'
    )

    # 수납 회차 정보
    installment_order = models.ForeignKey(
        'payment.InstallmentPaymentOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='납부회차',
        help_text='분할납부인 경우 해당 회차'
    )

    # 수납/환불 구분
    payment_type = models.CharField(
        max_length=10,
        choices=[
            ('PAYMENT', '수납'),
            ('REFUND', '환불'),
            ('ADJUSTMENT', '조정')
        ],
        default='PAYMENT',
        verbose_name='구분'
    )

    # 환불 관련 정보 (환불인 경우만)
    refund_contractor = models.ForeignKey(
        'contract.Contractor',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='환불계약자',
        help_text='환불 시 해당 계약자'
    )

    refund_reason = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='환불사유'
    )

    # 특수 용도
    is_special_purpose = models.BooleanField(
        default=False,
        verbose_name='특수목적',
        help_text='운영비, 대출금 등 특수 목적 거래'
    )

    special_purpose_type = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('IMPREST', '운영비'),
            ('LOAN', '대출금'),
            ('GUARANTEE', '보증금'),
            ('OTHERS', '기타')
        ],
        verbose_name='특수목적구분'
    )

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='등록자'
    )

    class Meta:
        verbose_name = '계약수납정보'
        verbose_name_plural = '계약수납정보'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['contract', 'payment_type']),
            models.Index(fields=['installment_order', 'created_at']),
        ]

    @property
    def related_transaction(self):
        """연결된 프로젝트 거래 반환"""
        return ProjectBankTransaction.objects.filter(
            transaction_id=self.transaction_id
        ).first()

    def clean(self):
        """모델 수준 검증"""
        # 환불인 경우 환불 계약자 필수
        if self.payment_type == 'REFUND' and not self.refund_contractor:
            raise ValidationError('환불 시 환불계약자를 지정해야 합니다.')

        # 계약과 프로젝트 일치 확인
        if self.contract.project_id != self.project_id:
            raise ValidationError('계약의 프로젝트와 일치하지 않습니다.')

        # 회차 정보 일치 확인
        if self.installment_order and self.installment_order.project_id != self.project_id:
            raise ValidationError('회차 정보의 프로젝트와 일치하지 않습니다.')

    def get_payment_amount(self):
        """수납 금액 조회"""
        transaction = self.related_transaction
        if transaction:
            return transaction.amount
        return 0

    def calculate_late_penalty(self):
        """연체 가산금 계산"""
        if not self.installment_order:
            return None

        from _utils.payment_adjustment import calculate_late_penalty
        return calculate_late_penalty(self)

    def is_prepayment_eligible(self):
        """선납 할인 대상 여부"""
        return (
            self.payment_type == 'PAYMENT' and
            self.installment_order and
            self.installment_order.is_prep_discount
        )
```

### 4. 거래분할 도메인 (Transaction Split)

#### 핵심 개념
- **거래분할(TransactionSplit)**: 하나의 은행거래를 여러 회계항목으로 분할
- **분할항목(SplitItem)**: 분할된 개별 항목

#### 모델 구조

```python
# transaction_split/models.py

class TransactionSplit(models.Model):
    """거래 분할 정보 관리"""

    # 원본 거래 정보
    parent_transaction_id = models.UUIDField(
        verbose_name='원본거래ID',
        help_text='분할되는 원본 거래의 ID'
    )

    parent_transaction_type = models.CharField(
        max_length=10,
        choices=[
            ('COMPANY', 'CompanyBankTransaction'),
            ('PROJECT', 'ProjectBankTransaction')
        ],
        verbose_name='원본거래모델'
    )

    # 분할 메타데이터
    split_reason = models.CharField(
        max_length=200,
        verbose_name='분할사유',
        help_text='거래를 분할하는 이유'
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='총금액',
        help_text='원본 거래의 총 금액'
    )

    split_count = models.PositiveSmallIntegerField(
        verbose_name='분할개수',
        validators=[MinValueValidator(2)]
    )

    # 분할 상태
    status = models.CharField(
        max_length=10,
        choices=[
            ('DRAFT', '임시저장'),
            ('CONFIRMED', '확정'),
            ('CANCELLED', '취소')
        ],
        default='DRAFT',
        verbose_name='상태'
    )

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='등록자'
    )

    class Meta:
        verbose_name = '거래분할'
        verbose_name_plural = '거래분할'
        indexes = [
            models.Index(fields=['parent_transaction_id']),
            models.Index(fields=['status', 'created_at']),
        ]

    @property
    def parent_transaction(self):
        """원본 거래 객체 반환"""
        if self.parent_transaction_type == 'COMPANY':
            return CompanyBankTransaction.objects.filter(
                transaction_id=self.parent_transaction_id
            ).first()
        else:
            return ProjectBankTransaction.objects.filter(
                transaction_id=self.parent_transaction_id
            ).first()

    def clean(self):
        """모델 수준 검증"""
        # 분할 항목의 합계가 총액과 일치하는지 확인
        if self.pk:  # 업데이트인 경우만
            split_items_total = self.split_items.aggregate(
                total=Sum('amount')
            )['total'] or 0

            if split_items_total != self.total_amount:
                raise ValidationError('분할 항목의 합계가 총액과 일치하지 않습니다.')

    def confirm_split(self):
        """분할 확정 처리"""
        if self.status != 'DRAFT':
            raise ValidationError('임시저장 상태에서만 확정할 수 있습니다.')

        # 분할 항목 검증
        if not self.split_items.exists():
            raise ValidationError('분할 항목이 없습니다.')

        self.status = 'CONFIRMED'
        self.save()

        # 각 분할 항목에 대해 회계분류 생성
        for item in self.split_items.all():
            item.create_accounting_entry()


class TransactionSplitItem(models.Model):
    """거래 분할 개별 항목"""

    split = models.ForeignKey(
        TransactionSplit,
        on_delete=models.CASCADE,
        related_name='split_items',
        verbose_name='분할'
    )

    # 분할 항목 정보
    sequence = models.PositiveSmallIntegerField(
        verbose_name='순서',
        validators=[MinValueValidator(1)]
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        validators=[MinValueValidator(1)],
        verbose_name='금액'
    )

    # 회계 분류 정보
    account_code = models.CharField(
        max_length=10,
        verbose_name='계정코드'
    )

    content = models.CharField(
        max_length=100,
        verbose_name='적요'
    )

    trader = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='거래처'
    )

    note = models.TextField(
        blank=True,
        verbose_name='비고'
    )

    # 연결된 회계분류 (분할 확정 후 생성)
    accounting_entry_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='회계분류ID',
        help_text='생성된 AccountingEntry의 ID'
    )

    class Meta:
        verbose_name = '거래분할항목'
        verbose_name_plural = '거래분할항목'
        unique_together = [['split', 'sequence']]
        ordering = ['sequence']

    def create_accounting_entry(self):
        """이 분할 항목에 대한 회계분류 생성"""
        if self.split.parent_transaction_type == 'COMPANY':
            entry = CompanyAccountingEntry.objects.create(
                transaction_id=self.split.parent_transaction_id,
                transaction_type='COMPANY',
                company=self.split.parent_transaction.company,
                account_code=self.account_code,
                content=self.content,
                trader=self.trader,
                note=self.note,
                # ... 기타 필드
            )
        else:
            entry = ProjectAccountingEntry.objects.create(
                transaction_id=self.split.parent_transaction_id,
                transaction_type='PROJECT',
                project=self.split.parent_transaction.project,
                account_code=self.account_code,
                content=self.content,
                trader=self.trader,
                note=self.note,
                # ... 기타 필드
            )

        # 생성된 회계분류 ID 저장
        self.accounting_entry_id = entry.pk
        self.save(update_fields=['accounting_entry_id'])

        return entry
```

## 🔗 도메인 간 통합 서비스

### 통합 거래 서비스 (Integrated Transaction Service)

```python
# services/transaction_service.py

class TransactionService:
    """거래 관련 통합 비즈니스 로직"""

    @transaction.atomic
    def create_simple_company_transaction(self, company_id, account_id,
                                        amount, transaction_type, deal_date,
                                        accounting_data, creator):
        """간단한 본사 거래 생성 (1:1 관계)"""

        # 1. 은행거래 생성
        bank_transaction = BankingService.create_company_transaction(
            company_id=company_id,
            account_id=account_id,
            amount=amount,
            transaction_type=transaction_type,
            deal_date=deal_date,
            creator=creator
        )

        # 2. 회계분류 생성
        accounting_entry = CompanyAccountingEntry.objects.create(
            transaction_id=bank_transaction.transaction_id,
            transaction_type='COMPANY',
            company_id=company_id,
            **accounting_data
        )

        return {
            'transaction': bank_transaction,
            'accounting': accounting_entry
        }

    @transaction.atomic
    def create_contract_payment(self, project_id, contract_id, account_id,
                              amount, deal_date, installment_order_id,
                              accounting_data, creator):
        """계약 수납 거래 생성 (프로젝트 + 계약정보)"""

        # 1. 프로젝트 은행거래 생성
        bank_transaction = ProjectBankTransaction.objects.create(
            project_id=project_id,
            bank_account_type='PROJECT',
            bank_account_id=account_id,
            amount=amount,
            transaction_type='INCOME',
            deal_date=deal_date,
            creator=creator
        )

        # 2. 프로젝트 회계분류 생성
        accounting_entry = ProjectAccountingEntry.objects.create(
            transaction_id=bank_transaction.transaction_id,
            transaction_type='PROJECT',
            project_id=project_id,
            **accounting_data
        )

        # 3. 계약 수납정보 생성
        contract_payment = ContractPayment.objects.create(
            transaction_id=bank_transaction.transaction_id,
            project_id=project_id,
            contract_id=contract_id,
            installment_order_id=installment_order_id,
            payment_type='PAYMENT',
            creator=creator
        )

        return {
            'transaction': bank_transaction,
            'accounting': accounting_entry,
            'contract_payment': contract_payment
        }

    @transaction.atomic
    def create_split_transaction(self, transaction_data, split_items_data, creator):
        """분할 거래 생성"""

        # 1. 원본 거래 생성
        if transaction_data['account_type'] == 'COMPANY':
            bank_transaction = CompanyBankTransaction.objects.create(
                **transaction_data,
                creator=creator
            )
            transaction_type = 'COMPANY'
        else:
            bank_transaction = ProjectBankTransaction.objects.create(
                **transaction_data,
                creator=creator
            )
            transaction_type = 'PROJECT'

        # 2. 거래분할 정보 생성
        total_split_amount = sum(item['amount'] for item in split_items_data)

        transaction_split = TransactionSplit.objects.create(
            parent_transaction_id=bank_transaction.transaction_id,
            parent_transaction_type=transaction_type,
            split_reason=f"거래를 {len(split_items_data)}개 항목으로 분할",
            total_amount=bank_transaction.amount,
            split_count=len(split_items_data),
            creator=creator
        )

        # 3. 분할 항목들 생성
        split_items = []
        for i, item_data in enumerate(split_items_data, 1):
            split_item = TransactionSplitItem.objects.create(
                split=transaction_split,
                sequence=i,
                **item_data
            )
            split_items.append(split_item)

        # 4. 분할 확정
        transaction_split.confirm_split()

        return {
            'transaction': bank_transaction,
            'split': transaction_split,
            'split_items': split_items
        }

    def get_transaction_summary(self, transaction_id, transaction_type):
        """거래 종합 정보 조회"""

        # 기본 거래 정보
        if transaction_type == 'COMPANY':
            transaction = CompanyBankTransaction.objects.get(
                transaction_id=transaction_id
            )
        else:
            transaction = ProjectBankTransaction.objects.get(
                transaction_id=transaction_id
            )

        # 회계분류 정보
        if transaction_type == 'COMPANY':
            accounting_entries = CompanyAccountingEntry.objects.filter(
                transaction_id=transaction_id
            )
        else:
            accounting_entries = ProjectAccountingEntry.objects.filter(
                transaction_id=transaction_id
            )

        # 계약정보 (프로젝트인 경우만)
        contract_payment = None
        if transaction_type == 'PROJECT':
            contract_payment = ContractPayment.objects.filter(
                transaction_id=transaction_id
            ).first()

        # 분할정보
        transaction_split = TransactionSplit.objects.filter(
            parent_transaction_id=transaction_id
        ).first()

        return {
            'transaction': transaction,
            'accounting_entries': accounting_entries,
            'contract_payment': contract_payment,
            'split_info': transaction_split,
            'is_split': transaction_split is not None
        }
```

### 조회 서비스 (Query Service)

```python
# services/query_service.py

class LedgerQueryService:
    """장부 조회 관련 서비스"""

    @staticmethod
    def get_company_transactions(company_id, start_date, end_date,
                               account_codes=None, limit=None):
        """본사 거래 조회"""

        # 기본 쿼리
        transactions = CompanyBankTransaction.objects.filter(
            company_id=company_id,
            deal_date__range=[start_date, end_date],
            status='CONFIRMED'
        ).select_related('company')

        # 회계분류 조인
        transactions = transactions.prefetch_related(
            Prefetch(
                'companyaccountingentry_set',
                queryset=CompanyAccountingEntry.objects.select_related(
                    'account_d1', 'account_d2', 'account_d3'
                )
            )
        )

        # 계정코드 필터
        if account_codes:
            transactions = transactions.filter(
                companyaccountingentry__account_code__in=account_codes
            )

        # 정렬 및 제한
        transactions = transactions.order_by('-deal_date', '-created_at')
        if limit:
            transactions = transactions[:limit]

        return transactions

    @staticmethod
    def get_project_cashflow(project_id, start_date, end_date):
        """프로젝트 현금흐름 조회"""

        transactions = ProjectBankTransaction.objects.filter(
            project_id=project_id,
            deal_date__range=[start_date, end_date],
            status='CONFIRMED'
        ).select_related('project')

        # 관련 정보 프리페치
        transactions = transactions.prefetch_related(
            'projectaccountingentry_set__project_account_d2',
            'contractpayment_set__contract__unit_type',
            'contractpayment_set__installment_order'
        )

        # 월별 집계
        monthly_summary = transactions.extra(
            select={'month': "DATE_FORMAT(deal_date, '%%Y-%%m')"}
        ).values('month', 'transaction_type').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('month', 'transaction_type')

        return {
            'transactions': transactions,
            'monthly_summary': monthly_summary
        }

    @staticmethod
    def get_contract_payment_history(contract_id):
        """계약별 수납 이력 조회"""

        payments = ContractPayment.objects.filter(
            contract_id=contract_id
        ).select_related(
            'contract',
            'installment_order',
            'refund_contractor'
        )

        # 연관 거래정보 포함
        payment_details = []
        for payment in payments:
            transaction = payment.related_transaction
            accounting = ProjectAccountingEntry.objects.filter(
                transaction_id=payment.transaction_id
            ).first()

            payment_details.append({
                'payment': payment,
                'transaction': transaction,
                'accounting': accounting,
                'late_penalty': payment.calculate_late_penalty()
            })

        return payment_details
```

## 📊 성능 최적화 전략

### 1. 데이터베이스 최적화

#### 인덱스 전략
```python
# models.py 내 인덱스 설정

class BankTransaction(models.Model):
    class Meta:
        indexes = [
            # 단일 컬럼 인덱스
            models.Index(fields=['transaction_id']),  # UUID 조회용
            models.Index(fields=['deal_date']),        # 날짜 범위 조회용
            models.Index(fields=['status']),           # 상태별 필터링용

            # 복합 인덱스 (조회 패턴 기반)
            models.Index(fields=['deal_date', 'transaction_type']),  # 날짜+유형 조회
            models.Index(fields=['status', 'created_at']),           # 상태+생성일 정렬
            models.Index(fields=['bank_account_id', 'deal_date']),   # 계좌별 거래 조회
        ]

class AccountingEntry(models.Model):
    class Meta:
        indexes = [
            # 거래 연결 조회용
            models.Index(fields=['transaction_id']),

            # 회계 집계용
            models.Index(fields=['account_code', 'created_at']),
            models.Index(fields=['sort', 'evidence_type']),

            # 복합 조회용
            models.Index(fields=['transaction_type', 'account_code']),
        ]
```

#### 쿼리 최적화
```python
# 효율적인 쿼리 패턴

# 1. Select Related 사용
def get_transactions_with_details(company_id):
    return CompanyBankTransaction.objects.filter(
        company_id=company_id
    ).select_related(
        'company',
        'creator'
    ).prefetch_related(
        Prefetch(
            'companyaccountingentry_set',
            queryset=CompanyAccountingEntry.objects.select_related(
                'account_d1', 'account_d2', 'account_d3'
            )
        )
    )

# 2. 집계 쿼리 최적화
def get_monthly_summary(project_id, year):
    return ProjectBankTransaction.objects.filter(
        project_id=project_id,
        deal_date__year=year
    ).extra(
        select={'month': "EXTRACT(month FROM deal_date)"}
    ).values('month', 'transaction_type').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    )

# 3. 배치 처리
def bulk_create_transactions(transaction_data_list):
    transactions = [
        CompanyBankTransaction(**data)
        for data in transaction_data_list
    ]
    return CompanyBankTransaction.objects.bulk_create(transactions)
```

### 2. 캐싱 전략

```python
# services/cache_service.py

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

class LedgerCacheService:
    """장부 관련 캐싱 서비스"""

    CACHE_TIMEOUT = {
        'account_balance': 300,      # 5분
        'monthly_summary': 3600,     # 1시간
        'yearly_report': 86400,      # 24시간
    }

    @staticmethod
    def get_account_balance(account_type, account_id, date=None):
        """계좌 잔액 캐싱"""
        cache_key = f"balance_{account_type}_{account_id}_{date or 'current'}"

        balance = cache.get(cache_key)
        if balance is None:
            balance = BankingService.get_account_balance(
                account_type, account_id, date
            )
            cache.set(cache_key, balance, LedgerCacheService.CACHE_TIMEOUT['account_balance'])

        return balance

    @staticmethod
    def invalidate_account_cache(account_type, account_id):
        """계좌 관련 캐시 무효화"""
        pattern = f"balance_{account_type}_{account_id}_*"
        cache.delete_pattern(pattern)

    @staticmethod
    def get_monthly_summary(project_id, year_month):
        """월별 요약 캐싱"""
        cache_key = f"monthly_summary_{project_id}_{year_month}"

        summary = cache.get(cache_key)
        if summary is None:
            summary = LedgerQueryService.get_monthly_summary(
                project_id, year_month
            )
            cache.set(cache_key, summary, LedgerCacheService.CACHE_TIMEOUT['monthly_summary'])

        return summary

# signals.py - 캐시 무효화
@receiver(post_save, sender=CompanyBankTransaction)
def invalidate_company_cache(sender, instance, **kwargs):
    LedgerCacheService.invalidate_account_cache(
        'COMPANY', instance.bank_account_id
    )

@receiver(post_save, sender=ProjectBankTransaction)
def invalidate_project_cache(sender, instance, **kwargs):
    LedgerCacheService.invalidate_account_cache(
        'PROJECT', instance.bank_account_id
    )
```

### 3. 비동기 처리

```python
# tasks.py - Celery 태스크

@shared_task
def process_bulk_transactions(transaction_data_list):
    """대량 거래 비동기 처리"""

    try:
        with transaction.atomic():
            for tx_data in transaction_data_list:
                TransactionService.create_simple_company_transaction(**tx_data)

        return {
            'status': 'SUCCESS',
            'processed': len(transaction_data_list)
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': str(e)
        }

@shared_task
def generate_monthly_report(company_id, year, month):
    """월별 보고서 생성"""

    # 시간이 오래 걸리는 보고서 생성 로직
    transactions = LedgerQueryService.get_company_transactions(
        company_id=company_id,
        start_date=date(year, month, 1),
        end_date=date(year, month, calendar.monthrange(year, month)[1])
    )

    # 보고서 데이터 생성 및 파일 저장
    report_data = generate_report_data(transactions)
    file_path = save_report_file(report_data, company_id, year, month)

    return file_path

@shared_task
def sync_legacy_data(batch_size=1000):
    """기존 데이터 동기화"""

    # Cash 앱 데이터를 Ledger 앱으로 동기화
    from cash.models import CashBook

    cashbooks = CashBook.objects.filter(
        migrated_to_ledger=False
    )[:batch_size]

    migrated_count = 0
    for cashbook in cashbooks:
        try:
            migrate_cashbook_to_ledger(cashbook)
            cashbook.migrated_to_ledger = True
            cashbook.save()
            migrated_count += 1
        except Exception as e:
            logger.error(f"Migration failed for CashBook {cashbook.id}: {e}")

    return migrated_count
```

## 🔒 보안 및 권한 관리

### 권한 기반 접근 제어

```python
# permissions.py

from rest_framework.permissions import BasePermission

class TransactionPermission(BasePermission):
    """거래 관련 권한 검증"""

    def has_permission(self, request, view):
        """기본 권한 확인"""
        if not request.user.is_authenticated:
            return False

        # 조회 권한
        if view.action in ['list', 'retrieve']:
            return request.user.has_perm('ledger.view_transaction')

        # 생성 권한
        if view.action == 'create':
            return request.user.has_perm('ledger.add_transaction')

        # 수정 권한
        if view.action in ['update', 'partial_update']:
            return request.user.has_perm('ledger.change_transaction')

        # 삭제 권한
        if view.action == 'destroy':
            return request.user.has_perm('ledger.delete_transaction')

        return False

    def has_object_permission(self, request, view, obj):
        """객체별 권한 확인"""
        # 소속 회사/프로젝트 확인
        if hasattr(obj, 'company'):
            return obj.company in request.user.accessible_companies.all()

        if hasattr(obj, 'project'):
            return obj.project in request.user.accessible_projects.all()

        return False

class CompanyDataPermission(BasePermission):
    """본사 데이터 접근 권한"""

    def has_permission(self, request, view):
        return request.user.has_perm('ledger.access_company_data')

    def has_object_permission(self, request, view, obj):
        # 본인이 속한 회사 데이터만 접근 가능
        user_companies = request.user.profile.companies.all()
        return obj.company in user_companies

class ProjectDataPermission(BasePermission):
    """프로젝트 데이터 접근 권한"""

    def has_permission(self, request, view):
        return request.user.has_perm('ledger.access_project_data')

    def has_object_permission(self, request, view, obj):
        # 담당 프로젝트 데이터만 접근 가능
        user_projects = request.user.profile.projects.all()
        return obj.project in user_projects
```

### 감사 로깅

```python
# audit/models.py

class AuditLog(models.Model):
    """감사 로그"""

    # 사용자 정보
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='사용자'
    )

    user_ip = models.GenericIPAddressField(verbose_name='접속IP')

    # 액션 정보
    action = models.CharField(
        max_length=20,
        choices=[
            ('CREATE', '생성'),
            ('UPDATE', '수정'),
            ('DELETE', '삭제'),
            ('VIEW', '조회')
        ],
        verbose_name='액션'
    )

    # 대상 객체
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # 변경 내용
    old_values = models.JSONField(blank=True, null=True, verbose_name='이전값')
    new_values = models.JSONField(blank=True, null=True, verbose_name='신규값')

    # 메타데이터
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '감사로그'
        verbose_name_plural = '감사로그'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]

# audit/signals.py

@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    """모델 저장 시 감사 로그 생성"""

    # 감사 대상 모델인지 확인
    if not issubclass(sender, (BankTransaction, AccountingEntry, ContractPayment)):
        return

    # 현재 요청 정보 가져오기 (middleware에서 설정)
    current_request = getattr(local, 'request', None)
    if not current_request:
        return

    AuditLog.objects.create(
        user=current_request.user,
        user_ip=get_client_ip(current_request),
        action='CREATE' if created else 'UPDATE',
        content_object=instance,
        new_values=model_to_dict(instance),
        old_values=getattr(instance, '_original_values', None)
    )
```

---

**문서 버전**: 1.0
**최종 수정일**: 2025-01-20
**다음 검토일**: 2025-02-01