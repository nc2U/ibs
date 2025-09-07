from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Site, SiteOwner, SiteContract
from _utils.slack_notifications import send_slack_notification


@receiver(post_save, sender=Site, dispatch_uid="site_slack_notification")
def notify_site_change(sender, instance, created, raw=False, **kwargs):
    """Site 등록/편집 시 Slack 알림"""
    if raw:
        return

    action = "등록" if created else "편집"
    send_slack_notification(instance, action, instance.creator)


@receiver(post_save, sender=SiteOwner, dispatch_uid="site_owner_slack_notification")
def notify_site_owner_change(sender, instance, created, raw=False, **kwargs):
    """SiteOwner 등록/편집 시 Slack 알림"""
    if raw:
        return

    action = "등록" if created else "편집"
    send_slack_notification(instance, action, instance.creator)


@receiver(post_save, sender=SiteContract, dispatch_uid="site_contract_slack_notification")
def notify_site_contract_change(sender, instance, created, raw=False, **kwargs):
    """SiteContract 등록/편집 시 Slack 알림"""
    if raw:
        return

    action = "등록" if created else "편집"
    send_slack_notification(instance, action, instance.creator)


@receiver(post_delete, sender=Site, dispatch_uid="site_slack_delete_notification")
def notify_site_delete(sender, instance, **kwargs):
    """Site 삭제 시 Slack 알림"""
    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))


@receiver(post_delete, sender=SiteOwner, dispatch_uid="site_owner_slack_delete_notification")
def notify_site_owner_delete(sender, instance, **kwargs):
    """SiteOwner 삭제 시 Slack 알림"""
    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))


@receiver(post_delete, sender=SiteContract, dispatch_uid="site_contract_slack_delete_notification")
def notify_site_contract_delete(sender, instance, **kwargs):
    """SiteContract 삭제 시 Slack 알림"""
    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))
