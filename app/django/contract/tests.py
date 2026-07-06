from django.contrib.auth import get_user_model
from django.test import TestCase

from company.models import Company
from contract.models import OrderGroup, Contract, ContractPrice
from contract.services import ContractPriceUpdateService
from items.models import UnitType, KeyUnit, HouseUnit
from payment.models import InstallmentPaymentOrder
from project.models import Project
from work.models.project import IssueProject

User = get_user_model()


class ContractAppTests(TestCase):
    def setUp(self):
        # 1. 테스트 기본 데이터 생성
        self.user = User.objects.create_user(username='testadmin', password='password123')

        # 1-1. Project 종속성(Company, IssueProject) 생성

        self.company = Company.objects.create(name='Test Company')
        self.issue_project = IssueProject.objects.create(
            company=self.company,
            name='Test Issue Project',
            slug='test-issue-project',
            creator=self.user
        )

        # 1-2. Project 필수 필드 채워 생성
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

        # 2. 차수(OrderGroup) 생성
        self.order_group = OrderGroup.objects.create(
            project=self.project,
            order_number=1,
            sort='2',  # 일반분양
            name='1차 일반분양',
            is_default_for_uncontracted=True
        )

        # 3. 타입(UnitType) 생성
        self.unit_type = UnitType.objects.create(
            project=self.project,
            name='84A',
            sort='1',  # 공동주택
            color='#FF0000',
            average_price=300000000,
            num_unit=100
        )

        # 4. 키유닛, 동(BuildingUnit) 및 하우스유닛 생성
        self.key_unit = KeyUnit.objects.create(
            project=self.project,
            unit_type=self.unit_type,
            unit_code='A001'
        )
        from items.models import BuildingUnit
        self.building_unit = BuildingUnit.objects.create(
            project=self.project,
            name='101동'
        )
        self.house_unit = HouseUnit.objects.create(
            unit_type=self.unit_type,
            building_unit=self.building_unit,
            floor_type=None,
            key_unit=self.key_unit,
            name='101호',
            bldg_line=1,
            floor_no=1
        )

        # 5. 분할 납부 일정 생성 (계약금 10%, 중도금 60%, 잔금 30%)
        # 계약금 (pay_sort='1')
        self.pay_order_down = InstallmentPaymentOrder.objects.create(
            project=self.project,
            type_sort='1',
            pay_sort='1',
            pay_code=1,
            pay_time=1,
            pay_name='계약금',
            pay_ratio=10.0
        )
        # 잔금 (pay_sort='3')
        self.pay_order_remain = InstallmentPaymentOrder.objects.create(
            project=self.project,
            type_sort='1',
            pay_sort='3',
            pay_code=10,
            pay_time=10,
            pay_name='잔금',
            pay_ratio=90.0
        )

    def test_contract_creation_and_price_cache(self):
        """계약 등록 시 가격 정보 생성 및 분양가 캐시 로직 검증"""
        # 1. 계약 생성
        contract = Contract.objects.create(
            project=self.project,
            serial_number='CONT-2026-0001',
            order_group=self.order_group,
            unit_type=self.unit_type,
            key_unit=self.key_unit
        )

        # 2. 계약 가격 생성 (3억원)
        contract_price = ContractPrice.objects.create(
            contract=contract,
            house_unit=self.house_unit,
            price=300000000,
            price_build=200000000,
            price_land=80000000,
            price_tax=20000000
        )

        # 3. DB에 올바르게 저장되었고 캐시 유효성(is_cache_valid)이 설정되었는지 확인
        self.assertTrue(contract_price.is_cache_valid)

        # 4. JSON 필드(payment_amounts)에 회차별 금액(계약금 10% = 3천만원, 잔금 90% = 2억 7천만원)이 저장되었는지 확인
        # JSON 키는 문자열 타입 ("1", "10")
        self.assertEqual(contract_price.payment_amounts.get('1'), 30000000)
        self.assertEqual(contract_price.payment_amounts.get('10'), 270000000)

        # 5. Helper 메소드 작동 검증
        self.assertEqual(contract_price.get_payment_amount_by_time(1), 30000000)
        self.assertEqual(contract_price.get_payment_amount_by_sort('1'), 30000000)
        self.assertEqual(contract_price.get_payment_amount_by_sort('3'), 270000000)

    def test_contract_price_uncontracted(self):
        """미계약 세대 등록 시 임시 납부 계약 계산 캐시 검증"""
        # 계약이 연결되지 않고 house_unit만 존재하는 ContractPrice 생성
        contract_price = ContractPrice.objects.create(
            contract=None,
            house_unit=self.house_unit,
            price=250000000
        )

        # 미계약 세대 캐시 확인
        self.assertTrue(contract_price.is_cache_valid)
        self.assertEqual(contract_price.payment_amounts.get('1'), 30000000)  # average_price(3억) 기준 10% = 3천만원
        self.assertEqual(contract_price.payment_amounts.get('10'), 270000000)  # average_price(3억) 기준 90% = 2억 7천만원

    def test_contract_price_update_service(self):
        """서비스 레이어를 통한 단일 계약 가격 자동 동기화 검증"""
        # 계약 생성
        contract = Contract.objects.create(
            project=self.project,
            serial_number='CONT-2026-0002',
            order_group=self.order_group,
            unit_type=self.unit_type,
            key_unit=self.key_unit
        )

        # 서비스 레이어 실행
        contract_price, created = ContractPriceUpdateService.update_single_contract_price(contract)

        self.assertTrue(created)
        # UnitType의 average_price(3억) 기준으로 임시 생성 검증
        self.assertEqual(contract_price.price, 300000000)
        self.assertTrue(contract_price.is_cache_valid)
