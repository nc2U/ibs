"""
CashBook 분리 거래 데이터 검증 관리 명령어

사용법:
    python manage.py validate_company_cashbook_splits
    python manage.py validate_company_cashbook_splits --fix
    python manage.py validate_company_cashbook_splits --company=1
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum, F

from cash.models import CashBook


class Command(BaseCommand):
    help = 'CashBook 분리 거래의 데이터 무결성 검증'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=int,
            help='특정 회사 ID만 검증',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='발견된 문제를 자동으로 수정 (is_separate 플래그)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='상세 출력',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('CashBook 분리 거래 검증 시작'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # 검증 대상 필터링
        queryset = CashBook.objects.all()
        if options['company']:
            queryset = queryset.filter(company_id=options['company'])
            self.stdout.write(f"\n📌 회사 ID {options['company']}만 검증합니다.\n")

        # 통계
        total_records = queryset.count()
        parent_records = queryset.filter(is_separate=False, separated__isnull=True).count()
        child_records = queryset.filter(separated__isnull=False).count()

        self.stdout.write(f"📊 전체 레코드: {total_records:,}개")
        self.stdout.write(f"   ├─ 부모 레코드: {parent_records:,}개")
        self.stdout.write(f"   └─ 자식 레코드: {child_records:,}개\n")

        # 검증 실행
        issues_found = []

        # 검증 1: 자기 참조
        self.stdout.write("🔍 검증 1: 자기 참조 확인...")
        # 자기 자신을 참조하는 레코드 찾기 (separated_id = id)
        self_ref = queryset.filter(separated_id=F('id'))
        if self_ref.exists():
            issue = f"❌ 자기 참조 레코드 {self_ref.count()}개 발견"
            self.stdout.write(self.style.ERROR(issue))
            issues_found.append(('self_reference', self_ref))
            if options['verbose']:
                for record in self_ref:
                    self.stdout.write(f"   - ID {record.pk}: {record}")
        else:
            self.stdout.write(self.style.SUCCESS("✅ 자기 참조 없음\n"))

        # 검증 2: is_separate 플래그 불일치
        self.stdout.write("🔍 검증 2: is_separate 플래그 일관성 확인...")

        # 자식인데 is_separate=False
        wrong_children = queryset.filter(separated__isnull=False, is_separate=False)
        if wrong_children.exists():
            issue = f"❌ is_separate=False인 자식 레코드 {wrong_children.count()}개 발견"
            self.stdout.write(self.style.ERROR(issue))
            issues_found.append(('wrong_child_flag', wrong_children))
            if options['verbose']:
                for record in wrong_children[:10]:  # 최대 10개만 출력
                    self.stdout.write(f"   - ID {record.pk}: separated={record.separated_id}")

            if options['fix']:
                fixed = wrong_children.update(is_separate=True)
                self.stdout.write(self.style.SUCCESS(f"   ✅ {fixed}개 레코드 수정 완료 (is_separate=True)\n"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ 자식 레코드 플래그 정상\n"))

        # 부모인데 is_separate=True
        wrong_parents = queryset.filter(separated__isnull=True, is_separate=True)
        if wrong_parents.exists():
            issue = f"❌ is_separate=True인 부모 레코드 {wrong_parents.count()}개 발견"
            self.stdout.write(self.style.ERROR(issue))
            issues_found.append(('wrong_parent_flag', wrong_parents))
            if options['verbose']:
                for record in wrong_parents[:10]:
                    self.stdout.write(f"   - ID {record.pk}: {record}")

            if options['fix']:
                fixed = wrong_parents.update(is_separate=False)
                self.stdout.write(self.style.SUCCESS(f"   ✅ {fixed}개 레코드 수정 완료 (is_separate=False)\n"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ 부모 레코드 플래그 정상\n"))

        # 검증 3: 고아 자식 레코드 (separated가 존재하지 않는 ID 참조)
        self.stdout.write("🔍 검증 3: 고아 자식 레코드 확인...")
        children_with_parent = queryset.filter(separated__isnull=False).values_list('separated_id', flat=True)
        parent_ids = set(queryset.filter(pk__in=children_with_parent).values_list('pk', flat=True))
        orphan_children = queryset.filter(
            separated__isnull=False
        ).exclude(separated_id__in=parent_ids)

        if orphan_children.exists():
            issue = f"❌ 고아 자식 레코드 {orphan_children.count()}개 발견"
            self.stdout.write(self.style.ERROR(issue))
            issues_found.append(('orphan_children', orphan_children))
            if options['verbose']:
                for record in orphan_children:
                    self.stdout.write(f"   - ID {record.pk}: separated={record.separated_id} (존재하지 않음)")
        else:
            self.stdout.write(self.style.SUCCESS("✅ 고아 레코드 없음\n"))

        # 검증 4: 금액 불일치
        self.stdout.write("🔍 검증 4: 부모-자식 금액 일치 확인...")
        parents_with_children = queryset.filter(
            is_separate=False,
            separated__isnull=True,
            sepItems__isnull=False
        ).distinct()

        amount_mismatches = []
        for parent in parents_with_children:
            children_sum = parent.sepItems.aggregate(
                total_outlay=Sum('outlay'),
                total_income=Sum('income')
            )

            expected_outlay = parent.outlay or 0
            expected_income = parent.income or 0
            actual_outlay = children_sum['total_outlay'] or 0
            actual_income = children_sum['total_income'] or 0

            if expected_outlay != actual_outlay or expected_income != actual_income:
                amount_mismatches.append({
                    'parent': parent,
                    'expected_outlay': expected_outlay,
                    'actual_outlay': actual_outlay,
                    'expected_income': expected_income,
                    'actual_income': actual_income,
                })

        if amount_mismatches:
            issue = f"❌ 금액 불일치 레코드 {len(amount_mismatches)}개 발견"
            self.stdout.write(self.style.ERROR(issue))
            issues_found.append(('amount_mismatch', amount_mismatches))
            if options['verbose']:
                for mismatch in amount_mismatches[:10]:
                    parent = mismatch['parent']
                    self.stdout.write(
                        f"   - ID {parent.pk}: "
                        f"출금(부모: ₩{mismatch['expected_outlay']:,} vs 자식합: ₩{mismatch['actual_outlay']:,}), "
                        f"입금(부모: ₩{mismatch['expected_income']:,} vs 자식합: ₩{mismatch['actual_income']:,})"
                    )
            self.stdout.write(self.style.WARNING("   ⚠️  금액 불일치는 자동 수정되지 않습니다. 수동 확인 필요\n"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ 금액 일치\n"))

        # 검증 5: 입금과 출금 동시 존재
        self.stdout.write("🔍 검증 5: 입금/출금 배타성 확인...")
        both_income_outlay = queryset.filter(
            income__isnull=False,
            income__gt=0,
            outlay__isnull=False,
            outlay__gt=0
        )
        if both_income_outlay.exists():
            issue = f"❌ 입금과 출금이 동시에 있는 레코드 {both_income_outlay.count()}개 발견"
            self.stdout.write(self.style.ERROR(issue))
            issues_found.append(('both_income_outlay', both_income_outlay))
            if options['verbose']:
                for record in both_income_outlay[:10]:
                    self.stdout.write(f"   - ID {record.pk}: 입금 ₩{record.income:,}, 출금 ₩{record.outlay:,}")
        else:
            self.stdout.write(self.style.SUCCESS("✅ 입금/출금 배타성 정상\n"))

        # 최종 결과
        self.stdout.write(self.style.SUCCESS('=' * 70))
        if not issues_found:
            self.stdout.write(self.style.SUCCESS('✅ 모든 검증 통과! 데이터 무결성 정상'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ {len(issues_found)}개 유형의 문제 발견'))
            self.stdout.write(self.style.WARNING('\n💡 --fix 옵션으로 일부 문제를 자동 수정할 수 있습니다.'))
            self.stdout.write(self.style.WARNING('💡 --verbose 옵션으로 상세 정보를 확인할 수 있습니다.'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # 오류 코드 반환 (CI/CD 파이프라인용)
        if issues_found and not options['fix']:
            raise CommandError('데이터 무결성 문제 발견')
