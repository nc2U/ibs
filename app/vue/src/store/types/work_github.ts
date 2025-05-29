export interface Repository {
  pk?: number
  project: number
  is_default: boolean
  slug: string
  local_path: string
  is_report: boolean
}

export interface Commit {
  pk: number
  repo: number
  commit_hash: string
  message: string
  author: string
  date: string
  issues: number[]
}

export interface CommitInfo {
  name: string
  commit: CommitApi
}

export interface Tree {
  path: string
  mode: string
  type: 'tree' | 'blob'
  sha: string
  url: string
  size?: number
  commit?: CommitApi
  open?: boolean
  loaded?: boolean
}

export interface CommitApi {
  sha: string
  url: string
  author: string
  date: string
  message: string
}
