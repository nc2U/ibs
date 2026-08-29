<script lang="ts" setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useChat } from '@/store/pinia/chat'
import { useAccount } from '@/store/pinia/account'
import api from '@/api'
import type { ChatRoom, ChatUser } from '@/store/types/chat'

const chatStore = useChat()
const accountStore = useAccount()

const currentUserId = computed(() => accountStore.userInfo?.pk ?? 0)
const isDrawerOpen = computed(() => chatStore.isDrawerOpen)
const currentRoom = computed(() => chatStore.currentRoom)
const messages = computed(() => chatStore.messages)

const activeTab = ref<'channel' | 'direct'>('channel')
const inputMessage = ref('')
const messageContainer = ref<HTMLElement | null>(null)

// 1:1 대화 상대 선택 모달 상태
const isUserSelectModalOpen = ref(false)
const userSearchQuery = ref('')
const allUsers = ref<any[]>([])
const isLoadingUsers = ref(false)

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

// 1:1 상대 선택 모달 열기
const openUserSelectModal = async () => {
  isUserSelectModalOpen.value = true
  userSearchQuery.value = ''
  isLoadingUsers.value = true
  try {
    const res = await api.get('/user/', {
      params: { is_active: true, staff__status: '1' },
      hideProgress: true,
    } as any)
    allUsers.value = res.data.results || res.data
  } catch (_) {
  } finally {
    isLoadingUsers.value = false
  }
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
      width="380"
      class="chat-drawer shadow-lg"
    >
      <div class="d-flex flex-column h-100 bg-surface">
        <!-- ── 헤더 ────────────────────────────────────────────── -->
        <div class="chat-header p-3 border-bottom d-flex align-items-center justify-content-between flex-shrink-0 bg-surface">
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
              :icon="currentRoom ? (currentRoom.room_type === 'channel' ? 'mdi-pound' : 'mdi-account') : 'mdi-chat-processing-outline'"
              size="small"
              color="primary"
              class="mr-2"
            />
            <span class="font-weight-bold text-truncate" style="max-width: 220px;">
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
        <div v-if="!currentRoom" class="chat-list-body d-flex flex-column flex-grow-1 overflow-hidden">
          <!-- 탭 바 -->
          <div class="px-3 pt-2 border-bottom bg-surface flex-shrink-0">
            <v-tabs v-model="activeTab" density="compact" color="primary" grow>
              <v-tab value="channel">🏢 워크스페이스 채널</v-tab>
              <v-tab value="direct">🔒 1:1 DM</v-tab>
            </v-tabs>
          </div>

          <!-- 방 목록 -->
          <div class="flex-grow-1 overflow-y-auto p-2">
            <!-- 채널 목록 -->
            <div v-if="activeTab === 'channel'">
              <div v-if="chatStore.channelRooms.length === 0" class="text-center text-muted py-8 text-sm">
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
                      <div class="text-xs text-muted">
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
              <div v-if="chatStore.directRooms.length === 0" class="text-center text-muted py-8 text-sm">
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
                      <div class="text-xs text-muted">
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
            <div v-if="messages.length === 0" class="text-center text-muted py-8 text-xs">
              대화가 시작되었습니다. 메시지를 남겨보세요! 👋
            </div>

            <div
              v-for="msg in messages"
              :key="msg.id"
              class="d-flex mb-3"
              :class="msg.sender?.pk === currentUserId ? 'justify-end' : 'justify-start'"
            >
              <!-- 상대방 아바타 -->
              <v-avatar
                v-if="msg.sender?.pk !== currentUserId"
                color="grey-lighten-2"
                size="28"
                class="mr-2 mt-1 flex-shrink-0"
              >
                <span class="text-xs font-weight-bold text-dark">
                  {{ msg.sender?.username?.slice(0, 1) || '?' }}
                </span>
              </v-avatar>

              <!-- 말풍선 -->
              <div style="max-width: 78%;">
                <div
                  v-if="msg.sender?.pk !== currentUserId && currentRoom?.room_type === 'channel'"
                  class="text-xs text-muted mb-1 ml-1"
                >
                  {{ msg.sender?.username }}
                </div>
                <div
                  class="p-2 rounded-lg text-sm"
                  :class="
                    msg.sender?.pk === currentUserId
                      ? 'bg-primary text-white ml-auto'
                      : 'bg-light text-dark border'
                  "
                  style="word-break: break-word; white-space: pre-wrap;"
                >
                  <!-- 리치 카드 (업무/회의/결재) -->
                  <div v-if="msg.ref_id" class="p-2 mb-1 rounded bg-white text-dark border text-xs">
                    <div class="font-weight-bold text-primary mb-1">
                      📌 {{ msg.ref_title || '연계 항목' }}
                    </div>
                    <div class="text-muted">{{ msg.ref_sub }}</div>
                  </div>
                  {{ msg.content }}
                </div>
                <div
                  class="text-xs text-muted mt-1 px-1"
                  :class="msg.sender?.pk === currentUserId ? 'text-right' : 'text-left'"
                >
                  {{ formatTime(msg.created) }}
                </div>
              </div>
            </div>
          </div>

          <!-- 메시지 입력창 (하단 고정) -->
          <div class="p-2 border-top bg-surface d-flex align-items-center flex-shrink-0">
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
      <v-card class="rounded-lg">
        <v-card-title class="font-weight-bold text-md border-bottom d-flex justify-content-between align-items-center p-3">
          <span>1:1 대화 상대 선택</span>
          <v-btn icon="mdi-close" variant="text" size="small" @click="isUserSelectModalOpen = false" />
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
          <div style="max-height: 320px; overflow-y: auto;">
            <div v-if="isLoadingUsers" class="text-center py-4">
              <v-progress-circular indeterminate size="24" color="primary" />
            </div>
            <div v-else-if="filteredUsers.length === 0" class="text-center text-muted py-4 text-xs">
              검색된 직원이 없습니다.
            </div>
            <v-list v-else density="compact">
              <v-list-item
                v-for="u in filteredUsers"
                :key="u.pk"
                class="rounded mb-1 hover-bg"
                @click="startDmWithUser(u)"
              >
                <template #prepend>
                  <v-avatar color="primary" size="32" class="mr-2 text-xs font-weight-bold text-white">
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
.chat-room-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
.chat-messages-area {
  background-color: #f8fafc;
}
</style>
