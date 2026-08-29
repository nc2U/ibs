<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useApproval } from '@/store/pinia/approval'
import { useIssue } from '@/store/pinia/work_issue'
import { useChat } from '@/store/pinia/chat'
import { playNotificationSound } from '@/utils/sound'
import TodoModal from '@/components/Modals/TodoModal.vue'

const router = useRouter()
const accountStore = useAccount()
const approvalStore = useApproval()
const issueStore = useIssue()
const chatStore = useChat()

const refsTodoModal = ref()
let isInitial = true

const isStaff = computed(() => accountStore.isStaff)
const isAuthorized = computed(() => accountStore.isAuthorized)
const userPk = computed(() => accountStore.userInfo?.pk)

const pendingCount = computed(() => approvalStore.pendingList.length)
const inProgressDraftCount = computed(
  () => approvalStore.draftedList.filter(d => d.status === 'pending').length,
)
const assignedIssueCount = computed(() => issueStore.issueNumByMember.open_charged || 0)
const todoCount = computed(() => accountStore.myTodos.length)
const unreadChatCount = computed(() => chatStore.totalUnreadCount)

// 결재 대기 건수 증가 시 알림 사운드 재생
watch(pendingCount, (newVal, oldVal) => {
  if (!isInitial && newVal > (oldVal ?? 0)) {
    playNotificationSound()
  }
})

const fetchAllCounts = () => {
  if (isAuthorized.value) {
    if (isStaff.value) {
      approvalStore.fetchMyPending()
      approvalStore.fetchMyDrafted()
    }
    issueStore.fetchIssueByMember(userPk.value ? String(userPk.value) : undefined)
    accountStore.fetchTodoList()
    chatStore.fetchTotalUnread()
  }
}

let pollTimer: any = null

onMounted(() => {
  fetchAllCounts()
  setTimeout(() => {
    isInitial = false
  }, 2000)

  // 15초 주기로 헤더 알림 & 메신저 미확인 배지 자동 갱신
  pollTimer = setInterval(() => {
    if (isAuthorized.value && !document.hidden) {
      chatStore.fetchRooms()
      chatStore.fetchTotalUnread()
    }
  }, 15000)
})

watch(
  () => [isAuthorized.value, userPk.value],
  ([auth]) => {
    if (auth) fetchAllCounts()
  },
)

const goApproval = () => {
  router.push('/approval/pending')
}

const goDrafted = () => {
  router.push('/approval/drafted')
}

const goIssue = () => {
  router.push('/work/issue')
}

const openTodo = () => {
  refsTodoModal.value?.callModal()
}
</script>

<template>
  <div v-if="isAuthorized" class="header-notification-bar d-flex align-items-center gap-2">
    <!-- 1. 결재 대기 알림 (본사 스태프 전용) -->
    <v-chip
      v-if="isStaff"
      size="small"
      variant="tonal"
      :color="pendingCount > 0 ? 'warning' : 'secondary'"
      class="cursor-pointer font-weight-medium px-3"
      @click="goApproval"
    >
      <v-icon icon="mdi-file-check-outline" start size="small" />
      결재 대기
      <v-badge v-if="pendingCount > 0" :content="pendingCount" color="danger" inline class="ms-1" />
      <span v-else class="text-caption ms-1 text-disabled">0</span>
      <v-tooltip activator="parent" location="bottom">
        {{
          pendingCount > 0 ? `결재 대기 문서 ${pendingCount}건` : '대기 중인 결재 문서가 없습니다'
        }}
      </v-tooltip>
    </v-chip>

    <!-- 2. 내 기안 문서 알림 (결재 진행중 건수) -->
    <v-chip
      v-if="isStaff"
      size="small"
      variant="tonal"
      :color="inProgressDraftCount > 0 ? 'warning' : 'secondary'"
      class="cursor-pointer font-weight-medium px-3"
      @click="goDrafted"
    >
      <v-icon icon="mdi-file-send-outline" start size="small" />
      내 기안
      <v-badge
        v-if="inProgressDraftCount > 0"
        :content="inProgressDraftCount"
        color="danger"
        inline
        class="ms-1"
      />
      <span v-else class="text-caption ms-1 text-disabled">0</span>
      <v-tooltip activator="parent" location="bottom">
        {{
          inProgressDraftCount > 0
            ? `결재 진행 중인 내 기안 ${inProgressDraftCount}건 (클릭하여 기안함 열기)`
            : '진행 중인 기안 문서가 없습니다'
        }}
      </v-tooltip>
    </v-chip>

    <!-- 3. 담당 업무 알림 -->
    <v-chip
      size="small"
      variant="text"
      :color="assignedIssueCount > 0 ? 'success' : 'secondary'"
      class="cursor-pointer font-weight-medium px-2"
      @click="goIssue"
    >
      <v-icon icon="mdi-clipboard-text-clock-outline" start size="small" />
      담당 업무
      <v-badge
        v-if="assignedIssueCount > 0"
        :content="assignedIssueCount"
        color="success"
        inline
        class="ms-1"
      />
      <span v-else class="text-caption ms-1 text-disabled">0</span>
      <v-tooltip activator="parent" location="bottom">
        {{
          assignedIssueCount > 0
            ? `내게 할당된 미완료 업무 ${assignedIssueCount}건`
            : '진행 중인 담당 업무가 없습니다'
        }}
      </v-tooltip>
    </v-chip>

    <!-- 4. 오늘의 할일 알림 -->
    <v-chip
      size="small"
      variant="text"
      :color="todoCount > 0 ? 'info' : 'secondary'"
      class="cursor-pointer font-weight-medium px-2"
      @click="openTodo"
    >
      <v-icon icon="mdi-calendar-check-outline" start size="small" />
      할일
      <v-badge v-if="todoCount > 0" :content="todoCount" color="info" inline class="ms-1" />
      <span v-else class="text-caption ms-1 text-disabled">0</span>
      <v-tooltip activator="parent" location="bottom">
        {{ todoCount > 0 ? `남은 할일 ${todoCount}건 (클릭하여 열기)` : '등록된 할일이 없습니다' }}
      </v-tooltip>
    </v-chip>

    <!-- 5. 실시간 사내 메신저 알림 & 토글 -->
    <v-chip
      size="small"
      variant="text"
      :color="unreadChatCount > 0 ? 'primary' : 'secondary'"
      class="cursor-pointer font-weight-medium px-2"
      @click="chatStore.toggleDrawer"
    >
      <v-icon icon="mdi-chat-processing-outline" start size="small" />
      메신저
      <v-badge v-if="unreadChatCount > 0" :content="unreadChatCount" color="error" inline class="ms-1" />
      <span v-else class="text-caption ms-1 text-disabled">0</span>
      <v-tooltip activator="parent" location="bottom">
        {{ unreadChatCount > 0 ? `미확인 메시지 ${unreadChatCount}건 (클릭하여 메신저 열기)` : '실시간 메신저 열기' }}
      </v-tooltip>
    </v-chip>

    <TodoModal ref="refsTodoModal" />
  </div>
</template>

<style scoped>
.header-notification-bar :deep(.v-chip) {
  transition: all 0.2s ease-in-out;
}
.header-notification-bar :deep(.v-chip:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
