export interface CommitInfo {
  name: string
  commit: Commit
}

export interface Commit {
  sha: string
  url: string
  author: string
  date: string
  message: string
}

export interface Tree {
  path: string
  mode: string
  type: 'tree' | 'blob'
  sha: string
  url: string
  size?: number
  commit?: Commit
  open?: boolean
  loaded?: boolean
}
