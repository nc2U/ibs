<script setup lang="ts">
import { computed, onMounted, watch, markRaw, type Component } from 'vue'
import { GridLayout, type LayoutItem } from 'grid-layout-plus'
import { useDashboard, WIDGET_REGISTRY } from '@/store/pinia/dashboard.ts'

// Widget components
import ProjectStatusWidget from './widgets/ProjectStatusWidget.vue'
import FinancialStatusWidget from './widgets/FinancialStatusWidget.vue'
import ContractStatusWidget from './widgets/ContractStatusWidget.vue'
import IssueTrackerWidget from './widgets/IssueTrackerWidget.vue'
import CalendarWidget from './widgets/CalendarWidget.vue'
import QuickActionsWidget from './widgets/QuickActionsWidget.vue'
import ActivityFeedWidget from './widgets/ActivityFeedWidget.vue'
import WorkLogWidget from './widgets/WorkLogWidget.vue'
import MainCarouselWidget from './widgets/MainCarouselWidget.vue'
import WiseWordWidget from './widgets/WiseWordWidget.vue'
import MyIssueWidget from './widgets/MyIssueWidget.vue'
import NoticeListWidget from './widgets/NoticeListWidget.vue'

const dashboardStore = useDashboard()

// Widget component mapping
const widgetComponents: Record<string, Component> = {
  'project-status': markRaw(ProjectStatusWidget),
  'financial-status': markRaw(FinancialStatusWidget),
  'contract-status': markRaw(ContractStatusWidget),
  'issue-tracker': markRaw(IssueTrackerWidget),
  calendar: markRaw(CalendarWidget),
  'quick-actions': markRaw(QuickActionsWidget),
  'activity-feed': markRaw(ActivityFeedWidget),
  'work-log': markRaw(WorkLogWidget),
  'main-carousel': markRaw(MainCarouselWidget),
  'wise-word': markRaw(WiseWordWidget),
  'my-issue': markRaw(MyIssueWidget),
  'notice-list': markRaw(NoticeListWidget),
}

// Computed layouts for grid-layout-plus (needs a mutable array)
const gridLayouts = computed({
  get: () =>
    dashboardStore.activeLayouts.map(l => ({
      x: l.x,
      y: l.y,
      w: l.w,
      h: l.h,
      i: l.i,
      minW: l.minW,
      minH: l.minH,
    })),
  set: (val: LayoutItem[]) => {
    dashboardStore.updateLayout(
      val.map(item => ({
        ...item,
        i: String(item.i),
        visible: true,
      })),
    )
  },
})

const getWidgetComponent = (widgetId: string) => {
  return widgetComponents[widgetId]
}

const getWidgetTitle = (widgetId: string) => {
  const widget = WIDGET_REGISTRY.find(w => w.id === widgetId)
  return widget?.titleKo || widget?.title || widgetId
}

const getWidgetIcon = (widgetId: string) => {
  const widget = WIDGET_REGISTRY.find(w => w.id === widgetId)
  return widget?.icon
}

const handleLayoutUpdated = (newLayout: LayoutItem[]) => {
  dashboardStore.updateLayout(
    newLayout.map(item => ({
      ...item,
      i: String(item.i),
      visible: true,
    })),
  )
}

onMounted(() => {
  dashboardStore.loadDashboardState()
})

watch(
  () => dashboardStore.activeLayouts,
  () => {
    // Layout changed, handled by computed setter
  },
  { deep: true },
)
</script>

<template>
  <div class="dashboard-grid">
    <GridLayout
      v-model:layout="gridLayouts"
      :col-num="12"
      :row-height="100"
      is-draggable
      is-resizable
      vertical-compact
      use-css-transforms
      :margin="[12, 12]"
      @layout-updated="handleLayoutUpdated"
    >
      <template #item="{ item }">
        <component
          :is="getWidgetComponent(String(item.i))"
          :widget-id="String(item.i)"
          :title="getWidgetTitle(String(item.i))"
          :icon="getWidgetIcon(String(item.i))"
        />
      </template>
    </GridLayout>
  </div>
</template>

<style scoped>
.dashboard-grid {
  min-height: 400px;
}

.dashboard-grid :deep(.vgl-layout) {
  --vgl-placeholder-bg: rgba(var(--v-theme-primary), 0.2);
}

.dashboard-grid :deep(.vgl-item) {
  transition: none;
}

.dashboard-grid :deep(.vgl-item--placeholder) {
  border-radius: 8px;
}
</style>
