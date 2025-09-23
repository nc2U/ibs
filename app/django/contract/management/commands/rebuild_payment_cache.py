from django.core.management.base import BaseCommand
from django.db import transaction
from contract.models import ContractPrice


class Command(BaseCommand):
    help = '모든 ContractPrice 인스턴스의 납부 금액 캐시를 재계산합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            type=int,
            help='특정 프로젝트 ID만 처리 (선택사항)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='배치 처리 크기 (기본값: 100)'
        )

    def handle(self, *args, **options):
        project_id = options.get('project')
        batch_size = options['batch_size']

        # 쿼리셋 준비
        queryset = ContractPrice.objects.select_related(
            'contract', 'contract__project').filter(contract__activation=True)

        if project_id:
            queryset = queryset.filter(contract__project_id=project_id)
            self.stdout.write(f'프로젝트 {project_id}의 ContractPrice 캐시를 재계산합니다.')
        else:
            self.stdout.write('모든 ContractPrice 캐시를 재계산합니다.')

        total_count = queryset.count()
        processed_count = 0
        success_count = 0
        error_count = 0

        self.stdout.write(f'총 {total_count}개의 레코드를 처리합니다.')

        # 배치 처리
        for i in range(0, total_count, batch_size):
            batch = queryset[i:i + batch_size]

            with transaction.atomic():
                for contract_price in batch:
                    try:
                        if contract_price.contract:
                            contract_price.calculate_and_cache_payments()
                            contract_price.save()
                            success_count += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'ContractPrice {contract_price.id}: 연결된 계약이 없습니다.')
                            )
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'ContractPrice {contract_price.id} 처리 실패: {e}')
                        )

                    processed_count += 1

            # 진행 상황 출력
            percentage = (processed_count / total_count) * 100
            self.stdout.write(f'진행률: {percentage:.1f}% ({processed_count}/{total_count})')

        # 최종 결과 출력
        self.stdout.write(
            self.style.SUCCESS(
                f'\n캐시 재계산 완료!\n'
                f'총 처리: {processed_count}\n'
                f'성공: {success_count}\n'
                f'실패: {error_count}'
            )
        )

        # 캐시 유효성 통계
        valid_cache_count = ContractPrice.objects.filter(is_cache_valid=True).count()
        invalid_cache_count = ContractPrice.objects.filter(is_cache_valid=False).count()

        self.stdout.write(
            f'\n캐시 상태:\n'
            f'유효: {valid_cache_count}\n'
            f'무효: {invalid_cache_count}'
        )
