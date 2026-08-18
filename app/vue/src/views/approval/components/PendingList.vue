<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval.ts'
import type { ApprovalDocument } from '@/store/types/approval.ts'

const router = useRouter()
const store = useApproval()
const { pendingList } = storeToRefs(store)
const { fetchMyPending, actDocument } = store

const showModal = ref(false)
const selectedDoc = ref<ApprovalDocument | null>(null)
const actComment = ref('')
const acting = ref<'approved' | 'rejected' | ''>('')
const searchText = ref('')

const filteredList = computed(() => {
  if (!searchText.value) return pendingList.value
  const q = searchText.value.toLowerCase()
  return pendingList.value.filter(
    d => d.title.toLowerCase().includes(q) || (d.doc_type_name ?? '').toLowerCase().includes(q),
  )
})

const fmtDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const goDetail = (id: number) => router.push({ name: '결재 대기함 - 보기', params: { docId: id } })

const openActModal = (doc: ApprovalDocument) => {
  selectedDoc.value = doc
  actComment.value = ''
  showModal.value = true
}

const doAct = async (action: 'approved' | 'rejected') => {
  if (!selectedDoc.value) return
  if (action === 'rejected' && !actComment.value.trim()) {
    alert('반려 사유를 입력해 주세요.')
    return
  }
  acting.value = action
  await actDocument(selectedDoc.value.id, { action, comment: actComment.value })
  acting.value = ''
  showModal.value = false
}

onMounted(fetchMyPending)
</script>

<template>
  <!-- 상단 액션바: 검색 + 총 건수 -->
  <CRow class="mb-3">
    <CCol md="5">
      <CInputGroup>
        <CFormInput v-model="searchText" placeholder="제목 또는 문서 유형 검색..." />
        <CButton color="secondary" variant="outline" @click="searchText = ''">
          <CIcon name="cilReload" />
        </CButton>
      </CInputGroup>
    </CCol>
    <CCol class="d-flex align-items-center">
      <span class="text-muted small">
        대기 중
        <strong class="text-danger ms-1">{{ filteredList.length }}</strong>
        건
      </span>
    </CCol>
  </CRow>

  <!-- 목록 테이블 -->
  <CTable hover responsive bordered align="middle">
    <CTableHead color="light">
      <CTableRow>
        <CTableHeaderCell class="text-center" style="width: 130px">문서 유형</CTableHeaderCell>
        <CTableHeaderCell class="pl-3">제목</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 150px">기안자</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 200px">상신일시</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 90px">단계</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 150px">처리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-if="!filteredList.length">
        <CTableDataCell colspan="6" class="text-center text-medium-emphasis py-5">
          <div class="mb-2" style="font-size: 2rem">✅</div>
          <div>결재 대기 중인 문서가 없습니다.</div>
        </CTableDataCell>
      </CTableRow>
      <CTableRow
        v-for="doc in filteredList"
        :key="doc.id"
        style="cursor: pointer"
        @click="goDetail(doc.id)"
      >
        <CTableDataCell class="text-center">
          <v-chip color="primary" variant="elevated" size="x-small">{{ doc.doc_type_name }}</v-chip>
        </CTableDataCell>
        <CTableDataCell class="pl-3 fw-semibold">{{ doc.title }}</CTableDataCell>
        <CTableDataCell class="text-center">{{ doc.drafter.full_name }}</CTableDataCell>
        <CTableDataCell class="text-center text-medium-emphasis small">
          {{ fmtDate(doc.submitted_at) }}
        </CTableDataCell>
        <CTableDataCell class="text-center">
          <v-chip color="warning" variant="elevated" size="x-small">
            {{ doc.current_step }}단계
          </v-chip>
        </CTableDataCell>
        <CTableDataCell class="text-center" @click.stop>
          <v-btn size="x-small" color="info" class="me-1" @click="goDetail(doc.id)"> 보기 </v-btn>
          <v-btn size="x-small" color="success" @click="openActModal(doc)"> 결재 </v-btn>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <!-- 결재 처리 모달 -->
  <CModal size="lg" :visible="showModal" alignment="center" @close="showModal = false">
    <CModalHeader>
      <CModalTitle>
        <CIcon name="cilTask" class="me-2" />
        결재 처리
      </CModalTitle>
    </CModalHeader>
    <CModalBody v-if="selectedDoc">
      <!-- 문서 요약 정보 -->
      <CTable small bordered class="mb-3">
        <CTableBody>
          <CTableRow>
            <CTableHeaderCell class="light" style="width: 80px">유형</CTableHeaderCell>
            <CTableDataCell>
              <CBadge color="primary">{{ selectedDoc.doc_type_name }}</CBadge>
            </CTableDataCell>
            <CTableHeaderCell class="light" style="width: 80px">기안자</CTableHeaderCell>
            <CTableDataCell>{{ selectedDoc.drafter.full_name }}</CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell class="light">제목</CTableHeaderCell>
            <CTableDataCell colspan="3" class="fw-semibold">{{ selectedDoc.title }}</CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <CFormLabel class="fw-semibold">
        결재 의견
        <span class="fw-normal text-muted small ms-1">(반려 시 필수)</span>
      </CFormLabel>
      <CFormTextarea
        v-model="actComment"
        rows="4"
        placeholder="의견 또는 반려 사유를 입력하세요."
      />
    </CModalBody>
    <CModalFooter class="d-flex justify-content-between">
      <v-btn color="secondary" variant="outlined" @click="showModal = false">닫기</v-btn>
      <div class="d-flex gap-2">
        <v-btn color="success" :disabled="!!acting" @click="doAct('approved')">
          <CSpinner v-if="acting === 'approved'" size="sm" class="me-1" />
          <span v-else class="mr-2">✓</span>
          승인
        </v-btn>
        <v-btn color="error" variant="outlined" :disabled="!!acting" @click="doAct('rejected')">
          <CSpinner v-if="acting === 'rejected'" size="sm" class="me-1" />
          <span v-else class="mr-2">✗</span>
          반려
        </v-btn>
      </div>
    </CModalFooter>
  </CModal>
</template>
