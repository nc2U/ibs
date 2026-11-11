import uuid
from datetime import date
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework import status as http_status
from rest_framework.test import APITestCase

from company.models import Company
from contract.models import OrderGroup, Contract, ContractPrice, Contractor
from ibs.models import AccountSort
from items.models import UnitType, KeyUnit, HouseUnit, BuildingUnit
from payment.models import InstallmentPaymentOrder, ContractPayment
from project.models import Project
from work.models.project import IssueProject, Member, Role, Permission
from ledger.models import (
    BankCode, CompanyBankAccount, ProjectBankAccount,
    CompanyAccount, ProjectAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    CompanyLedgerCalculation, ProjectLedgerCalculation,
    Affiliate,
)
from ledger.services.project_transaction import get_project_transactions

User = get_user_model()


class LedgerTestBase(APITestCase):
    """원장(Ledger) 테스트 공통 픽스처 베이스 클래스"""

    def setUp(self):
        # 1. 사용자 생성
        self.admin_user = User.objects.create_superuser(
            username='admin_user', email='admin@test.com', password='password123'
        )
        self.work_manager_user = User.objects.create_user(
            username='wm_user', email='wm@test.com', password='password123', work_manager=True
        )
        self.user_a = User.objects.create_user(
            username='user_a', email='usera@test.com', password='password123'
        )
        self.user_b = User.objects.create_user(
            username='user_b', email='userb@test.com', password='password123'
        )

        # 2. 기초 마스터 데이터 생성
        self.bank_code, _ = BankCode.objects.get_or_create(
            code='004', defaults={'name': '국민은행'}
        )
        self.sort_deposit, _ = AccountSort.objects.get_or_create(
            pk=1, defaults={'name': '입금'}
        )
        self.sort_withdraw, _ = AccountSort.objects.get_or_create(
            pk=2, defaults={'name': '출금'}
        )

        # 3. 본사 및 본사 워크스페이스 생성
        self.company = Company.objects.create(name='(주)테스트건설')
        self.hq_issue_project = IssueProject.objects.create(
            company=self.company,
            name='본사 업무 공간',
            slug='hq-workspace',
            type='1',  # 1 = 본사
            creator=self.admin_user,
        )

        # 4. 프로젝트 A & B 워크스페이스 및 프로젝트 생성
        self.issue_project_a = IssueProject.objects.create(
            company=self.company,
            name='프로젝트 A 워크스페이스',
            slug='project-a-workspace',
            type='2',  # 2 = 프로젝트
            creator=self.admin_user,
        )
        self.project_a = Project.objects.create(
            issue_project=self.issue_project_a,
            name='프로젝트 A',
            order=1,
            kind='1',
            start_year='2026',
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24,
        )

        self.issue_project_b = IssueProject.objects.create(
            company=self.company,
            name='프로젝트 B 워크스페이스',
            slug='project-b-workspace',
            type='2',
            creator=self.admin_user,
        )
        self.project_b = Project.objects.create(
            issue_project=self.issue_project_b,
            name='프로젝트 B',
            order=2,
            kind='1',
            start_year='2026',
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24,
        )

        # 5. 권한 코드 준비
        self.perm_ledger_read, _ = Permission.objects.get_or_create(
            code='ledger.read', defaults={'name': '원장 조회', 'module': 'ledger', 'is_for_project': True}
        )
        self.perm_ledger_create, _ = Permission.objects.get_or_create(
            code='ledger.create', defaults={'name': '원장 등록', 'module': 'ledger', 'is_for_project': True}
        )
        self.perm_ledger_update, _ = Permission.objects.get_or_create(
            code='ledger.update', defaults={'name': '원장 수정', 'module': 'ledger', 'is_for_project': True}
        )
        self.perm_ledger_delete, _ = Permission.objects.get_or_create(
            code='ledger.delete', defaults={'name': '원장 삭제', 'module': 'ledger', 'is_for_project': True}
        )
        self.perm_ledger_manage, _ = Permission.objects.get_or_create(
            code='ledger.manage', defaults={'name': '원장 관리', 'module': 'ledger', 'is_for_project': True}
        )

        self.perm_hq_read, _ = Permission.objects.get_or_create(
            code='hq.ledger.read', defaults={'name': '본사 원장 조회', 'module': 'ledger', 'is_for_hq': True}
        )
        self.perm_hq_manage, _ = Permission.objects.get_or_create(
            code='hq.ledger.manage', defaults={'name': '본사 원장 관리', 'module': 'ledger', 'is_for_hq': True}
        )

        # 6. 역할 및 멤버십 할당
        # 역할 A (일반 CUD 권한, manage 권한 없음)
        self.role_a = Role.objects.create(
            name='프로젝트A 담당자', creator=self.admin_user, category='ibs_pr_manage'
        )
        self.role_a.permissions.add(
            self.perm_ledger_read, self.perm_ledger_create,
            self.perm_ledger_update, self.perm_ledger_delete
        )
        self.member_a = Member.objects.create(
            project=self.issue_project_a,
            user=self.user_a,
        )
        self.member_a.roles.add(self.role_a)

        # 역할 B (프로젝트 B 권한)
        self.role_b = Role.objects.create(
            name='프로젝트B 담당자', creator=self.admin_user, category='ibs_pr_manage'
        )
        self.role_b.permissions.add(
            self.perm_ledger_read, self.perm_ledger_create,
            self.perm_ledger_update, self.perm_ledger_delete, self.perm_ledger_manage
        )
        self.member_b = Member.objects.create(
            project=self.issue_project_b,
            user=self.user_b,
        )
        self.member_b.roles.add(self.role_b)

        # 7. 프로젝트 계정과목 마스터 데이터
        self.account_deposit = ProjectAccount.objects.create(
            code='1110', name='보통예금', category='asset', direction='deposit',
            is_active=True, is_category_only=False
        )
        self.account_sales = ProjectAccount.objects.create(
            code='4110', name='분양수입금', category='revenue', direction='deposit',
            is_active=True, is_category_only=False, is_payment=True, requires_contract=True
        )
        self.account_expense = ProjectAccount.objects.create(
            code='5110', name='공사비', category='expense', direction='withdraw',
            is_active=True, is_category_only=False
        )

        # 8. 프로젝트 A 계좌 및 프로젝트 B 계좌
        self.bank_acc_a = ProjectBankAccount.objects.create(
            project=self.project_a,
            bankcode=self.bank_code,
            alias_name='A프로젝트 입출금',
            number='111-222-333333',
            holder='(주)테스트건설',
        )
        self.bank_acc_b = ProjectBankAccount.objects.create(
            project=self.project_b,
            bankcode=self.bank_code,
            alias_name='B프로젝트 입출금',
            number='999-888-777777',
            holder='(주)테스트건설',
        )

        # 9. 프로젝트 A 계약 및 수납 관련 모델
        self.order_group_a = OrderGroup.objects.create(
            project=self.project_a,
            order_number=1,
            sort='2',
            name='1차 일반분양',
            is_default_for_uncontracted=True
        )
        self.unit_type_a = UnitType.objects.create(
            project=self.project_a,
            name='84A',
            sort='1',
            color='#FF0000',
            average_price=500000000,
            num_unit=10
        )
        self.key_unit_a = KeyUnit.objects.create(
            project=self.project_a,
            unit_type=self.unit_type_a,
            unit_code='A101'
        )
        self.bldg_a = BuildingUnit.objects.create(
            project=self.project_a,
            name='101동'
        )
        self.house_unit_a = HouseUnit.objects.create(
            unit_type=self.unit_type_a,
            building_unit=self.bldg_a,
            key_unit=self.key_unit_a,
            name='101호',
            bldg_line=1,
            floor_no=1
        )
        self.pay_order_down = InstallmentPaymentOrder.objects.create(
            project=self.project_a,
            type_sort='1',
            pay_sort='1',
            pay_code=1,
            pay_time=1,
            pay_name='계약금',
            pay_ratio=10.0
        )
        self.contract_a = Contract.objects.create(
            project=self.project_a,
            order_group=self.order_group_a,
            unit_type=self.unit_type_a,
            key_unit=self.key_unit_a,
            serial_number='CONT-A-001',
            creator=self.admin_user,
        )
        self.contract_price_a = ContractPrice.objects.create(
            contract=self.contract_a,
            price=500000000,
        )
        self.contractor_a = Contractor.objects.create(
            contract=self.contract_a,
            name='홍길동',
            status='2'
        )


