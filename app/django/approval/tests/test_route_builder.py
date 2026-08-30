from django.test import TestCase
from django.contrib.auth import get_user_model
from company.models import Company, Department, Staff, StaffAssignment, DutyTitle, Position
from approval.models import DocCategory, DocumentType
from approval.services.route_builder import build_dynamic_approval_route

User = get_user_model()


class ApprovalRouteBuilderTestCase(TestCase):
    """동일인 겸직 시 최상위 직함 승격(Highest Role Promotion) 검증 테스트"""

    def setUp(self):
        # 1. 회사 및 직급/직책 생성
        self.company = Company.objects.create(name='(주)대영아이비에스', is_default=True)
        self.pos_staff = Position.objects.create(company=self.company, name='사원')
        self.pos_manager = Position.objects.create(company=self.company, name='팀장')
        self.pos_ceo = Position.objects.create(company=self.company, name='대표이사')

        self.duty_team_leader = DutyTitle.objects.create(company=self.company, name='팀장', code='TL')
        self.duty_division_head = DutyTitle.objects.create(company=self.company, name='본부장', code='DH')
        self.duty_ceo = DutyTitle.objects.create(company=self.company, name='대표이사', code='CEO')

        # 2. 상위 부서(본부) 및 하위 부서(팀) 생성
        self.dept_division = Department.objects.create(
            company=self.company, name='경영지원본부', level=1
        )
        self.dept_team = Department.objects.create(
            company=self.company, name='경영지원팀', level=2, upper_depart=self.dept_division
        )

        # 3. 사용자 및 직원 생성
        # 기안자 (팀원)
        self.user_drafter = User.objects.create_user(username='drafter', email='drafter@example.com')
        self.staff_drafter = Staff.objects.create(
            company=self.company, user=self.user_drafter, name='김사원',
            position=self.pos_staff, id_number='900101-1234567', personal_phone='010-1111-2222',
            date_join='2025-01-01', status='1'
        )
        self.assign_drafter = StaffAssignment.objects.create(
            staff=self.staff_drafter, company=self.company, department=self.dept_team,
            is_primary=True
        )

        # 대표이사 (경영지원팀장 겸직)
        self.user_ceo = User.objects.create_user(username='ceo', email='ceo@example.com')
        self.staff_ceo = Staff.objects.create(
            company=self.company, user=self.user_ceo, name='홍대표',
            position=self.pos_ceo, id_number='750101-1234567', personal_phone='010-3333-4444',
            date_join='2020-01-01', status='1'
        )
        # 대표이사 주보직
        StaffAssignment.objects.create(
            staff=self.staff_ceo, company=self.company, department=self.dept_division,
            duty=self.duty_ceo, is_primary=True
        )
        # 경영지원팀장 겸직
        StaffAssignment.objects.create(
            staff=self.staff_ceo, company=self.company, department=self.dept_team,
            duty=self.duty_team_leader, is_primary=False
        )

        # 4. 문서 유형 생성 (대표이사 최종 승인 방식)
        self.category = DocCategory.objects.create(name='일반품의', code='COMMON')
        self.doc_type = DocumentType.objects.create(
            category=self.category, name='업무품의서', code='BIZ_APPROVAL',
            route_type=DocumentType.ROUTE_ORGANIZATION
        )

    def test_ceo_concurrent_position_promotes_role_label(self):
        """팀원이 기안 시, 팀장을 겸직하는 대표이사의 결재 라벨이 '경영지원팀 팀장'이 아닌 '대표이사 최종 승인'으로 승격되는지 검증"""
        routes = build_dynamic_approval_route(
            doc_type=self.doc_type,
            drafter_user=self.user_drafter,
            drafter_assignment=self.assign_drafter,
        )

        # 결재 단계는 중복 없이 1단계로 단축되어야 함
        self.assertEqual(len(routes), 1)
        step1 = routes[0]
        self.assertEqual(step1['approver_ids'], [self.user_ceo.id])
        # 🌟 핵심 검증: 라벨이 '경영지원팀 팀장' 대신 '대표이사 최종 승인'으로 승격되었는지 확인
        self.assertEqual(step1['role_label'], '대표이사 최종 승인')

    def test_self_approval_prevention_promotes_to_higher_authority(self):
        """전결권자(팀장) 본인이 기안 시, 셀프 승인을 방지하고 상위 대표이사로 상향 승격되는지 검증"""
        # 팀장 본인을 기안자로 지정
        user_leader = User.objects.create_user(username='leader', email='leader@example.com')
        staff_leader = Staff.objects.create(
            company=self.company, user=user_leader, name='박팀장',
            position=self.pos_manager, id_number='800101-1234567', personal_phone='010-9999-8888',
            date_join='2021-01-01', status='1'
        )
        assign_leader = StaffAssignment.objects.create(
            staff=staff_leader, company=self.company, department=self.dept_team,
            duty=self.duty_team_leader, is_primary=True
        )

        # 팀장 전결 문서 유형 생성
        doc_type_tl = DocumentType.objects.create(
            category=self.category, name='팀장전결문서', code='TL_DOC',
            route_type=DocumentType.ROUTE_ORGANIZATION,
            final_approval_duty=self.duty_team_leader
        )

        # 팀장이 기안한 경우
        routes = build_dynamic_approval_route(
            doc_type=doc_type_tl,
            drafter_user=user_leader,
            drafter_assignment=assign_leader,
        )

        # 셀프 승인되지 않고 상위 대표이사 결재선으로 상향 승격되어야 함
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]['approver_ids'], [self.user_ceo.id])

    def test_ceo_drafter_returns_empty_routes_for_instant_approval(self):
        """단독/각자 대표이사가 직접 기안하는 경우 상신 즉시 완료를 위해 route_steps가 빈 리스트(0개)로 반환되는지 검증"""
        routes = build_dynamic_approval_route(
            doc_type=self.doc_type,
            drafter_user=self.user_ceo,
        )
        self.assertEqual(len(routes), 0)

    def test_joint_ceo_drafter_generates_and_step_for_other_ceos(self):
        """공동대표 체제에서 대표이사 A가 기안하는 경우, 기안자 본인은 제외되고 다른 공동대표 B가 AND 결재선으로 형성되는지 검증"""
        from company.models import Executive
        # 홍대표(ceo1)를 공동대표로 등록
        Executive.objects.create(
            company=self.company, staff=self.staff_ceo, represent_type='joint'
        )

        # 제2의 공동대표(ceo2) 등록
        user_ceo2 = User.objects.create_user(username='ceo2', email='ceo2@example.com')
        staff_ceo2 = Staff.objects.create(
            company=self.company, user=user_ceo2, name='이공동',
            position=self.pos_ceo, id_number='760101-1234567', personal_phone='010-7777-8888',
            date_join='2020-01-01', status='1'
        )
        StaffAssignment.objects.create(
            staff=staff_ceo2, company=self.company, department=self.dept_division,
            duty=self.duty_ceo, is_primary=True
        )
        Executive.objects.create(
            company=self.company, staff=staff_ceo2, represent_type='joint'
        )

        # 홍대표(ceo1)가 기안한 경우
        routes = build_dynamic_approval_route(
            doc_type=self.doc_type,
            drafter_user=self.user_ceo,
        )

        # 홍대표는 자동 승인되고, 이공동(ceo2)만 AND 최종 승인자로 결재선에 포함되어야 함
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]['approver_ids'], [user_ceo2.id])
        self.assertEqual(routes[0]['condition'], 'AND')
        self.assertEqual(routes[0]['role_label'], '공동대표 최종 승인')
