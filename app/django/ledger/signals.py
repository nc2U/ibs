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
        # is_balanced 값 계산
        try:
            validation_result = transaction.validate_accounting_entries()
            new_is_balanced = validation_result['is_valid']

            # 값이 실제로 변경된 경우에만 업데이트 (Slack 알림 중복 방지)
            if transaction.is_balanced != new_is_balanced:
                transaction.is_balanced = new_is_balanced
                # update_fields 사용하여 is_balanced만 업데이트하고 signal 트리거 방지

                # 거래 타입에 따라 적절한 signal handler disconnect/reconnect
                if isinstance(transaction, CompanyBankTransaction):
                    post_save.disconnect(notify_bank_transaction_change, sender=CompanyBankTransaction)
                    transaction.save(update_fields=['is_balanced'])
                    post_save.connect(notify_bank_transaction_change, sender=CompanyBankTransaction)
                elif isinstance(transaction, ProjectBankTransaction):
                    post_save.disconnect(notify_project_bank_transaction_change, sender=ProjectBankTransaction)
                    transaction.save(update_fields=['is_balanced'])
                    post_save.connect(notify_project_bank_transaction_change, sender=ProjectBankTransaction)
        except (AttributeError, NotImplementedError):
            # validate_accounting_entries가 구현되지 않은 경우 무시
            pass


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
