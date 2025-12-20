from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

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

    if is_payment_account:
        # is_payment 계정인 경우, ContractPayment 객체를 가져오거나 생성 (get_or_create 사용)
        defaults = {
            'project': instance.project,
            'is_payment_mismatch': False,
            'creator': instance.creator,
            'contract': instance.contract,  # Initial contract assignment
            'installment_order': instance.installment_order,  # 데이터 이관용 코드 - 이관 후 삭제
            'refund_contractor': instance.refund_contractor  # 데이터 이관용 코드 - 이관 후 삭제
        }
        contract_payment, created = ContractPayment.objects.get_or_create(
            accounting_entry=instance,
            defaults=defaults
        )

        update_fields = []
        # If it was not newly created, we might need to update its fields
        if not created:
            # Sync contract if it changed on ProjectAccountingEntry
            if contract_payment.contract != instance.contract:
                contract_payment.contract = instance.contract
                update_fields.append('contract')

            # Reset mismatch flag if it was True
            if contract_payment.is_payment_mismatch:
                contract_payment.is_payment_mismatch = False
                update_fields.append('is_payment_mismatch')

            if update_fields:
                contract_payment.save(update_fields=update_fields + ['updated_at'])

    else:  # not is_payment_account
        # Try to get existing contract_payment
        try:
            contract_payment = instance.contract_payment
            # If a ContractPayment exists for a non-payment account, its contract field should sync with instance.contract
            # and it should be flagged as mismatched if it's not already.
            update_fields = []
            if not contract_payment.is_payment_mismatch:
                contract_payment.is_payment_mismatch = True
                update_fields.append('is_payment_mismatch')

            # Sync contract or null. This handles the user's specific request for existing ContractPayments.
            if contract_payment.contract != instance.contract:
                contract_payment.contract = instance.contract
                update_fields.append('contract')

            if update_fields:
                contract_payment.save(update_fields=update_fields + ['updated_at'])

        except ContractPayment.DoesNotExist:
            # is_payment 계정이 아니며 ContractPayment도 없으므로 아무것도 하지 않음
            pass
