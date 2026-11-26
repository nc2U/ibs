<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval'
import type { ApprovalDocumentListItem } from '@/store/types/approval'
import { TableSecondary } from '@/utils/cssMixins'
import { message } from '@/utils/helper'
import { fmtDatetime, getUserDisplayName } from '../utils/approvalMeta'

const router = useRouter()
const store = useApproval()
const { pendingList } = storeToRefs(store)
const { fetchMyPending, actDocument } = store

// 단건 결재 모달 상태
const showModal = ref(false)
const selectedDoc = ref<ApprovalDocumentListItem | null>(null)
const actComment = ref('')
const acting = ref<'approved' | 'rejected' | ''>('')
const searchText = ref('')

// ── 다건 일괄 승인(Batch Action) 상태 ──
const selectedDocIds = ref<number[]>([])
const showBatchModal = ref(false)
const batchComment = ref('')
const isBatchProcessing = ref(false)
const batchProgress = ref({ current: 0, total: 0 })

watch(pendingList, list => {
  const validIds = new Set(list.map(d => d.id))
  const next = selectedDocIds.value.filter(id => validIds.has(id))
  if (next.length !== selectedDocIds.value.length) {
    selectedDocIds.value = next
  }
})

const filteredList = computed(() => {
  if (!searchText.value) return pendingList.value
  const q = searchText.value.toLowerCase()
  return pendingList.value.filter(
    d =>
      d.title.toLowerCase().includes(q) ||
      (d.doc_type_name ?? '').toLowerCase().includes(q) ||
      (d.doc_number ?? '').toLowerCase().includes(q) ||
      getUserDisplayName(d.drafter).toLowerCase().includes(q),
  )
})

// 전체 선택 관련 계산
const isAllSelected = computed(() => {
  return (
    filteredList.value.length > 0 &&
    filteredList.value.every(d => selectedDocIds.value.includes(d.id))
  )
})

const isIndeterminate = computed(() => {
  const selectedInFiltered = filteredList.value.filter(d => selectedDocIds.value.includes(d.id))
  return selectedInFiltered.length > 0 && selectedInFiltered.length < filteredList.value.length
})

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    const visibleIds = new Set(filteredList.value.map(d => d.id))
    selectedDocIds.value = selectedDocIds.value.filter(id => !visibleIds.has(id))
  } else {
    const merged = new Set([...selectedDocIds.value, ...filteredList.value.map(d => d.id)])
    selectedDocIds.value = Array.from(merged)
  }
}

const toggleSelect = (id: number) => {
  const idx = selectedDocIds.value.indexOf(id)
  if (idx > -1) {
    selectedDocIds.value.splice(idx, 1)
  } else {
    selectedDocIds.value.push(id)
  }
}

const selectedDocuments = computed(() => {
  return pendingList.value.filter(d => selectedDocIds.value.includes(d.id))
})

const goDetail = (id: number) => router.push({ name: '결재 대기함 - 보기', params: { docId: id } })

const openActModal = (doc: ApprovalDocumentListItem) => {
  selectedDoc.value = doc
  actComment.value = ''
  showModal.value = true
}

const doAct = async (action: 'approved' | 'rejected') => {
  if (!selectedDoc.value) return
  if (action === 'rejected' && !actComment.value.trim()) {
    message('warning', '입력 확인', '반려 사유를 입력해 주세요.')
    return
  }
  acting.value = action
  try {
    const res = await actDocument(selectedDoc.value.id, { action, comment: actComment.value })
    if (res) {
      showModal.value = false
      const idx = selectedDocIds.value.indexOf(selectedDoc.value.id)
      if (idx > -1) selectedDocIds.value.splice(idx, 1)
    }
  } finally {
    acting.value = ''
  }
}

// ── 다건 일괄 승인 실행 ──
const openBatchModal = () => {
  if (!selectedDocIds.value.length) return
  batchComment.value = ''
  showBatchModal.value = true
}

const executeBatchApprove = async () => {
  const validTargets = selectedDocuments.value.map(d => d.id)
  if (!validTargets.length || isBatchProcessing.value) return

  isBatchProcessing.value = true
  batchProgress.value = { current: 0, total: validTargets.length }

  const succeededIds = new Set<number>()
  let failCount = 0

  for (const docId of validTargets) {
    const res = await actDocument(
      docId,
      {
        action: 'approved',
        comment: batchComment.value.trim() || undefined,
      },
      { skipRefresh: true },
    )
    if (res) {
      succeededIds.add(docId)
    } else {
      failCount++
    }
    batchProgress.value.current++
  }

  isBatchProcessing.value = false
  showBatchModal.value = false
  selectedDocIds.value = selectedDocIds.value.filter(id => !succeededIds.has(id))

  await fetchMyPending()

  if (failCount === 0) {
    message('success', '일괄 승인 완료', `선택한 ${succeededIds.size}건의 문서가 모두 정상 승인되었습니다.`)
  } else {
    message(
      'warning',
      '일괄 승인 결과',
      `총 ${succeededIds.size}건 승인 완료 (실패 ${failCount}건)`,
      6000,
    )
  }
}

