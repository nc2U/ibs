import uuid
from datetime import date
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from company.models import Company
from contract.models import OrderGroup, Contract, ContractPrice
from items.models import UnitType, KeyUnit, HouseUnit, BuildingUnit, UnitFloorType
from project.models import Project, ProjectIncBudget
from work.models.project import IssueProject
from ibs.models import AccountSort
from ledger.models import ProjectAccount, ProjectBankAccount, ProjectBankTransaction, ProjectAccountingEntry, BankCode
from payment.models import (
    InstallmentPaymentOrder, SalesPriceByGT, PaymentPerInstallment,
    DownPayment, ContractPayment, OverDueRule
)

User = get_user_model()


class PaymentTestCaseBase(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='password123'
        )
        self.client.force_authenticate(user=self.user)

        # Create basic company and issue project
        self.company = Company.objects.create(name='Test Company')
        self.issue_project = IssueProject.objects.create(
            company=self.company,
            name='Test Issue Project',
            slug='test-issue-project',
            creator=self.user
        )

        # Create project
        self.project = Project.objects.create(
            issue_project=self.issue_project,
            name='Test Project',
            order=1,
            kind='1',
            start_year='2026',
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24
        )

        # Create order group
        self.order_group = OrderGroup.objects.create(
            project=self.project,
            order_number=1,
            sort='2',
            name='1차 일반분양',
            is_default_for_uncontracted=True
        )

        # Create unit type
        self.unit_type = UnitType.objects.create(
            project=self.project,
            name='84A',
            sort='1',
            color='#FF0000',
            average_price=300000000,
            num_unit=10
        )

        # Create floor type
        self.floor_type = UnitFloorType.objects.create(
            project=self.project,
            start_floor=1,
            end_floor=5,
            extra_cond='',
            alias_name='1-5층'
        )

        # Create building and key units
        self.building_unit = BuildingUnit.objects.create(
            project=self.project,
            name='101동'
        )
        self.key_unit = KeyUnit.objects.create(
            project=self.project,
            unit_type=self.unit_type,
            unit_code='A001'
        )
        self.house_unit = HouseUnit.objects.create(
            unit_type=self.unit_type,
            building_unit=self.building_unit,
            floor_type=self.floor_type,
            key_unit=self.key_unit,
            name='101호',
            bldg_line=1,
            floor_no=1
        )

        # Create installment orders
        self.pay_order_down = InstallmentPaymentOrder.objects.create(
            project=self.project,
            type_sort='1',
            pay_sort='1',
            pay_code=1,
            pay_time=1,
            pay_name='계약금',
            pay_ratio=10.0
        )
        self.pay_order_remain = InstallmentPaymentOrder.objects.create(
            project=self.project,
            type_sort='1',
            pay_sort='3',
            pay_code=10,
            pay_time=10,
            pay_name='잔금',
            pay_ratio=90.0
        )

        # Sales Price
        self.sales_price = SalesPriceByGT.objects.create(
            project=self.project,
            order_group=self.order_group,
            unit_type=self.unit_type,
            unit_floor_type=self.floor_type,
            price=300000000
        )

        # Down payment
        self.down_payment = DownPayment.objects.create(
            project=self.project,
            order_group=self.order_group,
            unit_type=self.unit_type,
            payment_amount=30000000
        )

        # Bank elements
        self.bank_code = BankCode.objects.create(code='001', name='Test Bank')
        self.project_bank_account = ProjectBankAccount.objects.create(
            project=self.project,
            bankcode=self.bank_code,
            alias_name='Test Project Account',
            number='123-456-7890',
            holder='Test Holder'
        )
        self.account_sort_deposit = AccountSort.objects.create(name='입금')
        self.project_account_payment = ProjectAccount.objects.create(
            name='분양대금',
            code='4100',
            category='revenue',
            is_payment=True,
            requires_contract=True
        )

        # Create ProjectIncBudget
        self.project_inc_budget = ProjectIncBudget.objects.create(
            project=self.project,
            account=self.project_account_payment,
            order_group=self.order_group,
            unit_type=self.unit_type,
            quantity=10,
            budget=3000000000
        )

        # Create Contract and Contract Price
        self.contract = Contract.objects.create(
            project=self.project,
            serial_number='CONT-2026-0001',
            order_group=self.order_group,
            unit_type=self.unit_type,
            key_unit=self.key_unit
        )
        self.contract_price = ContractPrice.objects.create(
            contract=self.contract,
            house_unit=self.house_unit,
            price=300000000,
            is_cache_valid=True,
            payment_amounts={"1": 30000000, "10": 270000000}
        )

        # ProjectBankTransaction
        self.bank_transaction = ProjectBankTransaction.objects.create(
            project=self.project,
            bank_account=self.project_bank_account,
            deal_date=date(2026, 1, 1),
            sort=self.account_sort_deposit,
            amount=30000000,
            content='1차 계약금 납부',
            creator=self.user
        )

        # ProjectAccountingEntry
        self.accounting_entry = ProjectAccountingEntry.objects.create(
            project=self.project,
            transaction_id=self.bank_transaction.transaction_id,
            account=self.project_account_payment,
            amount=30000000,
            trader='홍길동',
            contract=self.contract
        )


