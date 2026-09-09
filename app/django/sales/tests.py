from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.test import APITestCase

from company.models import Company
from contract.models import OrderGroup, Contract, Contractor
from items.models import UnitType, KeyUnit, BuildingUnit, HouseUnit
from project.models import Project
from work.models.project import IssueProject, Role, Permission, Member

from sales.models import (
    SalesAgency, SalesTeam, SalesPerson, SalesPersonDocument, CommissionPolicy,
    ContractSalesAgent, SettlementPeriod, CommissionPayout,
    PayoutContractDetail, CommissionClawback
)

User = get_user_model()


class SalesModelUnitTests(TestCase):
    """분양 대행 (sales) 모델 단위 및 비즈니스 로직 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='sales_tester',
            email='sales_tester@example.com',
            password='password123'
        )
        self.company = Company.objects.create(name='테스트 시행사')
        self.issue_project = IssueProject.objects.create(
            company=self.company,
            name='테스트 프로젝트',
            slug='test-sales-proj',
            creator=self.user
        )
        self.project = Project.objects.create(
            issue_project=self.issue_project,
            name='테스트 분양 사업지',
            order=1,
            kind='2',
            start_year='2026',
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24
        )
        self.order_group = OrderGroup.objects.create(
            project=self.project,
            order_number=1,
            name='일반분양 1차',
            is_default_for_uncontracted=True
        )
        self.unit_type = UnitType.objects.create(
            project=self.project,
            name='84A',
            color='#6366F1',
            average_price=450000000,
            num_unit=50
        )
        self.building = BuildingUnit.objects.create(
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
            building_unit=self.building,
            key_unit=self.key_unit,
            name='101호',
            bldg_line=1,
            floor_no=1
        )
        self.contract = Contract.objects.create(
            project=self.project,
            serial_number='CONT-2026-0001',
            order_group=self.order_group,
            unit_type=self.unit_type,
            key_unit=self.key_unit
        )
        self.contractor = Contractor.objects.create(
            contract=self.contract,
            name='홍길동',
            status='2',
            contract_date='2026-09-01'
        )

        # 영업 조직 기본 세팅
        self.agency = SalesAgency.objects.create(
            project=self.project,
            name='㈜골든분양대행',
            is_direct_managed=False,
            ceo_name='김대표',
            phone='02-1234-5678'
        )
        self.hq_team = SalesTeam.objects.create(
            agency=self.agency,
            name='영업1본부'
        )
        self.sub_team = SalesTeam.objects.create(
            agency=self.agency,
            parent=self.hq_team,
            name='분양1팀'
        )
        self.person = SalesPerson.objects.create(
            team=self.sub_team,
            name='이분양',
            duty='1',  # 분양상담사
            status='1',  # 재직
            phone='010-1111-2222',
            tax_type='1',  # 3.3% 프리랜서
            bank_name='국민은행',
            account_number='123-456-789012',
            account_holder='이분양'
        )

    def test_sales_agency_and_team_str(self):
        """대행사 및 영업팀 문자열 표현식 검증"""
        self.assertIn('[외주] ㈜골든분양대행', str(self.agency))
        self.assertEqual(str(self.hq_team), '영업1본부')
        self.assertEqual(str(self.sub_team), '영업1본부 > 분양1팀')

    def test_sales_person_str_and_duty(self):
        """영업 인력 문자열 및 직책 검증"""
        self.assertIn('이분양', str(self.person))
        self.assertIn('분양상담사', str(self.person))
        self.assertEqual(self.person.get_duty_display(), '분양상담사')
        self.assertEqual(self.person.get_tax_type_display(), '3.3% 사업소득 (프리랜서)')

    def test_commission_policy_str(self):
        """수수료 정책 문자열 표현식 (타입 지정 vs 전체 공통)"""
        policy_with_type = CommissionPolicy.objects.create(
            project=self.project,
            unit_type=self.unit_type,
            name='84A 정규 수수료',
            agent_fee=2500000,
            start_date='2026-09-01'
        )
        self.assertIn('84A 정규 수수료 - 84A', str(policy_with_type))

        policy_common = CommissionPolicy.objects.create(
            project=self.project,
            unit_type=None,
            name='전체 공통 기본 수수료',
            agent_fee=2000000,
            start_date='2026-09-01'
        )
        self.assertIn('전체 공통 기본 수수료 (전체 공통)', str(policy_common))

    def test_contract_sales_agent_team_auto_assignment(self):
        """계약 영업 매핑 시 소속 팀이 명시되지 않은 경우 상담사 소속 팀으로 자동 할당"""
        csa = ContractSalesAgent(
            contract=self.contract,
            sales_person=self.person,
            contract_date='2026-09-02'
        )
        csa.save()
        self.assertEqual(csa.team, self.sub_team)
        self.assertIn('CONT-2026-0001 ➔ 이분양 (분양1팀)', str(csa))

    def test_payout_tax_calculation_freelancer_3_3_percent(self):
        """3.3% 프리랜서 사업소득세 원 단위 절사 및 실지급액 계산 검증"""
        period = SettlementPeriod.objects.create(
            project=self.project,
            title='2026년 9월 1회차 정산',
            start_date='2026-09-01',
            end_date='2026-09-15'
        )

        # 1. 3,000,000원 기준 테스트 (정수 3% = 90,000 / 0.3% = 9,000)
        payout = CommissionPayout(
            period=period,
            sales_person=self.person,
            commission_amount=3000000,
            base_pay=0,
            bonus_amount=0,
            deduction_amount=0
        )
        payout.save()

        self.assertEqual(payout.gross_amount, 3000000)
        self.assertEqual(payout.income_tax, 90000)  # 3%
        self.assertEqual(payout.local_income_tax, 9000)  # 0.3%
        self.assertEqual(payout.total_tax, 99000)  # 3.3%
        self.assertEqual(payout.net_amount, 2901000)  # 3,000,000 - 99,000

        # 2. 원 단위 절사(10원 미만 절사) 검증: 3,333,333원
        # 소득세: 3,333,333 * 0.03 = 99,999.99 -> 99,990원 (10원 단위 절사)
        # 지방소득세: 99,990 * 0.1 = 9,999 -> 9,990원 (10원 단위 절사)
        # 원천세 합계: 99,990 + 9,990 = 109,980원
        # 실지급액: 3,333,333 - 109,980 = 3,223,353원
        payout.commission_amount = 3333333
        payout.save()

        self.assertEqual(payout.gross_amount, 3333333)
        self.assertEqual(payout.income_tax, 99990)
        self.assertEqual(payout.local_income_tax, 9990)
        self.assertEqual(payout.total_tax, 109980)
        self.assertEqual(payout.net_amount, 3223353)

    def test_payout_tax_calculation_non_freelancer(self):
        """근로소득/기타 소득 구분 시 원천세 0원 처리 검증"""
        employee = SalesPerson.objects.create(
            team=self.sub_team,
            name='박직원',
            duty='5',  # 지원/기타
            tax_type='2',  # 근로소득
            phone='010-3333-4444'
        )
        period = SettlementPeriod.objects.create(
            project=self.project,
            title='2026년 9월 1회차 정산',
            start_date='2026-09-01',
            end_date='2026-09-15'
        )
        payout = CommissionPayout(
            period=period,
            sales_person=employee,
            base_pay=2500000
        )
        payout.save()

        self.assertEqual(payout.gross_amount, 2500000)
        self.assertEqual(payout.total_tax, 0)
        self.assertEqual(payout.net_amount, 2500000)

    def test_payout_bank_account_auto_sync(self):
        """정산 지급 명세 등록 시 계좌 정보 미입력 시 영업인력 프로필 계좌 자동 복사"""
        period = SettlementPeriod.objects.create(
            project=self.project,
            title='2026년 9월 1회차 정산',
            start_date='2026-09-01',
            end_date='2026-09-15'
        )
        payout = CommissionPayout.objects.create(
            period=period,
            sales_person=self.person,
            commission_amount=1000000
        )
        self.assertEqual(payout.bank_name, self.person.bank_name)
        self.assertEqual(payout.account_number, self.person.account_number)
        self.assertEqual(payout.account_holder, self.person.account_holder)

    def test_commission_clawback_str(self):
        """수수료 환수 모델 상태 문자열 검증"""
        clawback = CommissionClawback.objects.create(
            contract=self.contract,
            sales_person=self.person,
            amount=500000,
            is_settled=False
        )
        self.assertIn('[미상계]', str(clawback))
        clawback.is_settled = True
        clawback.save()
        self.assertIn('[상계완료]', str(clawback))

    def test_sales_person_document_model(self):
        """영업 인력 제출 서류 모델 및 제목 자동완성/사용자지정 검증"""
        sample_file = SimpleUploadedFile("id_doc.pdf", b"dummy resident document content", content_type="application/pdf")

        # 1. title 미입력 시 doc_type의 표시명으로 자동 저장
        doc1 = SalesPersonDocument(
            sales_person=self.person,
            doc_type='1',  # 주민등록등본/초본
            file=sample_file
        )
        doc1.save()
        self.assertEqual(doc1.title, '주민등록등본/초본')
        self.assertIn('이분양 - 주민등록등본/초본', str(doc1))
        self.assertEqual(doc1.file_name, 'id_doc.pdf')
        self.assertFalse(doc1.is_verified)

        # 2. 서약서/각서 ('5') 선택 및 커스텀 title 입력
        sample_file2 = SimpleUploadedFile("pledge.pdf", b"dummy pledge content", content_type="application/pdf")
        doc2 = SalesPersonDocument(
            sales_person=self.person,
            doc_type='5',  # 각종 서약서/각서
            title='비밀유지 및 보안서약서',
            file=sample_file2
        )
        doc2.save()
        self.assertEqual(doc2.title, '비밀유지 및 보안서약서')
        self.assertIn('이분양 - 비밀유지 및 보안서약서', str(doc2))



class SalesAPITests(APITestCase):
    """분양 대행 (sales) REST API 및 핵심 비즈니스 액션 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='sales_admin',
            email='sales_admin@example.com',
            password='password123',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

        self.company = Company.objects.create(name='㈜한국개발')
        self.issue_project = IssueProject.objects.create(
            company=self.company,
            name='강남 센트럴타워',
            slug='gangnam-central',
            type='2',
            creator=self.user
        )
        self.project = Project.objects.create(
            issue_project=self.issue_project,
            name='강남 센트럴타워 프로젝트',
            order=1,
            kind='2',
            start_year='2026',
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24
        )

        # 권한 및 역할 생성
        perms = []
        for code, name in [
            ('sales.read', '분양 대행 조회'),
            ('sales.manage', '분양 조직/인력 관리'),
            ('sales.policy', '분양 수수료 정책'),
            ('sales.settle', '분양 수수료 정산'),
            ('sales.payout', '분양 수수료 지급'),
        ]:
            p, _ = Permission.objects.get_or_create(
                code=code,
                defaults={'name': name, 'module': 'sales', 'is_for_project': True}
            )
            perms.append(p)

        self.sales_role = Role.objects.create(
            name='분양총괄관리자', category='ibs_pr_manage', creator=self.user
        )
        self.sales_role.permissions.add(*perms)

        # 멤버 배정
        member = Member.objects.create(user=self.user, project=self.issue_project)
        member.roles.add(self.sales_role)
        self.order_group = OrderGroup.objects.create(
            project=self.project,
            order_number=1,
            name='1차 정규분양',
            is_default_for_uncontracted=True
        )
        self.unit_type_84 = UnitType.objects.create(
            project=self.project,
            name='84A',
            color='#6366F1',
            average_price=600000000,
            num_unit=50
        )
        self.unit_type_59 = UnitType.objects.create(
            project=self.project,
            name='59A',
            color='#10B981',
            average_price=450000000,
            num_unit=50
        )
        self.building = BuildingUnit.objects.create(
            project=self.project,
            name='101동'
        )

        # 영업 조직 구성
        self.agency = SalesAgency.objects.create(
            project=self.project,
            name='㈜미래분양대행',
            is_direct_managed=True,
            ceo_name='홍길동',
            phone='02-555-1234'
        )
        self.team = SalesTeam.objects.create(
            agency=self.agency,
            name='영업1본부 1팀'
        )
        # 상담사 1 (프리랜서 3.3%)
        self.counselor = SalesPerson.objects.create(
            team=self.team,
            name='김상담',
            duty='1',  # 분양상담사
            status='1',  # 재직
            phone='010-1234-5678',
            tax_type='1',
            bank_name='신한은행',
            account_number='110-123-456789',
            account_holder='김상담'
        )
        # 팀장 1 (프리랜서 3.3%)
        self.leader = SalesPerson.objects.create(
            team=self.team,
            name='박팀장',
            duty='2',  # 팀장
            status='1',  # 재직
            phone='010-8765-4321',
            tax_type='1',
            bank_name='하나은행',
            account_number='220-123-456789',
            account_holder='박팀장'
        )

        # 수수료 정책: 84A 타입 정책 (상담사 200만, 팀장 50만)
        self.policy_84 = CommissionPolicy.objects.create(
            project=self.project,
            unit_type=self.unit_type_84,
            name='84A 분양 수수료 기준',
            agent_fee=2000000,
            leader_fee=500000,
            director_fee=300000,
            agency_fee=1000000,
            start_date='2026-09-01'
        )

    def test_sales_agency_api_crud(self):
        """분양 대행사 등록 및 목록 조회 API 검증"""
        # 생성
        payload = {
            'project': self.project.id,
            'name': '㈜신한마케팅',
            'is_direct_managed': True,
            'ceo_name': '신대표',
            'phone': '02-777-8888',
            'business_number': '123-45-67890'
        }
        res = self.client.post('/api/v1/sales-agency/', payload)
        self.assertEqual(res.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], '㈜신한마케팅')
        self.assertTrue(res.data['is_direct_managed'])

        # 조회 및 필터링
        res_list = self.client.get(f'/api/v1/sales-agency/?project={self.project.id}')
        self.assertEqual(res_list.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res_list.data['count'], 2)

    def test_sales_team_api_crud_and_members_count(self):
        """영업 팀 등록 및 소속 인력 카운트 검증"""
        # 목록 조회: members_count 계산 필드 확인 (현재 self.team에 2명 등록됨)
        res = self.client.get(f'/api/v1/sales-team/?agency={self.agency.id}')
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['members_count'], 2)

        # 신규 팀 생성
        payload = {
            'agency': self.agency.id,
            'parent': self.team.id,
            'name': '분양2팀',
            'order': 2
        }
        res_post = self.client.post('/api/v1/sales-team/', payload)
        self.assertEqual(res_post.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(res_post.data['name'], '분양2팀')
        self.assertEqual(res_post.data['parent_name'], '영업1본부 1팀')

    def test_sales_person_api_crud_and_filtering(self):
        """영업 인력 등록 및 직책/상태별 필터링 API 검증"""
        payload = {
            'team': self.team.id,
            'name': '최본부',
            'duty': '3',  # 본부장
            'status': '1',
            'phone': '010-9999-0000',
            'tax_type': '1'
        }
        res_post = self.client.post('/api/v1/sales-person/', payload)
        self.assertEqual(res_post.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(res_post.data['duty_display'], '본부장')

        # 직책별 필터링 (상담사만 조회)
        res_filter = self.client.get('/api/v1/sales-person/?duty=1')
        self.assertEqual(res_filter.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res_filter.data['count'], 1)
        self.assertEqual(res_filter.data['results'][0]['name'], '김상담')

    def test_commission_policy_api_crud(self):
        """수수료 정책 등록 및 조회 API 검증"""
        payload = {
            'project': self.project.id,
            'unit_type': self.unit_type_59.id,
            'name': '59A 분양 수수료 기준',
            'agent_fee': 1800000,
            'leader_fee': 400000,
            'director_fee': 200000,
            'agency_fee': 800000,
            'start_date': '2026-09-01'
        }
        res = self.client.post('/api/v1/sales-policy/', payload)
        self.assertEqual(res.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(res.data['agent_fee'], 1800000)
        self.assertEqual(res.data['unit_type_name'], '59A')

    def test_contract_sales_agent_mapping_api(self):
        """계약 영업 담당자 매핑 생성 및 상세 조회 API 검증"""
        key_unit = KeyUnit.objects.create(
            project=self.project,
            unit_type=self.unit_type_84,
            unit_code='B101'
        )
        contract = Contract.objects.create(
            project=self.project,
            serial_number='CONT-2026-0010',
            order_group=self.order_group,
            unit_type=self.unit_type_84,
            key_unit=key_unit
        )
        Contractor.objects.create(
            contract=contract,
            name='강계약',
            status='2',
            contract_date='2026-09-03'
        )

        payload = {
            'contract': contract.id,
            'sales_person': self.counselor.id,
            'team': self.team.id,
            'policy': self.policy_84.id,
            'contract_date': '2026-09-03',
            'mgm_name': '강남공인중개사',
            'mgm_fee': 500000
        }
        res = self.client.post('/api/v1/sales-contract-agent/', payload)
        self.assertEqual(res.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(res.data['contract_serial'], 'CONT-2026-0010')
        self.assertEqual(res.data['sales_person_name'], '김상담')
        self.assertEqual(res.data['contractor_name'], '강계약')

    def test_generate_payouts_batch_action(self):
        """
        [핵심 정산 로직 검증]
        정산 회차(SettlementPeriod)의 generate-payouts 액션을 호출하여:
        1. 기간 내 계약 실적 자동 집계
        2. 직책별(상담사 200만 vs 팀장 50만) 수수료 차등 산출
        3. 미상계된 수수료 환수금(Clawback 30만) 자동 차감 및 상계 처리
        4. 회차 전체 합계 금액(총계약수, 총지급액, 총원천세, 총실지급액) 갱신
        """
        # 1. 계약 3건 생성 (김상담 2건, 박팀장 1건)
        # 1-1. 김상담 1차 계약
        ku1 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='C101')
        c1 = Contract.objects.create(project=self.project, serial_number='CONT-C101', order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku1)
        Contractor.objects.create(contract=c1, name='계약자A', status='2')
        ContractSalesAgent.objects.create(contract=c1, sales_person=self.counselor, team=self.team, policy=self.policy_84, contract_date='2026-09-02')

        # 1-2. 김상담 2차 계약
        ku2 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='C102')
        c2 = Contract.objects.create(project=self.project, serial_number='CONT-C102', order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku2)
        Contractor.objects.create(contract=c2, name='계약자B', status='2')
        ContractSalesAgent.objects.create(contract=c2, sales_person=self.counselor, team=self.team, policy=self.policy_84, contract_date='2026-09-05')

        # 1-3. 박팀장 계약 1건
        ku3 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='C103')
        c3 = Contract.objects.create(project=self.project, serial_number='CONT-C103', order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku3)
        Contractor.objects.create(contract=c3, name='계약자C', status='2')
        ContractSalesAgent.objects.create(contract=c3, sales_person=self.leader, team=self.team, policy=self.policy_84, contract_date='2026-09-06')

        # 1-4. 정산 기간 밖(2026-09-20)의 계약 (집계에서 제외되어야 함)
        ku_out = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='C104')
        c_out = Contract.objects.create(project=self.project, serial_number='CONT-C104', order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku_out)
        Contractor.objects.create(contract=c_out, name='계약자D', status='2')
        ContractSalesAgent.objects.create(contract=c_out, sales_person=self.counselor, team=self.team, policy=self.policy_84, contract_date='2026-09-20')

        # 2. 김상담 앞으로 이전 해지 계약에 대한 미상계 환수금(300,000원) 등록
        clawback = CommissionClawback.objects.create(
            contract=c1,
            sales_person=self.counselor,
            amount=300000,
            reason='이전 계약 해지 수수료 환수',
            is_settled=False
        )

        # 3. 정산 회차 생성 (2026-09-01 ~ 2026-09-15)
        period = SettlementPeriod.objects.create(
            project=self.project,
            title='2026년 9월 1회차 수수료 정산',
            start_date='2026-09-01',
            end_date='2026-09-15',
            created_by=self.user
        )

        # 4. 정산 집계 액션 실행: POST /api/v1/sales-settlement-period/{id}/generate-payouts/
        url = f'/api/v1/sales-settlement-period/{period.id}/generate-payouts/'
        res = self.client.post(url)
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)

        # 5. 김상담 지급 명세 검증
        # - 계약 2건 (건당 2,000,000원 = 4,000,000원)
        # - 환수 공제 300,000원
        # - 총 지급액(세전): 4,000,000 - 300,000 = 3,700,000원
        # - 소득세(3%): 3,700,000 * 0.03 = 111,000원
        # - 지방세(0.3%): 111,000 * 0.1 = 11,100원
        # - 원천세 합계(3.3%): 122,100원
        # - 실지급액(세후): 3,700,000 - 122,100 = 3,577,900원
        counselor_payout = CommissionPayout.objects.get(period=period, sales_person=self.counselor)
        self.assertEqual(counselor_payout.contract_count, 2)
        self.assertEqual(counselor_payout.commission_amount, 4000000)
        self.assertEqual(counselor_payout.deduction_amount, 300000)
        self.assertEqual(counselor_payout.gross_amount, 3700000)
        self.assertEqual(counselor_payout.income_tax, 111000)
        self.assertEqual(counselor_payout.local_income_tax, 11100)
        self.assertEqual(counselor_payout.total_tax, 122100)
        self.assertEqual(counselor_payout.net_amount, 3577900)

        # 환수금 상계 플래그가 True로 전환되었고 payout에 연결되었는지 확인
        clawback.refresh_from_db()
        self.assertTrue(clawback.is_settled)
        self.assertEqual(clawback.settled_payout, counselor_payout)

        # 김상담 계약 상세 2건 기록 확인
        self.assertEqual(counselor_payout.contract_details.count(), 2)
        for detail in counselor_payout.contract_details.all():
            self.assertEqual(detail.role_type, 'agent')
            self.assertEqual(detail.unit_fee, 2000000)

        # 6. 박팀장 지급 명세 검증
        # - 팀장 직책: 본인 계약 1건 (agent_fee 200만 + leader_fee 50만 = 250만)
        #             + 소속 상담사(김상담) 계약 2건에 대한 관리 수수료 (각 50만 * 2 = 100만)
        #             = 총 3건, 3,500,000원
        # - 소득세(3%): 105,000원 / 지방세(0.3%): 10,500원 / 합계: 115,500원
        # - 실지급액: 3,500,000 - 115,500 = 3,384,500원
        leader_payout = CommissionPayout.objects.get(period=period, sales_person=self.leader)
        self.assertEqual(leader_payout.contract_count, 3)
        self.assertEqual(leader_payout.commission_amount, 3500000)
        self.assertEqual(leader_payout.gross_amount, 3500000)
        self.assertEqual(leader_payout.income_tax, 105000)
        self.assertEqual(leader_payout.local_income_tax, 10500)
        self.assertEqual(leader_payout.total_tax, 115500)
        self.assertEqual(leader_payout.net_amount, 3384500)

        # 박팀장 계약 상세 3건 기록 확인
        self.assertEqual(leader_payout.contract_details.count(), 3)

        # 7. SettlementPeriod 합계 필드 갱신 검증
        # - 총 계약 건수: 2 + 1 = 3건
        # - 총 지급액 (세전): 3,700,000 + 3,500,000 = 7,200,000원
        # - 총 원천세: 122,100 + 115,500 = 237,600원
        # - 총 실지급액 (세후): 3,577,900 + 3,384,500 = 6,962,400원
        period.refresh_from_db()
        self.assertEqual(period.total_contracts, 3)
        self.assertEqual(period.total_gross_amount, 7200000)
        self.assertEqual(period.total_tax_amount, 237600)
        self.assertEqual(period.total_net_amount, 6962400)

    def test_generate_payouts_empty_period(self):
        """정산 기간 내 실적이 없을 경우 빈 결과 응답 반환 검증"""
        empty_period = SettlementPeriod.objects.create(
            project=self.project,
            title='실적 없는 회차',
            start_date='2026-08-01',
            end_date='2026-08-15'
        )
        url = f'/api/v1/sales-settlement-period/{empty_period.id}/generate-payouts/'
        res = self.client.post(url)
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res.data['total_contracts'], 0)

    def test_confirm_settlement_action(self):
        """정산 회차 확정 (상태: 정산 확정 '2') 액션 검증"""
        period = SettlementPeriod.objects.create(
            project=self.project,
            title='2026년 9월 1회차 수수료 정산',
            start_date='2026-09-01',
            end_date='2026-09-15',
            status='1'  # 작성 중
        )
        url = f'/api/v1/sales-settlement-period/{period.id}/confirm-settlement/'
        res = self.client.post(url)
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)

        period.refresh_from_db()
        self.assertEqual(period.status, '2')  # 확정됨

    def test_update_payout_status_action(self):
        """지급 명세 상태 변경 및 지급완료 시 지급일 자동 기록 검증"""
        period = SettlementPeriod.objects.create(
            project=self.project,
            title='2026년 9월 1회차 수수료 정산',
            start_date='2026-09-01',
            end_date='2026-09-15'
        )
        payout = CommissionPayout.objects.create(
            period=period,
            sales_person=self.counselor,
            commission_amount=2000000,
            pay_status='1'  # 대기
        )
        self.assertIsNone(payout.paid_date)

        # 1. 승인 상태로 변경
        url = f'/api/v1/sales-payout/{payout.id}/update-pay-status/'
        res_approve = self.client.post(url, {'pay_status': '2'})
        self.assertEqual(res_approve.status_code, http_status.HTTP_200_OK)
        payout.refresh_from_db()
        self.assertEqual(payout.pay_status, '2')
        self.assertIsNone(payout.paid_date)

        # 2. 지급 완료 상태로 변경 시 paid_date 오늘 날짜로 자동 기록
        res_paid = self.client.post(url, {'pay_status': '3'})
        self.assertEqual(res_paid.status_code, http_status.HTTP_200_OK)
        payout.refresh_from_db()
        self.assertEqual(payout.pay_status, '3')
        self.assertEqual(payout.paid_date, timezone.localdate())

        # 3. 잘못된 상태값 전송 시 400 에러 반환
        res_invalid = self.client.post(url, {'pay_status': '99'})
        self.assertEqual(res_invalid.status_code, http_status.HTTP_400_BAD_REQUEST)

    def test_sales_person_document_api_crud_and_verify(self):
        """영업 인력 서류 업로드, 인력 상세 조회 시 documents_count 연동, 관리자 검증(verify) 액션 검증"""
        # 1. 파일 업로드 API 호출
        test_file = SimpleUploadedFile("bank_book.pdf", b"%PDF-1.4 dummy bank book", content_type="application/pdf")
        payload = {
            'sales_person': self.counselor.id,
            'doc_type': '2',  # 통장 사본
            'title': '신한은행 통장 사본',
            'file': test_file
        }
        res_post = self.client.post('/api/v1/sales-person-document/', payload, format='multipart')
        self.assertEqual(res_post.status_code, http_status.HTTP_201_CREATED)
        doc_id = res_post.data['id']
        self.assertEqual(res_post.data['sales_person_name'], '김상담')
        self.assertEqual(res_post.data['doc_type_display'], '통장 사본 (계좌 사본)')
        self.assertEqual(res_post.data['uploader_name'], 'sales_admin')
        self.assertFalse(res_post.data['is_verified'])

        # 2. 영업 인력 목록/상세 조회 시 documents_count 및 documents 리스트 확인
        res_person = self.client.get(f'/api/v1/sales-person/{self.counselor.id}/')
        self.assertEqual(res_person.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res_person.data['documents_count'], 1)
        self.assertEqual(len(res_person.data['documents']), 1)
        self.assertEqual(res_person.data['documents'][0]['title'], '신한은행 통장 사본')

        # 3. 관리자 서류 검증(verify) 액션 호출
        verify_url = f'/api/v1/sales-person-document/{doc_id}/verify/'
        res_verify = self.client.post(verify_url, {'is_verified': True})
        self.assertEqual(res_verify.status_code, http_status.HTTP_200_OK)
        self.assertTrue(res_verify.data['is_verified'])
        self.assertEqual(res_verify.data['verified_by_name'], 'sales_admin')
        self.assertIsNotNone(res_verify.data['verified_at'])

        # 4. 필터링 검증 (is_verified=true)
        res_filter = self.client.get(f'/api/v1/sales-person-document/?sales_person={self.counselor.id}&is_verified=true')
        self.assertEqual(res_filter.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res_filter.data['count'], 1)

        # 5. 검증 취소 액션 호출
        res_unverify = self.client.post(verify_url, {'is_verified': False})
        self.assertEqual(res_unverify.status_code, http_status.HTTP_200_OK)
        self.assertFalse(res_unverify.data['is_verified'])

        # 6. 서류 구분(doc_type) 필터링 검증
        res_doc_type = self.client.get(f'/api/v1/sales-person-document/?sales_person={self.counselor.id}&doc_type=2')
        self.assertEqual(res_doc_type.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res_doc_type.data['count'], 1)

        res_other_type = self.client.get(f'/api/v1/sales-person-document/?sales_person={self.counselor.id}&doc_type=1')
        self.assertEqual(res_other_type.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res_other_type.data['count'], 0)

        # 7. 서류 삭제 API 호출 및 인력 documents_count 반영 검증
        res_del = self.client.delete(f'/api/v1/sales-person-document/{doc_id}/')
        self.assertEqual(res_del.status_code, http_status.HTTP_204_NO_CONTENT)

        res_person_after_del = self.client.get(f'/api/v1/sales-person/{self.counselor.id}/')
        self.assertEqual(res_person_after_del.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res_person_after_del.data['documents_count'], 0)
        self.assertEqual(len(res_person_after_del.data['documents']), 0)


