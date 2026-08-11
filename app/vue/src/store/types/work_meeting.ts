import type { SimpleUser, SimpleProject } from '@/store/types/work_project.ts'

export interface MeetingCategory {
  pk: number
  project: number
  name: string
  color: string
  order: number
}

export interface SimpleIssueInMeeting {
  pk: number
  project: string
  subject: string
  status: string
  assigned_to: SimpleUser | null
  closed: string | null
}

export interface Meeting {
  pk: number
  project: number
  project_desc: SimpleProject
  title: string
  category: number | null
  category_desc: MeetingCategory | null
  status: '1' | '2' | '3'
  status_display: '준비' | '종료' | '취소'
  is_confirmed: boolean
  agenda: string
  content: string
  decisions: string
  action_items: string
  meeting_date: string | null
  attendees: number[]
  attendees_desc: SimpleUser[]
  other_attendees: string
  files: MeetingFile[]
  links: MeetingLink[]
  issues: SimpleIssueInMeeting[]
  created: string
  updated: string
  creator: SimpleUser
  updater: SimpleUser | null
}

export interface MeetingLink {
  pk: number
  meeting: number
  link: string
  name: string
  description?: string
  hit: number
  created: string
  creator: SimpleUser | null
  del?: boolean
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
  category__exclude?: number
  status?: string
  status__exclude?: string
  is_confirmed?: boolean | ''
  creator?: number | null
  creator__exclude?: number | null
  attendees?: number | null
  attendees__exclude?: number | null
  meeting_date?: string
  meeting_date__range?: string
  meeting_date_after?: string
  meeting_date_before?: string
  created__range?: string
  created_after?: string
  created_before?: string
  search?: string
  project__my_project?: boolean
  project__bookmark?: boolean
  project_status?: string
  project_status__exclude?: string
  page?: number
}
