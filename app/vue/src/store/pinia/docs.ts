import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import type {
  Category,
  DFile,
  Docs,
  DocType,
  Link,
  PatchDocs,
  SimpleSuitCase,
  SuitCase,
  TrashDocs as TP,
  OfficialLetter,
  PatchLetter,
  InboundLetter,
  PatchInboundLetter,
  InboundLetterStatus,
} from '@/store/types/docs'
import type { CodeValue } from '@/store/types/work_issue.ts'

export type SuitCaseFilter = {
  company?: number | ''
  project?: number | ''
  is_real_dev?: '' | 'true' | 'false'
  issue_project?: number | ''
  related_case?: number | ''
  sort?: '1' | '2' | '3' | '4' | '5' | ''
  level?: '1' | '2' | '3' | '4' | '5' | '6' | '7' | ''
  court?: string
  in_progress?: boolean | ''
  search?: string
  page?: number
  limit?: number | ''
}

export type DocsFilter = {
  company?: number | ''
  project?: number | ''
  issue_project?: number | ''
  is_real_dev?: '' | 'true' | 'false'
  doc_type?: number | ''
  is_notice?: boolean | ''
  category?: number | ''
  lawsuit?: number | ''
  creator?: number | ''
  ordering?: string
  search?: string
  page?: number
  limit?: number | ''
}

export type LetterFilter = {
  company?: number | ''
  issue_date_from?: string
  issue_date_to?: string
  approval_status?: 'none' | 'pending' | 'approved' | 'rejected' | 'dispatched' | ''
  dispatch_method?: string
  creator?: number | ''
  ordering?: string
  search?: string
  page?: number
  limit?: number | ''
}

export type InboundLetterFilter = {
  company?: number | ''
  received_date_from?: string
  received_date_to?: string
  reply_due_date_from?: string
  reply_due_date_to?: string
  status?: InboundLetterStatus | ''
  recipient_dept?: number | ''
  recipient_manager?: number | ''
  ordering?: string
  search?: string
  page?: number
  limit?: number | ''
}

