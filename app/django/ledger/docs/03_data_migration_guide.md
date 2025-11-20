# 데이터 이관 가이드

## 🎯 이관 목표 및 원칙

### 이관 목표
- **무중단 서비스**: 운영 서비스 중단 없이 점진적 이관
- **데이터 무결성**: 100% 데이터 정확성 보장
- **성능 유지**: 기존 성능 수준 이상 유지
- **롤백 가능**: 문제 발생 시 즉시 원복 가능

### 이관 원칙
- **단계적 접근**: Phase별 점진적 이관으로 리스크 최소화
- **검증 우선**: 각 단계마다 철저한 검증 후 다음 단계 진행
- **병렬 운영**: 기존 시스템과 신규 시스템 동시 운영으로 안정성 확보
- **실시간 모니터링**: 이관 과정 전반에 대한 실시간 모니터링

## 📊 이관 대상 데이터 분석

### 기존 Cash 앱 데이터 구조

#### CashBook (본사 입출금)
```sql
-- 데이터 규모 분석
SELECT
    COUNT(*) as total_records,
    MIN(deal_date) as earliest_date,
    MAX(deal_date) as latest_date,
    SUM(CASE WHEN income IS NOT NULL THEN income ELSE 0 END) as total_income,
    SUM(CASE WHEN outlay IS NOT NULL THEN outlay ELSE 0 END) as total_outlay
FROM cash_cashbook;

-- 연도별 데이터 분포
SELECT
    YEAR(deal_date) as year,
    COUNT(*) as records,
    SUM(COALESCE(income, 0) + COALESCE(outlay, 0)) as total_amount
FROM cash_cashbook
GROUP BY YEAR(deal_date)
ORDER BY year;

-- 분할 거래 현황
SELECT
    is_separate,
    COUNT(*) as count,
    COUNT(DISTINCT separated_id) as parent_count
FROM cash_cashbook
GROUP BY is_separate;
```

#### ProjectCashBook (프로젝트 입출금)
```sql
-- 프로젝트별 데이터 분포
SELECT
    p.name as project_name,
    COUNT(pcb.id) as transaction_count,
    SUM(COALESCE(pcb.income, 0)) as total_income,
    SUM(COALESCE(pcb.outlay, 0)) as total_outlay
FROM cash_projectcashbook pcb
JOIN project_project p ON pcb.project_id = p.id
GROUP BY p.id, p.name
ORDER BY transaction_count DESC;

-- 계약 관련 거래 분석
SELECT
    COUNT(*) as total_contract_transactions,
    COUNT(DISTINCT contract_id) as unique_contracts,
    COUNT(DISTINCT installment_order_id) as unique_installments
FROM cash_projectcashbook
WHERE contract_id IS NOT NULL;
```

### 데이터 품질 검증

```sql
-- 데이터 무결성 체크 쿼리들

-- 1. 중복 거래 체크
SELECT deal_date, bank_account_id, income, outlay, COUNT(*)
FROM cash_cashbook
GROUP BY deal_date, bank_account_id, income, outlay
HAVING COUNT(*) > 1;

-- 2. 금액 이상치 체크
SELECT id, deal_date, income, outlay
FROM cash_cashbook
WHERE (income IS NOT NULL AND income <= 0)
   OR (outlay IS NOT NULL AND outlay <= 0)
   OR (income IS NOT NULL AND outlay IS NOT NULL);

-- 3. 분할 거래 일치성 체크
SELECT
    parent.id as parent_id,
    parent.income as parent_income,
    parent.outlay as parent_outlay,
    SUM(child.income) as child_income_sum,
    SUM(child.outlay) as child_outlay_sum
FROM cash_cashbook parent
LEFT JOIN cash_cashbook child ON parent.id = child.separated_id
WHERE parent.is_separate = true AND parent.separated_id IS NULL
GROUP BY parent.id, parent.income, parent.outlay
HAVING (COALESCE(parent.income, 0) != COALESCE(SUM(child.income), 0))
    OR (COALESCE(parent.outlay, 0) != COALESCE(SUM(child.outlay), 0));

-- 4. 외래키 무결성 체크
SELECT COUNT(*) as orphan_records
FROM cash_cashbook cb
LEFT JOIN company_companybankaccount cba ON cb.bank_account_id = cba.id
WHERE cba.id IS NULL;
```

## 🔄 단계별 이관 프로세스

### Phase 1: 읽기 전용 이관 (Read-Only Migration)

#### 목표
- 기존 데이터를 신규 구조로 변환하여 읽기 전용으로 생성
- 데이터 매핑 로직 검증
- 성능 기준선 설정

#### 이관 스크립트

