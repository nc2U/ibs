import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import type {
  DocType,
  Category,
  AFile,
  Link,
  PatchDocs,
  SuitCase,
  SimpleSuitCase,
  Docs,
  TrashDocs as TP,
} from '@/store/types/docs'
import type { CodeValue } from '@/store/types/work'

export type SuitCaseFilter = {
  company?: number | ''
  project?: number | ''
  is_com?: boolean
  court?: string
  related_case?: number | ''
  sort?: '1' | '2' | '3' | '4' | '5' | ''
  level?: '1' | '2' | '3' | '4' | '5' | '6' | '7' | ''
  in_progress?: boolean | ''
  search?: string
  page?: number
  limit?: number | ''
}

export type DocsFilter = {
  company?: number | ''
  project?: number | ''
  issue_project?: number | ''
  doc_type?: number | ''
  is_notice?: boolean | ''
  is_com?: boolean
  category?: number | ''
  lawsuit?: number | ''
  user?: number | ''
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
      value: s.pk,
      label: s.__str__
        .replace('지방법원', '지법')
        .replace('고등법원', '고법')
        .replace('대법원', '대법'),
    })),
  )
  const getCaseNav = computed(() =>
    suitcaseList.value.map(s => ({
      pk: s.pk,
      prev_pk: s.prev_pk,
      next_pk: s.next_pk,
    })),
  )

  const casePages = (itemsPerPage: number) => Math.ceil(suitcaseCount.value / itemsPerPage)

  const fetchSuitCase = (pk: number) =>
    api
      .get(`/suitcase/${pk}/`)
      .then(res => (suitcase.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const getQueryStr = (payload: SuitCaseFilter) => {
    const { project, is_com, in_progress, court, related_case, sort, level, search } = payload
    let queryStr = ''
    if (project) queryStr += `&project=${project}`
    queryStr += `&is_com=${is_com ?? ''}`
    queryStr += `&in_progress=${in_progress ?? ''}`
    if (court) queryStr += `&court=${court}`
    if (related_case) queryStr += `&related_case=${related_case}`
    if (sort) queryStr += `&sort=${sort}`
    if (level) queryStr += `&level=${level}`
    if (search) queryStr += `&search=${search}`
    return queryStr
  }

  const fetchSuitCaseList = async (payload: SuitCaseFilter) => {
    const limit = payload.limit || 10
    const page = payload.page || 1
    const company = payload.company ?? ''
    const queryStr = getQueryStr(payload)
    return await api
      .get(`/suitcase/?limit=${limit}&page=${page}&company=${company}${queryStr}`)
      .then(res => {
        suitcaseList.value = res.data.results
        suitcaseCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllSuitCaseList = async (payload: SuitCaseFilter) => {
    const queryStr = getQueryStr(payload)
    return await api
      .get(`/all-suitcase/?company=${payload.company ?? ''}&${queryStr}`)
      .then(res => (allSuitCaseList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const createSuitCase = async (
    payload: SuitCase & {
      isProject?: boolean
    },
  ) => {
    const retData: SuitCaseFilter = payload.isProject
      ? { company: payload.company ?? '', is_com: false, project: payload.project ?? '', page: 1 }
      : { company: payload.company ?? '', is_com: true, page: 1 }
    return await api
      .post(`/suitcase/`, payload)
      .then(() =>
        fetchAllSuitCaseList(retData).then(() => fetchSuitCaseList(retData).then(() => message())),
      )
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
    const { doc_type, page } = payload
    const limit = payload.limit || 10
    let url = `/docs/?limit=${limit}&page=${page ?? 1}`
    if (payload.doc_type) url += `&doc_type=${doc_type}`
    if (payload.company) url += `&company=${payload.company}`
    if (payload.is_com) url += `&is_com=${payload.is_com}`
    if (payload.project) url += `&project=${payload.project}`
    if (payload.category) url += `&category=${payload.category}`
    if (payload.lawsuit) url += `&lawsuit=${payload.lawsuit}`
    if (payload.user) url += `&user=${payload.user}`
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
          company: res.data.company,
          project: res.data.project,
          doc_type: res.data.doc_type,
          is_com: !payload.isProject,
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
          company: res.data.company,
          project: res.data.project,
          doc_type: res.data.doc_type,
          is_com: !payload.isProject,
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
          company: res.data.company,
          ...filter,
        }).then(() => fetchDocs(res.data.pk)),
      )
      .catch(err => errorHandle(err.response.data))
  }

  const copyDocs = (payload: { docs: number; doc_type: number; project: number | null }) =>
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
          company: res.data.company,
          project: res.data.project,
          doc_type: res.data.doc_type,
          is_com: !isProject,
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

  const link = ref<Link | null>(null)

  const fetchLink = (pk: number) =>
    api
      .get(`/link/${pk}/`)
      .then(res => (link.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const patchLink = (payload: Link) =>
    api
      .patch(`/link/${payload.pk}/`, payload)
      .then(res => fetchDocs(res.data.docs))
      .catch(err => errorHandle(err.response.data))

  const file = ref<AFile | null>(null)

  const fetchFile = (pk: number) =>
    api
      .get(`/file/${pk}/`)
      .then(res => (file.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const patchFile = (payload: AFile) =>
    api
      .patch(`/file/${payload.pk}/`, payload)
      .then(res => fetchDocs(res.data.docs))
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
    patchLink,

    file,
    fetchFile,
    patchFile,
  }
})
