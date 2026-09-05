from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from company.models import Company
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
