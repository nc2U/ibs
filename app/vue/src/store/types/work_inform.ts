import type { SimpleProject, SimpleUser } from '@/store/types/work_project.ts'

export interface News {
  pk?: number
  project?: SimpleProject
  title: string
  summary: string
  content: string
  author?: SimpleUser
  created: string
  updated: string
}

export interface NewsComment {
  pk?: number
  news: number
  parent: number | null
  user?: SimpleUser
  created: string
  updated: string
}