```python
# migration_scripts/phase1_readonly_migration.py

import uuid
from datetime import datetime
from django.db import transaction
from django.core.management.base import BaseCommand

from cash.models import CashBook, ProjectCashBook
from ledger.models import (
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    ContractPayment
)

class Command(BaseCommand):
    help = 'Phase 1: Read-only migration of cash data to ledger'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=1000)
        parser.add_argument('--start-date', type=str, help='YYYY-MM-DD format')
        parser.add_argument('--end-date', type=str, help='YYYY-MM-DD format')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        start_date = options.get('start_date')
        end_date = options.get('end_date')
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write('DRY RUN MODE - No data will be modified')

        # 1. CashBook 이관
        self.migrate_cashbooks(batch_size, start_date, end_date, dry_run)

        # 2. ProjectCashBook 이관
        self.migrate_project_cashbooks(batch_size, start_date, end_date, dry_run)

        # 3. 검증
        self.validate_migration(dry_run)

    def migrate_cashbooks(self, batch_size, start_date, end_date, dry_run):
        """CashBook 데이터 이관"""

        query = CashBook.objects.all()

        if start_date:
            query = query.filter(deal_date__gte=start_date)
        if end_date:
            query = query.filter(deal_date__lte=end_date)

        total_count = query.count()
        self.stdout.write(f'CashBook 이관 시작: 총 {total_count}건')

        processed = 0
        for cashbook_batch in self.batch_queryset(query, batch_size):
            if not dry_run:
                self.process_cashbook_batch(cashbook_batch)

            processed += len(cashbook_batch)
            self.stdout.write(f'CashBook 진행률: {processed}/{total_count}')

    def process_cashbook_batch(self, cashbook_batch):
        """CashBook 배치 처리"""

        with transaction.atomic():
            bank_transactions = []
            accounting_entries = []

            for cashbook in cashbook_batch:
                # 1. 은행거래 생성
                transaction_id = uuid.uuid4()

                bank_transaction = CompanyBankTransaction(
                    transaction_id=transaction_id,
                    company=cashbook.company,
                    amount=cashbook.income or cashbook.outlay or 0,
                    transaction_type='INCOME' if cashbook.income else 'OUTLAY',
                    deal_date=cashbook.deal_date,
                    bank_account_type='COMPANY',
                    bank_account_id=cashbook.bank_account.id,
                    reference_number=f'CASH_{cashbook.id}',
                    created_at=cashbook.created,
                    creator=cashbook.creator,
                    # 이관 추적용 필드
                    legacy_cashbook_id=cashbook.id
                )
                bank_transactions.append(bank_transaction)

                # 2. 회계분류 생성
                accounting_entry = CompanyAccountingEntry(
                    transaction_id=transaction_id,
                    transaction_type='COMPANY',
                    company=cashbook.company,
                    sort=cashbook.sort,
                    account_code=self.get_account_code(cashbook),
                    account_d1=cashbook.account_d1,
                    account_d2=cashbook.account_d2,
                    account_d3=cashbook.account_d3,
                    content=cashbook.content or '',
                    trader=cashbook.trader or '',
                    note=cashbook.note or '',
                    evidence_type=cashbook.evidence or '0',
                    created_at=cashbook.created
                )
                accounting_entries.append(accounting_entry)

            # 배치 생성
            CompanyBankTransaction.objects.bulk_create(bank_transactions)
            CompanyAccountingEntry.objects.bulk_create(accounting_entries)

    def migrate_project_cashbooks(self, batch_size, start_date, end_date, dry_run):
        """ProjectCashBook 데이터 이관"""

        query = ProjectCashBook.objects.select_related(
            'project', 'sort', 'project_account_d2', 'project_account_d3',
            'contract', 'installment_order', 'refund_contractor'
        )

        if start_date:
            query = query.filter(deal_date__gte=start_date)
        if end_date:
            query = query.filter(deal_date__lte=end_date)

        total_count = query.count()
        self.stdout.write(f'ProjectCashBook 이관 시작: 총 {total_count}건')

        processed = 0
        for pcb_batch in self.batch_queryset(query, batch_size):
            if not dry_run:
                self.process_project_cashbook_batch(pcb_batch)

            processed += len(pcb_batch)
            self.stdout.write(f'ProjectCashBook 진행률: {processed}/{total_count}')

    def process_project_cashbook_batch(self, pcb_batch):
        """ProjectCashBook 배치 처리"""

        with transaction.atomic():
            bank_transactions = []
            accounting_entries = []
            contract_payments = []

            for pcb in pcb_batch:
                # 1. 프로젝트 은행거래 생성
                transaction_id = uuid.uuid4()

                bank_transaction = ProjectBankTransaction(
                    transaction_id=transaction_id,
                    project=pcb.project,
                    amount=pcb.income or pcb.outlay or 0,
                    transaction_type='INCOME' if pcb.income else 'OUTLAY',
                    deal_date=pcb.deal_date,
                    bank_account_type='PROJECT',
                    bank_account_id=pcb.bank_account.id,
                    reference_number=f'PCB_{pcb.id}',
                    is_imprest=pcb.is_imprest,
                    created_at=pcb.created,
                    creator=pcb.creator,
                    # 이관 추적용 필드
                    legacy_pcb_id=pcb.id
                )
                bank_transactions.append(bank_transaction)

                # 2. 프로젝트 회계분류 생성
                accounting_entry = ProjectAccountingEntry(
                    transaction_id=transaction_id,
                    transaction_type='PROJECT',
                    project=pcb.project,
                    sort=pcb.sort,
                    account_code=self.get_project_account_code(pcb),
                    project_account_d2=pcb.project_account_d2,
                    project_account_d3=pcb.project_account_d3,
                    content=pcb.content or '',
                    trader=pcb.trader or '',
                    note=pcb.note or '',
                    evidence_type=pcb.evidence or '0',
                    created_at=pcb.created
                )
                accounting_entries.append(accounting_entry)

                # 3. 계약정보 생성 (해당하는 경우만)
                if pcb.contract_id or pcb.installment_order_id:
                    payment_type = 'REFUND' if pcb.refund_contractor else 'PAYMENT'

                    contract_payment = ContractPayment(
                        transaction_id=transaction_id,
                        project=pcb.project,
                        contract=pcb.contract,
                        installment_order=pcb.installment_order,
                        payment_type=payment_type,
                        refund_contractor=pcb.refund_contractor,
                        is_special_purpose=pcb.is_imprest,
                        special_purpose_type='IMPREST' if pcb.is_imprest else '',
                        created_at=pcb.created,
                        creator=pcb.creator
                    )
                    contract_payments.append(contract_payment)

            # 배치 생성
            ProjectBankTransaction.objects.bulk_create(bank_transactions)
            ProjectAccountingEntry.objects.bulk_create(accounting_entries)
            if contract_payments:
                ContractPayment.objects.bulk_create(contract_payments)

    def get_account_code(self, cashbook):
        """CashBook에서 계정코드 추출"""
        if cashbook.account_d3:
            return cashbook.account_d3.code
        elif cashbook.account_d2:
            return cashbook.account_d2.code
        elif cashbook.account_d1:
            return cashbook.account_d1.code
        else:
            return 'UNKNOWN'

    def get_project_account_code(self, pcb):
        """ProjectCashBook에서 계정코드 추출"""
        if pcb.project_account_d3:
            return pcb.project_account_d3.code
        elif pcb.project_account_d2:
            return pcb.project_account_d2.code
        else:
            return 'UNKNOWN'

    def batch_queryset(self, queryset, batch_size):
        """QuerySet을 배치로 나누어 처리"""
        start = 0
        while True:
            batch = list(queryset[start:start + batch_size])
            if not batch:
                break
            yield batch
            start += batch_size

    def validate_migration(self, dry_run):
        """이관 결과 검증"""
        if dry_run:
            return

        self.stdout.write('이관 결과 검증 시작...')

        # 1. 레코드 수 비교
        cashbook_count = CashBook.objects.count()
        company_tx_count = CompanyBankTransaction.objects.count()

        pcb_count = ProjectCashBook.objects.count()
        project_tx_count = ProjectBankTransaction.objects.count()

        self.stdout.write(f'CashBook: {cashbook_count} -> CompanyBankTransaction: {company_tx_count}')
        self.stdout.write(f'ProjectCashBook: {pcb_count} -> ProjectBankTransaction: {project_tx_count}')

        # 2. 금액 합계 비교
        self.validate_amount_totals()

        # 3. 샘플 데이터 상세 검증
        self.validate_sample_data()

    def validate_amount_totals(self):
        """금액 합계 검증"""
        # CashBook vs CompanyBankTransaction
        cb_income_sum = CashBook.objects.aggregate(
            total=models.Sum('income')
        )['total'] or 0

        cb_outlay_sum = CashBook.objects.aggregate(
            total=models.Sum('outlay')
        )['total'] or 0

        cbt_income_sum = CompanyBankTransaction.objects.filter(
            transaction_type='INCOME'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        cbt_outlay_sum = CompanyBankTransaction.objects.filter(
            transaction_type='OUTLAY'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        assert cb_income_sum == cbt_income_sum, f"입금 합계 불일치: {cb_income_sum} != {cbt_income_sum}"
        assert cb_outlay_sum == cbt_outlay_sum, f"출금 합계 불일치: {cb_outlay_sum} != {cbt_outlay_sum}"

        self.stdout.write('✓ 금액 합계 검증 통과')

    def validate_sample_data(self):
        """샘플 데이터 상세 검증"""
        sample_count = min(100, CashBook.objects.count())
        sample_cashbooks = CashBook.objects.order_by('?')[:sample_count]

        for cashbook in sample_cashbooks:
            # 해당 CashBook에서 생성된 거래 찾기
            company_tx = CompanyBankTransaction.objects.filter(
                legacy_cashbook_id=cashbook.id
            ).first()

            assert company_tx is not None, f"CashBook {cashbook.id}에 해당하는 거래를 찾을 수 없음"

            # 금액 검증
            expected_amount = cashbook.income or cashbook.outlay
            assert company_tx.amount == expected_amount, f"금액 불일치: {expected_amount} != {company_tx.amount}"

            # 거래 유형 검증
            expected_type = 'INCOME' if cashbook.income else 'OUTLAY'
            assert company_tx.transaction_type == expected_type, f"거래유형 불일치"

            # 날짜 검증
            assert company_tx.deal_date == cashbook.deal_date, f"거래일자 불일치"

        self.stdout.write(f'✓ 샘플 데이터 검증 통과 ({sample_count}건)')
```

