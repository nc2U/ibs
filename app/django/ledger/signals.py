from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from _utils.slack_notifications import send_slack_notification
from .models import CompanyBankTransaction, ProjectBankTransaction
from .resources import is_bulk_import_active


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
