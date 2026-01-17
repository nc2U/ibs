<script setup lang="ts">
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const quickActions = [
  { icon: 'mdi-plus', label: '새 프로젝트', color: 'primary', route: '/project/new' },
  { icon: 'mdi-file-document-plus', label: '계약 등록', color: 'success', route: '/contract/new' },
  { icon: 'mdi-bug-outline', label: '이슈 등록', color: 'warning', route: '/issue/new' },
  { icon: 'mdi-calendar-plus', label: '일정 추가', color: 'info', route: '/calendar/new' },
  { icon: 'mdi-clipboard-plus', label: '업무 기록', color: 'secondary', route: '/work-log/new' },
  { icon: 'mdi-bell-plus', label: '공지 작성', color: 'error', route: '/notice/new' },
]
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon">
    <div class="quick-actions-widget">
      <v-row dense>
        <v-col v-for="action in quickActions" :key="action.label" cols="6">
          <v-btn variant="tonal" :color="action.color" class="quick-action-btn" block size="small">
            <v-icon :icon="action.icon" size="small" class="mr-1" />
            <span class="text-caption">{{ action.label }}</span>
          </v-btn>
        </v-col>
      </v-row>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.quick-actions-widget {
  height: 100%;
}

.quick-action-btn {
  height: 36px;
  justify-content: flex-start;
}
</style>
