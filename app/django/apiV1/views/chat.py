from django.db.models import Q, Prefetch, Subquery, OuterRef, Count
from django.db.models.functions import Coalesce
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

    def _base_queryset_with_prefetch(self, qs):
        """
        공통 prefetch 적용: memberships, 최근 메시지(last_messages_prefetch)
        - serializer의 to_representation에서 추가 쿼리 없이 캐시 활용 가능
        """
        last_msg_qs = ChatMessage.objects.order_by('-created')
        return qs.prefetch_related(
            Prefetch('memberships', queryset=ChatRoomMember.objects.select_related('user__profile')),
            Prefetch('messages', queryset=last_msg_qs, to_attr='last_messages_prefetch'),
        )

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ChatRoom.objects.none()

        # 내가 실제로 멤버(직접 소속 및 상속 소속)로 참여 중인 워크스페이스 ID 목록
        my_project_ids = list(user.member_project_ids()) if hasattr(user, 'member_project_ids') else []

        # 내 활성 워크스페이스 중 메신저 공용 채널이 활성화된(chat_channel_enabled=True) 곳의 대화방 자동 생성
        # (total_unread와 같은 빈번한 카운트 호출 시에는 자동 생성 스킵)
        if getattr(self, 'action', None) != 'total_unread' and my_project_ids:
            existing_channel_pjt_ids = set(
                ChatRoom.objects.filter(
                    project_id__in=my_project_ids,
                    room_type='channel'
                ).values_list('project_id', flat=True)
            )
            missing_projects = IssueProject.objects.filter(
                pk__in=my_project_ids,
                status='1',
                chat_channel_enabled=True
            ).exclude(pk__in=existing_channel_pjt_ids)

            for pjt in missing_projects:
                try:
                    ChatRoom.objects.get_or_create(
                        project=pjt,
                        room_type='channel',
                        defaults={
                            'title': pjt.name,
                            'description': f'{pjt.name} 공용 대화방',
                            'created_by': user,
                        }
                    )
                except Exception:
                    pass

        # 슈퍼유저도 1:1 DM 및 그룹방은 본인이 참여한 방만 조회되어야 하며(사생활 격리), 공용 채널만 전체 열람 가능
        if user.is_superuser:
            qs = ChatRoom.objects.filter(
                (Q(members=user) & ~Q(memberships__user=user, memberships__is_hidden=True)) |
                Q(room_type='channel')
            ).distinct()
            return self._base_queryset_with_prefetch(qs)

        # 1) 내가 멤버로 속해 있고 숨김 처리하지 않은 방 (1:1 DM, 그룹방)
        # 2) 또는 내가 멤버로 소속되어 있고 공용 채널이 켜진 워크스페이스 채널
        qs = ChatRoom.objects.filter(
            (Q(members=user) & ~Q(memberships__user=user, memberships__is_hidden=True)) |
            Q(room_type='channel', project_id__in=my_project_ids, project__chat_channel_enabled=True)
        ).distinct()
        return self._base_queryset_with_prefetch(qs)

    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user)
        # 생성자 자동 멤버십 및 방장 등록
        ChatRoomMember.objects.get_or_create(
            room=room,
            user=self.request.user,
            defaults={'is_admin': True}
        )

    @action(detail=False, methods=['get', 'post'], url_path='get-or-create-self')
    def get_or_create_self(self, request):
        """
        나와의 채팅 (개인 메모 및 파일 보관함) 대화방 조회 또는 자동 개설
        - 카카오톡의 '나와의 채팅', 슬랙의 '자신과의 DM' 역할
        - 모바일(Flutter) ↔ PC 웹(Vue) 간 빠른 파일/도면 전송, 리치카드 프리뷰 및 개인 메모용
        """
        user = request.user
        room, created = ChatRoom.objects.get_or_create(
            created_by=user,
            room_type='self',
            defaults={
                'title': '나와의 채팅',
                'description': '나만의 개인 메모 및 파일 보관함',
            }
        )
        if created:
            ChatRoomMember.objects.get_or_create(
                room=room,
                user=user,
                defaults={'is_admin': True, 'is_pinned': True}
            )
        else:
            # 숨김(나가기) 상태였을 경우 다시 복구
            room.memberships.filter(user=user, is_hidden=True).update(is_hidden=False)

        serializer = ChatRoomListSerializer(room, context={'request': request})
        res_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=res_status)

    @action(detail=False, methods=['post'], url_path='get-or-create-dm')
    def get_or_create_dm(self, request):
        """특정 사용자와의 1:1 DM 대화방 조회 또는 자동 생성"""
        from django.db.models import Count
        from accounts.models import User

        target_user_id = request.data.get('target_user_id')
        if not target_user_id:
            return Response({'error': 'target_user_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 자기 자신에게 보낸 경우 '나와의 채팅'으로 자동 연결
        if int(target_user_id) == request.user.pk:
            return self.get_or_create_self(request)

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
        - 워크스페이스 공용 채널 및 나와의 채팅방: 나가기 불가
        """
        room = self.get_object()
        if room.room_type in ['channel', 'self']:
            return Response({'error': '워크스페이스 공용 채널 및 나와의 채팅방은 나갈 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

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

        # 활성 워크스페이스에 속한 멤버의 user_id — lazy Subquery로 IN절 비대화 방지
        active_member_subquery = Member.objects.filter(
            project__status='1'
        ).values('user_id')

        users = User.objects.filter(
            Q(is_active=True, is_system=False) & (
                    Q(staff__status='1') |
                    Q(pk__in=active_member_subquery)
            )
        ).distinct().select_related('profile', 'staff').order_by('profile__name', 'username')

        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='total-unread')
    def total_unread(self, request):
        """
        전체 대화방의 안 읽은 메시지 총 합계 (앱바 배지용)
        N+1 방지: prefetch된 memberships를 파이썬 레벨에서 탐색 후
        미읽음 카운트는 aggregate 서브쿼리로 단일 쿼리화
        """
        user = request.user
        rooms = self.get_queryset()

        # prefetch된 memberships 활용 → 방 수만큼 membership 쿼리 없음
        total = 0
        room_ids_and_last_read = []
        for room in rooms:
            memberships = getattr(room, '_prefetched_objects_cache', {}).get('memberships', None)
            if memberships is not None:
                my_membership = next((m for m in memberships if m.user_id == user.pk), None)
            else:
                my_membership = room.memberships.filter(user=user).first()
            last_read_id = my_membership.last_read_message_id if my_membership else 0
            room_ids_and_last_read.append((room.id, last_read_id))

        # 방별 미읽음 메시지 수를 단일 쿼리로 집계
        from django.db.models import Case, When, IntegerField, Sum
        if room_ids_and_last_read:
            whens = [
                When(
                    room_id=room_id,
                    id__gt=last_read_id,
                    then=1
                )
                for room_id, last_read_id in room_ids_and_last_read
            ]
            total = ChatMessage.objects.filter(
                room_id__in=[r[0] for r in room_ids_and_last_read]
            ).exclude(sender=user).aggregate(
                total=Coalesce(
                    Sum(Case(*whens, default=0, output_field=IntegerField())),
                    0
                )
            )['total']

        return Response({'total_unread': total})


class ChatMessageCursorPagination:
    """
    커서 페이지네이션 (before_id 기반 역방향 로딩)
    - ?before_id=<msg_id>  : 해당 ID보다 작은 메시지 최대 page_size개 반환
    - ?after_id=<msg_id>   : 해당 ID보다 큰 메시지 최대 page_size개 반환
    - 기본: 최신 메시지 50개
    """
    page_size = 50


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    메시지 내역 조회 및 전송 API (REST 백업 & 파일 업로드용)
    - 페이지네이션: ?before_id=<id> 또는 ?after_id=<id> 쿼리 파라미터
    - 파일 업로드 후 WebSocket 채널 그룹으로 실시간 브로드캐스팅
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer
    pagination_class = None  # 커스텀 커서 페이지네이션 사용 (아래 list 오버라이드)

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
            'sender', 'sender__profile',
            'reply_to', 'reply_to__sender', 'reply_to__sender__profile'
        ).order_by('-created')  # 역순 정렬 후 클라이언트에서 뒤집어 사용

    def list(self, request, *args, **kwargs):
        """
        커서 페이지네이션 적용 메시지 목록
        - ?before_id=N : N보다 작은 ID의 메시지 (이전 메시지 더 불러오기)
        - ?after_id=N  : N보다 큰 ID의 메시지 (최신 메시지 동기화)
        - 기본값: 최신 50개
        """
        qs = self.get_queryset()
        before_id = request.query_params.get('before_id')
        after_id = request.query_params.get('after_id')
        page_size = ChatMessageCursorPagination.page_size

        if before_id:
            qs = qs.filter(id__lt=before_id)
        elif after_id:
            qs = qs.filter(id__gt=after_id).order_by('created')

        messages = list(qs[:page_size])
        # before_id 방식은 역순으로 가져온 뒤 다시 오름차순 정렬
        if before_id or (not before_id and not after_id):
            messages = list(reversed(messages))

        serializer = self.get_serializer(messages, many=True)
        has_more = qs.count() > page_size if messages else False
        return Response({
            'results': serializer.data,
            'has_more': has_more,
        })

    def perform_create(self, serializer):
        """
        REST API를 통한 메시지 생성 (주로 파일 업로드)
        - 저장 완료 후 WebSocket 채널 그룹으로 브로드캐스팅하여 실시간 전파
        """
        msg = serializer.save(sender=self.request.user)
        # 방의 최근 활동시간(updated) 갱신
        msg.room.save(update_fields=['updated'])

        # WebSocket 채널 그룹으로 브로드캐스팅 (파일 업로드 실시간 전파)
        self._broadcast_new_message(msg)

    def _broadcast_new_message(self, msg):
        """채널 레이어를 통해 대화방 WebSocket 그룹에 새 메시지 이벤트 전송"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            try:
                profile = msg.sender.profile if msg.sender else None
                sender_name = (profile.name if profile and profile.name else None) or (msg.sender.username if msg.sender else '시스템')
                sender_avatar = profile.image.url if (profile and profile.image) else None
            except Exception:
                sender_name = msg.sender.username if msg.sender else '시스템'
                sender_avatar = None

            reply_to_detail = None
            if msg.reply_to:
                target = msg.reply_to
                t_profile = getattr(target.sender, 'profile', None) if target.sender else None
                reply_to_detail = {
                    'id': target.id,
                    'sender_name': (t_profile.name if t_profile and t_profile.name else None) or (target.sender.username if target.sender else '알 수 없음'),
                    'content': target.content[:60] if target.content else (f"[파일] {target.file_name}" if target.file_name else '[첨부]'),
                    'message_type': target.message_type,
                }

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_room_{msg.room_id}',
                {
                    'type': 'broadcast_message',
                    'message': {
                        'id': msg.id,
                        'room_id': msg.room_id,
                        'sender': {
                            'pk': msg.sender.pk if msg.sender else None,
                            'username': msg.sender.username if msg.sender else '시스템',
                            'name': sender_name,
                            'avatar': sender_avatar,
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
                    },
                }
            )
        except Exception:
            # 채널 레이어 오류 시 메시지 저장 자체는 성공이므로 조용히 무시
            pass

