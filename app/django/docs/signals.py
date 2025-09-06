from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .models import LawsuitCase, Document
from _utils.slack_notifications import send_slack_notification


@receiver(post_save, sender=LawsuitCase, dispatch_uid="lawsuitcase_slack_notification")
def notify_lawsuitcase_change(sender, instance, created, raw=False, **kwargs):
    """LawsuitCase 생성/수정 시 Slack 알림"""
    if raw:
        return

    action = "생성" if created else "수정"
    send_slack_notification(instance, action, instance.user)


# Document의 이전 상태를 저장하는 딕셔너리
_document_pre_save_state = {}


@receiver(pre_save, sender=Document, dispatch_uid="document_pre_save_state")
def store_document_pre_save_state(sender, instance, **kwargs):
    """Document 저장 전 상태 저장"""
    if instance.pk:
        try:
            old_instance = Document.objects.get(pk=instance.pk)
            _document_pre_save_state[instance.pk] = {
                'title': old_instance.title,
                'content': old_instance.content,
                'doc_type_id': old_instance.doc_type_id,
                'category_id': old_instance.category_id,
                'lawsuit_id': old_instance.lawsuit_id,
                'execution_date': old_instance.execution_date,
                'is_secret': old_instance.is_secret,
                'password': old_instance.password,
                'is_blind': old_instance.is_blind,
                'hit': old_instance.hit,
            }
        except Document.DoesNotExist:
            pass


@receiver(post_save, sender=Document, dispatch_uid="document_slack_notification")
def notify_document_change(sender, instance, created, raw=False, update_fields=None, **kwargs):
    """Document 생성/수정 시 Slack 알림"""
    if raw:
        return

    try:
        # 생성이 아닌 경우 hit만 변경되었는지 확인
        if not created and instance.pk in _document_pre_save_state:
            old_state = _document_pre_save_state[instance.pk]
            
            # hit를 제외한 필드들이 변경되었는지 확인
            meaningful_fields = ['title', 'content', 'doc_type_id', 'category_id', 
                               'lawsuit_id', 'execution_date', 'is_secret', 'password', 'is_blind']
            
            has_meaningful_change = False
            for field in meaningful_fields:
                if old_state.get(field) != getattr(instance, field):
                    has_meaningful_change = True
                    break
            
            # hit만 변경되고 다른 중요한 필드는 변경되지 않았으면 알림 제외
            if not has_meaningful_change:
                return

        action = "생성" if created else "수정"
        send_slack_notification(instance, action, instance.user)
        
    finally:
        # 저장된 상태 정리
        if instance.pk in _document_pre_save_state:
            del _document_pre_save_state[instance.pk]


@receiver(post_delete, sender=LawsuitCase, dispatch_uid="lawsuitcase_slack_delete_notification")
def notify_lawsuitcase_delete(sender, instance, **kwargs):
    """LawsuitCase 삭제 시 Slack 알림"""
    send_slack_notification(instance, "삭제", getattr(instance, 'user', None))


@receiver(post_delete, sender=Document, dispatch_uid="document_slack_delete_notification")
def notify_document_delete(sender, instance, **kwargs):
    """Document 삭제 시 Slack 알림"""
    send_slack_notification(instance, "삭제", getattr(instance, 'user', None))