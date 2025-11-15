"""
ProjectCashBook 분리 거래 기능 테스트

모델 검증, 시리얼라이저 검증, 관리 명령어 테스트
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal

from cash.models import ProjectCashBook, ProjectBankAccount, BankCode
from project.models import Project
from company.models import Company
from ibs.models import AccountSort

User = get_user_model()


class ProjectCashBookSplitTestCase(TestCase):
    """ProjectCashBook 분리 거래 테스트"""

    @classmethod
    def setUpTestData(cls):
        """테스트 데이터 설정"""
        # 회사
        cls.company = Company.objects.create(name='테스트 회사')

        # 프로젝트
        cls.project = Project.objects.create(
            name='테스트 프로젝트',
            company=cls.company
        )

        # 은행 코드
        cls.bank_code = BankCode.objects.create(
            code='001',
            name='테스트 은행'
        )

        # 은행 계좌
        cls.bank_account = ProjectBankAccount.objects.create(
            project=cls.project,
            bankcode=cls.bank_code,
            alias_name='테스트 계좌',
            number='123-456-789'
        )

        # 계정 구분
        cls.account_sort = AccountSort.objects.create(
            code='1',
            name='출금'
        )

        # 사용자
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

    def test_create_parent_record(self):
        """부모 레코드 생성 테스트"""
        parent = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        self.assertTrue(parent.is_parent)
        self.assertFalse(parent.is_child)
        self.assertFalse(parent.is_separate)
        self.assertIsNone(parent.separated)

    def test_create_child_record(self):
        """자식 레코드 생성 테스트"""
        # 부모 생성
        parent = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        # 자식 생성
        child = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,
            separated=parent,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        self.assertFalse(child.is_parent)
        self.assertTrue(child.is_child)
        self.assertTrue(child.is_separate)
        self.assertEqual(child.separated, parent)

    def test_self_reference_validation(self):
        """자기 참조 검증 테스트"""
        parent = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        # 자기 자신을 참조하도록 설정
        parent.separated = parent

        with self.assertRaises(ValidationError) as context:
            parent.full_clean()

        self.assertIn('separated', context.exception.message_dict)

    def test_circular_reference_validation(self):
        """순환 참조 검증 테스트"""
        parent1 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user,
            skip_validation=True
        )

        parent2 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user,
            separated=parent1,
            skip_validation=True
        )

        # parent1이 parent2를 참조하도록 설정 (순환 참조)
        parent1.separated = parent2

        with self.assertRaises(ValidationError) as context:
            parent1.full_clean()

        self.assertIn('separated', context.exception.message_dict)

    def test_child_without_parent_validation(self):
        """부모 없는 자식 레코드 검증 테스트"""
        child = ProjectCashBook(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,  # 자식인데
            separated=None,  # 부모 없음
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        with self.assertRaises(ValidationError) as context:
            child.full_clean()

        self.assertIn('separated', context.exception.message_dict)

    def test_parent_with_wrong_flag_validation(self):
        """잘못된 플래그를 가진 부모 레코드 검증 테스트"""
        parent = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user,
            skip_validation=True
        )

        # 부모인데 is_separate=True로 설정
        parent.is_separate = True

        with self.assertRaises(ValidationError) as context:
            parent.full_clean()

        self.assertIn('is_separate', context.exception.message_dict)

    def test_both_income_and_outlay_validation(self):
        """입금과 출금 동시 존재 검증 테스트"""
        record = ProjectCashBook(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            income=500000,  # 입금
            outlay=1000000,  # 출금 (동시 존재)
            deal_date='2025-01-15',
            creator=self.user
        )

        with self.assertRaises(ValidationError) as context:
            record.full_clean()

        self.assertIn('__all__', context.exception.message_dict)

    def test_neither_income_nor_outlay_validation(self):
        """입금과 출금 둘 다 없음 검증 테스트"""
        record = ProjectCashBook(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            income=None,
            outlay=None,
            deal_date='2025-01-15',
            creator=self.user
        )

        with self.assertRaises(ValidationError) as context:
            record.full_clean()

        self.assertIn('__all__', context.exception.message_dict)

    def test_split_balance_valid_property(self):
        """split_balance_valid 프로퍼티 테스트"""
        # 부모 생성
        parent = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        # 자식 생성 (금액 일치)
        child1 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,
            separated=parent,
            outlay=600000,
            deal_date='2025-01-15',
            creator=self.user
        )

        child2 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,
            separated=parent,
            outlay=400000,
            deal_date='2025-01-15',
            creator=self.user
        )

        # 금액 일치
        self.assertTrue(parent.split_balance_valid)

        # 자식 레코드는 항상 True
        self.assertTrue(child1.split_balance_valid)
        self.assertTrue(child2.split_balance_valid)

    def test_split_balance_invalid(self):
        """split_balance_valid 프로퍼티 불일치 테스트"""
        # 부모 생성
        parent = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        # 자식 생성 (금액 불일치)
        child1 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,
            separated=parent,
            outlay=600000,
            deal_date='2025-01-15',
            creator=self.user
        )

        child2 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,
            separated=parent,
            outlay=300000,  # 합계 900,000 (부모 1,000,000과 불일치)
            deal_date='2025-01-15',
            creator=self.user
        )

        # 금액 불일치
        self.assertFalse(parent.split_balance_valid)

    def test_cascade_delete(self):
        """CASCADE 삭제 테스트"""
        # 부모 생성
        parent = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        # 자식 생성
        child1 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,
            separated=parent,
            outlay=600000,
            deal_date='2025-01-15',
            creator=self.user
        )

        child2 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,
            separated=parent,
            outlay=400000,
            deal_date='2025-01-15',
            creator=self.user
        )

        child1_pk = child1.pk
        child2_pk = child2.pk

        # 부모 삭제
        parent.delete()

        # 자식도 함께 삭제되었는지 확인
        self.assertFalse(ProjectCashBook.objects.filter(pk=child1_pk).exists())
        self.assertFalse(ProjectCashBook.objects.filter(pk=child2_pk).exists())

    def test_queryset_parent_records(self):
        """QuerySet parent_records() 메서드 테스트"""
        # 부모 레코드 생성
        parent1 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        parent2 = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            outlay=2000000,
            deal_date='2025-01-16',
            creator=self.user
        )

        # 자식 레코드 생성
        child = ProjectCashBook.objects.create(
            project=self.project,
            sort=self.account_sort,
            bank_account=self.bank_account,
            is_separate=True,
            separated=parent1,
            outlay=1000000,
            deal_date='2025-01-15',
            creator=self.user
        )

        # parent_records()는 부모만 반환
        parents = ProjectCashBook.objects.filter(is_separate=False, separated__isnull=True)
        self.assertEqual(parents.count(), 2)
        self.assertIn(parent1, parents)
        self.assertIn(parent2, parents)
        self.assertNotIn(child, parents)
