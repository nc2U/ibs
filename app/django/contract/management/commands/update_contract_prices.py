"""
계약 가격 일괄 업데이트 Management Command

SalesPriceByGT 변경 후 프로젝트 내 모든 계약의 가격 정보를 일괄 업데이트할 때 사용

사용법:
    # 특정 프로젝트의 계약 가격 업데이트
    python manage.py update_contract_prices --project 1

    # 미계약 세대 ContractPrice도 함께 생성 (차수 ID 지정)
    python manage.py update_contract_prices --project 1 --uncontracted-order-group 2

    # 미리보기 모드 (실제 업데이트 없이 대상 계약만 확인)
    python manage.py update_contract_prices --project 1 --dry-run

    # 상세 로그와 함께 실행
    python manage.py update_contract_prices --project 1 --verbosity 2
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from contract.services import ContractPriceBulkUpdateService
from project.models import Project
from contract.models import OrderGroup


class Command(BaseCommand):
    help = 'SalesPriceByGT 변경 후 계약 가격 일괄 업데이트'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            type=int,
            required=True,
            help='업데이트할 프로젝트 ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 업데이트 없이 미리보기만 실행'
        )
        parser.add_argument(
            '--show-errors',
            action='store_true',
            help='오류 발생한 계약들의 상세 정보 표시'
        )
        parser.add_argument(
            '--uncontracted-order-group',
            type=int,
            help='미계약 세대 ContractPrice 생성시 사용할 차수(OrderGroup) ID (미지정시 프로젝트 기본 차수 사용)'
        )

    def handle(self, *args, **options):
        project_id = options['project']
        dry_run = options['dry_run']
        show_errors = options['show_errors']
        verbosity = options['verbosity']
        uncontracted_order_group_id = options.get('uncontracted_order_group')

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise CommandError(f'프로젝트 ID {project_id}를 찾을 수 없습니다.')

        # 미계약 세대용 차수 검증
        order_group_for_uncontracted = None
        if uncontracted_order_group_id:
            try:
                order_group_for_uncontracted = OrderGroup.objects.get(
                    pk=uncontracted_order_group_id,
                    project=project
                )
            except OrderGroup.DoesNotExist:
                raise CommandError(f'프로젝트 {project.name}에서 차수 ID {uncontracted_order_group_id}를 찾을 수 없습니다.')

        # ContractPriceBulkUpdateService는 이제 자동으로 프로젝트 기본 차수를 참조합니다
        service = ContractPriceBulkUpdateService(project, order_group_for_uncontracted)

        if verbosity >= 1:
            self.stdout.write(f'프로젝트: {project.name} (ID: {project.pk})')
            if service.order_group_for_uncontracted:
                prefix = "사용자 지정" if order_group_for_uncontracted else "프로젝트 기본"
                self.stdout.write(f'미계약 세대 대상 차수: {service.order_group_for_uncontracted.name} (ID: {service.order_group_for_uncontracted.pk}) [{prefix}]')
            else:
                self.stdout.write('미계약 세대 처리: 차수가 설정되지 않음')

        # 프로젝트 유효성 검증
        validation_result = service.validate_project()

        if verbosity >= 2:
            self.stdout.write('=== 프로젝트 검증 결과 ===')
            self.stdout.write(f'- 프로젝트명: {validation_result["project_name"]}')
            self.stdout.write(f'- 유효한 계약 수: {validation_result["active_contracts_count"]}')
            self.stdout.write(f'- 유효성: {"✓" if validation_result["is_valid"] else "✗"}')

        if not validation_result['is_valid']:
            self.stdout.write(
                self.style.ERROR('업데이트할 유효한 계약이 없습니다.')
            )
            return

        if dry_run:
            # 미리보기 모드
            self.stdout.write(
                self.style.WARNING('=== 미리보기 모드 (실제 업데이트 없음) ===')
            )

            contracts = service.get_contracts_to_update()
            total_count = contracts.count()

            self.stdout.write(f'업데이트 대상 계약: {total_count}개')

            if verbosity >= 2 and total_count > 0:
                self.stdout.write('\n대상 계약 목록 (최대 10개):')
                for contract in contracts[:10]:
                    contractor_name = contract.contractor.name if hasattr(contract, 'contractor') else 'N/A'
                    unit_type = contract.unit_type.name if contract.unit_type else 'N/A'
                    current_price = 'N/A'

                    if hasattr(contract, 'contractprice'):
                        current_price = f'{contract.contractprice.price:,}원'

                    self.stdout.write(
                        f'  - {contract.serial_number} | {contractor_name} | {unit_type} | {current_price}'
                    )

                if total_count > 10:
                    self.stdout.write(f'  ... 외 {total_count - 10}개')

            self.stdout.write(
                self.style.SUCCESS(f'\n미리보기 완료: {total_count}개 계약이 업데이트 대상입니다.')
            )

        else:
            # 실제 업데이트 실행
            self.stdout.write('=== 계약 가격 일괄 업데이트 시작 ===')

            try:
                with transaction.atomic():
                    result = service.update_all_contract_prices()

                # 결과 출력
                success_count = result['updated_count'] + result['created_count']
                error_count = len(result['errors'])

                if verbosity >= 1:
                    self.stdout.write('\n=== 업데이트 결과 ===')
                    self.stdout.write(f'- 처리된 계약 수: {result["total_processed"]}개')
                    self.stdout.write(f'- 업데이트된 계약: {result["updated_count"]}개')
                    self.stdout.write(f'- 새로 생성된 가격정보: {result["created_count"]}개')
                    if result.get('uncontracted_created_count', 0) > 0:
                        self.stdout.write(f'- 미계약 세대 ContractPrice 생성: {result["uncontracted_created_count"]}개')
                    self.stdout.write(f'- 성공: {success_count}개')
                    self.stdout.write(f'- 실패: {error_count}개')

                # 오류 상세 표시
                if error_count > 0:
                    self.stdout.write(
                        self.style.WARNING(f'\n{error_count}개 계약에서 오류 발생:')
                    )

                    if show_errors or verbosity >= 2:
                        for error in result['errors']:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'  - 계약 {error["serial_number"]} (ID: {error["contract_id"]}): {error["error"]}'
                                )
                            )
                    else:
                        self.stdout.write('  (상세 오류는 --show-errors 옵션으로 확인)')

                # 최종 메시지
                if error_count == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'\n✓ 모든 계약 가격이 성공적으로 업데이트되었습니다! ({success_count}개)')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'\n⚠ 부분적으로 완료되었습니다. 성공: {success_count}개, 실패: {error_count}개')
                    )

            except Exception as e:
                raise CommandError(f'업데이트 중 오류 발생: {str(e)}')

        if verbosity >= 1:
            self.stdout.write('\n=== 작업 완료 ===')

    @staticmethod
    def format_price(price):
        """가격을 형식화하여 반환"""
        if price is None:
            return 'N/A'
        return f'{price:,}원'