#### Phase 1 실행 및 검증

```bash
# 1. 최근 1년 데이터로 테스트
python manage.py phase1_readonly_migration --start-date=2024-01-01 --dry-run

# 2. 실제 이관 실행
python manage.py phase1_readonly_migration --start-date=2024-01-01 --batch-size=500

# 3. 전체 데이터 이관
python manage.py phase1_readonly_migration --batch-size=1000

# 4. 이관 결과 확인
python manage.py validate_phase1_migration
```

### Phase 2: 실시간 동기화 (Real-time Sync)

#### 목표
- 기존 Cash 앱의 신규/변경 데이터를 Ledger 앱에 실시간 반영
- 데이터 일관성 유지
- 동기화 지연 최소화

#### 동기화 시스템 구현

```python
# sync/services.py

import logging
from datetime import datetime
from django.db import transaction
from django.core.cache import cache

logger = logging.getLogger('ledger_sync')

class LegacyLedgerSyncService:
    """Cash 앱과 Ledger 앱 간 동기화 서비스"""

    SYNC_STATUS_CACHE_KEY = 'ledger_sync_status'
    LOCK_TIMEOUT = 300  # 5분

    @classmethod
    def sync_cashbook(cls, cashbook_id, operation='create'):
        """CashBook 동기화"""
        cache_key = f'sync_cashbook_{cashbook_id}'

        # 중복 처리 방지
        if cache.get(cache_key):
            return {'status': 'skipped', 'reason': 'already_processing'}

        try:
            cache.set(cache_key, True, cls.LOCK_TIMEOUT)

            from cash.models import CashBook
            cashbook = CashBook.objects.get(id=cashbook_id)

            if operation == 'create':
                return cls._create_company_transaction(cashbook)
            elif operation == 'update':
                return cls._update_company_transaction(cashbook)
            elif operation == 'delete':
                return cls._delete_company_transaction(cashbook)

        except Exception as e:
            logger.error(f'CashBook 동기화 실패: {cashbook_id}, 오류: {e}')
            return {'status': 'error', 'message': str(e)}
        finally:
            cache.delete(cache_key)

    @classmethod
    def _create_company_transaction(cls, cashbook):
        """본사 거래 생성"""

        # 이미 동기화된 경우 스킵
        existing = CompanyBankTransaction.objects.filter(
            legacy_cashbook_id=cashbook.id
        ).exists()

        if existing:
            return {'status': 'skipped', 'reason': 'already_synced'}

        with transaction.atomic():
            # 1. 은행거래 생성
            transaction_id = uuid.uuid4()

            bank_tx = CompanyBankTransaction.objects.create(
                transaction_id=transaction_id,
                company=cashbook.company,
                amount=cashbook.income or cashbook.outlay or 0,
                transaction_type='INCOME' if cashbook.income else 'OUTLAY',
                deal_date=cashbook.deal_date,
                bank_account_type='COMPANY',
                bank_account_id=cashbook.bank_account.id,
                reference_number=f'SYNC_CASH_{cashbook.id}',
                created_at=cashbook.created,
                creator=cashbook.creator,
                legacy_cashbook_id=cashbook.id
            )

            # 2. 회계분류 생성
            accounting = CompanyAccountingEntry.objects.create(
                transaction_id=transaction_id,
                transaction_type='COMPANY',
                company=cashbook.company,
                sort=cashbook.sort,
                account_code=cls._get_account_code(cashbook),
                account_d1=cashbook.account_d1,
                account_d2=cashbook.account_d2,
                account_d3=cashbook.account_d3,
                content=cashbook.content or '',
                trader=cashbook.trader or '',
                note=cashbook.note or '',
                evidence_type=cashbook.evidence or '0',
                created_at=cashbook.created
            )

            # 분할 거래 처리
            if cashbook.separated:
                cls._handle_split_transaction(cashbook, bank_tx)

            logger.info(f'CashBook {cashbook.id} 동기화 완료: {bank_tx.transaction_id}')

            return {
                'status': 'success',
                'transaction_id': str(bank_tx.transaction_id),
                'ledger_id': bank_tx.id
            }

    @classmethod
    def _update_company_transaction(cls, cashbook):
        """본사 거래 수정"""

        try:
            bank_tx = CompanyBankTransaction.objects.get(
                legacy_cashbook_id=cashbook.id
            )
        except CompanyBankTransaction.DoesNotExist:
            # 동기화되지 않은 경우 새로 생성
            return cls._create_company_transaction(cashbook)

        with transaction.atomic():
            # 거래 정보 업데이트
            bank_tx.amount = cashbook.income or cashbook.outlay or 0
            bank_tx.transaction_type = 'INCOME' if cashbook.income else 'OUTLAY'
            bank_tx.deal_date = cashbook.deal_date
            bank_tx.bank_account_id = cashbook.bank_account.id
            bank_tx.updated_at = datetime.now()
            bank_tx.save()

            # 회계분류 업데이트
            accounting = CompanyAccountingEntry.objects.get(
                transaction_id=bank_tx.transaction_id
            )
            accounting.account_code = cls._get_account_code(cashbook)
            accounting.account_d1 = cashbook.account_d1
            accounting.account_d2 = cashbook.account_d2
            accounting.account_d3 = cashbook.account_d3
            accounting.content = cashbook.content or ''
            accounting.trader = cashbook.trader or ''
            accounting.note = cashbook.note or ''
            accounting.evidence_type = cashbook.evidence or '0'
            accounting.save()

            return {'status': 'success', 'operation': 'updated'}

    @classmethod
    def sync_project_cashbook(cls, pcb_id, operation='create'):
        """ProjectCashBook 동기화"""
        # CashBook과 유사한 로직으로 구현
        pass

    @classmethod
    def _get_account_code(cls, cashbook):
        """계정코드 추출"""
        if cashbook.account_d3:
            return cashbook.account_d3.code
        elif cashbook.account_d2:
            return cashbook.account_d2.code
        elif cashbook.account_d1:
            return cashbook.account_d1.code
        return 'UNKNOWN'

# sync/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cash.models import CashBook, ProjectCashBook
from .tasks import sync_cashbook_async, sync_project_cashbook_async

@receiver(post_save, sender=CashBook)
def cashbook_sync_handler(sender, instance, created, **kwargs):
    """CashBook 변경 시 비동기 동기화"""
    operation = 'create' if created else 'update'
    sync_cashbook_async.delay(instance.id, operation)

@receiver(post_delete, sender=CashBook)
def cashbook_delete_sync_handler(sender, instance, **kwargs):
    """CashBook 삭제 시 동기화"""
    sync_cashbook_async.delay(instance.id, 'delete')

@receiver(post_save, sender=ProjectCashBook)
def project_cashbook_sync_handler(sender, instance, created, **kwargs):
    """ProjectCashBook 변경 시 비동기 동기화"""
    operation = 'create' if created else 'update'
    sync_project_cashbook_async.delay(instance.id, operation)

# sync/tasks.py

from celery import shared_task
from .services import LegacyLedgerSyncService

@shared_task(bind=True, max_retries=3)
def sync_cashbook_async(self, cashbook_id, operation):
    """CashBook 비동기 동기화 태스크"""
    try:
        result = LegacyLedgerSyncService.sync_cashbook(cashbook_id, operation)
        return result
    except Exception as e:
        # 재시도
        if self.request.retries < 3:
            self.retry(countdown=60 * (self.request.retries + 1))
        else:
            # 최종 실패 시 알림
            from .notifications import notify_sync_failure
            notify_sync_failure('CashBook', cashbook_id, str(e))
            raise

@shared_task(bind=True, max_retries=3)
def sync_project_cashbook_async(self, pcb_id, operation):
    """ProjectCashBook 비동기 동기화 태스크"""
    # 유사한 로직
    pass
```

