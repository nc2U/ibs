from rest_framework import serializers
from accounts.models import User
from apiV1.serializers.accounts import SimpleUserSerializer
from chat.models import ChatRoom, ChatRoomMember, ChatMessage


class ChatRoomMemberSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = ChatRoomMember
        fields = ('id', 'room', 'user', 'user_id', 'is_admin', 'is_pinned', 'is_muted', 'joined_at', 'last_read_message_id')
        read_only_fields = ('joined_at',)


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = SimpleUserSerializer(read_only=True)
    reply_to_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            'id', 'room', 'sender', 'message_type', 'content',
            'file', 'file_name', 'file_size',
            'ref_id', 'ref_title', 'ref_sub',
            'reply_to', 'reply_to_detail', 'created'
        )
        read_only_fields = ('created',)

    def get_reply_to_detail(self, obj):
        if not obj.reply_to:
            return None
        target = obj.reply_to
        return {
            'id': target.id,
            'sender_name': target.sender.profile.name if (target.sender and hasattr(target.sender, 'profile') and target.sender.profile.name) else (target.sender.username if target.sender else '알 수 없음'),
            'content': target.content[:60] if target.content else (f"[파일] {target.file_name}" if target.file_name else '[첨부]'),
            'message_type': target.message_type,
        }


class ChatRoomListSerializer(serializers.ModelSerializer):
    """대화방 목록 조회용 (안 읽은 메시지 수, 최근 메시지 요약 포함)"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)
    unread_count = serializers.SerializerMethodField(read_only=True)
    member_count = serializers.SerializerMethodField(read_only=True)
    members = serializers.SerializerMethodField(read_only=True)
    is_pinned = serializers.SerializerMethodField(read_only=True)
    is_muted = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatRoom
        fields = (
            'id', 'project', 'project_name', 'room_type', 'title', 'description',
            'created_by', 'created', 'updated', 'member_count', 'members',
            'last_message', 'unread_count', 'is_pinned', 'is_muted'
        )

    def to_representation(self, instance):
        """
        membership 조회를 한 번만 수행하여 캐시.
        prefetch_related('memberships')가 ViewSet queryset에 적용되어 있을 때 추가 쿼리 없음.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # prefetch 결과 활용: all() 대신 리스트 순회로 DB 히트 없음
            memberships = instance.memberships.all()
            instance._cached_my_membership = next(
                (m for m in memberships if m.user_id == request.user.pk), None
            )
        else:
            instance._cached_my_membership = None

        ret = super().to_representation(instance)
        if instance.room_type == 'self' and not ret.get('title'):
            ret['title'] = '나와의 채팅'
        return ret

    def get_last_message(self, obj):
        # prefetch_related('messages') → last_messages_prefetch to_attr 활용 시 쿼리 0회
        prefetched = getattr(obj, 'last_messages_prefetch', None)
        if prefetched is not None:
            msg = prefetched[0] if prefetched else None
        else:
            msg = obj.messages.order_by('-created').first()
        if not msg:
            return None
        return {
            'id': msg.id,
            'sender_name': msg.sender.username if msg.sender else '시스템',
            'message_type': msg.message_type,
            'content': msg.content if msg.message_type == 'text' else (msg.ref_title or f"[{msg.get_message_type_display()}]"),
            'created': msg.created,
        }

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        membership = getattr(obj, '_cached_my_membership', None)
        last_read_id = membership.last_read_message_id if membership else 0
        return obj.messages.filter(id__gt=last_read_id).exclude(sender=request.user).count()

    def get_members(self, obj):
        if obj.room_type == 'channel' and obj.project:
            # 워크스페이스 공용 채널인 경우 워크스페이스 구성원 자동 연동
            all_mems = getattr(obj, '_cached_all_members', None)
            if all_mems is None:
                all_mems = obj.project.all_members()
                obj._cached_all_members = all_mems
            return [m['user'] for m in all_mems]
        return SimpleUserSerializer(obj.members.all(), many=True).data

    def get_member_count(self, obj):
        if obj.room_type == 'channel' and obj.project:
            all_mems = getattr(obj, '_cached_all_members', None)
            if all_mems is None:
                all_mems = obj.project.all_members()
                obj._cached_all_members = all_mems
            return len(all_mems)
        return obj.members.count()

    def get_is_pinned(self, obj):
        membership = getattr(obj, '_cached_my_membership', None)
        return membership.is_pinned if membership else False

    def get_is_muted(self, obj):
        membership = getattr(obj, '_cached_my_membership', None)
        return membership.is_muted if membership else False


class ChatRoomDetailSerializer(serializers.ModelSerializer):
    """대화방 상세 정보 (참여자 목록 및 설정 포함)"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    memberships = ChatRoomMemberSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = (
            'id', 'project', 'project_name', 'room_type', 'title', 'description',
            'created_by', 'created', 'updated', 'memberships'
        )

