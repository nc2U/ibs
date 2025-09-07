import type { SimpleProject, SimpleUser } from '@/store/types/work_project.ts'

export interface SimpleCategory {
  pk: number
  name: string
  assigned_to: SimpleUser | null
}

interface IssueInGantt {
  pk: number
  tracker: string
  subject: string
  start_date: string
  due_date: string | null
  done_ratio: number
}

export interface GanttProject {
  pk: number
  company: number
  name: string
  slug: string
  start_first: string
  due_last: string | null
  depth: number
  sub_projects: GanttProject[]
  issues: IssueInGantt[]
}

export interface Gantts {
  isProj: boolean
  depth: number
  name: string
  start: string
  due: string
  done_ratio?: number
  ganttBarConfig: {
    id: number
    label: string
    immobile: boolean
    html: string
    style: {
      background?: string
      color?: string
      borderRadius?: string
      fontSize?: string
    }
  }
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
  estimated_hours: number | null
  spent_times: number
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
  subject: string
  status: string
  assigned_to: SimpleUser
  start_date: string
  estimated_hours: string | null
  done_ratio: number
  closed: string | null
}

export interface Issue {
  pk: number
  project: SimpleProject
  tracker: { pk: number; name: string; description: string }
  status: { pk: number; name: string }
  priority: { pk: number; name: string }
  subject: string
  description: string
  category: number | null
  fixed_version: { pk: number; name: string } | null
  assigned_to: SimpleUser | null
  parent: number | null
  watchers: SimpleUser[]
  is_private: boolean
  estimated_hours: number | null
  start_date: string
  due_date: string | null
  done_ratio: number
  closed: string | null
  spent_time: number | null
  files: Array<IssueFile>
  sub_issues: SubIssue[]
  related_issues: IssueRelation[]
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
  parent?: number | string
  parent__subject?: string
  parent__isnull?: string
  page?: number
}

export interface IssueRelation {
  pk?: number
  issue: number
  issue_to: SubIssue | null
  relation_type:
    | 'relates'
    | 'duplicates'
    | 'duplicated'
    | 'blocks'
    | 'blocked'
    | 'precedes'
    | 'follows'
    | 'copied_to'
    | 'copied_from'
  type_display?: string
  delay: number | null
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

export interface TimeEntry {
  pk: number
  issue: {
    pk: number
    project: SimpleProject
    tracker: string
    status: { pk: number; name: string; closed: boolean }
    subject: string
    description: string
  }
  spent_on: string
  hours: string
  activity: { pk: number; name: string }
  comment: string
  created: string
  updated: string
  creator: SimpleUser
  total_hours: number
}

export interface TimeEntryFilter {
  ordering?: string
  project?: string
  project__search?: string
  project__exclude?: string
  spent_on?: string
  from_spent_on?: string
  to_spent_on?: string
  issue?: number | ''
  issue__keyword?: string
  creator?: number | ''
  creator__exclude?: number | ''
  author?: number | ''
  activity?: number | ''
  hours?: number
  comment?: string
  tracker?: number | ''
  parent?: number | ''
  status?: number | ''
  version?: number | ''
  version__exclude?: number | ''
  subject?: string
  project_status?: number | ''
  page?: number
}
