from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status as http_status

from datetime import date
from company.models import Company
from contract.models import (OrderGroup, Contract, ContractPrice, Contractor,
                             ContractorAddress, ContractorContact, Succession, ContractorRelease)
from contract.services import ContractPriceUpdateService
from items.models import UnitType, KeyUnit, HouseUnit, BuildingUnit, UnitFloorType
from payment.models import InstallmentPaymentOrder, SalesPriceByGT, DownPayment, ContractPayment
from project.models import Project, ProjectIncBudget
from work.models.project import IssueProject, Member, Role, Permission
from ibs.models import AccountSort
from ledger.models import ProjectAccount, ProjectBankAccount, ProjectBankTransaction, ProjectAccountingEntry, BankCode

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
            trading_date='2026-02-01',
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
            trading_date='2026-02-01',
            status='3'  # 승계 완료
        )

        url = f'/api/v1/succession/{succession.pk}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Succession.objects.filter(pk=succession.pk).exists())

    def test_update_succession_to_canceled_inactivates_buyer(self):
        """승계 취소(status='9')로 변경 시 seller 복구 및 buyer 비활성화(status='4', is_active=False) 검증"""
        buyer = Contractor.objects.create(name='양수인', status='3', is_active=False)
        ContractorAddress.objects.create(contractor=buyer, id_zipcode='12345', id_address1='서울시 강남구', id_address2='101호', id_address3='')
        ContractorContact.objects.create(contractor=buyer, cell_phone='010-1234-5678')

        succession = Succession.objects.create(
            contract=self.contract,
            seller=self.seller,
            buyer=buyer,
            apply_date='2026-02-01',
            trading_date='2026-02-01',
            status='1'
        )

        url = f'/api/v1/succession/{succession.pk}/'
        data = {
            'contract': self.contract.pk,
            'seller': self.seller.pk,
            'buyer': buyer.pk,
            'name': '양수인',
            'gender': 'M',
            'id_zipcode': '12345',
            'id_address1': '서울시 강남구',
            'id_address2': '101호',
            'id_address3': '',
            'cell_phone': '010-1234-5678',
            'apply_date': '2026-02-01',
            'trading_date': '2026-02-01',
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

    def test_update_succession_to_completed_swaps_contractor(self):
        """변경인가대기(status='2') 또는 신청(1)에서 승계완료(status='3')로 변경 시 contract 소유권 정상 이전 및 Unique 제약 충돌 없는지 검증"""
        buyer = Contractor.objects.create(name='양수인', status='3', change_type='3', is_active=False)
        ContractorAddress.objects.create(contractor=buyer, id_zipcode='12345', id_address1='서울시 강남구', id_address2='101호', id_address3='')
        ContractorContact.objects.create(contractor=buyer, cell_phone='010-1234-5678')

        succession = Succession.objects.create(
            contract=self.contract,
            seller=self.seller,
            buyer=buyer,
            apply_date='2026-02-01',
            trading_date='2026-02-01',
            status='2'  # 변경인가대기
        )

        url = f'/api/v1/succession/{succession.pk}/'
        data = {
            'contract': self.contract.pk,
            'seller': self.seller.pk,
            'buyer': buyer.pk,
            'name': '양수인',
            'gender': 'M',
            'id_zipcode': '12345',
            'id_address1': '서울시 강남구',
            'id_address2': '101호',
            'id_address3': '',
            'cell_phone': '010-1234-5678',
            'apply_date': '2026-02-01',
            'trading_date': '2026-02-01',
            'status': '3'  # 승계완료
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        # 1. seller (양도인) 검증: contract 해제, prev_contract 지정, status='4', is_active=False
        self.seller.refresh_from_db()
        self.assertIsNone(self.seller.contract)
        self.assertEqual(self.seller.prev_contract, self.contract)
        self.assertEqual(self.seller.status, '4')
        self.assertFalse(self.seller.is_active)

        # 2. buyer (양수인) 검증: contract 획득, status='2', is_active=True
        buyer.refresh_from_db()
        self.assertEqual(buyer.contract, self.contract)
        self.assertIsNone(buyer.prev_contract)
        self.assertEqual(buyer.status, '2')
        self.assertTrue(buyer.is_active)

        # 3. succession status 검증
        succession.refresh_from_db()
        self.assertEqual(succession.status, '3')

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


class ContractAndPaymentSecurityTests(APITestCase):
    """
    Phase 3: 계약(contract) 및 수납(payment) 도메인 보안 격리(Row-Level Security) 및 무결성 테스트
    - 미인증 요청 차단 (401 Unauthorized)
    - 타 프로젝트 멤버의 계약 및 수납 데이터 접근 차단 (목록 필터링 및 단건 404 / 403 차단)
    - 슈퍼유저 및 work_manager의 전사 프로젝트 데이터 통합 조회
    - 계약(Contract) 직접 삭제 차단 (400 Bad Request)
    - ContractPriceUpdateService 납부 계획(payment_amounts) 계산 및 캐싱 정합성
    """

    def setUp(self):
        # 1. 사용자 계정 생성
        self.admin_user = User.objects.create_superuser(
            username='superadmin', email='super@test.com', password='password123'
        )
        self.work_manager_user = User.objects.create_user(
            username='wm_user', email='wm@test.com', password='password123', work_manager=True
        )
        self.user_a = User.objects.create_user(username='user_a', email='user_a@test.com', password='password123')
        self.user_b = User.objects.create_user(username='user_b', email='user_b@test.com', password='password123')

        # 2. 권한 및 역할 매핑
        perm_contract_read, _ = Permission.objects.get_or_create(
            code='contract.read', defaults={'name': '계약 조회', 'module': 'contract'}
        )
        perm_contract_create, _ = Permission.objects.get_or_create(
            code='contract.create', defaults={'name': '계약 생성', 'module': 'contract'}
        )
        perm_payment_read, _ = Permission.objects.get_or_create(
            code='payment.read', defaults={'name': '수납 조회', 'module': 'payment'}
        )
        perm_payment_create, _ = Permission.objects.get_or_create(
            code='payment.create', defaults={'name': '수납 등록', 'module': 'payment'}
        )

        self.role_staff = Role.objects.create(name='프로젝트 담당자', creator=self.admin_user, issue_visible='ALL')
        self.role_staff.permissions.set([
            perm_contract_read, perm_contract_create, perm_payment_read, perm_payment_create
        ])

        # 3. 프로젝트 A (강남) 및 B (판교) 생성
        self.company = Company.objects.create(name='IBS 건설')

        self.ip_a = IssueProject.objects.create(
            company=self.company, name='강남 프로젝트', slug='gangnam-prj', creator=self.admin_user
        )
        self.project_a = Project.objects.create(
            issue_project=self.ip_a, name='강남 프로젝트', order=1, kind='1',
            start_year='2026', monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01', construction_period_months=24
        )

        self.ip_b = IssueProject.objects.create(
            company=self.company, name='판교 프로젝트', slug='pangyo-prj', creator=self.admin_user
        )
        self.project_b = Project.objects.create(
            issue_project=self.ip_b, name='판교 프로젝트', order=2, kind='1',
            start_year='2026', monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01', construction_period_months=24
        )

        # 4. 멤버십 할당 (user_a는 프로젝트 A만, user_b는 프로젝트 B만 속함)
        m_a = Member.objects.create(user=self.user_a, project=self.ip_a)
        m_a.roles.add(self.role_staff)

        m_b = Member.objects.create(user=self.user_b, project=self.ip_b)
        m_b.roles.add(self.role_staff)

        # 5. 프로젝트 A 계약 및 수납 데이터 생성
        og_a = OrderGroup.objects.create(
            project=self.project_a, order_number=1, sort='2', name='1차 일반분양', is_default_for_uncontracted=True
        )
        ut_a = UnitType.objects.create(
            project=self.project_a, name='84A', sort='1', color='#FF0000', average_price=500000000, num_unit=10
        )
        floor_type_a = UnitFloorType.objects.create(
            project=self.project_a, start_floor=1, end_floor=5, alias_name='1-5층'
        )
        ku_a = KeyUnit.objects.create(project=self.project_a, unit_type=ut_a, unit_code='A-101')
        bu_a = BuildingUnit.objects.create(project=self.project_a, name='101동')
        hu_a = HouseUnit.objects.create(
            unit_type=ut_a, building_unit=bu_a, floor_type=floor_type_a, key_unit=ku_a,
            name='101호', bldg_line=1, floor_no=1
        )
        self.contract_a = Contract.objects.create(
            project=self.project_a, order_group=og_a, unit_type=ut_a, key_unit=ku_a, serial_number='CONT-A-0001'
        )
        self.contractor_a = Contractor.objects.create(
            contract=self.contract_a, name='홍길동', status='2', is_active=True
        )
        self.pay_order_down_a = InstallmentPaymentOrder.objects.create(
            project=self.project_a, type_sort='1', pay_sort='1', pay_code=1, pay_time=1,
            pay_name='계약금', pay_ratio=10.0
        )
        self.pay_order_remain_a = InstallmentPaymentOrder.objects.create(
            project=self.project_a, type_sort='1', pay_sort='3', pay_code=10, pay_time=10,
            pay_name='잔금', pay_ratio=90.0
        )
        self.sales_price_a = SalesPriceByGT.objects.create(
            project=self.project_a, order_group=og_a, unit_type=ut_a, unit_floor_type=floor_type_a,
            price=500000000
        )
        self.cp_a = ContractPrice.objects.create(
            contract=self.contract_a, house_unit=hu_a, price=500000000, is_cache_valid=True,
            payment_amounts={'1': 50000000, '10': 450000000}
        )

        # 6. 프로젝트 B 계약 및 수납 데이터 생성
        og_b = OrderGroup.objects.create(
            project=self.project_b, order_number=1, sort='2', name='1차 일반분양', is_default_for_uncontracted=True
        )
        ut_b = UnitType.objects.create(
            project=self.project_b, name='84B', sort='1', color='#00FF00', average_price=600000000, num_unit=10
        )
        floor_type_b = UnitFloorType.objects.create(
            project=self.project_b, start_floor=1, end_floor=5, alias_name='1-5층'
        )
        ku_b = KeyUnit.objects.create(project=self.project_b, unit_type=ut_b, unit_code='B-101')
        bu_b = BuildingUnit.objects.create(project=self.project_b, name='201동')
        hu_b = HouseUnit.objects.create(
            unit_type=ut_b, building_unit=bu_b, floor_type=floor_type_b, key_unit=ku_b,
            name='101호', bldg_line=1, floor_no=1
        )
        self.contract_b = Contract.objects.create(
            project=self.project_b, order_group=og_b, unit_type=ut_b, key_unit=ku_b, serial_number='CONT-B-0001'
        )
        self.contractor_b = Contractor.objects.create(
            contract=self.contract_b, name='이순신', status='2', is_active=True
        )
        self.cp_b = ContractPrice.objects.create(
            contract=self.contract_b, house_unit=hu_b, price=600000000, is_cache_valid=True,
            payment_amounts={'1': 60000000, '10': 540000000}
        )

        # 7. 회계 및 수납(ContractPayment) 데이터 생성
        bank_code = BankCode.objects.create(code='004', name='국민은행')
        sort_dep = AccountSort.objects.create(name='입금')
        acc_pay = ProjectAccount.objects.create(
            name='분양대금', code='4100', category='revenue', is_payment=True, requires_contract=True
        )

        ba_a = ProjectBankAccount.objects.create(
            project=self.project_a, bankcode=bank_code, alias_name='강남 분양계좌', number='111-111', holder='강남시행'
        )
        tx_a = ProjectBankTransaction.objects.create(
            project=self.project_a, bank_account=ba_a, deal_date=date(2026, 1, 15),
            sort=sort_dep, amount=50000000, content='계약금 입금', creator=self.admin_user
        )
        pae_a = ProjectAccountingEntry.objects.create(
            project=self.project_a, transaction_id=tx_a.transaction_id, account=acc_pay,
            amount=50000000, trader='홍길동', contract=self.contract_a
        )
        self.payment_a = ContractPayment.objects.get(accounting_entry=pae_a)

        ba_b = ProjectBankAccount.objects.create(
            project=self.project_b, bankcode=bank_code, alias_name='판교 분양계좌', number='222-222', holder='판교시행'
        )
        tx_b = ProjectBankTransaction.objects.create(
            project=self.project_b, bank_account=ba_b, deal_date=date(2026, 1, 20),
            sort=sort_dep, amount=60000000, content='계약금 입금', creator=self.admin_user
        )
        pae_b = ProjectAccountingEntry.objects.create(
            project=self.project_b, transaction_id=tx_b.transaction_id, account=acc_pay,
            amount=60000000, trader='이순신', contract=self.contract_b
        )
        self.payment_b = ContractPayment.objects.get(accounting_entry=pae_b)

    def test_unauthenticated_requests_blocked(self):
        """미인증 사용자의 계약 및 수납 API 접근 차단 (401 Unauthorized)"""
        self.client.logout()

        endpoints = [
            '/api/v1/contract/',
            '/api/v1/contract-set/',
            '/api/v1/simple-contract/',
            '/api/v1/ledger/payment/',
            '/api/v1/ledger/all-payment/',
            f'/api/v1/ledger/payment-summary/?project={self.project_a.pk}',
        ]
        for ep in endpoints:
            response = self.client.get(ep)
            self.assertEqual(
                response.status_code, http_status.HTTP_401_UNAUTHORIZED,
                f'Unauthenticated request to {ep} must return 401'
            )

    def test_row_level_security_contract_isolation(self):
        """프로젝트 A 멤버는 프로젝트 A 계약만 조회 가능하며 프로젝트 B 계약은 완벽 격리/은닉됨"""
        self.client.force_authenticate(user=self.user_a)

        # 1. ContractViewSet 목록 및 상세 격리
        res = self.client.get('/api/v1/contract/')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        ids = [item['pk'] for item in res.data['results']]
        self.assertIn(self.contract_a.pk, ids)
        self.assertNotIn(self.contract_b.pk, ids)

        # 본인 프로젝트 계약 상세 조회 성공
        res_a = self.client.get(f'/api/v1/contract/{self.contract_a.pk}/')
        self.assertEqual(res_a.status_code, http_status.HTTP_200_OK)

        # 타 프로젝트 계약 상세 조회 404 차단
        res_b = self.client.get(f'/api/v1/contract/{self.contract_b.pk}/')
        self.assertEqual(res_b.status_code, http_status.HTTP_404_NOT_FOUND)

        # 2. ContractSetViewSet 목록 및 상세 격리
        res_set = self.client.get('/api/v1/contract-set/')
        self.assertEqual(res_set.status_code, http_status.HTTP_200_OK)
        set_ids = [item['pk'] for item in res_set.data['results']]
        self.assertIn(self.contract_a.pk, set_ids)
        self.assertNotIn(self.contract_b.pk, set_ids)

        res_set_a = self.client.get(f'/api/v1/contract-set/{self.contract_a.pk}/')
        self.assertEqual(res_set_a.status_code, http_status.HTTP_200_OK)

        res_set_b = self.client.get(f'/api/v1/contract-set/{self.contract_b.pk}/')
        self.assertEqual(res_set_b.status_code, http_status.HTTP_404_NOT_FOUND)

        # 3. SimpleContractViewSet(simple-contract) 격리
        res_subs = self.client.get('/api/v1/simple-contract/')
        self.assertEqual(res_subs.status_code, http_status.HTTP_200_OK)
        subs_ids = [item['value'] for item in res_subs.data['results']]
        self.assertIn(self.contract_a.pk, subs_ids)
        self.assertNotIn(self.contract_b.pk, subs_ids)

        res_subs_b = self.client.get(f'/api/v1/simple-contract/{self.contract_b.pk}/')
        self.assertEqual(res_subs_b.status_code, http_status.HTTP_404_NOT_FOUND)

    def test_row_level_security_payment_isolation(self):
        """프로젝트 A 멤버는 프로젝트 A 수납 데이터만 조회 가능하며 프로젝트 B 수납 데이터는 완벽 은닉/차단됨"""
        self.client.force_authenticate(user=self.user_a)

        # 1. ContractPaymentViewSet 목록 격리
        res = self.client.get('/api/v1/ledger/payment/')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        ids = [item['pk'] for item in res.data['results']]
        self.assertIn(self.payment_a.pk, ids)
        self.assertNotIn(self.payment_b.pk, ids)

        # 본인 프로젝트 수납건 상세 조회 성공
        res_a = self.client.get(f'/api/v1/ledger/payment/{self.payment_a.pk}/')
        self.assertEqual(res_a.status_code, http_status.HTTP_200_OK)

        # 타 프로젝트 수납건 상세 조회 404 차단
        res_b = self.client.get(f'/api/v1/ledger/payment/{self.payment_b.pk}/')
        self.assertEqual(res_b.status_code, http_status.HTTP_404_NOT_FOUND)

        # 타 프로젝트 project ID 명시 조회 시 403 Forbidden 차단 (IbsModulePermission)
        res_param_b = self.client.get(f'/api/v1/ledger/payment/?project={self.project_b.pk}')
        self.assertEqual(res_param_b.status_code, http_status.HTTP_403_FORBIDDEN)

        # 2. ContractPaymentSummaryViewSet 접근 통제
        # 본인 프로젝트 요약 통계는 200 OK
        res_sum_a = self.client.get(f'/api/v1/ledger/payment-summary/?project={self.project_a.pk}')
        self.assertEqual(res_sum_a.status_code, http_status.HTTP_200_OK)

        # 타 프로젝트 요약 통계 접근 시 403 Forbidden 차단
        res_sum_b = self.client.get(f'/api/v1/ledger/payment-summary/?project={self.project_b.pk}')
        self.assertEqual(res_sum_b.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_superuser_and_work_manager_global_visibility(self):
        """슈퍼유저와 work_manager는 전사 모든 프로젝트의 계약 및 수납 데이터 통합 열람 가능"""
        for test_user in [self.admin_user, self.work_manager_user]:
            self.client.force_authenticate(user=test_user)

            # 1. Contract 통합 조회
            res_c = self.client.get('/api/v1/contract/')
            self.assertEqual(res_c.status_code, http_status.HTTP_200_OK)
            c_ids = [item['pk'] for item in res_c.data['results']]
            self.assertIn(self.contract_a.pk, c_ids)
            self.assertIn(self.contract_b.pk, c_ids)

            # 2. Payment 통합 조회
            res_p = self.client.get('/api/v1/ledger/payment/')
            self.assertEqual(res_p.status_code, http_status.HTTP_200_OK)
            p_ids = [item['pk'] for item in res_p.data['results']]
            self.assertIn(self.payment_a.pk, p_ids)
            self.assertIn(self.payment_b.pk, p_ids)

            # 3. 프로젝트 B 수납 통계 정상 조회
            res_sum_b = self.client.get(f'/api/v1/ledger/payment-summary/?project={self.project_b.pk}')
            self.assertEqual(res_sum_b.status_code, http_status.HTTP_200_OK)

    def test_contract_price_calculation_and_caching(self):
        """ContractPriceUpdateService를 통한 약정 금액 및 payment_amounts 캐싱 무결성 검증"""
        # 서비스 호출하여 계약 가격 업데이트
        cp, created = ContractPriceUpdateService.update_single_contract_price(self.contract_a)

        # DB 최신 상태 반영
        cp.refresh_from_db()
        self.assertTrue(cp.is_cache_valid)
        self.assertEqual(cp.price, 500000000)

        # 계약금 10% (5,000만원), 잔금 90% (4억 5,000만원) 자동 계산 검증
        self.assertIn('1', cp.payment_amounts)
        self.assertEqual(cp.get_payment_amount_by_time(1), 50000000)
        self.assertEqual(cp.get_payment_amount_by_time(10), 450000000)
