<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval.ts'
import { useAccount } from '@/store/pinia/account.ts'
import type {
  ApprovalStep,
  ApprovalActionRecord,
  DocumentStatus,
  StepStatus,
  ApprovalActionType,
} from '@/store/types/approval.ts'

const route = useRoute()
const router = useRouter()
const approvalStore = useApproval()
const accountStore = useAccount()

const { document } = storeToRefs(approvalStore)
const { fetchDocument, submitDocument, actDocument } = approvalStore
const myUser = computed(() => accountStore.userInfo)

const docId = computed(() => Number(route.params.docId))
const isMyDoc = computed(() => document.value?.drafter?.id === myUser.value?.pk)
const canSubmit = computed(
  () =>
    isMyDoc.value && (document.value?.status === 'draft' || document.value?.status === 'rejected'),
)

const showModal = ref(false)
const pendingAction = ref<ApprovalActionType>('approved')
const actComment = ref('')
const acting = ref(false)
const submitting = ref(false)

const fmtDatetime = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const STATUS_LABEL: Record<DocumentStatus, string> = {
  draft: '임시저장',
  pending: '결재중',
  approved: '최종승인',
  rejected: '반려',
  cancelled: '취소',
}
const STATUS_COLOR: Record<DocumentStatus, string> = {
  draft: 'secondary',
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  cancelled: 'dark',
}
const STEP_STATUS_LABEL: Record<StepStatus, string> = {
  pending: '대기',
  approved: '승인',
  rejected: '반려',
  skipped: '건너뜀',
}
const STEP_STATUS_COLOR: Record<StepStatus, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  skipped: 'secondary',
}

const getAction = (step: ApprovalStep, userId: number): ApprovalActionRecord | undefined =>
  step.actions.find(a => a.approver.id === userId)

const canAct = (step: ApprovalStep, approverId: number) => {
  if (!document.value || document.value.status !== 'pending') return false
  if (document.value.current_step !== step.step_order) return false
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
  submitting.value = true
  await submitDocument(docId.value)
  await fetchDocument(docId.value)
  submitting.value = false
}

// 결재선 진행률 계산
const progressPercent = computed(() => {
  const steps = document.value?.steps
  if (!steps?.length) return 0
  const done = steps.filter(s => s.status === 'approved').length
  return Math.round((done / steps.length) * 100)
})

onMounted(() => fetchDocument(docId.value))
</script>

