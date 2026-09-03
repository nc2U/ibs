import type { SimpleProject } from '@/store/types/work_project.ts'

export interface ActLogEntry {
  pk: number
  sort: '1' | '2' | '3' | '4' | '5' | '6'
  project: SimpleProject
  target_id: number | null
  parent_id: number | null
  title: string
  summary: string
  status_log: string
  act_date: string
  timestamp: string
  creator: { pk: number; username: string }
}

export interface ActLogEntryFilter {
  project?: string
  project__search?: string
  to_act_date?: string
  from_act_date?: string
  creator?: string
  sort?: Array<'1' | '2' | '3' | '4' | '5' | '6'>
  limit?: number
}

export interface IssueLogEntry {
  pk: number
  log_id: number
  issue: {
    pk: number
    project: SimpleProject
    tracker: string
    status: { pk: number; name: string; closed: boolean }
    subject: string
    description: string
  }
  action: string
  comment: {
    pk: number
    content: string
    is_private?: boolean
    is_blocked?: boolean
    creator: { pk: number; username: string }
  } | null
  details: string
  diff: string
  timestamp: string
  creator: {
    pk: number
    username: string
  }
}
