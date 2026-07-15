import type { SimpleCategory, SimpleIssue } from '@/store/types/work_issue.ts'

// issue project
export interface SimpleUser {
  pk: number
  username: string
}

export interface SimpleMember {
  pk: number
  user: SimpleUser
  roles: { pk: number; name: string; assignable: string; inherited?: boolean }[]
  add_roles?: { pk: number; name: string }[]
  created: string
}

export interface SimpleProject {
  pk: number
  name: string
  slug: string
  visible: boolean
}

export interface selectProject {
  pk: number
  module?: Module | null
  value: string
  label: string
  slug: string
  depth: number
  parent_visible: boolean
}

export interface MyRole {
  assignable: boolean
  issue_visible: 'ALL' | 'PUB' | 'PRI' | 'NOP'
  user_visible: 'ALL' | 'PRJ' | 'NOP'
}

export interface IssueProject {
  pk?: number
  company: number | null
  type: '1' | '2' | '3'
  name: string
  slug: string
  description: string
  is_public: boolean
  parent: number | null
  allowed_roles: { pk: number; name: string; inherited: boolean }[]
  status: '1' | '9'
  slack_notifications_enabled: boolean
  created?: string
  updated?: string
  creator?: string
  sub_projects: IssueProject[]
  depth: number
  module?: Module | null
  my_role?: MyRole
  my_perms?: string[]
  all_members: SimpleMember[]
  visible?: boolean
  parent_visible: boolean
  homepage: string | null
  is_inherit_members: boolean
  default_version: string | null
  trackers: { pk: number; name: string; description: string }[]
  ancestors: SimpleProject[]
  members: SimpleMember[]
  versions: SimpleVersion[]
  categories: SimpleCategory[]
  forums: number[]
}

export interface ProjectFilter {
  company?: number
  parent__isnull?: boolean
  parent?: string
  status?: '1' | '9'
  status__exclude?: '1' | '9'
  project?: string
  project__exclude?: string
  is_public?: '1' | '0'
  is_public__exclude?: '1' | '0'
  name?: string
  member?: number
  description?: string
}

export interface Module {
  pk?: number
  project: number
  issue: boolean
  time: boolean
  news: boolean
  document: boolean
  forum: boolean
  calendar: boolean
}

export interface Role {
  pk: number
  name: string
  assignable: boolean
  issue_visible: 'ALL' | 'PUB' | 'PRI' | 'NOP'
  issue_visible_desc: string
  user_visible: 'ALL' | 'PRJ' | 'NOP'
  user_visible_desc: string
  permissions: number[]
  order: number
  creator: number
  created: string
  updated: string
}

export interface Permission {
  pk: number
  module: 'project' | 'meeting' | 'issue' | 'news' | 'docs' | 'forum' | 'calendar'
  code: string
  name: string
  description: string
}

export interface Member {
  pk: number
  user: SimpleUser
  project: SimpleProject
  roles: { pk: number; name: string }[]
  created: string
}

export interface ProjectMember {
  pk: number
  user_id: number
  username: string
  roles: [
    {
      pk: number
      name: string
      assignable: boolean
      inherited: boolean
    },
  ]
  is_assignable: boolean
}

export interface SimpleVersion {
  pk: number
  name: string
  status: '1' | '2' | '3'
  status_desc: '진행' | '잠김' | '닫힘'
  sharing: '0' | '1' | '2' | '3' | '4'
  sharing_desc:
    | '공유 없음'
    | '하위 프로젝트'
    | '상위 및 하위 프로젝트'
    | '최상위 및 모든 하위 프로젝트'
    | '모든 프로젝트'
  is_default: boolean
  effective_date: string | null
  description: string
  proj_name: string
}

export interface Version {
  pk?: number
  project?: SimpleProject
  name: string
  status: '1' | '2' | '3'
  status_desc?: '진행' | '잠김' | '닫힘'
  sharing: '0' | '1' | '2' | '3' | '4'
  sharing_desc?:
    | '공유 없음'
    | '하위 프로젝트'
    | '상위 및 하위 프로젝트'
    | '최상위 및 모든 하위 프로젝트'
    | '모든 프로젝트'
  effective_date: string | null
  description: string
  is_default: boolean
  closed_num: number
  open_num: number
  total_num: number
  done_ratio: number
  issues?: SimpleIssue[]
}

export interface FormVersion {
  pk: number | null
  project: string
  name: string
  status: '1' | '2' | '3'
  sharing: '0' | '1' | '2' | '3' | '4'
  is_default: boolean
  effective_date: string | null
  description: string
}
