from datetime import date

from django.core.management.base import BaseCommand, CommandError

from contract.services import ContractorSensitiveService


class Command(BaseCommand):
    help = '보존기한(retention_until)이 만료된 계약자 주민등록번호를 일괄 파기하고 감사 로그를 기록합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--as-of',
            type=str,
            default=None,
            help='기준일(YYYY-MM-DD, 미지정 시 오늘 날짜 기준)',
        )

    def handle(self, *args, **options):
        as_of_raw = options.get('as_of')
        as_of_date = None
        if as_of_raw:
            try:
                as_of_date = date.fromisoformat(as_of_raw)
            except ValueError as exc:
                raise CommandError(f'잘못된 날짜 형식입니다: {as_of_raw} (YYYY-MM-DD)') from exc

        purged_count = ContractorSensitiveService.purge_expired_rrns(as_of_date=as_of_date)
        self.stdout.write(self.style.SUCCESS(f'보존기한 만료 주민등록번호 {purged_count}건 파기 완료'))