#### 동기화 모니터링

```python
# sync/monitoring.py

from django.core.management.base import BaseCommand
from django.core.cache import cache
from datetime import datetime, timedelta

class SyncMonitor:
    """동기화 상태 모니터링"""

    @staticmethod
    def get_sync_status():
        """전체 동기화 상태 조회"""

        # 1. 동기화되지 않은 CashBook 수
        unsynced_cashbooks = CashBook.objects.exclude(
            id__in=CompanyBankTransaction.objects.values_list(
                'legacy_cashbook_id', flat=True
            ).filter(legacy_cashbook_id__isnull=False)
        ).count()

        # 2. 최근 1시간 동기화 실패 수
        recent_failures = cache.get('sync_failures_count', 0)

        # 3. 동기화 지연 건수 (1분 이상 지연)
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        delayed_sync = cache.get('delayed_sync_count', 0)

        # 4. 평균 동기화 시간
        avg_sync_time = cache.get('avg_sync_time', 0)

        return {
            'unsynced_records': unsynced_cashbooks,
            'recent_failures': recent_failures,
            'delayed_sync': delayed_sync,
            'avg_sync_time': avg_sync_time,
            'status': 'healthy' if unsynced_cashbooks < 10 and recent_failures < 5 else 'warning'
        }

    @staticmethod
    def validate_data_consistency():
        """데이터 일관성 검증"""

        inconsistencies = []

        # 1. 금액 불일치 검사
        cashbooks_with_tx = CashBook.objects.filter(
            id__in=CompanyBankTransaction.objects.values_list(
                'legacy_cashbook_id', flat=True
            ).filter(legacy_cashbook_id__isnull=False)
        )

        for cb in cashbooks_with_tx[:100]:  # 샘플 검사
            tx = CompanyBankTransaction.objects.get(legacy_cashbook_id=cb.id)
            expected_amount = cb.income or cb.outlay

            if tx.amount != expected_amount:
                inconsistencies.append({
                    'type': 'amount_mismatch',
                    'cashbook_id': cb.id,
                    'expected': expected_amount,
                    'actual': tx.amount
                })

        # 2. 거래일자 불일치 검사
        # 3. 계정코드 불일치 검사
        # ...

        return inconsistencies

# Management Command
class Command(BaseCommand):
    help = 'Monitor sync status and data consistency'

    def handle(self, *args, **options):
        monitor = SyncMonitor()

        # 동기화 상태 확인
        status = monitor.get_sync_status()
        self.stdout.write(f"동기화 상태: {status['status']}")
        self.stdout.write(f"미동기화 건수: {status['unsynced_records']}")
        self.stdout.write(f"최근 실패 건수: {status['recent_failures']}")

        # 데이터 일관성 확인
        inconsistencies = monitor.validate_data_consistency()
        if inconsistencies:
            self.stdout.write(f"데이터 불일치 발견: {len(inconsistencies)}건")
            for issue in inconsistencies[:5]:
                self.stdout.write(f"  - {issue}")
        else:
            self.stdout.write("데이터 일관성 검증 통과")
```

### Phase 3: 양방향 동기화 (Bidirectional Sync)

