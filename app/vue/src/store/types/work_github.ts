export interface Repository {
  pk?: number
  project: number
  is_default: boolean
  slug: string
  local_path: string
  is_report: boolean
}

export interface RepoApi {
  name: string
  created_at: string
  pushed_at: string
  default_branch: string
}

export interface Commit {
  pk: number
  revision_id: number
  repo: number
  commit_hash: string
  message: string
  author: string
  date: string
  issues: number[]
}

export interface BranchInfo {
  name: string
  commit: CommitApi
}

export interface Tree {
  path: string
  name: string
  mode: string
  type: 'tree' | 'blob'
  sha: string
  size?: number
  commit?: CommitApi
}

export interface CommitApi {
  sha: string
  author: string
  date: string
  message: string
}

export interface FileInfo {
  name: string
  path: string
  sha: string
  size: number
  content: string
}
