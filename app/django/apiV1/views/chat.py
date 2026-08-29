from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from chat.models import ChatRoom, ChatRoomMember, ChatMessage
from apiV1.serializers.chat import (
    ChatRoomListSerializer,
    ChatRoomDetailSerializer,
    ChatMessageSerializer,
    ChatRoomMemberSerializer,
)


class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    메신저 대화방 ViewSet
    - list: 내가 참여 중인 대화방 또는 소속 워크스페이스 공용 채널 목록
    - create: 새 단체방 또는 1:1 DM 생성
    - read: 대화방 읽음 처리 (last_read_message_id 갱신)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return ChatRoomDetailSerializer
        return ChatRoomListSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ChatRoom.objects.none()

        # 슈퍼유저는 전체 대화방 조회 가능
        if user.is_superuser:
            return ChatRoom.objects.all().distinct()

        # 1) 내가 멤버로 속해 있는 방
        # 2) 또는 내가 소속된 워크스페이스의 공용 채널(channel)
        return ChatRoom.objects.filter(
            Q(members=user) |
            Q(room_type='channel', project__members__user=user) |
            Q(room_type='channel', project__is_public=True)
        ).distinct()

    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user)
        # 생성자 자동 멤버십 및 방장 등록
        ChatRoomMember.objects.get_or_create(
            room=room,
            user=self.request.user,
            defaults={'is_admin': True}
        )

    @action(detail=False, methods=['post'], url_path='get-or-create-dm')
    def get_or_create_dm(self, request):
        """특정 사용자와의 1:1 DM 대화방 조회 또는 자동 생성"""
        target_user_id = request.data.get('target_user_id')
        if not target_user_id:
            return Response({'error': 'target_user_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        if int(target_user_id) == request.user.pk:
            return Response({'error': '자기 자신과의 DM은 지원하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 이미 두 사람만 존재하는 DM이 있는지 검색
        existing_rooms = ChatRoom.objects.filter(
            room_type='direct',
            members=request.user
        ).filter(members__pk=target_user_id)

        if existing_rooms.exists():
            room = existing_rooms.first()
            serializer = ChatRoomListSerializer(room, context={'request': request})
            return Response(serializer.data)

        # 없으면 새로 생성
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=request.user
        )
        ChatRoomMember.objects.create(room=room, user=request.user, is_admin=True)
        ChatRoomMember.objects.create(room=room, user_id=target_user_id, is_admin=False)

        serializer = ChatRoomListSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='read')
    def mark_as_read(self, request, pk=None):
        """대화방 메시지 읽음 처리"""
        room = self.get_object()
        last_message_id = request.data.get('last_message_id')

        if not last_message_id:
            latest_msg = room.messages.order_by('-created').first()
            last_message_id = latest_msg.id if latest_msg else 0

        membership, _ = ChatRoomMember.objects.get_or_create(
            room=room,
            user=request.user
        )
        if int(last_message_id) > membership.last_read_message_id:
            membership.last_read_message_id = int(last_message_id)
            membership.save(update_fields=['last_read_message_id'])

        return Response({'success': True, 'last_read_message_id': membership.last_read_message_id})

    @action(detail=False, methods=['get'], url_path='total-unread')
    def total_unread(self, request):
        """전체 대화방의 안 읽은 메시지 총 합계 (앱바 배지용)"""
        user = request.user
        rooms = self.get_queryset()
        total = 0
        for room in rooms:
            membership = room.memberships.filter(user=user).first()
            last_read_id = membership.last_read_message_id if membership else 0
            total += room.messages.filter(id__gt=last_read_id).exclude(sender=user).count()
        return Response({'total_unread': total})


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    메시지 내역 조회 및 전송 API (REST 백업 & 파일 업로드용)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        room_id = self.request.query_params.get('room')
        if not room_id:
            return ChatMessage.objects.none()
        return ChatMessage.objects.filter(room_id=room_id).select_related('sender').order_by('created')

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user)
        # 방의 최근 활동시간(updated) 갱신
        msg.room.save(update_fields=['updated'])
