<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval.ts'
import type { DocumentStatus } from '@/store/types/approval.ts'
import { CTable, CTableBody, CTableDataCell, CTableRow } from '@coreui/vue'

const router = useRouter()
const store = useApproval()
const { draftedList } = storeToRefs(store)
const { fetchMyDrafted, submitDocument, cancelDocument } = store

const searchText = ref('')
const statusFilter = ref<DocumentStatus | ''>('')
const showSubmitModal = ref(false)
const showCancelModal = ref(false)
const targetDocId = ref<number | null>(null)
const processing = ref(false)

const filteredList = computed(() =>
  draftedList.value.filter(doc => {
    const matchStatus = !statusFilter.value || doc.status === statusFilter.value
    const matchSearch =
      !searchText.value || doc.title.toLowerCase().includes(searchText.value.toLowerCase())
    return matchStatus && matchSearch
  }),
)

const statusLabel = (s: DocumentStatus) => {
  const m: Record<DocumentStatus, string> = {
    draft: '임시저장',
    pending: '결재중',
    approved: '승인완료',
    rejected: '반려',
    cancelled: '취소',
  }
  return m[s] ?? s
}

const statusColor = (s: DocumentStatus) => {
  const m: Record<DocumentStatus, string> = {
    draft: 'blue-grey-lighten-2',
    pending: 'warning',
    approved: 'success',
    rejected: 'error',
    cancelled: 'dark',
  }
  return m[s] ?? 'secondary'
}

const fmtDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR')
}

const confirmSubmit = (id: number) => {
  targetDocId.value = id
  showSubmitModal.value = true
}

const confirmCancel = (id: number) => {
  targetDocId.value = id
  showCancelModal.value = true
}

const doSubmit = async () => {
  if (!targetDocId.value) return
  processing.value = true
  await submitDocument(targetDocId.value)
  processing.value = false
  showSubmitModal.value = false
}

const doCancel = async () => {
  if (!targetDocId.value) return
  processing.value = true
  await cancelDocument(targetDocId.value)
  processing.value = false
  showCancelModal.value = false
}

const resetFilter = () => {
  searchText.value = ''
  statusFilter.value = ''
}

onMounted(fetchMyDrafted)
</script>

