from django.apps import apps
from django.db import transaction
import threading
import logging

from payment.models import ContractPayment

logger = logging.getLogger(__name__)
_thread_locals = threading.local()


def trigger_sync_contract_payment(instance):
    if is_bulk_import_active():
        return
    _sync_contract_payment_for_entry(instance)


def is_bulk_import_active():
    """Check if bulk import is currently active in this thread"""
    return getattr(_thread_locals, 'bulk_import_active', False)


def set_bulk_import_active(active=True):
    """Set bulk import flag for current thread"""
    _thread_locals.bulk_import_active = active


@transaction.atomic
def _sync_contract_payment_for_entry(instance):
    """
    Helper function to synchronize ContractPayment based on a ProjectAccountingEntry instance.
    """
    if not instance.account:
        return

    # ✅ 런타임 안전 모델 로딩
    ProjectAccountingEntry = apps.get_model(
        'ledger', 'ProjectAccountingEntry'
    )

    # Re-fetch an instance to ensure it's fully committed/loaded from the current transaction's perspective.
    # This helps prevent "not a valid choice" errors in OneToOneField assignments during bulk imports.
    # ✅ PK 기준 재조회 (import-export FK validation 문제 해결)
    if instance.pk:  # Only try to fetch if it has been saved (i.e., has a primary key)
        try:
            instance = ProjectAccountingEntry.objects.select_related(
                'account', 'contract', 'project'
            ).get(pk=instance.pk)
        except ProjectAccountingEntry.DoesNotExist:
            logger.warning(
                f"ProjectAccountingEntry(pk={instance.pk}) not found. Skip sync."
            )
            return

    is_payment_account = instance.account.is_payment

    if is_payment_account:
        bank_transaction = instance.related_transaction
        creator = bank_transaction.creator if bank_transaction else None
        deal_date = bank_transaction.deal_date if bank_transaction else None
        defaults = {
            'project': instance.project,
            'contract': instance.contract,
            'deal_date': deal_date,
            'is_payment_mismatch': False,
            'creator': creator,
        }
        contract_payment, created = ContractPayment.objects.get_or_create(
            accounting_entry=instance,
            defaults=defaults
        )

        update_fields = []
        if not created:
            # project 동기화 (데이터 정합성)
            if contract_payment.project_id != instance.project_id:
                contract_payment.project = instance.project
                update_fields.append('project')

            # contract 동기화
            if contract_payment.contract_id != instance.contract_id:
                contract_payment.contract = instance.contract
                update_fields.append('contract')

            # deal_date 동기화
            if bank_transaction and contract_payment.deal_date != bank_transaction.deal_date:
                contract_payment.deal_date = bank_transaction.deal_date
                update_fields.append('deal_date')

            if contract_payment.is_payment_mismatch:
                contract_payment.is_payment_mismatch = False
                update_fields.append('is_payment_mismatch')

            if update_fields:
                contract_payment.save(update_fields=update_fields + ['updated_at'])
    else:
        try:
            contract_payment = instance.contract_payment
        except ContractPayment.DoesNotExist:
            return

        update_fields = []

        # project 동기화 (데이터 정합성)
        if contract_payment.project_id != instance.project_id:
            contract_payment.project = instance.project
            update_fields.append('project')

        # contract 동기화
        if contract_payment.contract_id != instance.contract_id:
            contract_payment.contract = instance.contract
            update_fields.append('contract')

        # deal_date 동기화
        bank_transaction = instance.related_transaction
        if bank_transaction and contract_payment.deal_date != bank_transaction.deal_date:
            contract_payment.deal_date = bank_transaction.deal_date
            update_fields.append('deal_date')

        if not contract_payment.is_payment_mismatch:
            contract_payment.is_payment_mismatch = True
            update_fields.append('is_payment_mismatch')

        if update_fields:
            contract_payment.save(update_fields=update_fields + ['updated_at'])
