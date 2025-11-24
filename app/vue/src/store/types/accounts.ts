export declare interface User {
  pk?: number
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  is_staff: boolean
  work_manager: boolean
  date_joined: string
  staffauth: StaffAuth | null
  profile: null | {
    pk: number
    name: string
    birth_date: string
    cell_phone: string
  }
  assigned_projects: {
    pk: number
    slug: string
    name: string
  }[]
  last_login: string | null
}

type Auth = '0' | '1' | '2'

export interface StaffAuth {
  pk?: number
  user?: number
  company: number | null
  is_staff: boolean
  is_project_staff: boolean
  allowed_projects: number[]
  assigned_project: number | null
  contract: Auth
  payment: Auth
  notice: Auth
  project_cash: Auth
  project_ledger: Auth
  project_docs: Auth
  project: Auth
  project_site: Auth
  company_cash: Auth
  company_ledger: Auth
  company_docs: Auth
  human_resource: Auth
  company_settings: Auth
  auth_manage: Auth
}

export type Profile = {
  [key: string]: undefined | number | number[] | null | string | File
  pk?: number | null
  user?: number | null
  name: string
  birth_date: string
  cell_phone: string
  image?: File | string | null
  like_posts?: number[]
  like_comments?: number[]
  blame_posts?: number[]
  blame_comments?: number[]
}

export interface Scrape {
  pk?: number
  user: number
  docs?: {
    pk: number
    doc_type: number
    type_name: string
    issue_project: number | null
    proj_sort: '1' | '2' | '3'
    title: string
  }
  post?: Post
  title: string
  created: string
}

interface Post {
  pk: number
  board: number
  board_name: string
  project: number | null
  title: string
}

export interface Todo {
  pk?: number
  user?: number
  title?: string
  completed?: boolean
  soft_deleted?: boolean
}
