from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
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


