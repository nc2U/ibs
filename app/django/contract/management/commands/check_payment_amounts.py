from django.core.management.base import BaseCommand
from contract.models import Contract, ContractPrice
from django.utils import timezone


class Command(BaseCommand):
    help = 'ContractPrice payment_amounts 필드 상태 확인'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contract-id',
            type=int,
            help='특정 계약 ID만 확인'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='확인할 계약 수 (기본값: 5)'
        )

    def handle(self, *args, **options):
        contract_id = options.get('contract_id')
        limit = options['limit']

        if contract_id:
            try:
                contracts = [Contract.objects.get(id=contract_id, activation=True)]
            except Contract.DoesNotExist:
                self.stdout.write(f'Contract {contract_id} not found or not active')
                return
        else:
            contracts = Contract.objects.filter(activation=True)[:limit]

        self.stdout.write(f"=== ContractPrice payment_amounts 상태 확인 ===")
        self.stdout.write(f"확인 시간: {timezone.now()}")
        self.stdout.write(f"확인 대상: {len(contracts)}개 계약\n")

        for i, contract in enumerate(contracts, 1):
            self.stdout.write(f"[{i}] 계약 ID: {contract.id}")
            self.stdout.write(f"    계약번호: {contract.serial_number}")
            self.stdout.write(f"    프로젝트: {contract.project.name}")
            self.stdout.write(f"    유닛타입: {contract.unit_type.name if contract.unit_type else 'None'}")

            try:
                contract_price = ContractPrice.objects.get(contract=contract)
                self.stdout.write(f"    ContractPrice ID: {contract_price.id}")
                self.stdout.write(f"    분양가격: {contract_price.price:,}원")
                self.stdout.write(f"    캐시 유효성: {contract_price.is_cache_valid}")
                self.stdout.write(f"    계산일시: {contract_price.calculated_at}")

                if contract_price.payment_amounts:
                    self.stdout.write(f"    payment_amounts: {len(contract_price.payment_amounts)}개 항목")
                    total_amount = sum(contract_price.payment_amounts.values())
                    self.stdout.write(f"    총 납부금액: {total_amount:,}원")

                    # 처음 3개 항목만 표시
                    items = list(contract_price.payment_amounts.items())[:3]
                    for pay_time, amount in items:
                        self.stdout.write(f"        {pay_time}회차: {amount:,}원")
                    if len(contract_price.payment_amounts) > 3:
                        self.stdout.write(f"        ... (총 {len(contract_price.payment_amounts)}개 회차)")
                else:
                    self.stdout.write(f"    payment_amounts: 비어있음 {contract_price.payment_amounts}")

            except ContractPrice.DoesNotExist:
                self.stdout.write(f"    ContractPrice: 없음")

            self.stdout.write("")  # 빈 줄

        # 전체 통계
        total_contracts = Contract.objects.filter(activation=True).count()
        total_contract_prices = ContractPrice.objects.count()
        valid_cache_count = ContractPrice.objects.filter(is_cache_valid=True).count()
        with_payment_amounts = ContractPrice.objects.exclude(payment_amounts={}).count()

        self.stdout.write("=== 전체 통계 ===")
        self.stdout.write(f"활성 계약 수: {total_contracts}")
        self.stdout.write(f"ContractPrice 수: {total_contract_prices}")
        self.stdout.write(f"캐시 유효한 수: {valid_cache_count}")
        self.stdout.write(f"payment_amounts 있는 수: {with_payment_amounts}")
        self.stdout.write(f"payment_amounts 없는 수: {total_contract_prices - with_payment_amounts}")