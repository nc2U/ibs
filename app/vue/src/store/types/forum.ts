export interface Forum {
  pk?: number | null
  project: number | null
  name: string
  description: string
  parent?: number | null
  search_able?: boolean
  manager?: number[]
  order?: number
  post_count?: number
  all_post_count?: number
  last_post?: {
    pk: number
    title: string
    creator: string
    created: string
  } | null
}

export interface PostCategory {
  pk?: number | null
  forum: number | null
  color: string | null
  name: string
  parent?: number | null
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
  forum: number | null
  forum_name?: string
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
  creator?: SimpleUser
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
  file_name: string
  file_size: number
  file_type: string
  newFile?: Blob
  hit: number
  del?: boolean
  edit?: boolean
}

export interface PatchPost {
  pk: number
  forum?: number
  category?: number | null
  // lawsuit?: number | null
  title?: string
  // execution_date?: string | null
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
    forum: number | null
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
  creator?: SimpleUser
  created?: string
}

export interface TrashPost {
  pk: number
  forum_name: string
  cate_name: string
  title: string
  content: string
  creator: string
  created: string
  deleted: string
}