onMounted(fetchMyPending)
</script>

<template>
  <!-- 상단 액션바: 검색 + 총 건수 + 일괄 승인 버튼 -->
  <CRow class="mb-3 align-items-center">
    <CCol md="5">
      <CInputGroup>
        <CInputGroupText class="bg-more-light">
          <v-icon icon="mdi-magnify" size="small" />
        </CInputGroupText>
        <CFormInput v-model="searchText" placeholder="제목, 문서 유형, 기안자, 문서번호 검색..." />
        <CButton
          v-if="searchText"
          color="light"
          type="button"
          title="검색어 초기화"
          @click="searchText = ''"
        >
          <v-icon icon="mdi-close" size="small" />
        </CButton>
      </CInputGroup>
    </CCol>
    <CCol md="3" class="d-flex align-items-center">
      <span class="text-muted small">
        대기 중
        <strong class="text-danger ms-1">{{ filteredList.length }}</strong>
        건
        <template v-if="selectedDocIds.length">
          (선택: <strong class="text-primary">{{ selectedDocIds.length }}</strong
          >건)
        </template>
      </span>
    </CCol>
    <CCol md="4" class="text-end">
      <v-btn
        v-if="selectedDocIds.length"
        color="success"
        size="small"
        prepend-icon="mdi-checkbox-multiple-marked-circle-outline"
        @click="openBatchModal"
      >
        선택 문서 일괄 승인 ({{ selectedDocIds.length }}건)
      </v-btn>
    </CCol>
  </CRow>

  <!-- 목록 테이블 -->
  <CTable hover responsive bordered align="middle">
    <CTableHead :color="TableSecondary">
      <CTableRow>
        <CTableHeaderCell class="text-center" style="width: 45px">
          <input
            type="checkbox"
            class="form-check-input"
            :checked="isAllSelected"
            :indeterminate.prop="isIndeterminate"
            aria-label="전체 선택 또는 해제"
            title="전체 선택/해제"
            @change="toggleSelectAll"
          />
        </CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 130px">문서 유형</CTableHeaderCell>
        <CTableHeaderCell class="ps-3">제목</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 150px">기안자</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 180px">상신일시</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 80px">단계</CTableHeaderCell>
        <CTableHeaderCell class="text-center" style="width: 140px">처리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-if="!filteredList.length">
        <CTableDataCell colspan="7" class="text-center text-medium-emphasis py-5">
          <div class="mb-2" style="font-size: 2rem">✅</div>
          <div>결재 대기 중인 문서가 없습니다.</div>
        </CTableDataCell>
      </CTableRow>
      <CTableRow
        v-for="doc in filteredList"
        :key="doc.id"
        style="cursor: pointer"
        :color="selectedDocIds.includes(doc.id) ? 'success' : undefined"
        class="table-row-item"
        @click="goDetail(doc.id)"
      >
        <CTableDataCell class="text-center" @click.stop>
          <input
            type="checkbox"
            class="form-check-input"
            :checked="selectedDocIds.includes(doc.id)"
            :aria-label="`${doc.title} 선택`"
            @change="toggleSelect(doc.id)"
          />
        </CTableDataCell>
        <CTableDataCell class="text-center">
          <v-chip color="primary" variant="elevated" size="x-small">{{ doc.doc_type_name }}</v-chip>
        </CTableDataCell>
        <CTableDataCell class="ps-3 fw-semibold">{{ doc.title }}</CTableDataCell>
        <CTableDataCell class="text-center">
          {{ getUserDisplayName(doc.drafter) }}
        </CTableDataCell>
        <CTableDataCell class="text-center text-medium-emphasis small">
          {{ fmtDatetime(doc.submitted_at) }}
        </CTableDataCell>
        <CTableDataCell class="text-center">
          <v-chip color="success" variant="flat" size="x-small" class="fw-bold">
            🟢 내 승인 차례 ({{ doc.current_step }}단계)
          </v-chip>
        </CTableDataCell>
        <CTableDataCell class="text-center" @click.stop>
          <v-btn size="x-small" color="info" class="me-1" @click="goDetail(doc.id)"> 보기 </v-btn>
          <v-btn size="x-small" color="success" @click="openActModal(doc)"> 결재 </v-btn>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <!-- 단건 결재 처리 모달 -->
  <CModal
    size="lg"
    :visible="showModal"
    alignment="center"
    backdrop="static"
    @close="!acting && (showModal = false)"
  >
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
            <CTableHeaderCell class="bg-more-light" style="width: 80px">유형</CTableHeaderCell>
            <CTableDataCell>
              <v-chip color="info" variant="flat" size="x-small">
                {{ selectedDoc.doc_type_name }}
              </v-chip>
            </CTableDataCell>
            <CTableHeaderCell class="bg-more-light" style="width: 80px">기안자</CTableHeaderCell>
            <CTableDataCell>
              {{ getUserDisplayName(selectedDoc.drafter) }}
            </CTableDataCell>
          </CTableRow>
          <CTableRow>
            <CTableHeaderCell class="bg-more-light">제목</CTableHeaderCell>
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
      <v-btn color="secondary" variant="outlined" :disabled="!!acting" @click="showModal = false">
        닫기
      </v-btn>
      <div class="d-flex gap-2">
        <v-btn color="success" :disabled="!!acting" @click="doAct('approved')">
          <CSpinner v-if="acting === 'approved'" size="sm" class="me-1" />
          <span v-else class="me-2">✓</span>
          승인
        </v-btn>
        <v-btn color="error" variant="outlined" :disabled="!!acting" @click="doAct('rejected')">
          <CSpinner v-if="acting === 'rejected'" size="sm" class="me-1" />
          <span v-else class="me-2">✗</span>
          반려
        </v-btn>
      </div>
    </CModalFooter>
  </CModal>

  <!-- 다건 일괄 승인 확인 모달 -->
  <CModal
    size="lg"
    :visible="showBatchModal"
    alignment="center"
    backdrop="static"
    @close="!isBatchProcessing && (showBatchModal = false)"
  >
    <CModalHeader>
      <CModalTitle class="d-flex align-items-center">
        <v-icon icon="mdi-checkbox-multiple-marked-circle" color="success" class="me-2" />
        선택 문서 일괄 승인 확인
      </CModalTitle>
    </CModalHeader>
    <CModalBody>
      <CAlert color="info" class="d-flex align-items-center mb-3 py-2">
        <div>
          선택하신 <strong>{{ selectedDocIds.length }}건</strong>의 결재 대기 문서를 일괄
          승인합니다.
          <div class="small text-medium-emphasis mt-1">
            승인된 문서는 다음 결재 단계로 이동하거나 최종 승인 완료 처리됩니다.
          </div>
        </div>
      </CAlert>

      <!-- 선택된 문서 목록 미리보기 -->
      <div class="mb-3">
        <label class="fw-semibold small text-muted mb-1">선택된 결재 대상 문서 목록:</label>
        <div class="border rounded p-2 bg-more-light" style="max-height: 180px; overflow-y: auto">
          <div
            v-for="(doc, idx) in selectedDocuments"
            :key="doc.id"
            class="d-flex justify-content-between align-items-center py-1 border-bottom"
            :class="{ 'border-bottom-0': idx === selectedDocuments.length - 1 }"
          >
            <div class="text-truncate me-2">
              <v-chip size="x-small" color="primary" variant="outlined" class="me-1">
                {{ doc.doc_type_name }}
              </v-chip>
              <span class="small fw-semibold">{{ doc.title }}</span>
            </div>
            <span class="small text-muted text-nowrap">
              기안자: {{ getUserDisplayName(doc.drafter) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 공통 결재 의견 입력란 -->
      <div class="mb-3">
        <CFormLabel class="fw-semibold small">
          공통 결재 의견
          <span class="text-muted fw-normal"
            >(선택 사항, 입력 시 모든 문서의 결재 이력에 공통 기록됩니다)</span
          >
        </CFormLabel>
        <CFormTextarea
          v-model="batchComment"
          rows="3"
          :disabled="isBatchProcessing"
          placeholder="예: 일괄 확인 및 승인합니다."
        />
      </div>

      <!-- 진행률 표시 (처리 중일 때) -->
      <div v-if="isBatchProcessing" class="mt-3">
        <div class="d-flex justify-content-between small text-muted mb-1">
          <span>일괄 승인 진행 중...</span>
          <span>{{ batchProgress.current }} / {{ batchProgress.total }}</span>
        </div>
        <CProgress
          :value="(batchProgress.current / batchProgress.total) * 100"
          color="success"
          animated
        />
      </div>
    </CModalBody>
    <CModalFooter class="d-flex justify-content-between">
      <v-btn
        color="secondary"
        variant="outlined"
        :disabled="isBatchProcessing"
        @click="showBatchModal = false"
      >
        취소
      </v-btn>
      <v-btn
        color="success"
        prepend-icon="mdi-check-all"
        :loading="isBatchProcessing"
        :disabled="isBatchProcessing || !selectedDocIds.length"
        @click="executeBatchApprove"
      >
        일괄 승인 실행 ({{ selectedDocIds.length }}건)
      </v-btn>
    </CModalFooter>
  </CModal>
</template>

<style scoped>
.table-row-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}
</style>
