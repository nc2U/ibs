import html
from django.utils.html import strip_tags
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver

from _utils.slack_notifications import send_slack_notification
from work.models.logging import ActivityLogEntry
from .models import LawsuitCase, Document


@receiver(post_save, sender=LawsuitCase, dispatch_uid="lawsuitcase_slack_notification")
def notify_lawsuitcase_change(sender, instance, created, raw=False, **kwargs):
    """LawsuitCase 등록/편집 시 Slack 알림"""
    if raw:
        return

    action = "등록" if created else "편집"
    user = instance.creator if created else (instance.updator or instance.creator)
    send_slack_notification(instance, action, user)


@receiver(pre_save, sender=Document, dispatch_uid="document_pre_save_state")
def store_document_pre_save_state(sender, instance, **kwargs):
    """Document 저장 전 상태 저장 (인스턴스 속성 바인딩으로 동시성 보장)"""
    if instance.pk:
        try:
            old_instance = Document.all_objects.get(pk=instance.pk)
            instance._pre_save_state = {
                'title': old_instance.title,
                'description': old_instance.description,
                'doc_type': old_instance.doc_type,
                'category_id': old_instance.category_id,
                'lawsuit_id': old_instance.lawsuit_id,
                'execution_date': old_instance.execution_date,
                'security_level': old_instance.security_level,
                'is_blind': old_instance.is_blind,
                'deleted': old_instance.deleted,
                'hit': old_instance.hit,
            }
        except Document.DoesNotExist:
            instance._pre_save_state = None


@receiver(post_save, sender=Document, dispatch_uid="document_slack_notification")
def notify_document_change(sender, instance, created, raw=False, update_fields=None, **kwargs):
    """Document 등록/편집 시 Slack 알림"""
    if raw:
        return

    try:
        old_state = getattr(instance, '_pre_save_state', None)
        # 등록이 아닌 경우 hit 또는 소프트 삭제/복원(deleted)만 변경되었는지 확인
        if not created and old_state is not None:
            meaningful_fields = ['title', 'description', 'doc_type', 'category_id',
                                 'lawsuit_id', 'execution_date', 'security_level', 'is_blind']

            has_meaningful_change = any(
                old_state.get(field) != getattr(instance, field)
                for field in meaningful_fields
            )

            # hit나 deleted만 변경되고 다른 중요한 필드는 변경되지 않았으면 알림 제외
            if not has_meaningful_change:
                return

        action = "등록" if created else "편집"
        user = instance.creator if created else (instance.updator or instance.creator)
        send_slack_notification(instance, action, user)

    finally:
        # 저장된 상태 정리
        if hasattr(instance, '_pre_save_state'):
            delattr(instance, '_pre_save_state')


@receiver(post_delete, sender=LawsuitCase, dispatch_uid="lawsuitcase_slack_delete_notification")
def notify_lawsuitcase_delete(sender, instance, **kwargs):
    """LawsuitCase 삭제 시 Slack 알림"""
    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))


@receiver(post_delete, sender=Document, dispatch_uid="document_slack_delete_notification")
def notify_document_delete(sender, instance, **kwargs):
    """Document 삭제 시 Slack 알림"""
    send_slack_notification(instance, "삭제", getattr(instance, 'creator', None))


@receiver(post_save, sender=Document, dispatch_uid="document_activity_log_changes")
def document_log_changes(sender, instance, created, **kwargs):
    """Document 생성 시 ActivityLogEntry 생성"""
    if created and instance.issue_project and instance.issue_project.status == '1':
        raw_content = instance.description or ''
        clean_summary = ' '.join(html.unescape(strip_tags(raw_content)).split())
        ActivityLogEntry.objects.create(
            sort='5', project=instance.issue_project, target_id=instance.pk,
            title=f"[문서] {instance.title}"[:250], summary=clean_summary[:150], creator=instance.creator
        )


@receiver(pre_delete, sender=Document, dispatch_uid="document_activity_log_delete")
def document_log_delete(sender, instance, **kwargs):
    """Document 삭제 전 ActivityLogEntry 제거"""
    ActivityLogEntry.objects.filter(sort='5', target_id=instance.pk).delete()
