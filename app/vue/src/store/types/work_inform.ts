import type { SimpleProject, SimpleUser } from '@/store/types/work_project.ts'

export interface News {
  pk: number
  project: SimpleProject
  title: string
  summary: string
  content: string
  is_important: boolean
  files: NewsFile[]
  author: SimpleUser
  comments: BaseComment[]
  is_new: boolean
  created: string
  updated: string
}

export interface NewsFile {
  pk: number
  news: number
  file_name: string
  file: string
  file_type: string
  file_size: number
  description: string
  creator: SimpleUser
  created: string
}

export interface BaseComment {
  pk?: number
  parent: number | null
  content: string
  creator?: SimpleUser
  created: string
  updated: string
}

export interface NewsComment extends BaseComment {
  news: number
}

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

