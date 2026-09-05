from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from company.models import Company, Department, Position, Staff, CompanySeal
from work.models.project import IssueProject, Member, Role, Permission

User = get_user_model()


class CompanyDataIsolationAndPermissionTests(APITestCase):
    def setUp(self):
        # 1. 관리자 및 일반 관리자 생성
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='password123'
        )
        self.work_mgr_user = User.objects.create_user(
            username='work_mgr', email='wm@test.com', password='password123',
            work_manager=True
        )

        # 2. 회사 2개 생성
        self.company_1 = Company.objects.create(
            name='(주)갑을건설', tax_number='111-11-11111', ceo='갑대표', org_number='111111-1111111'
        )
        self.company_2 = Company.objects.create(
            name='(주)병정개발', tax_number='222-22-22222', ceo='병대표', org_number='222222-2222222'
        )

        # 3. 본사 워크스페이스(type='1') 2개 생성
        self.hq_ip_1 = IssueProject.objects.create(
            company=self.company_1, name='본사 업무 (갑을)', slug='hq-gabul',
            type='1', creator=self.admin_user
        )
        self.hq_ip_2 = IssueProject.objects.create(
            company=self.company_2, name='본사 업무 (병정)', slug='hq-byeongjeong',
            type='1', creator=self.admin_user
        )

        # 4. 권한 및 역할 생성
        self.perm_read, _ = Permission.objects.get_or_create(
            code='hq.hr_work.read',
            defaults={'name': '인사 조회', 'module': 'hr_work', 'is_for_hq': True}
        )
        self.perm_create, _ = Permission.objects.get_or_create(
            code='hq.hr_work.create',
            defaults={'name': '인사 생성', 'module': 'hr_work', 'is_for_hq': True}
        )
        self.perm_update, _ = Permission.objects.get_or_create(
            code='hq.hr_work.update',
            defaults={'name': '인사 수정', 'module': 'hr_work', 'is_for_hq': True}
        )
        self.perm_delete, _ = Permission.objects.get_or_create(
            code='hq.hr_work.delete',
            defaults={'name': '인사 삭제', 'module': 'hr_work', 'is_for_hq': True}
        )

        self.hr_admin_role = Role.objects.create(
            name='인사관리자', category='ibs_hq_manage', creator=self.admin_user
        )
        self.hr_admin_role.permissions.add(
            self.perm_read, self.perm_create, self.perm_update, self.perm_delete
        )

        self.hr_viewer_role = Role.objects.create(
            name='인사조회자', category='ibs_hq_manage', creator=self.admin_user
        )
        self.hr_viewer_role.permissions.add(self.perm_read)

        # 5. 사용자, Staff 및 본사 멤버 구성
        # 회사 1 관리자
        self.user_1 = User.objects.create_user(
            username='hr_admin_1', email='hr1@test.com', password='password123'
        )
        self.staff_1 = Staff.objects.create(
            company=self.company_1, user=self.user_1, name='홍길동',
            id_number='900101-1234567', personal_phone='010-1111-2222', date_join='2020-01-01'
        )
        mem_1 = Member.objects.create(user=self.user_1, project=self.hq_ip_1)
        mem_1.roles.add(self.hr_admin_role)

        # 회사 1 조회자
        self.user_1_ro = User.objects.create_user(
            username='hr_ro_1', email='ro1@test.com', password='password123'
        )
        self.staff_1_ro = Staff.objects.create(
            company=self.company_1, user=self.user_1_ro, name='김조회',
            id_number='920202-1234567', personal_phone='010-3333-4444', date_join='2021-01-01'
        )
        mem_1_ro = Member.objects.create(user=self.user_1_ro, project=self.hq_ip_1)
        mem_1_ro.roles.add(self.hr_viewer_role)

        # 회사 2 관리자
        self.user_2 = User.objects.create_user(
            username='hr_admin_2', email='hr2@test.com', password='password123'
        )
        self.staff_2 = Staff.objects.create(
            company=self.company_2, user=self.user_2, name='이몽룡',
            id_number='950505-1234567', personal_phone='010-5555-6666', date_join='2022-01-01'
        )
        mem_2 = Member.objects.create(user=self.user_2, project=self.hq_ip_2)
        mem_2.roles.add(self.hr_admin_role)

        # 6. 기본 부서/직위/인장 데이터
        self.dept_1 = Department.objects.create(company=self.company_1, name='인사총무팀')
        self.dept_2 = Department.objects.create(company=self.company_2, name='기획개발팀')

        self.pos_1 = Position.objects.create(company=self.company_1, name='팀장')
        self.pos_2 = Position.objects.create(company=self.company_2, name='부장')

        self.seal_1 = CompanySeal.objects.create(
            company=self.company_1, seal_type='USAGE_SEAL', name='사용인감 1호'
        )
        self.seal_2 = CompanySeal.objects.create(
            company=self.company_2, seal_type='USAGE_SEAL', name='사용인감 2호'
        )

    def test_company_data_isolation_on_list(self):
        """소속 회사의 인사/조직 데이터만 조회되고 타사 데이터는 완벽히 은닉되는지 검증"""
        self.client.force_authenticate(user=self.user_1)

        # 1. 부서 목록 조회
        res = self.client.get('/api/v1/department/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        dept_names = [item['name'] for item in res.data['results']]
        self.assertIn('인사총무팀', dept_names)
        self.assertNotIn('기획개발팀', dept_names)

        # 2. 직원 목록 조회
        res = self.client.get('/api/v1/staff/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        staff_names = [item['name'] for item in res.data['results']]
        self.assertIn('홍길동', staff_names)
        self.assertIn('김조회', staff_names)
        self.assertNotIn('이몽룡', staff_names)

        # 3. 직위 목록 조회
        res = self.client.get('/api/v1/position/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        pos_names = [item['name'] for item in res.data['results']]
        self.assertIn('팀장', pos_names)
        self.assertNotIn('부장', pos_names)

        # 4. 회사 인장 목록 조회
        res = self.client.get('/api/v1/company-seal/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        seal_names = [item['name'] for item in res.data['results']]
        self.assertIn('사용인감 1호', seal_names)
        self.assertNotIn('사용인감 2호', seal_names)

    def test_permission_create_denied_without_hr_create(self):
        """hq.hr_work.create 권한이 없는 사용자의 생성 요청은 403 Forbidden 반환"""
        self.client.force_authenticate(user=self.user_1_ro)

        res = self.client.post('/api/v1/department/', {
            'company': self.company_1.pk,
            'name': '재경팀'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create_allowed_with_hr_create(self):
        """hq.hr_work.create 권한이 있는 사용자의 생성 정상 처리 및 소속 회사 자동 바인딩"""
        self.client.force_authenticate(user=self.user_1)

        res = self.client.post('/api/v1/department/', {
            'company': self.company_1.name,
            'name': '재경팀'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['company'], self.company_1.name)
        self.assertEqual(res.data['name'], '재경팀')

    def test_cross_company_create_denied(self):
        """타사(company_2)로 부서 생성 시도 시 403 Forbidden 차단"""
        self.client.force_authenticate(user=self.user_1)

        res = self.client.post('/api/v1/department/', {
            'company': self.company_2.name,
            'name': '불법부서'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cross_company_object_access_denied(self):
        """타사 데이터 상세 조회, 수정, 삭제 시도 시 격리 차단 (404/403)"""
        self.client.force_authenticate(user=self.user_1)

        # 타사 부서 조회 시도 (Row-Level Security 에 의해 404 반환)
        res_get = self.client.get(f'/api/v1/department/{self.dept_2.pk}/')
        self.assertEqual(res_get.status_code, status.HTTP_404_NOT_FOUND)

        # 타사 부서 수정 시도
        res_patch = self.client.patch(f'/api/v1/department/{self.dept_2.pk}/', {
            'name': '침범수정'
        })
        self.assertEqual(res_patch.status_code, status.HTTP_404_NOT_FOUND)

        # 타사 부서 삭제 시도
        res_del = self.client.delete(f'/api/v1/department/{self.dept_2.pk}/')
        self.assertEqual(res_del.status_code, status.HTTP_404_NOT_FOUND)

    def test_superuser_can_access_all_companies(self):
        """슈퍼유저는 전사 부서 데이터를 모두 조회 가능"""
        self.client.force_authenticate(user=self.admin_user)

        res = self.client.get('/api/v1/department/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        dept_names = [item['name'] for item in res.data['results']]
        self.assertIn('인사총무팀', dept_names)
        self.assertIn('기획개발팀', dept_names)

    def test_work_manager_cannot_access_hq_without_hq_membership(self):
        """work_manager라 하더라도 본사 워크스페이스 멤버 및 HQ 권한이 없으면 본사 부서 접근 차단 (403 Forbidden)"""
        self.client.force_authenticate(user=self.work_mgr_user)

        # 조회 시 본사 권한 부재로 403 차단
        res = self.client.get('/api/v1/department/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # 생성 시 본사 권한 부재로 403 차단
        res_post = self.client.post('/api/v1/department/', {
            'company': self.company_1.name,
            'name': '매니저부서'
        })
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)
