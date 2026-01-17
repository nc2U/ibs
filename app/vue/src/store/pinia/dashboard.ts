import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WidgetConfig, DashboardLayoutItem, DashboardState } from '@/store/types/dashboard.ts'

const STORAGE_KEY = 'ibs-dashboard-layout'
const CURRENT_VERSION = 1

// Widget Registry - 모든 위젯 정의
export const WIDGET_REGISTRY: WidgetConfig[] = [
  {
    id: 'main-carousel',
    type: 'main-carousel',
    title: 'Main Carousel',
    titleKo: '메인 캐러셀',
    icon: 'mdi-image-multiple',
    defaultLayout: { x: 0, y: 0, w: 12, h: 5 },
    minW: 6,
    minH: 3,
  },
  {
    id: 'wise-word',
    type: 'wise-word',
    title: 'Wise Word',
    titleKo: '명언',
    icon: 'mdi-format-quote-open',
    defaultLayout: { x: 0, y: 5, w: 12, h: 2 },
    minW: 4,
    minH: 2,
  },
  {
    id: 'project-status',
    type: 'project-status',
    title: 'Project Status',
    titleKo: '프로젝트 현황',
    icon: 'mdi-folder-outline',
    defaultLayout: { x: 0, y: 7, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'financial-status',
    type: 'financial-status',
    title: 'Financial Status',
    titleKo: '재무 현황',
    icon: 'mdi-currency-usd',
    defaultLayout: { x: 6, y: 7, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'contract-status',
    type: 'contract-status',
    title: 'Contract Status',
    titleKo: '계약 관리',
    icon: 'mdi-file-document-outline',
    defaultLayout: { x: 0, y: 11, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'issue-tracker',
    type: 'issue-tracker',
    title: 'Issue Tracker',
    titleKo: '이슈 트래커',
    icon: 'mdi-bug-outline',
    defaultLayout: { x: 6, y: 11, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'calendar',
    type: 'calendar',
    title: 'Calendar',
    titleKo: '캘린더',
    icon: 'mdi-calendar',
    defaultLayout: { x: 0, y: 15, w: 6, h: 5 },
    minW: 4,
    minH: 4,
  },
  {
    id: 'quick-actions',
    type: 'quick-actions',
    title: 'Quick Actions',
    titleKo: '빠른 작업',
    icon: 'mdi-lightning-bolt',
    defaultLayout: { x: 6, y: 15, w: 3, h: 3 },
    minW: 3,
    minH: 2,
  },
  {
    id: 'activity-feed',
    type: 'activity-feed',
    title: 'Activity Feed',
    titleKo: '활동 피드',
    icon: 'mdi-timeline',
    defaultLayout: { x: 9, y: 15, w: 3, h: 5 },
    minW: 3,
    minH: 3,
  },
  {
    id: 'work-log',
    type: 'work-log',
    title: 'Work Log',
    titleKo: '업무 로그',
    icon: 'mdi-clipboard-text-outline',
    defaultLayout: { x: 0, y: 20, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'my-issue',
    type: 'my-issue',
    title: 'My Issues',
    titleKo: '내 업무',
    icon: 'mdi-account-check-outline',
    defaultLayout: { x: 0, y: 7, w: 12, h: 4 },
    minW: 6,
    minH: 3,
  },
  {
    id: 'notice-list',
    type: 'notice-list',
    title: 'Notice List',
    titleKo: '공지 목록',
    icon: 'mdi-bulletin-board',
    defaultLayout: { x: 0, y: 11, w: 12, h: 4 },
    minW: 6,
    minH: 3,
  },
]

// 기본 표시 위젯
const DEFAULT_VISIBLE_WIDGETS = ['main-carousel', 'wise-word', 'my-issue', 'notice-list']

export const useDashboard = defineStore('dashboard', () => {
  // State
  const layouts = ref<DashboardLayoutItem[]>([])
  const visibleWidgets = ref<string[]>([...DEFAULT_VISIBLE_WIDGETS])

  // Getters
  const activeLayouts = computed(() => layouts.value.filter(l => l.visible))

  const availableWidgets = computed(() => {
    return WIDGET_REGISTRY.map(widget => ({
      ...widget,
      isVisible: visibleWidgets.value.includes(widget.id),
    }))
  })

  const getWidgetConfig = (id: string) => WIDGET_REGISTRY.find(w => w.id === id)

  // Actions
  const loadDashboardState = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const state: DashboardState = JSON.parse(saved)
        if (state.version === CURRENT_VERSION) {
          layouts.value = state.layouts
          visibleWidgets.value = state.visibleWidgets
          return
        }
      }
    } catch (e) {
      console.warn('Failed to load dashboard state:', e)
    }
    // 기본값으로 초기화
    resetToDefaults()
  }

  const saveDashboardState = () => {
    const state: DashboardState = {
      layouts: layouts.value,
      visibleWidgets: visibleWidgets.value,
      version: CURRENT_VERSION,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }

  const resetToDefaults = () => {
    visibleWidgets.value = [...DEFAULT_VISIBLE_WIDGETS]
    layouts.value = DEFAULT_VISIBLE_WIDGETS.map(id => {
      const widget = WIDGET_REGISTRY.find(w => w.id === id)!
      return {
        ...widget.defaultLayout,
        i: id,
        visible: true,
        minW: widget.minW,
        minH: widget.minH,
      }
    })
    saveDashboardState()
  }

  const toggleWidgetVisibility = (widgetId: string) => {
    const index = visibleWidgets.value.indexOf(widgetId)
    if (index > -1) {
      // 위젯 숨기기
      visibleWidgets.value.splice(index, 1)
      const layoutIndex = layouts.value.findIndex(l => l.i === widgetId)
      if (layoutIndex > -1) {
        layouts.value[layoutIndex].visible = false
      }
    } else {
      // 위젯 표시
      visibleWidgets.value.push(widgetId)
      const existingLayout = layouts.value.find(l => l.i === widgetId)
      if (existingLayout) {
        existingLayout.visible = true
      } else {
        // 새 레이아웃 추가
        const widget = WIDGET_REGISTRY.find(w => w.id === widgetId)
        if (widget) {
          layouts.value.push({
            ...widget.defaultLayout,
            i: widgetId,
            visible: true,
            minW: widget.minW,
            minH: widget.minH,
          })
        }
      }
    }
    saveDashboardState()
  }

  const updateLayout = (newLayouts: DashboardLayoutItem[]) => {
    // 레이아웃 업데이트 시 visible 상태 유지
    newLayouts.forEach(newLayout => {
      const existingLayout = layouts.value.find(l => l.i === newLayout.i)
      if (existingLayout) {
        existingLayout.x = newLayout.x
        existingLayout.y = newLayout.y
        existingLayout.w = newLayout.w
        existingLayout.h = newLayout.h
      }
    })
    saveDashboardState()
  }

  const removeWidget = (widgetId: string) => {
    toggleWidgetVisibility(widgetId)
  }

  return {
    // State
    layouts,
    visibleWidgets,

    // Getters
    activeLayouts,
    availableWidgets,
    getWidgetConfig,

    // Actions
    loadDashboardState,
    saveDashboardState,
    resetToDefaults,
    toggleWidgetVisibility,
    updateLayout,
    removeWidget,
  }
})
