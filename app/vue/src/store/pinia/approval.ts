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
      .catch(err => errorHandle(err.response.data))

  // ── 문서 유형 ─────────────────────────────────────────
  const docTypeList = ref<DocumentType[]>([])
  const forDraftDocTypeList = ref<DocumentType[]>([])

  const fetchDocTypeList = (categoryId?: number | null) => {
    const params = new URLSearchParams()
    if (categoryId) params.append('category_id', String(categoryId))
    return api
      .get(`/approval-doc-type/?${params}`)
      .then(res => (docTypeList.value = res.data.results ?? res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchForDraftDocTypeList = (assignmentId?: number | null) => {
    const params = new URLSearchParams()
    if (assignmentId) params.append('assignment', String(assignmentId))
    return api
      .get(`/approval-doc-type/for_draft/?${params}`)
      .then(res => (forDraftDocTypeList.value = res.data.results ?? res.data))
      .catch(err => errorHandle(err.response.data))
  }

  // ── 기안자의 보직 목록 ─────────────────────────────────
  const myAssignments = ref<StaffAssignmentItem[]>([])

  const fetchMyAssignments = () =>
    api
      .get('/approval-document/my_assignments/')
      .then(res => (myAssignments.value = res.data.results ?? res.data))
      .catch(err => errorHandle(err.response.data))

  // ── 동적 결재선 미리보기 ───────────────────────────────
  const routePreview = ref<RoutePreviewStep[]>([])

  const fetchRoutePreview = (docTypeId: number, assignmentId?: number | null, amount?: number | string | null) => {
    const params = new URLSearchParams({ doc_type: String(docTypeId) })
    if (assignmentId) params.append('assignment', String(assignmentId))
    if (amount !== undefined && amount !== null && amount !== '') params.append('amount', String(amount))
    return api
      .get(`/approval-document/preview_route/?${params}`)
      .then(res => (routePreview.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  // ── 결재 문서 ─────────────────────────────────────────
  const document = ref<ApprovalDocument | null>(null)
  const documentList = ref<ApprovalDocument[]>([])
  const documentCount = ref(0)

  const fetchDocumentList = (payload: DocFilter = {}) => {
    const params = new URLSearchParams()
    Object.entries(payload).forEach(([k, v]) => {
      if (v !== undefined && v !== '') params.append(k, String(v))
    })
    return api
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
      const headers = payload instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
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
      const headers = payload instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
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
      .catch(err => errorHandle(err.response.data))

  const fetchMyDrafted = () =>
    api
      .get('/approval-document/my_drafted/')
      .then(res => (draftedList.value = res.data))
      .catch(err => errorHandle(err.response.data))

  // ── 결재 완료(승인) 문서 목록 ─────────────────────────
  const approvedList = ref<ApprovalDocument[]>([])

  const fetchMyApproved = () =>
    api
      .get('/approval-document/my_approved/')
      .then(res => (approvedList.value = res.data))
      .catch(err => errorHandle(err.response.data))

  // ── 내가 참조된 문서 목록 ─────────────────────────────
  const observedList = ref<ApprovalDocument[]>([])

  const fetchMyObserved = () =>
    api
      .get('/approval-document/my_observed/')
      .then(res => (observedList.value = res.data))
      .catch(err => errorHandle(err.response.data))

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
    submitDocument,
    actDocument,
    cancelDocument,
  }
})
