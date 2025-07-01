import type { SimpleProject, SimpleUser } from '@/store/types/work_project.ts'

export interface News {
  pk?: number
  project?: SimpleProject
  title: string
  summary: string
  content: string
  author?: SimpleUser
  comments: BaseComment[]
  is_new: boolean
  created: string
  updated: string
}

export interface BaseComment {
  pk?: number
  parent: number | null
  user?: SimpleUser
  created: string
  updated: string
}

export interface NewsComment extends BaseComment {
  news: number
}