<template>
  <!-- 로딩 스켈레톤 -->
  <div v-if="!document" class="text-center py-5">
    <CSpinner color="primary" />
    <p class="mt-2 text-muted">문서를 불러오는 중...</p>
  </div>

  <template v-else>
    <!-- ① 헤더 카드 -->
    <CCard class="mb-3">
      <CCardHeader class="d-flex align-items-start justify-content-between flex-wrap gap-2">
        <div>
          <CBadge :color="STATUS_COLOR[document.status]" class="me-2">
            {{ STATUS_LABEL[document.status] }}
          </CBadge>
          <span class="fw-semibold fs-5">{{ document.title }}</span>
        </div>
        <div class="d-flex gap-2 flex-wrap">
          <CButton
            v-if="document.pdf_url"
            color="secondary"
            variant="outline"
            size="sm"
            :href="document.pdf_url"
            target="_blank"
          >
            <CIcon name="cilCloudDownload" class="me-1" />PDF
          </CButton>
          <CButton
            v-if="canSubmit"
            color="secondary"
            variant="outline"
            size="sm"
            @click="router.push({ name: '기안 문서 - 수정', params: { docId: document.id } })"
          >
            수정
          </CButton>
          <CButton
            v-if="canSubmit"
            color="primary"
            size="sm"
            :disabled="submitting"
            @click="confirmSubmit"
          >
            <CSpinner v-if="submitting" size="sm" class="me-1" />
            상신
          </CButton>
          <CButton color="secondary" variant="ghost" size="sm" @click="router.back()">
            목록
          </CButton>
        </div>
      </CCardHeader>

      <!-- 기본 정보 -->
      <CCardBody class="pb-2">
        <CTable small bordered responsive class="mb-0">
          <CTableBody>
            <CTableRow>
              <CTableHeaderCell class="bg-light" style="width: 100px">문서 번호</CTableHeaderCell>
              <CTableDataCell class="fw-semibold text-primary">{{
                document.doc_number || '(상신 후 채번)'
              }}</CTableDataCell>
              <CTableHeaderCell class="bg-light" style="width: 100px">문서 유형</CTableHeaderCell>
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

    <!-- ② 결재 내용 -->
    <CCard class="mb-3">
      <CCardHeader>
        <strong>결재 내용</strong>
      </CCardHeader>
      <CCardBody>
        <template v-if="document.doc_type_detail?.form_schema?.length">
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow v-for="field in document.doc_type_detail.form_schema" :key="field.key">
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
        <pre v-else class="mb-0 text-muted small">{{
          JSON.stringify(document.content, null, 2)
        }}</pre>
      </CCardBody>
    </CCard>

    <!-- ③ 결재선 현황 (타임라인 스타일) -->
    <CCard class="mb-3">
      <CCardHeader class="d-flex align-items-center justify-content-between">
        <strong>결재선 현황</strong>
        <div v-if="document.steps?.length" class="d-flex align-items-center gap-2">
          <span class="small text-muted">진행률</span>
          <CProgress
            :value="progressPercent"
            :color="progressPercent === 100 ? 'success' : 'primary'"
            style="width: 120px; height: 8px"
          />
          <span class="small fw-semibold">{{ progressPercent }}%</span>
        </div>
      </CCardHeader>
      <CCardBody>
        <div v-if="!document.steps?.length" class="text-center text-muted py-3">
          상신 후 결재선이 생성됩니다.
        </div>

        <!-- 타임라인 레이아웃 -->
        <div class="approval-timeline">
          <div
            v-for="(step, idx) in document.steps"
            :key="step.id"
            class="approval-step"
            :class="{
              'step-approved': step.status === 'approved',
              'step-rejected': step.status === 'rejected',
              'step-active': step.status === 'pending' && document.current_step === step.step_order,
              'step-pending':
                step.status === 'pending' && document.current_step !== step.step_order,
            }"
          >
            <!-- 스텝 헤더 -->
            <div class="step-header d-flex align-items-center justify-content-between mb-2">
              <div class="d-flex align-items-center gap-2">
                <div class="step-number">{{ step.step_order }}</div>
                <div>
                  <span class="fw-semibold">{{ step.role_label }}</span>
                  <CBadge
                    :color="step.condition === 'AND' ? 'primary' : 'info'"
                    size="sm"
                    class="ms-2"
                  >
                    {{ step.condition === 'AND' ? '전원 승인' : '1인 승인' }}
                  </CBadge>
                </div>
              </div>
              <CBadge :color="STEP_STATUS_COLOR[step.status]">
                {{ STEP_STATUS_LABEL[step.status] }}
              </CBadge>
            </div>

            <!-- 결재자 카드 -->
            <div class="d-flex flex-wrap gap-2">
              <div
                v-for="approver in step.approvers"
                :key="approver.id"
                class="approver-card"
                :class="{
                  'approver-approved': getAction(step, approver.id)?.action === 'approved',
                  'approver-rejected': getAction(step, approver.id)?.action === 'rejected',
                  'approver-mine': canAct(step, approver.id),
                }"
              >
                <div class="fw-semibold small mb-1">{{ approver.full_name }}</div>

                <template v-if="getAction(step, approver.id)">
                  <CBadge
                    :color="
                      getAction(step, approver.id)!.action === 'approved' ? 'success' : 'danger'
                    "
                    class="mb-1"
                  >
                    {{ getAction(step, approver.id)!.action === 'approved' ? '✓ 승인' : '✗ 반려' }}
                  </CBadge>
                  <div class="text-muted" style="font-size: 0.72rem">
                    {{ fmtDatetime(getAction(step, approver.id)!.acted_at) }}
                  </div>
                  <div
                    v-if="getAction(step, approver.id)!.comment"
                    class="mt-1 small fst-italic text-danger"
                  >
                    "{{ getAction(step, approver.id)!.comment }}"
                  </div>
                </template>
                <CBadge v-else color="secondary" class="mb-1">대기중</CBadge>

                <!-- 내가 결재할 수 있는 경우 -->
                <div v-if="canAct(step, approver.id)" class="d-flex gap-1 mt-2">
                  <CButton
                    size="sm"
                    color="success"
                    class="flex-fill"
                    @click="openActModal('approved')"
                  >
                    승인
                  </CButton>
                  <CButton
                    size="sm"
                    color="danger"
                    variant="outline"
                    class="flex-fill"
                    @click="openActModal('rejected')"
                  >
                    반려
                  </CButton>
                </div>
              </div>
            </div>

            <!-- 스텝 연결선 (마지막 제외) -->
            <div v-if="idx < (document.steps?.length ?? 0) - 1" class="step-connector" />
          </div>
        </div>
      </CCardBody>
    </CCard>
  </template>

  <!-- 결재 처리 모달 -->
  <CModal :visible="showModal" alignment="center" @close="showModal = false">
    <CModalHeader>
      <CModalTitle>
        {{ pendingAction === 'approved' ? '✓ 승인 처리' : '✗ 반려 처리' }}
      </CModalTitle>
    </CModalHeader>
    <CModalBody>
      <CFormLabel class="fw-semibold">
        {{ pendingAction === 'rejected' ? '반려 사유 (필수)' : '결재 의견 (선택)' }}
      </CFormLabel>
      <CFormTextarea
        v-model="actComment"
        rows="4"
        :placeholder="
          pendingAction === 'rejected' ? '반려 사유를 입력하세요.' : '의견을 입력하세요. (선택)'
        "
      />
    </CModalBody>
    <CModalFooter class="d-flex justify-content-between">
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

