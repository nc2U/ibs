from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from apiV1.serializers.accounts import UserSerializer
from apiV1.serializers.chat import (
    ChatRoomListSerializer,
    ChatRoomDetailSerializer,
    ChatMessageSerializer,
)
from chat.models import ChatRoom, ChatRoomMember, ChatMessage
from work.models import IssueProject
from work.models.project import Member


class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    메신저 대화방 ViewSet
    - list: 내가 참여 중인 대화방 또는 소속 워크스페이스 공용 채널 목록
    - create: 새 단체방 또는 1:1 DM 생성
    - read: 대화방 읽음 처리 (last_read_message_id 갱신)
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return ChatRoomDetailSerializer
        return ChatRoomListSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ChatRoom.objects.none()

        # 내가 실제로 멤버(직접 소속 및 상속 소속)로 참여 중인 워크스페이스 ID 목록
        my_project_ids = list(user.member_project_ids()) if hasattr(user, 'member_project_ids') else []

        # 내 활성 워크스페이스 중 메신저 공용 채널이 활성화된(chat_channel_enabled=True) 곳의 대화방 자동 생성
        my_projects = IssueProject.objects.filter(
            pk__in=my_project_ids,
            status='1',
            chat_channel_enabled=True
        )

        for pjt in my_projects:
            ChatRoom.objects.get_or_create(
                project=pjt,
                room_type='channel',
                defaults={
                    'title': pjt.name,
                    'description': f'{pjt.name} 공용 대화방',
                    'created_by': user,
                }
            )

        # 슈퍼유저도 1:1 DM 및 그룹방은 본인이 참여한 방만 조회되어야 하며(사생활 격리), 공용 채널만 전체 열람 가능
        if user.is_superuser:
            return ChatRoom.objects.filter(
                (Q(members=user) & ~Q(memberships__user=user, memberships__is_hidden=True)) |
                Q(room_type='channel')
            ).distinct()

        # 1) 내가 멤버로 속해 있고 숨김 처리하지 않은 방 (1:1 DM, 그룹방)
        # 2) 또는 내가 멤버로 소속되어 있고 공용 채널이 켜진 워크스페이스 채널
        return ChatRoom.objects.filter(
            (Q(members=user) & ~Q(memberships__user=user, memberships__is_hidden=True)) |
            Q(room_type='channel', project_id__in=my_project_ids, project__chat_channel_enabled=True)
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
        from django.db.models import Count
        from accounts.models import User

        target_user_id = request.data.get('target_user_id')
        if not target_user_id:
            return Response({'error': 'target_user_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        if int(target_user_id) == request.user.pk:
            return Response({'error': '자기 자신과의 DM은 지원하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        target_user = User.objects.filter(pk=target_user_id, is_active=True, is_system=False).first()
        if not target_user:
            return Response({'error': '대화할 수 없는 사용자이거나 시스템 계정입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 정확히 나와 대상자 2명만 존재하는 1:1 DM 검색
        existing_rooms = ChatRoom.objects.annotate(member_cnt=Count('members')).filter(
            room_type='direct',
            member_cnt=2,
            members=request.user
        ).filter(members=target_user)

        if existing_rooms.exists():
            room = existing_rooms.first()
            # 숨김(나가기) 상태였다면 다시 목록에 보이도록 복구
            room.memberships.filter(user=request.user, is_hidden=True).update(is_hidden=False)
            serializer = ChatRoomListSerializer(room, context={'request': request})
            return Response(serializer.data)

        # 없으면 새로 생성
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=request.user
        )
        ChatRoomMember.objects.create(room=room, user=request.user, is_admin=True)
        ChatRoomMember.objects.create(room=room, user=target_user, is_admin=False)

        serializer = ChatRoomListSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='leave')
    def leave_room(self, request, pk=None):
        """
        대화방 나가기 / 내 목록에서 숨기기
        - 1:1 DM: 내 멤버십을 is_hidden = True 처리하여 목록에서 숨김 (상대방 기록은 유지)
        - 비공개 그룹방: 멤버십 삭제
        """
        room = self.get_object()
        if room.room_type == 'channel':
            return Response({'error': '워크스페이스 공용 채널은 나갈 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        membership = room.memberships.filter(user=request.user).first()
        if not membership:
            return Response({'error': '해당 대화방의 참여 멤버가 아닙니다.'}, status=status.HTTP_404_NOT_FOUND)

        if room.room_type == 'direct':
            # 1:1 DM은 is_hidden=True 로 숨김
            membership.is_hidden = True
            membership.save(update_fields=['is_hidden'])
        else:
            # 그룹방은 멤버십 삭제
            membership.delete()

        return Response({'success': True, 'message': '대화방을 나갔습니다.'})

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

    @action(detail=False, methods=['get'], url_path='available-users')
    def available_users(self, request):
        """
        1:1 대화 개설이 가능한 협업 대상자 목록:
        1. 활성 본사 임직원 (staff__status='1' & is_active=True & is_system=False)
        2. 활성 워크스페이스에 1개 이상 멤버(Member)로 참여 중인 사용자 (is_system=False)
        """

        # 활성 워크스페이스에 속한 멤버의 user_id 목록
        active_member_user_ids = Member.objects.filter(
            project__status='1'
        ).values_list('user_id', flat=True)

        users = User.objects.filter(
            Q(is_active=True, is_system=False) & (
                    Q(staff__status='1') |
                    Q(pk__in=active_member_user_ids)
            )
        ).distinct().select_related('profile', 'staff').order_by('profile__name', 'username')

        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)

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
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        room_id = self.request.query_params.get('room')
        if not room_id or not user.is_authenticated:
            return ChatMessage.objects.none()

        # 방 접근 권한 검증: 1) 내가 멤버인 방 또는 2) 내 워크스페이스 공용 채널
        room = ChatRoom.objects.filter(pk=room_id).first()
        if not room:
            return ChatMessage.objects.none()

        if room.room_type == 'channel':
            my_project_ids = list(user.member_project_ids()) if hasattr(user, 'member_project_ids') else []
            if room.project_id not in my_project_ids and not user.is_superuser:
                return ChatMessage.objects.none()
        else:
            if not room.members.filter(pk=user.pk).exists() and not user.is_superuser:
                return ChatMessage.objects.none()

        return ChatMessage.objects.filter(room_id=room_id).select_related(
            'sender', 'reply_to', 'reply_to__sender', 'reply_to__sender__profile'
        ).order_by('created')

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user)
        # 방의 최근 활동시간(updated) 갱신
        msg.room.save(update_fields=['updated'])
