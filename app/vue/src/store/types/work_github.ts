export interface GitData {
  name: string
  commit: {
    sha: string
    url: string
    author: string
    date: string
    message: string
  }
}

export interface Master {
  sha: string
  url: string
  tree: Tree[]
  truncated: boolean
}

export interface Tree {
  path: string
  mode: string
  type: 'tree' | 'blob'
  sha: string
  url: string
  size?: number
  open?: boolean
  loaded?: boolean
}
