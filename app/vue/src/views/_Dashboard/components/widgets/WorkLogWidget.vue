<script setup lang="ts">
import { ref } from 'vue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

// Mock data
const mockWorkLogs = ref([
  {
    id: 1,
    date: '2024-01-15',
    project: '본관 건설',
    task: '기초 공사 감독',
    hours: 4,
    status: 'completed',
  },
  {
    id: 2,
    date: '2024-01-15',
    project: '본관 건설',
    task: '자재 검수',
    hours: 2,
    status: 'completed',
  },
  {
    id: 3,
    date: '2024-01-14',
    project: '별관 리모델링',
    task: '설계 검토 회의',
    hours: 3,
    status: 'completed',
  },
  {
    id: 4,
    date: '2024-01-14',
    project: '본관 건설',
    task: '안전 점검',
    hours: 1.5,
    status: 'completed',
  },
])

const totalHoursThisWeek = ref(32.5)
const targetHours = ref(40)
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable>
    <div class="work-log-widget">
      <div class="d-flex align-center justify-space-between mb-3">
        <div>
          <div class="text-h5 font-weight-bold">{{ totalHoursThisWeek }}h</div>
          <div class="text-caption text-medium-emphasis">이번 주 근무 시간</div>
        </div>
        <v-progress-circular
          :model-value="(totalHoursThisWeek / targetHours) * 100"
          :size="50"
          :width="4"
          color="primary"
        >
          <span class="text-caption"
            >{{ Math.round((totalHoursThisWeek / targetHours) * 100) }}%</span
          >
        </v-progress-circular>
      </div>

      <v-divider class="mb-2" />

      <div class="text-caption text-medium-emphasis mb-2">최근 기록</div>

      <v-list density="compact" class="pa-0">
        <v-list-item v-for="log in mockWorkLogs.slice(0, 4)" :key="log.id" class="px-0" lines="two">
          <v-list-item-title class="text-body-2">{{ log.task }}</v-list-item-title>
          <v-list-item-subtitle class="text-caption">
            {{ log.project }} · {{ log.date }}
          </v-list-item-subtitle>
          <template #append>
            <v-chip size="x-small" color="primary" variant="tonal">{{ log.hours }}h</v-chip>
          </template>
        </v-list-item>
      </v-list>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.work-log-widget {
  height: 100%;
}
</style>
