export type TargetType = 'issue' | 'project' | 'calendar' | 'meeting'

export interface CustomQuery {
  pk: number
  name: string
  target_type: TargetType
  target_type_display: string
  project: number | null
  user: number
  username: string
  is_public: boolean
  filters: Record<string, any>
  column_names: string[]
  sort_criteria: [string, 'asc' | 'desc'][]
  group_by: string
  created: string
  updated: string
}
