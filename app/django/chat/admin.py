from django.contrib import admin
from .models import ChatRoom, ChatRoomMember, ChatMessage


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'room_type', 'project', 'created_by', 'created', 'updated')
    list_filter = ('room_type', 'project')
    search_fields = ('title', 'description')


@admin.register(ChatRoomMember)
class ChatRoomMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'user', 'is_admin', 'is_pinned', 'is_muted', 'joined_at', 'last_read_message_id')
    list_filter = ('is_admin', 'is_pinned', 'is_muted')
    search_fields = ('user__username', 'room__title')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'message_type', 'content', 'created')
    list_filter = ('message_type', 'room')
    search_fields = ('content', 'sender__username')
