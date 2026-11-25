import type { NewsFile } from '@/store/types/work_inform'

export type NewsFormFile = NewsFile & { del?: boolean }

export interface NewsNewFileItem {
  file: File | null
  description: string
}

export interface NewsFormPayload {
  pk: number | null
  project: string | null
  title: string
  summary: string
  content: string
  is_important: boolean
  files: NewsFormFile[]
  newFiles: NewsNewFileItem[]
  cngFiles: { pk: number; file: File }[]
}

export const buildNewsFormData = (payload: NewsFormPayload): FormData => {
  const form = new FormData()

  if (payload.project) form.append('project', payload.project)
  form.append('title', payload.title ?? '')
  form.append('summary', payload.summary ?? '')
  form.append('content', payload.content ?? '')
  form.append('is_important', String(!!payload.is_important))

  if (Array.isArray(payload.files)) {
    payload.files.forEach(val => form.append('files', JSON.stringify(val)))
  }
  if (Array.isArray(payload.newFiles)) {
    payload.newFiles.forEach(val => {
      if (val?.file) {
        form.append('new_files', val.file)
        form.append('new_descs', val.description ?? '')
      }
    })
  }
  if (Array.isArray(payload.cngFiles)) {
    payload.cngFiles.forEach(val => {
      if (val?.file) {
        form.append('cngPks', String(val.pk))
        form.append('cngFiles', val.file)
      }
    })
  }
  return form
}
