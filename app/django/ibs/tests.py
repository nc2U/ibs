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
            title='현장 안전점검',
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
        self.assertEqual(results[0]['title'], '현장 안전점검')

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


class IbsPermsHardeningTest(TestCase):
    """IbsModulePermission의 방어 코드 검증"""

    def test_resolve_project_graceful_handling(self):
        """문자열, None, 잘못된 형식의 project_pk 전달 시 ValueError 없이 None 반환"""
        self.assertIsNone(IbsModulePermission._resolve_project_issue_project(None))
        self.assertIsNone(IbsModulePermission._resolve_project_issue_project('invalid_string'))
        self.assertIsNone(IbsModulePermission._resolve_project_issue_project(99999999))
