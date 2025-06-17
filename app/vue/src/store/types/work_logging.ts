import type { SimpleProject } from '@/store/types/work_project.ts'

export interface ActLogEntry {
  pk: number
  sort: '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'
  project: SimpleProject | null
  issue: {
    pk: number
    project: SimpleProject
    tracker: string
    status: { pk: number; name: string; closed: boolean }
    subject: string
    description: string
  } | null
  status_log: string
  comment: { pk: number; content: string } | null
  spent_time: { pk: number; hours: string; comment: '' } | null
  change_set: {
    repo: { pk: number; slug: string }
    sha: string
    message: string
  }
  // news: string
  // document: string
  // file: string
  // wiki: string
  // message: string
  act_date: string
  timestamp: string
  user: {
    pk: number
    username: string
  }
}

export interface ActLogEntryFilter {
  project?: string
  project__search?: string
  to_act_date?: string
  from_act_date?: string
  user?: string
  sort?: Array<'1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'>
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
    user: { pk: number; username: string }
  } | null
  details: string
  diff: string
  timestamp: string
  user: {
    pk: number
    username: string
  }
}
