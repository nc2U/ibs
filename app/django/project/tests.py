import uuid
from datetime import date
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError

from company.models import Company
from contract.models import OrderGroup
from items.models import UnitType
from ibs.models import AccountSort
from ledger.models import ProjectAccount
from project.models import (
    Project, ProjectIncBudget, ProjectOutBudget, Site, SiteOwner,
    SiteOwnshipRelationship, SiteOwnerConsultationLogs, SiteContract
)
from project.admin import (
    ProjectAdmin, ProjectIncBudgetAdmin, ProjectOutBudgetAdmin, SiteAdmin,
    SiteOwnerAdmin, SiteOwnshipRelationshipAdmin, SiteOwnerConsultationLogsAdmin, SiteContractAdmin
)
from apiV1.serializers.project import (
    SiteOwnerSerializer, ProjectIncBudgetSerializer,
    SiteContractSerializer, SiteOwnshipRelationshipSerializer
)
from work.models.project import IssueProject, Member, Role, Permission

User = get_user_model()


class ProjectTestCaseBase(APITestCase):
    def setUp(self):
        # 1. 관리자 유저
        self.admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='password123'
        )
        self.client.force_authenticate(user=self.admin_user)
        self.client.force_login(self.admin_user)

        # 2. 회사 및 기본 워크스페이스
        self.company = Company.objects.create(name='테스트건설')
        self.issue_project_a = IssueProject.objects.create(
            company=self.company,
            name='워크스페이스 A',
            slug='workspace-a',
            type='2',
            creator=self.admin_user
        )
        self.issue_project_b = IssueProject.objects.create(
            company=self.company,
            name='워크스페이스 B',
            slug='workspace-b',
            type='2',
            creator=self.admin_user
        )

        # 3. 프로젝트 A, B
        self.project_a = Project.objects.create(
            issue_project=self.issue_project_a,
            name='프로젝트 A',
            order=1,
            kind='1',
            start_year=2026,
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24
        )
        self.project_b = Project.objects.create(
            issue_project=self.issue_project_b,
            name='프로젝트 B',
            order=2,
            kind='1',
            start_year=2026,
            monthly_aggr_start_date='2026-01-01',
            construction_start_date='2026-06-01',
            construction_period_months=24
        )

        # 4. 일반 사용자 및 프로젝트 A 권한 할당
        self.user_a = User.objects.create_user(
            username='user_proj_a',
            email='usera@test.com',
            password='password123'
        )
        self.user_b = User.objects.create_user(
            username='user_proj_b',
            email='userb@test.com',
            password='password123'
        )

        # 역할 및 권한 설정
        self.role_dev = Role.objects.create(name='개발담당', is_for_dev_project=True, creator=self.admin_user)
        # site 및 project 권한 부여
        for code in ['site.read', 'site.create', 'site.update', 'site.delete', 'project.public']:
            perm, _ = Permission.objects.get_or_create(code=code, defaults={'name': code, 'module': 'project'})
            self.role_dev.permissions.add(perm)

        member_a = Member.objects.create(user=self.user_a, project=self.issue_project_a)
        member_a.roles.add(self.role_dev)

        member_b = Member.objects.create(user=self.user_b, project=self.issue_project_b)
        member_b.roles.add(self.role_dev)

        # 5. 계정 과목 및 관련 기초 데이터
        self.account_parent = ProjectAccount.objects.create(
            code='100',
            name='토지대',
            depth=1,
            category='expense',
            direction='withdraw',
            is_active=True
        )
        self.account = ProjectAccount.objects.create(
            parent=self.account_parent,
            code='101',
            name='용지매입비',
            depth=2,
            category='expense',
            direction='withdraw',
            is_active=True
        )

        self.order_group_a = OrderGroup.objects.create(
            project=self.project_a, order_number=1, sort='2', name='1차'
        )
        self.order_group_b = OrderGroup.objects.create(
            project=self.project_b, order_number=1, sort='2', name='1차'
        )

        self.unit_type_a = UnitType.objects.create(
            project=self.project_a, name='84A', sort='1', color='#FF0000', num_unit=50
        )
        self.unit_type_b = UnitType.objects.create(
            project=self.project_b, name='84B', sort='1', color='#00FF00', num_unit=50
        )

        # 6. 부지, 소유자, 계약 데이터 (프로젝트 A)
        self.site_a = Site.objects.create(
            project=self.project_a,
            order=1,
            district='역삼동',
            lot_number='100-1',
            site_purpose='대',
            official_area='330.5000000',
            creator=self.admin_user
        )
        self.owner_a = SiteOwner.objects.create(
            project=self.project_a,
            owner='소유자A',
            phone1='010-1111-2222',
            own_sort='1',
            creator=self.admin_user
        )
        self.relation_a = SiteOwnshipRelationship.objects.create(
            site=self.site_a,
            site_owner=self.owner_a,
            ownership_ratio='100.0000000',
            owned_area='330.5000000'
        )
        self.contract_a = SiteContract.objects.create(
            project=self.project_a,
            owner=self.owner_a,
            contract_date=date(2026, 1, 15),
            total_price=500000000,
            contract_area='330.5000000',
            acc_bank='신한은행',
            acc_number='110-123-456789',
            acc_owner='소유자A',
            creator=self.admin_user
        )
        self.consultation_a = SiteOwnerConsultationLogs.objects.create(
            site_owner=self.owner_a,
            consultation_date=date(2026, 1, 10),
            channel='visit',
            title='보상 협의 1차',
            content='보상 기준 논의',
            consultant=self.admin_user,
            creator=self.admin_user
        )

        # 7. 부지, 소유자, 계약 데이터 (프로젝트 B)
        self.site_b = Site.objects.create(
            project=self.project_b,
            order=1,
            district='서초동',
            lot_number='200-2',
            site_purpose='대',
            official_area='500.0000000',
            creator=self.admin_user
        )
        self.owner_b = SiteOwner.objects.create(
            project=self.project_b,
            owner='소유자B',
            phone1='010-3333-4444',
            own_sort='1',
            creator=self.admin_user
        )
        self.relation_b = SiteOwnshipRelationship.objects.create(
            site=self.site_b,
            site_owner=self.owner_b,
            ownership_ratio='100.0000000',
            owned_area='500.0000000'
        )
        self.contract_b = SiteContract.objects.create(
            project=self.project_b,
            owner=self.owner_b,
            contract_date=date(2026, 2, 20),
            total_price=900000000,
            contract_area='500.0000000',
            acc_bank='국민은행',
            acc_number='999-888-777666',
            acc_owner='소유자B',
            creator=self.admin_user
        )
        self.consultation_b = SiteOwnerConsultationLogs.objects.create(
            site_owner=self.owner_b,
            consultation_date=date(2026, 2, 5),
            channel='phone',
            title='보상 문의',
            content='전화 상담 완료',
            consultant=self.admin_user,
            creator=self.admin_user
        )

        # 8. 예산 데이터
        self.inc_budget_a = ProjectIncBudget.objects.create(
            project=self.project_a,
            account=self.account,
            order_group=self.order_group_a,
            unit_type=self.unit_type_a,
            quantity=10,
            budget=1000000000
        )
        self.out_budget_a = ProjectOutBudget.objects.create(
            project=self.project_a,
            order=1,
            account=self.account,
            budget=500000000
        )
        self.inc_budget_b = ProjectIncBudget.objects.create(
            project=self.project_b,
            account=self.account,
            order_group=self.order_group_b,
            unit_type=self.unit_type_b,
            quantity=20,
            budget=2000000000
        )
        self.out_budget_b = ProjectOutBudget.objects.create(
            project=self.project_b,
            order=1,
            account=self.account,
            budget=800000000
        )


