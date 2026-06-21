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
  category: number | null
  category_desc: MeetingCategory | null
  status: '1' | '2' | '3' | '4'
  title: string
  agenda: string
  content: string
  decisions: string
  action_items: string
  meeting_date: string | null
  attendees: number[]
  attendees_desc: SimpleUser[]
  other_attendees: string
  files: MeetingFile[]
  issues: SimpleIssueInMeeting[]
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
  status?: string
  meeting_date?: string
  meeting_date__range?: string
  search?: string
  page?: number
}
