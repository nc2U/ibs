import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import Cookies from 'js-cookie'
import type { ChatRoom, ChatMessage } from '@/store/types/chat'

export const useChat = defineStore('chat', () => {
  const isDrawerOpen = ref(false)
  const rooms = ref<ChatRoom[]>([])
  const currentRoom = ref<ChatRoom | null>(null)
  const messages = ref<ChatMessage[]>([])
  const totalUnreadCount = ref(0)
  const isConnecting = ref(false)
  const usersList = ref<any[]>([])
  const isLoadingUsers = ref(false)

  let ws: WebSocket | null = null

  const channelRooms = computed(() => rooms.value.filter(r => r.room_type === 'channel'))
  const directRooms = computed(() => rooms.value.filter(r => r.room_type !== 'channel'))

  const toggleDrawer = () => {
    isDrawerOpen.value = !isDrawerOpen.value
    if (isDrawerOpen.value) {
      fetchRooms()
      fetchTotalUnread()
    }
  }

  const openDrawer = () => {
    isDrawerOpen.value = true
    fetchRooms()
    fetchTotalUnread()
  }

  const closeDrawer = () => {
    isDrawerOpen.value = false
    leaveRoom()
  }

  const fetchRooms = async () => {
    try {
      const res = await api.get('/chat-room/', { hideProgress: true } as any)
      rooms.value = res.data.results || res.data
    } catch (_) {}
  }

  const fetchUsers = async () => {
    isLoadingUsers.value = true
    try {
      const res = await api.get('/user/', {
        params: { is_active: true, staff__status: '1' },
        hideProgress: true,
      } as any)
      usersList.value = res.data.results || res.data
    } catch (_) {
    } finally {
      isLoadingUsers.value = false
    }
  }

  const fetchTotalUnread = async () => {
    try {
      const res = await api.get('/chat-room/total-unread/', { hideProgress: true } as any)
      totalUnreadCount.value = res.data.total_unread || 0
    } catch (_) {}
  }

  const getOrCreateDm = async (targetUserId: number) => {
    try {
      const res = await api.post('/chat-room/get-or-create-dm/', { target_user_id: targetUserId })
      const room = res.data
      await fetchRooms()
      await enterRoom(room)
      return room
    } catch (e) {
      throw e
    }
  }

  const enterRoom = async (room: ChatRoom) => {
    leaveRoom()
    currentRoom.value = room
    messages.value = []

    try {
      const res = await api.get('/chat-message/', {
        params: { room: room.id },
        hideProgress: true,
      } as any)
      messages.value = (res.data.results || res.data).reverse()

      // 읽음 처리
      await api.post(`/chat-room/${room.id}/read/`, {}, { hideProgress: true } as any)
      room.unread_count = 0
      fetchTotalUnread()
    } catch (_) {}

    connectWebSocket(room.id)
  }

  const leaveRoom = () => {
    if (ws) {
      ws.close()
      ws = null
    }
    currentRoom.value = null
    messages.value = []
  }

  const connectWebSocket = (roomId: number) => {
    if (ws) ws.close()

    const token = Cookies.get('accessToken')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/chat/${roomId}/?token=${token || ''}`

    isConnecting.value = true
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      isConnecting.value = false
    }

    ws.onmessage = event => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'chat_message' && data.message) {
          const msg = data.message
          // 이미 추가된 메시지가 아닌 경우에만 push
          if (!messages.value.some(m => m.id === msg.id)) {
            messages.value.push(msg)
          }
          if (currentRoom.value && currentRoom.value.id === roomId) {
            api.post(`/chat-room/${roomId}/read/`, {}, { hideProgress: true } as any)
          }
        }
      } catch (_) {}
    }

    ws.onclose = () => {
      isConnecting.value = false
    }

    ws.onerror = () => {
      isConnecting.value = false
    }
  }

  const sendMessage = async (content: string, extra: Partial<ChatMessage> = {}) => {
    if (!content.trim() || !currentRoom.value) return

    const roomId = currentRoom.value.id
    const payload = {
      type: 'chat_message',
      content: content.trim(),
      message_type: extra.message_type || 'text',
      ref_id: extra.ref_id || null,
      ref_title: extra.ref_title || '',
      ref_sub: extra.ref_sub || '',
      reply_to: extra.reply_to || null,
    }

    // 1. WebSocket이 열려있으면 즉시 웹소켓 전송
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload))
      return
    }

    // 2. 웹소켓 미연결/프록시 환경 시 REST API로 전송 폴백 (신뢰성 100% 보장)
    try {
      const res = await api.post('/chat-message/', {
        room: roomId,
        content: content.trim(),
        message_type: extra.message_type || 'text',
        ref_id: extra.ref_id || null,
        ref_title: extra.ref_title || '',
        ref_sub: extra.ref_sub || '',
        reply_to: extra.reply_to || null,
      })
      const savedMsg = res.data
      messages.value.push(savedMsg)
    } catch (_) {}
  }

  return {
    isDrawerOpen,
    rooms,
    channelRooms,
    directRooms,
    currentRoom,
    messages,
    totalUnreadCount,
    isConnecting,
    usersList,
    isLoadingUsers,
    toggleDrawer,
    openDrawer,
    closeDrawer,
    fetchRooms,
    fetchUsers,
    fetchTotalUnread,
    getOrCreateDm,
    enterRoom,
    leaveRoom,
    sendMessage,
  }
})