#### 목표
- Ledger 앱에서 생성/수정된 데이터를 Cash 앱에도 반영
- 테스트 기간 중 완전한 데이터 일관성 유지
- 사용자가 두 시스템 중 어느 것을 사용하든 동일한 결과

#### 양방향 동기화 구현

```python
# sync/bidirectional_service.py

class BidirectionalSyncService:
    """양방향 동기화 서비스"""

    @classmethod
    def sync_ledger_to_cash(cls, transaction_id, operation='create'):
        """Ledger → Cash 동기화"""

        try:
            bank_tx = CompanyBankTransaction.objects.get(transaction_id=transaction_id)
            accounting = CompanyAccountingEntry.objects.get(transaction_id=transaction_id)
        except (CompanyBankTransaction.DoesNotExist, CompanyAccountingEntry.DoesNotExist):
            return {'status': 'error', 'message': 'Transaction not found'}

        if operation == 'create':
            return cls._create_cashbook_from_ledger(bank_tx, accounting)
        elif operation == 'update':
            return cls._update_cashbook_from_ledger(bank_tx, accounting)
        elif operation == 'delete':
            return cls._delete_cashbook_from_ledger(bank_tx)

    @classmethod
    def _create_cashbook_from_ledger(cls, bank_tx, accounting):
        """Ledger 데이터로부터 CashBook 생성"""

        # 이미 생성된 경우 스킵
        if bank_tx.legacy_cashbook_id:
            return {'status': 'skipped', 'reason': 'already_exists'}

        with transaction.atomic():
            # CashBook 생성
            cashbook = CashBook.objects.create(
                company=bank_tx.company,
                sort=accounting.sort,
                account_d1=accounting.account_d1,
                account_d2=accounting.account_d2,
                account_d3=accounting.account_d3,
                content=accounting.content,
                trader=accounting.trader,
                bank_account_id=bank_tx.bank_account_id,
                income=bank_tx.amount if bank_tx.transaction_type == 'INCOME' else None,
                outlay=bank_tx.amount if bank_tx.transaction_type == 'OUTLAY' else None,
                evidence=accounting.evidence_type,
                note=accounting.note,
                deal_date=bank_tx.deal_date,
                creator=bank_tx.creator,
                created=bank_tx.created_at,
                # 동기화 추적
                synced_from_ledger=True,
                ledger_transaction_id=str(bank_tx.transaction_id)
            )

            # 역참조 설정
            bank_tx.legacy_cashbook_id = cashbook.id
            bank_tx.save(update_fields=['legacy_cashbook_id'])

            return {'status': 'success', 'cashbook_id': cashbook.id}

# signals.py - Ledger 앱 신호 처리

@receiver(post_save, sender=CompanyBankTransaction)
def ledger_to_cash_sync_handler(sender, instance, created, **kwargs):
    """Ledger 거래 생성/수정 시 Cash로 동기화"""

    # 이미 Cash에서 동기화된 것은 제외
    if instance.legacy_cashbook_id:
        return

    operation = 'create' if created else 'update'
    sync_ledger_to_cash_async.delay(str(instance.transaction_id), operation)

@shared_task
def sync_ledger_to_cash_async(transaction_id, operation):
    """Ledger → Cash 비동기 동기화"""
    return BidirectionalSyncService.sync_ledger_to_cash(transaction_id, operation)
```

### Phase 4: 점진적 전환 (Gradual Migration)

#### 목표
- 사용자 그룹별 점진적으로 Ledger 앱 사용 전환
- 문제 발생 시 즉시 롤백 가능
- 사용자 피드백 수집 및 개선

#### 전환 전략

```python
# migration/feature_flags.py

class FeatureFlags:
    """기능별 전환 플래그 관리"""

    @staticmethod
    def should_use_ledger_for_user(user):
        """사용자별 Ledger 앱 사용 여부"""

        # 1. 관리자는 항상 Ledger 사용
        if user.is_superuser:
            return True

        # 2. 베타 사용자 그룹
        if user.groups.filter(name='ledger_beta_users').exists():
            return True

        # 3. 회사별 점진적 전환
        if hasattr(user, 'profile'):
            company = user.profile.company
            if company and company.use_ledger_app:
                return True

        # 4. 특정 날짜 이후 전체 전환
        from django.conf import settings
        cutoff_date = getattr(settings, 'LEDGER_FULL_MIGRATION_DATE', None)
        if cutoff_date and timezone.now().date() >= cutoff_date:
            return True

        return False

    @staticmethod
    def should_use_ledger_for_function(function_name, user=None):
        """기능별 Ledger 사용 여부"""

        function_flags = {
            'transaction_list': 'LEDGER_TRANSACTION_LIST_ENABLED',
            'transaction_create': 'LEDGER_TRANSACTION_CREATE_ENABLED',
            'reports': 'LEDGER_REPORTS_ENABLED',
            'bulk_import': 'LEDGER_BULK_IMPORT_ENABLED',
        }

        flag_name = function_flags.get(function_name)
        if not flag_name:
            return False

        # 환경변수에서 플래그 확인
        from django.conf import settings
        if not getattr(settings, flag_name, False):
            return False

        # 사용자별 확인
        if user:
            return FeatureFlags.should_use_ledger_for_user(user)

        return True

# views/routing.py

class SmartRoutingMixin:
    """Cash/Ledger 앱 간 라우팅 믹스인"""

    def dispatch(self, request, *args, **kwargs):
        """요청을 적절한 앱으로 라우팅"""

        function_name = getattr(self, 'function_name', None)

        if function_name and FeatureFlags.should_use_ledger_for_function(
            function_name, request.user
        ):
            # Ledger 앱으로 라우팅
            return self.route_to_ledger(request, *args, **kwargs)
        else:
            # 기존 Cash 앱 사용
            return super().dispatch(request, *args, **kwargs)

    def route_to_ledger(self, request, *args, **kwargs):
        """Ledger 앱으로 요청 전달"""
        from django.shortcuts import redirect

        # URL 매핑 규칙에 따라 리다이렉트
        ledger_url_mapping = {
            'cash:transaction_list': 'ledger:transaction_list',
            'cash:transaction_create': 'ledger:transaction_create',
            # ... 추가 매핑
        }

        current_url_name = request.resolver_match.url_name
        namespace = request.resolver_match.namespace
        full_url_name = f"{namespace}:{current_url_name}" if namespace else current_url_name

        ledger_url_name = ledger_url_mapping.get(full_url_name)
        if ledger_url_name:
            return redirect(ledger_url_name, *args, **kwargs)

        # 매핑이 없으면 기존 처리
        return super().dispatch(request, *args, **kwargs)

# 사용 예시
class TransactionListView(SmartRoutingMixin, ListView):
    function_name = 'transaction_list'
    model = CashBook
    template_name = 'cash/transaction_list.html'
    # ... 기존 Cash 앱 로직
```

