import api from '@/api'
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { errorHandle } from '@/utils/helper.ts'
import type {
  WidgetConfig,
  DashboardLayoutItem,
  DashboardState,
  Breakpoint,
} from '@/store/types/dashboard.ts'

const STORAGE_KEY = 'ibs-dashboard-layout'
const CURRENT_VERSION = 1

const BREAKPOINTS: Breakpoint[] = ['lg', 'md', 'sm', 'xs', 'xxs']

// Widget Registry - 모든 위젯 정의
export const WIDGET_REGISTRY: WidgetConfig[] = [
  {
    id: 'main-carousel',
    type: 'main-carousel',
    title: 'Main Carousel',
    titleKo: '메인 슬라이드',
    icon: 'mdi-image-multiple',
    defaultLayout: { x: 0, y: 0, w: 12, h: 5 },
    minW: 6,
    minH: 3,
  },
  {
    id: 'wise-word',
    type: 'wise-word',
    title: 'Wise Word',
    titleKo: '오늘의 한마디',
    icon: 'mdi-format-quote-open',
    defaultLayout: { x: 0, y: 5, w: 12, h: 2 },
    minW: 4,
    minH: 2,
  },
  {
    id: 'notice-list',
    type: 'notice-list',
    title: 'Notice List',
    titleKo: '공지 목록',
    icon: 'mdi-bulletin-board',
    defaultLayout: { x: 0, y: 7, w: 6, h: 4 },
    minW: 6,
    minH: 3,
  },
  {
    id: 'my-issue',
    type: 'my-issue',
    title: 'My Issues',
    titleKo: '내 업무',
    icon: 'mdi-account-check-outline',
    defaultLayout: { x: 6, y: 7, w: 6, h: 4 },
    minW: 6,
    minH: 3,
  },
  {
    id: 'meeting-minutes',
    type: 'meeting-minutes',
    title: 'Meeting Minutes',
    titleKo: '회의록',
    icon: 'mdi-account-group-outline',
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
    id: 'project-status',
    type: 'project-status',
    title: 'Project Status',
    titleKo: '프로젝트 보드',
    icon: 'mdi-folder-outline',
    defaultLayout: { x: 0, y: 15, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'contract-status',
    type: 'contract-status',
    title: 'Contract Status',
    titleKo: '프로젝트별 계약 현황',
    icon: 'mdi-file-document-outline',
    defaultLayout: { x: 6, y: 15, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'calendar',
    type: 'calendar',
    title: 'Calendar',
    titleKo: '캘린더',
    icon: 'mdi-calendar',
    defaultLayout: { x: 0, y: 19, w: 12, h: 5 },
    minW: 6,
    minH: 4,
  },
  {
    id: 'quick-actions',
    type: 'quick-actions',
    title: 'Quick Actions',
    titleKo: '빠른 작업',
    icon: 'mdi-lightning-bolt',
    defaultLayout: { x: 6, y: 19, w: 3, h: 4 },
    minW: 3,
    minH: 2,
  },
  {
    id: 'activity-feed',
    type: 'activity-feed',
    title: 'Activity Feed',
    titleKo: '활동 피드',
    icon: 'mdi-timeline',
    defaultLayout: { x: 9, y: 19, w: 3, h: 4 },
    minW: 3,
    minH: 3,
  },
  {
    id: 'contract-log',
    type: 'contract-log',
    title: 'Recent Contracts',
    titleKo: '최근 등록 계약',
    icon: 'mdi-file-sign',
    defaultLayout: { x: 0, y: 24, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'document-list',
    type: 'document-list',
    title: 'Document List',
    titleKo: '최근 문서 목록',
    icon: 'mdi-file-document-multiple-outline',
    defaultLayout: { x: 0, y: 28, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
  {
    id: 'financial-status',
    type: 'financial-status',
    title: 'Financial Status',
    titleKo: '재무 현황',
    icon: 'mdi-currency-usd',
    defaultLayout: { x: 6, y: 24, w: 6, h: 4 },
    minW: 4,
    minH: 3,
  },
]

// 기본 표시 위젯
const DEFAULT_VISIBLE_WIDGETS = [
  'wise-word',
  'notice-list',
  'my-issue',
  'meeting-minutes',
  'issue-tracker',
]

// 기본 레이아웃 빌더 — 저장 상태가 없을 때 즉시 렌더링할 초기값 생성
const buildDefaultLayouts = (): Record<Breakpoint, DashboardLayoutItem[]> => {
  const result = {} as Record<Breakpoint, DashboardLayoutItem[]>
  BREAKPOINTS.forEach(bp => {
    result[bp] = DEFAULT_VISIBLE_WIDGETS.map(id => {
      const widget = WIDGET_REGISTRY.find(w => w.id === id)!
      return {
        ...widget.defaultLayout,
        i: id,
        visible: true,
        minW: widget.minW,
        minH: widget.minH,
      }
    })
    result[bp].sort((a, b) => {
      const indexA = WIDGET_REGISTRY.findIndex(w => w.id === a.i)
      const indexB = WIDGET_REGISTRY.findIndex(w => w.id === b.i)
      return indexA - indexB
    })
  })
  return result
}

export const useDashboard = defineStore('dashboard', () => {
  // State — layouts를 기본값으로 초기화해 첫 로그인 시에도 위젯이 즉시 표시되게 함
  const layouts = ref<Record<Breakpoint, DashboardLayoutItem[]>>(buildDefaultLayouts())
  const visibleWidgets = ref<string[]>([...DEFAULT_VISIBLE_WIDGETS])
  const currentBreakpoint = ref<Breakpoint>('lg')
  const configPk = ref<number | null>(null)
  const isSyncing = ref(false)

  // Debounce timer for API sync
  let syncTimer: ReturnType<typeof setTimeout> | null = null

  // Getters
  const activeLayouts = computed(() =>
    layouts.value[currentBreakpoint.value].filter(l => l.visible),
  )

  const availableWidgets = computed(() => {
    return WIDGET_REGISTRY.map(widget => ({
      ...widget,
      isVisible: visibleWidgets.value.includes(widget.id),
    }))
  })

  const getWidgetConfig = (id: string) => WIDGET_REGISTRY.find(w => w.id === id)

  // Actions
  const loadDashboardState = async () => {
    // 1. Try DB first
    const dbLoaded = await fetchDashboardFromDB()
    if (dbLoaded) return

    // 2. Fallback to LocalStorage
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)

        // Migration logic: old format (array) to new format (record)
        if (Array.isArray(parsed.layouts)) {
          console.info('Migrating dashboard layout from old format...')
          resetToDefaults(false) // Don't save to DB yet
          layouts.value.lg = parsed.layouts // Preserve old layout as 'lg'
          visibleWidgets.value = parsed.visibleWidgets
          saveDashboardState()
          return
        }

        const state: DashboardState = parsed
        if (state.version === CURRENT_VERSION) {
          layouts.value = state.layouts
          visibleWidgets.value = state.visibleWidgets
          return
        }
      }
    } catch (e) {
      console.warn('Failed to load dashboard state from LocalStorage:', e)
    }

    // 3. Last resort: Defaults
    resetToDefaults()
  }

  const fetchDashboardFromDB = async () => {
    try {
      const res = await api.get('/user-widget-config/')
      if (res.data.results && res.data.results.length > 0) {
        const config = res.data.results[0]
        configPk.value = config.pk
        layouts.value = config.layouts
        visibleWidgets.value = config.visible_widgets
        // Update LocalStorage to keep in sync
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({
            layouts: config.layouts,
            visibleWidgets: config.visible_widgets,
            version: config.version,
          }),
        )
        return true
      }
    } catch (e) {
      console.warn('Failed to fetch dashboard config from DB:', e)
    }
    return false
  }

  const saveDashboardState = (syncToDB = true) => {
    // 1. Immediate save to LocalStorage
    const state: DashboardState = {
      layouts: layouts.value,
      visibleWidgets: visibleWidgets.value,
      version: CURRENT_VERSION,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))

    // 2. Debounced sync to DB
    if (syncToDB) {
      if (syncTimer) clearTimeout(syncTimer)
      syncTimer = setTimeout(async () => {
        await syncDashboardToDB()
      }, 2000) // 2 second debounce
    }
  }

  const syncDashboardToDB = async () => {
    isSyncing.value = true
    const payload = {
      layouts: layouts.value,
      visible_widgets: visibleWidgets.value,
      version: CURRENT_VERSION,
    }

    try {
      if (configPk.value) {
        await api.put(`/user-widget-config/${configPk.value}/`, payload)
      } else {
        const res = await api.post('/user-widget-config/', payload)
        configPk.value = res.data.pk
      }
    } catch (e: any) {
      errorHandle(e.response?.data)
    } finally {
      isSyncing.value = false
    }
  }

  const resetToDefaults = (syncToDB = true) => {
    visibleWidgets.value = [...DEFAULT_VISIBLE_WIDGETS]
    const defaultLayouts = buildDefaultLayouts()
    BREAKPOINTS.forEach(bp => {
      layouts.value[bp] = defaultLayouts[bp]
    })
    saveDashboardState(syncToDB)
  }

  const toggleWidgetVisibility = (widgetId: string) => {
    const index = visibleWidgets.value.indexOf(widgetId)
    if (index > -1) {
      // 위젯 숨기기
      visibleWidgets.value.splice(index, 1)
      BREAKPOINTS.forEach(bp => {
        const layoutIndex = layouts.value[bp].findIndex(l => l.i === widgetId)
        if (layoutIndex > -1) {
          layouts.value[bp][layoutIndex].visible = false
        }
      })
    } else {
      // 위젯 표시
      visibleWidgets.value.push(widgetId)
      BREAKPOINTS.forEach(bp => {
        const existingLayout = layouts.value[bp].find(l => l.i === widgetId)
        if (existingLayout) {
          existingLayout.visible = true
        } else {
          // 새 레이아웃 추가
          const widget = WIDGET_REGISTRY.find(w => w.id === widgetId)
          if (widget) {
            layouts.value[bp].push({
              ...widget.defaultLayout,
              i: widgetId,
              visible: true,
              minW: widget.minW,
              minH: widget.minH,
            })
          }
        }

        // 레이아웃 배열을 WIDGET_REGISTRY 순서대로 정렬하여 시각적 위계 유지
        layouts.value[bp].sort((a, b) => {
          const indexA = WIDGET_REGISTRY.findIndex(w => w.id === a.i)
          const indexB = WIDGET_REGISTRY.findIndex(w => w.id === b.i)
          return indexA - indexB
        })
      })
    }
    saveDashboardState()
  }

  const updateLayout = (newLayouts: DashboardLayoutItem[], breakpoint?: Breakpoint) => {
    const bp = breakpoint || currentBreakpoint.value
    // 레이아웃 업데이트 시 visible 상태 유지
    newLayouts.forEach(newLayout => {
      const existingLayout = layouts.value[bp].find(l => l.i === newLayout.i)
      if (existingLayout) {
        existingLayout.x = newLayout.x
        existingLayout.y = newLayout.y
        existingLayout.w = newLayout.w
        existingLayout.h = newLayout.h
      }
    })
    saveDashboardState()
  }

  const setCurrentBreakpoint = (bp: Breakpoint) => {
    currentBreakpoint.value = bp
  }

  const removeWidget = (widgetId: string) => {
    toggleWidgetVisibility(widgetId)
  }

  return {
    // State
    layouts,
    visibleWidgets,
    currentBreakpoint,
    isSyncing,

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
    setCurrentBreakpoint,
    removeWidget,
  }
})
