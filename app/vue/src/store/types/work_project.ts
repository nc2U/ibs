import type { CodeValue, SimpleCategory, SimpleIssue } from '@/store/types/work_issue.ts'

// issue project
export interface SimpleUser {
  pk: number
  username: string
}

export interface SimpleMember {
  pk: number
  user: SimpleUser
  roles: { pk: number; name: string; inherited?: boolean }[]
  add_roles?: { pk: number; name: string }[]
  created: string
}

export interface SimpleProject {
  pk: number
  name: string
  slug: string
  visible: boolean
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
  total_estimated_hours?: number
  total_time_spent?: number
  family_tree: SimpleProject[]
  parent: number | null
  parent_visible: boolean
  sub_projects: IssueProject[]
  user?: string
  my_perms?: Permission
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
  file: boolean
  wiki: boolean
  repository: boolean
  forum: boolean
  calendar: boolean
  gantt: boolean
}

export interface Role {
  pk: number
  name: string
  assignable: boolean
  issue_visible: 'ALL' | 'PUB' | 'PRI'
  time_entry_visible: 'ALL' | 'PRI'
  user_visible: 'ALL' | 'PRJ'
  default_time_activity: number | null
  permission: Permission
  order: number
  user: number
  created: string
  updated: string
}

export interface Permission {
  pk?: number
  project_create: boolean
  project_update: boolean
  project_close: boolean
  project_delete: boolean
  project_public: boolean
  project_module: boolean
  project_member: boolean
  project_version: boolean
  project_create_sub: boolean
  project_pub_query: boolean
  project_save_query: boolean
  forum_read: boolean
  forum_create: boolean
  forum_update: boolean
  forum_own_update: boolean
  forum_delete: boolean
  forum_own_delete: boolean
  forum_watcher_read: boolean
  forum_watcher_create: boolean
  forum_watcher_delete: boolean
  forum_manage: boolean
  calendar_read: boolean
  document_read: boolean
  document_create: boolean
  document_update: boolean
  document_delete: boolean
  file_read: boolean
  file_manage: boolean
  gantt_read: boolean
  issue_read: boolean
  issue_create: boolean
  issue_update: boolean
  issue_own_update: boolean
  issue_copy: boolean
  issue_rel_manage: boolean
  issue_sub_manage: boolean
  issue_public: boolean
  issue_own_public: boolean
  issue_comment_create: boolean
  issue_comment_update: boolean
  issue_comment_own_update: boolean
  issue_private_comment_read: boolean
  issue_private_comment_set: boolean
  issue_delete: boolean
  issue_watcher_read: boolean
  issue_watcher_create: boolean
  issue_watcher_delete: boolean
  issue_import: boolean
  issue_category_manage: boolean
  news_read: boolean
  news_manage: boolean
  news_comment: boolean
  repo_changesets_read: boolean
  repo_read: boolean
  repo_commit_access: boolean
  repo_rel_issue_manage: boolean
  repo_manage: boolean
  time_read: boolean
  time_create: boolean
  time_update: boolean
  time_own_update: boolean
  time_pro_act_manage: boolean
  time_other_user_log: boolean
  time_entries_import: boolean
  wiki_read: boolean
  wiki_history_read: boolean
  wiki_page_export: boolean
  wiki_page_update: boolean
  wiki_page_rename: boolean
  wiki_page_delete: boolean
  wiki_attachment_delete: boolean
  wiki_watcher_read: boolean
  wiki_watcher_create: boolean
  wiki_watcher_delete: boolean
  wiki_page_project: boolean
  wiki_manage: boolean
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
  wiki_page_title: string
  issues?: SimpleIssue[]
  is_default?: boolean
}
