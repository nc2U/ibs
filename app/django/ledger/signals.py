from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from _utils.slack_notifications import send_slack_notification
from .models import CompanyBankTransaction, ProjectBankTransaction, CompanyAccountingEntry, ProjectAccountingEntry
from .services.sync_payment_contract import is_bulk_import_active


@receiver(post_save, sender=CompanyBankTransaction, dispatch_uid="bank_transaction_slack_notification")
def notify_bank_transaction_change(sender, instance, created, raw=False, **kwargs):
    """bank_transaction 등록/편집 시 Slack 알림"""
    if raw:
        return

    # Skip individual notifications during bulk import
    if is_bulk_import_active():
        return

    action = "등록" if created else "편집"
    user = instance.creator if created else instance.updator
    send_slack_notification(instance, action, user)


@receiver(post_save, sender=ProjectBankTransaction, dispatch_uid="project_bank_transaction_slack_notification")
def notify_project_bank_transaction_change(sender, instance, created, raw=False, **kwargs):
    """Project_bank_transaction 등록/편집 시 Slack 알림"""
    if raw:
        return

    # Skip individual notifications during bulk import
    if is_bulk_import_active():
        return

    action = "등록" if created else "편집"
    user = instance.creator if created else instance.updator
    send_slack_notification(instance, action, user)


@receiver(post_delete, sender=CompanyBankTransaction, dispatch_uid="bank_transaction_slack_delete_notification")
def notify_bank_transaction_delete(sender, instance, **kwargs):
    """bank_transaction 삭제 시 Slack 알림"""
    # Skip individual notifications during bulk import
    if is_bulk_import_active():
        return

    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))


@receiver(post_delete, sender=ProjectBankTransaction, dispatch_uid="project_bank_transaction_slack_delete_notification")
def notify_project_bank_transaction_delete(sender, instance, **kwargs):
    """Project_bank_transaction 삭제 시 Slack 알림"""
    # Skip individual notifications during bulk import
    if is_bulk_import_active():
        return

    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))


# --- is_balanced 자동 업데이트를 위한 시그널 ---

def _update_bank_transaction_balance(entry_instance):
    """
    AccountingEntry 인스턴스에 연결된 BankTransaction의 is_balanced를 업데이트합니다.
    """
    # Skip updates during bulk import to avoid performance issues
    if is_bulk_import_active():
        return

    transaction = entry_instance.related_transaction
    if transaction:
        # BankTransaction의 save 메서드를 호출하여 is_balanced를 재계산하고 저장
        transaction.save()


@receiver(post_save, sender=CompanyAccountingEntry)
@receiver(post_save, sender=ProjectAccountingEntry)
def on_accounting_entry_save(sender, instance, created, raw=False, **kwargs):
    """CompanyAccountingEntry 또는 ProjectAccountingEntry 저장 후 호출됩니다."""
    if raw:
        return
    _update_bank_transaction_balance(instance)


@receiver(post_delete, sender=CompanyAccountingEntry)
@receiver(post_delete, sender=ProjectAccountingEntry)
def on_accounting_entry_delete(sender, instance, **kwargs):
    """CompanyAccountingEntry 또는 ProjectAccountingEntry 삭제 후 호출됩니다."""
    _update_bank_transaction_balance(instance)
