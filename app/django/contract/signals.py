from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from _utils.slack_notifications import send_slack_notification
from .models import Contract, Succession, ContractorRelease


@receiver(post_save, sender=Contract, dispatch_uid="contract_slack_notification")
def notify_contract_change(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    action = "등록" if created else "편집"
    send_slack_notification(instance, action, instance.creator)


@receiver(post_delete, sender=Contract, dispatch_uid="contract_delete_slack_notification")
def notify_contract_delete(sender, instance, **kwargs):
    send_slack_notification(instance, "삭제", instance.creator)


@receiver(post_save, sender=Succession, dispatch_uid="succession_slack_notification")
def notify_succession_change(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    action = "등록" if created else "편집"
    send_slack_notification(instance, action, instance.creator)


@receiver(post_delete, sender=Succession, dispatch_uid="succession_delete_slack_notification")
def notify_succession_delete(sender, instance, **kwargs):
    send_slack_notification(instance, "삭제", instance.creator)


@receiver(post_save, sender=ContractorRelease, dispatch_uid="contractor_release_slack_notification")
def notify_contractor_release_change(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    action = "등록" if created else "편집"
    send_slack_notification(instance, action, instance.creator)


@receiver(post_delete, sender=ContractorRelease, dispatch_uid="contractor_release_delete_slack_notification")
def notify_contractor_release_delete(sender, instance, **kwargs):
    send_slack_notification(instance, "삭제", instance.creator)