class SalesPermissionSecurityTests(APITestCase):
    """분양 대행 (sales) 권한 체계 및 Row-Level Security 격리 검증"""

    def setUp(self):
        # 1. 관리자, 회사 및 프로젝트 2개 생성
        self.admin_user = User.objects.create_superuser(
            username='admin_sales', email='admin_sales@test.com', password='password123'
        )
        self.company = Company.objects.create(name='㈜한국개발')
        self.ip_a = IssueProject.objects.create(
            company=self.company, name='프로젝트A', slug='project-a', type='2', creator=self.admin_user
        )
        self.project_a = Project.objects.create(
            issue_project=self.ip_a, name='프로젝트A', order=1, kind='2',
            start_year='2026', monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01', construction_period_months=24
        )

        self.ip_b = IssueProject.objects.create(
            company=self.company, name='프로젝트B', slug='project-b', type='2', creator=self.admin_user
        )
        self.project_b = Project.objects.create(
            issue_project=self.ip_b, name='프로젝트B', order=2, kind='2',
            start_year='2026', monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01', construction_period_months=24
        )

        # 2. 권한 객체 조회/생성
        self.perm_read, _ = Permission.objects.get_or_create(
            code='sales.read', defaults={'name': '분양 대행 조회', 'module': 'sales', 'is_for_project': True}
        )
        self.perm_manage, _ = Permission.objects.get_or_create(
            code='sales.manage', defaults={'name': '분양 조직/인력 관리', 'module': 'sales', 'is_for_project': True}
        )
        self.perm_policy, _ = Permission.objects.get_or_create(
            code='sales.policy', defaults={'name': '분양 수수료 정책', 'module': 'sales', 'is_for_project': True}
        )
        self.perm_settle, _ = Permission.objects.get_or_create(
            code='sales.settle', defaults={'name': '분양 수수료 정산', 'module': 'sales', 'is_for_project': True}
        )
        self.perm_payout, _ = Permission.objects.get_or_create(
            code='sales.payout', defaults={'name': '분양 수수료 지급', 'module': 'sales', 'is_for_project': True}
        )

        # 3. 역할 정의
        # 3-1. 읽기 전용 역할
        self.role_readonly = Role.objects.create(name='영업조회자', category='ibs_pr_manage', creator=self.admin_user)
        self.role_readonly.permissions.add(self.perm_read)

        # 3-2. 조직 관리자 역할
        self.role_manager = Role.objects.create(name='영업관리자', category='ibs_pr_manage', creator=self.admin_user)
        self.role_manager.permissions.add(self.perm_read, self.perm_manage)

        # 3-3. 정산 관리자 역할
        self.role_settler = Role.objects.create(name='정산관리자', category='ibs_pr_manage', creator=self.admin_user)
        self.role_settler.permissions.add(self.perm_read, self.perm_settle)

        # 4. 사용자 생성 및 프로젝트A 멤버 배정
        self.user_readonly = User.objects.create_user(
            username='user_ro', email='ro@test.com', password='password123'
        )
        mem_ro = Member.objects.create(user=self.user_readonly, project=self.ip_a)
        mem_ro.roles.add(self.role_readonly)

        self.user_manager = User.objects.create_user(
            username='user_mgr', email='mgr@test.com', password='password123'
        )
        mem_mgr = Member.objects.create(user=self.user_manager, project=self.ip_a)
        mem_mgr.roles.add(self.role_manager)

        self.user_settler = User.objects.create_user(
            username='user_settle', email='settle@test.com', password='password123'
        )
        mem_settle = Member.objects.create(user=self.user_settler, project=self.ip_a)
        mem_settle.roles.add(self.role_settler)

        # 외부 사용자 (프로젝트B 소속)
        self.user_outsider = User.objects.create_user(
            username='user_outsider', email='out@test.com', password='password123'
        )
        mem_out = Member.objects.create(user=self.user_outsider, project=self.ip_b)
        mem_out.roles.add(self.role_manager)

        # 5. 기본 데이터 생성 (프로젝트A)
        self.agency_a = SalesAgency.objects.create(project=self.project_a, name='A대행사')
        self.team_a = SalesTeam.objects.create(agency=self.agency_a, name='A-1팀')
        self.person_a = SalesPerson.objects.create(team=self.team_a, name='상담사A', phone='010-1111-2222')
        self.period_a = SettlementPeriod.objects.create(
            project=self.project_a, title='A-1회차', start_date='2026-09-01', end_date='2026-09-30'
        )
        self.payout_a = CommissionPayout.objects.create(
            period=self.period_a, sales_person=self.person_a, commission_amount=1000000
        )

        # 기본 데이터 생성 (프로젝트B)
        self.agency_b = SalesAgency.objects.create(project=self.project_b, name='B대행사')

    def test_sales_readonly_user_permission_denials(self):
        """sales.read만 가진 사용자는 대행사 등록, 정산 회차 생성 등이 차단(403)되어야 함"""
        self.client.force_authenticate(user=self.user_readonly)

        # 1. 대행사 조회는 허용 (200 OK)
        res_get = self.client.get(f'/api/v1/sales-agency/?project={self.project_a.id}')
        self.assertEqual(res_get.status_code, http_status.HTTP_200_OK)

        # 2. 대행사 생성 차단 (403 Forbidden - sales.manage 필요)
        res_post = self.client.post('/api/v1/sales-agency/', {
            'project': self.project_a.id,
            'name': '신규대행사'
        })
        self.assertEqual(res_post.status_code, http_status.HTTP_403_FORBIDDEN)

        # 3. 정산 회차 생성 차단 (403 Forbidden - sales.settle 필요)
        res_period = self.client.post('/api/v1/sales-settlement-period/', {
            'project': self.project_a.id,
            'title': '임의회차',
            'start_date': '2026-10-01',
            'end_date': '2026-10-31'
        })
        self.assertEqual(res_period.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_sales_manager_cannot_manage_settlement_or_payout(self):
        """sales.manage만 가진 사용자는 정산 회차 생성 및 지급 상태 변경이 차단(403)되어야 함"""
        self.client.force_authenticate(user=self.user_manager)

        # 1. 조직(팀) 등록 허용 (201 Created)
        res_team = self.client.post('/api/v1/sales-team/', {
            'agency': self.agency_a.id,
            'name': '신규팀'
        })
        self.assertEqual(res_team.status_code, http_status.HTTP_201_CREATED)

        # 2. 정산 회차 생성 차단 (403 Forbidden - sales.settle 필요)
        res_period = self.client.post('/api/v1/sales-settlement-period/', {
            'project': self.project_a.id,
            'title': '임의회차',
            'start_date': '2026-10-01',
            'end_date': '2026-10-31'
        })
        self.assertEqual(res_period.status_code, http_status.HTTP_403_FORBIDDEN)

        # 3. 지급 상태 변경 차단 (403 Forbidden - sales.payout 필요)
        res_payout = self.client.post(
            f'/api/v1/sales-payout/{self.payout_a.id}/update-pay-status/',
            {'pay_status': '2'}
        )
        self.assertEqual(res_payout.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_row_level_security_isolation_between_projects(self):
        """프로젝트B 사용자는 프로젝트A의 대행사, 팀, 인력 목록을 조회할 수 없음"""
        self.client.force_authenticate(user=self.user_outsider)

        # 타 프로젝트(A)를 명시하여 조회 시 해당 프로젝트의 권한이 없으므로 403 Forbidden 차단
        res = self.client.get(f'/api/v1/sales-agency/?project={self.project_a.id}')
        self.assertEqual(res.status_code, http_status.HTTP_403_FORBIDDEN)

        # 전체 대행사 목록 조회 시 본인 소속(프로젝트B) 대행사만 조회됨 (Row-Level Security)
        res_all = self.client.get('/api/v1/sales-agency/')
        self.assertEqual(res_all.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res_all.data['count'], 1)
        self.assertEqual(res_all.data['results'][0]['id'], self.agency_b.id)


class SalesMultiAgencyPayoutTests(APITestCase):
    """복수 외주 대행사 배정 및 직영+외주 복합 운영 정산 검증"""

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from company.models import Company
        from project.models import Project
        from work.models.project import IssueProject, Role, Permission, Member
        from contract.models import OrderGroup
        from items.models import UnitType

        self.admin_user = User.objects.create_superuser(
            username='sales_admin_ma', email='admin_ma@test.com', password='password123'
        )
        self.client.force_authenticate(user=self.admin_user)

        company = Company.objects.create(name='㈜복합분양개발')
        ip = IssueProject.objects.create(
            company=company, name='복합운영프로젝트', slug='multi-agency-proj',
            type='2', creator=self.admin_user
        )
        self.project = Project.objects.create(
            issue_project=ip, name='복합운영프로젝트', order=1, kind='2',
            start_year='2026', monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01', construction_period_months=24
        )

        perm_settle, _ = Permission.objects.get_or_create(
            code='sales.settle', defaults={'name': '분양 수수료 정산', 'module': 'sales', 'is_for_project': True}
        )
        perm_manage, _ = Permission.objects.get_or_create(
            code='sales.manage', defaults={'name': '분양 조직/인력 관리', 'module': 'sales', 'is_for_project': True}
        )
        perm_read, _ = Permission.objects.get_or_create(
            code='sales.read', defaults={'name': '분양 대행 조회', 'module': 'sales', 'is_for_project': True}
        )
        role = Role.objects.create(name='정산관리자MA', category='ibs_pr_manage', creator=self.admin_user)
        role.permissions.add(perm_read, perm_manage, perm_settle)
        mem = Member.objects.create(user=self.admin_user, project=ip)
        mem.roles.add(role)

        self.order_group = OrderGroup.objects.create(
            project=self.project, order_number=1, name='1차 정규분양', is_default_for_uncontracted=True
        )
        self.unit_type_84 = UnitType.objects.create(
            project=self.project, name='84A', color='#6366F1',
            average_price=600000000, num_unit=50
        )

        # 직영 대행사 + 팀 + 인력
        self.direct_agency = SalesAgency.objects.create(
            project=self.project, name='㈜직영분양대행', is_direct_managed=True
        )
        self.team = SalesTeam.objects.create(agency=self.direct_agency, name='직영1팀')
        self.counselor = SalesPerson.objects.create(
            team=self.team, name='김상담', duty='1', status='1',
            phone='010-1111-2222', tax_type='1'
        )
        self.leader = SalesPerson.objects.create(
            team=self.team, name='박팀장', duty='2', status='1',
            phone='010-3333-4444', tax_type='1'
        )

        # 공통 수수료 정책: agent 200만 / leader 50만 / director 30만 / agency 100만
        self.policy = CommissionPolicy.objects.create(
            project=self.project, unit_type=self.unit_type_84,
            name='84A 정책', agent_fee=2000000, leader_fee=500000,
            director_fee=300000, agency_fee=1000000, start_date='2026-09-01'
        )

    def test_generate_payouts_multi_outsource_agencies(self):
        """
        [복수 외주 대행사 복합 정산 검증]

        2개의 외주 대행사(외주A, 외주B)가 각각 계약 건을 배정 받았을 때:
        1. 각 대행사별로 독립적인 AgencyPayout이 생성되어야 한다.
        2. 각 AgencyPayout의 계약 건수 및 agency_fee_sum이 정확해야 한다.
        3. 직영 CommissionPayout은 생성되지 않아야 한다.
        4. total_contracts는 원천 계약 수(이중 계산 없이) 3건이어야 한다.
        """
        # 1. 외주 대행사 2개 생성 (is_direct_managed=False)
        agency_a = SalesAgency.objects.create(
            project=self.project,
            name='㈜아웃소싱A분양',
            is_direct_managed=False,
            business_number='111-11-11111'
        )
        agency_b = SalesAgency.objects.create(
            project=self.project,
            name='㈜아웃소싱B분양',
            is_direct_managed=False,
            business_number='222-22-22222'
        )

        # 2. 계약 3건 생성: 외주A 2건, 외주B 1건
        # 외주A 1번 계약
        ku1 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='MA01')
        c1 = Contract.objects.create(project=self.project, serial_number='CONT-MA01',
                                     order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku1)
        Contractor.objects.create(contract=c1, name='계약자MA01', status='2')
        ContractSalesAgent.objects.create(
            contract=c1, agency=agency_a, policy=self.policy, contract_date='2026-09-01'
        )

        # 외주A 2번 계약
        ku2 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='MA02')
        c2 = Contract.objects.create(project=self.project, serial_number='CONT-MA02',
                                     order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku2)
        Contractor.objects.create(contract=c2, name='계약자MA02', status='2')
        ContractSalesAgent.objects.create(
            contract=c2, agency=agency_a, policy=self.policy, contract_date='2026-09-03'
        )

        # 외주B 1번 계약
        ku3 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='MB01')
        c3 = Contract.objects.create(project=self.project, serial_number='CONT-MB01',
                                     order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku3)
        Contractor.objects.create(contract=c3, name='계약자MB01', status='2')
        ContractSalesAgent.objects.create(
            contract=c3, agency=agency_b, policy=self.policy, contract_date='2026-09-05'
        )

        # 3. 정산 회차 생성 후 generate-payouts 액션 호출
        period = SettlementPeriod.objects.create(
            project=self.project,
            title='복수 외주 대행사 정산 회차',
            start_date='2026-09-01',
            end_date='2026-09-15'
        )
        url = f'/api/v1/sales-settlement-period/{period.id}/generate-payouts/'
        res = self.client.post(url)
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)

        # 4. 반환 데이터 검증
        # - 직영 인력 정산 없음 (direct_person_count = 0)
        # - 대행사 수: 2개
        # - 총 계약 건수: 3건 (외주A 2 + 외주B 1)
        self.assertEqual(res.data['direct_person_count'], 0)
        self.assertEqual(res.data['agency_count'], 2)
        self.assertEqual(res.data['total_contracts'], 3)

        # 5. CommissionPayout (직영 인력 정산)이 생성되지 않아야 함
        from sales.models import AgencyPayout
        self.assertEqual(period.payouts.count(), 0)

        # 6. AgencyPayout 2개 독립 생성 검증
        self.assertEqual(period.agency_payouts.count(), 2)

        # 외주A: 건당 전체 수수료 합산 3,800,000 × 2건 = 7,600,000
        # (agent 200만 + leader 50만 + director 30만 + agency 100만 = 380만)
        payout_a = AgencyPayout.objects.get(period=period, agency=agency_a)
        self.assertEqual(payout_a.contract_count, 2)
        self.assertEqual(payout_a.agency_fee_sum, 7600000)
        # VAT 10%: 760,000 / 합계 8,360,000
        self.assertEqual(payout_a.vat_amount, 760000)
        self.assertEqual(payout_a.total_amount, 8360000)
        self.assertEqual(payout_a.contract_details.count(), 2)

        # 외주B: 건당 전체 수수료 합산 3,800,000 × 1건 = 3,800,000
        payout_b = AgencyPayout.objects.get(period=period, agency=agency_b)
        self.assertEqual(payout_b.contract_count, 1)
        self.assertEqual(payout_b.agency_fee_sum, 3800000)
        self.assertEqual(payout_b.vat_amount, 380000)
        self.assertEqual(payout_b.total_amount, 4180000)
        self.assertEqual(payout_b.contract_details.count(), 1)

        # 7. 총 외주 대행 지급 금액: 8,360,000 + 4,180,000 = 12,540,000
        self.assertEqual(res.data['total_agency_amount'], 12540000)


    def test_generate_payouts_mixed_direct_and_outsource(self):
        """
        [직영 + 외주 복합 운영 정산 검증]
        직영 상담사 2건 + 외주 대행사(2개) 3건이 동일 정산 회차에 포함될 때:
        1. CommissionPayout (직영 인력)과 AgencyPayout (외주 대행사)가 동시에 생성되어야 한다.
        2. 직영 상담사(김상담) 2건 수수료 + 팀장(박팀장) 관리 수수료 계층별 분배가 정확해야 한다.
        3. 외주A·B 대행사 각각의 AgencyPayout이 독립 집계되어야 한다.
        4. total_contracts는 원천 계약 수만 집계 (계층 cascade 중복 없음) = 5건.
        5. 동일 정산 회차에서 재실행(generate-payouts 재호출)해도 이중 정산이 발생하지 않아야 한다.
        """
        # 외주 대행사 2개 생성
        outsource_a = SalesAgency.objects.create(
            project=self.project,
            name='㈜외주분양대행A',
            is_direct_managed=False,
            business_number='333-33-33333'
        )
        outsource_b = SalesAgency.objects.create(
            project=self.project,
            name='㈜외주분양대행B',
            is_direct_managed=False,
            business_number='444-44-44444'
        )

        # ── 직영 계약 2건 (김상담 담당) ──
        ku_d1 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='D01')
        c_d1 = Contract.objects.create(project=self.project, serial_number='CONT-D01',
                                       order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku_d1)
        Contractor.objects.create(contract=c_d1, name='직영계약자1', status='2')
        ContractSalesAgent.objects.create(
            contract=c_d1, sales_person=self.counselor, team=self.team,
            policy=self.policy, contract_date='2026-09-01'
        )

        ku_d2 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='D02')
        c_d2 = Contract.objects.create(project=self.project, serial_number='CONT-D02',
                                       order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku_d2)
        Contractor.objects.create(contract=c_d2, name='직영계약자2', status='2')
        ContractSalesAgent.objects.create(
            contract=c_d2, sales_person=self.counselor, team=self.team,
            policy=self.policy, contract_date='2026-09-03'
        )

        # ── 외주A 계약 2건 ──
        ku_a1 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='A01')
        c_a1 = Contract.objects.create(project=self.project, serial_number='CONT-A01',
                                       order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku_a1)
        Contractor.objects.create(contract=c_a1, name='외주A계약자1', status='2')
        ContractSalesAgent.objects.create(
            contract=c_a1, agency=outsource_a, policy=self.policy, contract_date='2026-09-02'
        )

        ku_a2 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='A02')
        c_a2 = Contract.objects.create(project=self.project, serial_number='CONT-A02',
                                       order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku_a2)
        Contractor.objects.create(contract=c_a2, name='외주A계약자2', status='2')
        ContractSalesAgent.objects.create(
            contract=c_a2, agency=outsource_a, policy=self.policy, contract_date='2026-09-04'
        )

        # ── 외주B 계약 1건 ──
        ku_b1 = KeyUnit.objects.create(project=self.project, unit_type=self.unit_type_84, unit_code='B01')
        c_b1 = Contract.objects.create(project=self.project, serial_number='CONT-B01',
                                       order_group=self.order_group, unit_type=self.unit_type_84, key_unit=ku_b1)
        Contractor.objects.create(contract=c_b1, name='외주B계약자1', status='2')
        ContractSalesAgent.objects.create(
            contract=c_b1, agency=outsource_b, policy=self.policy, contract_date='2026-09-06'
        )

        # 정산 회차 생성 + 첫 번째 generate-payouts 호출
        period = SettlementPeriod.objects.create(
            project=self.project,
            title='직영+외주 복합 정산 회차',
            start_date='2026-09-01',
            end_date='2026-09-15'
        )
        url = f'/api/v1/sales-settlement-period/{period.id}/generate-payouts/'
        res = self.client.post(url)
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)

        # ── 기본 건수 검증 ──
        # - 총 원천 계약: 직영 2건 + 외주A 2건 + 외주B 1건 = 5건
        # - direct_person_count: 김상담 + 박팀장(계층 cascade) = 2명
        # - agency_count: 외주A 1개 + 외주B 1개 (+ 직영 대행사 청구 AgencyPayout 1개) = 3개
        self.assertEqual(res.data['total_contracts'], 5)
        self.assertEqual(res.data['direct_person_count'], 2)
        # agency_count에는 직영 대행사 청구 + 외주A + 외주B 포함
        self.assertEqual(res.data['agency_count'], 3)

        # ── 직영 인력 CommissionPayout 검증 ──
        from sales.models import AgencyPayout
        # 김상담: 2건 × agent_fee 200만 = 400만, clawback 없음
        counselor_payout = period.payouts.get(sales_person=self.counselor)
        self.assertEqual(counselor_payout.contract_count, 2)
        self.assertEqual(counselor_payout.commission_amount, 4000000)
        self.assertEqual(counselor_payout.contract_details.count(), 2)

        # 박팀장: 김상담 2건 × leader_fee 50만 = 100만 (팀장 cascade)
        leader_payout = period.payouts.get(sales_person=self.leader)
        self.assertEqual(leader_payout.contract_count, 2)
        self.assertEqual(leader_payout.commission_amount, 1000000)
        self.assertEqual(leader_payout.contract_details.count(), 2)

        # ── 외주 대행사 AgencyPayout 검증 ──
        payout_oa = AgencyPayout.objects.get(period=period, agency=outsource_a)
        self.assertEqual(payout_oa.contract_count, 2)
        # 외주A: 건당 전체 합산 3,800,000 × 2건 = 7,600,000
        self.assertEqual(payout_oa.agency_fee_sum, 7600000)

        payout_ob = AgencyPayout.objects.get(period=period, agency=outsource_b)
        self.assertEqual(payout_ob.contract_count, 1)
        # 외주B: 건당 전체 합산 3,800,000 × 1건 = 3,800,000
        self.assertEqual(payout_ob.agency_fee_sum, 3800000)

        # ── 이중 정산 방지: generate-payouts 재호출해도 Payout 수가 동일해야 함 ──
        res2 = self.client.post(url)
        self.assertEqual(res2.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res2.data['total_contracts'], 5)
        # 재실행 후 Payout 수 동일 (새로 생성되지 않음)
        self.assertEqual(period.payouts.count(), 2)          # 김상담, 박팀장
        self.assertEqual(period.agency_payouts.count(), 3)   # 직영대행사청구 + 외주A + 외주B

