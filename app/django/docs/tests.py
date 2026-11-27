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

        # 워크스페이스 생성 (type='1': 본사 관리 워크스페이스로 설정하여 IsStaffOrReadOnly 통과)
        self.workspace = IssueProject.objects.create(
            company=self.company_a, name='문서 워크스페이스', slug='docs-ws', type='1', creator=self.admin_user
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
            drafter_name='대표이사',
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
            drafter_name='대표이사 B',
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

    def test_document_copy_idor_blocked_and_allowed(self):
        """[T-5 / H-1] 타 프로젝트/권한 없는 비공개 문서 복사 시도 시 IDOR 차단(404) 및 권한 있는 문서의 정상 복제(201) 검증"""
        # 1. 권한이 없는 타 사용자(other_user)가 기획팀 전용 문서(self.doc_team) 복사 시도 -> 404 Not Found (self.get_object()에 의해 차단)
        self.client.force_authenticate(user=self.other_user)
        payload = {
            'issue_project': self.workspace.pk,
            'doc_type': '1',
        }

        res_copy_forbidden = self.client.post(f'/api/v1/docs/{self.doc_team.pk}/copy/', payload, format='json')
        self.assertIn(res_copy_forbidden.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

        # 2. 문서 권한이 있는 기획팀원(team_user)이 복사 시도 -> 201 Created 및 신규 문서 생성 완료
        self.client.force_authenticate(user=self.team_user)
        res_copy_ok = self.client.post(f'/api/v1/docs/{self.doc_team.pk}/copy/', payload, format='json')
        self.assertEqual(res_copy_ok.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_copy_ok.data['title'], self.doc_team.title)
        self.assertIn('복사됨', res_copy_ok.data['description'])


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

    def test_official_letter_solo_approval_instant_completion(self):
        """승인(전결)권자 직접 기안(is_solo_approval=True) 시 전자결재 즉시 최종 승인 처리 검증"""
        from approval.models import DocCategory, DocumentType, ApprovalDocument, ApprovalStep

        category = DocCategory.objects.create(name='공문카테고리', code='OFFICIAL_CAT')
        doc_type = DocumentType.objects.create(
            category=category,
            name='공문발송품의',
            code='OFFICIAL_LETTER_TYPE',
            form_template_key='OFFICIAL_LETTER',
            route_type=DocumentType.ROUTE_ORGANIZATION,
        )

        solo_letter = OfficialLetter.objects.create(
            company=self.company_a,
            document_number='2026-SOLO-001',
            title='[대표이사전결] 긴급 협약서 송부',
            recipient_name='한국토지주택공사',
            drafter_name='대표이사',
            content='긴급 협약서를 송부합니다.',
            issue_date=date(2026, 3, 1),
            is_solo_approval=True,
            creator=self.author_user
        )

        self.client.force_authenticate(user=self.author_user)
        res = self.client.post(f'/api/v1/official-letter/{solo_letter.pk}/submit_approval/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('즉시 최종 승인', res.data.get('detail', ''))

        solo_letter.refresh_from_db()
        self.assertEqual(solo_letter.approval_status, 'approved')
        self.assertIsNotNone(solo_letter.approval_document)

        app_doc = solo_letter.approval_document
        self.assertEqual(app_doc.status, ApprovalDocument.STATUS_APPROVED)
        self.assertIsNotNone(app_doc.completed_at)
        self.assertTrue(bool(app_doc.doc_number))

        # 승인된 Step이 1개 생성되었는지 검증
        self.assertEqual(app_doc.steps.count(), 1)
        step = app_doc.steps.first()
        self.assertEqual(step.status, ApprovalStep.STATUS_APPROVED)
        self.assertIn(self.author_user, step.approvers.all())

    def test_official_letter_markdown_pdf_generation(self):
        """마크다운 본문(표, 리스트, 강조)이 포함된 공문 PDF 생성 검증"""
        from docs.utils import generate_official_letter_pdf

        md_content = """
1. 귀 사의 무궁한 발전을 기원합니다.
2. 아래와 같이 일정 및 내역을 송부하오니 확인 바랍니다.

| 구분 | 품목 | 수량 | 비고 |
| :--- | :--- | :--- | :--- |
| 1 | 계약서 원본 | 1부 | 직인 날인 |
| 2 | 사업자등록증 | 1부 | 사본 |

* **특이사항**: 기한 내 회신 요망.
"""
        letter_md = OfficialLetter.objects.create(
            company=self.company_a,
            document_number='2026-MD-001',
            title='[공문] 마크다운 표 및 서식 송부 건',
            recipient_name='한국토지주택공사',
            drafter_name='담당자',
            content=md_content,
            issue_date=date(2026, 3, 1),
            creator=self.author_user
        )

        pdf_file = generate_official_letter_pdf(letter_md)
        self.assertIsNotNone(pdf_file)
        self.assertTrue(pdf_file.name.endswith('.pdf'))
        # PDF 파일 바이너리 내용 존재 확인
        self.assertGreater(len(pdf_file.read()), 1000)

    def test_dispatched_and_approved_letter_restrictions(self):
        """발송 완료 및 결재 승인된 공문의 수정/삭제 제한 검증"""
        from django.utils import timezone

        # 1. 발송 완료된 공문 (dispatched_at 설정)
        dispatched_letter = OfficialLetter.objects.create(
            company=self.company_a,
            document_number='2026-DISPATCHED-001',
            title='[발송완료] 회신 건',
            recipient_name='한국토지주택공사',
            drafter_name='담당자',
            content='발송 완료된 내용입니다.',
            issue_date=date(2026, 3, 1),
            dispatched_at=timezone.now(),
            creator=self.author_user
        )

        # 발송 완료 공문은 일반 사용자 및 관리자 모두 삭제/수정 차단 (400 Bad Request)
        self.client.force_authenticate(user=self.admin_user)
        res_del = self.client.delete(f'/api/v1/official-letter/{dispatched_letter.pk}/')
        self.assertEqual(res_del.status_code, status.HTTP_400_BAD_REQUEST)

        res_update = self.client.patch(f'/api/v1/official-letter/{dispatched_letter.pk}/', {'title': '임의수정'})
        self.assertEqual(res_update.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. 결재 승인된 공문 (approval_status='approved', 아직 미발송)
        approved_letter = OfficialLetter.objects.create(
            company=self.company_a,
            document_number='2026-APPROVED-001',
            title='[결재완료] 승인 건',
            recipient_name='한국토지주택공사',
            drafter_name='담당자',
            content='결재 승인된 내용입니다.',
            issue_date=date(2026, 3, 1),
            approval_status='approved',
            creator=self.author_user
        )

        # 일반 사용자는 수정/삭제 차단 (403 Forbidden)
        self.client.force_authenticate(user=self.author_user)
        res_author_del = self.client.delete(f'/api/v1/official-letter/{approved_letter.pk}/')
        self.assertEqual(res_author_del.status_code, status.HTTP_403_FORBIDDEN)

        res_author_up = self.client.patch(f'/api/v1/official-letter/{approved_letter.pk}/', {'title': '일반사용자수정'})
        self.assertEqual(res_author_up.status_code, status.HTTP_403_FORBIDDEN)

        # 관리자는 미발송 결재 승인 공문 수정 가능 (200 OK)
        self.client.force_authenticate(user=self.admin_user)
        res_admin_up = self.client.patch(f'/api/v1/official-letter/{approved_letter.pk}/', {'title': '관리자수정'})
        self.assertEqual(res_admin_up.status_code, status.HTTP_200_OK)

    def test_official_letter_filter_by_approval_status(self):
        """대외 공문 필터링(결재상태 및 발송완료) 검증"""
        from django.utils import timezone

        # 1. 발송완료 공문 (dispatched_at 존재)
        OfficialLetter.objects.create(
            company=self.company_a,
            document_number='2026-DISP-002',
            title='발송완료 공문',
            recipient_name='테스트수신처',
            drafter_name='담당자',
            content='내용',
            issue_date=date(2026, 3, 1),
            approval_status='approved',
            dispatched_at=timezone.now(),
            creator=self.author_user,
        )

        # 2. 결재진행중 공문
        OfficialLetter.objects.create(
            company=self.company_a,
            document_number='2026-PEND-001',
            title='결재대기 공문',
            recipient_name='테스트수신처',
            drafter_name='담당자',
            content='내용',
            issue_date=date(2026, 3, 1),
            approval_status='pending',
            creator=self.author_user,
        )

        self.client.force_authenticate(user=self.admin_user)

        # 발송완료 필터
        res_dispatched = self.client.get('/api/v1/official-letter/?approval_status=dispatched')
        self.assertEqual(res_dispatched.status_code, status.HTTP_200_OK)
        for item in res_dispatched.data['results']:
            self.assertIsNotNone(item['dispatched_at'])

        # 결재대기 필터
        res_pending = self.client.get('/api/v1/official-letter/?approval_status=pending')
        self.assertEqual(res_pending.status_code, status.HTTP_200_OK)
        for item in res_pending.data['results']:
            self.assertEqual(item['approval_status'], 'pending')

    def test_official_letter_download_pdf_auto_generates_when_missing(self):
        """PDF 파일이 없거나 스토리지에 유실된 경우 download_pdf 호출 시 자동 생성하여 반환하는지 검증"""
        letter_no_pdf = OfficialLetter.objects.create(
            company=self.company_a,
            document_number='2026-NOPDF-001',
            title='PDF 미생성 공문',
            recipient_name='테스트수신처',
            drafter_name='담당자',
            content='내용입니다.',
            issue_date=date(2026, 3, 1),
            creator=self.author_user,
        )

        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f'/api/v1/official-letter/{letter_no_pdf.pk}/download_pdf/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res['Content-Type'], 'application/pdf')
        letter_no_pdf.refresh_from_db()
        self.assertTrue(bool(letter_no_pdf.pdf_file))

    def test_docs_admin_query_optimization(self):
        """DocumentAdmin, OfficialLetterAdmin, InboundLetterAdmin의 select_related 최적화 검증 (추가 쿼리 0건)"""
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from docs.admin import DocumentAdmin, OfficialLetterAdmin, InboundLetterAdmin
        from docs.models import InboundLetter

        factory = RequestFactory()
        req = factory.get('/admin/')
        req.user = self.admin_user

        # 1. DocumentAdmin
        doc_admin = DocumentAdmin(Document, AdminSite())
        doc_qs = list(doc_admin.get_queryset(req).filter(pk=self.doc_project.pk))
        self.assertEqual(len(doc_qs), 1)
        with self.assertNumQueries(0):
            item = doc_qs[0]
            _ = item.issue_project.name
            _ = item.category.name

        # 2. OfficialLetterAdmin
        letter_admin = OfficialLetterAdmin(OfficialLetter, AdminSite())
        letter_qs = list(letter_admin.get_queryset(req).filter(pk=self.letter_a.pk))
        self.assertEqual(len(letter_qs), 1)
        with self.assertNumQueries(0):
            item = letter_qs[0]
            _ = item.company.name
            _ = item.creator.username

        # 3. InboundLetterAdmin
        inbound = InboundLetter.objects.create(
            company=self.company_a,
            document_number='IN-2026-001',
            sender_name='서울시 도시계획국',
            title='인가 접수 통지',
            creator=self.author_user,
            recipient_dept=self.dept_planning,
        )
        inbound_admin = InboundLetterAdmin(InboundLetter, AdminSite())
        inbound_qs = list(inbound_admin.get_queryset(req).filter(pk=inbound.pk))
        self.assertEqual(len(inbound_qs), 1)
        with self.assertNumQueries(0):
            item = inbound_qs[0]
            _ = item.company.name
            _ = item.recipient_dept.name

    def test_excel_export_views(self):
        """소송 사건 엑셀 내보내기(ExportSuitCases, ExportSuitCase) 200 응답 및 N+1 제거 검증"""
        from django.test import RequestFactory
        from docs.models import LawsuitCase
        from docs.exports.excel import ExportSuitCases, ExportSuitCase

        parent_case = LawsuitCase.objects.create(
            issue_project=self.workspace,
            sort='1',
            level='1',
            case_number='2025가합1234',
            case_name='공사대금 청구의 소',
            plaintiff='원고1',
            defendant='피고1',
            case_start_date=date(2025, 1, 1),
            creator=self.author_user,
        )
        child_case = LawsuitCase.objects.create(
            issue_project=self.workspace,
            sort='1',
            level='2',
            related_case=parent_case,
            case_number='2026나5678',
            case_name='공사대금 항소심',
            plaintiff='원고1',
            defendant='피고1',
            case_start_date=date(2026, 1, 1),
            creator=self.author_user,
        )

        factory = RequestFactory()

        # 1. ExportSuitCases (목록 엑셀)
        req_list = factory.get(f'/docs/export/suit-cases/?company={self.company_a.pk}')
        req_list.user = self.admin_user
        res_list = ExportSuitCases().get(req_list)
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(res_list['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertGreater(len(res_list.content), 1000)

        # 2. ExportSuitCase (단건 디테일 엑셀)
        req_detail = factory.get(f'/docs/export/suit-case/?pk={child_case.pk}')
        req_detail.user = self.admin_user
        res_detail = ExportSuitCase().get(req_detail)
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(res_detail['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertGreater(len(res_detail.content), 1000)

    def test_excel_export_security_and_rls(self):
        """소송 사건 엑셀 내보내기 권한 및 RLS 차단 검증"""
        from django.test import RequestFactory
        from docs.models import LawsuitCase
        from docs.exports.excel import ExportSuitCases, ExportSuitCase

        case_a = LawsuitCase.objects.create(
            issue_project=self.workspace,
            sort='1',
            level='1',
            case_number='2026가합9999',
            case_name='기밀 소송 사건',
            plaintiff='원고A',
            defendant='피고A',
            case_start_date=date(2026, 1, 1),
            creator=self.author_user,
        )

        factory = RequestFactory()

        # 1. 미인증 사용자 접근 시 401
        req_anon = factory.get(f'/docs/export/suit-case/?pk={case_a.pk}')
        res_anon = ExportSuitCase().get(req_anon)
        self.assertEqual(res_anon.status_code, 401)

        # 2. 타사/미인가 사용자(other_user)가 타 프로젝트 소송 단건 엑셀 접근 시 403 차단
        req_forbidden = factory.get(f'/docs/export/suit-case/?pk={case_a.pk}')
        req_forbidden.user = self.other_user
        res_forbidden = ExportSuitCase().get(req_forbidden)
        self.assertEqual(res_forbidden.status_code, 403)

        # 3. 잘못된 회사/프로젝트 ID 전달 시 500 크래시 없이 404 반환
        req_invalid_com = factory.get('/docs/export/suit-cases/?company=999999')
        req_invalid_com.user = self.admin_user
        res_invalid_com = ExportSuitCases().get(req_invalid_com)
        self.assertEqual(res_invalid_com.status_code, 404)

    def test_trash_document_permanent_delete_restrictions(self):
        """휴지통 문서 영구 삭제 시 작성자 및 관리자만 허용 검증"""
        doc_to_delete = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='휴지통 삭제 대상 문서',
            security_level=Document.SECURITY_COMPANY,
            creator=self.author_user
        )
        doc_to_delete.soft_delete()

        # 1. 작성자가 아닌 일반 직원(sales_user)이 영구 삭제 시도 -> 403 Forbidden
        self.client.force_authenticate(user=self.sales_user)
        res_denied = self.client.delete(f'/api/v1/docs-trash-can/{doc_to_delete.pk}/')
        self.assertEqual(res_denied.status_code, status.HTTP_403_FORBIDDEN)

        # 2. 작성자 본인(author_user)이 영구 삭제 시도 -> 204 No Content
        self.client.force_authenticate(user=self.author_user)
        res_ok = self.client.delete(f'/api/v1/docs-trash-can/{doc_to_delete.pk}/')
        self.assertEqual(res_ok.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.all_objects.filter(pk=doc_to_delete.pk).exists())

    def test_official_and_inbound_letter_attachment_security(self):
        """공문 및 수신공문 첨부파일 뷰셋의 회사별 RLS 및 발송/종결 후 수정/삭제 제한 검증"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.utils import timezone
        from docs.models import OfficialLetterAttachment, InboundLetter, InboundLetterAttachment

        # 1. Company A 공문 첨부파일
        dummy_file = SimpleUploadedFile("sample.txt", b"test attachment content")
        att_a = OfficialLetterAttachment.objects.create(
            letter=self.letter_a,
            file=dummy_file,
            name='설계도면_초안'
        )

        # Company B 워크스페이스 생성 및 other_user에게 docs.read 권한 부여
        workspace_b = IssueProject.objects.create(
            company=self.company_b, name='B사 워크스페이스', slug='ws-b-test', type='1', creator=self.admin_user
        )
        mb = Member.objects.create(project=workspace_b, user=self.other_user)
        mb.roles.add(self.role_staff)

        # 타사 사용자(other_user)는 조회 시 본인 회사 첨부파일만 조회되며 타사 파일은 격리됨
        self.client.force_authenticate(user=self.other_user)
        res_list = self.client.get('/api/v1/official-letter-attachment/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in res_list.data.get('results', res_list.data)]
        self.assertNotIn(att_a.id, ids)

        # 타사 공문(letter_a)에 첨부파일 업로드 시도 시 403 차단
        dummy_upload = SimpleUploadedFile("malicious.txt", b"hack")
        res_cross_upload = self.client.post(
            '/api/v1/official-letter-attachment/',
            {'letter': self.letter_a.pk, 'file': dummy_upload, 'name': '악성첨부'}
        )
        self.assertEqual(res_cross_upload.status_code, status.HTTP_403_FORBIDDEN)

        # 2. 이미 발송 완료된 공문(dispatched_at)의 첨부파일은 추가/삭제 금지
        self.letter_a.dispatched_at = timezone.now()
        self.letter_a.save(update_fields=['dispatched_at'])

        self.client.force_authenticate(user=self.author_user)
        res_del = self.client.delete(f'/api/v1/official-letter-attachment/{att_a.id}/')
        self.assertEqual(res_del.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. 종결 처리된 수신공문(status='closed')의 첨부파일 삭제 금지
        inbound = InboundLetter.objects.create(
            company=self.company_a,
            document_number='IN-CLOSED-1',
            sender_name='시청',
            title='종결 공문',
            status='closed',
            creator=self.author_user,
        )
        dummy_file2 = SimpleUploadedFile("inbound.txt", b"inbound attachment")
        att_inbound = InboundLetterAttachment.objects.create(
            letter=inbound,
            file=dummy_file2,
            name='접수증'
        )
        res_inbound_del = self.client.delete(f'/api/v1/inbound-letter-attachment/{att_inbound.id}/')
        self.assertEqual(res_inbound_del.status_code, status.HTTP_400_BAD_REQUEST)

    def test_model_cross_tenant_and_integrity_validations(self):
        """모델 clean() 수준의 크로스 테넌트 및 정합성 검증"""
        from django.core.exceptions import ValidationError
        from company.models import CompanySeal
        from docs.models import LawsuitCase

        # 1. 인감과 공문의 회사가 다른 경우 ValidationError
        seal_b = CompanySeal.objects.create(
            company=self.company_b,
            name='회사B 법인인감',
            seal_type='1'
        )
        with self.assertRaises(ValidationError):
            letter_invalid_seal = OfficialLetter(
                company=self.company_a,
                title='잘못된 인감 공문',
                recipient_name='수신처',
                drafter_name='담당자',
                content='내용',
                issue_date=date(2026, 3, 1),
                seal=seal_b
            )
            letter_invalid_seal.full_clean()

        # 2. 소송 사건 자기참조 불가 ValidationError
        case = LawsuitCase.objects.create(
            issue_project=self.workspace,
            sort='1',
            level='1',
            case_number='2026가합1111',
            case_name='원심 사건',
            plaintiff='원고',
            defendant='피고',
            case_start_date=date(2026, 1, 1),
            creator=self.author_user,
        )
        case.related_case = case
        with self.assertRaises(ValidationError):
            case.clean()

        # 3. 문서와 소송 사건의 프로젝트 불일치 시 ValidationError
        workspace_b = IssueProject.objects.create(
            company=self.company_b, name='B프로젝트', slug='ws-b', type='1', creator=self.admin_user
        )
        with self.assertRaises(ValidationError):
            doc_mismatched = Document(
                issue_project=workspace_b,
                category=self.category,
                title='프로젝트 불일치 문서',
                lawsuit=case,
                creator=self.author_user
            )
            doc_mismatched.clean()

    def test_document_copy_to_unauthorized_workspace_blocked(self):
        """권한 없는 대상 워크스페이스로 문서 복사 시도 시 403 Forbidden 차단 검증"""
        workspace_other = IssueProject.objects.create(
            company=self.company_b, name='타사 비공개 워크스페이스', slug='ws-other-locked', type='1', is_public=False, creator=self.admin_user
        )

        self.client.force_authenticate(user=self.author_user)
        payload = {
            'issue_project': workspace_other.pk,
            'doc_type': '1',
        }
        res_copy = self.client.post(f'/api/v1/docs/{self.doc_company.pk}/copy/', payload, format='json')
        self.assertEqual(res_copy.status_code, status.HTTP_403_FORBIDDEN)

    def test_document_json_links_creation(self):
        """JSON 요청으로 새 문서 등록 시 newLinks 목록이 정상 생성되는지 검증"""
        self.client.force_authenticate(user=self.author_user)
        payload = {
            'issue_project': self.workspace.pk,
            'doc_type': '1',
            'category': self.category.pk,
            'title': 'JSON 링크 등록 테스트',
            'description': '링크 포함 문서',
            'newLinks': ['https://google.com', 'naver.com']
        }
        res = self.client.post('/api/v1/docs/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_doc_id = res.data['pk']
        doc = Document.objects.get(pk=new_doc_id)
        self.assertEqual(doc.links.count(), 2)
        urls = [link.link for link in doc.links.all()]
        self.assertIn('https://google.com', urls)
        self.assertIn('https://naver.com', urls)

    def test_inbound_letter_d_day_and_workflow(self):
        """수신 공문 D-Day 산출, API 조회 및 전자결재 연동 워크플로우 검증"""
        from datetime import timedelta
        from django.utils import timezone
        from docs.models import InboundLetter

        today = timezone.localdate()
        inbound = InboundLetter.objects.create(
            company=self.company_a,
            document_number='GOV-2026-99',
            sender_name='국토교통부',
            title='사업계획 보완요청 통보',
            received_date=today,
            reply_due_date=today + timedelta(days=7),
            creator=self.author_user,
        )
        self.assertEqual(inbound.d_day, 7)

        # API 조회 검증
        self.client.force_authenticate(user=self.author_user)
        res_list = self.client.get('/api/v1/inbound-letter/')
        self.assertEqual(res_list.status_code, 200)
        results = res_list.data.get('results', res_list.data)
        self.assertTrue(any(item.get('receipt_number') == inbound.receipt_number for item in results))

        # 채번 조회 검증
        res_num = self.client.get(f'/api/v1/inbound-letter/next_receipt_number/?company={self.company_a.pk}')
        self.assertEqual(res_num.status_code, 200)
        self.assertIn('next_receipt_number', res_num.data)

    def test_document_link_update_idor_blocked(self):
        """문서 수정 시 타 문서 소속 Link PK를 전달해 변조/삭제 시도할 경우 IDOR 차단 검증"""
        from docs.models import Link

        target_link = Link.objects.create(
            docs=self.doc_company,
            link='https://safe-original.com',
            creator=self.author_user,
        )
        my_doc = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='내 문서',
            security_level=Document.SECURITY_COMPANY,
            creator=self.team_user,
        )

        self.client.force_authenticate(user=self.team_user)
        # 본인 문서(my_doc)를 수정하면서 타 문서(doc_company)의 링크 삭제/변조 시도
        res = self.client.patch(
            f'/api/v1/docs/{my_doc.pk}/',
            {
                'title': '내 문서 수정',
                'links': [
                    {'pk': target_link.pk, 'link': 'https://hacked.example.com'},
                ],
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        target_link.refresh_from_db()
        self.assertEqual(target_link.link, 'https://safe-original.com')

    def test_document_own_update_and_delete_permissions(self):
        """docs.own_update / docs.own_delete 권한만 보유한 경우 본인 문서만 수정/삭제 가능하고 타인 문서는 403 차단 검증"""
        perm_own_up = Permission.objects.create(module='docs', code='docs.own_update', name='본인 문서 수정')
        perm_own_del = Permission.objects.create(module='docs', code='docs.own_delete', name='본인 문서 삭제')
        role_own_only = Role.objects.create(name='본인문서전용역할', creator=self.admin_user)
        role_own_only.permissions.add(self.perm_read, self.perm_create, perm_own_up, perm_own_del)

        own_user = User.objects.create_user(username='own_only_user', email='own@test.com', password='password123')
        m = Member.objects.create(project=self.workspace, user=own_user)
        m.roles.add(role_own_only)

        own_doc = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='본인 작성 문서',
            security_level=Document.SECURITY_COMPANY,
            creator=own_user,
        )

        self.client.force_authenticate(user=own_user)
        # 1. 타인(author_user)이 작성한 문서 수정/삭제 시도 -> 403 Forbidden
        res_other_up = self.client.patch(f'/api/v1/docs/{self.doc_company.pk}/', {'title': '타인문서변조'}, format='json')
        self.assertEqual(res_other_up.status_code, status.HTTP_403_FORBIDDEN)
        res_other_del = self.client.delete(f'/api/v1/docs/{self.doc_company.pk}/')
        self.assertEqual(res_other_del.status_code, status.HTTP_403_FORBIDDEN)

        # 2. 본인(own_user)이 작성한 문서 수정/삭제 시도 -> 200 OK / 204 No Content
        res_own_up = self.client.patch(f'/api/v1/docs/{own_doc.pk}/', {'title': '본인문서정상수정'}, format='json')
        self.assertEqual(res_own_up.status_code, status.HTTP_200_OK)
        res_own_del = self.client.delete(f'/api/v1/docs/{own_doc.pk}/')
        self.assertEqual(res_own_del.status_code, status.HTTP_204_NO_CONTENT)

    def test_trash_document_restore_and_create_restrictions(self):
        """휴지통 직접 생성(POST) 405 차단 및 복원(PATCH) 시 작성자/관리자만 허용 검증"""
        trashed_doc = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='복원 테스트 문서',
            security_level=Document.SECURITY_COMPANY,
            creator=self.author_user,
        )
        trashed_doc.soft_delete()

        # 1. 휴지통 POST 생성 시도 -> 405 Method Not Allowed
        self.client.force_authenticate(user=self.admin_user)
        res_create = self.client.post('/api/v1/docs-trash-can/', {'title': '불법생성'}, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # 2. 작성자가 아닌 일반 멤버(sales_user)가 복원 시도 -> 403 Forbidden
        self.client.force_authenticate(user=self.sales_user)
        res_restore_denied = self.client.patch(f'/api/v1/docs-trash-can/{trashed_doc.pk}/', {}, format='json')
        self.assertEqual(res_restore_denied.status_code, status.HTTP_403_FORBIDDEN)

        # 3. 작성자 본인(author_user)이 복원 시도 -> 200 OK 및 정상 복구
        self.client.force_authenticate(user=self.author_user)
        res_restore_ok = self.client.patch(f'/api/v1/docs-trash-can/{trashed_doc.pk}/', {}, format='json')
        self.assertEqual(res_restore_ok.status_code, status.HTTP_200_OK)
        self.assertTrue(Document.objects.filter(pk=trashed_doc.pk).exists())

    def test_inbound_letter_closed_and_approval_restrictions(self):
        """종결 처리된 수신 공문의 수정/삭제 차단 검증"""
        from docs.models import InboundLetter

        closed_inbound = InboundLetter.objects.create(
            company=self.company_a,
            document_number='IN-CLOSE-99',
            sender_name='서울시청',
            title='종결된 수신 공문',
            status='closed',
            creator=self.author_user,
        )

        # 일반 사용자: 종결된 수신 공문 수정/삭제 모두 400 차단
        self.client.force_authenticate(user=self.author_user)
        res_up = self.client.patch(f'/api/v1/inbound-letter/{closed_inbound.pk}/', {'title': '임의변조'}, format='json')
        self.assertEqual(res_up.status_code, status.HTTP_400_BAD_REQUEST)

        res_del = self.client.delete(f'/api/v1/inbound-letter/{closed_inbound.pk}/')
        self.assertEqual(res_del.status_code, status.HTTP_400_BAD_REQUEST)

    def test_model_cycle_and_date_inversion_validations(self):
        """Category/LawsuitCase 순환 참조 및 LawsuitCase/InboundLetter 일자 역전 검증"""
        from django.core.exceptions import ValidationError
        from docs.models import LawsuitCase, InboundLetter

        # 1. Category 순환 참조 (A -> B -> A)
        cat_a = Category.objects.create(name='상위카테고리')
        cat_b = Category.objects.create(name='하위카테고리', parent=cat_a)
        cat_a.parent = cat_b
        with self.assertRaises(ValidationError):
            cat_a.clean()

        # 2. LawsuitCase 일자 역전 (case_start_date > case_end_date)
        with self.assertRaises(ValidationError):
            bad_case = LawsuitCase(
                issue_project=self.workspace,
                sort='1',
                level='1',
                case_number='2026가합0001',
                case_name='일자역전사건',
                defendant='피고',
                case_start_date=date(2026, 5, 10),
                case_end_date=date(2026, 5, 1),
            )
            bad_case.clean()

        # 3. InboundLetter 일자 역전 (received_date > reply_due_date)
        with self.assertRaises(ValidationError):
            bad_inbound = InboundLetter(
                company=self.company_a,
                sender_name='발신처',
                title='일자역전공문',
                received_date=date(2026, 5, 10),
                reply_due_date=date(2026, 5, 1),
            )
            bad_inbound.clean()

    def test_pending_official_letter_delete_blocked_and_resubmit_reuses_doc(self):
        """결재 진행 중(pending) 발송 공문 삭제 차단 및 회수/반려 후 재상신 시 기존 ApprovalDocument 재사용 검증"""
        from approval.models import DocCategory, DocumentType, ApprovalDocument

        category = DocCategory.objects.create(name='공문카테고리_재상신', code='OL_REUSE_CAT')
        DocumentType.objects.create(
            category=category,
            name='공문발송품의',
            code='OL_REUSE_TYPE',
            form_template_key='OFFICIAL_LETTER',
            route_type=DocumentType.ROUTE_ORGANIZATION,
        )

        # 1. pending 상태 삭제 시도 -> 400 차단
        pending_letter = OfficialLetter.objects.create(
            company=self.company_a,
            document_number='2026-PEND-DEL-001',
            title='결재중 삭제 금지 공문',
            recipient_name='수신처',
            drafter_name='담당자',
            content='내용',
            issue_date=date(2026, 3, 1),
            approval_status='pending',
            creator=self.author_user,
        )
        self.client.force_authenticate(user=self.admin_user)
        res_del = self.client.delete(f'/api/v1/official-letter/{pending_letter.pk}/')
        self.assertEqual(res_del.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(OfficialLetter.objects.filter(pk=pending_letter.pk).exists())

        # 2. 반려/회수 상태 기존 ApprovalDocument가 있는 공문 재상신 시 기존 문서 재사용
        old_doc = ApprovalDocument.objects.create(
            title='이전 결재문서',
            doc_type=DocumentType.objects.get(code='OL_REUSE_TYPE'),
            drafter=self.author_user,
            status=ApprovalDocument.STATUS_REJECTED,
            content={'official_letter_id': self.letter_a.pk},
            content_hash='legacy',
        )
        self.letter_a.approval_document = old_doc
        self.letter_a.approval_status = 'rejected'
        self.letter_a.is_solo_approval = True
        self.letter_a.save(update_fields=['approval_document', 'approval_status', 'is_solo_approval'])

        self.client.force_authenticate(user=self.author_user)
        res_resubmit = self.client.post(f'/api/v1/official-letter/{self.letter_a.pk}/submit_approval/')
        self.assertEqual(res_resubmit.status_code, status.HTTP_200_OK)
        self.letter_a.refresh_from_db()
        self.assertEqual(self.letter_a.approval_document_id, old_doc.pk)
        self.assertEqual(
            ApprovalDocument.objects.filter(content__official_letter_id=self.letter_a.pk).count(),
            1,
        )

    def test_inbound_letter_clear_scan_file_via_update(self):
        """수신 공문 수정 시 clear_scan_file 플래그로 기존 스캔본 제거 검증"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from docs.models import InboundLetter

        inbound = InboundLetter.objects.create(
            company=self.company_a,
            document_number='IN-SCAN-001',
            sender_name='서울시청',
            title='스캔 제거 테스트',
            scan_file=SimpleUploadedFile('origin.pdf', b'%PDF-1.4 test'),
            creator=self.author_user,
        )
        self.assertTrue(bool(inbound.scan_file))

        self.client.force_authenticate(user=self.author_user)
        res = self.client.patch(
            f'/api/v1/inbound-letter/{inbound.pk}/',
            {'clear_scan_file': 'true'},
            format='multipart',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        inbound.refresh_from_db()
        self.assertFalse(bool(inbound.scan_file))

    def test_excel_export_docs_read_permission_and_related_case_filter(self):
        """엑셀 내보내기 시 docs.read 권한 검증 및 related_case/미지정 타이틀 처리 검증"""
        from django.test import RequestFactory
        from docs.models import LawsuitCase
        from docs.exports.excel import ExportSuitCases, ExportSuitCase

        role_no_docs = Role.objects.create(name='이슈전용역할', creator=self.admin_user)
        user_no_docs = User.objects.create_user(
            username='issue_only_excel', email='nodocs@test.com', password='password123'
        )
        m = Member.objects.create(project=self.workspace, user=user_no_docs)
        m.roles.add(role_no_docs)

        case_parent = LawsuitCase.objects.create(
            issue_project=self.workspace,
            sort='1',
            level='1',
            case_number='2026가합100',
            case_name='본안 소송',
            plaintiff='원고1',
            defendant='피고1',
            case_start_date=date(2026, 1, 1),
            creator=self.author_user,
        )
        LawsuitCase.objects.create(
            issue_project=self.workspace,
            sort='4',
            level='5',
            related_case=case_parent,
            case_number='2026카합200',
            case_name='신청 사건',
            plaintiff='원고1',
            defendant='피고1',
            case_start_date=date(2026, 2, 1),
            creator=self.author_user,
        )

        factory = RequestFactory()
        # 1. 멤버지만 docs.read가 없는 사용자는 단건 엑셀 403 차단
        req_no_perm = factory.get(f'/excel/suitcase/?pk={case_parent.pk}')
        req_no_perm.user = user_no_docs
        res_no_perm = ExportSuitCase().get(req_no_perm)
        self.assertEqual(res_no_perm.status_code, 403)

        # 2. company/project 미지정 + related_case 필터 목록 엑셀 정상 200
        req_filter = factory.get(f'/excel/suitcases/?related_case={case_parent.pk}')
        req_filter.user = self.author_user
        res_filter = ExportSuitCases().get(req_filter)
        self.assertEqual(res_filter.status_code, 200)
        self.assertGreater(len(res_filter.content), 1000)

    def test_document_copy_truncates_long_description_to_255(self):
        """본문이 255자에 가까운 문서를 복사해도 400 max_length 오류 없이 201 반환 검증"""
        long_doc = Document.objects.create(
            issue_project=self.workspace,
            category=self.category,
            title='긴 본문 복사 테스트',
            description='가' * 240,
            security_level=Document.SECURITY_PROJECT,
            creator=self.author_user,
        )
        self.client.force_authenticate(user=self.author_user)
        res = self.client.post(
            f'/api/v1/docs/{long_doc.pk}/copy/',
            {'issue_project': self.workspace.pk, 'doc_type': 1},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertLessEqual(len(res.data['description']), 255)
        self.assertIn('복사됨', res.data['description'])
