<script setup lang="ts">
import { ref } from 'vue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

// Mock data - 추후 실제 API 연결
const myIssues = ref([
  {
    pk: 1,
    subject: '기초 공사 일정 조정',
    tracker: '업무',
    status: '진행중',
    priority: '높음',
    project: '본관 건설',
    dueDate: '2024-01-20',
  },
  {
    pk: 2,
    subject: '자재 발주 확인',
    tracker: '업무',
    status: '신규',
    priority: '보통',
    project: '본관 건설',
    dueDate: '2024-01-18',
  },
  {
    pk: 3,
    subject: '안전 교육 일정 수립',
    tracker: '업무',
    status: '진행중',
    priority: '보통',
    project: '별관 리모델링',
    dueDate: '2024-01-22',
  },
])

const getStatusColor = (status: string) => {
  switch (status) {
    case '진행중':
      return 'warning'
    case '신규':
      return 'info'
    case '완료':
      return 'success'
    default:
      return 'grey'
  }
}

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case '높음':
      return 'error'
    case '보통':
      return 'warning'
    case '낮음':
      return 'success'
    default:
      return 'grey'
  }
}
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable>
    <div class="my-issue-widget">
      <v-table density="compact" hover>
        <thead>
          <tr>
            <th class="text-left">제목</th>
            <th class="text-center" style="width: 80px">상태</th>
            <th class="text-center" style="width: 80px">우선순위</th>
            <th class="text-right" style="width: 100px">기한</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="issue in myIssues" :key="issue.pk">
            <td>
              <div class="text-body-2">{{ issue.subject }}</div>
              <div class="text-caption text-medium-emphasis">{{ issue.project }}</div>
            </td>
            <td class="text-center">
              <v-chip :color="getStatusColor(issue.status)" size="x-small" variant="tonal">
                {{ issue.status }}
              </v-chip>
            </td>
            <td class="text-center">
              <v-chip :color="getPriorityColor(issue.priority)" size="x-small" variant="outlined">
                {{ issue.priority }}
              </v-chip>
            </td>
            <td class="text-right text-caption">{{ issue.dueDate }}</td>
          </tr>
        </tbody>
      </v-table>

      <v-btn variant="text" color="primary" size="small" class="mt-2" block>
        전체 업무 보기
        <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.my-issue-widget {
  height: 100%;
  overflow-y: auto;
}

.my-issue-widget :deep(.v-table) {
  background: transparent;
}
</style>
