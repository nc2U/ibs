import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from chat.models import ChatRoom, ChatRoomMember, ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):
    """
    실시간 대화방 WebSocket Consumer
    - 연결: /ws/chat/<room_id>/
    - 이벤트:
      1. chat.message (새 메시지 전송 및 실시간 수신)
      2. typing (상대방 입력 중 알림)
      3. read (메시지 읽음 위치 갱신 동기화)
    """

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_room_{self.room_id}'
        self.user = self.scope.get('user', AnonymousUser())

        # 인증되지 않은 사용자는 연결 거부
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # 방 접근 권한 검증
        can_access = await self.check_room_access(self.room_id, self.user)
        if not can_access:
            await self.close(code=4003)
            return

        # 채널 레이어 그룹 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except Exception:
            return

        event_type = data.get('type', 'chat_message')

        if event_type == 'chat_message':
            content = data.get('content', '').strip()
            message_type = data.get('message_type', 'text')
            ref_id = data.get('ref_id')
            ref_title = data.get('ref_title', '')
            ref_sub = data.get('ref_sub', '')
            reply_to_id = data.get('reply_to_id') or data.get('reply_to')

            if not content and message_type == 'text':
                return

            # DB에 메시지 저장
            msg = await self.save_message(
                room_id=self.room_id,
                user=self.user,
                content=content,
                message_type=message_type,
                ref_id=ref_id,
                ref_title=ref_title,
                ref_sub=ref_sub,
                reply_to_id=reply_to_id,
            )

            # 같은 대화방 모든 접속자에게 브로드캐스팅
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'message': msg,
                }
            )

        elif event_type == 'typing':
            # 상대방 입력 중 브로드캐스팅
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_typing',
                    'user_id': self.user.pk,
                    'username': self.user.username,
                    'is_typing': data.get('is_typing', True),
                }
            )

        elif event_type == 'read':
            last_message_id = data.get('last_message_id', 0)
            if last_message_id:
                await self.update_last_read(self.room_id, self.user, last_message_id)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_read',
                        'user_id': self.user.pk,
                        'last_message_id': last_message_id,
                    }
                )

    # ── Channel Layer Handler ──────────────────────────────────────────

    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'data': event['message'],
        }))

    async def broadcast_typing(self, event):
        # 자신이 보낸 타이핑 이벤트는 제외
        if event['user_id'] != self.user.pk:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def broadcast_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read',
            'user_id': event['user_id'],
            'last_message_id': event['last_message_id'],
        }))

    # ── Database Sync Helpers ─────────────────────────────────────────

    @database_sync_to_async
    def check_room_access(self, room_id, user):
        if user.is_superuser:
            return True
        room = ChatRoom.objects.filter(pk=room_id).first()
        if not room:
            return False
        if room.room_type == 'channel':
            if not room.project:
                return False
            # 공용 채널이 꺼져있으면 접속 불가
            if not room.project.chat_channel_enabled:
                return False
            # 사용자가 소속된 워크스페이스(상속 포함)인지 검증
            my_pjt_ids = list(user.member_project_ids()) if hasattr(user, 'member_project_ids') else []
            return room.project_id in my_pjt_ids
        return room.members.filter(pk=user.pk).exists()

    @database_sync_to_async
    def save_message(self, room_id, user, content, message_type, ref_id, ref_title, ref_sub, reply_to_id):
        room = ChatRoom.objects.get(pk=room_id)
        msg = ChatMessage.objects.create(
            room=room,
            sender=user,
            content=content,
            message_type=message_type,
            ref_id=ref_id,
            ref_title=ref_title,
            ref_sub=ref_sub,
            reply_to_id=reply_to_id,
        )
        room.save(update_fields=['updated'])

        # 발신자의 last_read_message_id를 본인 메시지 ID로 자동 갱신 및 숨김 해제
        membership, _ = ChatRoomMember.objects.get_or_create(room=room, user=user)
        membership.last_read_message_id = msg.id
        membership.is_hidden = False
        membership.save(update_fields=['last_read_message_id', 'is_hidden'])

        # 모든 참여 멤버의 숨김(is_hidden) 상태 자동 해제 (새 메시지 도착 시 목록 복원)
        room.memberships.filter(is_hidden=True).update(is_hidden=False)

        reply_to_detail = None
        if reply_to_id:
            try:
                target = ChatMessage.objects.select_related('sender__profile').get(pk=reply_to_id)
                target_sender_name = target.sender.profile.name if (target.sender and hasattr(target.sender, 'profile') and target.sender.profile.name) else (target.sender.username if target.sender else '알 수 없음')
                reply_to_detail = {
                    'id': target.id,
                    'sender_name': target_sender_name,
                    'content': target.content[:60] if target.content else (f"[파일] {target.file_name}" if target.file_name else '[첨부]'),
                    'message_type': target.message_type,
                }
            except ChatMessage.DoesNotExist:
                pass

        return {
            'id': msg.id,
            'room_id': room.id,
            'sender': {
                'pk': user.pk,
                'username': user.username,
            },
            'message_type': msg.message_type,
            'content': msg.content,
            'file': msg.file.url if msg.file else None,
            'file_name': msg.file_name,
            'file_size': msg.file_size,
            'ref_id': msg.ref_id,
            'ref_title': msg.ref_title,
            'ref_sub': msg.ref_sub,
            'reply_to': msg.reply_to_id,
            'reply_to_detail': reply_to_detail,
            'created': msg.created.isoformat(),
        }

    @database_sync_to_async
    def update_last_read(self, room_id, user, last_message_id):
        membership, _ = ChatRoomMember.objects.get_or_create(room_id=room_id, user=user)
        if int(last_message_id) > membership.last_read_message_id:
            membership.last_read_message_id = int(last_message_id)
            membership.save(update_fields=['last_read_message_id'])
