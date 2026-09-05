import uuid
from datetime import date
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
)

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
            content='A현장 입금 거래',
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
            content='B현장 입금 거래',
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
