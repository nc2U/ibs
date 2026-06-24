import type { CodeValue, SimpleCategory, SimpleIssue } from '@/store/types/work_issue.ts'

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

export interface getProject {
  pk: number
  value: string
  label: string
  slug: string
  status: '1' | '9'
  depth: number
  parent_visible: boolean
}

export interface IssueProject {
  pk?: number
  company: number | null
  sort: '1' | '2' | '3'
  name: string
  slug: string
  description: string
  homepage: string | null
  is_public: boolean
  module?: Module | null
  is_inherit_members: boolean
  allowed_roles: { pk: number; name: string; inherited: boolean }[]
  trackers: { pk: number; name: string; description: string }[]
  forums: number[]
  versions: Version[]
  default_version: string | null
  categories: SimpleCategory[]
  status: '1' | '9'
  depth: number
  all_members: SimpleMember[]
  members: SimpleMember[]
  activities: CodeValue[]
  visible?: boolean
  total_time_spent?: number
  family_tree: SimpleProject[]
  parent: number | null
  parent_visible: boolean
  sub_projects: IssueProject[]
  creator?: string
  my_perms?: string[]
  created?: string
  updated?: string
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
  user_visible: 'ALL' | 'PRJ' | 'NOP'
  permissions: number[]
  order: number
  creator: number
  created: string
  updated: string
}

export interface Permission {
  pk: number
  sort: 'project' | 'meeting' | 'issue' | 'news' | 'docs' | 'forum' | 'calendar'
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
  issues?: SimpleIssue[]
  is_default?: boolean
}