class InstallmentPaymentOrderModelTests(PaymentTestCaseBase):
    def test_validation_prep_discount_ratio(self):
        order = InstallmentPaymentOrder(
            project=self.project,
            pay_name="test order",
            pay_code=2,
            pay_time=2,
            is_prep_discount=True,
            prep_discount_ratio=None
        )
        with self.assertRaises(ValidationError):
            order.clean()

    def test_validation_late_penalty_ratio(self):
        order = InstallmentPaymentOrder(
            project=self.project,
            pay_name="test order",
            pay_code=2,
            pay_time=2,
            is_late_penalty=True,
            late_penalty_ratio=None
        )
        with self.assertRaises(ValidationError):
            order.clean()

    def test_str_representation(self):
        self.assertEqual(str(self.pay_order_down), '[계약금] - 계약금')


class SalesPriceByGTModelTests(PaymentTestCaseBase):
    def test_str_representation(self):
        self.assertEqual(
            str(self.sales_price),
            f'1차 일반분양 / 84A / 1-5층 - {300000000:,}원'
        )


class PaymentPerInstallmentModelTests(PaymentTestCaseBase):
    def test_creation_and_str(self):
        ppi = PaymentPerInstallment.objects.create(
            sales_price=self.sales_price,
            pay_order=self.pay_order_down,
            amount=29000000
        )
        self.assertEqual(
            str(ppi),
            f'{self.sales_price.project}-{self.sales_price.order_group}-{self.sales_price.unit_type}-[{self.sales_price.unit_floor_type}]'
        )


class DownPaymentModelTests(PaymentTestCaseBase):
    def test_str_representation(self):
        self.assertEqual(
            str(self.down_payment),
            f'{self.order_group} / {self.unit_type} - {30000000:,}원'
        )


class OverDueRuleModelTests(PaymentTestCaseBase):
    def test_clean_validation(self):
        rule = OverDueRule(
            project=self.project,
            term_start=10,
            term_end=5,
            rate_year=5.0
        )
        with self.assertRaises(ValidationError):
            rule.clean()


class ContractPaymentModelTests(PaymentTestCaseBase):
    def test_automatic_contract_payment_creation(self):
        contract_payments = ContractPayment.objects.all()
        self.assertEqual(contract_payments.count(), 1)
        cp = contract_payments.first()
        self.assertEqual(cp.accounting_entry, self.accounting_entry)
        self.assertEqual(cp.project, self.project)
        self.assertEqual(cp.contract, self.contract)
        self.assertEqual(cp.deal_date, date(2026, 1, 1))
        self.assertFalse(cp.is_payment_mismatch)

    def test_mismatched_project_raises_validation_error(self):
        other_issue_project = IssueProject.objects.create(
            company=self.company,
            name='Other Issue Project',
            slug='other-issue-project',
            creator=self.user
        )
        other_project = Project.objects.create(
            issue_project=other_issue_project,
            name='Other Project',
            order=2,
            kind='1',
            start_year='2026',
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24
        )
        cp = ContractPayment.objects.first()
        cp.project = other_project
        with self.assertRaises(ValidationError):
            cp.clean()


class PaymentAPITests(PaymentTestCaseBase):
    def test_installment_order_list(self):
        url = reverse('api:installmentpaymentorder-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_sales_price_list(self):
        url = reverse('api:salespricebygt-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_payment_summary_list(self):
        url = reverse('api:payment-summary-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payment_status_by_unit_type_list(self):
        url = reverse('api:payment-status-by-unit-type-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_overall_summary_list(self):
        url = reverse('api:overall-summary-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ledger_payment_list(self):
        url = reverse('api:ledger-payment-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ledger_payment_summary_list(self):
        url = reverse('api:ledger-payment-summary-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ledger_payment_status_by_unit_type_list(self):
        url = reverse('api:ledger-payment-status-by-unit-type-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ledger_overall_summary_list(self):
        url = reverse('api:ledger-overall-summary-list')
        response = self.client.get(url, {'project': self.project.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