<template>
  <!-- 상단 액션바 -->
  <CRow class="mb-3">
    <CCol md="3">
      <CFormSelect v-model="statusFilter">
        <option value="">전체 상태</option>
        <option value="draft">임시저장</option>
        <option value="pending">결재중</option>
        <option value="approved">승인완료</option>
        <option value="rejected">반려</option>
        <option value="cancelled">취소</option>
      </CFormSelect>
    </CCol>
    <CCol md="4">
      <CInputGroup>
        <CFormInput v-model="searchText" placeholder="제목 검색..." />
        <v-btn color="light" variant="outlined" @click="resetFilter">
          <CIcon name="cilReload" />
        </v-btn>
      </CInputGroup>
    </CCol>
    <CCol class="d-flex align-items-center justify-content-between">
      <span class="text-muted small">
        총 <strong>{{ filteredList.length }}</strong>
        건
      </span>
      <v-btn color="primary" size="small" @click="router.push({ name: '기안 문서함 - 작성' })">
        <v-icon icon="mdi-plus" class="me-1" />새 기안
      </v-btn>
    </CCol>
  </CRow>

  <!-- 목록 테이블 -->
  <CTable hover bordered align="middle">
    <CTableHead color="light">
      <CTableRow>
        <CTableHeaderCell class="text-center" style="width: 130px">문서 유형</CTableHeaderCell>
        <CTableHeaderCell>제목</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 100px">상태</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 100px">단계</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 130px">기안일</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 130px">완료일</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 100px">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-if="!filteredList.length">
        <CTableDataCell colspan="7" class="text-center text-medium-emphasis py-5">
          <div class="mb-2" style="font-size: 2rem">📄</div>
          <div>기안한 문서가 없습니다.</div>
          <v-btn
            color="primary"
            size="small"
            class="mt-3"
            @click="router.push({ name: '기안 문서함 - 작성' })"
          >
            <v-icon icon="mdi-plus" class="me-1" />새 기안 작성
          </v-btn>
        </CTableDataCell>
      </CTableRow>
      <CTableRow
        v-for="doc in filteredList"
        :key="doc.id"
        style="cursor: pointer"
        @click="router.push({ name: '기안 문서함 - 보기', params: { docId: doc.id } })"
      >
        <CTableDataCell class="text-center">
          <v-chip color="primary" variant="elevated" size="x-small">{{ doc.doc_type_name }}</v-chip>
        </CTableDataCell>
        <CTableDataCell class="fw-semibold">{{ doc.title }}</CTableDataCell>
        <CTableDataCell class="text-center">
          <v-chip size="x-small" variant="elevated" :color="statusColor(doc.status)">{{
            statusLabel(doc.status)
          }}</v-chip>
        </CTableDataCell>
        <CTableDataCell class="text-center">
          <span v-if="doc.status === 'pending'">{{ doc.current_step }}단계</span>
          <span v-else class="text-medium-emphasis">-</span>
        </CTableDataCell>
        <CTableDataCell class="text-center text-medium-emphasis">
          {{ fmtDate(doc.created_at) }}
        </CTableDataCell>
        <CTableDataCell class="text-center text-medium-emphasis">
          {{ fmtDate(doc.completed_at) }}
        </CTableDataCell>
        <CTableDataCell class="text-center py-0" @click.stop>
          <CDropdown color="secondary" variant="input-group" placement="bottom-end">
            <CDropdownToggle
              :caret="true"
              color="secondary"
              variant="ghost"
              shape="rounded-pill"
              size="sm"
            >
              관리
            </CDropdownToggle>
            <CDropdownMenu>
              <CDropdownItem
                @click="router.push({ name: '기안 문서함 - 보기', params: { docId: doc.id } })"
              >
                상세 보기
              </CDropdownItem>
              <CDropdownItem
                v-if="doc.status === 'draft' || doc.status === 'rejected'"
                @click="router.push({ name: '기안 문서함 - 수정', params: { docId: doc.id } })"
              >
                수정
              </CDropdownItem>
              <CDropdownItem
                v-if="doc.status === 'draft' || doc.status === 'rejected'"
                @click="confirmSubmit(doc.id)"
              >
                상신
              </CDropdownItem>
              <CDropdownItem v-if="doc.pdf_url" :href="doc.pdf_url" target="_blank">
                PDF 다운로드
              </CDropdownItem>
              <template v-if="doc.status !== 'approved' && doc.status !== 'cancelled'">
                <CDropdownDivider />
                <CDropdownItem class="text-danger" @click="confirmCancel(doc.id)">
                  취소
                </CDropdownItem>
              </template>
            </CDropdownMenu>
          </CDropdown>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <!-- 상신 확인 모달 -->
  <CModal :visible="showSubmitModal" alignment="center" @close="showSubmitModal = false">
    <CModalHeader>
      <CModalTitle>결재 상신</CModalTitle>
    </CModalHeader>
    <CModalBody>
      <CAlert color="warning" class="mb-0">
        <strong>상신 후에는 문서를 수정할 수 없습니다.</strong><br />
        지정된 결재선으로 결재를 요청하시겠습니까?
      </CAlert>
    </CModalBody>
    <CModalFooter>
      <v-btn color="secondary" variant="outlined" @click="showSubmitModal = false">취소</v-btn>
      <v-btn color="primary" :disabled="processing" @click="doSubmit">
        <CSpinner v-if="processing" size="sm" class="me-1" />상신 확인
      </v-btn>
    </CModalFooter>
  </CModal>

  <!-- 취소 확인 모달 -->
  <CModal :visible="showCancelModal" alignment="center" @close="showCancelModal = false">
    <CModalHeader>
      <CModalTitle>결재 취소</CModalTitle>
    </CModalHeader>
    <CModalBody>
      <CAlert color="danger" class="mb-0">
        이 문서의 결재를 취소하시겠습니까?<br />
        <span class="small text-muted">취소된 문서는 다시 활성화할 수 없습니다.</span>
      </CAlert>
    </CModalBody>
    <CModalFooter>
      <v-btn color="secondary" variant="outlined" @click="showCancelModal = false">닫기</v-btn>
      <v-btn color="danger" :disabled="processing" @click="doCancel">
        <CSpinner v-if="processing" size="sm" class="me-1" />취소 확인
      </v-btn>
    </CModalFooter>
  </CModal>
</template>
