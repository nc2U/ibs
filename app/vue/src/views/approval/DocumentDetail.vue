<template>
  <CRow class="justify-content-center">
    <CCol lg="9" v-if="document">
      <!-- 헤더 -->
      <CCard class="mb-3">
        <CCardHeader class="d-flex align-items-center justify-content-between">
          <span>
            <CBadge :color="statusColor(document.status)" class="me-2 fs-6">
              {{ statusLabel(document.status) }}
            </CBadge>
            {{ document.title }}
          </span>
          <div class="d-flex gap-2">
            <CButton
              v-if="document.pdf_url"
              color="secondary"
              variant="outline"
              size="sm"
              :href="document.pdf_url"
              target="_blank"
            >
              <CIcon icon="cil-cloud-download" class="me-1" />PDF
            </CButton>
            <CButton
              v-if="isMyDoc && (document.status === 'draft' || document.status === 'rejected')"
              color="primary"
              variant="outline"
              size="sm"
              @click="router.push(`/approval/${document.id}/edit`)"
            >
              수정
            </CButton>
            <CButton
              v-if="isMyDoc && (document.status === 'draft' || document.status === 'rejected')"
              color="primary"
              size="sm"
              @click="confirmSubmit"
            >
              상신
            </CButton>
            <CButton color="secondary" variant="ghost" size="sm" @click="router.back()">
              목록
            </CButton>
          </div>
        </CCardHeader>

        <!-- 문서 기본 정보 -->
        <CCardBody>
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="bg-light" style="width: 120px">문서 번호</CTableHeaderCell>
                <CTableDataCell>{{ document.doc_number || '-' }}</CTableDataCell>
                <CTableHeaderCell class="bg-light" style="width: 120px">문서 유형</CTableHeaderCell>
                <CTableDataCell>{{ document.doc_type_detail?.name }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="bg-light">기안자</CTableHeaderCell>
                <CTableDataCell>{{ document.drafter?.full_name }}</CTableDataCell>
                <CTableHeaderCell class="bg-light">기안일시</CTableHeaderCell>
                <CTableDataCell>{{ fmtDatetime(document.created_at) }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="bg-light">상신일시</CTableHeaderCell>
                <CTableDataCell>{{ fmtDatetime(document.submitted_at) }}</CTableDataCell>
                <CTableHeaderCell class="bg-light">완료일시</CTableHeaderCell>
                <CTableDataCell>{{ fmtDatetime(document.completed_at) }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CCardBody>
      </CCard>

      <!-- 결재 내용 -->
      <CCard class="mb-3">
        <CCardHeader><strong>결재 내용</strong></CCardHeader>
        <CCardBody>
          <template v-if="document.doc_type_detail?.form_schema?.length">
            <CTable small bordered responsive class="mb-0">
              <CTableBody>
                <CTableRow
                  v-for="field in document.doc_type_detail.form_schema"
                  :key="field.key"
                >
                  <CTableHeaderCell class="bg-light" style="width: 130px">
                    {{ field.label }}
                  </CTableHeaderCell>
                  <CTableDataCell style="white-space: pre-wrap">
                    {{ document.content[field.key] || '-' }}
                  </CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </template>
          <pre v-else class="mb-0">{{ JSON.stringify(document.content, null, 2) }}</pre>
        </CCardBody>
      </CCard>

      <!-- 결재선 진행 현황 -->
      <CCard class="mb-3">
        <CCardHeader><strong>결재선 현황</strong></CCardHeader>
        <CCardBody>
          <div class="d-flex flex-column gap-3">
            <div
              v-for="step in document.steps"
              :key="step.id"
              class="border rounded p-3"
              :class="{
                'border-success bg-success-subtle': step.status === 'approved',
                'border-danger bg-danger-subtle': step.status === 'rejected',
                'border-warning bg-warning-subtle': step.status === 'pending' && document.current_step === step.step_order,
              }"
            >
              <div class="d-flex align-items-center justify-content-between mb-2">
                <div>
                  <CBadge color="secondary" class="me-2">{{ step.step_order }}단계</CBadge>
                  <strong>{{ step.role_label }}</strong>
                  <CBadge :color="step.condition === 'AND' ? 'primary' : 'info'" size="sm" class="ms-2">
                    {{ step.condition === 'AND' ? '전원 승인' : '1인 승인' }}
                  </CBadge>
                </div>
                <CBadge :color="stepBadgeColor(step.status)">{{ stepStatusLabel(step.status) }}</CBadge>
              </div>

              <!-- 결재자별 처리 현황 -->
              <div class="d-flex flex-wrap gap-2 mt-2">
                <div
                  v-for="approver in step.approvers"
                  :key="approver.id"
                  class="border rounded px-3 py-2 bg-white text-center"
                  style="min-width: 120px"
                >
                  <div class="fw-semibold small">{{ approver.full_name }}</div>
                  <template v-if="getAction(step, approver.id)">
                    <CBadge
                      :color="getAction(step, approver.id)!.action === 'approved' ? 'success' : 'danger'"
                      class="mt-1"
                    >
                      {{ getAction(step, approver.id)!.action === 'approved' ? '승인' : '반려' }}
                    </CBadge>
                    <div class="text-muted mt-1" style="font-size:0.72rem">
                      {{ fmtDatetime(getAction(step, approver.id)!.acted_at) }}
                    </div>
                    <div v-if="getAction(step, approver.id)!.comment" class="text-danger small mt-1">
                      {{ getAction(step, approver.id)!.comment }}
                    </div>
                  </template>
                  <CBadge v-else color="secondary" class="mt-1">대기</CBadge>

                  <!-- 현재 단계 결재자이고, 내가 해당 결재자인 경우 버튼 표시 -->
                  <div
                    v-if="canAct(step, approver.id)"
                    class="d-flex gap-1 justify-content-center mt-2"
                  >
                    <CButton size="sm" color="success" @click="openActModal('approved')">승인</CButton>
                    <CButton size="sm" color="danger" variant="outline" @click="openActModal('rejected')">반려</CButton>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CCardBody>
      </CCard>
    </CCol>

    <CCol lg="9" v-else class="text-center py-5">
      <CSpinner />
    </CCol>
  </CRow>

  <!-- 결재 처리 모달 -->
  <CModal :visible="showModal" alignment="center" @close="showModal = false">
    <CModalHeader>
      <CModalTitle>{{ pendingAction === 'approved' ? '✅ 승인' : '❌ 반려' }}</CModalTitle>
    </CModalHeader>
    <CModalBody>
      <CFormLabel>의견 {{ pendingAction === 'rejected' ? '(반려 사유 필수)' : '(선택)' }}</CFormLabel>
      <CFormTextarea
        v-model="actComment"
        rows="3"
        :placeholder="pendingAction === 'rejected' ? '반려 사유를 입력하세요.' : '의견을 입력하세요. (선택)'"
      />
    </CModalBody>
    <CModalFooter>
      <CButton color="secondary" variant="outline" @click="showModal = false">닫기</CButton>
      <CButton
        :color="pendingAction === 'approved' ? 'success' : 'danger'"
        :disabled="acting"
        @click="doAct"
      >
        <CSpinner v-if="acting" size="sm" class="me-1" />
        {{ pendingAction === 'approved' ? '승인 확인' : '반려 확인' }}
      </CButton>
    </CModalFooter>
  </CModal>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApproval } from '@/store/pinia/approval'
import { useAccount } from '@/store/pinia/account'
import type { ApprovalStep, ApprovalActionRecord, DocumentStatus, StepStatus, ApprovalActionType } from '@/store/types/approval'

const route = useRoute()
const router = useRouter()
const approvalStore = useApproval()
const accountStore = useAccount()

const { document, fetchDocument, submitDocument, actDocument } = approvalStore
const myUser = computed(() => accountStore.userInfo)

const docId = computed(() => Number(route.params.docId))
const isMyDoc = computed(() => document?.drafter?.id === myUser.value?.pk)

const showModal = ref(false)
const pendingAction = ref<ApprovalActionType>('approved')
const actComment = ref('')
const acting = ref(false)

const fmtDatetime = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

const statusLabel = (s: DocumentStatus) => {
  const m: Record<DocumentStatus, string> = {
    draft: '임시저장', pending: '결재중', approved: '최종승인', rejected: '반려', cancelled: '취소',
  }
  return m[s] ?? s
}

const statusColor = (s: DocumentStatus) => {
  const m: Record<DocumentStatus, string> = {
    draft: 'secondary', pending: 'warning', approved: 'success', rejected: 'danger', cancelled: 'dark',
  }
  return m[s] ?? 'secondary'
}

const stepStatusLabel = (s: StepStatus) => {
  const m: Record<StepStatus, string> = { pending: '대기', approved: '승인', rejected: '반려', skipped: '건너뜀' }
  return m[s] ?? s
}

const stepBadgeColor = (s: StepStatus) => {
  const m: Record<StepStatus, string> = { pending: 'warning', approved: 'success', rejected: 'danger', skipped: 'secondary' }
  return m[s] ?? 'secondary'
}

const getAction = (step: ApprovalStep, userId: number): ApprovalActionRecord | undefined =>
  step.actions.find(a => a.approver.id === userId)

const canAct = (step: ApprovalStep, approverId: number) => {
  if (!document || document.status !== 'pending') return false
  if (document.current_step !== step.step_order) return false
  if (approverId !== myUser.value?.pk) return false
  return !getAction(step, approverId)
}

const openActModal = (action: ApprovalActionType) => {
  pendingAction.value = action
  actComment.value = ''
  showModal.value = true
}

const doAct = async () => {
  if (pendingAction.value === 'rejected' && !actComment.value.trim()) {
    alert('반려 사유를 입력해 주세요.')
    return
  }
  acting.value = true
  await actDocument(docId.value, { action: pendingAction.value, comment: actComment.value })
  acting.value = false
  showModal.value = false
}

const confirmSubmit = async () => {
  if (confirm('상신하시겠습니까? 상신 후에는 수정할 수 없습니다.')) {
    await submitDocument(docId.value)
    await fetchDocument(docId.value)
  }
}

onMounted(() => fetchDocument(docId.value))
</script>
