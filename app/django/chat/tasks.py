import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from chat.models import ChatRoom, ChatMessage
from _utils.push_service import send_push_notification

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_chat_push_notification(self, message_id):
    """
    채팅 메시지 생성 시 대화방 멤버들에게 FCM 모바일 푸시 알림 비동기 전송
    - 발신자 본인은 제외
    - 알림 끄기(is_muted=True) 한 멤버는 제외
    """
    try:
        msg = ChatMessage.objects.select_related('room', 'sender').get(pk=message_id)
        room = msg.room
        sender = msg.sender
        sender_name = sender.profile.name if (sender and hasattr(sender, 'profile') and sender.profile.name) else (sender.username if sender else '알 수 없음')

        # 알림 수신 대상자 (발신자 제외 & 알림 켜진 멤버)
        if room.room_type == 'direct':
            target_memberships = room.memberships.exclude(user=sender).filter(is_muted=False)
            target_user_ids = list(target_memberships.values_list('user_id', flat=True))
            title = f"{sender_name}"
        elif room.room_type == 'channel':
            # 워크스페이스 채널인 경우 워크스페이스 소속 멤버들 중 발신자 제외
            if room.project:
                # 워크스페이스 전체 멤버 ID (하위 상속 포함)
                all_mems = room.project.all_members()
                pjt_member_ids = [m['user']['pk'] for m in all_mems]
                # 알림 끈 멤버 제외
                muted_user_ids = list(room.memberships.filter(is_muted=True).values_list('user_id', flat=True))
                target_user_ids = [uid for uid in set(pjt_member_ids) if uid != (sender.pk if sender else 0) and uid not in muted_user_ids]
            else:
                target_memberships = room.memberships.exclude(user=sender).filter(is_muted=False)
                target_user_ids = list(target_memberships.values_list('user_id', flat=True))
            title = f"#{room.project.name if room.project else room.title} ({sender_name})"
        else:
            target_memberships = room.memberships.exclude(user=sender).filter(is_muted=False)
            target_user_ids = list(target_memberships.values_list('user_id', flat=True))
            title = f"{room.title or '그룹 채팅'} ({sender_name})"

        if not target_user_ids:
            return f"No target users for chat message #{message_id}"

        # 메시지 미리보기 내용
        if msg.message_type == 'image':
            body = "📷 사진을 보냈습니다."
        elif msg.message_type == 'file':
            body = f"📎 파일: {msg.file_name or '첨부파일'}"
        elif msg.ref_id:
            body = f"📌 [{msg.ref_title}] {msg.content}"
        else:
            body = msg.content[:100]

        send_push_notification(
            user_ids=target_user_ids,
            title=title,
            body=body,
            category='chat',
            target_type='chat_room',
            target_id=str(room.id),
            extra_data={
                'room_id': str(room.id),
                'room_type': room.room_type,
                'message_id': str(msg.id),
            },
            create_notification_record=False,
        )
        return f"Chat push sent for message #{message_id} to {len(target_user_ids)} users"
    except ChatMessage.DoesNotExist:
        logger.warning(f"ChatMessage #{message_id} does not exist for push notification.")
    except Exception as e:
        logger.error(f"Error sending chat push notification: {e}")
        raise self.retry(exc=e)
