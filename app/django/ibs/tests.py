from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from company.models import Company, Staff
from ibs.models import (
    AccountSort, AccountSubD1, AccountSubD2, AccountSubD3,
    ProjectAccountD2, ProjectAccountD3, UserWidgetConfig,
    CalendarSchedule, WiseSaying
)
from apiV1.permissions.ibs_perms import IbsModulePermission
from work.models.project import IssueProject, Member

User = get_user_model()


class IbsModelStrAndMetaTest(TestCase):
    """IBS 모델의 문자열 표현(__str__) 및 Meta 옵션 검증"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='model_user', email='model@test.com', password='password123'
        )
        self.sort = AccountSort.objects.create(name='입금')
        self.d1 = AccountSubD1.objects.create(code='100', name='자산', description='자산 계정')
        self.d1.sorts.add(self.sort)
        self.d2 = AccountSubD2.objects.create(d1=self.d1, code='110', name='유동자산', description='유동자산')
        self.d3 = AccountSubD3.objects.create(
            sort=self.sort, d2=self.d2, code='111', name='보통예금', description='보통예금'
        )
        self.pro_d2 = ProjectAccountD2.objects.create(d1=self.d1, code='210', name='공사비', description='공사비')
        self.pro_d3 = ProjectAccountD3.objects.create(
            sort=self.sort, d2=self.pro_d2, code='211', name='토목공사비', description='토목'
        )

    def test_model_str_methods(self):
        self.assertEqual(str(self.sort), '입금')
        self.assertEqual(str(self.d1), '[100] 자산 계정')
        self.assertEqual(str(self.d2), '[110] 유동자산')
        self.assertEqual(str(self.d3), '[111] 보통예금')
        self.assertEqual(str(self.pro_d2), '공사비')
        self.assertEqual(str(self.pro_d3), '토목공사비')

        config = UserWidgetConfig.objects.create(
            user=self.user,
            layouts={'lg': []},
            visible_widgets=['widget1']
        )
        self.assertIn('model_user의 대시보드 설정', str(config))

        schedule = CalendarSchedule.objects.create(
            title='임원 정기회의',
            all_day=True,
            start_date='2026-09-26',
            creator=self.user
        )
        self.assertEqual(str(schedule), '임원 정기회의')

        wise = WiseSaying.objects.create(
            saying_ko='시작이 반이다',
            saying_en='Well begun is half done',
            spoked_by='아리스토텔레스'
        )
        self.assertEqual(str(wise), '시작이 반이다 - 아리스토텔레스')

    def test_model_ordering(self):
        self.assertEqual(CalendarSchedule._meta.ordering, ['-id'])
        self.assertEqual(WiseSaying._meta.ordering, ['id'])


class WiseSayViewSetTest(TestCase):
    """오늘의 한마디(WiseSayViewSet) 권한 및 동작 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name='IBS건설')
        self.admin = User.objects.create_superuser(
            username='admin_wise', email='admin@wise.com', password='password123'
        )
        self.normal_user = User.objects.create_user(
            username='normal_user', email='normal@wise.com', password='password123'
        )
        self.staff_user = User.objects.create_user(
            username='staff_user', email='staff@wise.com', password='password123'
        )
        Staff.objects.create(
            company=self.company, user=self.staff_user, name='스태프',
            id_number='800101-1234567', personal_phone='010-1234-5678', date_join='2020-01-01'
        )
        # 프로젝트 멤버로 등록하여 IsProjectStaffOrReadOnly 조건 만족
        self.project = IssueProject.objects.create(
            company=self.company,
            name='본사 프로젝트', slug='hq-proj', type='1', creator=self.admin
        )
        Member.objects.create(project=self.project, user=self.staff_user)

        self.wise = WiseSaying.objects.create(
            saying_ko='행동이 답이다', saying_en='Action is the answer', spoked_by='익명'
        )

    def test_anonymous_user_blocked(self):
        res = self.client.get('/api/v1/wise-say/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_user_read_only(self):
        """일반 유저는 GET 조회만 가능하고 POST, PUT, DELETE 차단 (permissions_classes 오타 수정 검증)"""
        self.client.force_authenticate(user=self.normal_user)

        res = self.client.get('/api/v1/wise-say/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # POST 차단
        post_res = self.client.post('/api/v1/wise-say/', {
            'saying_ko': '해킹 명언', 'saying_en': 'Hacked quote', 'spoked_by': '해커'
        })
        self.assertEqual(post_res.status_code, status.HTTP_403_FORBIDDEN)

        # DELETE 차단
        del_res = self.client.delete(f'/api/v1/wise-say/{self.wise.pk}/')
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_create_and_delete(self):
        """스태프 유저는 등록 및 삭제 가능"""
        self.client.force_authenticate(user=self.staff_user)

        post_res = self.client.post('/api/v1/wise-say/', {
            'saying_ko': '새 명언', 'saying_en': 'New quote', 'spoked_by': '작성자'
        })
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)

        new_pk = post_res.data['pk']
        del_res = self.client.delete(f'/api/v1/wise-say/{new_pk}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)


class UserWidgetConfigViewSetTest(TestCase):
    """대시보드 위젯 설정(UserWidgetConfigViewSet) 격리 및 upsert 검증"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1', email='u1@test.com', password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='u2@test.com', password='password123'
        )

    def test_upsert_on_duplicate_post(self):
        """동일 유저가 POST를 여러 번 호출해도 500 에러 없이 정상적으로 갱신(upsert)되어야 함"""
        self.client.force_authenticate(user=self.user1)

        # 1. 최초 생성 (201 Created)
        res1 = self.client.post('/api/v1/user-widget-config/', {
            'layouts': {'lg': [{'i': 'w1', 'x': 0, 'y': 0, 'w': 2, 'h': 2}]},
            'visible_widgets': ['w1'],
            'version': 1
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserWidgetConfig.objects.filter(user=self.user1).count(), 1)

        # 2. 동일 유저가 두 번째 POST 전송 -> 500 에러가 아닌 200 OK로 기존 설정 부분 갱신
        res2 = self.client.post('/api/v1/user-widget-config/', {
            'layouts': {'lg': [{'i': 'w1', 'x': 1, 'y': 1, 'w': 3, 'h': 3}]},
            'visible_widgets': ['w1', 'w2'],
            'version': 2
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(UserWidgetConfig.objects.filter(user=self.user1).count(), 1)

        # 갱신 내용 확인
        config = UserWidgetConfig.objects.get(user=self.user1)
        self.assertEqual(config.version, 2)
        self.assertEqual(config.visible_widgets, ['w1', 'w2'])

    def test_user_data_isolation(self):
        """유저 간 위젯 설정 격리(Row-Level Security) 확인"""
        cfg1 = UserWidgetConfig.objects.create(
            user=self.user1, layouts={'lg': []}, visible_widgets=['w1']
        )
        cfg2 = UserWidgetConfig.objects.create(
            user=self.user2, layouts={'lg': []}, visible_widgets=['w2']
        )

        self.client.force_authenticate(user=self.user1)
        res = self.client.get('/api/v1/user-widget-config/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # 본인 설정만 반환되어야 함
        pks = [item['pk'] for item in res.data['results']]
        self.assertIn(cfg1.pk, pks)
        self.assertNotIn(cfg2.pk, pks)

        # 타인 설정 접근 시 404
        other_res = self.client.get(f'/api/v1/user-widget-config/{cfg2.pk}/')
        self.assertEqual(other_res.status_code, status.HTTP_404_NOT_FOUND)


class CalendarScheduleViewSetTest(TestCase):
    """캘린더 일정(CalendarScheduleViewSet) 등록, 검색, 권한 검증"""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name='캘린더건설')
        self.admin = User.objects.create_superuser(
            username='admin_cal', email='admin@cal.com', password='password123'
        )
        self.normal_user = User.objects.create_user(
            username='normal_cal', email='normal@cal.com', password='password123'
        )
        self.project_staff = User.objects.create_user(
            username='staff_cal', email='staff@cal.com', password='password123'
        )
        self.project = IssueProject.objects.create(
            company=self.company,
            name='일정 프로젝트', slug='cal-proj', type='2', creator=self.admin
        )
        Member.objects.create(project=self.project, user=self.project_staff)

        # 일정 등록
        self.schedule1 = CalendarSchedule.objects.create(
            title='2026년 주간공정회의',
            all_day=True,
            start_date='2026-09-20',
            end_date='2026-09-20',
            creator=self.admin
        )
        self.schedule2 = CalendarSchedule.objects.create(
            title='프로젝트 안전점검',
            all_day=True,
            start_date='2026-09-25',
            end_date='2026-09-25',
            creator=self.project_staff
        )

    def test_schedule_title_search(self):
        """일정 제목(title) 검색 기능 검증"""
        self.client.force_authenticate(user=self.normal_user)

        res = self.client.get('/api/v1/schedule/?search=공정회의')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], '2026년 주간공정회의')

    def test_schedule_date_search(self):
        """일정 일자(start_date) 검색 기능 검증"""
        self.client.force_authenticate(user=self.normal_user)

        res = self.client.get('/api/v1/schedule/?search=2026-09-25')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], '프로젝트 안전점검')

    def test_schedule_create_permission(self):
        """일반 유저는 일정 등록 차단, 프로젝트 스태프는 등록 허용 및 creator 자동 설정"""
        # 일반 유저 차단
        self.client.force_authenticate(user=self.normal_user)
        denied_res = self.client.post('/api/v1/schedule/', {
            'title': '임의 등록', 'all_day': True, 'start_date': '2026-09-28'
        })
        self.assertEqual(denied_res.status_code, status.HTTP_403_FORBIDDEN)

        # 프로젝트 스태프 등록
        self.client.force_authenticate(user=self.project_staff)
        allow_res = self.client.post('/api/v1/schedule/', {
            'title': '인허가 협의', 'all_day': True, 'start_date': '2026-09-28'
        })
        self.assertEqual(allow_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(allow_res.data['creator']['username'], 'staff_cal')

    def test_schedule_date_range_filter(self):
        """[M-2] 캘린더 일정 날짜 범위 필터(CalendarScheduleFilterSet) 검증"""
        self.client.force_authenticate(user=self.normal_user)

        # 9월 20일 ~ 9월 22일 범위 조회 -> schedule1 (2026-09-20) 포함, schedule2 (2026-09-25) 제외
        res = self.client.get('/api/v1/schedule/?start_date_from=2026-09-20&start_date_to=2026-09-22')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], '2026년 주간공정회의')

        # 9월 24일 이후 조회 -> schedule2 포함
        res2 = self.client.get('/api/v1/schedule/?start_date_from=2026-09-24')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        results2 = res2.data['results']
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]['title'], '프로젝트 안전점검')

    def test_schedule_idor_protection(self):
        """[P0-보안] 타인의 캘린더 일정에 대한 수정(PUT/PATCH) 및 삭제(DELETE) IDOR 차단 검증"""
        # 프로젝트 스태프 유저가 최고관리자의 일정(schedule1) 수정 시도 -> 403 차단
        self.client.force_authenticate(user=self.project_staff)
        put_res = self.client.put(f'/api/v1/schedule/{self.schedule1.pk}/', {
            'title': '임의 변조 시도', 'all_day': True, 'start_date': '2026-09-20'
        })
        self.assertEqual(put_res.status_code, status.HTTP_403_FORBIDDEN)

        # 최고관리자의 일정 삭제 시도 -> 403 차단
        del_res = self.client.delete(f'/api/v1/schedule/{self.schedule1.pk}/')
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)

        # 본인 일정(schedule2) 수정 -> 200 성공
        own_put_res = self.client.put(f'/api/v1/schedule/{self.schedule2.pk}/', {
            'title': '정상 일정 변경', 'all_day': True, 'start_date': '2026-09-25'
        })
        self.assertEqual(own_put_res.status_code, status.HTTP_200_OK)

        # 최고관리자는 타인 일정 삭제 가능 -> 204 성공
        self.client.force_authenticate(user=self.admin)
        admin_del_res = self.client.delete(f'/api/v1/schedule/{self.schedule2.pk}/')
        self.assertEqual(admin_del_res.status_code, status.HTTP_204_NO_CONTENT)

    def test_schedule_auto_date_and_serializer_validation(self):
        """[P0/P2] 시간제 일정 저장 시 start_date 자동 보정 및 시작/종료일시 역전 방지 검증"""
        # 1. start_time만 있고 start_date가 없을 때 자동 보정 확인
        timed_schedule = CalendarSchedule(
            title='오후 현장 미팅',
            all_day=False,
            start_time='2026-11-04 14:00:00+09:00',
            end_time='2026-11-04 16:00:00+09:00',
            creator=self.project_staff
        )
        timed_schedule.save()
        self.assertIsNotNone(timed_schedule.start_date)
        self.assertEqual(str(timed_schedule.start_date), '2026-11-04')
        self.assertEqual(str(timed_schedule.end_date), '2026-11-04')

        # 2. 날짜 역전 (start_date > end_date) 시 유효성 검사 오류 (400)
        self.client.force_authenticate(user=self.project_staff)
        invalid_res = self.client.post('/api/v1/schedule/', {
            'title': '종료일 역전 일정',
            'all_day': True,
            'start_date': '2026-11-10',
            'end_date': '2026-11-05'
        })
        self.assertEqual(invalid_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', invalid_res.data)



class AccountViewSetsPermissionTest(TestCase):
    """회계 계정 과목 API의 권한 제어 검증 (일반 사용자 변조 차단)"""

    def setUp(self):
        self.client = APIClient()
        self.normal_user = User.objects.create_user(
            username='normal_acc', email='normal@acc.com', password='password123'
        )
        self.admin = User.objects.create_superuser(
            username='admin_acc', email='admin@acc.com', password='password123'
        )
        self.sort = AccountSort.objects.create(name='출금')
        self.d1 = AccountSubD1.objects.create(code='200', name='부채', description='부채 계정')
        self.d1.sorts.add(self.sort)
        self.d2 = AccountSubD2.objects.create(d1=self.d1, code='210', name='유동부채', description='유동부채')
        self.d3 = AccountSubD3.objects.create(
            sort=self.sort, d2=self.d2, code='211', name='외상매입금', description='외상'
        )
        self.pro_d2 = ProjectAccountD2.objects.create(d1=self.d1, code='310', name='판매비', description='판매비')
        self.pro_d3 = ProjectAccountD3.objects.create(
            sort=self.sort, d2=self.pro_d2, code='311', name='분양수수료', description='수수료'
        )

    def test_normal_user_cannot_delete_or_create_accounts(self):
        """일반 유저는 조회(GET)는 가능하나 삭제(DELETE) 및 생성(POST)은 403 차단"""
        self.client.force_authenticate(user=self.normal_user)

        # 조회 성공
        self.assertEqual(self.client.get('/api/v1/account-sort/').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/v1/account-depth1/').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/v1/account-depth2/').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/v1/account-depth3/').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/v1/project-account-depth2/').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get('/api/v1/project-account-depth3/').status_code, status.HTTP_200_OK)

        # 삭제 차단
        self.assertEqual(
            self.client.delete(f'/api/v1/account-sort/{self.sort.pk}/').status_code,
            status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            self.client.delete(f'/api/v1/account-depth1/{self.d1.pk}/').status_code,
            status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            self.client.delete(f'/api/v1/account-depth3/{self.d3.pk}/').status_code,
            status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            self.client.delete(f'/api/v1/project-account-depth3/{self.pro_d3.pk}/').status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_admin_can_modify_accounts(self):
        """관리자는 계정 생성 및 수정 가능"""
        self.client.force_authenticate(user=self.admin)

        patch_res = self.client.patch(f'/api/v1/account-depth3/{self.d3.pk}/', {
            'is_hide': True
        })
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.d3.refresh_from_db()
        self.assertTrue(self.d3.is_hide)

    def test_readonly_viewsets_block_post_and_delete_even_for_admin(self):
        """[P0-보안] 회계 계정 과목 API의 ReadOnly 전환으로 관리자라도 API를 통한 임의 DELETE/POST 불가 (405 차단)"""
        self.client.force_authenticate(user=self.admin)

        # 1. ReadOnlyModelViewSet 엔드포인트는 DELETE 및 POST 불가 (405 Method Not Allowed)
        self.assertEqual(
            self.client.delete(f'/api/v1/account-sort/{self.sort.pk}/').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            self.client.post('/api/v1/account-sort/', {'name': '테스트'}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            self.client.delete(f'/api/v1/project-account-depth3/{self.pro_d3.pk}/').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # 2. AccountSubD3는 is_hide 변경을 위해 PATCH만 허용, DELETE나 POST는 405 차단
        self.assertEqual(
            self.client.delete(f'/api/v1/account-depth3/{self.d3.pk}/').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            self.client.post('/api/v1/account-depth3/', {'name': '새계정'}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )



class IbsPermsHardeningTest(TestCase):
    """IbsModulePermission의 방어 코드 검증"""

    def test_resolve_project_graceful_handling(self):
        """문자열, None, 잘못된 형식의 project_pk 전달 시 ValueError 없이 None 반환"""
        self.assertIsNone(IbsModulePermission._resolve_project_issue_project(None))
        self.assertIsNone(IbsModulePermission._resolve_project_issue_project('invalid_string'))
        self.assertIsNone(IbsModulePermission._resolve_project_issue_project(99999999))


class IbsAdminQueryOptimizationTest(TestCase):
    """[M-3] AccountSubD3Admin, ProjectAccountD3Admin, CalendarScheduleAdmin list_select_related 최적화 검증"""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_opt', email='admin@opt.com', password='password123'
        )
        self.sort = AccountSort.objects.create(name='출금')
        self.d1 = AccountSubD1.objects.create(code='200', name='부채', description='부채 계정')
        self.d1.sorts.add(self.sort)
        self.d2 = AccountSubD2.objects.create(d1=self.d1, code='210', name='유동부채', description='유동부채')
        self.d3 = AccountSubD3.objects.create(
            sort=self.sort, d2=self.d2, code='211', name='외상매입금', description='외상'
        )
        self.pro_d2 = ProjectAccountD2.objects.create(d1=self.d1, code='310', name='판매비', description='판매비')
        self.pro_d3 = ProjectAccountD3.objects.create(
            sort=self.sort, d2=self.pro_d2, code='311', name='분양수수료', description='수수료'
        )
        self.schedule = CalendarSchedule.objects.create(
            title='공정회의',
            all_day=True,
            start_date='2026-09-20',
            end_date='2026-09-20',
            creator=self.admin
        )

    def test_ibs_admin_query_optimization(self):
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from ibs.admin import (
            AccountSubD3Admin, ProjectAccountD3Admin, CalendarScheduleAdmin
        )

        factory = RequestFactory()
        req = factory.get('/admin/')
        req.user = self.admin

        # 1. AccountSubD3Admin
        d3_admin = AccountSubD3Admin(AccountSubD3, AdminSite())
        d3_qs = list(d3_admin.get_queryset(req).filter(pk=self.d3.pk))
        self.assertEqual(len(d3_qs), 1)
        with self.assertNumQueries(0):
            item = d3_qs[0]
            _ = item.sort.name
            _ = item.d2.name

        # 2. ProjectAccountD3Admin
        pro_d3_admin = ProjectAccountD3Admin(ProjectAccountD3, AdminSite())
        pro_d3_qs = list(pro_d3_admin.get_queryset(req).filter(pk=self.pro_d3.pk))
        self.assertEqual(len(pro_d3_qs), 1)
        with self.assertNumQueries(0):
            item = pro_d3_qs[0]
            _ = item.sort.name
            _ = item.d2.name

        # 3. CalendarScheduleAdmin
        cal_admin = CalendarScheduleAdmin(CalendarSchedule, AdminSite())
        cal_qs = list(cal_admin.get_queryset(req).filter(pk=self.schedule.pk))
        self.assertEqual(len(cal_qs), 1)
        with self.assertNumQueries(0):
            item = cal_qs[0]
            _ = item.creator.username

    def test_ibs_admin_search_fields_and_rls(self):
        """UserWidgetConfigAdmin 및 CalendarScheduleAdmin 검색 시 FieldError가 발생하지 않고 비관리자 RLS가 동작하는지 검증"""
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from ibs.admin import UserWidgetConfigAdmin, CalendarScheduleAdmin

        other_user = User.objects.create_user(
            username='other_opt', email='other@opt.com', password='password123'
        )
        UserWidgetConfig.objects.create(user=self.admin, layouts={}, visible_widgets=[])
        UserWidgetConfig.objects.create(user=other_user, layouts={}, visible_widgets=[])

        factory = RequestFactory()
        req_other = factory.get('/admin/')
        req_other.user = other_user

        # 1. UserWidgetConfigAdmin 검색 및 RLS
        cfg_admin = UserWidgetConfigAdmin(UserWidgetConfig, AdminSite())
        qs_other = cfg_admin.get_queryset(req_other)
        self.assertEqual(qs_other.count(), 1)
        searched_qs, _ = cfg_admin.get_search_results(req_other, UserWidgetConfig.objects.all(), 'admin_opt')
        self.assertEqual(searched_qs.count(), 1)

        # 2. CalendarScheduleAdmin 검색 및 RLS
        cal_admin = CalendarScheduleAdmin(CalendarSchedule, AdminSite())
        cal_qs_other = cal_admin.get_queryset(req_other)
        self.assertEqual(cal_qs_other.count(), 0)
        cal_searched, _ = cal_admin.get_search_results(req_other, CalendarSchedule.objects.all(), '공정회의')
        self.assertGreaterEqual(cal_searched.count(), 1)

    def test_account_sub_d3_master_fields_protected_and_staff_blocked(self):
        """본사 세부계정(AccountSubD3) PATCH 시 권한 없는 일반 직원 차단 및 마스터 필드(code/name) 변조 방지 검증"""
        client = APIClient()
        company = Company.objects.create(name='회계테스트사')
        staff_no_perm = User.objects.create_user(
            username='staff_noperm', email='noperm@acc.com', password='password123'
        )
        Staff.objects.create(
            company=company, user=staff_no_perm, name='일반사원',
            id_number='900101-1234567', personal_phone='010-1111-2222', date_join='2024-01-01'
        )

        # 1. 회계 권한(ledger.com_update) 없는 일반 사원이 PATCH 시도 -> 403 차단
        client.force_authenticate(user=staff_no_perm)
        res_denied = client.patch(f'/api/v1/account-depth3/{self.d3.pk}/', {'is_hide': True}, format='json')
        self.assertEqual(res_denied.status_code, status.HTTP_403_FORBIDDEN)

        # 2. 관리자가 PATCH로 is_hide와 함께 code, name 변조 시도 -> is_hide만 반영되고 code/name은 보호됨
        client.force_authenticate(user=self.admin)
        res_admin = client.patch(
            f'/api/v1/account-depth3/{self.d3.pk}/',
            {'is_hide': True, 'code': '999', 'name': '변조된계정명'},
            format='json',
        )
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        self.d3.refresh_from_db()
        self.assertTrue(self.d3.is_hide)
        self.assertEqual(self.d3.code, '211')
        self.assertEqual(self.d3.name, '외상매입금')

    def test_schedule_kst_midnight_date_extraction_and_clean(self):
        """한국 시간(UTC+9) 오전 01:00 시간제 일정의 start_date가 UTC 전날로 밀리지 않고 당일로 저장되는지 검증"""
        from datetime import datetime, timezone as dt_tz
        from django.core.exceptions import ValidationError

        # 2026-11-04 01:00:00 KST == 2026-11-03 16:00:00 UTC
        utc_dt = datetime(2026, 11, 3, 16, 0, 0, tzinfo=dt_tz.utc)
        sched = CalendarSchedule.objects.create(
            title='심야 점검 일정',
            all_day=False,
            start_time=utc_dt,
            end_time=utc_dt,
            creator=self.admin,
        )
        self.assertEqual(str(sched.start_date), '2026-11-04')
        self.assertEqual(str(sched.end_date), '2026-11-04')

        # clean() 일자 역전 검증
        bad_sched = CalendarSchedule(
            title='역전 일정',
            all_day=True,
            start_date='2026-11-10',
            end_date='2026-11-01',
        )
        with self.assertRaises(ValidationError):
            bad_sched.clean()

    def test_user_widget_config_json_type_validation(self):
        """UserWidgetConfigSerializer에서 layouts(dict) 및 visible_widgets(list) 타입 불일치 시 400 차단 검증"""
        client = APIClient()
        client.force_authenticate(user=self.admin)

        res_bad_layout = client.post(
            '/api/v1/user-widget-config/',
            {'layouts': 'invalid-string', 'visible_widgets': ['w1']},
            format='json',
        )
        self.assertEqual(res_bad_layout.status_code, status.HTTP_400_BAD_REQUEST)

        res_bad_widgets = client.post(
            '/api/v1/user-widget-config/',
            {'layouts': {}, 'visible_widgets': {'not': 'a-list'}},
            format='json',
        )
        self.assertEqual(res_bad_widgets.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hq_permission_excludes_locked_workspace(self):
        """잠금보관(status='9')된 본사 워크스페이스의 권한이 HqProjectModulePermission에서 제외되는지 검증"""
        from apiV1.permissions.ibs_perms import HqProjectModulePermission
        from work.models.project import Role, Permission

        company = Company.objects.create(name='잠금본사테스트')
        user = User.objects.create_user(username='locked_hq_user', email='lhq@test.com', password='password123')
        perm = Permission.objects.create(module='ledger', code='ledger.com_update', name='본사회계수정')
        role = Role.objects.create(name='본사회계담당', creator=self.admin)
        role.permissions.add(perm)

        hq_proj = IssueProject.objects.create(
            company=company, name='잠긴본사워크스페이스', slug='locked-hq-ws', type='1', status='9', creator=self.admin
        )
        m = Member.objects.create(project=hq_proj, user=user)
        m.roles.add(role)

        perms = HqProjectModulePermission._get_all_hq_user_permissions(user)
        self.assertNotIn('ledger.com_update', perms)
