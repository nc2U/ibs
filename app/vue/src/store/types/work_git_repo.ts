export interface Repository {
  pk?: number
  project: number
  is_default: boolean
  slug: string
  local_path: string
  remote_url: string
  is_report: boolean
}

export interface RepoApi {
  name: string
  created: string
  pushed: string
  default_branch: string
}

export interface Commit {
  pk: number
  repo: number
  commit_hash: string
  author: string
  date: string
  message: string
  branches: string[]
  parents: string[]
  children: string[]
  issues: {
    pk: number
    project: string
    tracker: string
    subject: string
  }[]
  prev: string | null
  next: string | null
}

export interface BranchInfo {
  name: string
  branches: string[]
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
  modified: string
  binary: boolean
  content: string | null
  message?: string
}

export interface DiffApi {
  base: string | null
  head: string
  commits: CommitApi[]
  diff: string
  truncated: boolean
}

export interface ChangedFile {
  sha: string
  changed: Changed[]
}

export interface Changed {
  path: string
  type: 'A' | 'C' | 'D' | 'M' | 'R'
} // 'add', 'copied', 'deleted', 'modified', 'renamed'

export interface Dag {
  sha: string
  parents: string[]
  children: string[]
  author: string
  date: string
  message: string
  branches: string[]
  space: number
}
