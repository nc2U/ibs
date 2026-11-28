from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from company.models import Company, Department, Position, Staff, CompanySeal, Executive, ExecutiveRank
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

    def test_staff_id_number_masking_for_ordinary_users(self):
        """[T-6 / H-2] 일반 직원이 타 직원의 인사 정보 조회 시 주민등록번호 뒷자리가 마스킹(900101-*******)되고 본인/관리자는 원본 반환 검증"""
        # 1. 일반 조회자(user_1_ro)가 타인(staff_1)의 Staff 정보를 조회 시 마스킹 검증
        self.client.force_authenticate(user=self.user_1_ro)
        res_other = self.client.get(f'/api/v1/staff/{self.staff_1.pk}/')
        self.assertEqual(res_other.status_code, status.HTTP_200_OK)
        self.assertEqual(res_other.data['id_number'], '900101-*******')

        # 2. 본인(user_1)이 본인(staff_1)의 Staff 정보를 조회 시 원본 노출 검증
        self.client.force_authenticate(user=self.user_1)
        res_self = self.client.get(f'/api/v1/staff/{self.staff_1.pk}/')
        self.assertEqual(res_self.status_code, status.HTTP_200_OK)
        self.assertEqual(res_self.data['id_number'], '900101-1234567')

        # 3. 슈퍼유저(admin_user)가 조회 시 원본 노출 검증
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get(f'/api/v1/staff/{self.staff_1.pk}/')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(res_admin.data['id_number'], '900101-1234567')




class ExecutiveModelTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name='테스트회사')
        self.rank = ExecutiveRank.objects.create(company=self.company, code='E1', name='사장', sort_order=1)
        self.user = User.objects.create_user(username='testuser', password='password')
        self.staff = Staff.objects.create(company=self.company, user=self.user, name='홍길동', date_join='2020-01-01')

    def test_executive_with_staff_is_valid(self):
        exec = Executive(company=self.company, staff=self.staff, rank=self.rank)
        exec.full_clean()
        exec.save()
        self.assertEqual(exec.full_name, '홍길동')

    def test_executive_without_staff_with_name_is_valid(self):
        exec = Executive(company=self.company, name='외부이사', rank=self.rank)
        exec.full_clean()
        exec.save()
        self.assertEqual(exec.full_name, '외부이사')

    def test_executive_without_staff_without_name_is_invalid(self):
        exec = Executive(company=self.company, rank=self.rank)
        with self.assertRaises(ValidationError):
            exec.full_clean()

    def test_str_representation(self):
        exec_staff = Executive.objects.create(company=self.company, staff=self.staff, rank=self.rank)
        self.assertEqual(str(exec_staff), '홍길동 사장 (사내이사)')

        exec_name = Executive.objects.create(company=self.company, name='외부인', rank=self.rank)
        self.assertEqual(str(exec_name), '외부인 사장 (사내이사)')


