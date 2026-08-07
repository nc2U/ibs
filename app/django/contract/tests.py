from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status as http_status

from company.models import Company
from contract.models import (OrderGroup, Contract, ContractPrice, Contractor,
                             ContractorAddress, ContractorContact, Succession, ContractorRelease)
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


class SuccessionAndReleaseAPITests(APITestCase):
    def setUp(self):
        # 1. 슈퍼유저 생성 및 로그인
        self.user = User.objects.create_superuser(username='superadmin', password='password123', email='admin@test.com')
        self.client.force_authenticate(user=self.user)

        # 2. 기본 데이터 구조 생성
        self.company = Company.objects.create(name='Test Company')
        self.issue_project = IssueProject.objects.create(
            company=self.company,
            name='Test Issue Project',
            slug='test-issue-project',
            creator=self.user
        )
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
        self.order_group = OrderGroup.objects.create(
            project=self.project,
            order_number=1,
            sort='2',
            name='1차 일반분양',
            is_default_for_uncontracted=True
        )
        self.unit_type = UnitType.objects.create(
            project=self.project,
            name='84A',
            sort='1',
            color='#FF0000',
            average_price=300000000,
            num_unit=100
        )
        self.key_unit = KeyUnit.objects.create(
            project=self.project,
            unit_type=self.unit_type,
            unit_code='A001'
        )

        # 3. 정식 계약 및 기존 계약자(seller) 생성
        self.contract = Contract.objects.create(
            project=self.project,
            serial_number='CONT-2026-9999',
            order_group=self.order_group,
            unit_type=self.unit_type,
            key_unit=self.key_unit
        )
        self.seller = Contractor.objects.create(
            contract=self.contract,
            name='양도인(기존계약자)',
            status='2',
            contract_date='2026-01-15',
            is_active=True
        )

    def test_destroy_ongoing_succession_restores_seller_and_deletes_buyer(self):
        """승계 진행 중 건 삭제 시 seller 원상복구 및 buyer 개인정보 파기 검증"""
        # 양수인(buyer) 생성
        buyer = Contractor.objects.create(
            contract=None,
            name='양수인(신청자)',
            status='3',
            is_active=False
        )
        buyer_addr = ContractorAddress.objects.create(
            contractor=buyer,
            id_zipcode='12345',
            id_address1='서울시 강남구'
        )
        buyer_contact = ContractorContact.objects.create(
            contractor=buyer,
            cell_phone='010-1234-5678'
        )

        # 승계 신청 레코드 생성 (status='1' 신청접수)
        succession = Succession.objects.create(
            contract=self.contract,
            seller=self.seller,
            buyer=buyer,
            apply_date='2026-02-01',
            status='1'
        )
        self.seller.status = '3'
        self.seller.change_type = '3'
        self.seller.save()

        # DELETE API 호출
        url = f'/api/v1/succession/{succession.pk}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, http_status.HTTP_204_NO_CONTENT)

        # 1. seller 원상복구 검증 (status='2', is_active=True)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.status, '2')
        self.assertIsNone(self.seller.change_type)
        self.assertTrue(self.seller.is_active)

        # 2. buyer 및 주소/연락처 완전 파기 검증
        self.assertFalse(Contractor.objects.filter(pk=buyer.pk).exists())
        self.assertFalse(ContractorAddress.objects.filter(pk=buyer_addr.pk).exists())
        self.assertFalse(ContractorContact.objects.filter(pk=buyer_contact.pk).exists())

        # 3. Succession 레코드 삭제 검증
        self.assertFalse(Succession.objects.filter(pk=succession.pk).exists())

    def test_destroy_completed_succession_fails(self):
        """이미 승계 완료(status='3')된 건은 삭제가 거부(400)되는지 검증"""
        buyer = Contractor.objects.create(name='양수인', status='2', is_active=True)
        succession = Succession.objects.create(
            contract=self.contract,
            seller=self.seller,
            buyer=buyer,
            apply_date='2026-02-01',
            status='3'  # 승계 완료
        )

        url = f'/api/v1/succession/{succession.pk}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Succession.objects.filter(pk=succession.pk).exists())

    def test_update_succession_to_canceled_inactivates_buyer(self):
        """승계 취소(status='9')로 변경 시 seller 복구 및 buyer 비활성화(status='4', is_active=False) 검증"""
        buyer = Contractor.objects.create(name='양수인', status='3', is_active=False)
        succession = Succession.objects.create(
            contract=self.contract,
            seller=self.seller,
            buyer=buyer,
            apply_date='2026-02-01',
            status='1'
        )

        url = f'/api/v1/succession/{succession.pk}/'
        data = {
            'contract': self.contract.pk,
            'seller': self.seller.pk,
            'buyer': buyer.pk,
            'apply_date': '2026-02-01',
            'status': '9'  # 승계취소
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        # seller 원상복구 검증
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.status, '2')

        # buyer 비활성화 검증 (status='4', is_active=False)
        buyer.refresh_from_db()
        self.assertEqual(buyer.status, '4')
        self.assertFalse(buyer.is_active)

    def test_destroy_ongoing_contractor_release_restores_contractor(self):
        """해지 신청건 삭제 시 contractor 상태가 원래 상태로 복구되고 release 레코드만 삭제되는지 검증"""
        self.seller.status = '3'
        self.seller.change_type = '1'
        self.seller.save()

        release = ContractorRelease.objects.create(
            project=self.project,
            contractor=self.seller,
            request_date='2026-02-01',
            status='1'
        )

        url = f'/api/v1/contractor-release/{release.pk}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, http_status.HTTP_204_NO_CONTENT)

        # contractor 원래 상태('2') 원상복구 검증 (contract_date가 있으므로 '2')
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.status, '2')
        self.assertIsNone(self.seller.change_type)
        self.assertTrue(self.seller.is_active)

        # ContractorRelease 레코드만 삭제되고 Contractor는 살아있음
        self.assertFalse(ContractorRelease.objects.filter(pk=release.pk).exists())
        self.assertTrue(Contractor.objects.filter(pk=self.seller.pk).exists())

    def test_destroy_completed_contractor_release_fails(self):
        """해지 확정건(status='4') 삭제 시도 시 400 에러로 거부되는지 검증"""
        release = ContractorRelease.objects.create(
            project=self.project,
            contractor=self.seller,
            request_date='2026-02-01',
            status='4'  # 해지확정
        )

        url = f'/api/v1/contractor-release/{release.pk}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ContractorRelease.objects.filter(pk=release.pk).exists())

    def test_contract_direct_destroy_fails(self):
        """계약(Contract) direct 삭제 시도 시 400 ValidationError로 명시적 차단되는지 검증"""
        url = f'/api/v1/contract/{self.contract.pk}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '계약 정보는 직접 삭제할 수 없습니다. 계약 해지 절차(ContractorRelease)를 이용하십시오.')
        self.assertTrue(Contract.objects.filter(pk=self.contract.pk).exists())
