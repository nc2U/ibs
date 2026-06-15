export type WidgetType =
  | 'project-status'
  | 'financial-status'
  | 'contract-status'
  | 'issue-tracker'
  | 'calendar'
  | 'quick-actions'
  | 'activity-feed'
  | 'work-log'
  | 'main-carousel'
  | 'wise-word'
  | 'my-issue'
  | 'notice-list'

export interface WidgetConfig {
  id: string
  type: WidgetType
  title: string
  titleKo: string
  icon: string
  defaultLayout: {
    x: number
    y: number
    w: number
    h: number
  }
  minW?: number
  minH?: number
}

export interface DashboardLayoutItem {
  x: number
  y: number
  w: number
  h: number
  i: string
  visible: boolean
  minW?: number
  minH?: number
}

export type Breakpoint = 'lg' | 'md' | 'sm' | 'xs' | 'xxs'

export interface DashboardState {
  layouts: Record<Breakpoint, DashboardLayoutItem[]>
  visibleWidgets: string[]
  version: number
}
