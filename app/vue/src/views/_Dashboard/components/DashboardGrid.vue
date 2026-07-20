<script setup lang="ts">
import { computed, onMounted, nextTick, markRaw, ref, type Component } from 'vue'
import { GridLayout, type LayoutItem } from 'grid-layout-plus'
import { useDashboard, WIDGET_REGISTRY } from '@/store/pinia/dashboard.ts'
import type { Breakpoint } from '@/store/types/dashboard.ts'

// Widget components
import ProjectStatusWidget from './widgets/ProjectStatusWidget.vue'
import FinancialStatusWidget from './widgets/FinancialStatusWidget.vue'
import ContractStatusWidget from './widgets/ContractStatusWidget.vue'
import IssueTrackerWidget from './widgets/IssueTrackerWidget.vue'
import CalendarWidget from './widgets/CalendarWidget.vue'
import QuickActionsWidget from './widgets/QuickActionsWidget.vue'
import ActivityFeedWidget from './widgets/ActivityFeedWidget.vue'
import ContractLogWidget from './widgets/ContractLogWidget.vue'
import MainCarouselWidget from './widgets/MainCarouselWidget.vue'
import WiseWordWidget from './widgets/WiseWordWidget.vue'
import MyIssueWidget from './widgets/MyIssueWidget.vue'
import NoticeListWidget from './widgets/NoticeListWidget.vue'
import MeetingMinutesWidget from './widgets/MeetingMinutesWidget.vue'
import DocumentListWidget from './widgets/DocumentListWidget.vue'

const dashboardStore = useDashboard()

// Responsive configuration
const breakpoints: Record<Breakpoint, number> = { lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }
const cols: Record<Breakpoint, number> = { lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }

// Widget component mapping
const widgetComponents: Record<string, Component> = {
  'project-status': markRaw(ProjectStatusWidget),
  'financial-status': markRaw(FinancialStatusWidget),
  'contract-status': markRaw(ContractStatusWidget),
  'issue-tracker': markRaw(IssueTrackerWidget),
  calendar: markRaw(CalendarWidget),
  'quick-actions': markRaw(QuickActionsWidget),
  'activity-feed': markRaw(ActivityFeedWidget),
  'contract-log': markRaw(ContractLogWidget),
  'main-carousel': markRaw(MainCarouselWidget),
  'wise-word': markRaw(WiseWordWidget),
  'my-issue': markRaw(MyIssueWidget),
  'notice-list': markRaw(NoticeListWidget),
  'meeting-minutes': markRaw(MeetingMinutesWidget),
  'document-list': markRaw(DocumentListWidget),
}

// Computed layouts for grid-layout-plus (read-only — writes go through handleLayoutUpdated)
const gridLayouts = computed(() =>
  dashboardStore.activeLayouts.map(l => ({
    x: l.x,
    y: l.y,
    w: l.w,
    h: l.h,
    i: l.i,
    minW: l.minW,
    minH: l.minH,
  })),
)

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

// 초기 로드가 완료되기 전 @layout-updated 를 무시하기 위한 플래그
const isInitialized = ref(false)
// breakpoint 전환 중 자동 재배치로 인한 @layout-updated 를 무시하기 위한 플래그
let isBreakpointChanging = false
// 사용자가 마우스나 터치로 직접 드래그/리사이징 중인지 여부를 감지하는 플래그
const isUserInteracting = ref(false)

const handleDragStart = () => {
  isUserInteracting.value = true
}

const handleDragEnd = () => {
  // layout-updated가 최종적으로 동기화될 수 있도록 다음 틱에 인터랙션 플래그 해제
  nextTick(() => {
    isUserInteracting.value = false
  })
}

const handleResizeStart = () => {
  isUserInteracting.value = true
}

const handleResizeEnd = () => {
  nextTick(() => {
    isUserInteracting.value = false
  })
}

const handleBreakpointChange = (newBreakpoint: string) => {
  isBreakpointChanging = true
  dashboardStore.setCurrentBreakpoint(newBreakpoint as Breakpoint)
  // 라이브러리의 자동 재배치 이벤트가 처리된 후 플래그 해제
  nextTick(() => {
    isBreakpointChanging = false
  })
}

const handleLayoutUpdated = (newLayout: LayoutItem[]) => {
  // 초기 로드 완료 전 자동 재배치는 저장하지 않음
  if (!isInitialized.value) return
  // breakpoint 전환에 의한 자동 재배치는 저장하지 않음
  if (isBreakpointChanging) return
  // 사용자가 직접 드래그/리사이즈한 경우가 아니면 저장하지 않음 (반응형 자동 조정을 저장에서 제외)
  if (!isUserInteracting.value) return

  dashboardStore.updateLayout(
    newLayout.map(item => ({
      ...item,
      i: String(item.i),
      visible: true,
    })),
  )
}

onMounted(async () => {
  await dashboardStore.loadDashboardState()
  // 상태 로드 완료 후 다음 틱에 플래그 활성화
  // (라이브러리의 초기 렌더링 이벤트가 먼저 처리되도록 대기)
  nextTick(() => {
    isInitialized.value = true
  })
})
</script>

<template>
  <div class="dashboard-grid">
    <GridLayout
      :layout="gridLayouts"
      :responsive="true"
      :breakpoints="breakpoints"
      :cols="cols"
      :row-height="100"
      is-draggable
      is-resizable
      vertical-compact
      use-css-transforms
      :margin="[12, 12]"
      @breakpoint-change="handleBreakpointChange"
      @layout-updated="handleLayoutUpdated"
      @drag-start="handleDragStart"
      @drag-end="handleDragEnd"
      @resize-start="handleResizeStart"
      @resize-end="handleResizeEnd"
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
