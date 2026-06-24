import type { SimpleProject } from '@/store/types/work_project.ts'

export interface ActLogEntry {
  pk: number
  sort: '1' | '2' | '3' | '4' | '5' | '6'
  project: SimpleProject
  issue: {
    pk: number
    tracker: string
    status: { pk: number; name: string; closed: boolean }
    subject: string
    description: string
  } | null
  comment: { pk: number; content: string } | null
  meeting: { pk: number; title: string; agenda: string } | null
  news: { pk: number; title: string; summary: string } | null
  document: { pk: number; title: string; description: string } | null
  post: { pk: number; forum: string; title: string; content: string } | null
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
