from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError

from ledger.models import ProjectAccountingEntry
from .models import ContractPayment


@receiver(post_save, sender=ProjectAccountingEntry)
@transaction.atomic
def manage_contract_payment_auto_sync(sender, instance, created, **kwargs):
    """
    ProjectAccountingEntry의 is_payment 상태 변경에 따른 ContractPayment 자동 동기화

    시나리오:
    1. is_payment=True → ContractPayment 베이스 인스턴스 자동 생성
    2. is_payment=False → 기존 ContractPayment에 mismatch 플래그 표시
    3. is_payment=False → True → mismatch 플래그 해제
    """

    # account가 없으면 처리하지 않음
    if not instance.account:
        return

    is_payment_account = instance.account.is_payment
    has_contract_payment = hasattr(instance, 'contract_payment')

    if is_payment_account and not has_contract_payment:
        # 시나리오 1: is_payment=True이지만 ContractPayment가 없는 경우 → 베이스 인스턴스 생성
        try:
            ContractPayment.objects.create(
                accounting_entry=instance,
                project=instance.project,
                is_payment_mismatch=False,  # 새로 생성하므로 일치 상태
                creator=None,  # Signal에서는 creator 정보가 없음
            )
        except ValidationError:
            # 이미 존재하는 경우 등의 예외 상황은 무시
            pass

    elif is_payment_account and has_contract_payment:
        # 시나리오 3: is_payment=True이고 ContractPayment가 있는 경우 → mismatch 해제
        contract_payment = instance.contract_payment
        if contract_payment.is_payment_mismatch:
            contract_payment.is_payment_mismatch = False
            contract_payment.save(update_fields=['is_payment_mismatch', 'updated_at'])

    elif not is_payment_account and has_contract_payment:
        # 시나리오 2: is_payment=False이지만 ContractPayment가 있는 경우 → mismatch 플래그 표시
        contract_payment = instance.contract_payment
        if not contract_payment.is_payment_mismatch:
            contract_payment.is_payment_mismatch = True
            contract_payment.save(update_fields=['is_payment_mismatch', 'updated_at'])
