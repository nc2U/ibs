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
  creator?: number | ''
  ordering?: string
  search?: string
  page?: number
  limit?: number | ''
}

export const useDocs = defineStore('docs', () => {
  // state & getters
  const docType = ref<DocType | null>(null)
  const docTypeList = ref<DocType[]>([])

  const fetchDocType = (pk: number) =>
    api
      .get(`/doc-type/${pk}/`)
      .then(res => (docType.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchDocTypeList = () =>
    api
      .get('/doc-type/')
      .then(res => (docTypeList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

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
      .get(`/category/?doc_type=${type}`)
      .then(res => (categoryList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createCategory = () => 2
  const updateCategory = () => 3
  const deleteCategory = () => 4

  const suitcase = ref<SuitCase | null>(null)
  const suitcaseList = ref<SuitCase[]>([])
  const suitcaseCount = ref<number>(0)
  const allSuitCaseList = ref<SimpleSuitCase[]>([])

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
      .catch(err => errorHandle(err.response.data))

  const getQueryStr = (payload: SuitCaseFilter) => {
    const { company, project, issue_project, is_real_dev, in_progress, related_case } = payload
    let queryStr = ''
    if (company) queryStr += `&company=${company}`
    if (project) queryStr += `&issue_project__project=${project}`
    if (issue_project) queryStr += `&issue_project=${issue_project}`
    if (is_real_dev) queryStr += `&is_real_dev=${is_real_dev}`
    queryStr += `&in_progress=${in_progress ?? ''}`
    if (related_case) queryStr += `&related_case=${related_case}`
    if (payload.court) queryStr += `&court=${payload.court}`
    if (payload.sort) queryStr += `&sort=${payload.sort}`
    if (payload.level) queryStr += `&level=${payload.level}`
    if (payload.search) queryStr += `&search=${payload.search}`
    return queryStr
  }

  const fetchSuitCaseList = async (payload: SuitCaseFilter) => {
    const limit = payload.limit || 10
    const page = payload.page || 1
    const queryStr = getQueryStr(payload)
    return await api
      .get(`/suitcase/?limit=${limit}&page=${page}${queryStr}`)
      .then(res => {
        suitcaseList.value = res.data.results
        suitcaseCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllSuitCaseList = async (payload: SuitCaseFilter) => {
    const queryStr = getQueryStr(payload)
    return await api
      .get(`/all-suitcase/?1=1${queryStr}`)
      .then(res => (allSuitCaseList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const createSuitCase = async (
    payload: SuitCase & {
      is_real_dev?: boolean
    },
  ) => {
    const is_real_dev = payload.is_real_dev ? 'true' : 'false'
    const retData: SuitCaseFilter = {
      is_real_dev,
      issue_project: payload.issue_project ?? '',
      page: 1,
    }
    return await api
      .post(`/suitcase/`, payload)
      .then(res => {
        fetchAllSuitCaseList(retData).then(() => fetchSuitCaseList(retData).then(() => message()))
        return res.data.results
      })
      .catch(err => errorHandle(err.response.data))
  }

  const updateSuitCase = (payload: SuitCase) =>
    api
      .put(`/suitcase/${payload.pk}/`, payload)
      .then(() => message())
      .catch(err => errorHandle(err.response.data))

  const deleteSuitCase = (pk: number) =>
    api
      .delete(`/suitcase/${pk}/`)
      .then(() => fetchAllSuitCaseList({}).then(() => fetchSuitCaseList({}).then(() => message())))
      .catch(err => errorHandle(err.response.data))

  const docs = ref<Docs | null>(null)
  const docsList = ref<Docs[]>([])
  const docsCount = ref(0)
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
      })
      .catch(err => errorHandle(err.response.data))

  const removeDocs = () => (docs.value = null)

  const fetchDocsList = async (payload: DocsFilter) => {
    const limit = payload.limit || 10
    const page = payload.page || 1
    let url = `/docs/?limit=${limit}&page=${page}`

    const { company, project, is_real_dev, doc_type, issue_project } = payload
    if (company) url += `&company=${company}`
    if (project) url += `&issue_project__project=${project}`
    if (is_real_dev) url += `&is_real_dev=${is_real_dev}`
    if (doc_type) url += `&doc_type=${doc_type}`
    if (issue_project) url += `&issue_project=${issue_project}`
    if (payload.category) url += `&category=${payload.category}`
    if (payload.lawsuit) url += `&lawsuit=${payload.lawsuit}`
    if (payload.creator) url += `&user=${payload.creator}`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    if (payload.search) url += `&search=${payload.search}`

    return await api
      .get(url)
      .then(res => {
        docsList.value = res.data.results
        docsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const removeDocsList = () => (docsList.value = [])

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
        await fetchDocsList({
          issue_project: res.data.issue_project,
          doc_type: res.data.doc_type,
          page: 1,
        })
        message()
      })
      .catch(err => errorHandle(err.response.data))

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
        await fetchDocsList({
          issue_project: res.data.issue_project,
          doc_type: res.data.doc_type,
          page: 1,
        })
        await fetchDocs(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

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
          ...filter,
        }).then(() => fetchDocs(res.data.pk)),
      )
      .catch(err => errorHandle(err.response.data))
  }

  const copyDocs = (payload: { docs: number; doc_type: number; issue_project: number }) =>
    api
      .post(`docs/${payload.docs}/copy/`, payload)
      .then(() => message('success', '', '게시물 복사가 완료되었습니다.'))
      .catch(err => errorHandle(err.response.data))

  const deleteDocs = (pk: number, filter: DocsFilter) =>
    api
      .delete(`/docs/${pk}/`)
      .then(() =>
        fetchDocsList(filter).then(() =>
          message('warning', '', '해당 게시물이 휴지통으로 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

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
      .catch(err => errorHandle(err.response.data))

  const removeTrashDocs = () => (trashDocs.value = null)

  const fetchTrashDocsList = (page = 1) =>
    api
      .get(`/docs-trash-can/?page=${page}`)
      .then(res => {
        trashDocsList.value = res.data.results
        trashDocsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))

  const restoreDocs = (pk: number, isProject = false) =>
    api
      .patch(`/docs-trash-can/${pk}/`)
      .then(res =>
        fetchDocsList({
          issue_project: res.data.issue_project,
          doc_type: res.data.doc_type,
          page: 1,
        }).then(() =>
          fetchTrashDocsList().then(() =>
            message('success', '', '해당 게시물이 휴지통에서 복원되었습니다.'),
          ),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  const deleteTrashDocs = (pk: number, page = 1) =>
    api
      .delete(`/docs-trash-can/${pk}/?hard=1`)
      .then(() =>
        fetchTrashDocsList(page).then(() =>
          message('danger', '', '해당 게시물이 영구 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // link
  const link = ref<Link | null>(null)

  const fetchLink = (pk: number) =>
    api
      .get(`/link/${pk}/`)
      .then(res => (link.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createLink = (payload: Link) =>
    api
      .post(`/link/`, payload)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err.response.data))

  const patchLink = (pk: number, payload: Link | any) =>
    api
      .patch(`/link/${pk}/`, payload)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err.response.data))

  const deleteLink = (pk: number, docs: number) =>
    api
      .delete(`/link/${pk}/`)
      .then(() => fetchDocs(docs))
      .catch(err => errorHandle(err.response.data))

  // file
  const file = ref<DFile | null>(null)
  const fileList = ref<DFile[]>()

  const fetchFile = (pk: number) =>
    api
      .get(`/file/${pk}/`)
      .then(res => (file.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchFileList = async (docs: number | '') =>
    api
      .get(`/file/?docs=${docs}`)
      .then(res => (fileList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createFile = (payload: FormData) =>
    api
      .post(`/file/`, payload, config_headers)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err.response.data))

  const patchFile = (pk: number, payload: FormData | any) =>
    api
      .patch(`/file/${pk}/`, payload, config_headers)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err.response.data))

  const deleteFile = (pk: number, docs: number) =>
    api
      .delete(`/file/${pk}/`)
      .then(() => fetchDocs(docs))
      .catch(err => errorHandle(err.response.data))

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
      .catch(err => errorHandle(err.response.data))

  const removeLetter = () => (letter.value = null)

  const fetchLetterList = async (payload: LetterFilter) => {
    const limit = payload.limit || 10
    const page = payload.page || 1
    let url = `/official-letter/?limit=${limit}&page=${page}`

    const { company, issue_date_from, issue_date_to, creator } = payload
    if (company) url += `&company=${company}`
    if (issue_date_from) url += `&issue_date_from=${issue_date_from}`
    if (issue_date_to) url += `&issue_date_to=${issue_date_to}`
    if (creator) url += `&creator=${creator}`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    if (payload.search) url += `&search=${payload.search}`

    return await api
      .get(url)
      .then(res => {
        letterList.value = res.data.results
        letterCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const removeLetterList = () => (letterList.value = [])

  const createLetter = (payload: OfficialLetter) =>
    api
      .post('/official-letter/', payload)
      .then(async res => {
        await fetchLetterList({ company: res.data.company, page: 1 })
        message()
        return res.data
      })
      .catch(err => errorHandle(err.response.data))

  const updateLetter = (pk: number, payload: OfficialLetter) =>
    api
      .put(`/official-letter/${pk}/`, payload)
      .then(async res => {
        await fetchLetterList({ company: res.data.company, page: 1 })
        await fetchLetter(res.data.pk)
        message()
        return res.data
      })
      .catch(err => errorHandle(err.response.data))

  const patchLetter = async (pk: number, payload: PatchLetter) =>
    api
      .patch(`/official-letter/${pk}/`, payload)
      .then(res => fetchLetter(res.data.pk))
      .catch(err => errorHandle(err.response.data))

  const deleteLetter = (pk: number, filter: LetterFilter) =>
    api
      .delete(`/official-letter/${pk}/`)
      .then(() =>
        fetchLetterList(filter).then(() => message('warning', '', '해당 공문이 삭제되었습니다.')),
      )
      .catch(err => errorHandle(err.response.data))

  const generatePdf = async (pk: number) =>
    api
      .post(`/official-letter/${pk}/generate_pdf/`)
      .then(res => {
        fetchLetter(pk)
        message('success', '', 'PDF가 생성되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err.response.data))

  const getNextDocumentNumber = async (company: number) =>
    api
      .get(`/official-letter/next_document_number/?company=${company}`)
      .then(res => res.data.next_document_number)
      .catch(err => errorHandle(err.response.data))

  return {
    docType,
    docTypeList,

    fetchDocType,
    fetchDocTypeList,
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
    fetchDocsList,
    removeDocsList,
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
    createLink,
    patchLink,
    deleteLink,

    file,
    fetchFile,
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
    getNextDocumentNumber,
  }
})
