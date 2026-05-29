import type { SimpleUser, SimpleProject } from '@/store/types/work_project.ts'

export interface MeetingCategory {
  pk: number
  company: number
  project: number | null
  name: string
  color: string
  order: number
}

export interface Meeting {
  pk: number
  project: number | null
  project_desc: SimpleProject | null
  company: number
  category: number | null
  category_desc: MeetingCategory | null
  title: string
  content: string
  meeting_date: string | null
  attendees: number[]
  attendees_desc: SimpleUser[]
  other_attendees: string
  files: MeetingFile[]
  created: string
  updated: string
  creator: SimpleUser
  updater: SimpleUser | null
}

export interface MeetingFile {
  pk: number
  meeting: number
  file: string
  file_name: string
  file_type: string
  file_size: number
  description: string
  created: string
  creator: number | null
}

export interface MeetingFilter {
  project?: string
  category?: number
  meeting_date?: string
  meeting_date__range?: string
  search?: string
  page?: number
}
