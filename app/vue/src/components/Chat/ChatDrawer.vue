<script lang="ts" setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useChat } from '@/store/pinia/chat'
import { useAccount } from '@/store/pinia/account'
import { useStore } from '@/store'
import type { ChatRoom, ChatMessage } from '@/store/types/chat'

const chatStore = useChat()
const accountStore = useAccount()
const store = useStore()

const isDark = computed(() => store.isDark)
const currentUserId = computed(() => accountStore.userInfo?.pk ?? 0)
const isDrawerOpen = computed(() => chatStore.isDrawerOpen)
const currentRoom = computed(() => chatStore.currentRoom)
const messages = computed(() => chatStore.messages)
const allUsers = computed(() => chatStore.usersList)
const isLoadingUsers = computed(() => chatStore.isLoadingUsers)

const activeTab = ref<'channel' | 'direct'>('channel')
const inputMessage = ref('')
const messageContainer = ref<HTMLElement | null>(null)

// 1:1 대화 상대 선택 모달 상태
const isUserSelectModalOpen = ref(false)
const userSearchQuery = ref('')

const isMembersDrawerOpen = ref(false)

const getRoomDisplayName = (room: ChatRoom) => {
  if (room.room_type === 'direct' && room.members?.length) {
    const other = room.members.find(m => m.pk !== currentUserId.value)
    if (other) {
      return (other as any).name ? `${(other as any).name} (${other.username})` : other.username
    }
    return '1:1 대화'
  }
  if (room.title) return room.title
  if (room.room_type === 'channel') return `#${room.project_name || '공용 채널'}`
  return '그룹 대화방'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
}

watch(
  () => messages.value.length,
  () => {
    scrollToBottom()
  },
)

// ── 댓글 / 답장 (Reply) 상태 ─────────────────────────────
const replyingTo = ref<ChatMessage | null>(null)
const inputFieldRef = ref<any>(null)

const setReplyTarget = (msg: ChatMessage) => {
  replyingTo.value = msg
  nextTick(() => {
    // 입력창에 포커스 이동
    const inputEl = document.querySelector('.chat-input-area input') as HTMLInputElement
    if (inputEl) inputEl.focus()
  })
}

const cancelReply = () => {
  replyingTo.value = null
}

const handleSendMessage = (event?: KeyboardEvent) => {
  // 한글 입력(IME) 조합 중 엔터 입력 시 중복 발송 방지
  if (event && event.isComposing) return
  if (!inputMessage.value.trim()) return

  const text = inputMessage.value
  const replyTarget = replyingTo.value
  inputMessage.value = ''
  replyingTo.value = null

  chatStore.sendMessage(text, {
    reply_to: replyTarget ? replyTarget.id : undefined,
  })
  scrollToBottom()
}

const handleSelectRoom = (room: ChatRoom) => {
  chatStore.enterRoom(room)
}

const handleBackToList = () => {
  chatStore.leaveRoom()
  chatStore.fetchRooms()
}

// 1:1 상대 선택 모달 열기 (Pinia store 액션 호출)
const openUserSelectModal = async () => {
  isUserSelectModalOpen.value = true
  userSearchQuery.value = ''
  await chatStore.fetchUsers()
}

const filteredUsers = computed(() => {
  const q = userSearchQuery.value.trim().toLowerCase()
  return allUsers.value.filter((u: any) => {
    if (u.pk === currentUserId.value) return false
    if (!q) return true
    const name = (u.profile?.name || '').toLowerCase()
    const username = (u.username || '').toLowerCase()
    return name.includes(q) || username.includes(q)
  })
})

const startDmWithUser = async (user: any) => {
  try {
    isUserSelectModalOpen.value = false
    await chatStore.getOrCreateDm(user.pk)
  } catch (_) {}
}

const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const isDragging = ref(false)
let dragCounter = 0

const triggerFileUpload = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

const handleFileSelected = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  await processFileUpload(file)
  if (fileInputRef.value) fileInputRef.value.value = ''
}

const processFileUpload = async (file: File) => {
  try {
    isUploading.value = true
    await chatStore.uploadFile(file)
    scrollToBottom()
  } catch (err) {
    alert('파일 전송에 실패했습니다. 다시 시도해주세요.')
  } finally {
    isUploading.value = false
  }
}

// ── 드래그 앤 드롭 핸들러 ────────────────────────────────
const handleDragEnter = (e: DragEvent) => {
  e.preventDefault()
  dragCounter++
  if (e.dataTransfer?.types?.includes('Files')) {
    isDragging.value = true
  }
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  dragCounter--
  if (dragCounter <= 0) {
    dragCounter = 0
    isDragging.value = false
  }
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
}

