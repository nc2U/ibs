from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import StaffAuth
from project.models import Project
from work.models.project import IssueProject, Member, Role, Permission


class Command(BaseCommand):
    help = 'StaffAuth 권한 설정을 work.IssueProject 의 Role/Member 기반 구조로 이관합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 데이터베이스 수정을 수행하지 않고 미리보기만 진행합니다.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY-RUN 모드로 실행 중입니다 (DB 반영 안 됨) ===\n'))

        with transaction.atomic():
            staff_auths = StaffAuth.objects.select_related('user').prefetch_related('allowed_projects').all()
            total_migrated = 0

            for sa in staff_auths:
                user = sa.user
                allowed_pjts = sa.allowed_projects.all()

                # StaffAuth의 권한 설정으로부터 부여할 Permission 코드 도출
                perm_codes = self._extract_permission_codes(sa)

                if not perm_codes:
                    self.stdout.write(f'사용자 {user.username}: 부여할 권한이 없음 (스킵)')
                    continue

                # 도출된 Permission 객체들 가져오기
                permissions = list(Permission.objects.filter(code__in=perm_codes))

                for pjt in allowed_pjts:
                    try:
                        issue_pjt = pjt.issue_project
                    except (Project.issue_project.RelatedObjectDoesNotExist, AttributeError):
                        self.stdout.write(self.style.ERROR(f'  [오류] Project ({pjt.name}) 에 매핑된 IssueProject 가 없습니다.'))
                        continue

                    # 해당 Permission 구성에 맞는 Role 찾거나 생성
                    role = self._get_or_create_role(user, permissions, dry_run)

                    # Member 추가 및 Role 연결
                    if not dry_run:
                        member, created = Member.objects.get_or_create(user=user, project=issue_pjt)
                        member.roles.add(role)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [이관] {user.username} -> 프로젝트: {issue_pjt.name} (Role: {role.name}, 권한 수: {len(permissions)})'
                        )
                    )
                    total_migrated += 1

            if dry_run:
                self.stdout.write(self.style.WARNING(f'\nDRY-RUN 완료. 총 {total_migrated}건 이관 대상 확인.'))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS(f'\n이관 성공적으로 완료. 총 {total_migrated}건 이관됨.'))

    def _extract_permission_codes(self, sa: StaffAuth) -> set:
        codes = set()

        # 1. contract ('1': read, '2': write)
        if sa.contract == '1':
            codes.add('contract.read')
        elif sa.contract == '2':
            codes.update(['contract.read', 'contract.create', 'contract.update', 'contract.delete', 'contract.release', 'contract.succession'])

        # 2. payment
        if sa.payment == '1':
            codes.add('payment.read')
        elif sa.payment == '2':
            codes.update(['payment.read', 'payment.create', 'payment.update', 'payment.delete'])

        # 3. notice
        if sa.notice == '1':
            codes.add('notice.read')
        elif sa.notice == '2':
            codes.update(['notice.read', 'notice.create', 'notice.update', 'notice.delete'])

        # 4. project_ledger (사업비 자금 관리)
        if sa.project_ledger == '1':
            codes.add('ledger.read')
        elif sa.project_ledger == '2':
            codes.update(['ledger.read', 'ledger.create', 'ledger.update', 'ledger.delete'])

        # 5. project_site (부지 관리)
        if sa.project_site == '1':
            codes.add('site.read')
        elif sa.project_site == '2':
            codes.update(['site.read', 'site.create', 'site.update', 'site.delete'])

        # 6. human_resource (인사 관리)
        if sa.human_resource == '1':
            codes.add('hr_work.read')
        elif sa.human_resource == '2':
            codes.update(['hr_work.read', 'hr_work.create', 'hr_work.update', 'hr_work.delete'])

        # 7. project_docs (사업지 문서)
        if sa.project_docs == '1':
            codes.add('docs.read')
        elif sa.project_docs == '2':
            codes.update(['docs.read', 'docs.create', 'docs.update', 'docs.delete'])

        # 8. project (신규 프로젝트/설정)
        if sa.project == '1':
            codes.add('project.pub_query')
        elif sa.project == '2':
            codes.update(['project.create', 'project.update', 'project.close', 'project.delete', 'project.module', 'project.member', 'project.version'])

        return codes

    def _get_or_create_role(self, creator, permissions, dry_run) -> Role:

        perm_ids = sorted([p.id for p in permissions])
        
        # 기존 Role 중 동일한 권한 목록을 가진 Role 검색
        for role in Role.objects.all():
            role_perm_ids = sorted(list(role.permissions.values_list('id', flat=True)))
            if role_perm_ids == perm_ids:
                return role

        # 일치하는 Role이 없으면 신규 생성
        role_name = f"StaffRole_{creator.pk}"
        if dry_run:
            role = Role(name=role_name, is_work_role=False, creator=creator)
            return role

        role = Role.objects.create(name=role_name, is_work_role=False, creator=creator)
        role.permissions.set(permissions)
        return role
