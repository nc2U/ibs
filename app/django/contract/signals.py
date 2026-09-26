from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from _utils.slack_notifications import send_slack_notification
from .models import Contract, Succession, ContractorRelease


@receiver(post_save, sender=Contract, dispatch_uid="contract_slack_notification")
def notify_contract_change(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    action = "등록" if created else "편집"
    # [H-3] transaction.on_commit: DB 커밋 후 Slack 호출 → 네트워크 오류로 인한 트랜잭션 롤백 위험 제거
    transaction.on_commit(lambda: send_slack_notification(instance, action, instance.creator))


@receiver(post_delete, sender=Contract, dispatch_uid="contract_delete_slack_notification")
def notify_contract_delete(sender, instance, **kwargs):
    # [H-3] post_delete는 트랜잭션 내에서 발생하므로 on_commit으로 안전하게 처리
    transaction.on_commit(lambda: send_slack_notification(instance, "삭제", instance.creator))


@receiver(post_save, sender=Succession, dispatch_uid="succession_slack_notification")
def notify_succession_change(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    action = "등록" if created else "편집"
    # 편집 시에는 updator, 등록 시에는 creator 사용
    user = instance.creator if created else (instance.updator or instance.creator)
    # [H-3] transaction.on_commit으로 래핑
    transaction.on_commit(lambda: send_slack_notification(instance, action, user))


@receiver(post_delete, sender=Succession, dispatch_uid="succession_delete_slack_notification")
def notify_succession_delete(sender, instance, **kwargs):
    transaction.on_commit(lambda: send_slack_notification(instance, "삭제", instance.creator))


@receiver(post_save, sender=ContractorRelease, dispatch_uid="contractor_release_slack_notification")
def notify_contractor_release_change(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    action = "등록" if created else "편집"
    # 편집 시에는 updator, 등록 시에는 creator 사용
    user = instance.creator if created else (instance.updator or instance.creator)
    # [H-3] transaction.on_commit으로 래핑
    transaction.on_commit(lambda: send_slack_notification(instance, action, user))


@receiver(post_delete, sender=ContractorRelease, dispatch_uid="contractor_release_delete_slack_notification")
def notify_contractor_release_delete(sender, instance, **kwargs):
    transaction.on_commit(lambda: send_slack_notification(instance, "삭제", instance.creator))