class ProjectModelValidationTest(ProjectTestCaseBase):
    """모델 clean() 및 비즈니스 무결성 검증 테스트"""

    def test_project_inc_budget_clean_same_project_passes(self):
        """수입예산과 동일 프로젝트의 order_group, unit_type은 검증 통과"""
        budget = ProjectIncBudget(
            project=self.project_a,
            account=self.account,
            order_group=self.order_group_a,
            unit_type=self.unit_type_a,
            quantity=10,
            budget=1000000000
        )
        try:
            budget.clean()
        except ValidationError:
            self.fail("동일 프로젝트인 경우 ValidationError가 발생하면 안 됩니다.")

    def test_project_inc_budget_clean_different_order_group_fails(self):
        """수입예산과 차수의 프로젝트가 불일치하면 ValidationError 발생"""
        budget = ProjectIncBudget(
            project=self.project_a,
            account=self.account,
            order_group=self.order_group_b,  # 다른 프로젝트의 차수
            unit_type=self.unit_type_a,
            quantity=10,
            budget=1000000000
        )
        with self.assertRaises(ValidationError) as ctx:
            budget.clean()
        self.assertIn('order_group', ctx.exception.message_dict)

    def test_project_inc_budget_clean_different_unit_type_fails(self):
        """수입예산과 타입의 프로젝트가 불일치하면 ValidationError 발생"""
        budget = ProjectIncBudget(
            project=self.project_a,
            account=self.account,
            order_group=self.order_group_a,
            unit_type=self.unit_type_b,  # 다른 프로젝트의 타입
            quantity=10,
            budget=1000000000
        )
        with self.assertRaises(ValidationError) as ctx:
            budget.clean()
        self.assertIn('unit_type', ctx.exception.message_dict)

    def test_site_ownership_relationship_clean_different_project_fails(self):
        """부지와 소유자의 프로젝트가 불일치하면 ValidationError 발생"""
        rel = SiteOwnshipRelationship(
            site=self.site_a,        # 프로젝트 A 부지
            site_owner=self.owner_b  # 프로젝트 B 소유자
        )
        with self.assertRaises(ValidationError) as ctx:
            rel.clean()
        self.assertIn('부지의 프로젝트와 소유자의 프로젝트가 일치해야 합니다.', str(ctx.exception))

    def test_site_contract_clean_different_project_fails(self):
        """계약의 프로젝트와 소유자의 프로젝트가 불일치하면 ValidationError 발생"""
        contract = SiteContract(
            project=self.project_a,  # 프로젝트 A
            owner=self.owner_b,      # 프로젝트 B 소유자
            contract_date=date(2026, 1, 1),
            total_price=100000000,
            acc_bank='우리은행',
            acc_number='123-456-789',
            acc_owner='소유자B'
        )
        with self.assertRaises(ValidationError) as ctx:
            contract.clean()
        self.assertIn('owner', ctx.exception.message_dict)

    def test_project_inc_budget_save_calls_clean(self):
        """수입예산 저장 시 clean()이 호출되어 불일치 차수일 때 ValidationError 발생"""
        budget = ProjectIncBudget(
            project=self.project_a,
            account=self.account,
            order_group=self.order_group_b,  # 다른 프로젝트의 차수
            unit_type=self.unit_type_a,
            quantity=10,
            budget=1000000000
        )
        with self.assertRaises(ValidationError):
            budget.save()

    def test_site_ownership_relationship_save_calls_clean(self):
        """부지-소유자 관계 저장 시 clean()이 호출되어 불일치 프로젝트일 때 ValidationError 발생"""
        rel = SiteOwnshipRelationship(
            site=self.site_a,
            site_owner=self.owner_b
        )
        with self.assertRaises(ValidationError):
            rel.save()

    def test_site_contract_save_calls_clean(self):
        """계약 저장 시 clean()이 호출되어 불일치 프로젝트일 때 ValidationError 발생"""
        contract = SiteContract(
            project=self.project_a,
            owner=self.owner_b,
            contract_date=date(2026, 1, 1),
            total_price=100000000,
            acc_bank='우리은행',
            acc_number='123-456-789',
            acc_owner='소유자B'
        )
        with self.assertRaises(ValidationError):
            contract.save()


