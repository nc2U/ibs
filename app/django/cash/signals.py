from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import CashBook, ProjectCashBook
from _utils.slack_notifications import send_slack_notification


@receiver(post_save, sender=CashBook, dispatch_uid="cashbook_slack_notification")
def notify_cashbook_change(sender, instance, created, raw=False, **kwargs):
    """CashBook 등록/편집 시 Slack 알림"""
    if raw:
        return

    # Skip individual notifications during bulk import
    from .resources import is_bulk_import_active
    if is_bulk_import_active():
        return

    action = "등록" if created else "편집"
    send_slack_notification(instance, action, instance.creator)


@receiver(post_save, sender=ProjectCashBook, dispatch_uid="project_cashbook_slack_notification")
def notify_project_cashbook_change(sender, instance, created, raw=False, **kwargs):
    """ProjectCashBook 등록/편집 시 Slack 알림"""
    if raw:
        return

    # Skip individual notifications during bulk import
    from .resources import is_bulk_import_active
    if is_bulk_import_active():
        return

    action = "등록" if created else "편집"
    send_slack_notification(instance, action, instance.creator)


@receiver(post_delete, sender=CashBook, dispatch_uid="cashbook_slack_delete_notification")
def notify_cashbook_delete(sender, instance, **kwargs):
    """CashBook 삭제 시 Slack 알림"""
    # Skip individual notifications during bulk import
    from .resources import is_bulk_import_active
    if is_bulk_import_active():
        return

    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))


@receiver(post_delete, sender=ProjectCashBook, dispatch_uid="project_cashbook_slack_delete_notification")
def notify_project_cashbook_delete(sender, instance, **kwargs):
    """ProjectCashBook 삭제 시 Slack 알림"""
    # Skip individual notifications during bulk import
    from .resources import is_bulk_import_active
    if is_bulk_import_active():
        return

    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))