const handleDrop = async (e: DragEvent) => {
  e.preventDefault()
  dragCounter = 0
  isDragging.value = false

  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    for (let i = 0; i < files.length; i++) {
      await processFileUpload(files[i])
    }
  }
}

// ── 클립보드 붙여넣기 (캡처 이미지 붙여넣기 지원) ──────────
const handlePaste = async (e: ClipboardEvent) => {
  const items = e.clipboardData?.items
  if (!items) return

  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      const file = items[i].getAsFile()
      if (file) {
        e.preventDefault()
        await processFileUpload(file)
      }
    }
  }
}

// ── 복사 및 전달/공유 (Copy & Forward) ──────────────────────────
const isForwardModalOpen = ref(false)
const forwardTargetMsg = ref<ChatMessage | null>(null)
const copySnackbar = ref(false)
const copySnackbarText = ref('')

const showCopyNotice = (text = '클립보드에 복사되었습니다.') => {
  copySnackbarText.value = text
  copySnackbar.value = true
}

const copyMessageContent = async (msg: ChatMessage) => {
  try {
    if (msg.message_type === 'image' || msg.message_type === 'file') {
      const fileUrl = msg.file ? (msg.file.startsWith('http') ? msg.file : window.location.origin + msg.file) : ''
      await navigator.clipboard.writeText(fileUrl || msg.content)
      showCopyNotice('파일/이미지 링크가 복사되었습니다.')
    } else {
      await navigator.clipboard.writeText(msg.content)
      showCopyNotice('메시지가 복사되었습니다.')
    }
  } catch (err) {
    showCopyNotice('복사에 실패했습니다.')
  }
}

const openForwardModal = (msg: ChatMessage) => {
  forwardTargetMsg.value = msg
  isForwardModalOpen.value = true
}

const handleForwardToRoom = async (room: ChatRoom) => {
  if (!forwardTargetMsg.value) return
  const msg = forwardTargetMsg.value
  isForwardModalOpen.value = false

  try {
    // 1. 대상 방으로 전환
    await chatStore.enterRoom(room)

    // 2. 메시지 유형에 따라 전달 전송
    if (msg.message_type === 'image' || msg.message_type === 'file') {
      // 첨부파일 공유인 경우 파일 링크 및 메시지 전달
      await chatStore.sendMessage(msg.content || (msg.file_name ? `[공유 파일] ${msg.file_name}` : '[공유 첨부]'), {
        message_type: msg.message_type,
        ref_title: msg.file_name ? `공유 파일: ${msg.file_name}` : '전달된 항목',
      })
    } else {
      await chatStore.sendMessage(msg.content, {
        message_type: msg.message_type,
        ref_id: msg.ref_id,
        ref_title: msg.ref_title,
        ref_sub: msg.ref_sub,
      })
    }
    showCopyNotice(`'${getRoomDisplayName(room)}' 방으로 공유되었습니다.`)
  } catch (err) {
    alert('메시지 전달에 실패했습니다.')
  }
}

