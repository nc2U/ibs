<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useApproval } from '@/store/pinia/approval'
import { useIssue } from '@/store/pinia/work_issue'
import TodoModal from '@/components/Modals/TodoModal.vue'

const router = useRouter()
const accountStore = useAccount()
const approvalStore = useApproval()
const issueStore = useIssue()

const refsTodoModal = ref()

const isStaff = computed(() => accountStore.isStaff)
const isAuthorized = computed(() => accountStore.isAuthorized)
const userPk = computed(() => accountStore.userInfo?.pk)

const pendingCount = computed(() => approvalStore.pendingList.length)
const assignedIssueCount = computed(() => issueStore.issueNumByMember.open_charged || 0)
const todoCount = computed(() => accountStore.myTodos.length)

const fetchAllCounts = () => {
  if (isAuthorized.value) {
    if (isStaff.value) {
      approvalStore.fetchMyPending()
    }
    issueStore.fetchIssueByMember(userPk.value ? String(userPk.value) : undefined)
    accountStore.fetchTodoList()
  }
}

onMounted(() => {
  fetchAllCounts()
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
      :color="pendingCount > 0 ? 'error' : 'secondary'"
      class="cursor-pointer font-weight-medium px-3"
      @click="goApproval"
    >
      <v-icon icon="mdi-file-check-outline" start size="small" />
      결재 대기
      <v-badge v-if="pendingCount > 0" :content="pendingCount" color="error" inline class="ms-1" />
      <span v-else class="text-caption ms-1 text-disabled">0</span>
      <v-tooltip activator="parent" location="bottom">
        {{
          pendingCount > 0 ? `결재 대기 문서 ${pendingCount}건` : '대기 중인 결재 문서가 없습니다'
        }}
      </v-tooltip>
    </v-chip>

    <!-- 2. 담당 업무 알림 -->
    <v-chip
      size="small"
      variant="tonal"
      :color="assignedIssueCount > 0 ? 'primary' : 'secondary'"
      class="cursor-pointer font-weight-medium px-3"
      @click="goIssue"
    >
      <v-icon icon="mdi-clipboard-text-clock-outline" start size="small" />
      담당 업무
      <v-badge
        v-if="assignedIssueCount > 0"
        :content="assignedIssueCount"
        color="primary"
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

    <!-- 3. 오늘의 할일 알림 -->
    <v-chip
      size="small"
      variant="tonal"
      :color="todoCount > 0 ? 'success' : 'secondary'"
      class="cursor-pointer font-weight-medium px-3"
      @click="openTodo"
    >
      <v-icon icon="mdi-calendar-check-outline" start size="small" />
      할일
      <v-badge v-if="todoCount > 0" :content="todoCount" color="success" inline class="ms-1" />
      <span v-else class="text-caption ms-1 text-disabled">0</span>
      <v-tooltip activator="parent" location="bottom">
        {{ todoCount > 0 ? `남은 할일 ${todoCount}건 (클릭하여 열기)` : '등록된 할일이 없습니다' }}
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
