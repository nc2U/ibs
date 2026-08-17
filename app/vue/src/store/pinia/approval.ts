import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import type {
  DocumentType,
  ApprovalDocument,
  PatchApprovalDocument,
  ApprovalActPayload,
} from '@/store/types/approval'

export type DocFilter = {
  status?: string
  doc_type?: string
  drafter?: string
  page?: number
}

export const useApproval = defineStore('approval', () => {
  // ── 문서 유형 ─────────────────────────────────────────
  const docTypeList = ref<DocumentType[]>([])

  const fetchDocTypeList = () =>
    api
      .get('/approval-doc-type/')
      .then(res => (docTypeList.value = res.data.results ?? res.data))
      .catch(err => errorHandle(err.response.data))

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

  const createDocument = async (payload: PatchApprovalDocument) => {
    try {
      const res = await api.post('/approval-document/', payload)
      document.value = res.data
      await fetchMyDrafted()
      message()
      return res.data as ApprovalDocument
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const updateDocument = async (pk: number, payload: PatchApprovalDocument) => {
    try {
      const res = await api.patch(`/approval-document/${pk}/`, payload)
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
    docTypeList,
    document,
    documentList,
    documentCount,
    pendingList,
    draftedList,
    // actions
    fetchDocTypeList,
    fetchDocumentList,
    fetchDocument,
    createDocument,
    updateDocument,
    deleteDocument,
    fetchMyPending,
    fetchMyDrafted,
    submitDocument,
    actDocument,
    cancelDocument,
  }
})