#### 사용자 피드백 수집

```python
# feedback/models.py

class MigrationFeedback(models.Model):
    """마이그레이션 피드백"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feedback_type = models.CharField(max_length=20, choices=[
        ('BUG', '버그 신고'),
        ('PERFORMANCE', '성능 이슈'),
        ('UX', '사용성 개선'),
        ('FEATURE_REQUEST', '기능 요청'),
        ('POSITIVE', '긍정적 피드백')
    ])

    function_name = models.CharField(max_length=50, verbose_name='기능명')
    description = models.TextField(verbose_name='상세 설명')
    severity = models.CharField(max_length=10, choices=[
        ('LOW', '낮음'),
        ('MEDIUM', '보통'),
        ('HIGH', '높음'),
        ('CRITICAL', '심각')
    ], default='MEDIUM')

    browser_info = models.TextField(blank=True)
    page_url = models.URLField(blank=True)

    status = models.CharField(max_length=20, choices=[
        ('NEW', '신규'),
        ('IN_PROGRESS', '처리중'),
        ('RESOLVED', '해결됨'),
        ('CLOSED', '종료')
    ], default='NEW')

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

# 피드백 수집 API
class MigrationFeedbackView(CreateAPIView):
    serializer_class = MigrationFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

### Phase 5: 최종 전환 및 정리 (Final Cutover)

#### 목표
- Cash 앱 완전 비활성화
- 데이터 아카이브
- 코드 정리

#### 최종 전환 절차

```python
# management/commands/final_cutover.py

class Command(BaseCommand):
    help = 'Execute final cutover from Cash to Ledger app'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true',
                          help='Confirm the final cutover')
        parser.add_argument('--archive-data', action='store_true',
                          help='Archive old Cash app data')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write('최종 전환을 확인하려면 --confirm 옵션을 사용하세요.')
            return

        self.stdout.write('🔄 최종 전환 시작...')

        # 1. 최종 데이터 검증
        self.validate_final_data()

        # 2. Cash 앱 비활성화
        self.disable_cash_app()

        # 3. 데이터 아카이브 (옵션)
        if options['archive_data']:
            self.archive_cash_data()

        # 4. 정리 작업
        self.cleanup_migration_artifacts()

        self.stdout.write('✅ 최종 전환 완료!')

    def validate_final_data(self):
        """최종 데이터 검증"""
        self.stdout.write('📊 최종 데이터 검증 중...')

        # 모든 CashBook이 동기화되었는지 확인
        unsynced_count = CashBook.objects.exclude(
            id__in=CompanyBankTransaction.objects.values_list(
                'legacy_cashbook_id', flat=True
            ).filter(legacy_cashbook_id__isnull=False)
        ).count()

        if unsynced_count > 0:
            raise CommandError(f'아직 동기화되지 않은 CashBook이 {unsynced_count}건 있습니다.')

        # 데이터 일관성 최종 검증
        monitor = SyncMonitor()
        inconsistencies = monitor.validate_data_consistency()

        if inconsistencies:
            raise CommandError(f'데이터 불일치가 {len(inconsistencies)}건 발견되었습니다.')

        self.stdout.write('✅ 데이터 검증 완료')

    def disable_cash_app(self):
        """Cash 앱 비활성화"""
        self.stdout.write('🚫 Cash 앱 비활성화 중...')

        # settings에서 Cash 앱 제거 (동적)
        from django.conf import settings

        # INSTALLED_APPS에서 cash 제거
        new_installed_apps = [app for app in settings.INSTALLED_APPS if app != 'cash']
        settings.INSTALLED_APPS = new_installed_apps

        # URL 패턴 비활성화 마킹
        # (실제로는 웹서버 설정에서 처리하는 것이 좋음)

        self.stdout.write('✅ Cash 앱 비활성화 완료')

    def archive_cash_data(self):
        """Cash 앱 데이터 아카이브"""
        self.stdout.write('📦 데이터 아카이브 중...')

        from django.core import serializers
        from datetime import datetime

        # 아카이브 파일 생성
        archive_date = datetime.now().strftime('%Y%m%d_%H%M%S')

        # CashBook 데이터 아카이브
        cashbooks = CashBook.objects.all()
        with open(f'archive/cashbook_{archive_date}.json', 'w') as f:
            serializers.serialize('json', cashbooks, stream=f, indent=2)

        # ProjectCashBook 데이터 아카이브
        project_cashbooks = ProjectCashBook.objects.all()
        with open(f'archive/project_cashbook_{archive_date}.json', 'w') as f:
            serializers.serialize('json', project_cashbooks, stream=f, indent=2)

        self.stdout.write(f'✅ 데이터 아카이브 완료: archive/*_{archive_date}.json')

    def cleanup_migration_artifacts(self):
        """마이그레이션 관련 정리 작업"""
        self.stdout.write('🧹 정리 작업 중...')

        # 동기화 태스크 중지
        from celery import current_app
        # 실행 중인 동기화 태스크 종료

        # 임시 테이블 및 필드 제거
        # (별도 마이그레이션으로 처리하는 것이 좋음)

        # 캐시 정리
        from django.core.cache import cache
        cache.delete_pattern('sync_*')
        cache.delete_pattern('migration_*')

        self.stdout.write('✅ 정리 작업 완료')

# 웹서버 설정 업데이트
# nginx.conf
location /cash/ {
    return 301 /ledger/$is_args$args;
}

# 또는 Django URL 설정
# urls.py
from django.shortcuts import redirect

def cash_redirect(request, path=''):
    return redirect(f'/ledger/{path}', permanent=True)

urlpatterns = [
    path('cash/<path:path>', cash_redirect),
    path('ledger/', include('ledger.urls')),
]
```

## 📈 성능 최적화 및 모니터링

### 이관 성능 최적화

```python
# optimization/bulk_operations.py