class CompanyBugFixRegressionTests(APITestCase):
    def setUp(self):
        from decimal import Decimal
        self.company = Company.objects.create(name='(주)아이비에스건설', tax_number='123-45-67890', ceo='대표자')
        self.admin = User.objects.create_superuser(username='superadmin', email='superadmin@test.com', password='password123')
        self.user = User.objects.create_user(username='normaluser', email='normaluser@test.com', password='password123')
        self.staff = Staff.objects.create(
            company=self.company, user=self.user, name='테스트직원',
            id_number='880808-1234567', personal_phone='010-9999-8888', date_join='2020-01-01'
        )
        self.rank = ExecutiveRank.objects.create(company=self.company, code='E1', name='전무', sort_order=2)
        self.executive = Executive.objects.create(
            company=self.company, staff=self.staff, rank=self.rank,
            executive_type='inside', represent_type='none'
        )

    def test_executive_serializer_type_desc_no_error(self):
        """Fix 1: ExecutiveSerializer가 executive_type_desc를 정상 반환하는지 검증 (오타 재발 방지)"""
        from apiV1.serializers.company import ExecutiveSerializer
        serializer = ExecutiveSerializer(self.executive)
        self.assertEqual(serializer.data['executive_type_desc'], '사내이사')
        self.assertEqual(serializer.data['full_name'], '테스트직원')

    def test_department_circular_reference_prevention(self):
        """Fix 8: Department의 순환 참조 방어 검증"""
        d1 = Department.objects.create(company=self.company, name='본부')
        d2 = Department.objects.create(company=self.company, name='팀', upper_depart=d1)
        self.assertEqual(d1.level, 1)
        self.assertEqual(d2.level, 2)

        # 1) 자기 자신을 상위 부서로 지정 시 ValidationError
        d1.upper_depart = d1
        with self.assertRaises(ValidationError):
            d1.clean()

        # 2) 순환 참조 (d1의 상위를 d2로 지정) 시 ValidationError
        d1.upper_depart = d2
        with self.assertRaises(ValidationError):
            d1.clean()

    def test_staff_leave_quota_used_days_aggregate(self):
        """Fix 7: StaffLeaveQuota.used_days DB aggregate 계산 검증"""
        from decimal import Decimal
        from company.models import StaffLeaveQuota, StaffLeaveUsage
        quota = StaffLeaveQuota.objects.create(
            company=self.company, staff=self.staff, year=2026,
            granted_days=Decimal('15.00'), valid_start='2026-01-01', valid_end='2026-12-31'
        )
        # 휴가 사용 등록
        StaffLeaveUsage.objects.create(
            company=self.company, staff=self.staff, start_date='2026-03-01', end_date='2026-03-01',
            deduction_days=Decimal('1.00'), is_cancelled=False
        )
        StaffLeaveUsage.objects.create(
            company=self.company, staff=self.staff, start_date='2026-04-01', end_date='2026-04-01',
            deduction_days=Decimal('0.50'), is_cancelled=False
        )
        # 취소된 휴가는 제외되어야 함
        StaffLeaveUsage.objects.create(
            company=self.company, staff=self.staff, start_date='2026-05-01', end_date='2026-05-01',
            deduction_days=Decimal('1.00'), is_cancelled=True
        )

        self.assertEqual(quota.used_days, Decimal('1.50'))
        self.assertEqual(quota.remaining_days, Decimal('13.50'))

    def test_excel_export_views_no_500_error(self):
        """Fix 2, 3, 4: ExportExecutives, ExportStaffs, ExportStaffAttendanceStatus 엑셀 내보내기 뷰 200 검증"""
        from django.test import RequestFactory
        from company.exports.excel import ExportExecutives, ExportStaffs, ExportStaffAttendanceStatus
        factory = RequestFactory()

        # 1. ExportExecutives
        req_exec = factory.get(f'/company/export/executives/?company={self.company.pk}')
        res_exec = ExportExecutives().get(req_exec)
        self.assertEqual(res_exec.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', res_exec['Content-Type'])

        # 2. ExportStaffs
        req_staff = factory.get(f'/company/export/staffs/?company={self.company.pk}')
        res_staff = ExportStaffs().get(req_staff)
        self.assertEqual(res_staff.status_code, 200)

        # 3. ExportStaffAttendanceStatus
        req_att = factory.get(f'/company/export/attendance/?company={self.company.pk}&year=2026')
        res_att = ExportStaffAttendanceStatus().get(req_att)
        self.assertEqual(res_att.status_code, 200)

    def test_company_seal_terminology(self):
        """CompanySeal의 도메인 용어 체계 준수 검증 ('현장' 배제 및 '부서/사업소 직인' 확인)"""
        seal = CompanySeal.objects.create(
            company=self.company,
            seal_type='DEPT_SEAL',
            name='개발사업소 직인',
            custody_type='internal',
        )
        self.assertEqual(seal.get_seal_type_display(), '부서/사업소 직인')
        self.assertEqual(seal.get_custody_type_display(), '사내 보관 (본사/사업소)')

    def test_staff_admin_and_prefetch_cache_query_optimization(self):
        """StaffAdmin 렌더링 및 Staff.primary_assignment prefetch 캐시 활용 시 추가 쿼리 0건 검증"""
        from django.contrib.admin.sites import AdminSite
        from company.admin import StaffAdmin
        from company.models import Department, DutyTitle, StaffAssignment

        dept = Department.objects.create(company=self.company, name='경영기획팀')
        duty = DutyTitle.objects.create(company=self.company, code='D1', name='팀장')
        StaffAssignment.objects.create(
            company=self.company, staff=self.staff, department=dept, duty=duty, is_primary=True
        )

        admin = StaffAdmin(Staff, AdminSite())
        from django.test import RequestFactory
        request = RequestFactory().get('/admin/company/staff/')
        request.user = self.admin

        qs = admin.get_queryset(request)
        staff_list = list(qs)
        self.assertEqual(len(staff_list), 1)

        # 쿼리가 이미 끝난 상태에서 display 메서드 호출 시 추가 쿼리가 0건이어야 함
        with self.assertNumQueries(0):
            item = staff_list[0]
            self.assertEqual(admin.get_executive_rank(item), '전무')
            self.assertEqual(admin.get_department(item), '경영기획팀')
            self.assertEqual(admin.get_duty(item), '팀장')

    def test_excel_export_optimized_views(self):
        """리팩토링된 ExportDeparts, ExportPositions, ExportGrades 엑셀 내보내기 200 검증"""
        from django.test import RequestFactory
        from company.exports.excel import ExportDeparts, ExportPositions, ExportGrades
        from company.models import Department, JobGrade, Position
        factory = RequestFactory()

        dept = Department.objects.create(company=self.company, name='개발기획팀')
        grade = JobGrade.objects.create(company=self.company, code='G1', role='과장')
        pos = Position.objects.create(company=self.company, name='선임연구원')
        pos.grades.add(grade)

        # 1. ExportDeparts
        req = factory.get(f'/company/export/departs/?company={self.company.pk}')
        res = ExportDeparts().get(req)
        self.assertEqual(res.status_code, 200)

        # 2. ExportPositions
        req = factory.get(f'/company/export/positions/?company={self.company.pk}')
        res = ExportPositions().get(req)
        self.assertEqual(res.status_code, 200)

        # 3. ExportGrades (검색어 포함 시에도 FieldError 없이 200 반환 검증)
        req = factory.get(f'/company/export/grades/?company={self.company.pk}&search=G1')
        res = ExportGrades().get(req)
        self.assertEqual(res.status_code, 200)

        # 4. ExportStaffs에 직급(grade) 보유 직원이 있을 때 AttributeError 없이 200 반환 및 ExportExecutiveRanks sort_order 검증
        from company.exports.excel import ExportStaffs, ExportExecutiveRanks
        self.staff.grade = grade
        self.staff.position = pos
        self.staff.save()
        req_staff = factory.get(f'/company/export/staffs/?company={self.company.pk}')
        res_staff = ExportStaffs().get(req_staff)
        self.assertEqual(res_staff.status_code, 200)

        req_er = factory.get(f'/company/export/executive-ranks/?company={self.company.pk}')
        res_er = ExportExecutiveRanks().get(req_er)
        self.assertEqual(res_er.status_code, 200)


class CompanySecurityAndOptimizationTests(APITestCase):
    def setUp(self):
        from decimal import Decimal
        self.admin = User.objects.create_superuser(username='super_admin', email='super_admin@test.com', password='password123')

        self.company_1 = Company.objects.create(name='(주)테스트건설', tax_number='123-11-11111', ceo='홍대표')
        self.company_2 = Company.objects.create(name='(주)타사개발', tax_number='456-22-22222', ceo='홍대표')

        self.user_1 = User.objects.create_user(username='staff_user1', email='su1@test.com', password='password123')
        self.staff_1 = Staff.objects.create(
            company=self.company_1, user=self.user_1, name='김사원', sort='2',
            id_number='950505-1234567', personal_phone='010-1234-5678', date_join='2022-01-01'
        )

        self.user_2 = User.objects.create_user(username='staff_user2', email='su2@test.com', password='password123')
        self.staff_2 = Staff.objects.create(
            company=self.company_2, user=self.user_2, name='이대리', sort='2',
            id_number='920202-2345678', personal_phone='010-8765-4321', date_join='2021-01-01'
        )

        self.dept_1 = Department.objects.create(company=self.company_1, name='본사영업팀')
        self.dept_2 = Department.objects.create(company=self.company_2, name='타사기획팀')

    def test_cross_company_staff_assignment_rejected(self):
        """A사 직원을 B사 부서에 발령 등록 시도 시 ValidationError(400) 차단 검증"""
        from company.models import StaffAssignment
        from django.core.exceptions import ValidationError

        assign = StaffAssignment(
            company=self.company_1,
            staff=self.staff_1,
            department=self.dept_2,  # 타사 부서!
        )
        with self.assertRaises(ValidationError):
            assign.full_clean()

    def test_department_api_circular_reference_rejected(self):
        """API를 통해 Department의 upper_depart를 자기 자신으로 지정 시 400 Bad Request 검증"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(f'/api/v1/department/{self.dept_1.pk}/', {
            'upper_depart': self.dept_1.pk
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('upper_depart', res.data)

    def test_department_api_cross_company_upper_depart_rejected(self):
        """API를 통해 Department의 upper_depart를 타사 부서로 지정 시 400 Bad Request 검증"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(f'/api/v1/department/{self.dept_1.pk}/', {
            'upper_depart': self.dept_2.pk
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('upper_depart', res.data)

    def test_excel_export_missing_company_param_returns_400(self):
        """company 쿼리 파라미터가 누락된 엑셀 내보내기 요청은 400 Bad Request 반환"""
        from django.test import RequestFactory
        from company.exports.excel import ExportStaffs
        factory = RequestFactory()
        req = factory.get('/company/export/staffs/')
        req.user = self.admin
        res = ExportStaffs().get(req)
        self.assertEqual(res.status_code, 400)

    def test_excel_export_cross_tenant_denied_returns_403(self):
        """Company 1 소속 일반 직원이 Company 2의 엑셀 내보내기 시도 시 403 Forbidden 반환"""
        from django.test import RequestFactory
        from company.exports.excel import ExportStaffs
        factory = RequestFactory()
        req = factory.get(f'/company/export/staffs/?company={self.company_2.pk}')
        req.user = self.user_1
        res = ExportStaffs().get(req)
        self.assertEqual(res.status_code, 403)

    def test_excel_export_staffs_id_number_masked_for_ordinary_user(self):
        """일반 직원이 본인 회사의 엑셀 다운로드 시 주민등록번호가 950505-*******로 마스킹되는지 검증"""
        from django.test import RequestFactory
        from company.exports.excel import ExportStaffs
        import openpyxl
        import io

        factory = RequestFactory()
        req = factory.get(f'/company/export/staffs/?company={self.company_1.pk}')
        req.user = self.user_1
        res = ExportStaffs().get(req)
        self.assertEqual(res.status_code, 200)

        # 엑셀 파일 파싱하여 주민번호 열 마스킹 확인
        wb = openpyxl.load_workbook(io.BytesIO(res.content))
        ws = wb.active
        # 행 4(인덱스 4)의 4번째 열(D열: 주민등록번호)
        id_cell = ws.cell(row=4, column=4).value
        self.assertEqual(id_cell, '950505-*******')

    def test_staff_leave_quota_property_instance_caching(self):
        """StaffLeaveQuota.used_days 호출 시 인스턴스 캐시를 활용하여 쿼리 재실행 방지 검증"""
        from decimal import Decimal
        from company.models import StaffLeaveQuota, StaffLeaveUsage
        quota = StaffLeaveQuota.objects.create(
            company=self.company_1, staff=self.staff_1, year=2026,
            granted_days=Decimal('15.00'), valid_start='2026-01-01', valid_end='2026-12-31'
        )
        StaffLeaveUsage.objects.create(
            company=self.company_1, staff=self.staff_1, start_date='2026-06-01', end_date='2026-06-01',
            deduction_days=Decimal('2.00'), is_cancelled=False
        )

        with self.assertNumQueries(1):
            used = quota.used_days
            self.assertEqual(used, Decimal('2.00'))

        # 인스턴스 캐시가 적용되어 subsequent 호출 및 remaining_days 호출 시 추가 쿼리 0건
        with self.assertNumQueries(0):
            used_cached = quota.used_days
            rem_cached = quota.remaining_days
            self.assertEqual(used_cached, Decimal('2.00'))
            self.assertEqual(rem_cached, Decimal('13.00'))

    def test_company_representative_staff_company_isolation(self):
        """다른 회사에 동일한 이름의 직원이 있더라도 자사 직원만 대표자로 매핑되는지 검증"""
        # company_2의 직원을 홍대표로 생성
        Staff.objects.create(company=self.company_2, name='홍대표', date_join='2020-01-01')

        # company_1에는 '홍대표'라는 직원이 없음 -> 사업자등록증상 ceo 텍스트 자체 반환
        rep_1 = self.company_1.get_representative_staff_name()
        self.assertEqual(rep_1, '홍대표')

        # company_1에 진짜 자사 직원 '홍대표' 생성
        Staff.objects.create(company=self.company_1, name='홍대표', date_join='2019-01-01')
        rep_1_after = self.company_1.get_representative_staff_name()
        self.assertEqual(rep_1_after, '홍대표')

    def test_duplicate_position_and_grade_names_across_companies_no_500(self):
        """다중 회사에 동일한 직위명/직급 코드가 존재할 때 MultipleObjectsReturned 없이 자사 직위/직급으로 매핑되는지 검증"""
        from company.models import JobGrade
        pos_c1 = Position.objects.create(company=self.company_1, name='공통과장')
        pos_c2 = Position.objects.create(company=self.company_2, name='공통과장')
        grade_c1 = JobGrade.objects.create(company=self.company_1, code='G1')
        grade_c2 = JobGrade.objects.create(company=self.company_2, code='G1')

        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(f'/api/v1/staff/{self.staff_1.pk}/', {
            'company': self.company_1.name,
            'position': '공통과장',
            'grade': 'G1',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.staff_1.refresh_from_db()
        self.assertEqual(self.staff_1.position_id, pos_c1.pk)
        self.assertNotEqual(self.staff_1.position_id, pos_c2.pk)
        self.assertEqual(self.staff_1.grade_id, grade_c1.pk)
        self.assertNotEqual(self.staff_1.grade_id, grade_c2.pk)

    def test_unauthenticated_excel_export_returns_401(self):
        """미인증 사용자(AnonymousUser)가 엑셀 다운로드 요청 시 401 차단 검증"""
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory
        from company.exports.excel import ExportStaffs

        factory = RequestFactory()
        req = factory.get(f'/company/export/staffs/?company={self.company_1.pk}')
        req.user = AnonymousUser()
        res = ExportStaffs().get(req)
        self.assertEqual(res.status_code, 401)

    def test_staff_masked_id_number_preserved_on_update_and_rejected_on_invalid(self):
        """[hrManage 수정] 마스킹된 주민번호로 PATCH/PUT 시 원본이 보존되고, 위조/생성 시 * 포함 값은 400 거부"""
        from work.models.project import IssueProject, Member, Role, Permission
        hq_ip = IssueProject.objects.create(
            company=self.company_1, name='본사', slug='hq-mask-test', type='1', creator=self.admin
        )
        perm_upd, _ = Permission.objects.get_or_create(
            code='hq.hr_work.update',
            defaults={'name': '인사 수정', 'module': 'hr_work', 'is_for_hq': True}
        )
        role_upd = Role.objects.create(name='인사수정자', category='ibs_hq_manage', creator=self.admin)
        role_upd.permissions.add(perm_upd)
        # user_2는 타사지만 company_1 직원을 생성해 테스트
        updater_user = User.objects.create_user(username='updater_u1', email='upd@test.com', password='password123')
        Staff.objects.create(
            company=self.company_1, user=updater_user, name='인사담당', sort='2',
            id_number='910101-1111111', personal_phone='010-2222-3333', date_join='2022-01-01'
        )
        mem = Member.objects.create(user=updater_user, project=hq_ip)
        mem.roles.add(role_upd)

        self.client.force_authenticate(user=updater_user)
        # 1) 조회 시 마스킹 문자열 수신 확인
        get_res = self.client.get(f'/api/v1/staff/{self.staff_1.pk}/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['id_number'], '950505-*******')

        # 2) 마스킹된 id_number 그대로 포함해 다른 필드(email) 수정 시 원본 주민번호 보존
        put_res = self.client.patch(f'/api/v1/staff/{self.staff_1.pk}/', {
            'id_number': get_res.data['id_number'],
            'email': 'updated@test.com',
        })
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)
        self.staff_1.refresh_from_db()
        self.assertEqual(self.staff_1.id_number, '950505-1234567')
        self.assertEqual(self.staff_1.email, 'updated@test.com')

        # 3) 일치하지 않는 임의 * 문자열은 400 거부
        bad_res = self.client.patch(f'/api/v1/staff/{self.staff_1.pk}/', {
            'id_number': '999999-*******',
        })
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_grade_filter_and_leave_usage_date_filter_and_excel_filters(self):
        """[hrManage 수정] StaffFilter grade 필터, StaffLeaveUsageFilter 날짜 필터, Excel 추가 필터 검증"""
        from decimal import Decimal
        from django.test import RequestFactory
        from company.models import JobGrade, PromotionPolicy, PromotionCandidate, StaffLeaveUsage
        from company.exports.excel import ExportStaffLeaveUsages, ExportPromotionCandidates

        g1 = JobGrade.objects.create(company=self.company_1, code='G1')
        g2 = JobGrade.objects.create(company=self.company_1, code='G2')
        self.staff_1.grade = g1
        self.staff_1.save()

        self.client.force_authenticate(user=self.admin)
        res_g1 = self.client.get(f'/api/v1/staff/?company={self.company_1.pk}&grade={g1.pk}')
        res_g2 = self.client.get(f'/api/v1/staff/?company={self.company_1.pk}&grade={g2.pk}')
        self.assertEqual(res_g1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_g1.data['results']), 1)
        self.assertEqual(len(res_g2.data['results']), 0)

        u1 = StaffLeaveUsage.objects.create(
            company=self.company_1, staff=self.staff_1, start_date='2026-03-01', end_date='2026-03-01',
            deduction_days=Decimal('1.00'), is_cancelled=False, reason='정상휴가'
        )
        u2 = StaffLeaveUsage.objects.create(
            company=self.company_1, staff=self.staff_1, start_date='2026-05-10', end_date='2026-05-10',
            deduction_days=Decimal('1.00'), is_cancelled=True, reason='취소휴가'
        )
        res_date = self.client.get(
            f'/api/v1/staff-leave-usage/?company={self.company_1.pk}&start_date=2026-04-01&end_date=2026-05-31'
        )
        self.assertEqual(res_date.status_code, status.HTTP_200_OK)
        self.assertEqual([x['pk'] for x in res_date.data['results']], [u2.pk])

        factory = RequestFactory()
        req_lu = factory.get(f'/excel/staff-leave-usages/?company={self.company_1.pk}&is_cancelled=false')
        req_lu.user = self.admin
        res_lu_excel = ExportStaffLeaveUsages().get(req_lu)
        self.assertEqual(res_lu_excel.status_code, 200)

        pol = PromotionPolicy.objects.create(company=self.company_1, current_grade=g1, target_grade=g2, min_years=3)
        PromotionCandidate.objects.create(company=self.company_1, policy=pol, staff=self.staff_1, eval_year=2026)
        req_pc = factory.get(f'/excel/staff-promotion-candidates/?company={self.company_1.pk}&policy={pol.pk}')
        req_pc.user = self.admin
        res_pc_excel = ExportPromotionCandidates().get(req_pc)
        self.assertEqual(res_pc_excel.status_code, 200)

    def test_company_viewset_permissions_extended_fields_and_protected_delete(self):
        """[settings/Company] 비슈퍼유저 쓰기 차단, 확장 필드 수정 및 PROTECT 연결 회사 삭제 시 409 반환"""
        from ledger.models import Affiliate

        # 비슈퍼유저는 생성/수정/삭제 불가 (403)
        self.client.force_authenticate(user=self.user_1)
        res_create_denied = self.client.post('/api/v1/company/', {
            'name': '무단회사', 'tax_number': '111-11-11111', 'ceo': '홍길동', 'org_number': '111111-1111111'
        })
        self.assertEqual(res_create_denied.status_code, status.HTTP_403_FORBIDDEN)
        res_patch_denied = self.client.patch(f'/api/v1/company/{self.company_1.pk}/', {'en_name': 'Hacked Co.'})
        self.assertEqual(res_patch_denied.status_code, status.HTTP_403_FORBIDDEN)

        # 슈퍼유저는 확장 필드 포함 부분 수정 및 null 날짜 처리 가능
        self.client.force_authenticate(user=self.admin)
        res_patch = self.client.patch(f'/api/v1/company/{self.company_1.pk}/', {
            'en_name': 'Gabul Construction Co., Ltd.',
            'phone': '02-1234-5678',
            'fax': '02-1234-5679',
            'email': 'info@gabul.co.kr',
            'is_default': True,
            'es_date': None,
        }, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.company_1.refresh_from_db()
        self.assertEqual(self.company_1.en_name, 'Gabul Construction Co., Ltd.')
        self.assertEqual(self.company_1.phone, '02-1234-5678')
        self.assertTrue(self.company_1.is_default)
        self.assertIsNone(self.company_1.es_date)

        # Affiliate(PROTECT) 연결 시 삭제하면 500 대신 409 Conflict 반환
        Affiliate.objects.create(sort='company', company=self.company_1)
        res_del = self.client.delete(f'/api/v1/company/{self.company_1.pk}/')
        self.assertEqual(res_del.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Company.objects.filter(pk=self.company_1.pk).exists())



