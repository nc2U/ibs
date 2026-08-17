<template>
  <CRow>
    <CCol>
      <CCard class="mb-4">
        <CCardHeader class="d-flex align-items-center justify-content-between">
          <span>
            <CIcon icon="cil-check-circle" class="me-2" />
            결재 대기함
            <CBadge v-if="pendingList.length" color="danger" class="ms-2">
              {{ pendingList.length }}
            </CBadge>
          </span>
        </CCardHeader>
        <CCardBody>
          <CTable hover responsive>
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell style="width: 140px">문서 유형</CTableHeaderCell>
                <CTableHeaderCell>제목</CTableHeaderCell>
                <CTableHeaderCell style="width: 100px">기안자</CTableHeaderCell>
                <CTableHeaderCell style="width: 120px">상신일시</CTableHeaderCell>
                <CTableHeaderCell style="width: 80px">단계</CTableHeaderCell>
                <CTableHeaderCell style="width: 80px" class="text-center">처리</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow v-if="!pendingList.length">
                <CTableDataCell colspan="6" class="text-center text-medium-emphasis py-4">
                  결재 대기 중인 문서가 없습니다.
                </CTableDataCell>
              </CTableRow>
              <CTableRow
                v-for="doc in pendingList"
                :key="doc.id"
                class="cursor-pointer"
                @click="goDetail(doc.id)"
              >
                <CTableDataCell>
                  <CBadge color="primary" shape="rounded-pill">{{ doc.doc_type_name }}</CBadge>
                </CTableDataCell>
                <CTableDataCell class="fw-semibold">{{ doc.title }}</CTableDataCell>
                <CTableDataCell>{{ doc.drafter.full_name }}</CTableDataCell>
                <CTableDataCell class="text-medium-emphasis small">
                  {{ fmtDate(doc.submitted_at) }}
                </CTableDataCell>
                <CTableDataCell class="text-center">
                  <CBadge color="warning">{{ doc.current_step }}단계</CBadge>
                </CTableDataCell>
                <CTableDataCell class="text-center" @click.stop>
                  <CButton size="sm" color="success" variant="outline" @click="openActModal(doc)">
                    결재
                  </CButton>
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>

  <!-- 결재 처리 모달 -->
  <CModal :visible="showModal" alignment="center" @close="showModal = false">
    <CModalHeader>
      <CModalTitle>결재 처리</CModalTitle>
    </CModalHeader>
    <CModalBody v-if="selectedDoc">
      <p class="mb-1 text-medium-emphasis small">문서</p>
      <p class="fw-semibold mb-3">{{ selectedDoc.title }}</p>
      <CFormLabel>결재 의견 (선택)</CFormLabel>
      <CFormTextarea v-model="actComment" rows="3" placeholder="의견을 입력하세요." />
    </CModalBody>
    <CModalFooter>
      <CButton color="secondary" variant="outline" @click="showModal = false">닫기</CButton>
      <CButton color="danger" variant="outline" :disabled="acting" @click="doAct('rejected')">
        <CSpinner v-if="acting === 'rejected'" size="sm" class="me-1" />반려
      </CButton>
      <CButton color="success" :disabled="!!acting" @click="doAct('approved')">
        <CSpinner v-if="acting === 'approved'" size="sm" class="me-1" />승인
      </CButton>
    </CModalFooter>
  </CModal>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useApproval } from '@/store/pinia/approval'
import type { ApprovalDocument } from '@/store/types/approval'

const router = useRouter()
const store = useApproval()
const { pendingList, fetchMyPending, actDocument } = store

const showModal = ref(false)
const selectedDoc = ref<ApprovalDocument | null>(null)
const actComment = ref('')
const acting = ref<'approved' | 'rejected' | ''>('')

const fmtDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

const goDetail = (id: number) => router.push(`/approval/${id}`)

const openActModal = (doc: ApprovalDocument) => {
  selectedDoc.value = doc
  actComment.value = ''
  showModal.value = true
}

const doAct = async (action: 'approved' | 'rejected') => {
  if (!selectedDoc.value) return
  acting.value = action
  await actDocument(selectedDoc.value.id, { action, comment: actComment.value })
  acting.value = ''
  showModal.value = false
}

onMounted(fetchMyPending)
</script>
