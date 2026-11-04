from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status

from rest_framework.test import APITestCase


from company.models import Company
from contract.models import Contract, OrderGroup
from items.models import UnitType, UnitFloorType, KeyUnit, BuildingUnit, HouseUnit, OptionItem
from project.models import Project
from work.models.project import IssueProject, Member, Role, Permission

User = get_user_model()


class ItemsIsolationAndPermissionTests(APITestCase):
    def setUp(self):
        # 1. 관리자 및 회사 생성
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='password123'
        )
        self.company = Company.objects.create(name='테스트건설')

        # 2. 권한 코드 생성 (contract.update, contract.read)
        self.perm_update, _ = Permission.objects.get_or_create(
            code='contract.update',
            defaults={'name': '계약 수정', 'module': 'contract', 'is_for_project': True}
        )
        self.perm_read, _ = Permission.objects.get_or_create(
            code='contract.read',
            defaults={'name': '계약 조회', 'module': 'contract', 'is_for_project': True}
        )
        self.perm_delete, _ = Permission.objects.get_or_create(
            code='contract.delete',
            defaults={'name': '계약 삭제', 'module': 'contract', 'is_for_project': True}
        )

        # 역할 생성
        self.manager_role = Role.objects.create(
            name='분양관리자', category='ibs_pr_manage', creator=self.admin_user
        )
        self.manager_role.permissions.add(self.perm_update, self.perm_read)

        self.viewer_role = Role.objects.create(
            name='분양조회자', category='ibs_pr_manage', creator=self.admin_user
        )
        self.viewer_role.permissions.add(self.perm_read)

        # 3. 프로젝트 A 생성
        self.ip_a = IssueProject.objects.create(
            company=self.company, name='프로젝트A', slug='project-a',
            type='2', creator=self.admin_user
        )
        self.project_a = Project.objects.create(
            issue_project=self.ip_a, name='프로젝트A', kind='1',
            start_year=2026, monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-03-01', construction_period_months=24
        )

        # 4. 프로젝트 B 생성
        self.ip_b = IssueProject.objects.create(
            company=self.company, name='프로젝트B', slug='project-b',
            type='2', creator=self.admin_user
        )
        self.project_b = Project.objects.create(
            issue_project=self.ip_b, name='프로젝트B', kind='1',
            start_year=2026, monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-03-01', construction_period_months=24
        )

        # 5. 사용자 생성 및 멤버 배정
        self.user_a = User.objects.create_user(
            username='user_a', email='usera@test.com', password='password123'
        )
        mem_a = Member.objects.create(user=self.user_a, project=self.ip_a)
        mem_a.roles.add(self.manager_role)

        self.user_a_readonly = User.objects.create_user(
            username='user_a_ro', email='useraro@test.com', password='password123'
        )
        mem_a_ro = Member.objects.create(user=self.user_a_readonly, project=self.ip_a)
        mem_a_ro.roles.add(self.viewer_role)

        self.user_b = User.objects.create_user(
            username='user_b', email='userb@test.com', password='password123'
        )
        mem_b = Member.objects.create(user=self.user_b, project=self.ip_b)
        mem_b.roles.add(self.manager_role)

        # 6. 기본 유니트 데이터 생성
        self.unit_type_a = UnitType.objects.create(
            project=self.project_a, name='84A', color='#123456', sort='1', num_unit=100
        )
        self.unit_type_b = UnitType.objects.create(
            project=self.project_b, name='59A', color='#654321', sort='1', num_unit=50
        )

        self.floor_type_a = UnitFloorType.objects.create(
            project=self.project_a, sort='1', start_floor=1, end_floor=10, alias_name='저층'
        )

        self.bldg_a = BuildingUnit.objects.create(project=self.project_a, name='101동')
        self.bldg_b = BuildingUnit.objects.create(project=self.project_b, name='201동')

        self.house_a = HouseUnit.objects.create(
            building_unit=self.bldg_a, unit_type=self.unit_type_a,
            floor_type=self.floor_type_a, bldg_line=1, floor_no=1, name='101'
        )
        self.house_b = HouseUnit.objects.create(
            building_unit=self.bldg_b, unit_type=self.unit_type_b,
            bldg_line=1, floor_no=1, name='201'
        )

        self.key_unit_a = KeyUnit.objects.create(
            project=self.project_a, unit_type=self.unit_type_a, unit_code='KU-001'
        )
        self.option_a = OptionItem.objects.create(
            project=self.project_a, opt_name='시스템에어컨', opt_price=5000000
        )

    def test_items_list_isolation_by_project_membership(self):
        """소속 프로젝트의 유니트 데이터만 조회되고 타 프로젝트 데이터는 은닉되는지 검증"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 타입 목록 조회
        res = self.client.get('/api/v1/type/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in res.data['results']]
        self.assertIn('84A', names)
        self.assertNotIn('59A', names)

        # 2. 동수(BuildingUnit) 목록 조회
        res = self.client.get('/api/v1/bldg/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        bldg_names = [item['name'] for item in res.data['results']]
        self.assertIn('101동', bldg_names)
        self.assertNotIn('201동', bldg_names)

        # 3. 호수(HouseUnit) 목록 조회
        res = self.client.get('/api/v1/house-unit/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        house_ids = [item['pk'] for item in res.data['results']]
        self.assertIn(self.house_a.pk, house_ids)
        self.assertNotIn(self.house_b.pk, house_ids)

        # 4. 옵션 품목 조회
        res = self.client.get('/api/v1/option-item/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        opt_names = [item['opt_name'] for item in res.data['results']]
        self.assertIn('시스템에어컨', opt_names)

    def test_items_create_denied_without_contract_update(self):
        """contract.update 권한이 없는 사용자의 유니트 생성 요청은 403 Forbidden 반환"""
        self.client.force_authenticate(user=self.user_a_readonly)

        # 동수 생성 시도
        res = self.client.post('/api/v1/bldg/', {
            'project': self.project_a.pk,
            'name': '102동'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # 호수 생성 시도
        res = self.client.post('/api/v1/house-unit/', {
            'building_unit': self.bldg_a.pk,
            'unit_type': self.unit_type_a.pk,
            'bldg_line': 2,
            'floor_no': 1,
            'name': '102'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_items_create_allowed_with_contract_update(self):
        """contract.update 권한이 있는 사용자의 유니트 생성 정상 처리"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 동수 생성
        res = self.client.post('/api/v1/bldg/', {
            'project': self.project_a.pk,
            'name': '102동'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_bldg_id = res.data['pk']

        # 2. 호수 생성 (building_unit으로부터 프로젝트 역추적 검증)
        res = self.client.post('/api/v1/house-unit/', {
            'building_unit': new_bldg_id,
            'unit_type': self.unit_type_a.pk,
            'bldg_line': 1,
            'floor_no': 1,
            'name': '101'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_items_cross_project_create_denied(self):
        """프로젝트 A 권한자가 타 프로젝트(B)의 유니트 생성 시도 시 403 Forbidden 차단"""
        self.client.force_authenticate(user=self.user_a)

        # 타 프로젝트에 동수 생성 시도
        res = self.client.post('/api/v1/bldg/', {
            'project': self.project_b.pk,
            'name': '202동'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # 타 프로젝트 동수에 호수 생성 시도
        res = self.client.post('/api/v1/house-unit/', {
            'building_unit': self.bldg_b.pk,
            'unit_type': self.unit_type_b.pk,
            'bldg_line': 2,
            'floor_no': 1,
            'name': '202'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_access_all_items(self):
        """슈퍼유저는 전체 프로젝트의 유니트 데이터 조회 및 생성 가능"""
        self.client.force_authenticate(user=self.admin_user)

        res = self.client.get('/api/v1/type/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in res.data['results']]
        self.assertIn('84A', names)
        self.assertIn('59A', names)

        res = self.client.post('/api/v1/bldg/', {
            'project': self.project_b.pk,
            'name': '202동'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_available_house_unit_filtering(self):
        """가용 호수(AvailableHouseUnit) 필터링: unit_type 누락 시에도 미분양 유닛만 조회, contract 지정 시 본인 계약 포함"""
        self.client.force_authenticate(user=self.user_a)

        # house_a: key_unit 미배정 (가용 상태)
        # house_assigned: key_unit 배정 + 계약 체결
        key_unit_assigned = KeyUnit.objects.create(
            project=self.project_a, unit_type=self.unit_type_a, unit_code='KU-ASGN'
        )
        house_assigned = HouseUnit.objects.create(
            building_unit=self.bldg_a, unit_type=self.unit_type_a,
            bldg_line=1, floor_no=2, name='102', key_unit=key_unit_assigned
        )
        order_group = OrderGroup.objects.create(
            project=self.project_a, order_number=1, name='일반분양'
        )
        contract = Contract.objects.create(
            project=self.project_a, order_group=order_group, serial_number='CONT-TEST-001',
            key_unit=key_unit_assigned, creator=self.admin_user
        )

        # 1. unit_type 없이 project만 전달했을 때 -> 미배정 유닛(house_a)만 반환되어야 함
        res = self.client.get(f'/api/v1/available-house-unit/?project={self.project_a.pk}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        pks = [item['pk'] for item in res.data['results']]
        self.assertIn(self.house_a.pk, pks)
        self.assertNotIn(house_assigned.pk, pks)

        # 2. contract를 함께 전달했을 때 -> 미배정 유닛(house_a) + 해당 계약 배정 유닛(house_assigned) 모두 반환되어야 함
        res_with_cont = self.client.get(
            f'/api/v1/available-house-unit/?project={self.project_a.pk}&contract={contract.pk}'
        )
        self.assertEqual(res_with_cont.status_code, status.HTTP_200_OK)
        cont_pks = [item['pk'] for item in res_with_cont.data['results']]
        self.assertIn(self.house_a.pk, cont_pks)
        self.assertIn(house_assigned.pk, cont_pks)

    def test_house_unit_patch_unit_code_fallback(self):
        """HouseUnit에 unit_code만 전달하여 PATCH할 때 KeyError 없이 안전하게 KeyUnit이 바인딩되는지 검증"""
        self.client.force_authenticate(user=self.user_a)

        res = self.client.patch(f'/api/v1/house-unit/{self.house_a.pk}/', {
            'unit_code': 'KU-P01'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.house_a.refresh_from_db()
        self.assertIsNotNone(self.house_a.key_unit)
        self.assertEqual(self.house_a.key_unit.unit_code, 'KU-P01')

    def test_house_unit_key_unit_already_bound_raises_validation_error(self):
        """이미 타 세대에 배정된 KeyUnit을 다른 세대에 지정 시 500이 아닌 400 ValidationError 반환"""
        self.client.force_authenticate(user=self.user_a)

        # 1. house_a에 KU-DUP1 배정
        self.client.patch(f'/api/v1/house-unit/{self.house_a.pk}/', {
            'unit_code': 'KU-DUP1'
        })
        self.house_a.refresh_from_db()
        self.assertEqual(self.house_a.key_unit.unit_code, 'KU-DUP1')

        # 2. 신규 세대 생성 시 동일한 KU-DUP1 지정 시도 -> 400 Bad Request
        res = self.client.post('/api/v1/house-unit/', {
            'building_unit': self.bldg_a.pk,
            'unit_type': self.unit_type_a.pk,
            'bldg_line': 2,
            'floor_no': 2,
            'name': '103',
            'unit_code': 'KU-DUP1'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unit_code', res.data)

    def test_unit_floor_type_floor_range_validation(self):
        """시작 층이 종료 층보다 큰 경우 400 ValidationError 발생 검증"""
        self.client.force_authenticate(user=self.user_a)

        # 잘못된 층범위 (시작 10층 > 종료 5층)
        res = self.client.post('/api/v1/floor/', {
            'project': self.project_a.pk,
            'sort': '1',
            'start_floor': 10,
            'end_floor': 5,
            'alias_name': '역전층'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_floor', res.data)

    def test_option_item_patch_price_validation(self):
        """옵션 품목 PATCH 수정 시에도 계약금+잔금 합계 정합성 검증이 작동하는지 확인"""
        self.client.force_authenticate(user=self.user_a)

        option = OptionItem.objects.create(
            project=self.project_a,
            opt_name='빌트인 냉장고',
            opt_price=3000000,
            opt_deposit=300000,
            opt_balance=2700000
        )

        # 잘못된 계약금으로 PATCH (1,000,000 + 2,700,000 != 3,000,000)
        res_fail = self.client.patch(f'/api/v1/option-item/{option.pk}/', {
            'opt_deposit': 1000000
        })
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('opt_deposit', res_fail.data)

        # 올바른 잔금과 함께 PATCH (1,000,000 + 2,000,000 == 3,000,000)
        res_ok = self.client.patch(f'/api/v1/option-item/{option.pk}/', {
            'opt_deposit': 1000000,
            'opt_balance': 2000000
        })
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        option.refresh_from_db()
        self.assertEqual(option.opt_deposit, 1000000)
        self.assertEqual(option.opt_balance, 2000000)

    def test_house_unit_and_key_unit_search(self):
        """호수(name), 동(building_unit__name), 유닛코드(unit_code) 검색 검증"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 호수 검색
        res_house = self.client.get('/api/v1/house-unit/?search=101')
        self.assertEqual(res_house.status_code, status.HTTP_200_OK)
        pks = [item['pk'] for item in res_house.data['results']]
        self.assertIn(self.house_a.pk, pks)

        # 2. 동 이름 검색
        res_bldg = self.client.get('/api/v1/house-unit/?search=101동')
        self.assertEqual(res_bldg.status_code, status.HTTP_200_OK)
        pks = [item['pk'] for item in res_bldg.data['results']]
        self.assertIn(self.house_a.pk, pks)

        # 3. 유닛 코드 검색
        res_ku = self.client.get('/api/v1/key-unit/?search=KU-001')
        self.assertEqual(res_ku.status_code, status.HTTP_200_OK)
        ku_pks = [item['pk'] for item in res_ku.data['results']]
        self.assertIn(self.key_unit_a.pk, ku_pks)

    def test_key_unit_unique_together_constraint(self):
        """[T-1 / C-1] 동일 프로젝트 내 KeyUnit의 unit_code 중복 생성 시 IntegrityError 차단 검증"""
        # 1. 동일 프로젝트(project_a)에 이미 존재하는 unit_code('KU-001')로 생성 시도 -> IntegrityError 발생
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                KeyUnit.objects.create(
                    project=self.project_a,
                    unit_type=self.unit_type_a,
                    unit_code='KU-001'
                )


        # 2. 서로 다른 프로젝트(project_b)에는 동일한 unit_code('KU-001') 생성이 정상 허용됨
        ku_other_proj = KeyUnit.objects.create(
            project=self.project_b,
            unit_type=self.unit_type_b,
            unit_code='KU-001'
        )
        self.assertIsNotNone(ku_other_proj.pk)
        self.assertEqual(ku_other_proj.unit_code, 'KU-001')
        self.assertEqual(ku_other_proj.project, self.project_b)

    def test_member_without_contract_read_blocked_by_rls(self):
        """[RLS] 워크스페이스 멤버이지만 contract.read 권한이 없는 사용자는 items 데이터 접근 시 빈 목록(은닉) 반환"""
        # contract.read 권한이 없는 일반 워크스페이스 역할 생성
        workspace_role = Role.objects.create(
            name='일반협력업체', category='work_space', creator=self.admin_user
        )
        no_perm_user = User.objects.create_user(
            username='user_no_perm', email='noperm@test.com', password='password123'
        )
        mem = Member.objects.create(user=no_perm_user, project=self.ip_a)
        mem.roles.add(workspace_role)

        self.client.force_authenticate(user=no_perm_user)

        # 1. 타입 목록 조회 -> 0건
        res_type = self.client.get('/api/v1/type/')
        self.assertEqual(res_type.status_code, status.HTTP_200_OK)
        self.assertEqual(res_type.data['count'], 0)

        # 2. 동수 목록 조회 -> 0건
        res_bldg = self.client.get('/api/v1/bldg/')
        self.assertEqual(res_bldg.status_code, status.HTTP_200_OK)
        self.assertEqual(res_bldg.data['count'], 0)

        # 3. 호수 목록 조회 -> 0건
        res_house = self.client.get('/api/v1/house-unit/')
        self.assertEqual(res_house.status_code, status.HTTP_200_OK)
        self.assertEqual(res_house.data['count'], 0)

        # 4. 전체 호수(계약자 및 공급가격 정보 포함) 배치도 조회 -> 0건
        res_all_house = self.client.get('/api/v1/all-house-unit/')
        self.assertEqual(res_all_house.status_code, status.HTTP_200_OK)
        self.assertEqual(res_all_house.data['count'], 0)

        # 5. 옵션 품목 조회 -> 0건
        res_opt = self.client.get('/api/v1/option-item/')
        self.assertEqual(res_opt.status_code, status.HTTP_200_OK)
        self.assertEqual(res_opt.data['count'], 0)

    def test_cross_project_house_unit_validation_error(self):
        """[데이터 무결성] HouseUnit의 동수, 타입, 층타입, KeyUnit 간 프로젝트 불일치 및 타입 불일치 차단 검증"""
        # 1. ORM 레벨: 동수(project_a)에 타 프로젝트 타입(unit_type_b) 지정 시 ValidationError 발생
        with self.assertRaises(ValidationError):
            HouseUnit.objects.create(
                building_unit=self.bldg_a,
                unit_type=self.unit_type_b,
                bldg_line=1, floor_no=1, name='999'
            )

        # 2. API 레벨: 동수(bldg_a)에 unit_type_b 전달하여 POST 시 400 Bad Request
        self.client.force_authenticate(user=self.admin_user)
        res_api = self.client.post('/api/v1/house-unit/', {
            'building_unit': self.bldg_a.pk,
            'unit_type': self.unit_type_b.pk,
            'bldg_line': 1,
            'floor_no': 1,
            'name': '999'
        })
        self.assertEqual(res_api.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unit_type', res_api.data)

        # 3. ORM 레벨: 동수(project_a)에 타 프로젝트 층범위(floor_type_b) 지정 시 ValidationError 발생
        floor_type_b = UnitFloorType.objects.create(
            project=self.project_b, sort='1', start_floor=1, end_floor=10, alias_name='B저층'
        )
        with self.assertRaises(ValidationError):
            HouseUnit.objects.create(
                building_unit=self.bldg_a,
                unit_type=self.unit_type_a,
                floor_type=floor_type_b,
                bldg_line=1, floor_no=1, name='998'
            )

        # 4. ORM 레벨: 동수(project_a)에 타 프로젝트 KeyUnit(key_unit_b) 지정 시 ValidationError 발생
        key_unit_b = KeyUnit.objects.create(
            project=self.project_b, unit_type=self.unit_type_b, unit_code='KU-B01'
        )
        with self.assertRaises(ValidationError):
            HouseUnit.objects.create(
                building_unit=self.bldg_a,
                unit_type=self.unit_type_a,
                key_unit=key_unit_b,
                bldg_line=1, floor_no=1, name='997'
            )

        # 5. ORM 레벨: 동일 프로젝트이지만 호수의 타입(unit_type_a)과 KeyUnit의 타입이 불일치할 때 ValidationError 발생
        unit_type_a2 = UnitType.objects.create(
            project=self.project_a, name='104A', color='#333333', sort='1', num_unit=30
        )
        key_unit_a2 = KeyUnit.objects.create(
            project=self.project_a, unit_type=unit_type_a2, unit_code='KU-A02'
        )
        with self.assertRaises(ValidationError):
            HouseUnit.objects.create(
                building_unit=self.bldg_a,
                unit_type=self.unit_type_a,  # 84A
                key_unit=key_unit_a2,        # 104A
                bldg_line=1, floor_no=1, name='996'
            )

    def test_cross_project_key_unit_validation_error(self):
        """[데이터 무결성] KeyUnit의 프로젝트와 unit_type의 프로젝트 불일치 차단 검증"""
        # 1. ORM 레벨: 프로젝트 A의 KeyUnit에 프로젝트 B의 unit_type 지정 시 ValidationError 발생
        with self.assertRaises(ValidationError):
            KeyUnit.objects.create(
                project=self.project_a,
                unit_type=self.unit_type_b,
                unit_code='KU-ERR'
            )

        # 2. API 레벨: 프로젝트 A의 KeyUnit 생성 시 unit_type_b 지정 요청 시 400 Bad Request
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post('/api/v1/key-unit/', {
            'project': self.project_a.pk,
            'unit_type': self.unit_type_b.pk,
            'unit_code': 'KU-ERR'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unit_type', res.data)

    def test_option_item_clean_price_validation(self):
        """[데이터 무결성] OptionItem 모델 레벨의 계약금+잔금 합계 정합성 검증 확인"""
        # 1. 계약금 + 잔금 != 옵션가격 인 경우 ValidationError 발생
        with self.assertRaises(ValidationError):
            OptionItem.objects.create(
                project=self.project_a,
                opt_name='시스템에어컨 추가',
                opt_price=2000000,
                opt_deposit=200000,
                opt_balance=1500000  # 합계 1,700,000 != 2,000,000
            )

        # 2. 계약금 + 잔금 == 옵션가격 인 경우 정상 생성
        valid_opt = OptionItem.objects.create(
            project=self.project_a,
            opt_name='시스템에어컨 추가',
            opt_price=2000000,
            opt_deposit=200000,
            opt_balance=1800000
        )
        self.assertIsNotNone(valid_opt.pk)
        self.assertEqual(valid_opt.opt_price, 2000000)

    def test_house_unit_direct_key_unit_already_bound_validation(self):
        """[H-1] key_unit PK 직접 전달 시 이미 타 세대에 바인딩된 경우 500이 아닌 400 ValidationError 반환"""
        self.client.force_authenticate(user=self.user_a)

        # 1. house_a에 key_unit_a 배정
        self.house_a.key_unit = self.key_unit_a
        self.house_a.save()

        # 2. 신규 세대 생성 시 key_unit_a를 직접 key_unit 필드로 전달 -> 400 Bad Request
        res = self.client.post('/api/v1/house-unit/', {
            'building_unit': self.bldg_a.pk,
            'unit_type': self.unit_type_a.pk,
            'bldg_line': 2,
            'floor_no': 3,
            'name': '105',
            'key_unit': self.key_unit_a.pk
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('key_unit', res.data)

    def test_house_unit_resolve_key_unit_type_mismatch(self):
        """[H-2] unit_code가 이미 동일 프로젝트 내 다른 unit_type으로 존재하는 경우 500이 아닌 400 ValidationError 반환"""
        self.client.force_authenticate(user=self.user_a)

        # 1. unit_type_a2 생성 및 해당 타입으로 KU-MIS 유닛코드 등록
        unit_type_a2 = UnitType.objects.create(
            project=self.project_a, name='104B', color='#777777', sort='1', num_unit=20
        )
        KeyUnit.objects.create(
            project=self.project_a, unit_type=unit_type_a2, unit_code='KU-MIS'
        )

        # 2. unit_type_a로 세대 생성 시 동일한 KU-MIS를 unit_code로 전달 -> 400 Bad Request
        res = self.client.post('/api/v1/house-unit/', {
            'building_unit': self.bldg_a.pk,
            'unit_type': self.unit_type_a.pk,
            'bldg_line': 1,
            'floor_no': 5,
            'name': '106',
            'unit_code': 'KU-MIS'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unit_code', res.data)

    def test_option_item_cross_project_types_validation(self):
        """[H-3] OptionItem에 타 프로젝트의 UnitType을 ManyToMany로 배정 시 400 ValidationError 차단"""
        self.client.force_authenticate(user=self.user_a)

        # project_a의 옵션 품목에 project_b의 unit_type_b 배정 시도 -> 400 Bad Request
        res = self.client.post('/api/v1/option-item/', {
            'project': self.project_a.pk,
            'opt_name': '주방 엔지니어드스톤',
            'opt_price': 1500000,
            'types': [self.unit_type_b.pk]
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('types', res.data)

    def test_unit_floor_type_model_clean_validation(self):
        """[M-1] UnitFloorType 모델 레벨 clean()에서 시작 층 > 종료 층 시 ValidationError 발생 검증"""
        floor = UnitFloorType(
            project=self.project_a, sort='1', start_floor=15, end_floor=10, alias_name='역전층'
        )
        with self.assertRaises(ValidationError):
            floor.save()

    def test_available_house_unit_viewset_readonly(self):
        """[L-1] AvailableHouseUnitViewSet은 ReadOnly이므로 POST 등 쓰기 요청 시 405 Method Not Allowed 반환"""
        self.client.force_authenticate(user=self.user_a)

        res = self.client.post('/api/v1/available-house-unit/', {
            'building_unit': self.bldg_a.pk,
            'unit_type': self.unit_type_a.pk,
            'bldg_line': 1,
            'floor_no': 1,
            'name': '909'
        })
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_contracted_house_unit_cannot_change_key_unit_or_unit_code(self):
        """[P0-보안] 계약이 체결된 세대의 unit_code 교체 및 key_unit/unit_type/building_unit 변조 차단 (이중분양 방지)"""
        self.client.force_authenticate(user=self.user_a)

        # 1. key_unit_a와 house_a 연결 및 계약 생성
        self.house_a.key_unit = self.key_unit_a
        self.house_a.save()

        order_group = OrderGroup.objects.create(
            project=self.project_a, order_number=1, name='일반분양'
        )
        Contract.objects.create(
            project=self.project_a, order_group=order_group, serial_number='CONT-P0-001',
            key_unit=self.key_unit_a, creator=self.admin_user
        )

        # 2. 계약된 세대에 새로운 unit_code 전달하여 PATCH 시도 -> 400 Bad Request
        res_code = self.client.patch(f'/api/v1/house-unit/{self.house_a.pk}/', {
            'unit_code': 'KU-NEW'
        })
        self.assertEqual(res_code.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unit_code', res_code.data)

        # 3. 계약된 세대에 다른 key_unit PK 전달하여 PATCH 시도 -> 400 Bad Request
        other_key_unit = KeyUnit.objects.create(
            project=self.project_a, unit_type=self.unit_type_a, unit_code='KU-OTHER'
        )
        res_ku = self.client.patch(f'/api/v1/house-unit/{self.house_a.pk}/', {
            'key_unit': other_key_unit.pk
        })
        self.assertEqual(res_ku.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('key_unit', res_ku.data)

        # 4. 계약된 세대의 unit_type 변경 시도 -> 400 Bad Request
        unit_type_a2 = UnitType.objects.create(
            project=self.project_a, name='74A', color='#555555', sort='1', num_unit=50
        )
        res_type = self.client.patch(f'/api/v1/house-unit/{self.house_a.pk}/', {
            'unit_type': unit_type_a2.pk
        })
        self.assertEqual(res_type.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unit_type', res_type.data)

    def test_contracted_key_unit_and_house_unit_cannot_be_deleted(self):
        """[P0-보안] 계약이 체결된 KeyUnit 및 HouseUnit의 무단 삭제(DELETE) 차단 검증"""
        self.client.force_authenticate(user=self.admin_user)

        # 1. 계약 연결
        self.house_a.key_unit = self.key_unit_a
        self.house_a.save()

        order_group = OrderGroup.objects.create(
            project=self.project_a, order_number=1, name='일반분양'
        )
        contract = Contract.objects.create(
            project=self.project_a, order_group=order_group, serial_number='CONT-DEL-001',
            key_unit=self.key_unit_a, creator=self.admin_user
        )

        # 2. 계약된 KeyUnit 삭제 시도 -> 400 Bad Request
        res_ku_del = self.client.delete(f'/api/v1/key-unit/{self.key_unit_a.pk}/')
        self.assertEqual(res_ku_del.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(KeyUnit.objects.filter(pk=self.key_unit_a.pk).exists())
        contract.refresh_from_db()
        self.assertIsNotNone(contract.key_unit)

        # 3. 계약된 HouseUnit 삭제 시도 -> 400 Bad Request
        res_hu_del = self.client.delete(f'/api/v1/house-unit/{self.house_a.pk}/')
        self.assertEqual(res_hu_del.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(HouseUnit.objects.filter(pk=self.house_a.pk).exists())

    def test_destroy_requires_contract_delete_permission(self):
        """[P1-권한] 삭제(destroy) 요청 시 contract.delete 권한이 필요하며, contract.update만 있는 유저는 403 차단"""
        # uncontracted_house 생성 (floor_no=9, bldg_line=9)
        uncontracted_house = HouseUnit.objects.create(
            building_unit=self.bldg_a, unit_type=self.unit_type_a,
            bldg_line=9, floor_no=9, name='909'
        )

        # user_a는 contract.update, contract.read만 보유 (contract.delete 없음) -> 403 Forbidden
        self.client.force_authenticate(user=self.user_a)
        res_denied = self.client.delete(f'/api/v1/house-unit/{uncontracted_house.pk}/')
        self.assertEqual(res_denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(HouseUnit.objects.filter(pk=uncontracted_house.pk).exists())

        # contract.delete 권한 부여 후 삭제 성공 -> 204 No Content
        self.manager_role.permissions.add(self.perm_delete)
        res_allowed = self.client.delete(f'/api/v1/house-unit/{uncontracted_house.pk}/')
        self.assertEqual(res_allowed.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(HouseUnit.objects.filter(pk=uncontracted_house.pk).exists())

    def test_duplicates_and_area_validation(self):
        """[P1/P2] 동일 프로젝트/동 내 중복(BuildingUnit, UnitType, HouseUnit) 방어 및 면적 정합성 검증"""
        self.client.force_authenticate(user=self.admin_user)

        # 1. 동일 프로젝트 내 동 이름 중복 등록 시 400
        res_dup_bldg = self.client.post('/api/v1/bldg/', {
            'project': self.project_a.pk,
            'name': '101동'  # 이미 setUp에 존재
        })
        self.assertEqual(res_dup_bldg.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res_dup_bldg.data)

        # 2. 동일 프로젝트 내 타입 명칭 중복 등록 시 400
        res_dup_type = self.client.post('/api/v1/type/', {
            'project': self.project_a.pk,
            'name': '84A',  # 이미 setUp에 존재
            'color': '#111111',
            'sort': '1',
            'num_unit': 10
        })
        self.assertEqual(res_dup_type.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res_dup_type.data)

        # 3. 면적 역전 (actual_area > supply_area) 시 400
        res_area = self.client.post('/api/v1/type/', {
            'project': self.project_a.pk,
            'name': '84C',
            'color': '#222222',
            'sort': '1',
            'num_unit': 10,
            'actual_area': 84.5,
            'supply_area': 59.5
        })
        self.assertEqual(res_area.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('supply_area', res_area.data)

        # 4. 동일 동 내 동일 라인/층 중복 등록 시 400
        res_dup_hu_line = self.client.post('/api/v1/house-unit/', {
            'building_unit': self.bldg_a.pk,
            'unit_type': self.unit_type_a.pk,
            'bldg_line': 1,
            'floor_no': 1,  # 이미 house_a(1동 1층 1라인)가 존재
            'name': '101N'
        })
        self.assertEqual(res_dup_hu_line.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('bldg_line', res_dup_hu_line.data)

        # 5. 동일 동 내 동일 호수명 중복 등록 시 400
        res_dup_hu_name = self.client.post('/api/v1/house-unit/', {
            'building_unit': self.bldg_a.pk,
            'unit_type': self.unit_type_a.pk,
            'bldg_line': 3,
            'floor_no': 3,
            'name': '101'  # 이미 house_a(101호)가 존재
        })
        self.assertEqual(res_dup_hu_name.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res_dup_hu_name.data)

    def test_option_item_auto_balance_and_deposit_calculation(self):
        """[P2] OptionItem 등록 시 잔금 미입력 시 옵션가 - 계약금 자동 계산 검증"""
        self.client.force_authenticate(user=self.admin_user)

        res = self.client.post('/api/v1/option-item/', {
            'project': self.project_a.pk,
            'opt_name': '발코니 확장',
            'opt_price': 10000000,
            'opt_deposit': 1000000,
            'types': [self.unit_type_a.pk]
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['opt_balance'], 9000000)



class ItemsAdminQueryOptimizationTest(TestCase):
    """[M-2, M-4] KeyUnitAdmin, UnitTypeAdmin, HouseUnitAdmin 등 get_queryset 최적화 및 N+1 방어 검증"""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_item_opt', email='admin_opt@test.com', password='password123'
        )
        self.company = Company.objects.create(name='옵티건설')
        self.ip = IssueProject.objects.create(
            company=self.company, name='옵티프로젝트', slug='opti-proj', type='2', creator=self.admin
        )
        self.project = Project.objects.create(
            issue_project=self.ip, name='옵티프로젝트', kind='1',
            start_year=2026, monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-03-01', construction_period_months=24
        )
        self.unit_type = UnitType.objects.create(
            project=self.project, name='84A', color='#000000', sort='1', num_unit=50
        )
        self.floor_type = UnitFloorType.objects.create(
            project=self.project, sort='1', start_floor=1, end_floor=5, alias_name='1-5층'
        )
        self.bldg = BuildingUnit.objects.create(project=self.project, name='101동')
        self.key_unit = KeyUnit.objects.create(
            project=self.project, unit_type=self.unit_type, unit_code='KU-OPT'
        )
        self.house = HouseUnit.objects.create(
            building_unit=self.bldg, unit_type=self.unit_type, floor_type=self.floor_type,
            bldg_line=1, floor_no=1, name='101', key_unit=self.key_unit
        )
        self.order_group = OrderGroup.objects.create(
            project=self.project, order_number=1, name='일반분양'
        )
        self.contract = Contract.objects.create(
            project=self.project, order_group=self.order_group, serial_number='CONT-OPT-001',
            key_unit=self.key_unit, creator=self.admin
        )
        self.option = OptionItem.objects.create(
            project=self.project, opt_name='빌트인 오븐', opt_price=800000
        )
        self.option.types.add(self.unit_type)

    def test_items_admin_query_optimization(self):
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from items.admin import (
            UnitTypeAdmin, UnitFloorTypeAdmin, KeyUnitAdmin,
            BuildingUnitAdmin, HouseUnitAdmin, OptionItemAdmin
        )

        factory = RequestFactory()
        req = factory.get('/admin/')
        req.user = self.admin
        site = AdminSite()

        # 1. KeyUnitAdmin - project, unit_type, contract pre-fetched
        ku_admin = KeyUnitAdmin(KeyUnit, site)
        ku_qs = list(ku_admin.get_queryset(req).filter(pk=self.key_unit.pk))
        self.assertEqual(len(ku_qs), 1)
        with self.assertNumQueries(0):
            item = ku_qs[0]
            _ = item.project.name
            _ = item.unit_type.name
            _ = item.contract.serial_number

        # 2. HouseUnitAdmin - building_unit__project, unit_type, building_unit, floor_type, key_unit
        hu_admin = HouseUnitAdmin(HouseUnit, site)
        hu_qs = list(hu_admin.get_queryset(req).filter(pk=self.house.pk))
        self.assertEqual(len(hu_qs), 1)
        with self.assertNumQueries(0):
            item = hu_qs[0]
            _ = item.building_unit.project.name
            _ = item.unit_type.name
            _ = item.building_unit.name
            _ = item.floor_type.alias_name
            _ = item.key_unit.unit_code

        # 3. UnitTypeAdmin
        ut_admin = UnitTypeAdmin(UnitType, site)
        ut_qs = list(ut_admin.get_queryset(req).filter(pk=self.unit_type.pk))
        self.assertEqual(len(ut_qs), 1)
        with self.assertNumQueries(0):
            item = ut_qs[0]
            _ = item.project.name

        # 4. BuildingUnitAdmin
        bu_admin = BuildingUnitAdmin(BuildingUnit, site)
        bu_qs = list(bu_admin.get_queryset(req).filter(pk=self.bldg.pk))
        self.assertEqual(len(bu_qs), 1)
        with self.assertNumQueries(0):
            item = bu_qs[0]
            _ = item.project.name

        # 5. OptionItemAdmin
        oi_admin = OptionItemAdmin(OptionItem, site)
        oi_qs = list(oi_admin.get_queryset(req).filter(pk=self.option.pk))
        self.assertEqual(len(oi_qs), 1)
        with self.assertNumQueries(0):
            item = oi_qs[0]
            _ = item.project.name
            _ = list(item.types.all())



