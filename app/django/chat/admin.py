from django.contrib import admin
from django.utils.html import format_html
from .models import ChatRoom, ChatRoomMember, ChatMessage


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'room_type', 'project', 'created_by', 'created', 'updated')
    list_filter = ('room_type', 'project')
    search_fields = ('title', 'description')

    def get_queryset(self, request):
        """
        보안 정책:
        - 1:1 DM(direct)은 프라이버시 보호를 위해 일반 스태프 어드민 목록에서 제외
        - 오직 시스템 최고관리자(superuser)만 감사(Audit) 목적으로 전체 열람 가능
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.exclude(room_type='direct')


@admin.register(ChatRoomMember)
class ChatRoomMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'user', 'is_admin', 'is_pinned', 'is_muted', 'is_hidden', 'joined_at', 'last_read_message_id')
    list_filter = ('is_admin', 'is_pinned', 'is_muted', 'is_hidden')
    search_fields = ('user__username', 'room__title')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.exclude(room__room_type='direct')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'message_type', 'masked_content', 'created')
    list_filter = ('message_type', 'room__room_type')
    search_fields = ('content', 'sender__username')

    def get_queryset(self, request):
        """
        보안 정책:
        - 일반 스태프 관리자는 공용 채널/그룹방 메시지만 열람 가능
        - 1:1 DM 메시지는 일반 어드민에 미노출
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.exclude(room__room_type='direct')

    @admin.display(description='메시지 내용')
    def masked_content(self, obj):
        """1:1 대화인 경우 마스킹 텍스트 안내 표출"""
        if obj.room and obj.room.room_type == 'direct':
            return format_html('<span style="color: #888; font-style: italic;">🔒 [1:1 비밀 대화] {}</span>', obj.content[:30] if len(obj.content) > 30 else obj.content)
        return obj.content[:50]