class OptimizedMigrationService:
    """최적화된 이관 서비스"""

    @staticmethod
    def bulk_migrate_with_progress(model_class, batch_size=5000, progress_callback=None):
        """대량 데이터 이관 (진행률 추적)"""

        total_count = model_class.objects.count()
        processed = 0

        # 메모리 효율적인 쿼리
        queryset = model_class.objects.all().only(
            'id', 'company_id', 'project_id', 'amount',
            'deal_date', 'created', 'creator_id'
            # 필수 필드만 로드
        ).iterator(chunk_size=batch_size)

        batch = []
        for obj in queryset:
            batch.append(obj)

            if len(batch) >= batch_size:
                OptimizedMigrationService._process_batch(batch)
                processed += len(batch)

                # 진행률 콜백
                if progress_callback:
                    progress_callback(processed, total_count)

                batch = []

        # 마지막 배치 처리
        if batch:
            OptimizedMigrationService._process_batch(batch)
            processed += len(batch)

        return processed

    @staticmethod
    def _process_batch(batch):
        """배치 처리 (개별 트랜잭션)"""

        bank_transactions = []
        accounting_entries = []

        for item in batch:
            # 변환 로직
            tx_id = uuid.uuid4()

            # 은행거래 객체 생성 (아직 DB 저장 안함)
            bank_tx = CompanyBankTransaction(
                transaction_id=tx_id,
                # ... 필드 매핑
            )
            bank_transactions.append(bank_tx)

            # 회계분류 객체 생성
            accounting = CompanyAccountingEntry(
                transaction_id=tx_id,
                # ... 필드 매핑
            )
            accounting_entries.append(accounting)

        # 배치 삽입 (단일 쿼리)
        with transaction.atomic():
            CompanyBankTransaction.objects.bulk_create(
                bank_transactions,
                ignore_conflicts=True
            )
            CompanyAccountingEntry.objects.bulk_create(
                accounting_entries,
                ignore_conflicts=True
            )

# 사용 예시
def migrate_with_progress_bar():
    from tqdm import tqdm

    progress_bar = tqdm(total=CashBook.objects.count(), desc="Migrating CashBooks")

    def update_progress(current, total):
        progress_bar.n = current
        progress_bar.refresh()

    OptimizedMigrationService.bulk_migrate_with_progress(
        CashBook,
        batch_size=1000,
        progress_callback=update_progress
    )

    progress_bar.close()
```

### 실시간 모니터링 대시보드

```python
# monitoring/dashboard.py

from django.http import JsonResponse
from django.views import View

class MigrationDashboardAPI(View):
    """마이그레이션 대시보드 API"""

    def get(self, request):
        """대시보드 데이터 조회"""

        # 기본 통계
        stats = {
            'total_cashbooks': CashBook.objects.count(),
            'migrated_cashbooks': CompanyBankTransaction.objects.filter(
                legacy_cashbook_id__isnull=False
            ).count(),
            'total_project_cashbooks': ProjectCashBook.objects.count(),
            'migrated_project_cashbooks': ProjectBankTransaction.objects.filter(
                legacy_pcb_id__isnull=False
            ).count(),
        }

        # 진행률 계산
        stats['cashbook_migration_progress'] = (
            stats['migrated_cashbooks'] / stats['total_cashbooks'] * 100
            if stats['total_cashbooks'] > 0 else 100
        )

        stats['project_migration_progress'] = (
            stats['migrated_project_cashbooks'] / stats['total_project_cashbooks'] * 100
            if stats['total_project_cashbooks'] > 0 else 100
        )

        # 동기화 상태
        sync_status = SyncMonitor.get_sync_status()
        stats.update(sync_status)

        # 최근 활동
        recent_migrations = self.get_recent_migration_activity()

        # 성능 메트릭
        performance_metrics = self.get_performance_metrics()

        return JsonResponse({
            'stats': stats,
            'recent_activity': recent_migrations,
            'performance': performance_metrics,
            'timestamp': timezone.now().isoformat()
        })

    def get_recent_migration_activity(self):
        """최근 마이그레이션 활동"""

        # 최근 1시간 내 생성된 거래
        one_hour_ago = timezone.now() - timedelta(hours=1)

        recent_company_tx = CompanyBankTransaction.objects.filter(
            created_at__gte=one_hour_ago,
            legacy_cashbook_id__isnull=False
        ).count()

        recent_project_tx = ProjectBankTransaction.objects.filter(
            created_at__gte=one_hour_ago,
            legacy_pcb_id__isnull=False
        ).count()

        return {
            'last_hour': {
                'company_transactions': recent_company_tx,
                'project_transactions': recent_project_tx
            }
        }

    def get_performance_metrics(self):
        """성능 메트릭"""

        return {
            'avg_sync_time': cache.get('avg_sync_time', 0),
            'sync_queue_size': cache.get('sync_queue_size', 0),
            'error_rate': cache.get('sync_error_rate', 0)
        }

# templates/monitoring/dashboard.html
<!DOCTYPE html>
<html>
<head>
    <title>Migration Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .widget { border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
        .progress { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; }
        .progress-bar { height: 100%; background: #4caf50; border-radius: 10px; }
        .status-healthy { color: green; }
        .status-warning { color: orange; }
        .status-error { color: red; }
    </style>
</head>
<body>
    <h1>Cash → Ledger Migration Dashboard</h1>

    <div class="dashboard">
        <!-- 진행률 위젯 -->
        <div class="widget">
            <h3>Migration Progress</h3>
            <div>
                <label>CashBook Migration:</label>
                <div class="progress">
                    <div class="progress-bar" id="cashbook-progress"></div>
                </div>
                <span id="cashbook-percentage">0%</span>
            </div>
            <div>
                <label>ProjectCashBook Migration:</label>
                <div class="progress">
                    <div class="progress-bar" id="project-progress"></div>
                </div>
                <span id="project-percentage">0%</span>
            </div>
        </div>

        <!-- 시스템 상태 위젯 -->
        <div class="widget">
            <h3>System Status</h3>
            <div id="sync-status">Loading...</div>
            <div>Unsynced Records: <span id="unsynced-count">-</span></div>
            <div>Recent Failures: <span id="failure-count">-</span></div>
            <div>Avg Sync Time: <span id="avg-sync-time">-</span>ms</div>
        </div>

        <!-- 실시간 차트 -->
        <div class="widget">
            <h3>Real-time Activity</h3>
            <canvas id="activity-chart" width="400" height="200"></canvas>
        </div>

        <!-- 최근 활동 -->
        <div class="widget">
            <h3>Recent Activity</h3>
            <div id="recent-activity">Loading...</div>
        </div>
    </div>

    <script>
        // 대시보드 업데이트 함수
        function updateDashboard() {
            fetch('/api/migration/dashboard/')
                .then(response => response.json())
                .then(data => {
                    // 진행률 업데이트
                    document.getElementById('cashbook-progress').style.width =
                        data.stats.cashbook_migration_progress + '%';
                    document.getElementById('cashbook-percentage').textContent =
                        data.stats.cashbook_migration_progress.toFixed(1) + '%';

                    document.getElementById('project-progress').style.width =
                        data.stats.project_migration_progress + '%';
                    document.getElementById('project-percentage').textContent =
                        data.stats.project_migration_progress.toFixed(1) + '%';

                    // 시스템 상태 업데이트
                    const statusElement = document.getElementById('sync-status');
                    statusElement.textContent = data.stats.status;
                    statusElement.className = 'status-' + data.stats.status;

                    document.getElementById('unsynced-count').textContent = data.stats.unsynced_records;
                    document.getElementById('failure-count').textContent = data.stats.recent_failures;
                    document.getElementById('avg-sync-time').textContent = data.performance.avg_sync_time;

                    // 최근 활동 업데이트
                    document.getElementById('recent-activity').innerHTML = `
                        <div>Company Transactions (1h): ${data.recent_activity.last_hour.company_transactions}</div>
                        <div>Project Transactions (1h): ${data.recent_activity.last_hour.project_transactions}</div>
                    `;
                });
        }

        // 차트 초기화
        const ctx = document.getElementById('activity-chart').getContext('2d');
        const activityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Sync Rate',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Sync Rate (per minute)'
                    }
                }
            }
        });

        // 5초마다 업데이트
        setInterval(updateDashboard, 5000);
        updateDashboard(); // 초기 로드
    </script>