<style scoped>
/* 타임라인 레이아웃 */
.approval-timeline {
  display: flex;
  flex-direction: column;
}

.approval-step {
  position: relative;
  border: 1px solid var(--cui-border-color);
  border-radius: 0.5rem;
  padding: 1rem;
  background: var(--cui-body-bg);
  transition: box-shadow 0.2s;
}

.approval-step.step-approved {
  border-color: var(--cui-success);
  background-color: rgba(var(--cui-success-rgb), 0.04);
}

.approval-step.step-rejected {
  border-color: var(--cui-danger);
  background-color: rgba(var(--cui-danger-rgb), 0.04);
}

.approval-step.step-active {
  border-color: var(--cui-warning);
  background-color: rgba(var(--cui-warning-rgb), 0.06);
  box-shadow: 0 0 0 3px rgba(var(--cui-warning-rgb), 0.15);
}

/* 스텝 번호 뱃지 */
.step-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--cui-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}

.step-approved .step-number {
  background: var(--cui-success);
}
.step-rejected .step-number {
  background: var(--cui-danger);
}
.step-active .step-number {
  background: var(--cui-warning);
}
.step-pending .step-number {
  background: var(--cui-secondary);
}

/* 스텝 연결선 */
.step-connector {
  width: 2px;
  height: 1.25rem;
  background: var(--cui-border-color);
  margin: 0 auto;
}

/* 결재자 카드 */
.approver-card {
  border: 1px solid var(--cui-border-color);
  border-radius: 0.4rem;
  padding: 0.6rem 0.85rem;
  min-width: 130px;
  background: var(--cui-body-bg);
  text-align: center;
}

.approver-card.approver-approved {
  border-color: var(--cui-success);
  background: rgba(var(--cui-success-rgb), 0.06);
}

.approver-card.approver-rejected {
  border-color: var(--cui-danger);
  background: rgba(var(--cui-danger-rgb), 0.06);
}

.approver-card.approver-mine {
  border-color: var(--cui-warning);
  box-shadow: 0 0 0 2px rgba(var(--cui-warning-rgb), 0.2);
}
</style>
