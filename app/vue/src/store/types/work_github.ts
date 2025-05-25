export interface Branch {
  name: string
  commit: {
    sha: string
    url: string
  }
  protected: boolean
}

export interface Tag {
  name: string
  zipball_url: string
  tarball_url: string
  commit: {
    sha: string
    url: string
  }
  node_id: string
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
}

export interface TreeNode {
  name: string
  type: 'tree' | 'blob'
  sha: string
  url: string
  size?: number
  children?: TreeNode[]
  loaded?: boolean
}
