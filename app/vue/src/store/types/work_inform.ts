import type { SimpleProject, SimpleUser } from '@/store/types/work_project.ts'

export interface News {
  pk: number
  project: SimpleProject
  title: string
  summary: string
  content: string
  files: NewsFile[]
  author: SimpleUser
  comments: BaseComment[]
  is_new: boolean
  created: string
  updated: string
}

interface NewsFile {
  pk: number
  news: number
  file_name: string
  file: string
  file_type: string
  file_size: number
  description: string
  user: string | null
  created: string
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
