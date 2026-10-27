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


class BankScrapingAPITests(LedgerTestBase):
    """은행 API 자동 수집 및 도메인(회사/프로젝트/전도금) 격리/승인 테스트"""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

        # 1. 제2회사 생성 (멀티 컴퍼니 검증용)
        self.company2 = Company.objects.create(name='(주)테스트시행사')

        # 2. 본사 계좌 생성
        self.com1_bank = CompanyBankAccount.objects.create(
            company=self.company,
            bankcode=self.bank_code,
            alias_name='본사1 국민계좌',
            number='111-11-11111',
            holder='(주)테스트건설',
            order=1
        )
        self.com2_bank = CompanyBankAccount.objects.create(
            company=self.company2,
            bankcode=self.bank_code,
            alias_name='본사2 국민계좌',
            number='222-22-22222',
            holder='(주)테스트시행사',
            order=2
        )

        # 3. 프로젝트 계좌 생성 (신탁계좌 vs 운영비 전도금 계좌)
        self.proj_trust_bank = ProjectBankAccount.objects.create(
            project=self.project_a,
            bankcode=self.bank_code,
            alias_name='프로젝트A 신탁수납계좌',
            number='333-33-33333',
            holder='한국신탁(프로젝트A)',
            is_imprest=False,
            order=1
        )
        self.proj_imprest_bank = ProjectBankAccount.objects.create(
            project=self.project_a,
            bankcode=self.bank_code,
            alias_name='프로젝트A 운영비전도금계좌',
            number='444-44-44444',
            holder='프로젝트A 운영비전도금',
            is_imprest=True,
            order=2
        )

        # 4. 연동 계좌(BankApiCredential) 생성
        from ledger.models import BankApiCredential, RawBankTransaction
        self.cred_com1 = BankApiCredential.objects.create(
            company_bank_account=self.com1_bank,
            connected_id='cid_com1',
            bank_code='0004',
            account_number='1111111111',
            is_active=True
        )
        self.cred_com2 = BankApiCredential.objects.create(
            company_bank_account=self.com2_bank,
            connected_id='cid_com2',
            bank_code='0004',
            account_number='2222222222',
            is_active=True
        )
        self.cred_proj_trust = BankApiCredential.objects.create(
            project_bank_account=self.proj_trust_bank,
            connected_id='cid_proj_trust',
            bank_code='0004',
            account_number='3333333333',
            is_active=True
        )
        self.cred_proj_imprest = BankApiCredential.objects.create(
            project_bank_account=self.proj_imprest_bank,
            connected_id='cid_proj_imprest',
            bank_code='0004',
            account_number='4444444444',
            is_active=True
        )

        # 5. 회계 계정과목 생성
        self.com_account = CompanyAccount.objects.create(
            code='5110', name='여비교통비', category='expense', depth=2
        )
        self.proj_account = ProjectAccount.objects.create(
            code='5210', name='프로젝트운영비', category='expense', depth=2
        )

    def test_credential_filtering_by_company_and_project(self):
        """BankApiCredential 목록 조회 시 회사 및 프로젝트 파라미터 격리 필터링 검증"""
        # (1) 본사 1 필터링: 본사 1 계좌만 반환
        res = self.client.get(f'/api/v1/ledger/credentials/?company={self.company.pk}')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        pks = [item['pk'] for item in res.data['results']]
        self.assertIn(self.cred_com1.pk, pks)
        self.assertNotIn(self.cred_com2.pk, pks)
        self.assertNotIn(self.cred_proj_trust.pk, pks)

        # (2) 본사 2 필터링: 본사 2 계좌만 반환
        res2 = self.client.get(f'/api/v1/ledger/credentials/?company={self.company2.pk}')
        self.assertEqual(res2.status_code, http_status.HTTP_200_OK)
        pks2 = [item['pk'] for item in res2.data['results']]
        self.assertIn(self.cred_com2.pk, pks2)
        self.assertNotIn(self.cred_com1.pk, pks2)

        # (3) 프로젝트 A 필터링: 프로젝트 A의 계좌 2개만 반환
        res_pr = self.client.get(f'/api/v1/ledger/credentials/?project={self.project_a.pk}')
        self.assertEqual(res_pr.status_code, http_status.HTTP_200_OK)
        pks_pr = [item['pk'] for item in res_pr.data['results']]
        self.assertEqual(len(pks_pr), 2)
        self.assertIn(self.cred_proj_trust.pk, pks_pr)
        self.assertIn(self.cred_proj_imprest.pk, pks_pr)

        # (4) 프로젝트 A 내 운영비 전도금(is_imprest=true) 필터링: 전도금 계좌 1개만 반환
        res_imp = self.client.get(f'/api/v1/ledger/credentials/?project={self.project_a.pk}&is_imprest=true')
        self.assertEqual(res_imp.status_code, http_status.HTTP_200_OK)
        pks_imp = [item['pk'] for item in res_imp.data['results']]
        self.assertEqual(len(pks_imp), 1)
        self.assertIn(self.cred_proj_imprest.pk, pks_imp)
        self.assertNotIn(self.cred_proj_trust.pk, pks_imp)

    def test_raw_transaction_filtering_by_domain(self):
        """RawBankTransaction 조회 시 회사별/프로젝트별/전도금별 필터링 검증"""
        from ledger.models import RawBankTransaction

        # 각 계좌별 거래 생성
        tx_c1 = RawBankTransaction.objects.create(
            credential=self.cred_com1,
            deal_date=date(2026, 7, 1),
            sort_type='withdraw',
            amount=50000,
            client_name='본사1 지출처',
            tx_hash=RawBankTransaction.generate_hash('1111111111', '2026-07-01', None, 'withdraw', 50000, None, '본사1 지출처', '')
        )
        tx_c2 = RawBankTransaction.objects.create(
            credential=self.cred_com2,
            deal_date=date(2026, 7, 2),
            sort_type='withdraw',
            amount=80000,
            client_name='본사2 지출처',
            tx_hash=RawBankTransaction.generate_hash('2222222222', '2026-07-02', None, 'withdraw', 80000, None, '본사2 지출처', '')
        )
        tx_trust = RawBankTransaction.objects.create(
            credential=self.cred_proj_trust,
            deal_date=date(2026, 7, 3),
            sort_type='deposit',
            amount=50000000,
            client_name='홍길동 101-101',
            tx_hash=RawBankTransaction.generate_hash('3333333333', '2026-07-03', None, 'deposit', 50000000, None, '홍길동 101-101', '')
        )
        tx_imprest = RawBankTransaction.objects.create(
            credential=self.cred_proj_imprest,
            deal_date=date(2026, 7, 4),
            sort_type='withdraw',
            amount=300000,
            client_name='프로젝트 식대',
            tx_hash=RawBankTransaction.generate_hash('4444444444', '2026-07-04', None, 'withdraw', 300000, None, '프로젝트 식대', '')
        )

        # (1) 본사 1 거래 필터링
        res_c1 = self.client.get(f'/api/v1/ledger/raw-transactions/?company={self.company.pk}')
        self.assertEqual(res_c1.status_code, http_status.HTTP_200_OK)
        tx_pks_c1 = [item['pk'] for item in res_c1.data['results']]
        self.assertIn(tx_c1.pk, tx_pks_c1)
        self.assertNotIn(tx_c2.pk, tx_pks_c1)
        self.assertNotIn(tx_trust.pk, tx_pks_c1)

        # (2) 프로젝트 A 내 신탁수납(is_imprest=false) 필터링
        res_trust = self.client.get(f'/api/v1/ledger/raw-transactions/?project={self.project_a.pk}&is_imprest=false')
        self.assertEqual(res_trust.status_code, http_status.HTTP_200_OK)
        tx_pks_trust = [item['pk'] for item in res_trust.data['results']]
        self.assertIn(tx_trust.pk, tx_pks_trust)
        self.assertNotIn(tx_imprest.pk, tx_pks_trust)

        # (3) 프로젝트 A 내 운영비 전도금(is_imprest=true) 필터링
        res_imp = self.client.get(f'/api/v1/ledger/raw-transactions/?project={self.project_a.pk}&is_imprest=true')
        self.assertEqual(res_imp.status_code, http_status.HTTP_200_OK)
        tx_pks_imp = [item['pk'] for item in res_imp.data['results']]
        self.assertIn(tx_imprest.pk, tx_pks_imp)
        self.assertNotIn(tx_trust.pk, tx_pks_imp)

    def test_confirm_raw_transaction_creates_proper_ledger_records(self):
        """수집 거래 단건 승인 시 정식 원장(본사 vs 프로젝트)으로 정확히 승격되는지 검증"""
        from ledger.models import RawBankTransaction, CompanyBankTransaction, ProjectBankTransaction

        # 본사 거래 생성 및 승인
        raw_com = RawBankTransaction.objects.create(
            credential=self.cred_com1,
            deal_date=date(2026, 7, 5),
            sort_type='withdraw',
            amount=120000,
            client_name='교통비 테스트',
            status='ready',
            suggested_company_account=self.com_account,
            confidence_score=95,
            tx_hash='hash_test_com_confirm'
        )

        res = self.client.post(f'/api/v1/ledger/raw-transactions/{raw_com.pk}/confirm/', {})
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)

        raw_com.refresh_from_db()
        self.assertEqual(raw_com.status, 'confirmed')
        self.assertEqual(raw_com.confirmed_by, self.admin_user)
        self.assertIsNotNone(raw_com.created_company_transaction)

        com_tx = raw_com.created_company_transaction
        self.assertEqual(com_tx.company, self.company)
        self.assertEqual(com_tx.amount, 120000)
        self.assertEqual(com_tx.accounting_entries.first().account, self.com_account)

        # 프로젝트 전도금 거래 생성 및 승인
        raw_proj = RawBankTransaction.objects.create(
            credential=self.cred_proj_imprest,
            deal_date=date(2026, 7, 6),
            sort_type='withdraw',
            amount=450000,
            client_name='프로젝트 문구류',
            status='ready',
            suggested_project_account=self.proj_account,
            confidence_score=90,
            tx_hash='hash_test_proj_confirm'
        )

        res_pr = self.client.post(f'/api/v1/ledger/raw-transactions/{raw_proj.pk}/confirm/', {})
        self.assertEqual(res_pr.status_code, http_status.HTTP_200_OK)

        raw_proj.refresh_from_db()
        self.assertEqual(raw_proj.status, 'confirmed')
        self.assertIsNotNone(raw_proj.created_project_transaction)

        pr_tx = raw_proj.created_project_transaction
        self.assertEqual(pr_tx.project, self.project_a)
        self.assertEqual(pr_tx.amount, 450000)
        self.assertEqual(pr_tx.accounting_entries.first().account, self.proj_account)

    def test_confirm_raw_transaction_composite_split(self):
        """복합 거래(수수료 분리 등) 분할 승인 시 1개의 은행거래와 N개의 회계전표 생성 검증"""
        from ledger.models import RawBankTransaction, CompanyAccount

        fee_account = CompanyAccount.objects.create(
            code='5120', name='지급수수료', category='expense', depth=2
        )

        raw_split = RawBankTransaction.objects.create(
            credential=self.cred_com1,
            deal_date=date(2026, 7, 7),
            sort_type='withdraw',
            amount=1500,
            client_name='차입금 상환 및 수수료',
            status='ready',
            tx_hash='hash_test_split_confirm'
        )

        # 1. 금액 불일치 테스트 (1000 + 400 != 1500) -> 400 에러
        invalid_payload = {
            'entries': [
                {'account_id': self.com_account.pk, 'amount': 1000, 'trader': '차입금 상환'},
                {'account_id': fee_account.pk, 'amount': 400, 'trader': '이체수수료'},
            ]
        }
        res_fail = self.client.post(f'/api/v1/ledger/raw-transactions/{raw_split.pk}/confirm/', invalid_payload, format='json')
        self.assertEqual(res_fail.status_code, http_status.HTTP_400_BAD_REQUEST)

        # 2. 정상 분할 테스트 (1000 + 500 == 1500)
        valid_payload = {
            'entries': [
                {'account_id': self.com_account.pk, 'amount': 1000, 'trader': '차입금 상환'},
                {'account_id': fee_account.pk, 'amount': 500, 'trader': '이체수수료'},
            ]
        }
        res_ok = self.client.post(f'/api/v1/ledger/raw-transactions/{raw_split.pk}/confirm/', valid_payload, format='json')
        self.assertEqual(res_ok.status_code, http_status.HTTP_200_OK)

        raw_split.refresh_from_db()
        self.assertEqual(raw_split.status, 'confirmed')
        self.assertIsNotNone(raw_split.created_company_transaction)

        com_tx = raw_split.created_company_transaction
        self.assertEqual(com_tx.amount, 1500)
        self.assertEqual(com_tx.accounting_entries.count(), 2)

        entries = list(com_tx.accounting_entries.order_by('id'))
        self.assertEqual(entries[0].account, self.com_account)
        self.assertEqual(entries[0].amount, 1000)
        self.assertEqual(entries[0].trader, '차입금 상환')

        self.assertEqual(entries[1].account, fee_account)
        self.assertEqual(entries[1].amount, 500)
        self.assertEqual(entries[1].trader, '이체수수료')

    def test_register_certificate_and_batch_link(self):
        """인증서/계정 등록(Mock) 및 보유 계좌 일괄 연동 API 검증"""
        from unittest.mock import patch
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_authenticate(user=self.admin_user)

        with patch('ledger.services.codef_client.CodefClient.create_account') as mock_create, \
             patch('ledger.services.codef_client.CodefClient.fetch_account_list') as mock_list, \
             patch('ledger.services.codef_client.CodefClient.encrypt_rsa', return_value='ENC_PW'):

            mock_create.return_value = 'MOCK-CONNECTED-ID-123'
            mock_list.return_value = [
                {
                    'resAccount': '1111111111',  # com_bank_acc1과 일치
                    'resAccountName': '기업보통예금1',
                    'resAccountHolder': '(주)테스트건설',
                },
                {
                    'resAccount': '5555555555',  # 신규 계좌
                    'resAccountName': '운영비전도금신규',
                    'resAccountHolder': '(주)테스트건설',
                }
            ]

            # 1-A. der + key 분리형 호출
            der_file = SimpleUploadedFile("signCert.der", b"fake_der_content", content_type="application/octet-stream")
            key_file = SimpleUploadedFile("signPri.key", b"fake_key_content", content_type="application/octet-stream")

            res = self.client.post(
                '/api/v1/ledger/credentials/register_certificate/',
                {
                    'bank_code': '0004',
                    'login_type': '0',
                    'password': 'password123!',
                    'der_file': der_file,
                    'key_file': key_file
                },
                format='multipart'
            )
            self.assertEqual(res.status_code, http_status.HTTP_200_OK)
            data = res.json()
            self.assertEqual(data['connected_id'], 'MOCK-CONNECTED-ID-123')
            self.assertEqual(len(data['accounts']), 2)
            # 첫 번째 계좌는 기존 com1_bank와 자동 매칭되어야 함
            self.assertEqual(data['accounts'][0]['matched_type'], 'company')
            self.assertEqual(data['accounts'][0]['matched_account_id'], self.com1_bank.id)

            # 1-B. cert_file 단일 통합 파일 (.pfx, .p12, .pt2) 호출
            single_file = SimpleUploadedFile("company_cert.pt2", b"fake_pfx_content", content_type="application/octet-stream")
            res_single = self.client.post(
                '/api/v1/ledger/credentials/register_certificate/',
                {
                    'bank_code': '0004',
                    'login_type': '0',
                    'password': 'password123!',
                    'cert_file': single_file
                },
                format='multipart'
            )
            self.assertEqual(res_single.status_code, http_status.HTTP_200_OK)
            self.assertEqual(res_single.json()['connected_id'], 'MOCK-CONNECTED-ID-123')


            # 2. batch_link 호출 (두 계좌 일괄 연동)
            link_payload = {
                'connected_id': 'MOCK-CONNECTED-ID-123',
                'bank_code': '0004',
                'items': [
                    {
                        'account_number': '1111111111',
                        'target_type': 'company',
                        'existing_account_id': self.com1_bank.id,
                    },
                    {
                        'account_number': '5555555555',
                        'account_name': '신규전도금',
                        'target_type': 'project',
                        'project_id': self.project_a.id,
                        'is_imprest': True,
                    }
                ]
            }
            res_link = self.client.post('/api/v1/ledger/credentials/batch_link/', link_payload, format='json')
            self.assertEqual(res_link.status_code, http_status.HTTP_200_OK)
            self.assertEqual(res_link.json()['linked_count'], 2)

            # DB에 정상 생성/연동되었는지 확인
            from ledger.models import BankApiCredential, ProjectBankAccount
            cred_new = BankApiCredential.objects.get(account_number='5555555555')
            self.assertEqual(cred_new.connected_id, 'MOCK-CONNECTED-ID-123')
            self.assertTrue(cred_new.project_bank_account.is_imprest)
            self.assertEqual(cred_new.project_bank_account.project, self.project_a)


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

    def test_bank_api_credential_save_full_clean(self):
        """BankApiCredential.save() 호출 시 clean() 유효성 검사 강제 동작 검증"""
        from ledger.models import BankApiCredential
        # 둘 다 None인 경우
        cred_empty = BankApiCredential(
            bank_code='004',
            account_number='111222333',
        )
        with self.assertRaises(ValidationError):
            cred_empty.save()

        # 둘 다 지정된 경우
        cred_both = BankApiCredential(
            bank_code='004',
            account_number='111222333',
            company_bank_account=self.com_bank_acc,
            project_bank_account=self.bank_acc_a,
        )
        with self.assertRaises(ValidationError):
            cred_both.save()

    def test_raw_transaction_and_credential_rls_isolation(self):
        """비인가 사용자의 타 프로젝트/회사 Credential 및 RawTransaction 접근/승인 차단 검증"""
        from ledger.models import BankApiCredential, RawBankTransaction

        cred_b = BankApiCredential.objects.create(
            project_bank_account=self.bank_acc_b,
            connected_id='cid_b',
            bank_code='004',
            account_number='999888777',
            is_active=True,
        )
        raw_b = RawBankTransaction.objects.create(
            credential=cred_b,
            deal_date=date(2026, 7, 20),
            sort_type='deposit',
            amount=5000000,
            client_name='B수납자',
            status='ready',
            tx_hash='hash_b_rls_test',
        )

        # user_a(프로젝트 A만 접근 가능)로 로그인
        self.client.force_authenticate(user=self.user_a)

        # 1. Credential 목록 조회 시 프로젝트 B의 Credential은 조회되지 않아야 함
        res_cred = self.client.get('/api/v1/ledger/credentials/')
        self.assertEqual(res_cred.status_code, http_status.HTTP_200_OK)
        cred_pks = [item['pk'] for item in res_cred.data.get('results', [])]
        self.assertNotIn(cred_b.pk, cred_pks)

        # 2. Raw Transaction 목록 조회 시 프로젝트 B 거래는 조회되지 않아야 함
        res_raw = self.client.get('/api/v1/ledger/raw-transactions/')
        self.assertEqual(res_raw.status_code, http_status.HTTP_200_OK)
        raw_pks = [item['pk'] for item in res_raw.data.get('results', [])]
        self.assertNotIn(raw_b.pk, raw_pks)

        # 3. 프로젝트 B 거래 승인(confirm) 시도 시 404 (또는 403) 차단되어야 함
        res_confirm = self.client.post(f'/api/v1/ledger/raw-transactions/{raw_b.pk}/confirm/', {})
        self.assertIn(res_confirm.status_code, (http_status.HTTP_404_NOT_FOUND, http_status.HTTP_403_FORBIDDEN))

    def test_confirm_raw_transaction_concurrency_lock_and_idempotency(self):
        """confirm_raw_transaction 이중 호출 시 이미 승인된 거래 에러 방어 검증"""
        from ledger.models import BankApiCredential, RawBankTransaction
        from ledger.services.transaction_confirm import confirm_raw_transaction

        cred_a = BankApiCredential.objects.create(
            project_bank_account=self.bank_acc_a,
            connected_id='cid_a',
            bank_code='004',
            account_number='111222333',
            is_active=True,
        )
        raw_a = RawBankTransaction.objects.create(
            credential=cred_a,
            deal_date=date(2026, 7, 21),
            sort_type='withdraw',
            amount=200000,
            client_name='소모품비',
            status='ready',
            suggested_project_account=self.account_expense,
            tx_hash='hash_a_concurrency_test',
        )

        # 1차 승인 성공
        result = confirm_raw_transaction(raw_a, user=self.admin_user)
        self.assertTrue(result['success'])

        raw_a.refresh_from_db()
        self.assertEqual(raw_a.status, 'confirmed')

        # 2차 동시/중복 승인 시도 시 ValueError 발생
        with self.assertRaises(ValueError) as cm:
            confirm_raw_transaction(raw_a, user=self.admin_user)
        self.assertIn('이미 승인 완료된 거래입니다', str(cm.exception))

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


