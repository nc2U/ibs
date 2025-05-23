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

export interface Tree {
  path: string
  mode: string
  type: 'blob' | 'tree'
  sha: string
  url: string
}

export interface Trunk {
  sha: string
  url: string
  tree: Tree[]
  truncated: boolean
}
