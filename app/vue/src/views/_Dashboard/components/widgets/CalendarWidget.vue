<script setup lang="ts">
import { ref } from 'vue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

// Mock data - current date info
const today = new Date()
const currentYear = today.getFullYear()
const currentMonth = today.getMonth()
const currentDate = today.getDate()

// Mock events
const mockEvents = ref([
  { date: new Date(currentYear, currentMonth, currentDate), title: '정기 회의', color: 'primary' },
  {
    date: new Date(currentYear, currentMonth, currentDate + 2),
    title: '자재 검수',
    color: 'warning',
  },
  {
    date: new Date(currentYear, currentMonth, currentDate + 5),
    title: '착공식',
    color: 'success',
  },
])

const upcomingEvents = ref([
  { date: '오늘', title: '정기 회의', time: '10:00', color: 'primary' },
  { date: '내일', title: '현장 점검', time: '14:00', color: 'info' },
  { date: '모레', title: '자재 검수', time: '09:00', color: 'warning' },
])
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable>
    <div class="calendar-widget">
      <div class="calendar-header d-flex align-center justify-center mb-3">
        <v-btn icon variant="text" size="small">
          <v-icon icon="mdi-chevron-left" />
        </v-btn>
        <span class="text-body-1 font-weight-medium mx-2">
          {{ currentYear }}년 {{ currentMonth + 1 }}월
        </span>
        <v-btn icon variant="text" size="small">
          <v-icon icon="mdi-chevron-right" />
        </v-btn>
      </div>

      <div class="text-caption text-medium-emphasis mb-2">다가오는 일정</div>

      <v-list density="compact" class="pa-0 bg-transparent">
        <v-list-item
          v-for="(event, index) in upcomingEvents"
          :key="index"
          class="mb-1 rounded-sm list-item"
        >
          <template #prepend>
            <v-avatar :color="event.color" size="8" />
          </template>
          <v-list-item-title class="text-body-2">{{ event.title }}</v-list-item-title>
          <template #append>
            <span class="text-caption text-medium-emphasis">
              {{ event.date }} {{ event.time }}
            </span>
          </template>
        </v-list-item>
      </v-list>

      <v-btn variant="text" color="primary" size="small" class="mt-2" block :to="{ name: '달력' }">
        전체 일정 보기
        <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.calendar-widget {
  height: 100%;
}

.calendar-header {
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 8px;
  padding: 4px;
}

.list-item {
  background-color: #ffffff;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  transition: all 0.2s;
}

.list-item:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
}

body.dark-theme .list-item {
  background-color: rgba(255, 255, 255, 0.05);
  border-color: transparent;
}

body.dark-theme .list-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}
</style>