class LedgerAuthenticationTests(LedgerTestBase):
    """원장 API 미인증 접근 차단 테스트"""

    def test_unauthenticated_requests_blocked(self):
        """인증되지 않은 모든 원장 API 요청은 401 Unauthorized로 거부됨"""
        endpoints = [
            '/api/v1/ledger/bank-code/',
            '/api/v1/ledger/company-bank-account/',
            '/api/v1/ledger/project-bank-account/',
            '/api/v1/ledger/company-transaction/',
            '/api/v1/ledger/project-transaction/',
            '/api/v1/ledger/company-accounting-entry/',
            '/api/v1/ledger/project-accounting-entry/',
            f'/api/v1/ledger/project-bank-account/{self.bank_acc_a.pk}/',
            f'/api/v1/ledger/project-transaction/balance_by_account/?project={self.project_a.pk}',
            '/api/v1/ledger/company-calculation/',
            '/api/v1/ledger/project-calculation/',
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(
                res.status_code, http_status.HTTP_401_UNAUTHORIZED,
                f'Unauthenticated access to {ep} must return 401'
            )


class LedgerRowLevelSecurityAndIsolationTests(LedgerTestBase):
    """프로젝트 간 원장 데이터 격리(Row-Level Security) 및 권한 검증"""

    def setUp(self):
        super().setUp()
        # 프로젝트 A의 은행 거래 및 분개 생성
        self.tx_a = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 7, 10),
            amount=10000000,
            sort=self.sort_deposit,
            content='A프로젝트 입금 거래',
            creator=self.user_a,
        )
        self.entry_a = ProjectAccountingEntry.objects.create(
            transaction_id=self.tx_a.transaction_id,
            project=self.project_a,
            account=self.account_deposit,
            amount=10000000,
            trader='A거래처',
        )

        # 프로젝트 B의 은행 거래 및 분개 생성
        self.tx_b = ProjectBankTransaction.objects.create(
            project=self.project_b,
            bank_account=self.bank_acc_b,
            deal_date=date(2026, 7, 15),
            amount=20000000,
            sort=self.sort_deposit,
            content='B프로젝트 입금 거래',
            creator=self.user_b,
        )
        self.entry_b = ProjectAccountingEntry.objects.create(
            transaction_id=self.tx_b.transaction_id,
            project=self.project_b,
            account=self.account_deposit,
            amount=20000000,
            trader='B거래처',
        )

    def test_project_bank_account_isolation(self):
        """프로젝트 A 멤버는 프로젝트 A 은행 계좌만 열람 가능하며 타 프로젝트 계좌는 차단됨"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 목록 조회 시 본인 프로젝트 계좌만 포함
        res = self.client.get('/api/v1/ledger/project-bank-account/')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        acc_ids = [item['pk'] for item in res.data['results']]
        self.assertIn(self.bank_acc_a.pk, acc_ids)
        self.assertNotIn(self.bank_acc_b.pk, acc_ids)

        # 2. 본인 프로젝트 계좌 상세 조회 성공
        res_a = self.client.get(f'/api/v1/ledger/project-bank-account/{self.bank_acc_a.pk}/')
        self.assertEqual(res_a.status_code, http_status.HTTP_200_OK)

        # 3. 타 프로젝트 계좌 상세 조회 404 차단
        res_b = self.client.get(f'/api/v1/ledger/project-bank-account/{self.bank_acc_b.pk}/')
        self.assertEqual(res_b.status_code, http_status.HTTP_404_NOT_FOUND)

        # 4. 타 프로젝트 ID로 필터링 시도 시 403 차단 (IbsModulePermission)
        res_filter_b = self.client.get(f'/api/v1/ledger/project-bank-account/?project={self.project_b.pk}')
        self.assertEqual(res_filter_b.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_project_bank_transaction_isolation(self):
        """프로젝트 A 멤버는 프로젝트 A 은행 거래만 열람 가능하며 타 프로젝트 거래는 격리됨"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 목록 조회 시 본인 프로젝트 거래만 포함
        res = self.client.get('/api/v1/ledger/project-transaction/')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        tx_ids = [item['pk'] for item in res.data['results']]
        self.assertIn(self.tx_a.pk, tx_ids)
        self.assertNotIn(self.tx_b.pk, tx_ids)

        # 2. 본인 프로젝트 거래 상세 조회 성공
        res_a = self.client.get(f'/api/v1/ledger/project-transaction/{self.tx_a.pk}/')
        self.assertEqual(res_a.status_code, http_status.HTTP_200_OK)

        # 3. 타 프로젝트 거래 상세 조회 404 차단
        res_b = self.client.get(f'/api/v1/ledger/project-transaction/{self.tx_b.pk}/')
        self.assertEqual(res_b.status_code, http_status.HTTP_404_NOT_FOUND)

        # 4. balance_by_account에서 타 프로젝트 조회 시 403 Forbidden 차단
        res_bal_b = self.client.get(
            f'/api/v1/ledger/project-transaction/balance_by_account/?project={self.project_b.pk}'
        )
        self.assertEqual(res_bal_b.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_project_accounting_entry_isolation(self):
        """프로젝트 A 멤버는 프로젝트 A 분개만 열람 가능하며 타 프로젝트 분개는 은닉됨"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 목록 조회
        res = self.client.get('/api/v1/ledger/project-accounting-entry/')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        entry_ids = [item['pk'] for item in res.data['results']]
        self.assertIn(self.entry_a.pk, entry_ids)
        self.assertNotIn(self.entry_b.pk, entry_ids)

        # 2. 타 프로젝트 분개 상세 조회 404 차단
        res_b = self.client.get(f'/api/v1/ledger/project-accounting-entry/{self.entry_b.pk}/')
        self.assertEqual(res_b.status_code, http_status.HTTP_404_NOT_FOUND)

    def test_composite_transaction_cross_project_blocked(self):
        """복합 거래 엔드포인트에서 타 프로젝트 데이터의 수정, 삭제 및 타 프로젝트 거래 생성이 차단됨"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 타 프로젝트로 복합 거래 신규 생성 시도 -> 403 Forbidden 차단
        payload_create_b = {
            'project': self.project_b.pk,
            'bank_account': self.bank_acc_b.pk,
            'deal_date': '2026-07-20',
            'amount': 5000000,
            'sort': 1,
            'content': '부정 거래 생성 시도',
            'accounting_entries': [
                {
                    'account': self.account_deposit.pk,
                    'amount': 5000000,
                    'trader': '부정거래처',
                }
            ]
        }
        res_create = self.client.post(
            '/api/v1/ledger/project-composite-transaction/',
            data=payload_create_b,
            format='json'
        )
        self.assertEqual(res_create.status_code, http_status.HTTP_403_FORBIDDEN)

        # 2. 타 프로젝트 거래 수정 시도 -> 404 Not Found 차단
        payload_update_b = {
            'content': '부정 거래 수정 시도',
            'accounting_entries': []
        }
        res_update = self.client.patch(
            f'/api/v1/ledger/project-composite-transaction/{self.tx_b.pk}/',
            data=payload_update_b,
            format='json'
        )
        self.assertEqual(res_update.status_code, http_status.HTTP_404_NOT_FOUND)

        # 3. 타 프로젝트 거래 삭제 시도 -> 404 Not Found 차단
        res_delete = self.client.delete(
            f'/api/v1/ledger/project-composite-transaction/{self.tx_b.pk}/'
        )
        self.assertEqual(res_delete.status_code, http_status.HTTP_404_NOT_FOUND)
        # 삭제되지 않고 DB에 보존되었는지 검증
        self.assertTrue(ProjectBankTransaction.objects.filter(pk=self.tx_b.pk).exists())


class ProjectCompositeTransactionIntegrityTests(LedgerTestBase):
    """복합 거래(Composite Transaction) 금액 균형 및 분양대금 연동 무결성 테스트"""

    def test_composite_transaction_amount_mismatch_validation(self):
        """은행 거래 금액과 분개 합계가 불일치할 때 400 Bad Request 에러 반환"""
        self.client.force_authenticate(user=self.user_a)

        payload_unbalanced = {
            'project': self.project_a.pk,
            'bank_account': self.bank_acc_a.pk,
            'deal_date': '2026-07-20',
            'amount': 10000000,  # 1,000만원
            'sort': 1,
            'content': '금액 불일치 테스트',
            'accounting_entries': [
                {
                    'account': self.account_deposit.pk,
                    'amount': 9000000,  # 900만원 (100만원 차이)
                    'trader': '불일치거래처',
                }
            ]
        }
        res = self.client.post(
            '/api/v1/ledger/project-composite-transaction/',
            data=payload_unbalanced,
            format='json'
        )
        self.assertEqual(res.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('accounting_entries', res.data)

    def test_composite_transaction_create_and_sync_contract_payment(self):
        """복합 거래 생성 시 은행거래, 분개가 생성되고 분양금 분개는 ContractPayment로 자동 동기화됨"""
        self.client.force_authenticate(user=self.user_a)

        deal_amount = 50000000  # 계약금 5,000만원
        payload_balanced = {
            'project': self.project_a.pk,
            'bank_account': self.bank_acc_a.pk,
            'deal_date': '2026-07-20',
            'amount': deal_amount,
            'sort': 1,  # 입금
            'content': '홍길동 계약금 납부',
            'accounting_entries': [
                {
                    'account': self.account_sales.pk,
                    'amount': deal_amount,
                    'contract': self.contract_a.pk,
                    'contractor': self.contractor_a.pk,
                    'installment_order': self.pay_order_down.pk,
                    'trader': '홍길동',
                }
            ]
        }
        res = self.client.post(
            '/api/v1/ledger/project-composite-transaction/',
            data=payload_balanced,
            format='json'
        )
        self.assertEqual(res.status_code, http_status.HTTP_201_CREATED)
        self.assertIn('bank_transaction', res.data)
        self.assertIn('accounting_entries', res.data)

        created_tx_pk = res.data['bank_transaction']['pk']
        tx_obj = ProjectBankTransaction.objects.get(pk=created_tx_pk)
        self.assertEqual(tx_obj.amount, deal_amount)

        # 회계 분개 생성 확인
        entries = ProjectAccountingEntry.objects.filter(transaction_id=tx_obj.transaction_id)
        self.assertEqual(entries.count(), 1)
        entry_obj = entries.first()
        self.assertEqual(entry_obj.amount, deal_amount)
        self.assertEqual(entry_obj.contract, self.contract_a)

        # ContractPayment 자동 생성 및 동기화 확인
        payment_record = ContractPayment.objects.filter(contract=self.contract_a).first()
        self.assertIsNotNone(payment_record)
        self.assertEqual(payment_record.accounting_entry.amount, deal_amount)
        self.assertEqual(payment_record.deal_date, date(2026, 7, 20))
        self.assertEqual(payment_record.installment_order, self.pay_order_down)

        # 복합 거래 삭제 시 은행거래, 분개, ContractPayment가 원자적으로 연쇄 삭제되는지 검증
        res_del = self.client.delete(f'/api/v1/ledger/project-composite-transaction/{created_tx_pk}/')
        self.assertEqual(res_del.status_code, http_status.HTTP_204_NO_CONTENT)

        self.assertFalse(ProjectBankTransaction.objects.filter(pk=created_tx_pk).exists())
        self.assertFalse(ProjectAccountingEntry.objects.filter(transaction_id=tx_obj.transaction_id).exists())
        self.assertFalse(ContractPayment.objects.filter(pk=payment_record.pk).exists())

    def test_composite_transaction_overpayment_blocked(self):
        """[T-3 / M-6] 잔여 미납액을 초과하는 납부 분개 등록 시 400 ValidationError 차단 검증"""
        self.client.force_authenticate(user=self.user_a)

        # self.contract_a의 총 공급가는 500,000,000원(5억)
        # 잔여 미납액(5억)을 초과하는 600,000,000원(6억) 납부 분개 생성 시도
        overpay_amount = 600000000
        payload_overpay = {
            'project': self.project_a.pk,
            'bank_account': self.bank_acc_a.pk,
            'deal_date': '2026-07-20',
            'amount': overpay_amount,
            'sort': 1,
            'content': '초과 납부 시도',
            'accounting_entries': [
                {
                    'account': self.account_sales.pk,
                    'amount': overpay_amount,
                    'contract': self.contract_a.pk,
                    'contractor': self.contractor_a.pk,
                    'installment_order': self.pay_order_down.pk,
                    'trader': '홍길동',
                }
            ]
        }
        res = self.client.post(
            '/api/v1/ledger/project-composite-transaction/',
            data=payload_overpay,
            format='json'
        )
        self.assertEqual(res.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('잔여 미납액', str(res.data))
        self.assertIn('초과합니다', str(res.data))




class ProjectLedgerSettlementLockTests(LedgerTestBase):
    """원장 정산 마감일(ProjectLedgerCalculation) 방어벽 및 권한 테스트"""

    def setUp(self):
        super().setUp()
        # 프로젝트 A의 정산 마감일을 2026-06-30으로 설정
        self.calc_a = ProjectLedgerCalculation.objects.create(
            project=self.project_a,
            calculated=date(2026, 6, 30),
            creator=self.admin_user,
        )

        # 마감일 이전 거래 (2026-06-15)
        self.tx_locked = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 6, 15),
            amount=3000000,
            sort=self.sort_deposit,
            content='마감일 이전 거래',
            creator=self.user_a,
        )
        self.entry_locked = ProjectAccountingEntry.objects.create(
            transaction_id=self.tx_locked.transaction_id,
            project=self.project_a,
            account=self.account_deposit,
            amount=3000000,
            trader='마감거래처',
        )

    def test_ordinary_user_cannot_create_or_delete_before_settlement_date(self):
        """일반 담당자는 정산 마감일 이전 날짜로 거래를 생성하거나 삭제할 수 없음"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 마감일 이전 날짜(2026-06-10)로 거래 생성 시도 -> 400 차단
        payload_before = {
            'project': self.project_a.pk,
            'bank_account': self.bank_acc_a.pk,
            'deal_date': '2026-06-10',
            'amount': 2000000,
            'sort': 1,
            'content': '마감일 이전 신규 거래 시도',
            'accounting_entries': [
                {
                    'account': self.account_deposit.pk,
                    'amount': 2000000,
                    'trader': '마감거래처',
                }
            ]
        }
        res_create = self.client.post(
            '/api/v1/ledger/project-composite-transaction/',
            data=payload_before,
            format='json'
        )
        self.assertEqual(res_create.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('deal_date', res_create.data)

        # 2. 마감일 이전 기존 거래 삭제 시도 -> 400 차단
        res_del = self.client.delete(
            f'/api/v1/ledger/project-composite-transaction/{self.tx_locked.pk}/'
        )
        self.assertEqual(res_del.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('정산 마감일', res_del.data['detail'])
        # DB에서 삭제되지 않았는지 확인
        self.assertTrue(ProjectBankTransaction.objects.filter(pk=self.tx_locked.pk).exists())

    def test_ordinary_user_can_create_and_delete_after_settlement_date(self):
        """일반 담당자는 정산 마감일 이후 날짜의 거래는 정상적으로 생성 및 삭제 가능"""
        self.client.force_authenticate(user=self.user_a)

        # 마감일 이후 날짜(2026-07-05)로 거래 생성
        payload_after = {
            'project': self.project_a.pk,
            'bank_account': self.bank_acc_a.pk,
            'deal_date': '2026-07-05',
            'amount': 1500000,
            'sort': 1,
            'content': '마감일 이후 정상 거래',
            'accounting_entries': [
                {
                    'account': self.account_deposit.pk,
                    'amount': 1500000,
                    'trader': '정상거래처',
                }
            ]
        }
        res_create = self.client.post(
            '/api/v1/ledger/project-composite-transaction/',
            data=payload_after,
            format='json'
        )
        self.assertEqual(res_create.status_code, http_status.HTTP_201_CREATED)
        new_pk = res_create.data['bank_transaction']['pk']

        # 삭제 정상 동작
        res_del = self.client.delete(f'/api/v1/ledger/project-composite-transaction/{new_pk}/')
        self.assertEqual(res_del.status_code, http_status.HTTP_204_NO_CONTENT)

    def test_manager_or_superuser_can_override_settlement_lock(self):
        """슈퍼유저 또는 ledger.manage 권한 보유자는 마감일 이전 거래도 삭제 가능"""
        # 슈퍼유저로 로그인
        self.client.force_authenticate(user=self.admin_user)

        res_del = self.client.delete(
            f'/api/v1/ledger/project-composite-transaction/{self.tx_locked.pk}/'
        )
        self.assertEqual(res_del.status_code, http_status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectBankTransaction.objects.filter(pk=self.tx_locked.pk).exists())


class HqLedgerAndGlobalVisibilityTests(LedgerTestBase):
    """본사 회계 격리(HqProjectModulePermission) 및 글로벌 관리자 열람 검증"""

    def setUp(self):
        super().setUp()
        # 본사 은행 계좌 및 거래
        self.hq_bank_acc = CompanyBankAccount.objects.create(
            company=self.company,
            bankcode=self.bank_code,
            alias_name='본사 운영계좌',
            number='100-200-300000',
            holder='(주)테스트건설',
        )
        self.hq_tx = CompanyBankTransaction.objects.create(
            company=self.company,
            bank_account=self.hq_bank_acc,
            deal_date=date(2026, 7, 1),
            amount=50000000,
            sort=self.sort_deposit,
            content='본사 자본금 입금',
            creator=self.admin_user,
        )

    def test_ordinary_project_user_blocked_from_hq_ledger(self):
        """본사 권한이 없는 일반 프로젝트 사용자는 본사 회계 API 접근 시 403 Forbidden으로 차단됨"""
        self.client.force_authenticate(user=self.user_a)

        endpoints = [
            '/api/v1/ledger/company-bank-account/',
            f'/api/v1/ledger/company-bank-account/{self.hq_bank_acc.pk}/',
            '/api/v1/ledger/company-transaction/',
            f'/api/v1/ledger/company-transaction/{self.hq_tx.pk}/',
            '/api/v1/ledger/company-accounting-entry/',
            '/api/v1/ledger/company-calculation/',
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(
                res.status_code, http_status.HTTP_403_FORBIDDEN,
                f'User without HQ permission must be forbidden from {ep}'
            )

    def test_global_managers_can_view_all_ledgers(self):
        """슈퍼유저는 본사 및 전사 프로젝트를 열람하고, work_manager는 본사 보안격리 및 전사 프로젝트를 열람 가능"""
        # 프로젝트 A 거래 생성
        tx_a = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 7, 2),
            amount=1000000,
            sort=self.sort_deposit,
            content='A 거래',
            creator=self.user_a,
        )
        # 프로젝트 B 거래 생성
        tx_b = ProjectBankTransaction.objects.create(
            project=self.project_b,
            bank_account=self.bank_acc_b,
            deal_date=date(2026, 7, 3),
            amount=2000000,
            sort=self.sort_deposit,
            content='B 거래',
            creator=self.user_b,
        )

        # 1. 슈퍼유저(admin_user): 본사 계좌/거래 및 전사 프로젝트 거래 통합 열람 가능
        self.client.force_authenticate(user=self.admin_user)
        res_hq_acc = self.client.get('/api/v1/ledger/company-bank-account/')
        self.assertEqual(res_hq_acc.status_code, http_status.HTTP_200_OK)

        res_hq_tx = self.client.get('/api/v1/ledger/company-transaction/')
        self.assertEqual(res_hq_tx.status_code, http_status.HTTP_200_OK)

        res_pr_tx = self.client.get('/api/v1/ledger/project-transaction/')
        self.assertEqual(res_pr_tx.status_code, http_status.HTTP_200_OK)
        tx_ids = [item['pk'] for item in res_pr_tx.data['results']]
        self.assertIn(tx_a.pk, tx_ids)
        self.assertIn(tx_b.pk, tx_ids)

        # 2. work_manager: 본사 권한이 없으므로 본사 원장은 403 차단(보안 격리), 전사 프로젝트 거래는 통합 열람 가능
        self.client.force_authenticate(user=self.work_manager_user)
        res_wm_hq = self.client.get('/api/v1/ledger/company-bank-account/')
        self.assertEqual(res_wm_hq.status_code, http_status.HTTP_403_FORBIDDEN)

        res_wm_pr = self.client.get('/api/v1/ledger/project-transaction/')
        self.assertEqual(res_wm_pr.status_code, http_status.HTTP_200_OK)
        wm_tx_ids = [item['pk'] for item in res_wm_pr.data['results']]
        self.assertIn(tx_a.pk, wm_tx_ids)
        self.assertIn(tx_b.pk, wm_tx_ids)

    def test_company_transaction_is_balanced_filtering(self):
        """본사 거래 is_balanced=true / false 필터링이 500 FieldError 없이 정상 작동하는지 검증"""
        self.client.force_authenticate(user=self.admin_user)

        com_account = CompanyAccount.objects.create(
            code='1100', name='본사 보통예금', category='asset', direction='deposit',
            is_active=True, is_category_only=False
        )

        # 1. 균형 거래: 10,000,000원 거래 + 10,000,000원 분개
        tx_balanced = CompanyBankTransaction.objects.create(
            company=self.company, bank_account=self.hq_bank_acc, deal_date=date(2026, 7, 5),
            amount=10000000, sort=self.sort_deposit, content='균형 거래', creator=self.admin_user
        )
        CompanyAccountingEntry.objects.create(
            transaction_id=tx_balanced.transaction_id, company=self.company,
            account=com_account, amount=10000000, trader='균형처'
        )

        # 2. 불균형 거래: 20,000,000원 거래 + 5,000,000원 분개
        tx_unbalanced = CompanyBankTransaction.objects.create(
            company=self.company, bank_account=self.hq_bank_acc, deal_date=date(2026, 7, 6),
            amount=20000000, sort=self.sort_deposit, content='불균형 거래', creator=self.admin_user
        )
        CompanyAccountingEntry.objects.create(
            transaction_id=tx_unbalanced.transaction_id, company=self.company,
            account=com_account, amount=5000000, trader='불균형처'
        )

        # is_balanced=true 필터링
        res_true = self.client.get(
            f'/api/v1/ledger/company-transaction/?company={self.company.pk}&is_balanced=true'
        )
        self.assertEqual(res_true.status_code, http_status.HTTP_200_OK)
        pks_true = [item['pk'] for item in res_true.data['results']]
        self.assertIn(tx_balanced.pk, pks_true)
        self.assertNotIn(tx_unbalanced.pk, pks_true)

        # is_balanced=false 필터링
        res_false = self.client.get(
            f'/api/v1/ledger/company-transaction/?company={self.company.pk}&is_balanced=false'
        )
        self.assertEqual(res_false.status_code, http_status.HTTP_200_OK)
        pks_false = [item['pk'] for item in res_false.data['results']]
        self.assertNotIn(tx_balanced.pk, pks_false)
        self.assertIn(tx_unbalanced.pk, pks_false)

    def test_company_transaction_search_and_category_filter_combined(self):
        """본사 거래에서 search와 account_category 필터가 결합될 때 AND로 결합되어 카테고리 필터가 유지되는지 검증"""
        self.client.force_authenticate(user=self.admin_user)

        acc_rev = CompanyAccount.objects.create(
            code='4100', name='용역수수료수익', category='revenue', direction='deposit',
            is_active=True, is_category_only=False
        )
        acc_exp = CompanyAccount.objects.create(
            code='5100', name='지급수수료비용', category='expense', direction='withdraw',
            is_active=True, is_category_only=False
        )

        tx_rev = CompanyBankTransaction.objects.create(
            company=self.company, bank_account=self.hq_bank_acc, deal_date=date(2026, 7, 7),
            amount=3000000, sort=self.sort_deposit, content='수익 거래', creator=self.admin_user
        )
        CompanyAccountingEntry.objects.create(
            transaction_id=tx_rev.transaction_id, company=self.company,
            account=acc_rev, amount=3000000, trader='고객사'
        )

        tx_exp = CompanyBankTransaction.objects.create(
            company=self.company, bank_account=self.hq_bank_acc, deal_date=date(2026, 7, 8),
            amount=500000, sort=self.sort_withdraw, content='비용 거래', creator=self.admin_user
        )
        CompanyAccountingEntry.objects.create(
            transaction_id=tx_exp.transaction_id, company=self.company,
            account=acc_exp, amount=500000, trader='협력사'
        )

        # 검색어 '수수료' + category='revenue' -> tx_rev만 나와야 하고 tx_exp는 제외되어야 함
        res = self.client.get(
            f'/api/v1/ledger/company-transaction/?company={self.company.pk}&account_category=revenue&search=수수료'
        )
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        pks = [item['pk'] for item in res.data['results']]
        self.assertIn(tx_rev.pk, pks)
        self.assertNotIn(tx_exp.pk, pks)

    def test_company_composite_transaction_hq_manage_perm_support(self):
        """hq.ledger.manage 권한을 가진 사용자는 본사 정산 마감일 이전의 거래도 수정/삭제 가능"""
        # 본사 정산일 설정 (2026-07-10)
        CompanyLedgerCalculation.objects.create(
            company=self.company, calculated=date(2026, 7, 10), creator=self.admin_user
        )

        # HQ 담당자 유저 생성 및 hq.ledger.manage 권한 부여
        hq_user = User.objects.create_user(
            username='hq_manager_user', email='hqm@test.com', password='password123'
        )
        perm_hq_delete, _ = Permission.objects.get_or_create(
            code='hq.ledger.delete', defaults={'name': '본사 원장 삭제', 'module': 'ledger', 'is_for_hq': True}
        )
        role_hq_manage = Role.objects.create(
            name='본사 경영관리자', creator=self.admin_user, category='ibs_hq_manage'
        )
        role_hq_manage.permissions.add(self.perm_hq_read, perm_hq_delete, self.perm_hq_manage)
        member_hq = Member.objects.create(project=self.hq_issue_project, user=hq_user)
        member_hq.roles.add(role_hq_manage)

        # 마감일 이전의 거래 (2026-07-05)
        com_acc = CompanyAccount.objects.create(
            code='1101', name='본사 보통예금2', category='asset', direction='deposit',
            is_active=True, is_category_only=False
        )
        tx_locked = CompanyBankTransaction.objects.create(
            company=self.company, bank_account=self.hq_bank_acc, deal_date=date(2026, 7, 5),
            amount=5000000, sort=self.sort_deposit, content='마감일 이전 거래', creator=self.admin_user
        )
        entry_locked = CompanyAccountingEntry.objects.create(
            transaction_id=tx_locked.transaction_id, company=self.company,
            account=com_acc, amount=5000000, trader='거래처'
        )

        # hq.ledger.manage 권한자로 로그인하여 거래 삭제 시도 -> 204 No Content 성공해야 함
        self.client.force_authenticate(user=hq_user)
        res_del = self.client.delete(
            f'/api/v1/ledger/company-composite-transaction/{tx_locked.pk}/'
        )
        self.assertEqual(res_del.status_code, http_status.HTTP_204_NO_CONTENT)
        self.assertFalse(CompanyBankTransaction.objects.filter(pk=tx_locked.pk).exists())


class LedgerRlsSecurityIsolationTests(LedgerTestBase):
    """원장 RLS(행 단위 보안) 격리 및 IDOR 방어 정밀 검증 테스트"""

    def setUp(self):
        super().setUp()
        # 제2의 회사 생성 (타사 데이터 격리 검증용)
        self.other_company = Company.objects.create(name='(주)타사건설')
        self.other_issue_project = IssueProject.objects.create(
            company=self.other_company,
            name='타사 본사 워크스페이스',
            slug='other-hq-workspace',
            type='1',
            creator=self.admin_user,
        )

        # 본사 은행 계좌 (회사 1 vs 회사 2)
        self.bank_acc_hq1 = CompanyBankAccount.objects.create(
            company=self.company,
            bankcode=self.bank_code,
            alias_name='회사1 본사계좌',
            number='111-000-111111',
            holder='(주)테스트건설',
        )
        self.bank_acc_hq2 = CompanyBankAccount.objects.create(
            company=self.other_company,
            bankcode=self.bank_code,
            alias_name='회사2 본사계좌',
            number='222-000-222222',
            holder='(주)타사건설',
        )

        # 거래 생성 (회사 1 vs 회사 2)
        self.tx_hq1 = CompanyBankTransaction.objects.create(
            company=self.company,
            bank_account=self.bank_acc_hq1,
            deal_date=date(2026, 7, 20),
            amount=15000000,
            sort=self.sort_deposit,
            content='회사1 입금',
            creator=self.admin_user,
        )
        self.tx_hq2 = CompanyBankTransaction.objects.create(
            company=self.other_company,
            bank_account=self.bank_acc_hq2,
            deal_date=date(2026, 7, 25),
            amount=25000000,
            sort=self.sort_deposit,
            content='회사2 입금',
            creator=self.admin_user,
        )

        # 프로젝트 거래 생성 (프로젝트 A vs 프로젝트 B)
        self.tx_pr_a = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 7, 10),
            amount=5000000,
            sort=self.sort_deposit,
            content='프로젝트A 거래',
            creator=self.user_a,
        )
        self.tx_pr_b = ProjectBankTransaction.objects.create(
            project=self.project_b,
            bank_account=self.bank_acc_b,
            deal_date=date(2026, 7, 18),
            amount=8000000,
            sort=self.sort_deposit,
            content='프로젝트B 거래',
            creator=self.user_b,
        )

        # 회사1 본사 관리자 유저 (회사2에는 소속되지 않음)
        self.hq1_user = User.objects.create_user(
            username='hq1_manager', email='hq1@test.com', password='password123'
        )
        role_hq1 = Role.objects.create(
            name='회사1 본사 관리자', creator=self.admin_user, category='ibs_hq_manage'
        )
        role_hq1.permissions.add(self.perm_hq_read)
        member_hq1 = Member.objects.create(project=self.hq_issue_project, user=self.hq1_user)
        member_hq1.roles.add(role_hq1)

    def test_company_balance_by_account_rls_isolation(self):
        """본사 balance_by_account: 타 회사 계좌 잔액 노출 차단 RLS 및 권한 격리 검증"""
        self.client.force_authenticate(user=self.hq1_user)

        # 1. 권한 없는 타 회사 ID로 직접 조회 시 HqProjectModulePermission에 의해 403 Forbidden으로 원천 차단됨
        res_other = self.client.get(
            f'/api/v1/ledger/company-transaction/balance_by_account/?company={self.other_company.pk}&date=2026-12-31'
        )
        self.assertEqual(res_other.status_code, http_status.HTTP_403_FORBIDDEN)

        # 2. company 파라미터 미지정 시에도 본인이 접근 가능한 회사1의 계좌만 포함되고 타사 계좌는 제외되어야 함
        res_all = self.client.get(
            '/api/v1/ledger/company-transaction/balance_by_account/?date=2026-12-31'
        )
        self.assertEqual(res_all.status_code, http_status.HTTP_200_OK)
        account_names = [item['bank_acc'] for item in res_all.data]
        self.assertIn(self.bank_acc_hq1.alias_name, account_names)
        self.assertNotIn(self.bank_acc_hq2.alias_name, account_names)

    def test_last_deal_idor_isolation(self):
        """본사 및 프로젝트 last_deal 엔드포인트 IDOR 방어 검증"""
        # 1. 본사 last_deal: 권한 없는 타사 조회 시 403 Forbidden 차단
        self.client.force_authenticate(user=self.hq1_user)
        res_hq_other = self.client.get(
            f'/api/v1/ledger/company-transaction/last_deal/?company={self.other_company.pk}'
        )
        self.assertEqual(res_hq_other.status_code, http_status.HTTP_403_FORBIDDEN)

        # 자신의 회사 조회 시 정상 날짜 반환
        res_hq_own = self.client.get(
            f'/api/v1/ledger/company-transaction/last_deal/?company={self.company.pk}'
        )
        self.assertEqual(res_hq_own.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(res_hq_own.data['results']), 1)
        self.assertEqual(res_hq_own.data['results'][0]['deal_date'], date(2026, 7, 20))

        # 2. 프로젝트 last_deal: 프로젝트 A 권한자(user_a)가 타 프로젝트 B 조회 시 403 Forbidden 차단
        self.client.force_authenticate(user=self.user_a)
        res_pr_other = self.client.get(
            f'/api/v1/ledger/project-transaction/last_deal/?project={self.project_b.pk}'
        )
        self.assertEqual(res_pr_other.status_code, http_status.HTTP_403_FORBIDDEN)

        # 자신의 프로젝트 A 조회 시 정상 날짜 반환
        res_pr_own = self.client.get(
            f'/api/v1/ledger/project-transaction/last_deal/?project={self.project_a.pk}'
        )
        self.assertEqual(res_pr_own.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(res_pr_own.data['results']), 1)
        self.assertEqual(res_pr_own.data['results'][0]['deal_date'], date(2026, 7, 10))

    def test_affiliate_rls_isolation(self):
        """Affiliate 모델 조회 시 소속 회사 및 소속 프로젝트만 필터링되는 RLS 검증"""
        # Affiliate 데이터 생성
        aff_c1 = Affiliate.objects.create(sort='company', company=self.company)
        aff_c2 = Affiliate.objects.create(sort='company', company=self.other_company)
        aff_pa = Affiliate.objects.create(sort='project', project=self.project_a)
        aff_pb = Affiliate.objects.create(sort='project', project=self.project_b)

        # 1. 회사 1 권한만 있는 본사 관리자(hq1_user): 회사 1의 Affiliate만 열람 가능
        self.client.force_authenticate(user=self.hq1_user)
        res = self.client.get('/api/v1/ledger/affiliate/')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        pks = [item['pk'] for item in res.data['results']]
        self.assertIn(aff_c1.pk, pks)
        self.assertNotIn(aff_c2.pk, pks)
        self.assertNotIn(aff_pa.pk, pks)
        self.assertNotIn(aff_pb.pk, pks)

        # 2. 슈퍼유저: 전체 Affiliate 열람 가능
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get('/api/v1/ledger/affiliate/')
        self.assertEqual(res_admin.status_code, http_status.HTTP_200_OK)
        admin_pks = [item['pk'] for item in res_admin.data['results']]
        self.assertIn(aff_c1.pk, admin_pks)
        self.assertIn(aff_c2.pk, admin_pks)
        self.assertIn(aff_pa.pk, admin_pks)
        self.assertIn(aff_pb.pk, admin_pks)

    def test_project_transactions_service_permission_filtering(self):
        """get_project_transactions 서비스가 사용자의 ledger.read 권한에 따라 프로젝트 거래를 정확히 필터링하는지 검증"""
        # 1. 프로젝트 A 권한자: 프로젝트 A 거래만 반환
        qs_a = get_project_transactions({}, user=self.user_a)
        pks_a = list(qs_a.values_list('pk', flat=True))
        self.assertIn(self.tx_pr_a.pk, pks_a)
        self.assertNotIn(self.tx_pr_b.pk, pks_a)

        # 2. 권한 없는 일반 유저: 0건
        no_perm_user = User.objects.create_user(
            username='noperm_user', email='noperm@test.com', password='password123'
        )
        qs_none = get_project_transactions({}, user=no_perm_user)
        self.assertEqual(qs_none.count(), 0)

        # 3. 슈퍼유저: 전체 프로젝트 거래 반환
        qs_admin = get_project_transactions({}, user=self.admin_user)
        pks_admin = list(qs_admin.values_list('pk', flat=True))
        self.assertIn(self.tx_pr_a.pk, pks_admin)
        self.assertIn(self.tx_pr_b.pk, pks_admin)


class LedgerAuditEnhancementsTests(LedgerTestBase):
    """정밀 검사 감사 지적사항 및 비즈니스 무결성 강화 검증 테스트"""

    def setUp(self):
        super().setUp()
        self.com_bank_acc = CompanyBankAccount.objects.create(
            company=self.company,
            bankcode=self.bank_code,
            alias_name='본사 계좌',
            number='100-200-3000',
        )

    def test_bank_transaction_cross_company_and_project_clean(self):
        """은행계좌와 거래 간 회사 및 프로젝트 불일치 시 ValidationError 발생 검증"""
        company2 = Company.objects.create(name='(주)타회사')
        tx_com = CompanyBankTransaction(
            company=company2,
            bank_account=self.com_bank_acc,  # self.com_bank_acc는 self.company 소속
            deal_date=date(2026, 7, 1),
            amount=100000,
            sort=self.sort_deposit,
        )
        with self.assertRaises(ValidationError) as cm:
            tx_com.clean()
        self.assertIn('bank_account', cm.exception.message_dict)

        tx_proj = ProjectBankTransaction(
            project=self.project_b,
            bank_account=self.bank_acc_a,  # self.bank_acc_a는 project_a 소속
            deal_date=date(2026, 7, 1),
            amount=100000,
            sort=self.sort_deposit,
        )
        with self.assertRaises(ValidationError) as cm:
            tx_proj.clean()
        self.assertIn('bank_account', cm.exception.message_dict)

    def test_project_accounting_entry_contract_cross_project_clean(self):
        """ProjectAccountingEntry의 계약/계약자 프로젝트 일치 및 requires_contract clean 검증"""
        # 1. 계약의 프로젝트 불일치 검증
        entry_wrong_project = ProjectAccountingEntry(
            project=self.project_b,
            account=self.account_deposit,
            amount=10000,
            contract=self.contract_a,  # self.contract_a는 project_a 소속
            transaction_id=uuid.uuid4(),
        )
        with self.assertRaises(ValidationError) as cm:
            entry_wrong_project.clean()
        self.assertIn('contract', cm.exception.message_dict)

        # 2. 계약자의 계약 불일치 검증
        other_contract = Contract.objects.create(
            project=self.project_a,
            order_group=self.order_group_a,
            unit_type=self.unit_type_a,
            key_unit=KeyUnit.objects.create(project=self.project_a, unit_type=self.unit_type_a, unit_code='A102'),
            serial_number='CONT-A-002',
            creator=self.admin_user,
        )
        other_contractor = Contractor.objects.create(
            contract=other_contract,
            name='이몽룡',
            status='2',
        )
        entry_mismatch_contractor = ProjectAccountingEntry(
            project=self.project_a,
            account=self.account_deposit,
            amount=10000,
            contract=self.contract_a,
            contractor=other_contractor,  # contractor는 other_contract 소속
            transaction_id=uuid.uuid4(),
        )
        with self.assertRaises(ValidationError) as cm:
            entry_mismatch_contractor.clean()
        self.assertIn('contractor', cm.exception.message_dict)

        # 3. requires_contract=True 계정이라도 회계 거래 입력 시 contract=None 허용 (미매칭 수납건 지원)
        entry_missing_contract = ProjectAccountingEntry(
            project=self.project_a,
            account=self.account_sales,  # requires_contract=True
            amount=10000,
            contract=None,
            transaction_id=uuid.uuid4(),
        )
        try:
            entry_missing_contract.clean()
        except ValidationError:
            self.fail("ProjectAccountingEntry with contract=None should not raise ValidationError")

    def test_cascade_delete_bank_transaction_deletes_accounting_entries(self):
        """BankTransaction.delete() 호출 시 연결된 AccountingEntry 및 ContractPayment CASCADE 삭제 검증"""
        # 1. CompanyBankTransaction 삭제 시 CompanyAccountingEntry 함께 삭제
        com_acc = CompanyAccount.objects.create(name='본사보통예금', code='1110', category='asset', depth=2)
        tx_com = CompanyBankTransaction.objects.create(
            company=self.company,
            bank_account=self.com_bank_acc,
            deal_date=date(2026, 8, 1),
            sort=self.sort_deposit,
            amount=50000,
            content='본사 입금 테스트',
        )
        entry_com = CompanyAccountingEntry.objects.create(
            company=self.company,
            transaction_id=tx_com.transaction_id,
            account=com_acc,
            amount=50000,
        )
        self.assertEqual(CompanyAccountingEntry.objects.filter(transaction_id=tx_com.transaction_id).count(), 1)
        tx_com.delete()
        self.assertEqual(CompanyAccountingEntry.objects.filter(transaction_id=tx_com.transaction_id).count(), 0)

        # 2. ProjectBankTransaction 삭제 시 ProjectAccountingEntry 및 ContractPayment 함께 삭제
        tx_proj = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 8, 1),
            sort=self.sort_deposit,
            amount=100000,
            content='프로젝트 입금 테스트',
        )
        entry_proj = ProjectAccountingEntry.objects.create(
            project=self.project_a,
            transaction_id=tx_proj.transaction_id,
            account=self.account_sales,
            amount=100000,
            contract=self.contract_a,
        )
        # entry_proj 생성 시 is_payment=True로 인해 ContractPayment가 자동 생성됨
        payment = ContractPayment.objects.get(accounting_entry=entry_proj)
        self.assertEqual(ProjectAccountingEntry.objects.filter(transaction_id=tx_proj.transaction_id).count(), 1)
        self.assertEqual(ContractPayment.objects.filter(pk=payment.pk).count(), 1)

        tx_proj.delete()
        self.assertEqual(ProjectAccountingEntry.objects.filter(transaction_id=tx_proj.transaction_id).count(), 0)
        self.assertEqual(ContractPayment.objects.filter(pk=payment.pk).count(), 0)

    def test_settlement_lock_on_direct_transaction_and_entry_destroy(self):
        """정산 마감일 이전의 은행 거래 및 분개 직접 삭제 시 차단 검증"""
        from ledger.models import ProjectLedgerCalculation
        ProjectLedgerCalculation.objects.create(
            project=self.project_a,
            calculated=date(2026, 7, 15),
            creator=self.admin_user,
        )

        # 마감일(7/15) 이전 거래 생성
        tx_proj = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 7, 10),
            sort=self.sort_deposit,
            amount=10000,
        )
        entry_proj = ProjectAccountingEntry.objects.create(
            project=self.project_a,
            transaction_id=tx_proj.transaction_id,
            account=self.account_deposit,
            amount=10000,
        )

        # 일반 담당자(self.user_a: ledger.delete 있으나 ledger.manage 없음)로 시도
        self.client.force_authenticate(user=self.user_a)
        res_del_tx = self.client.delete(f'/api/v1/ledger/project-transaction/{tx_proj.pk}/')
        self.assertEqual(res_del_tx.status_code, http_status.HTTP_400_BAD_REQUEST)

        res_del_entry = self.client.delete(f'/api/v1/ledger/project-accounting-entry/{entry_proj.pk}/')
        self.assertEqual(res_del_entry.status_code, http_status.HTTP_400_BAD_REQUEST)

    def test_account_generate_code_collision_avoidance(self):
        """Account._generate_code()가 기존 코드와 충돌 시 자동으로 다음 코드를 발급하는지 검증"""
        parent = CompanyAccount.objects.create(name='테스트대분류', category='asset', code='1000', depth=1)
        child1 = CompanyAccount.objects.create(name='테스트중분류1', parent=parent, category='asset', code='1100', depth=2)
        child2 = CompanyAccount(name='테스트중분류2', parent=parent, category='asset', depth=2)
        generated_code = child2._generate_code()
        self.assertNotEqual(generated_code, '1100')
        self.assertTrue(int(generated_code) > 1000)

    def test_protected_error_on_bank_account_destroy(self):
        """참조 중인 거래가 있는 계좌 삭제 시 400 Bad Request 반환 검증 (500 ProtectedError 방어)"""
        self.client.force_authenticate(user=self.admin_user)
        CompanyBankTransaction.objects.create(
            company=self.company,
            bank_account=self.com_bank_acc,
            deal_date=date(2026, 8, 2),
            sort=self.sort_deposit,
            amount=10000,
        )
        res = self.client.delete(f'/api/v1/ledger/company-bank-account/{self.com_bank_acc.pk}/')
        self.assertEqual(res.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('삭제할 수 없습니다', str(res.data))

    def test_project_composite_transaction_cross_project_contract_validation(self):
        """ProjectCompositeTransaction 생성 시 타 프로젝트 계약 지정 차단 검증"""
        self.client.force_authenticate(user=self.admin_user)

        payload = {
            'project': self.project_b.pk,
            'bank_account': self.bank_acc_b.pk,
            'deal_date': '2026-07-22',
            'sort': 1,
            'amount': 10000000,
            'content': '타 프로젝트 계약 수납 시도',
            'accounting_entries': [
                {
                    'account': self.account_sales.pk,
                    'amount': 10000000,
                    'trader': '홍길동',
                    'contract': self.contract_a.pk,  # contract_a는 project_a 소속!
                }
            ],
        }

        res = self.client.post('/api/v1/ledger/project-composite-transaction/', payload, format='json')
        self.assertEqual(res.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('accounting_entries', res.data)
        self.assertIn('일치하지 않습니다', str(res.data['accounting_entries']))

    def test_ledger_admin_query_optimization(self):
        """Admin prefetch 및 preload 동작 및 N+1 방지 메모리 검증 테스트"""
        from ledger.services.company_transaction import prefetch_company_transactions
        from ledger.services.project_transaction import prefetch_project_transactions
        from ledger.admin import preload_bank_transactions

        # 1. CompanyBankTransaction prefetch 검증
        tx_com = CompanyBankTransaction.objects.create(
            company=self.company,
            bank_account=self.com_bank_acc,
            deal_date=date(2026, 7, 23),
            sort=self.sort_deposit,
            amount=150000,
            content='본사 입금 테스트',
        )
        CompanyAccountingEntry.objects.create(
            company=self.company,
            transaction_id=tx_com.transaction_id,
            account=CompanyAccount.objects.create(code='4110', name='매출', category='revenue', depth=2),
            amount=150000,
            trader='매출처',
        )

        prefetch_company_transactions([tx_com])
        self.assertTrue(hasattr(tx_com, 'prefetched_accounting_entries'))
        self.assertEqual(len(tx_com.prefetched_accounting_entries), 1)
        self.assertTrue(tx_com.is_balanced)

        # 2. ProjectAccountingEntry preload 검증
        tx_proj = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 7, 24),
            sort=self.sort_withdraw,
            amount=50000,
            content='프로젝트 출금 테스트',
        )
        entry_proj = ProjectAccountingEntry.objects.create(
            project=self.project_a,
            transaction_id=tx_proj.transaction_id,
            account=self.account_expense,
            amount=50000,
            trader='출금처',
        )

        preload_bank_transactions([entry_proj], ProjectBankTransaction)
        self.assertTrue(hasattr(entry_proj, '_related_transaction'))
        self.assertEqual(entry_proj._related_transaction.pk, tx_proj.pk)
        self.assertEqual(entry_proj.sort, self.sort_withdraw)

    def test_account_hierarchy_filter_and_search_and_combination(self):
        """상위 계정(code='1000' -> 하위 '1010') 트리 탐색 필터링 및 카테고리+검색어 AND 결합 검증"""
        from ledger.services.company_transaction import get_company_transactions

        # 4자리 코드 체계: 부모 '1000' -> 자식 '1010' (code__startswith로는 매칭 불가했던 케이스)
        parent_acc = ProjectAccount.objects.create(
            code='1000', name='프로젝트자산대분류', category='asset', direction='deposit',
            depth=1, is_category_only=True, is_active=True
        )
        child_acc = ProjectAccount.objects.create(
            code='1010', name='프로젝트단기예금', parent=parent_acc, category='asset', direction='deposit',
            depth=2, is_category_only=False, is_active=True
        )

        tx_asset = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 8, 10),
            sort=self.sort_deposit,
            amount=200000,
            content='공통검색키워드 자산입금',
        )
        ProjectAccountingEntry.objects.create(
            project=self.project_a,
            transaction_id=tx_asset.transaction_id,
            account=child_acc,
            amount=200000,
            trader='자산거래처',
        )

        tx_expense = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 8, 11),
            sort=self.sort_withdraw,
            amount=300000,
            content='공통검색키워드 비용출금',
        )
        ProjectAccountingEntry.objects.create(
            project=self.project_a,
            transaction_id=tx_expense.transaction_id,
            account=self.account_expense,  # category='expense'
            amount=300000,
            trader='비용거래처',
        )

        # 1. 상위 분류 계정(parent_acc, code='1000')으로 필터링 시 하위 계정('1010') 거래가 조회되어야 함
        qs_by_parent = get_project_transactions({'account': parent_acc.pk}, user=self.admin_user)
        pks_by_parent = list(qs_by_parent.values_list('pk', flat=True))
        self.assertIn(tx_asset.pk, pks_by_parent)
        self.assertNotIn(tx_expense.pk, pks_by_parent)

        # 2. 상위 계정 이름(account_name='프로젝트자산대분류') 검색 시에도 하위 계정 거래 조회
        qs_by_name = get_project_transactions({'account_name': '프로젝트자산대분류'}, user=self.admin_user)
        self.assertIn(tx_asset.pk, list(qs_by_name.values_list('pk', flat=True)))

        # 3. account_category='asset' 과 search='공통검색키워드' 동시 지정 시 AND 조건으로 동작해야 함
        qs_combined = get_project_transactions(
            {'account_category': 'asset', 'search': '공통검색키워드'},
            user=self.admin_user
        )
        combined_pks = list(qs_combined.values_list('pk', flat=True))
        self.assertIn(tx_asset.pk, combined_pks)
        self.assertNotIn(tx_expense.pk, combined_pks)

        # 4. 본사(Company) 상위 계정('2000' -> '2010') 트리 필터링 및 AND 검색 검증
        com_parent = CompanyAccount.objects.create(
            code='2000', name='본사부채대분류', category='liability', direction='deposit',
            depth=1, is_category_only=True, is_active=True
        )
        com_child = CompanyAccount.objects.create(
            code='2010', name='본사단기차입금', parent=com_parent, category='liability', direction='deposit',
            depth=2, is_category_only=False, is_active=True
        )
        tx_com = CompanyBankTransaction.objects.create(
            company=self.company,
            bank_account=self.com_bank_acc,
            deal_date=date(2026, 8, 12),
            sort=self.sort_deposit,
            amount=500000,
            content='본사차입금입금',
        )
        CompanyAccountingEntry.objects.create(
            company=self.company,
            transaction_id=tx_com.transaction_id,
            account=com_child,
            amount=500000,
            trader='차입거래처',
        )
        qs_com = get_company_transactions({'account': com_parent.pk})
        self.assertIn(tx_com.pk, list(qs_com.values_list('pk', flat=True)))

    def test_prefetch_project_transactions_eliminates_n_plus_1_queries(self):
        """prefetch_project_transactions 적용 후 ProjectBankTransactionSerializer 직렬화 시 추가 쿼리 0건 검증"""
        from ledger.services.project_transaction import prefetch_project_transactions
        from apiV1.serializers.ledger import ProjectBankTransactionSerializer

        txs = []
        for idx in range(5):
            tx = ProjectBankTransaction.objects.create(
                project=self.project_a,
                bank_account=self.bank_acc_a,
                deal_date=date(2026, 8, 15),
                sort=self.sort_deposit,
                amount=100000 * (idx + 1),
                content=f'대량직렬화테스트-{idx}',
                creator=self.admin_user,
            )
            ProjectAccountingEntry.objects.create(
                project=self.project_a,
                transaction_id=tx.transaction_id,
                account=self.account_sales,
                amount=100000 * (idx + 1),
                contract=self.contract_a,
                contractor=self.contractor_a,
                trader=f'거래처-{idx}',
            )
            txs.append(tx)

        loaded_txs = list(
            ProjectBankTransaction.objects.filter(pk__in=[t.pk for t in txs]).select_related(
                'project', 'bank_account', 'sort', 'creator'
            )
        )
        prefetch_project_transactions(loaded_txs)

        with self.assertNumQueries(0):
            serialized = ProjectBankTransactionSerializer(loaded_txs, many=True).data
            self.assertEqual(len(serialized), 5)

    def test_put_composite_transaction_balance_and_split_overpayment_validation(self):
        """PUT 전체 교체 시 삭제된 분개 제외 합계 검증 및 동일 계약 분할 분개 합산 초과 수납 차단 검증"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 동일 계약(잔여 5억)에 대해 3억 + 3억 = 6억으로 분할 수납 시도 시 합산 금액으로 차단되어야 함
        split_overpay_payload = {
            'project': self.project_a.pk,
            'bank_account': self.bank_acc_a.pk,
            'deal_date': '2026-08-20',
            'amount': 600000000,
            'sort': 1,
            'content': '분할 수납 초과 시도',
            'accounting_entries': [
                {
                    'account': self.account_sales.pk,
                    'amount': 300000000,
                    'contract': self.contract_a.pk,
                    'contractor': self.contractor_a.pk,
                    'trader': '홍길동',
                },
                {
                    'account': self.account_sales.pk,
                    'amount': 300000000,
                    'contract': self.contract_a.pk,
                    'contractor': self.contractor_a.pk,
                    'trader': '홍길동',
                },
            ],
        }
        res_overpay = self.client.post(
            '/api/v1/ledger/project-composite-transaction/',
            data=split_overpay_payload,
            format='json',
        )
        self.assertEqual(res_overpay.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('잔여 미납액', str(res_overpay.data))

        # 2. 정상 분할 거래(50,000 + 50,000 = 100,000) 생성 후 PUT으로 분개 1개만 남기고 거래금액을 100,000으로 유지하면 불일치 차단
        create_res = self.client.post(
            '/api/v1/ledger/project-composite-transaction/',
            data={
                'project': self.project_a.pk,
                'bank_account': self.bank_acc_a.pk,
                'deal_date': '2026-08-21',
                'amount': 100000,
                'sort': 1,
                'content': '분할 입금',
                'accounting_entries': [
                    {'account': self.account_deposit.pk, 'amount': 50000, 'trader': 'A'},
                    {'account': self.account_deposit.pk, 'amount': 50000, 'trader': 'B'},
                ],
            },
            format='json',
        )
        self.assertEqual(create_res.status_code, http_status.HTTP_201_CREATED)
        tx_pk = create_res.data['bank_transaction']['pk']
        first_entry_pk = create_res.data['accounting_entries'][0]['pk']

        # PUT 요청으로 분개 1건(50,000원)만 전달하면서 은행 거래금액은 100,000원인 경우 400 에러 발생해야 함
        put_unbalanced_res = self.client.put(
            f'/api/v1/ledger/project-composite-transaction/{tx_pk}/',
            data={
                'project': self.project_a.pk,
                'bank_account': self.bank_acc_a.pk,
                'deal_date': '2026-08-21',
                'amount': 100000,
                'sort': 1,
                'content': '분할 입금 수정',
                'accounting_entries': [
                    {'pk': first_entry_pk, 'account': self.account_deposit.pk, 'amount': 50000, 'trader': 'A'},
                ],
            },
            format='json',
        )
        self.assertEqual(put_unbalanced_res.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('accounting_entries', put_unbalanced_res.data)

        # PUT 요청으로 은행 거래금액도 50,000원으로 맞추면 정상 업데이트 및 updator 기록
        put_balanced_res = self.client.put(
            f'/api/v1/ledger/project-composite-transaction/{tx_pk}/',
            data={
                'project': self.project_a.pk,
                'bank_account': self.bank_acc_a.pk,
                'deal_date': '2026-08-21',
                'amount': 50000,
                'sort': 1,
                'content': '분할 입금 정상 축소',
                'accounting_entries': [
                    {'pk': first_entry_pk, 'account': self.account_deposit.pk, 'amount': 50000, 'trader': 'A'},
                ],
            },
            format='json',
        )
        self.assertEqual(put_balanced_res.status_code, http_status.HTTP_200_OK)
        updated_tx = ProjectBankTransaction.objects.get(pk=tx_pk)
        self.assertEqual(updated_tx.updator, self.user_a)

    def test_settlement_lock_on_entry_update_and_readonly_master_endpoints(self):
        """정산 마감일 이전 분개 수정 차단, 마스터 엔드포인트 쓰기 권한 방어 및 엑셀 내보내기 RLS 검증"""
        ProjectLedgerCalculation.objects.create(
            project=self.project_a,
            calculated=date(2026, 7, 15),
            creator=self.admin_user,
        )
        tx_locked = ProjectBankTransaction.objects.create(
            project=self.project_a,
            bank_account=self.bank_acc_a,
            deal_date=date(2026, 7, 10),
            sort=self.sort_deposit,
            amount=100000,
            content='마감 거래',
        )
        entry_locked = ProjectAccountingEntry.objects.create(
            project=self.project_a,
            transaction_id=tx_locked.transaction_id,
            account=self.account_deposit,
            amount=100000,
            trader='기존거래처',
        )

        # 1. 일반 담당자(user_a, ledger.manage 없음)가 마감된 분개의 거래처(중요 필드) 수정 시도 -> 400 차단
        self.client.force_authenticate(user=self.user_a)
        res_patch_trader = self.client.patch(
            f'/api/v1/ledger/project-accounting-entry/{entry_locked.pk}/',
            data={'trader': '변경거래처'},
            format='json',
        )
        self.assertEqual(res_patch_trader.status_code, http_status.HTTP_400_BAD_REQUEST)

        # 단, 계정과목(account)만 단독 변경하는 것은 허용됨
        other_acc = ProjectAccount.objects.create(
            code='1120', name='별단예금', category='asset', direction='deposit', is_active=True
        )
        res_patch_acc = self.client.patch(
            f'/api/v1/ledger/project-accounting-entry/{entry_locked.pk}/',
            data={'account': other_acc.pk},
            format='json',
        )
        self.assertEqual(res_patch_acc.status_code, http_status.HTTP_200_OK)

        # 2. 일반 담당자(user_a)가 BankCode 또는 ProjectAccount 마스터 생성 시도 -> 403 Forbidden
        res_bank_code = self.client.post(
            '/api/v1/ledger/bank-code/',
            data={'code': '999', 'name': '불법은행'},
            format='json',
        )
        self.assertEqual(res_bank_code.status_code, http_status.HTTP_403_FORBIDDEN)

        res_proj_acc = self.client.post(
            '/api/v1/ledger/project-account/',
            data={'code': '9999', 'name': '불법계정', 'category': 'expense', 'direction': 'withdraw'},
            format='json',
        )
        self.assertEqual(res_proj_acc.status_code, http_status.HTTP_403_FORBIDDEN)

        # 3. LastDealDate 엔드포인트는 ReadOnly이므로 슈퍼유저라도 POST/DELETE 시 405 Method Not Allowed 반환
        self.client.force_authenticate(user=self.admin_user)
        res_last_deal_post = self.client.post('/api/v1/ledger/project-last-deal-date/', data={}, format='json')
        self.assertEqual(res_last_deal_post.status_code, http_status.HTTP_405_METHOD_NOT_ALLOWED)
        res_com_last_deal_post = self.client.post('/api/v1/ledger/company-last-deal-date/', data={}, format='json')
        self.assertEqual(res_com_last_deal_post.status_code, http_status.HTTP_405_METHOD_NOT_ALLOWED)

        # 4. 엑셀 내보내기 엔드포인트 RLS: user_a(프로젝트 A 권한만 보유)가 프로젝트 B 엑셀 다운로드 시도 -> 403 차단
        self.client.force_login(self.user_a)
        res_excel_b = self.client.get(f'/excel/pro-balance/?project={self.project_b.pk}')
        self.assertEqual(res_excel_b.status_code, http_status.HTTP_403_FORBIDDEN)

        res_excel_tx_b = self.client.get(f'/excel/pro-trans/?project={self.project_b.pk}')
        self.assertEqual(res_excel_tx_b.status_code, http_status.HTTP_403_FORBIDDEN)

        # 반면 권한이 있는 프로젝트 A 엑셀 다운로드는 200 OK
        res_excel_a = self.client.get(f'/excel/pro-balance/?project={self.project_a.pk}')
        self.assertEqual(res_excel_a.status_code, http_status.HTTP_200_OK)



