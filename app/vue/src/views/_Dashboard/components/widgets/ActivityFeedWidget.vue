<script setup lang="ts">
import { ref } from 'vue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

// Mock data - 추후 API 연결
const mockActivities = ref([
  {
    id: 1,
    user: '김철수',
    action: '이슈를 생성했습니다',
    target: '#101 외벽 균열 보수',
    time: '5분 전',
    icon: 'mdi-plus-circle',
    color: 'success',
  },
  {
    id: 2,
    user: '이영희',
    action: '계약서를 업로드했습니다',
    target: '전기 설비 계약',
    time: '15분 전',
    icon: 'mdi-file-upload',
    color: 'info',
  },
  {
    id: 3,
    user: '박민수',
    action: '이슈를 완료했습니다',
    target: '#98 배관 점검',
    time: '30분 전',
    icon: 'mdi-check-circle',
    color: 'success',
  },
  {
    id: 4,
    user: '정수진',
    action: '댓글을 남겼습니다',
    target: '#95 자재 발주',
    time: '1시간 전',
    icon: 'mdi-comment-text',
    color: 'primary',
  },
  {
    id: 5,
    user: '김철수',
    action: '일정을 추가했습니다',
    target: '착공식',
    time: '2시간 전',
    icon: 'mdi-calendar-plus',
    color: 'warning',
  },
])
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable>
    <div class="activity-feed-widget">
      <v-timeline density="compact" side="end" truncate-line="both">
        <v-timeline-item
          v-for="activity in mockActivities"
          :key="activity.id"
          :dot-color="activity.color"
          size="x-small"
        >
          <template #icon>
            <v-icon :icon="activity.icon" size="x-small" />
          </template>
          <div class="activity-item">
            <div class="text-body-2">
              <strong>{{ activity.user }}</strong>
              {{ activity.action }}
            </div>
            <div class="text-caption text-primary">{{ activity.target }}</div>
            <div class="text-caption text-medium-emphasis">{{ activity.time }}</div>
          </div>
        </v-timeline-item>
      </v-timeline>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.activity-feed-widget {
  height: 100%;
  overflow-y: auto;
}

.activity-item {
  padding-bottom: 8px;
}

.activity-feed-widget :deep(.v-timeline-item) {
  margin-bottom: 0;
}
</style>
