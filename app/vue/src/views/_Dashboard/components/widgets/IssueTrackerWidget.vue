<script setup lang="ts">
import { ref, computed } from 'vue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

// Mock data
const mockIssues = ref({
  total: 45,
  open: 12,
  inProgress: 8,
  resolved: 20,
  closed: 5,
})

const issueCategories = computed(() => [
  { label: '신규', value: mockIssues.value.open, color: 'error' },
  { label: '진행중', value: mockIssues.value.inProgress, color: 'warning' },
  { label: '해결됨', value: mockIssues.value.resolved, color: 'success' },
  { label: '종료', value: mockIssues.value.closed, color: 'grey' },
])

const recentIssues = ref([
  { id: 101, subject: '외벽 균열 보수 필요', priority: 'high', assignee: '김철수' },
  { id: 102, subject: '전기 배선 점검', priority: 'medium', assignee: '이영희' },
  { id: 103, subject: '자재 배송 지연', priority: 'low', assignee: '박민수' },
])

const priorityColor = (priority: string) => {
  switch (priority) {
    case 'high':
      return 'error'
    case 'medium':
      return 'warning'
    default:
      return 'info'
  }
}
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable>
    <div class="issue-tracker-widget">
      <v-row dense class="mb-3">
        <v-col v-for="cat in issueCategories" :key="cat.label" cols="3">
          <div class="text-center">
            <div class="text-h6 font-weight-bold" :class="`text-${cat.color}`">
              {{ cat.value }}
            </div>
            <div class="text-caption text-medium-emphasis">{{ cat.label }}</div>
          </div>
        </v-col>
      </v-row>

      <v-divider class="mb-2" />

      <div class="text-caption text-medium-emphasis mb-2">최근 이슈</div>

      <v-list density="compact" class="pa-0">
        <v-list-item v-for="issue in recentIssues" :key="issue.id" class="px-0" lines="one">
          <template #prepend>
            <v-avatar :color="priorityColor(issue.priority)" size="8" class="mr-2" />
          </template>
          <v-list-item-title class="text-body-2">
            #{{ issue.id }} {{ issue.subject }}
          </v-list-item-title>
          <template #append>
            <span class="text-caption text-medium-emphasis">{{ issue.assignee }}</span>
          </template>
        </v-list-item>
      </v-list>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.issue-tracker-widget {
  height: 100%;
}
</style>
