import type { SimpleProject, SimpleUser } from '@/store/types/work_project.ts'

export interface SimpleCategory {
  pk: number
  name: string
  assigned_to: SimpleUser | null
}

// issue
export interface SimpleIssue {
  pk: number
  project: SimpleProject
  subject: string
  status: number
  tracker: {
    pk: number
    name: string
    description: string
  }
  priority: number
  fixed_version: number | null
  category: number | null
  assigned_to: number | null
  watchers: SimpleUser[]
  expected_duration: string | null
  expected_duration_display: string
  done_ratio: number
  closed: string | null
}

export interface Tracker {
  pk: number
  name: string
  description: string
  is_in_roadmap: boolean
  default_status: number
  projects: SimpleProject[]
  order: number
}

export interface IssueCategory {
  pk: number
  project: SimpleProject
  name: string
  assigned_to: number | null
}

export interface IssueStatus {
  pk: number
  name: string
  description: string
  closed: boolean
  order: number
}

export interface CodeValue {
  pk: number
  name: string
  active: boolean
  default: boolean
  order: number | null
}

export interface IssueFile {
  pk: number
  file: string
  file_name: string
  file_type: string
  file_size: number
  description: string
  created: string
  creator: {
    pk: number
    username: string
  }
  cngFile?: File | null
  del?: boolean
  edit?: boolean
}

export interface SubIssue {
  pk: number
  project: SimpleProject
  subject: string
  tracker: {
    pk: number
    name: string
    description: string
  }
  status: string
  assigned_to: SimpleUser
  watchers: SimpleUser[]
  priority: number
  start_date: string
  due_date: string | null
  done_ratio: number
  closed: string | null // DateTimeField
}

export interface IssueRelation {
  pk?: number
  issue: SubIssue | null
  delay: number | null
}

export interface Issue {
  pk: number
  project: SimpleProject
  tracker: { pk: number; name: string; description: string }
  status: { pk: number; name: string; closed: boolean }
  priority: { pk: number; name: string }
  subject: string
  description: string
  category: number | null
  fixed_version: { pk: number; name: string; description: string } | null
  assigned_to: SimpleUser | null
  parent: number | null
  watchers: SimpleUser[]
  is_private: boolean
  expected_duration: string | null
  expected_duration_display: string
  start_date: string
  due_date: string | null
  meeting: number | null
  meeting_desc: { pk: number; title: string } | null
  done_ratio: number
  closed: string | null
  files: Array<IssueFile>
  sub_issues: SubIssue[]
  outgoing_relations: IssueRelation[] // Outgoing
  incoming_relation: IssueRelation | null // Incoming
  creator: SimpleUser
  updater: SimpleUser | null
  created: string
  updated: string
}

export interface IssueFilter {
  status__closed?: '' | '0' | '1' // '0: any' | '0: open' | '1: closed'
  status?: number | null
  status__exclude?: number | null
  project?: string
  project__search?: string
  project__exclude?: string
  tracker?: number | null
  tracker__exclude?: number | null
  author?: number | null
  author__exclude?: number | null
  assignee?: number | null
  assignee__exclude?: number | null
  assignee__isnull?: string
  version?: number | null
  version__exclude?: number | null
  version__isnull?: '0' | '1'
  id?: number | null
  id__gte?: number | null
  id__lte?: number | null
  id__between?: string // 'ID 범위 예: 10,20'
  id__any?: string // 'ID 포함목록 예: 1,2,3'
  parent__subject?: string
  parent__isnull?: string
  parent_issue?: number | null // 상위업무
  parent?: number | string // 하위업무
  follows_issue?: number | null // 선행업무
  precedes_issue?: number | null // 후속업무
  page?: number
}

export interface IssueComment {
  pk: number
  issue: {
    pk: number
    project: SimpleProject
    tracker: string
    status: string
    subject: string
    description: string
  }
  content: string
  is_private: boolean
  created: string
  updated: string
  creator: {
    pk: number
    username: string
  }
}
