from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.models import ChatMessage
from chat.tasks import send_chat_push_notification


@receiver(post_save, sender=ChatMessage)
def trigger_chat_push_notification(sender, instance, created, **kwargs):
    """
    ChatMessage가 생성되면(WebSocket 또는 REST API) 백그라운드 Celery로 FCM 푸시 발송 트리거
    - DB 트랜잭션 커밋 완료 후 실행되도록 on_commit 보장 (DoesNotExist 방지)
    """
    if created:
        transaction.on_commit(lambda: send_chat_push_notification.delay(instance.id))
