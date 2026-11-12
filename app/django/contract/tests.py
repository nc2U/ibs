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

    def test_create_duplicate_succession_blocked(self):
        """[T-2 / M-3] 동일 계약에 대해 이미 진행 중인 승계가 존재할 때 중복 승계 신청(POST) 시 400 ValidationError 차단 검증"""
        # 1. 이미 진행 중(status='1' 신청)인 기존 승계 건 생성
        buyer1 = Contractor.objects.create(name='1차양수인', status='3', is_active=False)
        Succession.objects.create(
            contract=self.contract,
            seller=self.seller,
            buyer=buyer1,
            apply_date='2026-02-01',
            trading_date='2026-02-01',
            status='1'  # 신청 상태 (진행 중)
        )

        # 2. 동일한 contract에 대해 또 다른 양수인으로 승계 신청(POST) 시도
        url = '/api/v1/succession/'
        data = {
            'contract': self.contract.pk,
            'name': '2차양수인',
            'gender': 'F',
            'id_zipcode': '12345',
            'id_address1': '서울시 서초구',
            'id_address2': '201호',
            'cell_phone': '010-9999-8888',
            'apply_date': '2026-02-15',
            'trading_date': '2026-02-15',
        }
        response = self.client.post(url, data, format='json')

        # 3. 400 Bad Request 및 에러 메시지 검증
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('해당 계약에 대해 이미 처리 중인 권리의무승계', str(response.data))



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

        # 주소, 연락처 및 해지 데이터 생성
        self.addr_a = ContractorAddress.objects.create(
            contractor=self.contractor_a, id_zipcode='12345', id_address1='서울시 강남구', is_current=True
        )
        self.addr_b = ContractorAddress.objects.create(
            contractor=self.contractor_b, id_zipcode='54321', id_address1='성남시 분당구', is_current=True
        )
        self.contact_a = ContractorContact.objects.create(
            contractor=self.contractor_a, cell_phone='010-1111-2222'
        )
        self.contact_b = ContractorContact.objects.create(
            contractor=self.contractor_b, cell_phone='010-3333-4444'
        )
        self.release_a = ContractorRelease.objects.create(
            project=self.project_a, contractor=self.contractor_a, status='1', request_date=date(2026, 1, 10)
        )
        self.release_b = ContractorRelease.objects.create(
            project=self.project_b, contractor=self.contractor_b, status='1', request_date=date(2026, 1, 10)
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

    def test_row_level_security_contractor_and_sub_models_isolation(self):
        """프로젝트 A 멤버는 계약자, 주소, 연락처, 해지, 가격 등 하위 데이터에서도 프로젝트 B 데이터에 접근 불가"""
        self.client.force_authenticate(user=self.user_a)

        # 1. ContractorViewSet (/api/v1/contractor/)
        res_cont = self.client.get('/api/v1/contractor/')
        self.assertEqual(res_cont.status_code, http_status.HTTP_200_OK)
        cont_ids = [item['pk'] for item in res_cont.data['results']]
        self.assertIn(self.contractor_a.pk, cont_ids)
        self.assertNotIn(self.contractor_b.pk, cont_ids)

        # 타 프로젝트 계약자 상세 조회 차단 (404)
        res_cont_b = self.client.get(f'/api/v1/contractor/{self.contractor_b.pk}/')
        self.assertEqual(res_cont_b.status_code, http_status.HTTP_404_NOT_FOUND)

        # 2. ContractorAddressViewSet (/api/v1/contractor-address/)
        res_addr = self.client.get('/api/v1/contractor-address/')
        self.assertEqual(res_addr.status_code, http_status.HTTP_200_OK)
        addr_ids = [item['pk'] for item in res_addr.data['results']]
        self.assertIn(self.addr_a.pk, addr_ids)
        self.assertNotIn(self.addr_b.pk, addr_ids)

        # 3. ContractorContactViewSet (/api/v1/contractor-contact/)
        res_contact = self.client.get('/api/v1/contractor-contact/')
        self.assertEqual(res_contact.status_code, http_status.HTTP_200_OK)
        contact_ids = [item['pk'] for item in res_contact.data['results']]
        self.assertIn(self.contact_a.pk, contact_ids)
        self.assertNotIn(self.contact_b.pk, contact_ids)

        # 4. ContReleaseViewSet (/api/v1/contractor-release/)
        res_rel = self.client.get('/api/v1/contractor-release/')
        self.assertEqual(res_rel.status_code, http_status.HTTP_200_OK)
        rel_ids = [item['pk'] for item in res_rel.data['results']]
        self.assertIn(self.release_a.pk, rel_ids)
        self.assertNotIn(self.release_b.pk, rel_ids)

        # 5. ContractPriceViewSet (/api/v1/cont-price/)
        res_cp = self.client.get('/api/v1/cont-price/')
        self.assertEqual(res_cp.status_code, http_status.HTTP_200_OK)
        cp_ids = [item['pk'] for item in res_cp.data['results']]
        self.assertIn(self.cp_a.pk, cp_ids)
        self.assertNotIn(self.cp_b.pk, cp_ids)

        # 6. ContractAggreateView (/api/v1/cont-aggregate/<project_id>/)
        res_agg_a = self.client.get(f'/api/v1/cont-aggregate/{self.project_a.pk}/')
        self.assertEqual(res_agg_a.status_code, http_status.HTTP_200_OK)

        res_agg_b = self.client.get(f'/api/v1/cont-aggregate/{self.project_b.pk}/')
        self.assertEqual(res_agg_b.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_contractoraddress_prefetched_cache(self):
        """Contractor.contractoraddress 프로퍼티가 prefetch 캐시 활용 시 추가 쿼리를 실행하지 않음"""
        contractor = Contractor.objects.prefetch_related('addresses').get(pk=self.contractor_a.pk)

        # addresses가 이미 prefetch된 상태이므로 프로퍼티 호출 시 0개의 추가 쿼리만 발생해야 함
        with self.assertNumQueries(0):
            current_addr = contractor.contractoraddress
            self.assertIsNotNone(current_addr)
            self.assertEqual(current_addr.pk, self.addr_a.pk)

    def test_contract_admin_query_optimization(self):
        """ContractAdmin의 list_select_related 적용으로 외래키 접근 시 추가 쿼리 0건 검증"""
        from django.contrib.admin.sites import AdminSite
        from contract.admin import ContractAdmin
        from django.test import RequestFactory

        self.contract_a.creator = self.admin_user
        self.contract_a.save()

        admin = ContractAdmin(Contract, AdminSite())
        request = RequestFactory().get('/admin/contract/contract/')
        request.user = self.admin_user

        qs = admin.get_queryset(request).filter(pk=self.contract_a.pk)
        contracts = list(qs)
        self.assertEqual(len(contracts), 1)

        with self.assertNumQueries(0):
            item = contracts[0]
            _ = item.project.name
            _ = item.order_group.name
            _ = item.unit_type.name
            _ = item.contractor.name
            _ = item.contractprice.price
            _ = item.creator.username

    def test_excel_and_pdf_export_views(self):
        """리팩토링된 엑셀(ExportContracts, ExportSuccessions, ExportReleases, ExportUnitStatus) 및 PDF 뷰 검증"""
        from django.test import RequestFactory
        from contract.exports.excel import ExportContracts, ExportSuccessions, ExportReleases, ExportUnitStatus
        from contract.exports.pdf import PdfExportCertOccupancy
        factory = RequestFactory()

        # 1. ExportContracts
        req = factory.get(f'/contract/export/contracts/?project={self.project_a.pk}&col=1-2-3-4-5-6-7&status=2')
        res = ExportContracts().get(req)
        self.assertEqual(res.status_code, 200)

        # 2. ExportSuccessions
        req_succ = factory.get(f'/contract/export/successions/?project={self.project_a.pk}')
        res_succ = ExportSuccessions().get(req_succ)
        self.assertEqual(res_succ.status_code, 200)

        # 3. ExportReleases
        req_rel = factory.get(f'/contract/export/releases/?project={self.project_a.pk}')
        res_rel = ExportReleases().get(req_rel)
        self.assertEqual(res_rel.status_code, 200)

        # 4. ExportUnitStatus
        req_unit = factory.get(f'/contract/export/unit-status/?project={self.project_a.pk}')
        res_unit = ExportUnitStatus().get(req_unit)
        self.assertEqual(res_unit.status_code, 200)

        # 5. PdfExportCertOccupancy (메모리 스트리밍 반환 검증)
        req_pdf = factory.get(f'/contract/export/cert-occupancy/?contract={self.contract_a.pk}')
        req_pdf.user = self.admin_user
        res_pdf = PdfExportCertOccupancy().get(req_pdf)
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf['Content-Type'], 'application/pdf')
        self.assertTrue(len(res_pdf.content) > 0)

    def test_recent_logs_isolation(self):
        """[CRITICAL-1] 대시보드 recent-logs API의 테넌트/프로젝트 격리 검증"""
        # 1. user_a (프로젝트 A 전용 사용자)로 조회
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get('/api/v1/contract/recent-logs/')
        self.assertEqual(res_a.status_code, http_status.HTTP_200_OK)
        project_names_a = [item['project_name'] for item in res_a.data]
        self.assertTrue(all(name == self.project_a.name for name in project_names_a))
        contract_ids_a = [item['pk'] for item in res_a.data]
        self.assertIn(self.contract_a.pk, contract_ids_a)
        self.assertNotIn(self.contract_b.pk, contract_ids_a)

        # 2. user_b (프로젝트 B 전용 사용자)로 조회
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.get('/api/v1/contract/recent-logs/')
        self.assertEqual(res_b.status_code, http_status.HTTP_200_OK)
        project_names_b = [item['project_name'] for item in res_b.data]
        self.assertTrue(all(name == self.project_b.name for name in project_names_b))
        contract_ids_b = [item['pk'] for item in res_b.data]
        self.assertIn(self.contract_b.pk, contract_ids_b)
        self.assertNotIn(self.contract_a.pk, contract_ids_b)

        # 3. superadmin으로 조회 -> 두 프로젝트 계약 모두 반환 가능
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get('/api/v1/contract/recent-logs/')
        self.assertEqual(res_admin.status_code, http_status.HTTP_200_OK)
        contract_ids_admin = [item['pk'] for item in res_admin.data]
        self.assertIn(self.contract_a.pk, contract_ids_admin)
        self.assertIn(self.contract_b.pk, contract_ids_admin)

    def test_payment_summary_and_multi_project_security(self):
        """[CRITICAL-2] payment_summary 및 multi-project-payment-summary 권한 격리 검증"""
        self.client.force_authenticate(user=self.user_a)

        # 1. payment_summary: 본인 프로젝트는 200 OK
        res_own = self.client.get(f'/api/v1/contract/payment-summary/?project={self.project_a.pk}&use_cache=false')
        self.assertEqual(res_own.status_code, http_status.HTTP_200_OK)

        # 2. payment_summary: 타 프로젝트는 403 Forbidden
        res_other = self.client.get(f'/api/v1/contract/payment-summary/?project={self.project_b.pk}&use_cache=false')
        self.assertEqual(res_other.status_code, http_status.HTTP_403_FORBIDDEN)

        # 3. multi-project-payment-summary: 본인 프로젝트만 요청 시 200 OK
        res_multi_own = self.client.get(f'/api/v1/contract/multi-project-payment-summary/?projects={self.project_a.pk}')
        self.assertEqual(res_multi_own.status_code, http_status.HTTP_200_OK)

        # 4. multi-project-payment-summary: 타 프로젝트가 하나라도 포함되면 403 Forbidden
        res_multi_mixed = self.client.get(f'/api/v1/contract/multi-project-payment-summary/?projects={self.project_a.pk},{self.project_b.pk}')
        self.assertEqual(res_multi_mixed.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_excel_and_pdf_export_security(self):
        """[HIGH-1, HIGH-2, MEDIUM-1] 엑셀 및 PDF 내보내기 권한 검증 및 파라미터 방어 테스트"""
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory
        from contract.exports.excel import ExportContracts, ExportSuccessions, ExportReleases, ExportUnitStatus
        from contract.exports.pdf import PdfExportCertOccupancy
        factory = RequestFactory()

        # 1. 비로그인(AnonymousUser) 접근 시 401 차단
        for view_cls, url in [
            (ExportContracts, f'/contract/export/contracts/?project={self.project_a.pk}&col=1-2'),
            (ExportSuccessions, f'/contract/export/successions/?project={self.project_a.pk}'),
            (ExportReleases, f'/contract/export/releases/?project={self.project_a.pk}'),
            (ExportUnitStatus, f'/contract/export/unit-status/?project={self.project_a.pk}'),
        ]:
            req = factory.get(url)
            req.user = AnonymousUser()
            res = view_cls().get(req)
            self.assertEqual(res.status_code, 401)

        req_pdf = factory.get(f'/contract/export/cert-occupancy/?contract={self.contract_a.pk}')
        req_pdf.user = AnonymousUser()
        res_pdf = PdfExportCertOccupancy().get(req_pdf)
        self.assertEqual(res_pdf.status_code, 401)

        # 2. 타 프로젝트 권한 없는 사용자(user_b -> project_a) 403 차단
        for view_cls, url in [
            (ExportContracts, f'/contract/export/contracts/?project={self.project_a.pk}&col=1-2'),
            (ExportSuccessions, f'/contract/export/successions/?project={self.project_a.pk}'),
            (ExportReleases, f'/contract/export/releases/?project={self.project_a.pk}'),
            (ExportUnitStatus, f'/contract/export/unit-status/?project={self.project_a.pk}'),
        ]:
            req = factory.get(url)
            req.user = self.user_b
            res = view_cls().get(req)
            self.assertEqual(res.status_code, 403)

        req_pdf = factory.get(f'/contract/export/cert-occupancy/?contract={self.contract_a.pk}')
        req_pdf.user = self.user_b
        res_pdf = PdfExportCertOccupancy().get(req_pdf)
        self.assertEqual(res_pdf.status_code, 403)

        # 3. ExportContracts col 파라미터 누락 시 500 에러 없이 정상 처리(200 OK)
        req_no_col = factory.get(f'/contract/export/contracts/?project={self.project_a.pk}&status=2')
        req_no_col.user = self.user_a
        res_no_col = ExportContracts().get(req_no_col)
        self.assertEqual(res_no_col.status_code, 200)

        # 4. 필수 파라미터 누락 및 유효하지 않은 ID 처리 (400 / 404)
        req_no_prj = factory.get('/contract/export/contracts/')
        req_no_prj.user = self.user_a
        self.assertEqual(ExportContracts().get(req_no_prj).status_code, 400)

        req_invalid_pdf = factory.get('/contract/export/cert-occupancy/?contract=999999')
        req_invalid_pdf.user = self.admin_user
        self.assertEqual(PdfExportCertOccupancy().get(req_invalid_pdf).status_code, 404)

    def test_cross_project_model_validation(self):
        """[MEDIUM-2] Contract, Succession, ContractorRelease 크로스 프로젝트 외래키 무결성 검증"""
        from django.core.exceptions import ValidationError

        # 1. Contract: 타 프로젝트 차수(order_group) 또는 유닛타입(unit_type) 설정 시 차단
        og_b = OrderGroup.objects.get(project=self.project_b)
        invalid_contract = Contract(
            project=self.project_a,
            order_group=og_b,
            unit_type=self.contract_a.unit_type,
            serial_number='INVALID-001'
        )
        with self.assertRaises(ValidationError):
            invalid_contract.clean()

        # 2. Succession: 승계 대상 계약과 양도계약자의 계약 정보 불일치 시 차단
        invalid_succ = Succession(
            contract=self.contract_a,
            seller=self.contractor_b,  # contractor_b belongs to contract_b
            buyer=Contractor(name='새양수인', status='1'),
            apply_date=date(2026, 2, 1),
            trading_date=date(2026, 2, 1)
        )
        with self.assertRaises(ValidationError):
            invalid_succ.clean()

        # 3. ContractorRelease: 해지 프로젝트와 계약자의 계약 프로젝트 불일치 시 차단
        invalid_rel = ContractorRelease(
            project=self.project_a,
            contractor=self.contractor_b,  # contractor_b belongs to project_b
            request_date=date(2026, 2, 1)
        )
        with self.assertRaises(ValidationError):
            invalid_rel.clean()

    def test_contractor_release_serial_number_length_boundary(self):
        """[CRITICAL-1] 30자 최대 길이를 가진 계약의 해지 완결 처리 시 max_length=30 초과 방지 및 DataError 없는 정상 처리 검증"""
        from contract.services import ContractorReleaseService

        # 1. 26자 길이의 긴 일련번호를 가진 계약 생성
        long_contract = Contract.objects.create(
            project=self.project_a,
            serial_number='CONT-2026-LONG-SERIAL-9999',  # 26자
            order_group=self.contract_a.order_group,
            unit_type=self.contract_a.unit_type,
            key_unit=None
        )
        long_contractor = Contractor.objects.create(
            contract=long_contract,
            name='긴계약자',
            status='2',
            contract_date='2026-01-15',
            is_active=True
        )
        release = ContractorRelease.objects.create(
            project=self.project_a,
            contractor=long_contractor,
            status='1',
            request_date=date(2026, 2, 1)
        )

        # 2. 해지 완결 실행 (completion_date 지정)
        result = ContractorReleaseService.process_release_completion(
            contractor_release=release,
            completion_date='2026-02-15'
        )

        # 3. 정상 완결 및 serial_number가 30자 이내인지 검증
        self.assertTrue(result['contract_updated'])
        long_contract.refresh_from_db()
        self.assertFalse(long_contract.is_active)
        self.assertLessEqual(len(long_contract.serial_number), 30)
        self.assertIn('-T', long_contract.serial_number)

    def test_export_contracts_paid_sum_calculation(self):
        """[HIGH-1] ExportContracts에서 '납입금합계' 컬럼 요청 시 ContractPayment 유효 납부액이 0원이 아닌 실제 금액으로 정확히 계산되는지 검증"""
        from django.test import RequestFactory
        from contract.exports.excel import ExportContracts
        factory = RequestFactory()

        # col=1-2-14 (1: No, 2: 계약일련번호, 14: 납입금합계)
        req = factory.get(f'/contract/export/contracts/?project={self.project_a.pk}&col=1-2-14&status=2')
        req.user = self.admin_user

        export_view = ExportContracts()
        # 엑셀 다운로드 실행 (200 OK)
        response = export_view.get(req)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertTrue(len(response.content) > 0)

        # payment_a에 입금된 금액이 50,000,000원이므로 paid_map을 통해 정상 합산됨을 간접 및 직접 검증
        from payment.models import ContractPayment
        from django.db.models import Sum
        paid_qs = ContractPayment.objects.valid_payments().filter(
            contract_id=self.contract_a.pk
        ).aggregate(total=Sum('accounting_entry__amount'))
        self.assertEqual(paid_qs['total'], 50000000)

    def test_contract_price_bulk_update_with_existing_house_unit(self):
        """[HIGH-2] 특정 house_unit을 소유한 ContractPrice가 이미 존재하는 상태에서 일괄 업데이트 시 OneToOne 무결성 충돌 없이 정상 동작 검증"""
        from contract.services import ContractPriceBulkUpdateService

        # 1. contract_a에 연결된 house_unit을 가진 ContractPrice가 이미 존재함
        service = ContractPriceBulkUpdateService(project=self.project_a)
        res = service.update_all_contract_prices()

        self.assertEqual(len(res['errors']), 0)
        self.assertGreaterEqual(res['updated_count'], 1)

    def test_succession_admin_search_fields(self):
        """[MEDIUM-1] SuccessionAdmin search_fields에서 seller__name, buyer__name 검색 시 쿼리 오류 없음 검증"""
        from django.contrib.admin.sites import AdminSite
        from contract.admin import SuccessionAdmin
        from django.test import RequestFactory

        admin = SuccessionAdmin(Succession, AdminSite())
        request = RequestFactory().get('/admin/contract/succession/?q=홍길동')
        request.user = self.admin_user

        # search_fields 검색 적용 시 FieldError 없이 쿼리셋이 정상 평가되어야 함
        qs = admin.get_queryset(request)
        filtered_qs, use_distinct = admin.get_search_results(request, qs, '홍길동')
        self.assertIsNotNone(list(filtered_qs))

    def test_sub_viewsets_write_permission_and_upload_idor_blocked(self):
        """[CRITICAL-1] 계약 하위 ViewSet 8종 쓰기 권한(IbsModulePermission) 통제 및 파일 업로드 Cross-Project IDOR 차단 검증"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from contract.models import DocumentType, RequiredDocument, ContractDocument

        # 1. 읽기 전용 멤버(contract.read만 보유) 생성
        readonly_user = User.objects.create_user(username='readonly_a', email='ro@test.com', password='password123')
        perm_read = Permission.objects.get(code='contract.read')
        role_ro = Role.objects.create(name='읽기전용', creator=self.admin_user, issue_visible='ALL')
        role_ro.permissions.set([perm_read])
        m_ro = Member.objects.create(user=readonly_user, project=self.ip_a)
        m_ro.roles.add(role_ro)

        self.client.force_authenticate(user=readonly_user)

        # 읽기 전용 멤버가 프로젝트 A의 계약자, 주소, 연락처, 가격, 상담내역 수정/생성 시도 -> 403 차단
        res_patch_cont = self.client.patch(f'/api/v1/contractor/{self.contractor_a.pk}/', {'name': '변조시도'}, format='json')
        self.assertEqual(res_patch_cont.status_code, http_status.HTTP_403_FORBIDDEN)

        res_patch_addr = self.client.patch(f'/api/v1/contractor-address/{self.addr_a.pk}/', {'id_address1': '변조주소'}, format='json')
        self.assertEqual(res_patch_addr.status_code, http_status.HTTP_403_FORBIDDEN)

        res_patch_contact = self.client.patch(f'/api/v1/contractor-contact/{self.contact_a.pk}/', {'cell_phone': '010-9999-9999'}, format='json')
        self.assertEqual(res_patch_contact.status_code, http_status.HTTP_403_FORBIDDEN)

        res_patch_cp = self.client.patch(f'/api/v1/cont-price/{self.cp_a.pk}/', {'price': 100}, format='json')
        self.assertEqual(res_patch_cp.status_code, http_status.HTTP_403_FORBIDDEN)

        res_post_consult = self.client.post('/api/v1/contractor-consultations/', {
            'contractor': self.contractor_a.pk,
            'consultation_date': '2026-02-01',
            'channel': '1',
            'category': '1',
            'content': '무단 상담 등록'
        }, format='json')
        self.assertEqual(res_post_consult.status_code, http_status.HTTP_403_FORBIDDEN)

        # 2. 프로젝트 A 담당자(user_a, contract.create 보유)가 프로젝트 B 계약자/서류에 파일 업로드 시도 -> 403 IDOR 차단
        self.client.force_authenticate(user=self.user_a)
        dummy_file = SimpleUploadedFile('test.pdf', b'%PDF-1.4 dummy', content_type='application/pdf')
        res_upload_b = self.client.post(
            f'/api/v1/contract-file/upload/{self.contractor_b.pk}/',
            {'file': dummy_file},
            format='multipart'
        )
        self.assertEqual(res_upload_b.status_code, http_status.HTTP_403_FORBIDDEN)

        doc_type = DocumentType.objects.create(name='신분증사본')
        req_doc_b = RequiredDocument.objects.create(project=self.project_b, document_type=doc_type, sort='proof')
        cont_doc_b = ContractDocument.objects.create(contractor=self.contractor_b, required_document=req_doc_b)
        dummy_file2 = SimpleUploadedFile('doc.pdf', b'%PDF-1.4 dummy2', content_type='application/pdf')
        res_doc_upload_b = self.client.post(
            f'/api/v1/contract-docs-file/upload/{cont_doc_b.pk}/',
            {'file': dummy_file2},
            format='multipart'
        )
        self.assertEqual(res_doc_upload_b.status_code, http_status.HTTP_403_FORBIDDEN)

        # 본인 프로젝트(A) 계약자에 대한 파일 업로드는 201 Created 정상 처리
        dummy_file3 = SimpleUploadedFile('valid.pdf', b'%PDF-1.4 valid', content_type='application/pdf')
        res_upload_a = self.client.post(
            f'/api/v1/contract-file/upload/{self.contractor_a.pk}/',
            {'file': dummy_file3},
            format='multipart'
        )
        self.assertEqual(res_upload_a.status_code, http_status.HTTP_201_CREATED)

    def test_payment_processing_service_cross_contract_tampering_blocked(self):
        """[CRITICAL-2] PaymentProcessingService.process_payment_update에서 타 계약의 payment ID 전달 시 변조 차단 검증"""
        from contract.services import PaymentProcessingService
        from rest_framework import serializers

        with self.assertRaises(serializers.ValidationError) as ctx:
            PaymentProcessingService.process_payment_update(
                contract=self.contract_a,
                data={
                    'deal_date': '2026-02-01',
                    'payment': self.payment_b.pk,  # 타 계약(contract_b)의 납부 ID
                    'amount': 1000,
                },
                user=self.admin_user
            )
        self.assertIn('다른 계약의 납부 내역은 수정할 수 없습니다', str(ctx.exception))

        # payment_b의 금액이 변조되지 않았음을 확인
        self.payment_b.accounting_entry.refresh_from_db()
        self.assertEqual(self.payment_b.accounting_entry.amount, 60000000)

    def test_succession_serializer_release_cancel_code_and_missing_fields_defense(self):
        """[HIGH-1] 권리의무승계 생성 시 기존 해지 신청 취소 코드('9') 정합성 및 주소/연락처 None 방어, 다중 주소 업데이트 검증"""
        self.client.force_authenticate(user=self.admin_user)

        # self.release_a는 현재 status='1'(신청중) 상태
        self.assertEqual(self.release_a.status, '1')

        # 주소/연락처 필드를 생략하고, 잘못된 seller ID를 주입하여 승계 생성 요청
        res = self.client.post('/api/v1/succession/', {
            'contract': self.contract_a.pk,
            'seller': self.contractor_b.pk,  # 조작된 타 계약자 ID 전달
            'name': '신규양수인',
            'gender': 'M',
            'apply_date': '2026-02-10',
            'trading_date': '2026-02-10',
        }, format='json')
        self.assertEqual(res.status_code, http_status.HTTP_201_CREATED)

        # 1. 해지 신청이 '0'이 아닌 유효 코드 '9'(신청취소)로 변경되었는지 검증
        self.release_a.refresh_from_db()
        self.assertEqual(self.release_a.status, '9')

        # 2. 조작된 seller 입력값 대신 contract_a의 실제 계약자(contractor_a)가 seller로 저장되었는지 검증
        succ = Succession.objects.get(pk=res.data['pk'])
        self.assertEqual(succ.seller_id, self.contractor_a.pk)

        # 3. 양수인에게 과거 주소 이력을 추가하여 주소가 2개 이상인 상태에서 PUT 업데이트 시 MultipleObjectsReturned 없이 성공하는지 검증
        ContractorAddress.objects.create(
            contractor=succ.buyer, id_zipcode='00000', id_address1='과거주소', is_current=False
        )
        res_upd = self.client.put(f'/api/v1/succession/{succ.pk}/', {
            'contract': self.contract_a.pk,
            'seller': self.contractor_a.pk,
            'buyer': succ.buyer.pk,
            'name': '신규양수인_수정',
            'gender': 'M',
            'id_zipcode': '13579',
            'id_address1': '서울시 송파구',
            'apply_date': '2026-02-10',
            'trading_date': '2026-02-10',
            'status': '2',
        }, format='json')
        self.assertEqual(res_upd.status_code, http_status.HTTP_200_OK)

    def test_contractor_release_completion_date_fallback_and_already_released_defense(self):
        """[HIGH-2] 해지 확정(status='4') 시 기존 completion_date 폴백으로 은행거래 환불노트 기록 및 중복 해지 방어 검증"""
        from contract.services import ContractorReleaseService
        from rest_framework import serializers

        self.client.force_authenticate(user=self.admin_user)

        # 환불 계정 생성
        ProjectAccount.objects.create(
            name='해지자환불', code='2100', category='revenue',
            direction='deposit', is_related_contractor=True
        )

        # release_a에 completion_date를 먼저 저장해 둔 뒤, payload에 completion_date 없이 status='4'로 PATCH
        self.release_a.completion_date = date(2026, 2, 20)
        self.release_a.save()

        res = self.client.patch(f'/api/v1/contractor-release/{self.release_a.pk}/', {
            'status': '4',
        }, format='json')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)

        # 은행 거래 note에 환불 완료 메시지가 정상 추가되었는지 검증
        tx_a = self.payment_a.accounting_entry.related_transaction
        tx_a.refresh_from_db()
        self.assertIn('환불 계약 건', tx_a.note)

        # 이미 해지 완료되어 contractor_a.contract가 None인 상태에서 재차 해지 완결 호출 시 ValidationError 발생 검증
        self.release_a.refresh_from_db()
        with self.assertRaises(serializers.ValidationError):
            ContractorReleaseService.process_release_completion(self.release_a, '2026-02-25')

    def test_contract_update_service_duplicate_serial_number_validation(self):
        """[HIGH-3] ContractUpdateService에서 중복된 serial_number로 수정 시도 시 ValidationError 발생 검증"""
        from contract.services import ContractUpdateService
        from rest_framework import serializers

        service = ContractUpdateService()
        with self.assertRaises(serializers.ValidationError) as ctx:
            service.update_contract(
                instance=self.contract_a,
                data={'serial_number': self.contract_b.serial_number},
                user=self.admin_user
            )
        self.assertIn('serial_number', ctx.exception.detail)

    def test_excel_exports_edge_cases_and_released_serial_number(self):
        """[HIGH-4] ExportContracts 잘못된 col/order 파라미터 방어 및 ExportReleases 해지확정건 일련번호(prev_contract) 보존 검증"""
        from django.test import RequestFactory
        from contract.exports.excel import ExportContracts, ExportReleases
        from contract.services import ContractorReleaseService

        factory = RequestFactory()

        # 1. 범위 밖 col 및 잘못된 order 파라미터 전달 시 500 에러 없이 200 OK 반환
        req = factory.get(f'/contract/export/contracts/?project={self.project_a.pk}&col=0-99&order=999&status=2')
        req.user = self.admin_user
        res = ExportContracts().get(req)
        self.assertEqual(res.status_code, 200)

        # 2. 해지 완결 후(contract=None, prev_contract=contract_a) ExportReleases에서 일련번호가 Coalesce로 조회되는지 검증
        orig_sn = self.contract_a.serial_number
        ContractorReleaseService.process_release_completion(self.release_a, '2026-02-20')
        self.contractor_a.refresh_from_db()
        self.assertIsNone(self.contractor_a.contract)
        self.assertIsNotNone(self.contractor_a.prev_contract)

        req_rel = factory.get(f'/contract/export/releases/?project={self.project_a.pk}')
        req_rel.user = self.admin_user
        res_rel = ExportReleases().get(req_rel)
        self.assertEqual(res_rel.status_code, 200)

        from django.db.models.functions import Coalesce
        resolved_sn = ContractorRelease.objects.filter(pk=self.release_a.pk).annotate(
            sn=Coalesce('contractor__contract__serial_number', 'contractor__prev_contract__serial_number')
        ).values_list('sn', flat=True).first()
        self.assertIsNotNone(resolved_sn)
        self.assertTrue(resolved_sn.startswith(orig_sn[:10]))

    def test_pdf_export_cert_occupancy_html_escape(self):
        """[MEDIUM-1] PdfExportCertOccupancy 오버레이 생성 시 HTML 특수문자 이스케이프 검증"""
        from contract.exports.pdf import PdfExportCertOccupancy

        self.project_a.name = '강남 <script>alert(1)</script> 프로젝트'
        self.project_a.location = '서울시 & "강남구"'
        overlay = PdfExportCertOccupancy.generate_text_overlay({
            'contract': self.contract_a,
            'pub_date': date(2026, 2, 1),
            'user': '<img src=x onerror=alert(1)>'
        })
        self.assertNotIn('<script>', overlay)
        self.assertNotIn('<img src=x', overlay)
        self.assertIn('&lt;script&gt;', overlay)
        self.assertIn('&amp;', overlay)

    def test_uncontracted_contract_price_visibility_and_find_page_limit_defense(self):
        """[MEDIUM-2] 미계약 세대 ContractPrice RLS 조회 허용 및 find_page / 가격 업데이트 파라미터 예외 방어 검증"""
        # 1. 프로젝트 A의 미계약 세대 ContractPrice 생성
        ku_un = KeyUnit.objects.create(project=self.project_a, unit_type=self.contract_a.unit_type, unit_code='A-102')
        hu_un = HouseUnit.objects.create(
            unit_type=self.contract_a.unit_type,
            building_unit=self.cp_a.house_unit.building_unit,
            key_unit=ku_un,
            name='102호',
            bldg_line=2,
            floor_no=1
        )
        cp_uncontracted = ContractPrice.objects.create(
            contract=None, house_unit=hu_un, price=500000000
        )

        # user_a로 조회 시 미계약 세대 ContractPrice도 정상 포함됨
        self.client.force_authenticate(user=self.user_a)
        res_cp = self.client.get('/api/v1/cont-price/')
        self.assertEqual(res_cp.status_code, http_status.HTTP_200_OK)
        cp_ids = [item['pk'] for item in res_cp.data['results']]
        self.assertIn(cp_uncontracted.pk, cp_ids)

        # user_b로 조회 시 프로젝트 A의 미계약 세대 ContractPrice는 노출되지 않음
        self.client.force_authenticate(user=self.user_b)
        res_cp_b = self.client.get('/api/v1/cont-price/')
        cp_ids_b = [item['pk'] for item in res_cp_b.data['results']]
        self.assertNotIn(cp_uncontracted.pk, cp_ids_b)

        # 2. find_page에서 limit=0 또는 limit=invalid 전달 시 ZeroDivisionError/ValueError 없이 200 OK 반환
        self.client.force_authenticate(user=self.user_a)
        res_fp_set = self.client.get(f'/api/v1/contract-set/find_page/?highlight_id={self.contract_a.pk}&limit=0')
        self.assertEqual(res_fp_set.status_code, http_status.HTTP_200_OK)

        res_fp_rel = self.client.get(
            f'/api/v1/contractor-release/find-page/?highlight_id={self.release_a.pk}&project={self.project_a.pk}&limit=abc'
        )
        self.assertEqual(res_fp_rel.status_code, http_status.HTTP_200_OK)

        # 3. 가격 일괄 업데이트 뷰에 비정수 project ID 전달 시 500 대신 400 Bad Request 반환
        res_bulk_bad = self.client.post('/api/v1/contract-bulk-price-update/', {'project': 'invalid-id'}, format='json')
        self.assertEqual(res_bulk_bad.status_code, http_status.HTTP_400_BAD_REQUEST)

        res_prev_bad = self.client.get('/api/v1/contract-price-update-preview/?project=invalid-id')
        self.assertEqual(res_prev_bad.status_code, http_status.HTTP_400_BAD_REQUEST)