const formatFileSize = (bytes?: number) => {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div>
    <!-- 숨김 파일 인풋 -->
    <input
      ref="fileInputRef"
      type="file"
      class="d-none"
      @change="handleFileSelected"
    />

    <!-- 슬라이드 드로어 사이드바 -->
    <v-navigation-drawer
      v-model="chatStore.isDrawerOpen"
      location="right"
      temporary
      width="480"
      class="chat-drawer shadow-lg"
      :class="{ 'dark-drawer': isDark }"
    >
      <div class="d-flex flex-column h-100 chat-main-container">
        <!-- ── 헤더 ────────────────────────────────────────────── -->
        <div
          class="chat-header p-3 border-bottom d-flex align-items-center justify-content-between flex-shrink-0"
        >
          <div class="d-flex align-items-center">
            <v-btn
              v-if="currentRoom"
              icon="mdi-chevron-left"
              variant="text"
              size="small"
              class="mr-1"
              @click="handleBackToList"
            />
            <v-icon
              :icon="
                currentRoom
                  ? currentRoom.room_type === 'channel'
                    ? 'mdi-pound'
                    : 'mdi-account'
                  : 'mdi-chat-processing-outline'
              "
              size="small"
              color="primary"
              class="mr-2"
            />
            <span class="font-weight-bold text-truncate room-header-title" style="max-width: 260px">
              {{ currentRoom ? getRoomDisplayName(currentRoom) : '실시간 사내 메신저' }}
            </span>
            <span
              v-if="currentRoom?.project_name"
              class="text-xs text-muted ml-2 text-truncate"
              style="max-width: 120px"
            >
              {{ currentRoom.project_name }}
            </span>
          </div>
          <div class="d-flex align-items-center">
            <!-- 대화방 진입 시: 참여 멤버 목록 버튼 -->
            <v-btn
              v-if="currentRoom"
              icon="mdi-account-group-outline"
              variant="text"
              size="small"
              color="primary"
              class="mr-1"
              title="참여 멤버 목록"
              @click="isMembersDrawerOpen = !isMembersDrawerOpen"
            >
              <v-badge
                v-if="(currentRoom.members?.length || 0) > 0"
                :content="currentRoom.members.length"
                color="primary"
                inline
              >
                <v-icon icon="mdi-account-group-outline" size="small" />
              </v-badge>
              <v-icon v-else icon="mdi-account-group-outline" size="small" />
            </v-btn>

            <!-- 목록 화면: 새 1:1 대화 버튼 -->
            <v-btn
              v-if="!currentRoom"
              icon="mdi-account-plus-outline"
              variant="text"
              size="small"
              color="primary"
              class="mr-1"
              title="새 1:1 대화"
              @click="openUserSelectModal"
            />
            <v-btn icon="mdi-close" variant="text" size="small" @click="chatStore.closeDrawer" />
          </div>
        </div>

        <!-- ── 1. 대화방 목록 뷰 ────────────────────────────────── -->
        <div
          v-if="!currentRoom"
          class="chat-list-body d-flex flex-column flex-grow-1 overflow-hidden"
        >
          <!-- 탭 바 -->
          <div class="px-3 pt-2 border-bottom flex-shrink-0 chat-tabs-area">
            <v-tabs v-model="activeTab" density="compact" color="primary" grow>
              <v-tab value="channel">
                🏢 워크스페이스 채널
                <v-badge
                  v-if="chatStore.channelUnreadCount > 0"
                  :content="chatStore.channelUnreadCount"
                  color="error"
                  inline
                  class="ml-1"
                />
              </v-tab>
              <v-tab value="direct">
                🔒 1:1 DM
                <v-badge
                  v-if="chatStore.directUnreadCount > 0"
                  :content="chatStore.directUnreadCount"
                  color="error"
                  inline
                  class="ml-1"
                />
              </v-tab>
            </v-tabs>
          </div>

          <!-- 방 목록 -->
          <div class="flex-grow-1 overflow-y-auto p-2">
            <!-- 채널 목록 -->
            <div v-if="activeTab === 'channel'">
              <div
                v-if="chatStore.channelRooms.length === 0"
                class="text-center py-8 text-sm empty-state-text"
              >
                <v-icon icon="mdi-pound-box-outline" size="large" class="mb-2 opacity-50" /><br />
                참여 중인 워크스페이스 채널이 없습니다.
              </div>
              <v-list v-else density="compact" class="bg-transparent py-0">
                <v-list-item
                  v-for="room in chatStore.channelRooms"
                  :key="room.id"
                  class="rounded-lg mb-1 chat-room-item"
                  @click="handleSelectRoom(room)"
                >
                  <template #prepend>
                    <v-avatar color="primary" variant="tonal" size="36" class="mr-3">
                      <v-icon icon="mdi-pound" size="small" />
                    </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-bold text-sm">
                    {{ room.project_name || room.title }}
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-xs text-truncate">
                    {{ room.last_message?.content || '대화를 시작해보세요' }}
                  </v-list-item-subtitle>
                  <template #append>
                    <div class="text-right">
                      <div class="text-xs timestamp-text">
                        {{ formatTime(room.last_message?.created || room.updated) }}
                      </div>
                      <v-badge
                        v-if="room.unread_count > 0"
                        :content="room.unread_count"
                        color="error"
                        inline
                        class="mt-1"
                      />
                    </div>
                  </template>
                </v-list-item>
              </v-list>
            </div>

            <!-- 1:1 DM 목록 -->
            <div v-else>
              <div
                v-if="chatStore.directRooms.length === 0"
                class="text-center py-8 text-sm empty-state-text"
              >
                <v-icon icon="mdi-message-outline" size="large" class="mb-2 opacity-50" /><br />
                진행 중인 1:1 대화가 없습니다.<br />
                <v-btn
                  color="primary"
                  size="small"
                  variant="flat"
                  class="mt-3"
                  prepend-icon="mdi-account-plus"
                  @click="openUserSelectModal"
                >
                  대화 상대 선택
                </v-btn>
              </div>
              <v-list v-else density="compact" class="bg-transparent py-0">
                <v-list-item
                  v-for="room in chatStore.directRooms"
                  :key="room.id"
                  class="rounded-lg mb-1 chat-room-item"
                  @click="handleSelectRoom(room)"
                >
                  <template #prepend>
                    <v-avatar color="success" variant="tonal" size="36" class="mr-3">
                      <v-icon icon="mdi-account" size="small" />
                    </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-bold text-sm">
                    {{ getRoomDisplayName(room) }}
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-xs text-truncate">
                    {{ room.last_message?.content || '대화를 시작해보세요' }}
                  </v-list-item-subtitle>
                  <template #append>
                    <div class="text-right">
                      <div class="text-xs timestamp-text">
                        {{ formatTime(room.last_message?.created || room.updated) }}
                      </div>
                      <v-badge
                        v-if="room.unread_count > 0"
                        :content="room.unread_count"
                        color="error"
                        inline
                        class="mt-1"
                      />
                    </div>
                  </template>
                </v-list-item>
              </v-list>
            </div>
          </div>
        </div>

        <!-- ── 2. 대화방 채팅창 뷰 ──────────────────────────────── -->
        <div
          v-else
          class="chat-room-body d-flex flex-column flex-grow-1 overflow-hidden position-relative"
          @dragenter="handleDragEnter"
          @dragleave="handleDragLeave"
          @dragover="handleDragOver"
          @drop="handleDrop"
          @paste="handlePaste"
        >
          <!-- 드래그앤드롭 감지 시 나타나는 시각적 드롭존 오버레이 -->
          <div
            v-if="isDragging"
            class="drag-drop-overlay d-flex flex-column align-items-center justify-content-center"
          >
            <v-icon icon="mdi-cloud-upload-outline" size="48" color="primary" class="mb-2 animate-bounce" />
            <div class="font-weight-bold text-sm text-primary">파일을 여기에 놓으면 바로 전송됩니다</div>
            <div class="text-xs text-muted mt-1">도면, 문서, 사진 등 모든 파일 지원</div>
          </div>

          <!-- 메시지 리스트 -->
          <div ref="messageContainer" class="flex-grow-1 overflow-y-auto p-3 chat-messages-area">
            <div v-if="messages.length === 0" class="text-center py-8 text-xs empty-state-text">
              대화가 시작되었습니다. 메시지를 남겨보세요! 👋
            </div>

            <div
              v-for="msg in messages"
              :key="msg.id"
              class="d-flex mb-3 chat-msg-row"
              :class="msg.sender?.pk === currentUserId ? 'justify-end' : 'justify-start'"
            >
              <!-- 상대방 아바타 -->
              <v-avatar
                v-if="msg.sender?.pk !== currentUserId"
                color="primary"
                variant="tonal"
                size="30"
                class="mr-2 mt-1 flex-shrink-0"
              >
                <span class="text-xs font-weight-bold">
                  {{ msg.sender?.username?.slice(0, 1) || '?' }}
                </span>
              </v-avatar>

              <!-- 말풍선 영역 -->
              <div style="max-width: 82%">
                <div
                  v-if="msg.sender?.pk !== currentUserId && currentRoom?.room_type === 'channel'"
                  class="text-xs sender-name-label mb-1 ml-1"
                >
                  {{ msg.sender?.username }}
                </div>
                <div
                  class="p-2.5 rounded-lg text-sm chat-bubble shadow-sm position-relative msg-bubble-wrapper cursor-pointer"
                  :class="msg.sender?.pk === currentUserId ? 'my-bubble ml-auto' : 'other-bubble'"
                  title="더블클릭하여 답장/댓글 쓰기"
                  @dblclick="setReplyTarget(msg)"
                >
                  <!-- 호버 액션 툴바 (답장, 복사 & 다른 방으로 공유/전달) -->
                  <div class="msg-action-toolbar d-flex align-items-center">
                    <v-btn
                      icon="mdi-reply-outline"
                      size="x-small"
                      variant="text"
                      density="compact"
                      title="답장/댓글 쓰기"
                      @click.stop="setReplyTarget(msg)"
                    />
                    <v-btn
                      icon="mdi-content-copy"
                      size="x-small"
                      variant="text"
                      density="compact"
                      title="텍스트/링크 복사"
                      @click.stop="copyMessageContent(msg)"
                    />
                    <v-btn
                      icon="mdi-share-outline"
                      size="x-small"
                      variant="text"
                      density="compact"
                      title="다른 대화방으로 전달/공유"
                      @click.stop="openForwardModal(msg)"
                    />
                  </div>

                  <!-- 0. 답장(댓글) 대상 메시지 인용 표시 -->
                  <div
                    v-if="msg.reply_to_detail"
                    class="p-2 mb-2 rounded reply-quote-box text-xs"
                  >
                    <div class="font-weight-bold reply-quote-sender mb-0.5">
                      <v-icon icon="mdi-reply" size="x-small" class="mr-1" />
                      {{ msg.reply_to_detail.sender_name }}님에게 답장
                    </div>
                    <div class="text-truncate reply-quote-content">
                      {{ msg.reply_to_detail.content }}
                    </div>
                  </div>

                  <!-- 1. 리치 카드 (업무/회의/결재 연계 항목) -->
                  <div v-if="msg.ref_id" class="p-2 mb-2 rounded ref-card text-xs">
                    <div class="font-weight-bold ref-card-title mb-1">
                      📌 {{ msg.ref_title || '연계 항목' }}
                    </div>
                    <div class="ref-card-sub">{{ msg.ref_sub }}</div>
                  </div>

                  <!-- 2. 이미지 첨부파일 -->
                  <div v-if="msg.message_type === 'image' && msg.file" class="chat-image-preview mb-1">
                    <a :href="msg.file" target="_blank" rel="noopener">
                      <img
                        :src="msg.file"
                        :alt="msg.file_name || '사진'"
                        class="rounded mw-100"
                        style="max-height: 200px; object-fit: cover"
                      />
                    </a>
                  </div>

                  <!-- 3. 일반 문서/도면 첨부파일 카드 -->
                  <div
                    v-else-if="msg.message_type === 'file' && msg.file"
                    class="p-2 mb-1 rounded file-attachment-card d-flex align-items-center"
                  >
                    <v-icon icon="mdi-file-document-outline" size="24" class="mr-2 flex-shrink-0" />
                    <div class="flex-grow-1 overflow-hidden mr-2">
                      <div class="font-weight-bold text-truncate text-xs">
                        {{ msg.file_name || '첨부파일' }}
                      </div>
                      <div class="text-xs opacity-75">
                        {{ formatFileSize(msg.file_size) }}
                      </div>
                    </div>
                    <v-btn
                      :href="msg.file"
                      target="_blank"
                      download
                      icon="mdi-download"
                      size="x-small"
                      variant="tonal"
                      class="flex-shrink-0"
                    />
                  </div>

                  <!-- 메시지 본문 텍스트 (텍스트가 있을 때만 표시) -->
                  <div
                    v-if="msg.content && msg.content !== msg.file_name"
                    class="chat-text-content"
                  >
                    {{ msg.content }}
                  </div>
                </div>

                <div
                  class="text-xs timestamp-text mt-1 px-1"
                  :class="msg.sender?.pk === currentUserId ? 'text-right' : 'text-left'"
                >
                  {{ formatTime(msg.created) }}
                </div>
              </div>
            </div>
          </div>

          <!-- 메시지 입력창 영역 (답장 안내 바 + 인풋창) -->
          <div class="chat-input-wrapper border-top flex-shrink-0">
            <!-- 답장 진행 중일 때 나타나는 상단 인용 바 -->
            <div
              v-if="replyingTo"
              class="reply-target-bar px-3 py-2 d-flex align-items-center justify-content-between text-xs"
            >
              <div class="d-flex align-items-center overflow-hidden mr-2">
                <v-icon icon="mdi-reply" size="small" color="primary" class="mr-2 flex-shrink-0" />
                <div class="overflow-hidden">
                  <div class="font-weight-bold text-truncate text-primary">
                    {{ replyingTo.sender?.username || '상대방' }}님에게 답장
                  </div>
                  <div class="text-truncate opacity-75">
                    {{ replyingTo.content || replyingTo.file_name || '첨부파일' }}
                  </div>
                </div>
              </div>
              <v-btn
                icon="mdi-close"
                size="x-small"
                variant="text"
                density="compact"
                @click="cancelReply"
              />
            </div>

            <!-- 하단 인풋 폼 -->
            <div class="px-3 pt-3 pb-4 chat-input-area d-flex align-items-center">
              <!-- 📎 파일/사진 첨부 버튼 -->
              <v-btn
                icon="mdi-paperclip"
                variant="text"
                size="small"
                color="primary"
                class="mr-1"
                :loading="isUploading"
                title="파일/사진 첨부"
                @click="triggerFileUpload"
              />
              <v-text-field
                v-model="inputMessage"
                :placeholder="replyingTo ? '답장 메시지를 입력하세요...' : '메시지를 입력하세요 (Enter)'"
                density="compact"
                variant="outlined"
                hide-details
                class="flex-grow-1 mr-2 text-sm"
                @keydown.enter.prevent="handleSendMessage($event)"
              />
              <v-btn
                icon="mdi-send"
                color="primary"
                size="small"
                variant="flat"
                :disabled="!inputMessage.trim()"
                @click="handleSendMessage()"
              />
            </div>
          </div>
        </div>
      </div>
    </v-navigation-drawer>

    <!-- ── 1:1 대화 상대 선택 모달 ────────────────────────────── -->
    <v-dialog v-model="isUserSelectModalOpen" max-width="420">
      <v-card class="rounded-lg user-select-modal-card">
        <v-card-title
          class="font-weight-bold text-md border-bottom d-flex justify-content-between align-items-center p-3"
        >
          <span>1:1 대화 상대 선택</span>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="isUserSelectModalOpen = false"
          />
        </v-card-title>
        <v-card-text class="p-3">
          <v-text-field
            v-model="userSearchQuery"
            placeholder="이름 또는 아이디 검색"
            prepend-inner-icon="mdi-magnify"
            density="compact"
            variant="outlined"
            hide-details
            class="mb-3 text-sm"
          />
          <div style="max-height: 320px; overflow-y: auto">
            <div v-if="isLoadingUsers" class="text-center py-4">
              <v-progress-circular indeterminate size="24" color="primary" />
            </div>
            <div v-else-if="filteredUsers.length === 0" class="text-center py-4 text-xs empty-state-text">
              검색된 직원이 없습니다.
            </div>
            <v-list v-else density="compact" class="bg-transparent">
              <v-list-item
                v-for="u in filteredUsers"
                :key="u.pk"
                class="rounded mb-1 user-list-item"
                @click="startDmWithUser(u)"
              >
                <template #prepend>
                  <v-avatar
                    color="primary"
                    variant="tonal"
                    size="32"
                    class="mr-2 text-xs font-weight-bold"
                  >
                    {{ u.profile?.name?.[0] || u.username[0] }}
                  </v-avatar>
                </template>
                <v-list-item-title class="text-sm font-weight-bold">
                  {{ u.profile?.name ? `${u.profile.name} (${u.username})` : u.username }}
                </v-list-item-title>
                <v-list-item-subtitle v-if="u.profile?.cell_phone" class="text-xs text-muted">
                  {{ u.profile.cell_phone }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- ── 2. 다른 대화방으로 전달/공유 모달 ──────────────────────── -->
    <v-dialog v-model="isForwardModalOpen" max-width="440">
      <v-card class="rounded-lg user-select-modal-card">
        <v-card-title
          class="font-weight-bold text-md border-bottom d-flex justify-content-between align-items-center p-3"
        >
          <span>다른 대화방으로 전달/공유</span>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="isForwardModalOpen = false"
          />
        </v-card-title>
        <v-card-text class="p-3">
          <div v-if="forwardTargetMsg" class="p-2 mb-3 rounded border text-xs bg-light">
            <span class="font-weight-bold">전달할 내용: </span>
            {{ forwardTargetMsg.content || forwardTargetMsg.file_name || '첨부파일' }}
          </div>
          <div class="text-xs text-muted mb-2 font-weight-bold">전달할 대화방 선택:</div>
          <div style="max-height: 280px; overflow-y: auto">
            <v-list density="compact" class="bg-transparent">
              <v-list-item
                v-for="room in chatStore.rooms"
                :key="room.id"
                class="rounded mb-1 user-list-item"
                @click="handleForwardToRoom(room)"
              >
                <template #prepend>
                  <v-avatar
                    :color="room.room_type === 'channel' ? 'primary' : 'success'"
                    variant="tonal"
                    size="28"
                    class="mr-2"
                  >
                    <v-icon :icon="room.room_type === 'channel' ? 'mdi-pound' : 'mdi-account'" size="x-small" />
                  </v-avatar>
                </template>
                <v-list-item-title class="text-xs font-weight-bold">
                  {{ getRoomDisplayName(room) }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- ── 3. 대화방 참여 멤버 목록 모달 ────────────────────────── -->
    <v-dialog v-model="isMembersDrawerOpen" max-width="400">
      <v-card class="rounded-lg user-select-modal-card">
        <v-card-title
          class="font-weight-bold text-md border-bottom d-flex justify-content-between align-items-center p-3"
        >
          <div class="d-flex align-items-center">
            <v-icon
              :icon="currentRoom?.room_type === 'channel' ? 'mdi-account-group' : 'mdi-account-multiple'"
              color="primary"
              size="small"
              class="mr-2"
            />
            <span>{{ currentRoom?.room_type === 'channel' ? '채널 참여 멤버' : '대화방 참여자' }}</span>
            <v-chip size="x-small" color="primary" class="ml-2 font-weight-bold">
              {{ currentRoom?.members?.length || 0 }}명
            </v-chip>
          </div>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="isMembersDrawerOpen = false"
          />
        </v-card-title>
        <v-card-text class="p-3">
          <div v-if="!currentRoom?.members?.length" class="text-center py-4 text-xs empty-state-text">
            참여 멤버 정보를 불러오는 중입니다.
          </div>
          <div v-else style="max-height: 360px; overflow-y: auto">
            <v-list density="compact" class="bg-transparent py-0">
              <v-list-item
                v-for="m in currentRoom.members"
                :key="m.pk"
                class="rounded mb-1 user-list-item"
              >
                <template #prepend>
                  <v-avatar
                    :color="m.pk === currentUserId ? 'primary' : 'success'"
                    variant="tonal"
                    size="32"
                    class="mr-2 text-xs font-weight-bold"
                  >
                    {{ (m as any).name?.[0] || m.username[0] }}
                  </v-avatar>
                </template>
                <v-list-item-title class="text-xs font-weight-bold d-flex align-items-center">
                  <span>{{ (m as any).name ? `${(m as any).name} (${m.username})` : m.username }}</span>
                  <v-chip
                    v-if="m.pk === currentUserId"
                    size="x-small"
                    color="primary"
                    variant="flat"
                    class="ml-1.5 px-1 font-weight-bold"
                    style="height: 16px; font-size: 9px"
                  >
                    나
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle v-if="(m as any).email" class="text-xs text-muted">
                  {{ (m as any).email }}
                </v-list-item-subtitle>
                <template #append>
                  <v-btn
                    v-if="m.pk !== currentUserId"
                    icon="mdi-message-outline"
                    variant="text"
                    size="x-small"
                    color="primary"
                    title="1:1 대화 시작"
                    @click="isMembersDrawerOpen = false; chatStore.getOrCreateDm(m.pk)"
                  />
                </template>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- ── 클립보드 복사 알림 스낵바 ────────────────────────────── -->
    <v-snackbar
      v-model="copySnackbar"
      :timeout="2000"
      location="top"
      color="secondary"
      density="compact"
      rounded="pill"
    >
      <div class="text-center text-xs font-weight-medium">
        {{ copySnackbarText }}
      </div>
    </v-snackbar>
  </div>
</template>

<style scoped>
.chat-drawer {
  z-index: 1050 !important;
}
.chat-drawer :deep(.v-navigation-drawer__content) {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ==========================================================================
   라이트 모드 (기본 테마)
   ========================================================================== */
.chat-main-container {
  background-color: #ffffff;
  color: #1e293b;
}
.chat-header,
.chat-tabs-area,
.chat-input-area {
  background-color: #ffffff;
  border-color: #e2e8f0 !important;
}
.room-header-title {
  color: #0f172a;
}
.chat-messages-area {
  background-color: #f1f5f9;
}
.chat-room-item:hover,
.user-list-item:hover {
  background-color: #f1f5f9;
}
.empty-state-text,
.timestamp-text {
  color: #64748b;
  font-size: 0.72rem;
}
.sender-name-label {
  color: #334155;
  font-weight: 600;
  font-size: 0.75rem;
}

/* 라이트모드 말풍선: 날렵하고 세련된 패딩 (세로 7px, 가로 13px) + 자연스러운 색감 */
.chat-bubble {
  padding: 7px 13px !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
.msg-action-toolbar {
  position: absolute;
  top: -22px;
  right: 6px;
  background-color: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 20px;
  padding: 2px 4px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s ease-in-out, visibility 0.15s;
  z-index: 20;
}
.msg-action-toolbar .v-btn {
  color: #475569 !important;
}
.msg-action-toolbar .v-btn:hover {
  color: #1e293b !important;
  background-color: #f1f5f9 !important;
}
/* 마우스가 툴바로 이동할 때 hover가 끊기지 않도록 투명 브릿지 영역 생성 */
.msg-action-toolbar::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  height: 12px;
}
.msg-bubble-wrapper:hover .msg-action-toolbar,
.msg-action-toolbar:hover {
  opacity: 1;
  visibility: visible;
}
.dark-drawer .msg-action-toolbar {
  background-color: #242b3a !important;
  border-color: #3e485e !important;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.45);
}
.dark-drawer .msg-action-toolbar .v-btn {
  color: #cbd5e1 !important;
}
.dark-drawer .msg-action-toolbar .v-btn:hover {
  color: #ffffff !important;
  background-color: #333c52 !important;
}

/* 답장/댓글 원본 인용 박스 */
.reply-quote-box {
  background-color: rgba(0, 0, 0, 0.05);
  border-left: 3px solid #3b82f6;
  border-radius: 4px;
}
.my-bubble .reply-quote-box {
  background-color: rgba(0, 0, 0, 0.15);
  border-left-color: #ffffff;
}
.reply-quote-sender {
  color: #2563eb;
  font-size: 0.72rem;
}
.my-bubble .reply-quote-sender {
  color: #ffffff;
}
.reply-quote-content {
  color: #475569;
  font-size: 0.72rem;
}
.my-bubble .reply-quote-content {
  color: #e2e8f0;
}

/* 다크모드 답장 원본 인용 박스 */
.dark-drawer .reply-quote-box {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border-left: 3px solid #60a5fa !important;
}
.dark-drawer .reply-quote-sender {
  color: #93c5fd !important;
}
.dark-drawer .reply-quote-content {
  color: #cbd5e1 !important;
}

/* 하단 답장 대상 안내 바 */
.reply-target-bar {
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.dark-drawer .reply-target-bar {
  background-color: #1a1e27 !important;
  border-color: #2e3547 !important;
  color: #f1f5f9 !important;
}

.my-bubble {
  background-color: #e2eefc; /* 눈이 아주 편안하고 세련된 소프트 파스텔 연청색 */
  color: #0f2e5c; /* 시인성이 뛰어난 딥 네이비 텍스트 */
  border: 1px solid #c7defa;
  border-radius: 14px 14px 2px 14px;
}
.other-bubble {
  background-color: #ffffff;
  color: #1e293b; /* 가독성 좋은 차콜 네이비 */
  border: 1px solid #e2e8f0;
  border-radius: 14px 14px 14px 2px;
}
.chat-text-content {
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.45;
  font-size: 0.88rem;
}

/* 라이트모드 리치 카드 */
.ref-card {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 6px 9px;
}
.my-bubble .ref-card {
  background-color: rgba(255, 255, 255, 0.7);
  border-color: #c7defa;
  color: #0f2e5c;
}
.ref-card-title {
  color: #2563eb;
  font-weight: 600;
}
.my-bubble .ref-card-title {
  color: #1d4ed8;
}
.ref-card-sub {
  color: #64748b;
}
.my-bubble .ref-card-sub {
  color: #475569;
}

/* 라이트모드 첨부파일 카드 */
.file-attachment-card {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  max-width: 260px;
}
.my-bubble .file-attachment-card {
  background-color: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.3);
  color: #ffffff;
}
.chat-image-preview img {
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: opacity 0.2s;
}
.chat-image-preview img:hover {
  opacity: 0.9;
}

/* ==========================================================================
   다크 모드 (IBS CoreUI 다크 테마 일원화)
   ========================================================================== */
.dark-drawer .chat-main-container {
  background-color: #1e222d !important;
  color: #f1f5f9 !important;
}
.dark-drawer .chat-header,
.dark-drawer .chat-tabs-area,
.dark-drawer .chat-input-area {
  background-color: #1e222d !important;
  border-color: #2e3547 !important;
}
.dark-drawer .room-header-title {
  color: #f8fafc !important;
}
.dark-drawer .chat-messages-area {
  background-color: #11141a !important;
}
.dark-drawer .chat-room-item:hover,
.dark-drawer .user-list-item:hover {
  background-color: #282e3f !important;
}
.dark-drawer .empty-state-text,
.dark-drawer .timestamp-text {
  color: #94a3b8 !important;
  font-size: 0.72rem;
}
.dark-drawer .sender-name-label {
  color: #cbd5e1 !important;
  font-weight: 600;
  font-size: 0.75rem;
}

/* 다크모드 말풍선: 눈이 편안한 고급 슬레이트 블루(내 메시지) & 다크 차콜(상대 메시지) */
.dark-drawer .my-bubble {
  background-color: #2b3a55 !important; /* 눈이 아주 편안한 차분한 슬레이트 네이비/블루 */
  color: #f8fafc !important; /* 맑고 선명한 화이트 */
  border: 1px solid #3d4f72 !important;
  border-radius: 14px 14px 2px 14px;
}
.dark-drawer .other-bubble {
  background-color: #202430 !important;
  color: #e2e8f0 !important;
  border: 1px solid #2d3345 !important;
  border-radius: 14px 14px 14px 2px;
}

/* 다크모드 리치 카드 & 첨부파일 카드 */
.dark-drawer .my-bubble .ref-card,
.dark-drawer .my-bubble .file-attachment-card {
  background-color: rgba(0, 0, 0, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.15) !important;
  color: #ffffff !important;
}
.dark-drawer .other-bubble .ref-card,
.dark-drawer .other-bubble .file-attachment-card {
  background-color: #171a22 !important;
  border-color: #2d3345 !important;
  padding: 6px 9px;
  color: #e2e8f0 !important;
}
.dark-drawer .other-bubble .ref-card-title {
  color: #93c5fd !important;
  font-weight: 600;
}
.dark-drawer .other-bubble .ref-card-sub {
  color: #94a3b8 !important;
}
.dark-drawer .chat-image-preview img {
  border-color: #2d3345;
}

/* ── 드래그 앤 드롭 오버레이 스타일 ───────────────────────── */
.drag-drop-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.92);
  border: 2px dashed #2563eb;
  z-index: 50;
  pointer-events: none;
  backdrop-filter: blur(2px);
}
.dark-drawer .drag-drop-overlay {
  background-color: rgba(20, 23, 31, 0.92) !important;
  border-color: #3b82f6 !important;
}
.animate-bounce {
  animation: bounce 1s infinite alternate;
}
@keyframes bounce {
  from {
    transform: translateY(0);
  }
  to {
    transform: translateY(-8px);
  }
}

/* 다크모드 1:1 선택 모달 */
.dark-theme .user-select-modal-card {
  background-color: #1e222d !important;
  color: #f1f5f9 !important;
}
</style>
