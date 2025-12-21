import threading
from payment.models import ContractPayment

# Thread-local storage for bulk import flags
_thread_locals = threading.local()

def is_bulk_import_active():
    """Check if bulk import is currently active in this thread"""
    return getattr(_thread_locals, 'bulk_import_active', False)

def set_bulk_import_active(active=True):
    """Set bulk import flag for current thread"""
    _thread_locals.bulk_import_active = active

def _sync_contract_payment_for_entry(instance):
    """
    Helper function to synchronize ContractPayment based on a ProjectAccountingEntry instance.
    """
    if not instance.account:
        return

    is_payment_account = instance.account.is_payment

    if is_payment_account:
        bank_transaction = instance.related_transaction
        creator = bank_transaction.creator if bank_transaction else None
        defaults = {
            'project': instance.project,
            'is_payment_mismatch': False,
            'creator': creator,
            'contract': instance.contract,
            'installment_order': instance.installment_order,
        }
        contract_payment, created = ContractPayment.objects.get_or_create(
            accounting_entry=instance,
            defaults=defaults
        )

        update_fields = []
        if not created:
            if contract_payment.contract != instance.contract:
                contract_payment.contract = instance.contract
                update_fields.append('contract')
            
            if contract_payment.is_payment_mismatch:
                contract_payment.is_payment_mismatch = False
                update_fields.append('is_payment_mismatch')
            
            if update_fields:
                contract_payment.save(update_fields=update_fields + ['updated_at'])
    else:
        try:
            contract_payment = instance.contract_payment
            update_fields = []
            if not contract_payment.is_payment_mismatch:
                contract_payment.is_payment_mismatch = True
                update_fields.append('is_payment_mismatch')
            
            if contract_payment.contract != instance.contract:
                contract_payment.contract = instance.contract
                update_fields.append('contract')
            
            if update_fields:
                contract_payment.save(update_fields=update_fields + ['updated_at'])
        except ContractPayment.DoesNotExist:
            pass
