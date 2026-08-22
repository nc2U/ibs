from django.test import TestCase
from django.contrib.auth import get_user_model
from company.models import Company, Department, Staff, StaffAssignment, Duty, Position
from approval.models import DocCategory, DocumentType
from approval.services.route_builder import build_dynamic_approval_route

User = get_user_model()


class ApprovalRouteBuilderTestCase(TestCase):
    """동일인 겸직 시 최상위 직함 승격(Highest Role Promotion) 검증 테스트"""

    def setUp(self):
        # 1. 회사 및 직급/직책 생성
        self.company = Company.objects.create(name='(주)대영아이비에스', is_default=True)
        self.pos_staff = Position.objects.create(company=self.company, name='사원', rank=1)
        self.pos_manager = Position.objects.create(company=self.company, name='팀장', rank=3)
        self.pos_ceo = Position.objects.create(company=self.company, name='대표이사', rank=10)

        self.duty_team_leader = Duty.objects.create(company=self.company, name='팀장', code='TL')
        self.duty_division_head = Duty.objects.create(company=self.company, name='본부장', code='DH')
        self.duty_ceo = Duty.objects.create(company=self.company, name='대표이사', code='CEO')

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
        self.staff_drafter = Staff.objects.create(company=self.company, user=self.user_drafter, name='김사원', status='1')
        self.assign_drafter = StaffAssignment.objects.create(
            staff=self.staff_drafter, company=self.company, department=self.dept_team,
            position=self.pos_staff, is_primary=True
        )

        # 대표이사 (경영지원팀장 겸직)
        self.user_ceo = User.objects.create_user(username='ceo', email='ceo@example.com')
        self.staff_ceo = Staff.objects.create(company=self.company, user=self.user_ceo, name='홍대표', status='1')
        # 대표이사 주보직
        StaffAssignment.objects.create(
            staff=self.staff_ceo, company=self.company, department=None,
            position=self.pos_ceo, duty=self.duty_ceo, is_primary=True
        )
        # 경영지원팀장 겸직
        StaffAssignment.objects.create(
            staff=self.staff_ceo, company=self.company, department=self.dept_team,
            position=self.pos_manager, duty=self.duty_team_leader, is_primary=False
        )

        # 4. 문서 유형 생성 (대표이사 최종 승인 방식)
        self.category = DocCategory.objects.create(name='일반품의')
        self.doc_type = DocumentType.objects.create(
            category=self.category, name='업무품의서', code='BIZ_APPROVAL',
            route_type=DocumentType.ROUTE_DYNAMIC
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
