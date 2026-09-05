<script lang="ts" setup>
import { computed, ref, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { diffDate } from '@/utils/baseMixins.ts'
import type { Issue, IssueStatus, CodeValue, Tracker } from '@/store/types/work_issue.ts'
import IssueDropDown from './IssueDropDown.vue'
import NoData from '@/components/NoData/Index.vue'

const props = defineProps({
  issueList: { type: Array as PropType<Issue[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  priorityList: { type: Array as PropType<CodeValue[]>, default: () => [] },
  trackerList: { type: Array as PropType<Tracker[]>, default: () => [] },
})

const route = useRoute()
const accStore = useAccount()
const issueStore = useIssue()
const { can, PERM } = usePerms()

const canIssueUpdate = computed(() => can(PERM.ISSUE_UPDATE) || can(PERM.ISSUE_OWN_UPDATE))

// Local filter states for Kanban board
const kanbanSearch = ref('')
const onlyMyIssues = ref(false)

const filteredIssues = computed(() => {
  return props.issueList.filter(issue => {
    // 1. Search term (title or issue ID)
    if (kanbanSearch.value.trim()) {
      const q = kanbanSearch.value.trim().toLowerCase()
      const matchSubject = issue.subject?.toLowerCase().includes(q)
      const matchId = String(issue.pk).includes(q)
      const matchProject = issue.project?.name?.toLowerCase().includes(q)
      if (!matchSubject && !matchId && !matchProject) return false
    }

    // 2. Only my issues
    if (onlyMyIssues.value && accStore.userInfo?.pk) {
      const isMine =
        issue.assigned_to?.pk === accStore.userInfo.pk || issue.creator?.pk === accStore.userInfo.pk
      if (!isMine) return false
    }

    return true
  })
})

// Group issues by status
const issuesByStatus = computed(() => {
  const map = new Map<number, Issue[]>()

  // Initialize map with all available statuses
  props.statusList.forEach(st => {
    map.set(st.pk, [])
  })

  filteredIssues.value.forEach(issue => {
    const statusPk = issue.status?.pk
    if (statusPk && map.has(statusPk)) {
      map.get(statusPk)!.push(issue)
    } else if (statusPk) {
      map.set(statusPk, [issue])
    }
  })

  return map
})

// Color helper for statuses
const getStatusBorderColor = (status: IssueStatus) => {
  if (status.closed) return '#2eb85c'
  if (status.name.includes('진행')) return '#321fdb'
  if (status.name.includes('해결')) return '#9b59b6'
  if (status.name.includes('피드백') || status.name.includes('보류')) return '#f9b115'
  return '#39f'
}

// Color helper for priorities
const getPriorityColor = (priorityPk?: number) => {
  if (priorityPk === 2) return 'cyan-accent-4'
  if (priorityPk === 3) return 'deep-orange-lighten-1'
  if (priorityPk === 4) return 'deep-orange-darken-4'
  if (priorityPk === 5) return 'pink-darken-4'
  return 'blue-grey-lighten-2'
}

// Drag & Drop State
const draggedIssue = ref<Issue | null>(null)
const dragOverStatusId = ref<number | null>(null)

const onDragStart = (event: DragEvent, issue: Issue) => {
  draggedIssue.value = issue
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(issue.pk))
  }
}

const onDragEnd = () => {
  draggedIssue.value = null
  dragOverStatusId.value = null
}

const onDragOver = (statusId: number) => {
  if (canIssueUpdate.value) {
    dragOverStatusId.value = statusId
  }
}

const onDragLeave = (statusId: number) => {
  if (dragOverStatusId.value === statusId) {
    dragOverStatusId.value = null
  }
}

const onDrop = async (targetStatus: IssueStatus) => {
  dragOverStatusId.value = null
  if (!draggedIssue.value || !canIssueUpdate.value) return

  const issue = draggedIssue.value
  if (issue.status.pk === targetStatus.pk) return

  const formData = new FormData()
  formData.append('status', targetStatus.pk.toString())
  if (targetStatus.closed && issue.done_ratio < 100) {
    formData.append('done_ratio', '100')
  }

  // Optimistic UI update
  issue.status = { ...issue.status, pk: targetStatus.pk, name: targetStatus.name }

  await issueStore.patchIssue(issue.pk, formData)
  draggedIssue.value = null
}
</script>

<template>
  <div class="issue-kanban-wrapper mt-3">
    <!-- Kanban Header Controls -->
    <div class="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
      <div class="d-flex align-items-center gap-3">
        <div style="width: 260px">
          <CFormInput
            v-model="kanbanSearch"
            size="sm"
            placeholder="칸반 내 검색 (제목, #번호, 워크스페이스)"
            clearable
          >
            <template #prepend>
              <CInputGroupText>
                <v-icon icon="mdi-magnify" size="14" />
              </CInputGroupText>
            </template>
          </CFormInput>
        </div>

        <CFormCheck
          v-model="onlyMyIssues"
          id="onlyMyIssuesCheck"
          label="내 담당/등록 업무만 보기"
          class="small mb-0"
        />
      </div>

      <div class="text-muted small">
        총 <strong>{{ filteredIssues.length }}</strong
        >건의 업무
      </div>
    </div>

    <!-- Empty state if no issues match filter -->
    <NoData v-if="!filteredIssues.length && !issueList.length" />

    <!-- Kanban Columns Container -->
    <div v-else class="kanban-board-scroll">
      <div class="kanban-columns-container">
        <div
          v-for="status in statusList"
          :key="status.pk"
          class="kanban-column bg-more-light"
          :class="{ 'drag-over': dragOverStatusId === status.pk }"
          @dragover.prevent="onDragOver(status.pk)"
          @dragleave="onDragLeave(status.pk)"
          @drop.prevent="onDrop(status)"
        >
          <!-- Column Header -->
          <div
            class="kanban-column-header bg-more-white"
            :style="{ borderTopColor: getStatusBorderColor(status) }"
          >
            <div class="d-flex align-items-center justify-content-between">
              <span class="column-title">
                <v-icon
                  :icon="status.closed ? 'mdi-check-circle' : 'mdi-circle-slice-5'"
                  size="14"
                  :color="getStatusBorderColor(status)"
                  class="mr-1"
                />
                {{ status.name }}
              </span>
              <span class="badge rounded-pill bg-more-light text-body border">
                {{ issuesByStatus.get(status.pk)?.length || 0 }}
              </span>
            </div>
          </div>

          <!-- Cards List in Column -->
          <div class="kanban-cards-list">
            <div
              v-for="issue in issuesByStatus.get(status.pk) || []"
              :key="issue.pk"
              class="kanban-card card shadow-sm mb-2 bg-more-white"
              :draggable="canIssueUpdate"
              @dragstart="onDragStart($event, issue)"
              @dragend="onDragEnd"
            >
              <div class="card-body p-2">
                <!-- Card Header: Tracker, Priority, Dropdown -->
                <div class="d-flex align-items-center justify-content-between mb-1">
                  <div class="d-flex align-items-center gap-1">
                    <span
                      class="badge bg-more-light text-secondary border small"
                      style="font-size: 11px"
                    >
                      {{ issue.tracker?.name || '업무' }}
                    </span>
                    <v-chip
                      size="x-small"
                      :color="getPriorityColor(issue.priority?.pk)"
                      label
                      class="px-1"
                      style="font-size: 10px; height: 18px"
                    >
                      {{ issue.priority?.name || '보통' }}
                    </v-chip>
                  </div>

                  <IssueDropDown :issue="issue" :is-delete="false" />
                </div>

                <!-- Card Title & Link -->
                <div class="mb-1">
                  <router-link
                    :to="{
                      name: '(업무) - 보기',
                      params: {
                        projId: issue.project?.slug || ($route.params.projId as string),
                        issueId: issue.pk,
                      },
                    }"
                    class="issue-subject-link text-decoration-none"
                  >
                    <span class="issue-id mr-1">#{{ issue.pk }}</span>
                    {{ issue.subject }}
                  </router-link>
                </div>

                <!-- Project & Meeting Tags -->
                <div class="d-flex flex-wrap gap-1 mb-2">
                  <span
                    v-if="!$route.params.projId && issue.project?.name"
                    class="badge bg-secondary-subtle text-secondary small"
                    style="font-size: 10px"
                  >
                    <v-icon icon="mdi-folder-outline" size="10" class="mr-1" />
                    {{ issue.project.name }}
                  </span>
                  <span
                    v-if="issue.meeting_desc"
                    class="badge bg-purple-subtle text-purple small"
                    style="font-size: 10px"
                  >
                    <v-icon icon="mdi-account-group" size="10" class="mr-1" />
                    {{ issue.meeting_desc.title }}
                  </span>
                </div>

                <!-- Progress Bar if in progress -->
                <div v-if="issue.done_ratio > 0" class="mb-2">
                  <div class="d-flex justify-content-between text-muted" style="font-size: 10px">
                    <span>진척도</span>
                    <span>{{ issue.done_ratio }}%</span>
                  </div>
                  <v-progress-linear
                    :model-value="issue.done_ratio"
                    height="3"
                    :color="issue.done_ratio === 100 ? 'success' : 'primary'"
                    rounded
                  />
                </div>

                <!-- Card Footer: Assignee & Due Date -->
                <div
                  class="d-flex align-items-center justify-content-between pt-1 border-top mt-1"
                  style="font-size: 11px"
                >
                  <span class="text-muted text-truncate" style="max-width: 140px">
                    <v-icon icon="mdi-account" size="12" class="mr-1 text-secondary" />
                    {{ issue.assigned_to?.username || '미지정' }}
                  </span>

                  <span
                    v-if="issue.due_date"
                    :class="{
                      'text-danger font-weight-bold': !issue.closed && diffDate(issue.due_date) < 0,
                      'text-muted': issue.closed || diffDate(issue.due_date) >= 0,
                    }"
                  >
                    <v-icon icon="mdi-calendar-clock" size="11" class="mr-1" />
                    {{ issue.due_date }}
                  </span>
                  <span v-else class="text-muted" style="font-size: 10px">-</span>
                </div>
              </div>
            </div>

            <!-- Empty column indicator -->
            <div
              v-if="!issuesByStatus.get(status.pk)?.length"
              class="empty-column-box text-center p-3 text-muted small"
            >
              업무가 없습니다
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.issue-kanban-wrapper {
  width: 100%;
}

