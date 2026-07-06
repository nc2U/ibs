<script setup lang="ts">
import { useRouter } from 'vue-router'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const router = useRouter()

const quickActions = [
  {
    icon: 'mdi-plus',
    label: '새 프로젝트',
    color: 'primary',
    routeName: '프로젝트 - 추가',
  },
  {
    icon: 'mdi-file-document-plus',
    label: '계약 등록',
    color: 'success',
    routeName: '계약 등록 조회',
  },
  {
    icon: 'mdi-bug-outline',
    label: '이슈 등록',
    color: 'warning',
    routeName: '업무',
  },
  {
    icon: 'mdi-calendar-plus',
    label: '일정 추가',
    color: 'info',
    routeName: '달력',
  },
  {
    icon: 'mdi-clipboard-plus',
    label: '업무 기록',
    color: 'secondary',
    routeName: '업무실행내역',
  },
  {
    icon: 'mdi-bell-plus',
    label: '공지 작성',
    color: 'error',
    routeName: '공지',
  },
]

const handleAction = (routeName: string) => {
  router.push({ name: routeName })
}
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon">
    <div class="quick-actions-widget">
      <v-row dense>
        <v-col v-for="action in quickActions" :key="action.label" cols="6">
          <v-btn
            variant="tonal"
            :color="action.color"
            class="quick-action-btn"
            block
            size="small"
            @click="handleAction(action.routeName)"
          >
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
