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
        contract_payment, created = ContractPayment.objects.get_or_create(
            accounting_entry=instance,
            defaults={
                'project': instance.project,
                'is_payment_mismatch': False,
                'creator': None,
            }
        )

        # 이미 존재하던 객체이고, mismatch 상태였다면 정상으로 되돌림
        if not created and contract_payment.is_payment_mismatch:
            contract_payment.is_payment_mismatch = False
            contract_payment.save(update_fields=['is_payment_mismatch', 'updated_at'])

    else:  # is_payment 계정이 아닌 경우
        # 관련 ContractPayment가 존재하고, mismatch 상태가 아니라면 mismatch로 변경
        try:
            contract_payment = instance.contract_payment
            if not contract_payment.is_payment_mismatch:
                contract_payment.is_payment_mismatch = True
                contract_payment.save(update_fields=['is_payment_mismatch', 'updated_at'])
        except ContractPayment.DoesNotExist:
            # is_payment 계정이 아니며 ContractPayment도 없으므로 아무것도 하지 않음
            pass
