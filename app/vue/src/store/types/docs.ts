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
  issue_project: number | null
  proj_name?: string
  proj_sort?: '1' | '2' | '3' // 회사 / 부동산 프로젝트 / 기타
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
  creator?: SimpleUser
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
    | File[]
    | { pk: number; file: File }[]
  pk?: number
  issue_project: number | null
  proj_name?: string
  proj_sort?: '1' | '2' | '3'
  doc_type: number | null
  type_name?: string
  category: number | null
  cate_name?: string
  cate_color?: string
  lawsuit: number | null | string
  lawsuit_name?: string
  title: string
  execution_date: string | null
  content: string
  hit?: number
  scrape?: number
  my_scrape?: boolean
  ip?: string | null
  device: string
  is_secret: boolean
  password: string
  is_blind: boolean
  deleted?: string | null
  links?: Link[]
  newLinks?: Link[]
  files?: AFile[]
  newFiles?: File[]
  cngFiles?: { pk: number; file: File }[]
  creator?: SimpleUser
  created?: string
  updated?: string
  is_new?: boolean
  prev_pk?: number | null
  next_pk?: number | null
}

export interface Link {
  pk?: null | number
  docs: number | null
  link: string
  description: string
  hit?: number
  creator?: string
  created?: string
  del?: boolean
}

export interface AFile {
  pk: null | number
  docs?: number
  file?: string
  file_name?: string
  file_type?: string
  file_size?: number
  description?: string
  created?: string
  creator?: string
  hit?: number
  newFile?: Blob
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

export type DFile = {
  pk?: number
  docs: number | null
  file: File | string | null
  file_name?: string
  file_type?: string
  file_size?: number
  description: string
  hit?: number
  creator?: string
  created?: string
}

export interface PatchDocs {
  pk: number
  issue_project?: number
  doc_type?: number
  category?: number | null
  lawsuit?: number | null
  title?: string
  execution_date?: string | null
  content?: string
  hit?: number
  scrape?: number
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
  creator: string
  created: string
  deleted: string
}

// Official Letter (공문) Types
export interface OfficialLetter {
  pk?: number
  company: number | null
  company_name?: string
  document_number?: string
  title: string
  recipient_name: string
  recipient_address?: string
  recipient_contact?: string
  recipient_reference?: string
  sender_name: string
  sender_position?: string
  sender_department?: string
  content: string
  issue_date: string
  pdf_file?: string | null
  creator?: SimpleUser
  updator?: SimpleUser
  created?: string
  updated?: string
  prev_pk?: number | null
  next_pk?: number | null
}

export interface PatchLetter {
  pk: number
  title?: string
  recipient_name?: string
  recipient_address?: string
  recipient_contact?: string
  recipient_reference?: string
  sender_name?: string
  sender_position?: string
  sender_department?: string
  content?: string
  issue_date?: string
}
