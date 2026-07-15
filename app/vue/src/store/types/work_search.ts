import type { SimpleProject } from '@/store/types/work_project.ts'

export interface SearchResultIssue {
  pk: number
  project: { slug: string; name: string }
  tracker: { pk: number; name: string }
  status: { name: string; closed: boolean }
  subject: string
  created: string
  creator: { pk: number; username: string } | null
  is_private: boolean
}

export interface SearchResultComment {
  pk: number
  issue: {
    pk: number
    subject: string
    project: { slug: string; name: string }
  }
  content: string
  created: string
  creator: { pk: number; username: string }
}

export interface SearchResultMeeting {
  pk: number
  project: { slug: string; name: string }
  title: string
  meeting_date: string | null
  status: string
  creator: { pk: number; username: string }
}

export interface SearchResultNews {
  pk: number
  project: { slug: string; name: string }
  title: string
  summary: string
  created: string
  author: { pk: number; username: string }
}

export interface SearchResultDoc {
  pk: number
  project: { slug: string; name: string }
  title: string
  description: string
  created: string
  creator: { pk: number; username: string } | null
}

export interface SearchResultPost {
  pk: number
  project: { slug: string; name: string }
  forum: number
  title: string
  created: string
  creator: { pk: number; username: string } | null
}

export interface SearchResults {
  issues?: SearchResultIssue[]
  comments?: SearchResultComment[]
  meetings?: SearchResultMeeting[]
  news?: SearchResultNews[]
  documents?: SearchResultDoc[]
  posts?: SearchResultPost[]
}

export interface SearchParams {
  q: string
  scope?: 'all' | 'my' | 'project'
  slug?: string
  t?: string[]
  title_only?: '0' | '1'
  opened_only?: '0' | '1'
}
