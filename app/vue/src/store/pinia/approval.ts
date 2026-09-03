import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import type {
  DocCategory,
  DocumentType,
  ApprovalDocument,
  PatchApprovalDocument,
  ApprovalActPayload,
  StaffAssignmentItem,
  RoutePreviewStep,
  AllDocFilter,
  ApprovalDocumentListItem,
  ApprovalDelegation,
} from '@/store/types/approval'

export type DocFilter = {
  status?: string
  doc_type?: string
  drafter?: string
  page?: number
}

export const useApproval = defineStore('approval', () => {
  // ── 문서 카테고리 ─────────────────────────────────────
  const docCategoryList = ref<DocCategory[]>([])

  const fetchDocCategoryList = () =>
    api
      .get('/approval-doc-category/')
      .then(res => (docCategoryList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchDocCategoryList failed:', err?.message || err)
      })

  // ── 문서 유형 ─────────────────────────────────────────
  const docTypeList = ref<DocumentType[]>([])
  const forDraftDocTypeList = ref<DocumentType[]>([])

  const fetchDocTypeList = async (categoryId?: number | null) => {
    const params = new URLSearchParams()
    if (categoryId) params.append('category_id', String(categoryId))
    return await api
      .get(`/approval-doc-type/?${params}`)
      .then(res => (docTypeList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchDocTypeList failed:', err?.message || err)
      })
  }

  const fetchForDraftDocTypeList = async (assignmentId?: number | null) => {
    const params = new URLSearchParams()
    if (assignmentId) params.append('assignment', String(assignmentId))
    return await api
      .get(`/approval-doc-type/for_draft/?${params}`)
      .then(res => (forDraftDocTypeList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchForDraftDocTypeList failed:', err?.message || err)
      })
  }

  // ── 기안자의 보직 목록 ─────────────────────────────────
  const myAssignments = ref<StaffAssignmentItem[]>([])

  const fetchMyAssignments = () =>
    api
      .get('/approval-document/my_assignments/')
      .then(res => (myAssignments.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchMyAssignments failed:', err?.message || err)
      })

  // ── 동적 결재선 미리보기 ───────────────────────────────
  const routePreview = ref<RoutePreviewStep[]>([])

  const fetchRoutePreview = async (
    docTypeId: number,
    assignmentId?: number | null,
    amount?: number | string | null,
  ) => {
    const params = new URLSearchParams({ doc_type: String(docTypeId) })
    if (assignmentId) params.append('assignment', String(assignmentId))
    if (amount !== undefined && amount !== null && amount !== '')
      params.append('amount', String(amount))
    return await api
      .get(`/approval-document/preview_route/?${params}`)
      .then(res => (routePreview.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  // ── 결재 문서 ─────────────────────────────────────────
  const document = ref<ApprovalDocument | null>(null)
  const documentList = ref<ApprovalDocument[]>([])
  const documentCount = ref(0)

  const fetchDocumentList = async (payload: DocFilter = {}) => {
    const params = new URLSearchParams()
    Object.entries(payload).forEach(([k, v]) => {
      if (v !== undefined && v !== '') params.append(k, String(v))
    })
    return await api
      .get(`/approval-document/?${params}`)
      .then(res => {
        documentList.value = res.data.results ?? res.data
        documentCount.value = res.data.count ?? documentList.value.length
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchDocument = (pk: number) =>
    api
      .get(`/approval-document/${pk}/`)
      .then(res => (document.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createDocument = async (payload: PatchApprovalDocument | FormData) => {
    try {
      const headers =
        payload instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
      const res = await api.post('/approval-document/', payload, { headers })
      document.value = res.data
      await fetchMyDrafted()
      message()
      return res.data as ApprovalDocument
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const updateDocument = async (pk: number, payload: PatchApprovalDocument | FormData) => {
    try {
      const headers =
        payload instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
      const res = await api.patch(`/approval-document/${pk}/`, payload, { headers })
      document.value = res.data
      message()
      return res.data as ApprovalDocument
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const deleteDocument = async (pk: number) => {
    try {
      await api.delete(`/approval-document/${pk}/`)
      await fetchMyDrafted()
      message()
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const deleteAttachment = async (attachmentId: number, docId?: number) => {
    try {
      await api.delete(`/approval-attachment/${attachmentId}/`)
      if (docId) {
        await fetchDocument(docId)
      }
      message()
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  // ── 결재 대기함 / 기안함 ─────────────────────────────
  const pendingList = ref<ApprovalDocument[]>([])
  const draftedList = ref<ApprovalDocument[]>([])

  const fetchMyPending = () =>
    api
      .get('/approval-document/my_pending/')
      .then(res => (pendingList.value = res.data))
      .catch(err => {
        console.warn('fetchMyPending failed:', err?.message || err)
      })

  const fetchMyDrafted = () =>
    api
      .get('/approval-document/my_drafted/')
      .then(res => (draftedList.value = res.data))
      .catch(err => {
        console.warn('fetchMyDrafted failed:', err?.message || err)
      })

  // ── 60초 주기 자동 갱신 (Polling) ─────────────────────
  let pollingTimer: ReturnType<typeof setInterval> | null = null

  const startPollingMyPending = () => {
    if (pollingTimer) return
    pollingTimer = setInterval(async () => {
      await api
        .get('/approval-document/my_pending/', {
          skipErrorInterceptor: true,
          hideProgress: true,
        } as any)
        .then(res => (pendingList.value = res.data))
        .catch(err => console.warn('Polling my_pending failed:', err?.message))
    }, 60000)
  }

  const stopPollingMyPending = () => {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  // ── 결재 완료(승인) 문서 목록 ─────────────────────────
  const approvedList = ref<ApprovalDocument[]>([])

  const fetchMyApproved = () =>
    api
      .get('/approval-document/my_approved/')
      .then(res => (approvedList.value = res.data))
      .catch(err => {
        console.warn('fetchMyApproved failed:', err?.message || err)
      })

  // ── 내가 참조된 문서 목록 ─────────────────────────────
  const observedList = ref<ApprovalDocument[]>([])

  const fetchMyObserved = () =>
    api
      .get('/approval-document/my_observed/')
      .then(res => (observedList.value = res.data))
      .catch(err => {
        console.warn('fetchMyObserved failed:', err?.message || err)
      })

  // ── 전사 결재 문서 (관리자 전용) ─────────────────────
  const allDocumentList = ref<ApprovalDocumentListItem[]>([])
  const allDocumentsCount = ref(0)

  const allDocumentPages = (itemsPerPage: number) =>
    Math.ceil(allDocumentsCount.value / itemsPerPage)

  const fetchAllDocuments = async (payload: AllDocFilter = {}) => {
    const params = new URLSearchParams()
    Object.entries(payload).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') params.append(k, String(v))
    })
    return await api
      .get(`/approval-document/all_documents/?${params}`)
      .then(res => {
        allDocumentList.value = res.data.results ?? res.data
        allDocumentsCount.value = res.data.count ?? allDocumentList.value.length
      })
      .catch(err => errorHandle(err.response.data))
  }

  // ── 결재 액션 ─────────────────────────────────────────
  const submitDocument = async (pk: number) => {
    try {
      const res = await api.post(`/approval-document/${pk}/submit/`)
      document.value = res.data
      await fetchMyDrafted()
      message()
      return res.data
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const actDocument = async (pk: number, payload: ApprovalActPayload) => {
    try {
      const res = await api.post(`/approval-document/${pk}/act/`, payload)
      await fetchMyPending()
      await fetchDocument(pk)
      message()
      return res.data
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const cancelDocument = async (pk: number) => {
    try {
      await api.post(`/approval-document/${pk}/cancel/`)
      await fetchMyDrafted()
      message()
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  // ── 결재 위임 (대결) ──────────────────────────────────
  const delegationList = ref<ApprovalDelegation[]>([])

  const fetchDelegationList = () =>
    api
      .get('/approval-delegation/')
      .then(res => (delegationList.value = res.data.results ?? res.data))
      .catch(err => errorHandle(err.response.data))

  const createDelegation = (payload: Partial<ApprovalDelegation>) =>
    api
      .post('/approval-delegation/', payload)
      .then(async () => {
        message()
        await fetchDelegationList()
      })
      .catch(err => errorHandle(err.response.data))

  const updateDelegation = (id: number, payload: Partial<ApprovalDelegation>) =>
    api
      .patch(`/approval-delegation/${id}/`, payload)
      .then(async () => {
        message()
        await fetchDelegationList()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteDelegation = (id: number) =>
    api
      .delete(`/approval-delegation/${id}/`)
      .then(async () => {
        message()
        await fetchDelegationList()
      })
      .catch(err => errorHandle(err.response.data))

  return {
    // state
    docCategoryList,
    docTypeList,
    forDraftDocTypeList,
    myAssignments,
    routePreview,
    document,
    documentList,
    documentCount,
    pendingList,
    draftedList,
    approvedList,
    observedList,
    allDocumentList,
    allDocumentsCount,
    allDocumentPages,
    delegationList,
    // actions
    fetchDocCategoryList,
    fetchDocTypeList,
    fetchForDraftDocTypeList,
    fetchMyAssignments,
    fetchRoutePreview,
    fetchDocumentList,
    fetchDocument,
    createDocument,
    updateDocument,
    deleteDocument,
    deleteAttachment,
    fetchMyPending,
    fetchMyDrafted,
    fetchMyApproved,
    fetchMyObserved,
    fetchAllDocuments,
    submitDocument,
    actDocument,
    cancelDocument,
    fetchDelegationList,
    createDelegation,
    updateDelegation,
    deleteDelegation,
    // polling
    startPollingMyPending,
    stopPollingMyPending,
  }
})