class ProjectSerializerValidationTest(ProjectTestCaseBase):
    """시리얼라이저 레벨 프로젝트 불일치 차단 검증"""

    def test_site_owner_serializer_create_cross_project_site_fails(self):
        """SiteOwnerSerializer 생성 시 타 프로젝트 부지 전달 시 ValidationError 발생"""
        data = {
            'project': self.project_a.pk,
            'owner': '신규소유자',
            'sites': [self.site_b.pk]  # 프로젝트 B 부지
        }
        serializer = SiteOwnerSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(DRFValidationError) as ctx:
            serializer.save()
        self.assertIn('sites', ctx.exception.detail)

    def test_site_owner_serializer_update_cross_project_site_fails(self):
        """SiteOwnerSerializer 수정 시 타 프로젝트 부지 전달 시 ValidationError 발생"""
        data = {
            'owner': '소유자A_수정',
            'sites': [self.site_b.pk]  # 프로젝트 B 부지
        }
        serializer = SiteOwnerSerializer(instance=self.owner_a, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(DRFValidationError) as ctx:
            serializer.save()
        self.assertIn('sites', ctx.exception.detail)

    def test_project_inc_budget_serializer_cross_project_fails(self):
        """ProjectIncBudgetSerializer validate에서 프로젝트 불일치 차수 전달 시 차단"""
        data = {
            'project': self.project_a.pk,
            'account': self.account.pk,
            'order_group': self.order_group_b.pk,  # 프로젝트 B 차수
            'quantity': 10,
            'budget': 500000000
        }
        serializer = ProjectIncBudgetSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('order_group', serializer.errors)

    def test_site_contract_serializer_cross_project_fails(self):
        """SiteContractSerializer validate에서 프로젝트 불일치 소유자 전달 시 차단"""
        data = {
            'project': self.project_a.pk,
            'owner': self.owner_b.pk,  # 프로젝트 B 소유자
            'contract_date': '2026-03-01',
            'total_price': 100000000,
            'acc_bank': '우리은행',
            'acc_number': '123-456-789',
            'acc_owner': '소유자B'
        }
        serializer = SiteContractSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('owner', serializer.errors)

    def test_site_ownership_relationship_serializer_cross_project_fails(self):
        """SiteOwnshipRelationshipSerializer validate에서 프로젝트 불일치 관계 전달 시 차단"""
        data = {
            'site': self.site_a.pk,
            'site_owner': self.owner_b.pk  # 프로젝트 B 소유자
        }
        serializer = SiteOwnshipRelationshipSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class ProjectRLSTestCase(ProjectTestCaseBase):
    """행 단위 데이터 보안(RLS) 격리 테스트"""

    def test_site_owner_viewset_rls_filters_by_accessible_projects(self):
        """SiteOwnerViewSet: user_a는 프로젝트 A 소유자만 조회되고 프로젝트 B 소유자는 노출되지 않음"""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('api:siteowner-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        owner_ids = [item['pk'] for item in response.data['results']]
        self.assertIn(self.owner_a.pk, owner_ids)
        self.assertNotIn(self.owner_b.pk, owner_ids)

    def test_site_contract_viewset_rls_filters_by_accessible_projects(self):
        """SiteContractViewSet: user_a는 프로젝트 A 계약만 조회되고 프로젝트 B 계약은 노출되지 않음"""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('api:sitecontract-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contract_ids = [item['pk'] for item in response.data['results']]
        self.assertIn(self.contract_a.pk, contract_ids)
        self.assertNotIn(self.contract_b.pk, contract_ids)

    def test_site_viewset_rls_filters_by_accessible_projects(self):
        """SiteViewSet: user_a는 프로젝트 A 부지만 조회되고 프로젝트 B 부지는 노출되지 않음"""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('api:site-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        site_ids = [item['pk'] for item in response.data['results']]
        self.assertIn(self.site_a.pk, site_ids)
        self.assertNotIn(self.site_b.pk, site_ids)

    def test_all_site_and_all_owner_rls(self):
        """AllSite 및 AllOwner ViewSet: user_a에게 프로젝트 A 데이터만 노출"""
        self.client.force_authenticate(user=self.user_a)

        res_site = self.client.get(reverse('api:all-site-list'))
        site_ids = [s['pk'] for s in res_site.data['results']]
        self.assertIn(self.site_a.pk, site_ids)
        self.assertNotIn(self.site_b.pk, site_ids)

        res_owner = self.client.get(reverse('api:all-owner-list'))
        owner_ids = [o['pk'] for o in res_owner.data['results']]
        self.assertIn(self.owner_a.pk, owner_ids)
        self.assertNotIn(self.owner_b.pk, owner_ids)

    def test_site_relation_viewset_rls(self):
        """SiteRelationViewSet: user_a에게 프로젝트 A 소유관계만 노출"""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(reverse('api:siteownshiprelationship-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rel_ids = [r['pk'] for r in response.data['results']]
        self.assertIn(self.relation_a.pk, rel_ids)
        self.assertNotIn(self.relation_b.pk, rel_ids)

    def test_site_owner_consultation_logs_viewset_rls(self):
        """SiteOwnerConsultationLogsViewSet: user_a에게 프로젝트 A 상담 기록만 노출"""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(reverse('api:siteownerconsultationlogs-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log_ids = [c['pk'] for c in response.data['results']]
        self.assertIn(self.consultation_a.pk, log_ids)
        self.assertNotIn(self.consultation_b.pk, log_ids)

    def test_total_viewsets_rls(self):
        """TotalSiteArea, TotalOwnerArea, TotalContractedArea ViewSet RLS 격리"""
        self.client.force_authenticate(user=self.user_a)

        # TotalSiteArea
        res_site = self.client.get(reverse('api:sites-total-list'))
        project_ids = [item['project'] for item in res_site.data['results']]
        self.assertIn(self.project_a.pk, project_ids)
        self.assertNotIn(self.project_b.pk, project_ids)

        # TotalOwnerArea
        res_owner = self.client.get(reverse('api:owners-total-list'))
        project_ids = [item['project'] for item in res_owner.data['results']]
        self.assertIn(self.project_a.pk, project_ids)
        self.assertNotIn(self.project_b.pk, project_ids)

        # TotalContractedArea
        res_cont = self.client.get(reverse('api:conts-total-list'))
        project_ids = [item['project'] for item in res_cont.data['results']]
        self.assertIn(self.project_a.pk, project_ids)
        self.assertNotIn(self.project_b.pk, project_ids)


class ProjectExcelExportTestCase(ProjectTestCaseBase):
    """Excel 내보내기 뷰 안정성 및 가드 테스트"""

    def test_export_sites_missing_project_returns_400(self):
        """ExportSites: project 파라미터 누락 시 400 Bad Request 반환"""
        url = reverse('excel:sites')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('프로젝트 ID가 필요합니다', response.content.decode('utf-8'))

    def test_export_sites_invalid_project_returns_400(self):
        """ExportSites: 존재하지 않는 project 파라미터 전달 시 400 Bad Request 반환"""
        url = reverse('excel:sites') + '?project=999999'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('유효하지 않은 프로젝트 ID', response.content.decode('utf-8'))

    def test_export_sites_success(self):
        """ExportSites: 정상 요청 시 200 OK와 올바른 엑셀 헤더 반환"""
        url = reverse('excel:sites') + f'?project={self.project_a.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'],
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment;', response['Content-Disposition'])

    def test_export_sites_by_owner_missing_project_returns_400(self):
        """ExportSitesByOwner: project 파라미터 누락 시 400 Bad Request 반환"""
        url = reverse('excel:sites-by-owner')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_export_sites_by_owner_success(self):
        """ExportSitesByOwner: 정상 요청 시 200 OK 반환"""
        url = reverse('excel:sites-by-owner') + f'?project={self.project_a.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'],
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_export_sites_contracts_missing_project_returns_400(self):
        """ExportSitesContracts: project 파라미터 누락 시 400 Bad Request 반환"""
        url = reverse('excel:sites-contracts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_export_sites_contracts_success(self):
        """ExportSitesContracts: 정상 요청 시 200 OK 반환"""
        url = reverse('excel:sites-contracts') + f'?project={self.project_a.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'],
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_export_sites_unauthorized_user_forbidden(self):
        """ExportSites: 권한이 없는 사용자가 요청 시 403 Forbidden 반환"""
        self.client.force_login(self.user_b)
        url = reverse('excel:sites') + f'?project={self.project_a.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('열람 권한이 없습니다', response.content.decode('utf-8'))

    def test_export_sites_by_owner_unauthorized_user_forbidden(self):
        """ExportSitesByOwner: 권한이 없는 사용자가 요청 시 403 Forbidden 반환"""
        self.client.force_login(self.user_b)
        url = reverse('excel:sites-by-owner') + f'?project={self.project_a.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('열람 권한이 없습니다', response.content.decode('utf-8'))

    def test_export_sites_contracts_unauthorized_user_forbidden(self):
        """ExportSitesContracts: 권한이 없는 사용자가 요청 시 403 Forbidden 반환"""
        self.client.force_login(self.user_b)
        url = reverse('excel:sites-contracts') + f'?project={self.project_a.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('열람 권한이 없습니다', response.content.decode('utf-8'))


class ProjectAdminTestCase(ProjectTestCaseBase):
    """Admin 클래스 N+1 쿼리 방지 list_select_related 및 RLS 설정 검증"""

    def test_admin_list_select_related_configured(self):
        site = AdminSite()
        self.assertEqual(ProjectAdmin(Project, site).list_select_related, ('issue_project',))
        self.assertEqual(
            ProjectIncBudgetAdmin(ProjectIncBudget, site).list_select_related,
            ('project', 'account', 'account_d2', 'account_d3', 'order_group', 'unit_type')
        )
        self.assertEqual(
            ProjectOutBudgetAdmin(ProjectOutBudget, site).list_select_related,
            ('project', 'account', 'account_d2', 'account_d3')
        )
        self.assertEqual(SiteAdmin(Site, site).list_select_related, ('project',))
        self.assertEqual(SiteOwnerAdmin(SiteOwner, site).list_select_related, ('project',))
        self.assertEqual(
            SiteOwnshipRelationshipAdmin(SiteOwnshipRelationship, site).list_select_related,
            ('site', 'site_owner', 'site__project')
        )
        self.assertEqual(
            SiteOwnerConsultationLogsAdmin(SiteOwnerConsultationLogs, site).list_select_related,
            ('site_owner', 'consultant', 'site_owner__project')
        )
        self.assertEqual(SiteContractAdmin(SiteContract, site).list_select_related, ('owner', 'project'))

    def test_admin_get_queryset_rls_filtering(self):
        """8개 Admin 클래스별 get_queryset RLS 필터링 검증"""
        factory = RequestFactory()
        site = AdminSite()

        # 1. ProjectAdmin
        admin_obj = ProjectAdmin(Project, site)
        req_a = factory.get('/admin/project/project/')
        req_a.user = self.user_a
        qs_a = admin_obj.get_queryset(req_a)
        self.assertIn(self.project_a, qs_a)
        self.assertNotIn(self.project_b, qs_a)

        # 2. ProjectIncBudgetAdmin
        admin_obj = ProjectIncBudgetAdmin(ProjectIncBudget, site)
        qs_a = admin_obj.get_queryset(req_a)
        self.assertIn(self.inc_budget_a, qs_a)
        self.assertNotIn(self.inc_budget_b, qs_a)

        # 3. ProjectOutBudgetAdmin
        admin_obj = ProjectOutBudgetAdmin(ProjectOutBudget, site)
        qs_a = admin_obj.get_queryset(req_a)
        self.assertIn(self.out_budget_a, qs_a)
        self.assertNotIn(self.out_budget_b, qs_a)

        # 4. SiteAdmin
        admin_obj = SiteAdmin(Site, site)
        qs_a = admin_obj.get_queryset(req_a)
        self.assertIn(self.site_a, qs_a)
        self.assertNotIn(self.site_b, qs_a)

        # 5. SiteOwnerAdmin
        admin_obj = SiteOwnerAdmin(SiteOwner, site)
        qs_a = admin_obj.get_queryset(req_a)
        self.assertIn(self.owner_a, qs_a)
        self.assertNotIn(self.owner_b, qs_a)

        # 6. SiteOwnshipRelationshipAdmin
        admin_obj = SiteOwnshipRelationshipAdmin(SiteOwnshipRelationship, site)
        qs_a = admin_obj.get_queryset(req_a)
        self.assertIn(self.relation_a, qs_a)
        self.assertNotIn(self.relation_b, qs_a)

        # 7. SiteOwnerConsultationLogsAdmin
        admin_obj = SiteOwnerConsultationLogsAdmin(SiteOwnerConsultationLogs, site)
        qs_a = admin_obj.get_queryset(req_a)
        self.assertIn(self.consultation_a, qs_a)
        self.assertNotIn(self.consultation_b, qs_a)

        # 8. SiteContractAdmin
        admin_obj = SiteContractAdmin(SiteContract, site)
        qs_a = admin_obj.get_queryset(req_a)
        self.assertIn(self.contract_a, qs_a)
        self.assertNotIn(self.contract_b, qs_a)

        # Superuser는 전체 접근 가능
        req_admin = factory.get('/admin/project/sitecontract/')
        req_admin.user = self.admin_user
        qs_admin = admin_obj.get_queryset(req_admin)
        self.assertIn(self.contract_a, qs_admin)
        self.assertIn(self.contract_b, qs_admin)


class ProjectSignalTestCase(ProjectTestCaseBase):
    """신호 및 슬랙 알림 트리거 검증"""

    @patch('project.signals.send_slack_notification')
    def test_site_change_signal_sends_updator_on_edit(self, mock_notify):
        """Site 편집 시 updator 정보가 알림에 전달됨"""
        self.site_a.district = '신사동'
        self.site_a.updator = self.user_a
        self.site_a.save()

        mock_notify.assert_called_with(self.site_a, '편집', self.user_a)


class ProjectPermissionTestCase(ProjectTestCaseBase):
    """일반 사용자(비슈퍼유저)의 Project API 권한 및 IbsModulePermission 검증"""

    def test_user_with_permission_can_retrieve_project(self):
        """소속 프로젝트 권한(project.public)을 가진 비슈퍼유저는 자신의 프로젝트를 조회할 수 있어야 함"""
        self.client.force_authenticate(user=self.user_a)

        # 1. 권한 있는 자신의 프로젝트(Project A) 조회 -> 200 OK
        res_a = self.client.get(f'/api/v1/project/{self.project_a.pk}/')
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        self.assertEqual(res_a.data.get('name'), '프로젝트 A')

        # 2. 권한 없는 타 프로젝트(Project B) 조회 -> 403 Forbidden
        res_b = self.client.get(f'/api/v1/project/{self.project_b.pk}/')
        self.assertEqual(res_b.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_list_projects_filtered_by_permission(self):
        """목록 조회 시 소속/권한이 있는 프로젝트만 필터링되어 반환됨"""
        self.client.force_authenticate(user=self.user_a)

        res = self.client.get('/api/v1/project/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        returned_ids = [p['pk'] for p in results]
        self.assertIn(self.project_a.pk, returned_ids)
        self.assertNotIn(self.project_b.pk, returned_ids)

    def test_locked_project_denies_access(self):
        """잠금보관(status='9') 상태의 워크스페이스는 데이터 조회가 차단됨"""
        self.issue_project_a.status = '9'
        self.issue_project_a.save()

        self.client.force_authenticate(user=self.user_a)
        res = self.client.get(f'/api/v1/project/{self.project_a.pk}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