</body>
</html>
```

## 🚨 위험 관리 및 롤백 계획

### 롤백 시나리오별 대응 방안

```python
# rollback/emergency_rollback.py

class EmergencyRollbackService:
    """긴급 롤백 서비스"""

    @staticmethod
    def execute_immediate_rollback():
        """즉시 롤백 (5분 내 완료 목표)"""

        # 1. Ledger 앱 비활성화 (Feature Flag)
        cache.set('LEDGER_EMERGENCY_DISABLED', True, timeout=3600)

        # 2. 모든 요청을 Cash 앱으로 리다이렉트
        cache.set('FORCE_CASH_APP', True, timeout=3600)

        # 3. 동기화 프로세스 중지
        EmergencyRollbackService.stop_all_sync_processes()

        # 4. 알림 발송
        EmergencyRollbackService.notify_emergency_rollback()

        logger.critical("Emergency rollback executed")

    @staticmethod
    def execute_data_rollback(cutoff_datetime):
        """데이터 롤백 (특정 시점으로 복구)"""

        with transaction.atomic():
            # 특정 시점 이후 생성된 Ledger 데이터 삭제
            deleted_tx = CompanyBankTransaction.objects.filter(
                created_at__gte=cutoff_datetime,
                legacy_cashbook_id__isnull=True  # Ledger에서 생성된 것만
            ).delete()

            deleted_accounting = CompanyAccountingEntry.objects.filter(
                created_at__gte=cutoff_datetime
            ).delete()

            # 동기화 상태 리셋
            CashBook.objects.filter(
                updated__gte=cutoff_datetime
            ).update(synced_to_ledger=False)

            return {
                'deleted_transactions': deleted_tx,
                'deleted_accounting': deleted_accounting
            }

    @staticmethod
    def validate_rollback_safety():
        """롤백 안전성 검증"""

        # 1. 현재 진행 중인 중요 작업 확인
        active_jobs = ImportJob.objects.filter(
            status__in=['PROCESSING', 'PENDING']
        ).count()

        # 2. 최근 사용자 활동 확인
        recent_activity = timezone.now() - timedelta(minutes=5)
        active_users = User.objects.filter(
            last_login__gte=recent_activity
        ).count()

        # 3. 중요한 거래 확인 (최근 1시간 내 대용량 거래)
        large_transactions = CompanyBankTransaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1),
            amount__gte=10000000  # 1천만원 이상
        ).count()

        return {
            'active_jobs': active_jobs,
            'active_users': active_users,
            'large_transactions': large_transactions,
            'safe_to_rollback': active_jobs == 0 and active_users < 5
        }

# 자동 모니터링 및 알림
class AutoRollbackMonitor:
    """자동 롤백 모니터링"""

    CRITICAL_THRESHOLDS = {
        'error_rate': 10,      # 10% 이상 오류율
        'sync_delay': 300,     # 5분 이상 동기화 지연
        'data_inconsistency': 100,  # 100건 이상 데이터 불일치
    }

    @staticmethod
    def check_critical_conditions():
        """심각한 상황 감지"""

        conditions = {}

        # 1. 오류율 확인
        error_rate = cache.get('sync_error_rate', 0)
        conditions['high_error_rate'] = error_rate > AutoRollbackMonitor.CRITICAL_THRESHOLDS['error_rate']

        # 2. 동기화 지연 확인
        sync_delay = cache.get('avg_sync_delay', 0)
        conditions['sync_delayed'] = sync_delay > AutoRollbackMonitor.CRITICAL_THRESHOLDS['sync_delay']

        # 3. 데이터 불일치 확인
        inconsistencies = SyncMonitor.validate_data_consistency()
        conditions['data_inconsistent'] = len(inconsistencies) > AutoRollbackMonitor.CRITICAL_THRESHOLDS['data_inconsistency']

        return conditions

    @staticmethod
    def should_trigger_auto_rollback():
        """자동 롤백 트리거 여부"""

        conditions = AutoRollbackMonitor.check_critical_conditions()

        # 2개 이상 조건이 만족되면 자동 롤백
        critical_count = sum(conditions.values())
        return critical_count >= 2

# Celery 태스크
@shared_task
def monitor_for_auto_rollback():
    """자동 롤백 모니터링 태스크"""

    if AutoRollbackMonitor.should_trigger_auto_rollback():
        # 안전성 검증
        safety_check = EmergencyRollbackService.validate_rollback_safety()

        if safety_check['safe_to_rollback']:
            # 자동 롤백 실행
            EmergencyRollbackService.execute_immediate_rollback()

            # 관리자에게 즉시 알림
            send_critical_alert(
                "Auto-rollback executed due to critical conditions",
                level="CRITICAL"
            )
        else:
            # 수동 개입 필요 알림
            send_critical_alert(
                "Critical conditions detected but auto-rollback unsafe - manual intervention required",
                level="CRITICAL"
            )
```

---

**문서 버전**: 1.0
**최종 수정일**: 2025-01-20
**다음 검토일**: 2025-02-01

**관련 문서**:
- [리팩토링 마스터 플랜](01_refactoring_master_plan.md)
- [아키텍처 설계 가이드](02_architecture_design.md)
- API 설계 명세서 (작성 예정)
- 테스트 전략 (작성 예정)
- 운영 가이드 (작성 예정)