import type { SimpleProject, SimpleUser } from '@/store/types/work_project.ts'

export interface News {
  pk?: number
  project?: SimpleProject
  title: string
  summary: string
  description: string
  author?: SimpleUser
  created: string
}
