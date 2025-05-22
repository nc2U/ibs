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
