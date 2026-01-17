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

/* Style the widget component inside the grid item */
.dashboard-grid :deep(.vgl-item > *) {
  height: 100%;
  border-radius: 12px;
  border: 1px solid #e5e6eb;
  box-shadow:
    0 1px 2px 0 rgba(0, 0, 0, 0.03),
    0 1px 6px -1px rgba(0, 0, 0, 0.02),
    0 2px 4px 0 rgba(0, 0, 0, 0.02);
  transition:
    box-shadow 0.2s,
    border-color 0.2s,
    background-color 0.2s;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Ensures content respects border-radius */
}

.dashboard-grid :deep(.vgl-item:hover > *) {
  border-color: #c9cdd4;
  box-shadow:
    0 1px 2px -2px rgba(0, 0, 0, 0.16),
    0 3px 6px 0 rgba(0, 0, 0, 0.12),
    0 5px 12px 4px rgba(0, 0, 0, 0.09);
}

.dashboard-grid :deep(.vgl-item--placeholder) {
  border-radius: 12px; /* Consistent with widget radius */
}

/* Dark Theme Overrides */
body.dark-theme .dashboard-grid :deep(.vgl-item > *) {
  background-color: rgb(30 30 40 / 80%); /* Dark background for widgets */
  border-color: rgb(64 64 79); /* Subtle border color */
  color: #d1d1d1; /* Brighter text for dark mode */
  box-shadow: none; /* Often better to remove shadows on dark backgrounds */
}

body.dark-theme .dashboard-grid :deep(.vgl-item > * .text-body-2.font-weight-medium) {
  color: #d1d1d1; /* Explicitly bright white for header in dark mode */
}

body.dark-theme .dashboard-grid :deep(.vgl-item:hover > *) {
  border-color: #5a5a6f;
  background-color: rgb(42 42 53 / 80%);
}
</style>