.kanban-board-scroll {
  overflow-x: auto;
  padding-bottom: 12px;
}

.kanban-columns-container {
  display: flex;
  gap: 14px;
  min-width: 100%;
  align-items: flex-start;
}

.kanban-column {
  flex: 0 0 290px;
  max-width: 290px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  max-height: 80vh;
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.kanban-column.drag-over {
  border-color: #321fdb;
  background-color: #e8ecfc;
}

.kanban-column-header {
  padding: 10px 12px;
  border-top: 4px solid #ced4da;
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
  border-bottom: 1px solid #e9ecef;
}

.column-title {
  font-weight: 600;
  font-size: 13px;
  color: #3c4b64;
}

.kanban-cards-list {
  padding: 8px;
  overflow-y: auto;
  flex-grow: 1;
  min-height: 120px;
}

.kanban-card {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: grab;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.kanban-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
}

.kanban-card:active {
  cursor: grabbing;
}

.issue-subject-link {
  font-size: 13px;
  font-weight: 600;
  color: #2c3e50;
  display: block;
  line-height: 1.4;
  word-break: break-word;
}

.issue-subject-link:hover {
  color: #321fdb;
}

.issue-id {
  color: #6c757d;
  font-size: 12px;
}

.empty-column-box {
  border: 1px dashed #ced4da;
  border-radius: 6px;
  margin-top: 4px;
  background-color: rgba(255, 255, 255, 0.6);
}

.bg-purple-subtle {
  background-color: #f3e8ff;
}

.text-purple {
  color: #7e22ce;
}

:global(body.dark-theme .kanban-column),
:global(.dark-theme .kanban-column) {
  border-color: rgba(255, 255, 255, 0.05);
}

:global(body.dark-theme .kanban-column-header),
:global(.dark-theme .kanban-column-header) {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

:global(body.dark-theme .column-title),
:global(.dark-theme .column-title) {
  color: #f1f5f9;
}

:global(body.dark-theme .kanban-card),
:global(.dark-theme .kanban-card) {
  border-color: rgba(255, 255, 255, 0.1);
}

:global(body.dark-theme .kanban-card:hover),
:global(.dark-theme .kanban-card:hover) {
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}

:global(body.dark-theme .issue-subject-link),
:global(.dark-theme .issue-subject-link) {
  color: #f1f5f9;
}

:global(body.dark-theme .issue-subject-link:hover),
:global(.dark-theme .issue-subject-link:hover) {
  color: #60a5fa;
}

:global(body.dark-theme .empty-column-box),
:global(.dark-theme .empty-column-box) {
  border-color: rgba(255, 255, 255, 0.15);
  background-color: rgba(0, 0, 0, 0.2);
}

:global(body.dark-theme .kanban-column.drag-over),
:global(.dark-theme .kanban-column.drag-over) {
  background-color: rgba(50, 31, 219, 0.25) !important;
  border-color: #6366f1;
}

:global(body.dark-theme .bg-purple-subtle),
:global(.dark-theme .bg-purple-subtle) {
  background-color: rgba(126, 34, 206, 0.2);
}

:global(body.dark-theme .text-purple),
:global(.dark-theme .text-purple) {
  color: #c084fc;
}
</style>
