export interface DocType {
  pk: number | null
  type: '1' | '2'
  name: string
}

export interface Category {
  pk: number | null
  doc_type: number
  color: string | null
  name: string
  parent: number | null
  order: number | null
  active: boolean
  default: boolean
}

interface SimpleUser {
  pk: number
  username: string
}

export interface SuitCase {
  pk: number | null
  company: number | null
  project: number | null
  proj_name?: string
  sort: '' | '1' | '2' | '3' | '4' | '5'
  sort_desc?: string
  level: '' | '0' | '1' | '2' | '3'
  level_desc?: string
  related_case: number | null
  related_case_name?: string
  court: string
  court_desc?: string
  other_agency: string
  case_number: string
  case_name: string
  __str__?: string
  plaintiff: string
  plaintiff_attorney: string
  plaintiff_case_price: number | null
  defendant: string
  defendant_attorney: string
  defendant_case_price: number | null
  related_debtor: string
  case_start_date: string | null
  case_end_date: string | null
  summary: string
  user?: SimpleUser
  links?: Array<{ pk: number; category: { name: string; color?: string }; link: string }>
  files?: Array<{ pk: number; category: { name: string; color?: string }; file: string }>
  created?: string
  prev_pk?: number | null
  next_pk?: number | null
}

export interface SimpleSuitCase {
  pk: number | null
  __str__: string
}

export type Docs = {
  [key: string]:
    | undefined
    | number
    | number[]
    | null
    | string
    | boolean
    | SimpleUser
    | Link[]
    | AFile[]
  pk?: number
  issue_project: number | null
  proj_name?: string
  doc_type: number | null
  type_name?: string
  category: number | null
  cate_name?: string
  lawsuit: number | null | string
  lawsuit_name?: string
  title: string
  execution_date: string | null
  content: string
  hit?: number
  scrape?: number
  my_scrape?: boolean
  ip: string | null
  device: string
  is_secret: boolean
  password: string
  is_blind: boolean
  deleted?: string | null
  links?: Link[]
  files?: AFile[]
  user?: SimpleUser
  created?: string
  updated?: string
  is_new?: boolean
  prev_pk?: number | null
  next_pk?: number | null
}

export interface Link {
  pk: null | number
  docs: number
  link: string
  hit: number
  del?: boolean
}

export interface AFile {
  pk: null | number
  docs?: number
  file?: string
  newFile?: Blob
  hit: number
  del?: boolean
  edit?: boolean
}

export type Attatches = {
  newLinks: Link[]
  newFiles?: (string | File)[]
  cngFiles?: {
    pk: number
    file: File
  }[]
}

export interface PatchDocs {
  pk: number
  company?: number
  project?: number
  doc_type?: number
  category?: number | null
  lawsuit?: number | null
  title?: string
  execution_date?: string | null
  content?: string
  hit?: number
  like?: number
  scrape?: number
  blame?: number
  is_secret?: boolean
  password?: string
  is_blind?: boolean
  deleted?: string | null
}

export interface TrashDocs {
  pk: number
  type_name: string
  cate_name: string
  title: string
  content: string
  user: string
  created: string
  deleted: string
}
