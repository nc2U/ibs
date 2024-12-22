export interface Group {
  pk: number | null
  name: string
  manager: number[]
}

export interface Board {
  pk: number | null
  group: number | null
  issue_project: number | null
  is_notice: boolean
  name: string
  order: number | null
  search_able: boolean
  manager: number[]
}

export interface PostCategory {
  pk: number | null
  board: number | null
  color: string | null
  name: string
  parent: number | null
  order: number | null
}

interface SimpleUser {
  pk: number
  username: string
}

export type Post = {
  [key: string]:
    | undefined
    | number
    | number[]
    | null
    | string
    | boolean
    | SimpleUser
    | PostLink[]
    | PostFile[]
    | Comment[]
  pk?: number
  board: number | null
  board_name?: string
  issue_project: number | null
  category: number | null
  cate_name?: string
  title: string
  content: string
  hit?: number
  like?: number
  my_like?: boolean
  scrape?: number
  my_scrape?: boolean
  blame?: number
  my_blame?: boolean
  ip: string | null
  device: string
  is_secret: boolean
  password: string
  is_hide_comment: boolean
  is_notice: boolean
  is_blind: boolean
  deleted?: string | null
  links?: PostLink[]
  files?: PostFile[]
  comments?: number[]
  user?: SimpleUser
  created?: string
  updated?: string
  is_new?: boolean
  prev_pk?: number | null
  next_pk?: number | null
}

export interface PostLink {
  pk: null | number
  post: number
  link: string
  hit: number
  del?: boolean
}

export interface PostFile {
  pk: null | number
  post?: number
  file?: string
  newFile?: Blob
  hit: number
  del?: boolean
  edit?: boolean
}

export type Attatches = {
  newLinks: PostLink[]
  newFiles?: (string | File)[]
  cngFiles?: {
    pk: number
    file: File
  }[]
}

export interface PatchPost {
  pk: number
  company?: number
  project?: number
  board?: number
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
  is_hide_comment?: boolean
  is_notice?: boolean
  is_blind?: boolean
  deleted?: string | null
}

export interface Comment {
  pk?: number
  post: {
    pk?: number
    company: number | null
    project: number | null
    board: number | null
  }
  content: string
  parent: number | null
  replies?: Comment[]
  like?: number
  my_like?: boolean
  blame?: number
  my_blame?: boolean
  ip?: string
  device?: string
  secret: boolean
  user?: SimpleUser
  created?: string
}

export interface TrashPost {
  pk: number
  board_name: string
  cate_name: string
  title: string
  content: string
  user: string
  created: string
  deleted: string
}
