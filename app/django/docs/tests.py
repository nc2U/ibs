from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from company.models import Company
from company.models.organization import Department
from company.models.staff import Staff, StaffAssignment
from docs.models import Document, Category, OfficialLetter
from work.models.project import IssueProject, Member, Role, Permission

User = get_user_model()


class DocsAppSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 회사 생성
        self.company_a = Company.objects.create(name='테스트건설 A')
        self.company_b = Company.objects.create(name='테스트건설 B')

        # 사용자 생성
        self.admin_user = User.objects.create_superuser(
            username='admin_docs', email='admin@test.com', password='password123'
        )
        self.author_user = User.objects.create_user(
            username='author_docs', email='author@test.com', password='password123'
        )
        self.team_user = User.objects.create_user(
            username='team_docs', email='team@test.com', password='password123'
        )
        self.sales_user = User.objects.create_user(
            username='sales_docs', email='sales@test.com', password='password123'
        )
        self.granted_user = User.objects.create_user(
            username='granted_docs', email='granted@test.com', password='password123'
        )
        self.other_user = User.objects.create_user(
            username='other_docs', email='other@test.com', password='password123'
        )

        # 부서 및 Staff 생성 (Company A)
        self.dept_planning = Department.objects.create(company=self.company_a, name='기획팀')
        self.dept_sales = Department.objects.create(company=self.company_a, name='영업팀')

        # Staff 및 StaffAssignment 연결
        staff_author = Staff.objects.create(
            company=self.company_a, user=self.author_user, name='기획작성자',
            id_number='900101-1234567', personal_phone='010-1111-1111', date_join=date(2025, 1, 1)
        )
        StaffAssignment.objects.create(company=self.company_a, staff=staff_author, department=self.dept_planning, is_primary=True)

        staff_team = Staff.objects.create(
            company=self.company_a, user=self.team_user, name='기획팀원',
            id_number='900102-1234567', personal_phone='010-2222-2222', date_join=date(2025, 1, 1)
        )
        StaffAssignment.objects.create(company=self.company_a, staff=staff_team, department=self.dept_planning, is_primary=True)

        staff_sales = Staff.objects.create(
            company=self.company_a, user=self.sales_user, name='영업팀원',
            id_number='900103-1234567', personal_phone='010-3333-3333', date_join=date(2025, 1, 1)
        )
        StaffAssignment.objects.create(company=self.company_a, staff=staff_sales, department=self.dept_sales, is_primary=True)

        # Staff (Company B)
        staff_other = Staff.objects.create(
            company=self.company_b, user=self.other_user, name='타사직원',
            id_number='900104-1234567', personal_phone='010-4444-4444', date_join=date(2025, 1, 1)
        )

        # 권한 및 역할 생성
        self.perm_read = Permission.objects.create(module='docs', code='docs.read', name='문서 읽기')
        self.perm_create = Permission.objects.create(module='docs', code='docs.create', name='문서 등록')
        self.perm_update = Permission.objects.create(module='docs', code='docs.update', name='문서 수정')
        self.perm_delete = Permission.objects.create(module='docs', code='docs.delete', name='문서 삭제')

        self.role_staff = Role.objects.create(name='일반직원', creator=self.admin_user)
        self.role_staff.permissions.add(self.perm_read, self.perm_create, self.perm_update, self.perm_delete)

        # 워크스페이스 생성
        self.workspace = IssueProject.objects.create(
            company=self.company_a, name='문서 워크스페이스', slug='docs-ws', creator=self.admin_user
        )
        # 멤버십 등록 (author, team, sales, granted)
        for u in [self.author_user, self.team_user, self.sales_user, self.granted_user]:
            m = Member.objects.create(project=self.workspace, user=u)
            m.roles.add(self.role_staff)

        # 카테고리
        self.category = Category.objects.create(name='일반행정')

        # ── 4단계 보안 등급 문서 생성 ──
        # 1등급: 비공개
        self.doc_private = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='1등급 비공개 문서 (경영 비밀)',
            security_level=Document.SECURITY_PRIVATE,
            creator=self.author_user
        )
        self.doc_private.allowed_users.add(self.granted_user)

        # 2등급: 팀 공개
        self.doc_team = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='2등급 기획팀 공개 문서',
            security_level=Document.SECURITY_TEAM,
            creator=self.author_user
        )

        # 3등급: 프로젝트 공개
        self.doc_project = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='3등급 프로젝트 멤버 공개 문서',
            security_level=Document.SECURITY_PROJECT,
            creator=self.author_user
        )

        # 4등급: 전사 공개
        self.doc_company = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='4등급 전사 공개 규정집',
            security_level=Document.SECURITY_COMPANY,
            creator=self.author_user
        )

        # 블라인드 문서
        self.doc_blind = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='블라인드 처리된 문서',
            security_level=Document.SECURITY_COMPANY,
            is_blind=True,
            creator=self.author_user
        )

        # 공문 생성 (Company A)
        self.letter_a = OfficialLetter.objects.create(
            company=self.company_a,
            title='[공문] 사업계획 인가 승인 건',
            recipient_name='서울특별시청',
            sender_name='대표이사',
            content='사업계획 인가를 신청합니다.',
            issue_date=date(2026, 3, 1),
            creator=self.author_user
        )
        # 공문 생성 (Company B - document_number 명시하여 unique 제약조건 준수)
        self.letter_b = OfficialLetter.objects.create(
            company=self.company_b,
            document_number='2026-999',
            title='[타사공문] 제휴 제안',
            recipient_name='거래처 B',
            sender_name='대표이사 B',
            content='타사 공문 내용입니다.',
            issue_date=date(2026, 3, 1),
            creator=self.other_user
        )

    def test_document_security_level_1_private(self):
        """1등급 비공개: 작성자/명시적 허가자만 열람 가능, 일반 멤버 차단(403/404)"""
        # 작성자 본인 정상 조회 (200 OK)
        self.client.force_authenticate(user=self.author_user)
        res_author = self.client.get(f'/api/v1/docs/{self.doc_private.pk}/')
        self.assertEqual(res_author.status_code, status.HTTP_200_OK)

        # 명시적 허가자(allowed_users) 정상 조회 (200 OK)
        self.client.force_authenticate(user=self.granted_user)
        res_granted = self.client.get(f'/api/v1/docs/{self.doc_private.pk}/')
        self.assertEqual(res_granted.status_code, status.HTTP_200_OK)

        # 같은 팀원이라도 미허가자(team_user)는 상세 조회 차단 (403 Forbidden 또는 404 Not Found)
        self.client.force_authenticate(user=self.team_user)
        res_denied = self.client.get(f'/api/v1/docs/{self.doc_private.pk}/')
        self.assertIn(res_denied.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_document_security_level_2_team(self):
        """2등급 팀공개: 같은 부서원만 열람 가능, 타 부서원 차단(403/404)"""
        # 같은 기획팀 동료(team_user) 정상 조회 (200 OK)
        self.client.force_authenticate(user=self.team_user)
        res_team = self.client.get(f'/api/v1/docs/{self.doc_team.pk}/')
        self.assertEqual(res_team.status_code, status.HTTP_200_OK)

        # 다른 부서인 영업팀(sales_user)은 상세 조회 차단 (403 Forbidden 또는 404 Not Found)
        self.client.force_authenticate(user=self.sales_user)
        res_sales = self.client.get(f'/api/v1/docs/{self.doc_team.pk}/')
        self.assertIn(res_sales.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_document_security_level_3_and_4(self):
        """3등급 프로젝트 공개 및 4등급 전사 공개 열람 검증"""
        # 3등급: 워크스페이스 멤버(sales_user) 정상 조회
        self.client.force_authenticate(user=self.sales_user)
        res_proj = self.client.get(f'/api/v1/docs/{self.doc_project.pk}/')
        self.assertEqual(res_proj.status_code, status.HTTP_200_OK)

        # 3등급: 타 워크스페이스 사용자(other_user)는 차단 (403 Forbidden 또는 404 Not Found)
        self.client.force_authenticate(user=self.other_user)
        res_other = self.client.get(f'/api/v1/docs/{self.doc_project.pk}/')
        self.assertIn(res_other.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # 4등급: 워크스페이스 멤버면 전사 공개 문서 열람 가능
        self.client.force_authenticate(user=self.author_user)
        res_comp = self.client.get(f'/api/v1/docs/{self.doc_company.pk}/')
        self.assertEqual(res_comp.status_code, status.HTTP_200_OK)

    def test_blind_document_access_control(self):
        """블라인드 문서 일반 사용자 차단 및 관리자 열람 검증"""
        # 일반 멤버 조회 시 차단 (403 Forbidden 또는 404 Not Found)
        self.client.force_authenticate(user=self.author_user)
        res_blind = self.client.get(f'/api/v1/docs/{self.doc_blind.pk}/')
        self.assertIn(res_blind.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Superuser는 블라인드 문서 정상 열람 (200 OK)
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get(f'/api/v1/docs/{self.doc_blind.pk}/')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)

    def test_official_letter_company_isolation(self):
        """공문 회사별 격리 및 문서번호 채번 권한 검증"""
        # Company A 소속 직원은 Company A 공문만 조회 가능
        self.client.force_authenticate(user=self.author_user)
        res_list = self.client.get('/api/v1/official-letter/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        letter_ids = [item.get('pk') or item.get('id') for item in res_list.data.get('results', res_list.data)]
        self.assertIn(self.letter_a.pk, letter_ids)
        self.assertNotIn(self.letter_b.pk, letter_ids)

        # 타사 공문 번호 채번 요청 시 403 Forbidden 차단
        res_seq_forbidden = self.client.get(f'/api/v1/official-letter/next_document_number/?company={self.company_b.pk}')
        self.assertEqual(res_seq_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # 본인 회사 공문 번호 채번 요청 시 200 OK 및 번호 반환
        res_seq_ok = self.client.get(f'/api/v1/official-letter/next_document_number/?company={self.company_a.pk}')
        self.assertEqual(res_seq_ok.status_code, status.HTTP_200_OK)
        self.assertIn('next_document_number', res_seq_ok.data)