export const useDocs = defineStore('docs', () => {
  // state & getters
  const docTypes = ref<DocType[]>([
    { value: 1, label: '일반문서' },
    { value: 2, label: '소송기록' },
  ])

  const createDocType = () => 2
  const updateDocType = () => 3
  const deleteDocType = () => 4

  const categoryList = ref<Category[]>([])

  const getCategories = computed<CodeValue[]>(() =>
    categoryList.value.map(c => ({
      pk: c.pk as number,
      name: c.name,
      active: c.active,
      default: c.default,
      order: c.order,
    })),
  )

  const fetchCategoryList = (type: number) =>
    api
      .get(`/category/?doc_type=${type}&active=true`)
      .then(res => (categoryList.value = res.data.results))
      .catch(err => errorHandle(err))

  const createCategory = () => 2
  const updateCategory = () => 3
  const deleteCategory = () => 4

  const suitcase = ref<SuitCase | null>(null)
  const suitcaseList = ref<SuitCase[]>([])
  const suitcaseCount = ref<number>(0)
  const allSuitCaseList = ref<SimpleSuitCase[]>([])
  const lastSuitCaseFilter = ref<SuitCaseFilter | null>(null)
  const lastAllSuitCaseFilter = ref<SuitCaseFilter | null>(null)

  const getSuitCase = computed(() =>
    allSuitCaseList.value.map(s => ({
      value: s.pk as number,
      label: s.__str__
        .replace('지방법원', '지법')
        .replace('고등법원', '고법')
        .replace('대법원', '대법') as string,
    })),
  )
  const getCaseNav = computed(() =>
    suitcaseList.value.map(s => ({
      pk: s.pk,
      prev_pk: s.prev_pk,
      next_pk: s.next_pk,
    })),
  )

  const removeSuitcase = () => (suitcase.value = null)
  const removeSuitcaseList = () => (suitcaseList.value = [])

  const casePages = (itemsPerPage: number) => Math.ceil(suitcaseCount.value / itemsPerPage)

  const fetchSuitCase = (pk: number) =>
    api
      .get(`/suitcase/${pk}/`)
      .then(res => (suitcase.value = res.data))
      .catch(err => errorHandle(err))

  const buildSuitCaseParams = (payload: SuitCaseFilter) => {
    const params = new URLSearchParams()
    const { company, project, issue_project, is_real_dev, in_progress, related_case } = payload
    if (company) params.append('company', String(company))
    if (project) params.append('issue_project__project', String(project))
    if (issue_project) params.append('issue_project', String(issue_project))
    if (is_real_dev) params.append('is_real_dev', String(is_real_dev))
    if (in_progress !== undefined && in_progress !== '')
      params.append('in_progress', String(in_progress))
    if (related_case) params.append('related_case', String(related_case))
    if (payload.court) params.append('court', payload.court)
    if (payload.sort) params.append('sort', payload.sort)
    if (payload.level) params.append('level', payload.level)
    if (payload.search) params.append('search', payload.search)
    return params
  }

  const fetchSuitCaseList = async (payload: SuitCaseFilter) => {
    lastSuitCaseFilter.value = { ...payload }
    const params = buildSuitCaseParams(payload)
    params.append('limit', String(payload.limit || 10))
    params.append('page', String(payload.page || 1))
    return await api
      .get(`/suitcase/?${params.toString()}`)
      .then(res => {
        suitcaseList.value = res.data.results
        suitcaseCount.value = res.data.count
      })
      .catch(err => errorHandle(err))
  }

  const fetchAllSuitCaseList = async (payload: SuitCaseFilter) => {
    lastAllSuitCaseFilter.value = { ...payload }
    const params = buildSuitCaseParams(payload)
    const qs = params.toString()
    return await api
      .get(qs ? `/all-suitcase/?${qs}` : `/all-suitcase/`)
      .then(res => (allSuitCaseList.value = res.data.results))
      .catch(err => errorHandle(err))
  }

  const createSuitCase = async (
    payload: SuitCase & {
      is_real_dev?: boolean
    },
  ) => {
    const is_real_dev =
      payload.is_real_dev !== undefined
        ? payload.is_real_dev
          ? 'true'
          : 'false'
        : (lastAllSuitCaseFilter.value?.is_real_dev ?? lastSuitCaseFilter.value?.is_real_dev ?? '')
    const fallbackFilter: SuitCaseFilter = {
      is_real_dev,
      issue_project: payload.issue_project ?? '',
      page: 1,
    }
    const allFilter: SuitCaseFilter = lastAllSuitCaseFilter.value
      ? {
          ...lastAllSuitCaseFilter.value,
          ...(is_real_dev ? { is_real_dev } : {}),
        }
      : fallbackFilter
    const listFilter: SuitCaseFilter = lastSuitCaseFilter.value
      ? {
          ...lastSuitCaseFilter.value,
          ...(is_real_dev ? { is_real_dev } : {}),
          page: 1,
        }
      : fallbackFilter
    return await api
      .post(`/suitcase/`, payload)
      .then(async res => {
        await fetchAllSuitCaseList(allFilter)
        await fetchSuitCaseList(listFilter)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const updateSuitCase = (payload: SuitCase) =>
    api
      .put(`/suitcase/${payload.pk}/`, payload)
      .then(() => {
        message()
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const deleteSuitCase = (pk: number, listFilter?: SuitCaseFilter, allFilter?: SuitCaseFilter) =>
    api
      .delete(`/suitcase/${pk}/`)
      .then(async () => {
        await fetchAllSuitCaseList(allFilter ?? lastAllSuitCaseFilter.value ?? {})
        await fetchSuitCaseList(listFilter ?? lastSuitCaseFilter.value ?? {})
        message()
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const docs = ref<Docs | null>(null)
  const docsList = ref<Docs[]>([])
  const docsCount = ref(0)
  const lastDocsFilter = ref<DocsFilter | null>(null)
  const getDocsNav = computed(() =>
    docsList.value.map(p => ({
      pk: p.pk,
      prev_pk: p.prev_pk,
      next_pk: p.next_pk,
    })),
  )

  const docsPages = (itemsPerPage: number) => Math.ceil(docsCount.value / itemsPerPage)

  const fetchDocs = async (pk: number) =>
    api
      .get(`/docs/${pk}/`)
      .then(res => {
        docs.value = res.data
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const removeDocs = () => (docs.value = null)
  const setDocs = (payload: Docs) => (docs.value = payload)

  const fetchDocsList = async (payload: DocsFilter) => {
    lastDocsFilter.value = { ...payload }
    const params = new URLSearchParams()
    params.append('limit', String(payload.limit || 10))
    params.append('page', String(payload.page || 1))

    const { company, project, is_real_dev, doc_type, issue_project } = payload
    if (company) params.append('company', String(company))
    if (project) params.append('issue_project__project', String(project))
    if (is_real_dev) params.append('is_real_dev', String(is_real_dev))
    if (doc_type) params.append('doc_type', String(doc_type))
    if (issue_project) params.append('issue_project', String(issue_project))
    if (payload.category) params.append('category', String(payload.category))
    if (payload.lawsuit) params.append('lawsuit', String(payload.lawsuit))
    if (payload.creator) params.append('creator', String(payload.creator))
    if (payload.ordering) params.append('ordering', payload.ordering)
    if (payload.search) params.append('search', payload.search)

    return await api
      .get(`/docs/?${params.toString()}`)
      .then(res => {
        docsList.value = res.data.results
        docsCount.value = res.data.count
      })
      .catch(err => errorHandle(err))
  }

  const removeDocsList = () => (docsList.value = [])

  const hitDocs = (pk: number) =>
    api
      .post(`/docs/${pk}/hit/`)
      .then(res => {
        if (docs.value?.pk === pk) docs.value.hit = res.data.hit
        return res.data
      })
      .catch(err => errorHandle(err))

  const config_headers = { headers: { 'Content-Type': 'multipart/form-data' } }

  const createDocs = (
    payload: {
      form: FormData
    } & {
      isProject?: boolean
    },
  ) =>
    api
      .post(`/docs/`, payload.form, config_headers)
      .then(async res => {
        const listFilter: DocsFilter = lastDocsFilter.value
          ? {
              ...lastDocsFilter.value,
              doc_type: res.data.doc_type,
              page: 1,
            }
          : {
              issue_project: res.data.project?.pk ?? res.data.issue_project ?? '',
              doc_type: res.data.doc_type,
              page: 1,
            }
        await fetchDocsList(listFilter)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateDocs = (
    payload: {
      pk: number
      form: FormData
    } & {
      isProject?: boolean
    },
  ) =>
    api
      .put(`/docs/${payload.pk}/`, payload.form, config_headers)
      .then(async res => {
        const listFilter: DocsFilter = lastDocsFilter.value
          ? {
              ...lastDocsFilter.value,
              doc_type: res.data.doc_type,
            }
          : {
              issue_project: res.data.project?.pk ?? res.data.issue_project ?? '',
              doc_type: res.data.doc_type,
              page: 1,
            }
        await fetchDocsList(listFilter)
        await fetchDocs(res.data.pk)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchDocs = async (
    payload: PatchDocs & {
      filter?: DocsFilter
    },
  ) => {
    const { filter, ...data } = payload
    return await api
      .patch(`/docs/${data.pk}/`, data)
      .then(res =>
        fetchDocsList({
          ...(filter ?? lastDocsFilter.value ?? {}),
        }).then(() => fetchDocs(res.data.pk)),
      )
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const copyDocs = (payload: {
    docs: number
    doc_type: number
    issue_project: number
  }): Promise<boolean> =>
    api
      .post(`/docs/${payload.docs}/copy/`, payload)
      .then(() => {
        message('success', '', '게시물 복사가 완료되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const deleteDocs = (pk: number, filter: DocsFilter): Promise<boolean> =>
    api
      .delete(`/docs/${pk}/`)
      .then(async () => {
        docs.value = null
        await fetchDocsList(filter)
        message('warning', '', '해당 게시물이 휴지통으로 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  // state
  const trashDocs = ref<TP | null>(null)
  const trashDocsList = ref<TP[]>([])
  const trashDocsCount = ref(0)

  const trashDocsPages = (itemsPerPage: number) => Math.ceil(trashDocsCount.value / itemsPerPage)

  const fetchTrashDocs = async (pk: number) =>
    api
      .get(`/docs-trash-can/${pk}/`)
      .then(res => {
        trashDocs.value = res.data
      })
      .catch(err => errorHandle(err))

  const removeTrashDocs = () => (trashDocs.value = null)

  const fetchTrashDocsList = (page = 1, limit = 10) =>
    api
      .get(`/docs-trash-can/?limit=${limit}&page=${page}`)
      .then(res => {
        trashDocsList.value = res.data.results
        trashDocsCount.value = res.data.count
      })
      .catch(err => errorHandle(err))

  const restoreDocs = (pk: number, page = 1): Promise<boolean> =>
    api
      .patch(`/docs-trash-can/${pk}/`)
      .then(() =>
        fetchTrashDocsList(page).then(() => {
          message('success', '', '해당 문서가 휴지통에서 복원되었습니다.')
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })

  const deleteTrashDocs = (pk: number, page = 1): Promise<boolean> =>
    api
      .delete(`/docs-trash-can/${pk}/?hard=1`)
      .then(() =>
        fetchTrashDocsList(page).then(() => {
          message('warning', '', '해당 문서가 영구 삭제되었습니다.')
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })

  // link
  const link = ref<Link | null>(null)

  const fetchLink = (pk: number) =>
    api
      .get(`/link/${pk}/`)
      .then(res => (link.value = res.data))
      .catch(err => errorHandle(err))

  const hitLink = (pk: number) =>
    api
      .post(`/link/${pk}/hit/`)
      .then(res => {
        const target = docs.value?.links?.find(l => l.pk === pk)
        if (target) target.hit = res.data.hit
        return res.data
      })
      .catch(err => errorHandle(err))

  const createLink = (payload: Link) =>
    api
      .post(`/link/`, payload)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err))

  const patchLink = (pk: number, payload: Partial<Link> | Record<string, unknown>) =>
    api
      .patch(`/link/${pk}/`, payload)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err))

  const deleteLink = (pk: number, docs: number) =>
    api
      .delete(`/link/${pk}/`)
      .then(() => fetchDocs(docs))
      .catch(err => errorHandle(err))

  // file
  const file = ref<DFile | null>(null)
  const fileList = ref<DFile[]>()

  const fetchFile = (pk: number) =>
    api
      .get(`/file/${pk}/`)
      .then(res => (file.value = res.data))
      .catch(err => errorHandle(err))

  const hitFile = (pk: number) =>
    api
      .post(`/file/${pk}/hit/`)
      .then(res => {
        const target = docs.value?.files?.find(f => f.pk === pk)
        if (target) target.hit = res.data.hit
        return res.data
      })
      .catch(err => errorHandle(err))

  const fetchFileList = async (docs: number | '') =>
    api
      .get(`/file/?docs=${docs}`)
      .then(res => (fileList.value = res.data.results))
      .catch(err => errorHandle(err))

  const createFile = (payload: FormData) =>
    api
      .post(`/file/`, payload, config_headers)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err))

  const patchFile = (pk: number, payload: FormData | Partial<DFile> | Record<string, unknown>) =>
    api
      .patch(`/file/${pk}/`, payload, config_headers)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err))

  const deleteFile = (pk: number, docs: number) =>
    api
      .delete(`/file/${pk}/`)
      .then(() => fetchDocs(docs))
      .catch(err => errorHandle(err))

  // Official Letter (공문)
  const letter = ref<OfficialLetter | null>(null)
  const letterList = ref<OfficialLetter[]>([])
  const letterCount = ref(0)

  const getLetterNav = computed(() =>
    letterList.value.map(l => ({
      pk: l.pk,
      prev_pk: l.prev_pk,
      next_pk: l.next_pk,
    })),
  )

  const letterPages = (itemsPerPage: number) => Math.ceil(letterCount.value / itemsPerPage)

  const fetchLetter = async (pk: number) =>
    api
      .get(`/official-letter/${pk}/`)
      .then(res => (letter.value = res.data))
      .catch(err => errorHandle(err))

  const removeLetter = () => (letter.value = null)

  const fetchLetterList = async (payload: LetterFilter) => {
    const params = new URLSearchParams()
    params.append('limit', String(payload.limit || 10))
    params.append('page', String(payload.page || 1))

    if (payload.company) params.append('company', String(payload.company))
    if (payload.issue_date_from) params.append('issue_date_from', payload.issue_date_from)
    if (payload.issue_date_to) params.append('issue_date_to', payload.issue_date_to)
    if (payload.approval_status) params.append('approval_status', payload.approval_status)
    if (payload.dispatch_method) params.append('dispatch_method', payload.dispatch_method)
    if (payload.creator) params.append('creator', String(payload.creator))
    if (payload.ordering) params.append('ordering', payload.ordering)
    if (payload.search) params.append('search', payload.search)

    return api
      .get(`/official-letter/?${params.toString()}`)
      .then(res => {
        letterList.value = res.data.results
        letterCount.value = res.data.count
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const removeLetterList = () => (letterList.value = [])

  const createLetter = (payload: OfficialLetter, filter?: LetterFilter) =>
    api
      .post('/official-letter/', payload)
      .then(async res => {
        await fetchLetterList(
          filter
            ? { ...filter, company: res.data.company, page: 1 }
            : { company: res.data.company, page: 1 },
        )
        message()
        return res.data as OfficialLetter
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateLetter = (pk: number, payload: OfficialLetter, filter?: LetterFilter) =>
    api
      .put(`/official-letter/${pk}/`, payload)
      .then(async res => {
        await fetchLetterList(
          filter
            ? { ...filter, company: res.data.company }
            : { company: res.data.company, page: 1 },
        )
        await fetchLetter(res.data.pk)
        message()
        return res.data as OfficialLetter
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchLetter = async (pk: number, payload: PatchLetter) =>
    api
      .patch(`/official-letter/${pk}/`, payload)
      .then(async res => {
        await fetchLetter(res.data.pk)
        message()
        return res.data as OfficialLetter
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteLetter = (pk: number, filter: LetterFilter) =>
    api
      .delete(`/official-letter/${pk}/`)
      .then(async () => {
        await fetchLetterList(filter)
        message('warning', '', '해당 공문이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const generatePdf = async (pk: number) =>
    api
      .post(`/official-letter/${pk}/generate_pdf/`)
      .then(async res => {
        await fetchLetter(pk)
        message('success', '', 'PDF가 생성되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const uploadLetterPdf = async (pk: number, file: File) => {
    const formData = new FormData()
    formData.append('pdf_file', file)
    return api
      .post(`/official-letter/${pk}/upload_pdf/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then(async res => {
        await fetchLetter(pk)
        message('success', '', '공문 PDF(스캔본) 파일이 성공적으로 업로드되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const getNextDocumentNumber = async (company: number) =>
    api
      .get(`/official-letter/next_document_number/?company=${company}`)
      .then(res => res.data.next_document_number)
      .catch(err => {
        errorHandle(err)
        return ''
      })

  const submitApproval = async (pk: number) =>
    api
      .post(`/official-letter/${pk}/submit_approval/`)
      .then(async res => {
        await fetchLetter(pk)
        message('success', '', '전자결재가 성공적으로 상신되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const uploadLetterAttachment = async (letterId: number, formData: FormData) =>
    api
      .post('/official-letter-attachment/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then(async res => {
        await fetchLetter(letterId)
        message('success', '', '첨부파일이 등록되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteLetterAttachment = async (attachmentId: number, letterId: number) =>
    api
      .delete(`/official-letter-attachment/${attachmentId}/`)
      .then(async () => {
        await fetchLetter(letterId)
        message('warning', '', '첨부파일이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  // Inbound Official Letter (수신 공문)
  const inboundLetter = ref<InboundLetter | null>(null)
  const inboundLetterList = ref<InboundLetter[]>([])
  const inboundLetterCount = ref(0)

  const getInboundLetterNav = computed(() =>
    inboundLetterList.value.map(l => ({
      pk: l.pk,
      prev_pk: l.prev_pk,
      next_pk: l.next_pk,
    })),
  )

  const inboundLetterPages = (itemsPerPage: number) =>
    Math.ceil(inboundLetterCount.value / itemsPerPage)

  const fetchInboundLetter = async (pk: number) =>
    api
      .get(`/inbound-letter/${pk}/`)
      .then(res => {
        inboundLetter.value = res.data
        return res.data as InboundLetter
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const removeInboundLetter = () => (inboundLetter.value = null)

  const fetchInboundLetterList = async (payload: InboundLetterFilter) => {
    const params = new URLSearchParams()
    params.append('limit', String(payload.limit || 10))
    params.append('page', String(payload.page || 1))

    if (payload.company) params.append('company', String(payload.company))
    if (payload.received_date_from) params.append('received_date_from', payload.received_date_from)
    if (payload.received_date_to) params.append('received_date_to', payload.received_date_to)
    if (payload.reply_due_date_from)
      params.append('reply_due_date_from', payload.reply_due_date_from)
    if (payload.reply_due_date_to) params.append('reply_due_date_to', payload.reply_due_date_to)
    if (payload.status) params.append('status', payload.status)
    if (payload.recipient_dept) params.append('recipient_dept', String(payload.recipient_dept))
    if (payload.recipient_manager)
      params.append('recipient_manager', String(payload.recipient_manager))
    if (payload.ordering) params.append('ordering', payload.ordering)
    if (payload.search) params.append('search', payload.search)

    return api
      .get(`/inbound-letter/?${params.toString()}`)
      .then(res => {
        inboundLetterList.value = res.data.results
        inboundLetterCount.value = res.data.count
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const removeInboundLetterList = () => (inboundLetterList.value = [])

  const createInboundLetter = (payload: FormData | InboundLetter, filter?: InboundLetterFilter) => {
    const headers = payload instanceof FormData ? config_headers : undefined
    return api
      .post('/inbound-letter/', payload, headers)
      .then(async res => {
        await fetchInboundLetterList(
          filter
            ? { ...filter, company: res.data.company, page: 1 }
            : { company: res.data.company, page: 1 },
        )
        message()
        return res.data as InboundLetter
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const updateInboundLetter = (
    pk: number,
    payload: FormData | InboundLetter,
    filter?: InboundLetterFilter,
  ) => {
    const headers = payload instanceof FormData ? config_headers : undefined
    return api
      .put(`/inbound-letter/${pk}/`, payload, headers)
      .then(async res => {
        await fetchInboundLetterList(
          filter
            ? { ...filter, company: res.data.company }
            : { company: res.data.company, page: 1 },
        )
        await fetchInboundLetter(res.data.pk)
        message()
        return res.data as InboundLetter
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const patchInboundLetter = async (pk: number, payload: PatchInboundLetter) =>
    api
      .patch(`/inbound-letter/${pk}/`, payload)
      .then(async res => {
        await fetchInboundLetter(res.data.pk)
        message()
        return res.data as InboundLetter
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteInboundLetter = (pk: number, filter: InboundLetterFilter) =>
    api
      .delete(`/inbound-letter/${pk}/`)
      .then(async () => {
        await fetchInboundLetterList(filter)
        message('warning', '', '해당 수신 공문이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const getNextReceiptNumber = async (company: number) =>
    api
      .get(`/inbound-letter/next_receipt_number/?company=${company}`)
      .then(res => res.data.next_receipt_number)
      .catch(err => {
        errorHandle(err)
        return ''
      })

  const uploadInboundAttachment = async (letterId: number, formData: FormData) =>
    api
      .post('/inbound-letter-attachment/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then(async res => {
        await fetchInboundLetter(letterId)
        message('success', '', '첨부파일이 등록되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteInboundAttachment = async (attachmentId: number, letterId: number) =>
    api
      .delete(`/inbound-letter-attachment/${attachmentId}/`)
      .then(async () => {
        await fetchInboundLetter(letterId)
        message('warning', '', '첨부파일이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const submitInboundApproval = async (pk: number) =>
    api
      .post(`/inbound-letter/${pk}/submit_approval/`)
      .then(async res => {
        await fetchInboundLetter(pk)
        message('success', '', res.data.detail || '전자결재가 상신되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  return {
    docTypes,

    createDocType,
    updateDocType,
    deleteDocType,

    categoryList,
    getCategories,

    fetchCategoryList,
    createCategory,
    updateCategory,
    deleteCategory,

    suitcase,
    suitcaseList,
    suitcaseCount,
    getSuitCase,
    getCaseNav,

    removeSuitcase,
    removeSuitcaseList,
    casePages,
    fetchSuitCase,
    fetchSuitCaseList,
    fetchAllSuitCaseList,
    createSuitCase,
    updateSuitCase,
    deleteSuitCase,

    docs,
    docsList,
    docsCount,
    getDocsNav,

    docsPages,
    fetchDocs,
    removeDocs,
    setDocs,
    fetchDocsList,
    removeDocsList,
    hitDocs,
    createDocs,
    updateDocs,
    patchDocs,
    copyDocs,
    deleteDocs,

    trashDocs,
    trashDocsList,
    trashDocsCount,

    trashDocsPages,
    fetchTrashDocs,
    removeTrashDocs,
    fetchTrashDocsList,
    restoreDocs,
    deleteTrashDocs,

    link,
    fetchLink,
    hitLink,
    createLink,
    patchLink,
    deleteLink,

    file,
    fetchFile,
    hitFile,
    fetchFileList,
    createFile,
    patchFile,
    deleteFile,

    // Official Letter (공문)
    letter,
    letterList,
    letterCount,
    getLetterNav,

    letterPages,
    fetchLetter,
    removeLetter,
    fetchLetterList,
    removeLetterList,
    createLetter,
    updateLetter,
    patchLetter,
    deleteLetter,
    generatePdf,
    uploadLetterPdf,
    getNextDocumentNumber,
    submitApproval,
    uploadLetterAttachment,
    deleteLetterAttachment,

    // Inbound Letter (수신 공문)
    inboundLetter,
    inboundLetterList,
    inboundLetterCount,
    getInboundLetterNav,
    inboundLetterPages,
    fetchInboundLetter,
    removeInboundLetter,
    fetchInboundLetterList,
    removeInboundLetterList,
    createInboundLetter,
    updateInboundLetter,
    patchInboundLetter,
    deleteInboundLetter,
    getNextReceiptNumber,
    uploadInboundAttachment,
    deleteInboundAttachment,
    submitInboundApproval,
  }
})
