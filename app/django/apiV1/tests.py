from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from work.models.meeting import Meeting, MeetingCategory, MeetingFile
from work.models.project import IssueProject
from company.models import Company
from apiV1.serializers.work.meeting import MeetingSerializer

User = get_user_model()

class MeetingSerializerTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.company = Company.objects.create(name='Test Company')
        self.project = IssueProject.objects.create(
            company=self.company,
            name='Test Project',
            slug='test-project',
            creator=self.user
        )
        self.category = MeetingCategory.objects.create(
            project=self.project,
            name='Regular Meeting',
            color='#FF0000',
            order=1
        )

    def test_meeting_creation_with_files(self):
        # Create request context
        request = self.factory.post('/')
        request.user = self.user
        
        # Prepare data
        file_content = b"file content"
        test_file = SimpleUploadedFile("test.txt", file_content)
        
        data = {
            'project': self.project.pk,
            'category': self.category.pk,
            'title': 'Test Meeting',
            'meeting_date': '2026-06-28T10:00:00Z',
        }
        
        serializer = MeetingSerializer(data=data, context={'request': request})
        
        from django.http import QueryDict
        qdict = QueryDict('', mutable=True)
        qdict.update(data)
        qdict.appendlist('new_files', test_file)
        qdict.appendlist('descriptions', 'Test description')
        
        serializer.initial_data = qdict
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Manually set creator as the view normally does
        meeting = serializer.save(creator=self.user)
        
        self.assertEqual(Meeting.objects.count(), 1)
        self.assertEqual(meeting.title, 'Test Meeting')
        self.assertEqual(meeting.creator, self.user)
        self.assertEqual(MeetingFile.objects.filter(meeting=meeting).count(), 1)
        self.assertEqual(MeetingFile.objects.first().description, 'Test description')

    def test_meeting_update_file_logic(self):
        # Setup existing meeting with file
        meeting = Meeting.objects.create(
            project=self.project,
            category=self.category,
            title='Old Title',
            creator=self.user
        )
        
        old_file_content = b"old content"
        old_file = SimpleUploadedFile("old.txt", old_file_content)
        meeting_file = MeetingFile.objects.create(
            meeting=meeting,
            file=old_file,
            creator=self.user
        )
        
        # Update request
        request = self.factory.put('/')
        request.user = self.user
        
        # Prepare data for update
        data = {
            'title': 'New Title',
        }
        
        from django.http import QueryDict
        qdict = QueryDict('', mutable=True)
        qdict.update(data)
        
        # Simulate deleting the old file and adding a new one
        file_json = f'{{"pk": {meeting_file.pk}, "del": true}}'
        qdict.appendlist('files', file_json)
        
        new_file = SimpleUploadedFile("new.txt", b"new content")
        qdict.appendlist('new_files', new_file)
        qdict.appendlist('descriptions', 'New description')
        
        serializer = MeetingSerializer(instance=meeting, data=qdict, partial=True, context={'request': request})
        serializer.initial_data = qdict
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_meeting = serializer.save(updater=self.user)
        
        self.assertEqual(updated_meeting.title, 'New Title')
        
        # Check files
        files = MeetingFile.objects.filter(meeting=updated_meeting)
        self.assertEqual(files.count(), 1)
        # Check that the file was created (the name is renamed by Django)
        self.assertTrue(files.first().file.name.endswith('.txt'))


from rest_framework.test import APIClient
from project.models import Project, SiteOwner, SiteContract, SiteContractFile


class SiteContractAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='site_testuser', password='password', is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.company = Company.objects.create(name='Test Company 2')
        self.issue_project = IssueProject.objects.create(
            company=self.company,
            name='Test Project 2',
            slug='test-project-2',
            creator=self.user,
        )
        self.project = Project.objects.create(
            issue_project=self.issue_project,
            name='Test Project 2',
            kind='2',
            start_year=2026,
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24,
        )
        self.owner = SiteOwner.objects.create(
            project=self.project,
            owner='홍길동',
            phone1='010-1234-5678',
        )

    def test_create_site_contract_with_multiple_files(self):
        file1 = SimpleUploadedFile("contract_main.pdf", b"pdf content 1")
        file2 = SimpleUploadedFile("id_card.png", b"png content 2")
        file3 = SimpleUploadedFile("bank_book.pdf", b"pdf content 3")

        data = {
            'project': self.project.pk,
            'owner': self.owner.pk,
            'contract_date': '2026-06-01',
            'total_price': 500000000,
            'contract_area': 330.5,
            'acc_bank': '국민은행',
            'acc_number': '123-456-789',
            'acc_owner': '홍길동',
            'new_files': [file1, file2, file3],
        }
        response = self.client.post('/api/v1/site-contract/', data, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)

        self.assertEqual(SiteContract.objects.count(), 1)
        contract = SiteContract.objects.first()
        self.assertEqual(contract.site_cont_files.count(), 3)
        file_names = list(contract.site_cont_files.values_list('file_name', flat=True))
        self.assertIn('contract_main.pdf', file_names)
        self.assertIn('id_card.png', file_names)
        self.assertIn('bank_book.pdf', file_names)

    def test_update_site_contract_add_and_delete_files(self):
        contract = SiteContract.objects.create(
            project=self.project,
            owner=self.owner,
            contract_date='2026-06-01',
            total_price=500000000,
            contract_area=330.5,
            creator=self.user,
        )
        file_a = SiteContractFile.objects.create(
            site_contract=contract,
            file=SimpleUploadedFile("file_a.pdf", b"content a"),
            creator=self.user,
        )
        file_b = SiteContractFile.objects.create(
            site_contract=contract,
            file=SimpleUploadedFile("file_b.pdf", b"content b"),
            creator=self.user,
        )
        self.assertEqual(contract.site_cont_files.count(), 2)

        file_new = SimpleUploadedFile("file_c.pdf", b"content c")
        update_data = {
            'note': '업데이트된 비고',
            'del_files': [file_a.pk],
            'new_files': [file_new],
        }
        response = self.client.patch(f'/api/v1/site-contract/{contract.pk}/', update_data, format='multipart')
        self.assertEqual(response.status_code, 200, response.data)

        contract.refresh_from_db()
        self.assertEqual(contract.note, '업데이트된 비고')
        # file_a가 삭제되고 file_c가 추가되어 총 2개 (file_b, file_c)
        remaining_files = contract.site_cont_files.all()
        self.assertEqual(remaining_files.count(), 2)
        remaining_names = list(remaining_files.values_list('file_name', flat=True))
        self.assertNotIn('file_a.pdf', remaining_names)
        self.assertIn('file_b.pdf', remaining_names)
        self.assertIn('file_c.pdf', remaining_names)


from company.models import Department, Staff, Position, JobGrade
from work.models.project import Member, Role, Permission
from ledger.models import CompanyBankAccount, BankCode, CompanyAccount, CompanyBankTransaction
from ibs.models import AccountSort


class HqPermissionPolicyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name='본사 법인')

        # 입출금 구분
        self.sort_expense = AccountSort.objects.create(name='출금')

        # 본사 워크스페이스 생성 (type='1')
        self.hq_admin = User.objects.create_user(username='hq_admin', email='hq_admin@example.com', password='password')
        self.hq_ip = IssueProject.objects.create(
            company=self.company,
            name='본사 관리 워크스페이스',
            slug='hq-workspace',
            type='1',
            creator=self.hq_admin,
        )

        # 부서 및 직급
        self.department = Department.objects.create(company=self.company, name='재경부')
        self.position = Position.objects.create(company=self.company, name='과장')
        self.grade = JobGrade.objects.create(company=self.company, code='G3')

        # 은행 계좌 및 기초 회계 계정
        self.bank_code = BankCode.objects.create(code='004', name='국민은행')
        self.bank_account = CompanyBankAccount.objects.create(
            company=self.company,
            depart=self.department,
            bankcode=self.bank_code,
            alias_name='본사 운영계좌',
            number='111-222-3333',
        )
        self.account = CompanyAccount.objects.create(
            name='지급수수료',
            code='8001',
            category='expense',
            is_active=True,
            is_category_only=False
        )

        # HQ 회계 권한 및 역할 세팅
        self.perm_ledger_read, _ = Permission.objects.get_or_create(
            code='hq.ledger.read',
            defaults={'name': '본사 회계 조회'}
        )
        self.perm_ledger_create, _ = Permission.objects.get_or_create(
            code='hq.ledger.create',
            defaults={'name': '본사 회계 등록'}
        )

        self.hq_role = Role.objects.create(name='HQ 회계담당', category='ibs_hq_manage', creator=self.hq_admin)
        self.hq_role.permissions.add(self.perm_ledger_read, self.perm_ledger_create)

        # 사용자 생성 (권한은 있지만 Staff는 아직 미등록)
        self.accountant_user = User.objects.create_user(username='accountant_user', email='accountant@example.com', password='password')
        member = Member.objects.create(project=self.hq_ip, user=self.accountant_user)
        member.roles.add(self.hq_role)

    def test_hq_read_allowed_without_staff(self):
        """HQ 회계 권한이 있으면 Staff 미등록자여도 부서/직원/계좌 조회가 허용된다."""
        self.client.force_authenticate(user=self.accountant_user)

        # 부서 목록 조회
        res_dept = self.client.get(f'/api/v1/department/?company={self.company.pk}')
        self.assertEqual(res_dept.status_code, 200, res_dept.data)

        # 직원 목록 조회
        res_staff = self.client.get(f'/api/v1/staff/?company={self.company.pk}&limit=500&status=1')
        self.assertEqual(res_staff.status_code, 200, res_staff.data)

    def test_hq_write_denied_without_staff_with_clear_message(self):
        """HQ 회계 권한이 있더라도 Staff 미등록 상태에서는 거래 등록이 거부되고 명확한 안내 메시지를 반환한다."""
        self.client.force_authenticate(user=self.accountant_user)

        post_data = {
            'company': self.company.pk,
            'bank_account': self.bank_account.pk,
            'deal_date': '2026-06-15',
            'sort': self.sort_expense.pk,
            'amount': 50000,
            'content': '서버 호스팅비',
            'accounting_entries': [
                {
                    'account': self.account.pk,
                    'amount': 50000,
                }
            ]
        }
        res = self.client.post('/api/v1/ledger/company-composite-transaction/', post_data, format='json')
        self.assertEqual(res.status_code, 403)
        self.assertIn('임직원(Staff)으로 등록되어 있어야 합니다', res.data.get('detail', ''))

    def test_hq_write_denied_when_staff_is_inactive(self):
        """Staff로 등록되었으나 퇴사(status!='1') 상태이면 거래 등록이 거부된다."""
        # 퇴사자 Staff 생성
        Staff.objects.create(
            company=self.company,
            user=self.accountant_user,
            name='김회계',
            id_number='900101-1234567',
            personal_phone='010-1111-2222',
            date_join='2026-01-01',
            position=self.position,
            grade=self.grade,
            status='4',  # 4: 퇴직
        )
        self.client.force_authenticate(user=self.accountant_user)

        post_data = {
            'company': self.company.pk,
            'bank_account': self.bank_account.pk,
            'deal_date': '2026-06-15',
            'sort': self.sort_expense.pk,
            'amount': 50000,
            'content': '서버 호스팅비',
            'accounting_entries': [
                {
                    'account': self.account.pk,
                    'amount': 50000,
                }
            ]
        }
        res = self.client.post('/api/v1/ledger/company-composite-transaction/', post_data, format='json')
        self.assertEqual(res.status_code, 403)
        self.assertIn('재직 중인 임직원(Staff)만', res.data.get('detail', ''))

    def test_hq_write_allowed_when_staff_is_active_with_permission(self):
        """HQ 회계 권한이 있고 재직 중인 Staff(status='1')이면 거래 등록이 정상 처리된다."""
        # 재직자 Staff 등록
        Staff.objects.create(
            company=self.company,
            user=self.accountant_user,
            name='김회계',
            id_number='900101-1234567',
            personal_phone='010-1111-2222',
            date_join='2026-01-01',
            position=self.position,
            grade=self.grade,
            status='1',  # 1: 재직
        )
        self.client.force_authenticate(user=self.accountant_user)

        post_data = {
            'company': self.company.pk,
            'bank_account': self.bank_account.pk,
            'deal_date': '2026-06-15',
            'sort': self.sort_expense.pk,
            'amount': 50000,
            'content': '서버 호스팅비',
            'accounting_entries': [
                {
                    'account': self.account.pk,
                    'amount': 50000,
                }
            ]
        }
        res = self.client.post('/api/v1/ledger/company-composite-transaction/', post_data, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(CompanyBankTransaction.objects.count(), 1)
