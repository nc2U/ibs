import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import Cookies from 'js-cookie'
import type {
  ChatRoom,
  ChatMessage,
  ChatSearchResult,
  ChatFilesResult,
  ChatContextResult,
} from '@/store/types/chat'
import { useAccount } from '@/store/pinia/account'

export const useChat = defineStore('chat', () => {
  const accountStore = useAccount()
  const getMyUserId = () => accountStore.userInfo?.pk || 0
  const getMyUsername = () => accountStore.userInfo?.username || ''

  const isDrawerOpen = ref(false)
  const rooms = ref<ChatRoom[]>([])
  const currentRoom = ref<ChatRoom | null>(null)
  const messages = ref<ChatMessage[]>([])
  const totalUnreadCount = ref(0)
  const isConnecting = ref(false)
  const usersList = ref<any[]>([])
  const isLoadingUsers = ref(false)

  // 📜 커서 기반 페이지네이션 & 윈도우잉 상태
  const hasMoreOlder = ref(false)
  const isLoadingOlder = ref(false)
  const isLoadingNewer = ref(false)
  const atLatest = ref(true)

  let ws: WebSocket | null = null
  let reconnectTimer: any = null
  let reconnectAttempts = 0
  let hasConnectedOnce = false

  const channelRooms = computed(() => rooms.value.filter(r => r.room_type === 'channel'))
  const selfRoom = computed(() => rooms.value.find(r => r.room_type === 'self'))
  const directRooms = computed(() =>
    rooms.value.filter(r => r.room_type !== 'channel' && r.room_type !== 'self'),
  )

  // 각 탭별 안 읽은 메시지 수 합계
  const channelUnreadCount = computed(() =>
    channelRooms.value.reduce((acc, r) => acc + (r.unread_count || 0), 0),
  )
  const directUnreadCount = computed(() =>
    rooms.value
      .filter(r => r.room_type !== 'channel')
      .reduce((acc, r) => acc + (r.unread_count || 0), 0),
  )

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
      // rooms 목록의 unread_count를 기반으로 실시간 즉각 합산 반영
      const sum = rooms.value.reduce((acc, r) => acc + (r.unread_count || 0), 0)
      if (sum > 0 || totalUnreadCount.value === 0) {
        totalUnreadCount.value = sum
      }
    } catch (_) {}
  }

  const fetchUsers = async () => {
    isLoadingUsers.value = true
    try {
      const res = await api.get('/chat-room/available-users/', {
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

  const getOrCreateSelf = async () => {
    try {
      const res = await api.get('/chat-room/get-or-create-self/')
      const room = res.data
      await fetchRooms()
      await enterRoom(room)
      return room
    } catch (e) {
      throw e
    }
  }

  /// 1. 커서 기반 메시지 페이지 조회
  const fetchMessagePage = async (
    roomId: number,
    options: { beforeId?: number; afterId?: number } = {},
  ): Promise<{ results: ChatMessage[]; has_more: boolean }> => {
    try {
      const res = await api.get('/chat-message/', {
        params: {
          room: roomId,
          ...(options.beforeId ? { before_id: options.beforeId } : {}),
          ...(!options.beforeId && options.afterId ? { after_id: options.afterId } : {}),
        },
        hideProgress: true,
      } as any)
      const data = res.data
      const results: ChatMessage[] = data.results || data || []
      const has_more: boolean = data.has_more ?? false
      return { results, has_more }
    } catch (_) {
      return { results: [], has_more: false }
    }
  }

  const enterRoom = async (room: ChatRoom) => {
    leaveRoom()
    currentRoom.value = room
    messages.value = []
    atLatest.value = true

    try {
      const page = await fetchMessagePage(room.id)
      messages.value = page.results
      hasMoreOlder.value = page.has_more

      // 읽음 처리 (마지막 메시지 ID 전달)
      const lastMsg = messages.value.length ? messages.value[messages.value.length - 1] : null
      const lastId = lastMsg?.id || 0
      await api.post(`/chat-room/${room.id}/read/`, { last_message_id: lastId }, {
        hideProgress: true,
      } as any)
      room.unread_count = 0
      fetchTotalUnread()
    } catch (_) {}

    connectWebSocket(room.id)
  }

  const leaveRoom = () => {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
    reconnectAttempts = 0
    hasConnectedOnce = false
    if (ws) {
      ws.close()
      ws = null
    }
    currentRoom.value = null
    messages.value = []
    hasMoreOlder.value = false
    atLatest.value = true
  }

  /// ⬆️ 더 오래된 메시지 불러오기 (위로 스크롤 시)
  const loadOlder = async (): Promise<boolean> => {
    if (isLoadingOlder.value || !hasMoreOlder.value || !messages.value.length || !currentRoom.value) {
      return false
    }
    isLoadingOlder.value = true
    try {
      const firstId = messages.value[0].id
      const page = await fetchMessagePage(currentRoom.value.id, { beforeId: firstId })
      hasMoreOlder.value = page.has_more

      const existingIds = new Set(messages.value.map(m => m.id))
      const older = page.results.filter(m => !existingIds.has(m.id))
      if (older.length) {
        messages.value = [...older, ...messages.value]
      }
      return older.length > 0
    } catch (_) {
      return false
    } finally {
      isLoadingOlder.value = false
    }
  }

  /// ⬇️ 과거 구간(window)을 보는 중 아래로 스크롤 시 최근 메시지 불러오기
  const loadNewer = async (): Promise<boolean> => {
    if (isLoadingNewer.value || atLatest.value || !messages.value.length || !currentRoom.value) {
      return false
    }
    isLoadingNewer.value = true
    try {
      const lastId = messages.value[messages.value.length - 1].id
      const page = await fetchMessagePage(currentRoom.value.id, { afterId: lastId })
      const existingIds = new Set(messages.value.map(m => m.id))
      const newer = page.results.filter(m => !existingIds.has(m.id))

      if (!page.has_more) atLatest.value = true
      if (newer.length || atLatest.value) {
        messages.value = [...messages.value, ...newer]
      }
      if (atLatest.value && messages.value.length) {
        const last = messages.value[messages.value.length - 1]
        api.post(`/chat-room/${currentRoom.value.id}/read/`, { last_message_id: last.id }, {
          hideProgress: true,
        } as any)
      }
      return newer.length > 0
    } catch (_) {
      return false
    } finally {
      isLoadingNewer.value = false
    }
  }

  /// 🎯 특정 메시지 전후 맥락을 불러와 목록을 해당 구간으로 교체 (윈도우 전환)
  const loadAround = async (messageId: number): Promise<boolean> => {
    if (!currentRoom.value) return false
    if (messages.value.some(m => m.id === messageId)) return true
    try {
      const contextRes = await fetchMessageContext(messageId, 20)
      if (contextRes.results && contextRes.results.length) {
        hasMoreOlder.value = true
        atLatest.value = false
        messages.value = contextRes.results
        return messages.value.some(m => m.id === messageId)
      }
      return false
    } catch (_) {
      return false
    }
  }

  /// 🔽 최신 대화로 복귀 (과거 구간을 보고 있을 때)
  const jumpToLatest = async () => {
    if (!currentRoom.value) return
    try {
      const page = await fetchMessagePage(currentRoom.value.id)
      hasMoreOlder.value = page.has_more
      atLatest.value = true
      messages.value = page.results
      const last = messages.value.length ? messages.value[messages.value.length - 1] : null
      if (last) {
        api.post(`/chat-room/${currentRoom.value.id}/read/`, { last_message_id: last.id }, {
          hideProgress: true,
        } as any)
      }
    } catch (_) {}
  }

  /// 최신 메시지 갱신 (삭제 등 반영)
  const refreshMessages = async () => {
    if (!currentRoom.value || !atLatest.value) return
    try {
      const page = await fetchMessagePage(currentRoom.value.id)
      const fetched = page.results
      if (!fetched.length) {
        messages.value = []
        return
      }
      const firstId = fetched[0].id
      const kept = messages.value.filter(m => m.id < firstId)
      if (!kept.length) hasMoreOlder.value = page.has_more
      messages.value = [...kept, ...fetched]
    } catch (_) {}
  }

  const exitAndHideRoom = async (roomId: number) => {
    try {
      await api.post(`/chat-room/${roomId}/leave/`, {})
      if (currentRoom.value?.id === roomId) {
        leaveRoom()
      }
      await fetchRooms()
      await fetchTotalUnread()
    } catch (e) {
      throw e
    }
  }

  /// 재연결 직후 끊겨 있던 동안 놓친 메시지를 보충
  const syncMissedMessages = async () => {
    if (!currentRoom.value || !atLatest.value || !messages.value.length) return
    try {
      let lastId = messages.value[messages.value.length - 1].id
      for (let i = 0; i < 5; i++) {
        const page = await fetchMessagePage(currentRoom.value.id, { afterId: lastId })
        if (!currentRoom.value || !atLatest.value) return
        const existingIds = new Set(messages.value.map(m => m.id))
        const newer = page.results.filter(m => !existingIds.has(m.id))
        if (newer.length) {
          messages.value = [...messages.value, ...newer]
          lastId = newer[newer.length - 1].id
        }
        if (!page.has_more || !newer.length) break
      }
    } catch (_) {}
  }

  const scheduleReconnect = (roomId: number) => {
    if (!currentRoom.value || currentRoom.value.id !== roomId) return
    clearTimeout(reconnectTimer)
    const delaySeconds = Math.min(20, Math.max(2, Math.pow(2, reconnectAttempts)))
    reconnectAttempts++
    reconnectTimer = setTimeout(() => {
      if (currentRoom.value && currentRoom.value.id === roomId && (!ws || ws.readyState === WebSocket.CLOSED)) {
        connectWebSocket(roomId)
      }
    }, delaySeconds * 1000)
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
      reconnectAttempts = 0
      if (hasConnectedOnce) {
        syncMissedMessages()
      }
      hasConnectedOnce = true
    }

    ws.onmessage = event => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'chat_message') {
          const msg = payload.data || payload.message
          if (msg) {
            // 과거 구간(window)을 보는 중에는 목록 연속성이 깨지므로 추가하지 않는다
            if (atLatest.value) {
              if (!messages.value.some(m => m.id === msg.id)) {
                messages.value.push(msg)
              }
            }
            const myId = getMyUserId()
            const myUsername = getMyUsername()
            const isMe =
              (msg.sender?.pk && myId > 0 && msg.sender.pk === myId) ||
              (msg.sender?.username && myUsername && msg.sender.username === myUsername)

            // 내가 보낸 메시지가 아닐 때(상대방 메시지)에만 읽음 처리 전송
            if (!isMe && currentRoom.value && currentRoom.value.id === roomId) {
              api.post(`/chat-room/${roomId}/read/`, { last_message_id: msg.id }, {
                hideProgress: true,
              } as any)
              if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(
                  JSON.stringify({
                    type: 'read',
                    last_message_id: msg.id,
                  }),
                )
              }
            }
          }
        } else if (payload.type === 'delete_message') {
          const messageId = payload.message_id
          const isSoft = payload.is_soft
          if (messageId) {
            if (isSoft) {
              const target = messages.value.find(m => m.id === messageId)
              if (target) {
                target.is_deleted = true
                target.content = '삭제된 메시지입니다.'
                target.file = null
                target.file_name = ''
                target.file_size = 0
                target.ref_id = null
                target.ref_title = ''
                target.ref_sub = ''
              }
            } else {
              messages.value = messages.value.filter(m => m.id !== messageId)
            }
          }
        } else if (payload.type === 'read') {
          const readUserId = payload.user_id
          const lastReadId = payload.last_message_id
          const myId = getMyUserId()

          // 다른 사용자가 읽은 경우에만 내가 보낸 메시지의 unread_count 차감 (자신이 발생시킨 read 이벤트 제외)
          if (readUserId && myId > 0 && readUserId !== myId && lastReadId) {
            messages.value.forEach(m => {
              if (m.id <= lastReadId && m.unread_count && m.unread_count > 0) {
                m.unread_count = Math.max(0, m.unread_count - 1)
              }
            })
          }
        } else if (payload.type === 'error') {
          console.error('[WebSocket Chat Error]', payload.message)
        }
      } catch (_) {}
    }

    ws.onclose = () => {
      isConnecting.value = false
      scheduleReconnect(roomId)
    }

    ws.onerror = () => {
      isConnecting.value = false
      scheduleReconnect(roomId)
    }
  }

  const sendMessage = async (content: string, extra: Partial<ChatMessage> = {}) => {
    if (!content.trim() || !currentRoom.value) return

    if (!atLatest.value) await jumpToLatest()

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

    // 2. 웹소켓 미연결 시 REST API로 즉시 전송 및 화면에 실시간 추가
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
      if (!messages.value.some(m => m.id === savedMsg.id)) {
        messages.value.push(savedMsg)
      }
    } catch (_) {}
  }

  const uploadFile = async (file: File, comment = '', replyToId?: number) => {
    if (!currentRoom.value) return

    if (!atLatest.value) await jumpToLatest()

    const isImg = file.type.startsWith('image/')
    const formData = new FormData()
    formData.append('room', String(currentRoom.value.id))
    formData.append('message_type', isImg ? 'image' : 'file')
    formData.append('content', comment || file.name)
    formData.append('file', file)
    formData.append('file_name', file.name)
    formData.append('file_size', String(file.size))
    if (replyToId) {
      formData.append('reply_to', String(replyToId))
    }

    try {
      const res = await api.post('/chat-message/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        hideProgress: true,
      } as any)
      const savedMsg = res.data
      if (!messages.value.some(m => m.id === savedMsg.id)) {
        messages.value.push(savedMsg)
      }
      return savedMsg
    } catch (e) {
      throw e
    }
  }

  const deleteMessage = async (messageId: number, roomId?: number) => {
    try {
      const targetRoomId = roomId || currentRoom.value?.id
      await api.delete(`/chat-message/${messageId}/`, {
        params: targetRoomId ? { room: targetRoomId } : {},
        hideProgress: true,
      } as any)
      // 웹소켓 미연결 시 로컬 동기화 (웹소켓 연결 시에는 ws.onmessage의 delete_message 이벤트가 자동 처리)
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        await refreshMessages()
      }
    } catch (e) {
      throw e
    }
  }

  // ── 🔍 검색 & 전후 맥락 & 영구 파일 서랍 액션 ───────────────────
  const searchMessages = async (params: {
    q: string
    room?: number
    type?: 'all' | 'text' | 'file' | 'image'
    page?: number
    pageSize?: number
  }): Promise<ChatSearchResult> => {
    try {
      const res = await api.get('/chat-message/search/', {
        params: {
          q: params.q,
          room: params.room,
          type: params.type || 'all',
          page: params.page || 1,
          page_size: params.pageSize || 30,
        },
        hideProgress: true,
      } as any)
      return res.data
    } catch (e) {
      throw e
    }
  }

  const fetchMessageContext = async (
    messageId: number,
    limit = 15,
  ): Promise<ChatContextResult> => {
    try {
      const res = await api.get('/chat-message/context/', {
        params: { message_id: messageId, limit },
        hideProgress: true,
      } as any)
      return res.data
    } catch (e) {
      throw e
    }
  }

  const fetchChatFiles = async (params: {
    room: number
    tab?: 'all' | 'media' | 'doc' | 'link'
    page?: number
    pageSize?: number
  }): Promise<ChatFilesResult> => {
    try {
      const res = await api.get('/chat-message/files/', {
        params: {
          room: params.room,
          tab: params.tab || 'all',
          page: params.page || 1,
          page_size: params.pageSize || 30,
        },
        hideProgress: true,
      } as any)
      return res.data
    } catch (e) {
      throw e
    }
  }

  return {
    isDrawerOpen,
    rooms,
    channelRooms,
    selfRoom,
    directRooms,
    channelUnreadCount,
    directUnreadCount,
    currentRoom,
    messages,
    totalUnreadCount,
    isConnecting,
    usersList,
    isLoadingUsers,
    hasMoreOlder,
    isLoadingOlder,
    isLoadingNewer,
    atLatest,
    toggleDrawer,
    openDrawer,
    closeDrawer,
    fetchRooms,
    fetchUsers,
    fetchTotalUnread,
    getOrCreateDm,
    getOrCreateSelf,
    enterRoom,
    leaveRoom,
    exitAndHideRoom,
    sendMessage,
    uploadFile,
    deleteMessage,
    searchMessages,
    fetchMessageContext,
    fetchChatFiles,
    fetchMessagePage,
    loadOlder,
    loadNewer,
    loadAround,
    jumpToLatest,
    refreshMessages,
  }
})
