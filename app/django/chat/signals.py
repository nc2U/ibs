from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.models import ChatMessage
from chat.tasks import send_chat_push_notification


@receiver(post_save, sender=ChatMessage)
def trigger_chat_push_notification(sender, instance, created, **kwargs):
    """
    ChatMessage가 생성되면(WebSocket 또는 REST API) 백그라운드 Celery로 FCM 푸시 발송 트리거
    """
    if created:
        send_chat_push_notification.delay(instance.id)
