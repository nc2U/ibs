<script lang="ts" setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useChat } from '@/store/pinia/chat'
import { useAccount } from '@/store/pinia/account'
import { useStore } from '@/store'
import type { ChatRoom } from '@/store/types/chat'

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

const getRoomDisplayName = (room: ChatRoom) => {
  if (room.room_type === 'direct') {
    const other = room.members.find(m => m.pk !== currentUserId.value)
    return other ? other.username : '1:1 대화'
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

const handleSendMessage = (event?: KeyboardEvent) => {
  // 한글 입력(IME) 조합 중 엔터 입력 시 중복 발송 방지
  if (event && event.isComposing) return
  if (!inputMessage.value.trim()) return

  const text = inputMessage.value
  inputMessage.value = ''
  chatStore.sendMessage(text)
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

const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div>
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
            <span class="font-weight-bold text-truncate room-header-title" style="max-width: 300px">
              {{ currentRoom ? getRoomDisplayName(currentRoom) : '실시간 사내 메신저' }}
            </span>
          </div>
          <div class="d-flex align-items-center">
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
              <v-tab value="channel">🏢 워크스페이스 채널</v-tab>
              <v-tab value="direct">🔒 1:1 DM</v-tab>
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
        <div v-else class="chat-room-body d-flex flex-column flex-grow-1 overflow-hidden">
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
              <div style="max-width: 80%">
                <div
                  v-if="msg.sender?.pk !== currentUserId && currentRoom?.room_type === 'channel'"
                  class="text-xs sender-name-label mb-1 ml-1"
                >
                  {{ msg.sender?.username }}
                </div>
                <div
                  class="p-2.5 rounded-lg text-sm chat-bubble shadow-sm"
                  :class="msg.sender?.pk === currentUserId ? 'my-bubble ml-auto' : 'other-bubble'"
                >
                  <!-- 리치 카드 (업무/회의/결재 연계 항목) -->
                  <div v-if="msg.ref_id" class="p-2 mb-2 rounded ref-card text-xs">
                    <div class="font-weight-bold ref-card-title mb-1">
                      📌 {{ msg.ref_title || '연계 항목' }}
                    </div>
                    <div class="ref-card-sub">{{ msg.ref_sub }}</div>
                  </div>

                  <!-- 메시지 본문 텍스트 -->
                  <div class="chat-text-content">{{ msg.content }}</div>
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

          <!-- 메시지 입력창 (하단 고정 & 넉넉한 바닥 여백) -->
          <div class="px-3 pt-3 pb-4 border-top chat-input-area d-flex align-items-center flex-shrink-0">
            <v-text-field
              v-model="inputMessage"
              placeholder="메시지를 입력하세요 (Enter)"
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
.my-bubble {
  background-color: #3b82f6; /* 눈이 편안하고 화사한 모던 소프트 블루 */
  color: #ffffff;
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
  background-color: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.3);
  color: #ffffff;
}
.ref-card-title {
  color: #2563eb;
  font-weight: 600;
}
.my-bubble .ref-card-title {
  color: #ffffff;
}
.ref-card-sub {
  color: #64748b;
}
.my-bubble .ref-card-sub {
  color: #e2e8f0;
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

/* 다크모드 리치 카드 */
.dark-drawer .my-bubble .ref-card {
  background-color: rgba(0, 0, 0, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.15) !important;
}
.dark-drawer .other-bubble .ref-card {
  background-color: #171a22 !important;
  border-color: #2d3345 !important;
  padding: 6px 9px;
}
.dark-drawer .other-bubble .ref-card-title {
  color: #93c5fd !important;
  font-weight: 600;
}
.dark-drawer .other-bubble .ref-card-sub {
  color: #94a3b8 !important;
}

/* 다크모드 1:1 선택 모달 */
.dark-theme .user-select-modal-card {
  background-color: #1e222d !important;
  color: #f1f5f9 !important;
}
</style>
