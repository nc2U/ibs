<script setup lang="ts">
import { ref } from 'vue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

// Mock data
const mockData = ref({
  totalProjects: 12,
  activeProjects: 8,
  completedProjects: 3,
  delayedProjects: 1,
  budgetExecution: 67,
})

const statusItems = [
  { label: '진행중', value: 8, color: 'primary', icon: 'mdi-play-circle' },
  { label: '완료', value: 3, color: 'success', icon: 'mdi-check-circle' },
  { label: '지연', value: 1, color: 'error', icon: 'mdi-alert-circle' },
]
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable>
    <div class="project-status-widget">
      <div class="text-center mb-4">
        <div class="text-h3 font-weight-bold text-primary">{{ mockData.totalProjects }}</div>
        <div class="text-caption text-medium-emphasis">전체 프로젝트</div>
      </div>

      <v-row dense>
        <v-col v-for="item in statusItems" :key="item.label" cols="4">
          <v-card variant="tonal" :color="item.color" class="text-center pa-2">
            <v-icon :icon="item.icon" size="small" />
            <div class="text-h6 font-weight-bold">{{ item.value }}</div>
            <div class="text-caption">{{ item.label }}</div>
          </v-card>
        </v-col>
      </v-row>

      <v-divider class="my-3" />

      <div class="d-flex align-center justify-space-between mb-1">
        <span class="text-body-2">예산 집행률</span>
        <span class="text-body-2 font-weight-bold">{{ mockData.budgetExecution }}%</span>
      </div>
      <v-progress-linear
        :model-value="mockData.budgetExecution"
        color="primary"
        height="8"
        rounded
      />
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.project-status-widget {
  height: 100%;
}
</style>
