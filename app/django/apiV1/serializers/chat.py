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

    class Meta:
        model = ChatMessage
        fields = (
            'id', 'room', 'sender', 'message_type', 'content',
            'file', 'file_name', 'file_size',
            'ref_id', 'ref_title', 'ref_sub',
            'reply_to', 'created'
        )
        read_only_fields = ('created',)


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

    def get_last_message(self, obj):
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
        membership = obj.memberships.filter(user=request.user).first()
        last_read_id = membership.last_read_message_id if membership else 0
        return obj.messages.filter(id__gt=last_read_id).exclude(sender=request.user).count()

    def get_members(self, obj):
        if obj.room_type == 'channel' and obj.project:
            # 워크스페이스 공용 채널인 경우 워크스페이스 구성원 자동 연동
            all_mems = obj.project.all_members()
            return [m['user'] for m in all_mems]
        return SimpleUserSerializer(obj.members.all(), many=True).data

    def get_member_count(self, obj):
        if obj.room_type == 'channel' and obj.project:
            return len(obj.project.all_members())
        return obj.members.count()

    def get_is_pinned(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        membership = obj.memberships.filter(user=request.user).first()
        return membership.is_pinned if membership else False

    def get_is_muted(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        membership = obj.memberships.filter(user=request.user).first()
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
