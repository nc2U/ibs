<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval'
import { useAccount } from '@/store/pinia/account'
import type {
  ApprovalStep,
  ApprovalActionRecord,
  ApprovalActionType,
  ApprovalContent,
} from '@/store/types/approval'
import { CCard, CCardBody } from '@coreui/vue'
import { message } from '@/utils/helper'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import { STATIC_DETAIL_REGISTRY, FallbackDetail } from '../details'
import { markNotificationReadByTarget } from '@/utils/notification'
import {
  DOC_STATUS_CHIP_COLOR,
  DOC_STATUS_DETAIL_LABEL,
  SECURITY_LEVEL_META,
  STEP_STATUS_CHIP_COLOR,
  STEP_STATUS_LABEL,
  fmtDatetime,
  formatFileSize,
  getLocalToday,
  getSafeExternalUrl,
  getUserDisplayName,
  resolveRegistryEntry,
} from '../utils/approvalMeta'

const route = useRoute()
const router = useRouter()
const approvalStore = useApproval()
const accountStore = useAccount()

const { document } = storeToRefs(approvalStore)
const {
  fetchDocument,
  clearDocument,
  fetchDelegationList,
  submitDocument,
  actDocument,
  cancelDocument,
} = approvalStore
const myUser = computed(() => accountStore.userInfo)

const docId = computed(() => Number(route.params.docId))

const isMyDoc = computed(() => document.value?.drafter?.id === myUser.value?.pk)
const canSubmit = computed(
  () =>
    isMyDoc.value && (document.value?.status === 'draft' || document.value?.status === 'rejected'),
)
const canCancel = computed(() => {
  if (!isMyDoc.value || document.value?.status !== 'pending') return false
  const firstStep = document.value?.steps?.find(s => s.step_order === 1)
  const isFirstStepApproved = firstStep?.actions?.some(a => a.action === 'approved')
  return !isFirstStepApproved
})

const showModal = ref(false)
const pendingAction = ref<ApprovalActionType>('approved')
const actComment = ref('')
const acting = ref(false)
const submitting = ref(false)
const cancelling = ref(false)
const refCancelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)

const toList = () => {
  const name = (route.name as string) || ''
  const go_route = name.replace(/\s*-\s*보기$/, '')
  if (go_route && go_route !== name) {
    router.replace({ name: go_route })
  } else {
    router.push({ name: '결재 대기함' })
  }
}

const getAction = (step: ApprovalStep, userId: number): ApprovalActionRecord | undefined =>
  step.actions.find(
    a =>
      (a.action === 'approved' || a.action === 'rejected') &&
      (a.approver.id === userId || a.delegated_from?.id === userId),
  )

const getStepComments = (step: ApprovalStep): ApprovalActionRecord[] =>
  step.actions.filter(a => a.action === 'commented')

const isDelegateFor = (approverId: number) => {
  const today = getLocalToday()
  return approvalStore.delegationList.some(
    d =>
      d.is_active &&
      (d.delegator?.id === approverId || d.delegator_id === approverId) &&
      (d.delegatee?.id === myUser.value?.pk || d.delegatee_id === myUser.value?.pk) &&
      d.start_date <= today &&
      d.end_date >= today,
  )
}

const isStepDirectApprover = (step: ApprovalStep) =>
  step.approvers.some(a => a.id === myUser.value?.pk)

const canAct = (step: ApprovalStep, approverId: number) => {
  if (!document.value || document.value.status !== 'pending') return false
  if (document.value.current_step !== step.step_order) return false
  const isDirect = approverId === myUser.value?.pk
  // 백엔드 act()는 직접 결재자인 단계에서 대결 분기로 진입하지 않으므로, 동일 단계 직접 결재자일 경우 타인의 대결 버튼 미노출
  const isDelegate = !isStepDirectApprover(step) && isDelegateFor(approverId)
  if (!isDirect && !isDelegate) return false
  return !getAction(step, approverId)
}

const openActModal = (action: ApprovalActionType) => {
  pendingAction.value = action
  actComment.value = ''
  showModal.value = true
}

const doAct = async () => {
  if (pendingAction.value === 'rejected' && !actComment.value.trim()) {
    message('warning', '입력 확인', '반려 사유를 입력해 주세요.')
    return
  }
  if (pendingAction.value === 'commented' && !actComment.value.trim()) {
    message('warning', '입력 확인', '등록할 의견을 입력해 주세요.')
    return
  }
  acting.value = true
  try {
    const res = await actDocument(docId.value, {
      action: pendingAction.value,
      comment: actComment.value,
    })
    if (res) {
      showModal.value = false
    }
  } finally {
    acting.value = false
  }
}

const confirmSubmit = async () => {
  submitting.value = true
  try {
    await submitDocument(docId.value)
  } finally {
    submitting.value = false
  }
}

const confirmCancel = () => {
  refCancelModal.value?.callModal(
    '기안 회수 확인',
    '결재 진행 중인 기안 문서를 회수(취소)하시겠습니까?\n회수된 문서는 임시저장 상태로 전환되어 수정 후 재상신할 수 있습니다.',
    'mdi-undo',
    'warning',
    '회수 확인',
    'error',
  )
}

const doCancel = async () => {
  refCancelModal.value?.close()
  cancelling.value = true
  try {
    const ok = await cancelDocument(docId.value)
    if (ok) {
      await fetchDocument(docId.value)
    }
  } finally {
    cancelling.value = false
  }
}

// 결재선 진행률 계산
const progressPercent = computed(() => {
  const steps = document.value?.steps
  if (!steps?.length) return 0
  const done = steps.filter(s => s.status === 'approved').length
  return Math.round((done / steps.length) * 100)
})

const docContent = computed<ApprovalContent>(() => document.value?.content || {})

const detailComponent = computed(() => {
  return (
    resolveRegistryEntry(STATIC_DETAIL_REGISTRY, document.value?.doc_type_detail) ?? FallbackDetail
  )
})

// 전자결재 상세 진입/전환 시 문서 재조회 및 미확인 알림 자동 읽음 처리
watch(
  docId,
  async newId => {
    clearDocument()
    if (Number.isFinite(newId) && newId > 0) {
      markNotificationReadByTarget('approval_document', newId)
      await fetchDocument(newId)
    }
  },
  { immediate: true },
)

onMounted(async () => {
  await fetchDelegationList()
})

onUnmounted(() => {
  clearDocument()
})
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
          <v-chip
            variant="elevated"
            size="x-small"
            :color="DOC_STATUS_CHIP_COLOR[document.status]"
            class="me-2"
          >
            {{ DOC_STATUS_DETAIL_LABEL[document.status] }}
          </v-chip>
          <v-chip
            v-if="document.security_level"
            variant="tonal"
            size="x-small"
            :color="SECURITY_LEVEL_META[document.security_level].color"
            class="me-2"
          >
            <v-icon start size="x-small" :icon="SECURITY_LEVEL_META[document.security_level].icon" />
            {{ SECURITY_LEVEL_META[document.security_level].label }}
          </v-chip>
          <span class="fw-semibold fs-5">{{ document.title }}</span>
        </div>
        <div class="d-flex gap-2 flex-wrap">
          <v-btn
            v-if="getSafeExternalUrl(document.pdf_url)"
            size="small"
            :href="getSafeExternalUrl(document.pdf_url)"
            target="_blank"
            rel="noopener noreferrer"
            class="no-underline text-body"
          >
            <v-icon icon="mdi-download" color="error" class="me-1" />
            PDF 다운로드
          </v-btn>
          <v-btn
            v-if="canSubmit"
            color="success"
            variant="outlined"
            size="small"
            @click="router.push({ name: '기안 문서함 - 수정', params: { docId: document.id } })"
          >
            수정
          </v-btn>
          <v-btn
            v-if="canSubmit"
            color="primary"
            size="small"
            :disabled="submitting"
            @click="confirmSubmit"
          >
            <CSpinner v-if="submitting" size="sm" class="me-1" />
            상신
          </v-btn>
          <v-btn
            v-if="canCancel"
            color="error"
            variant="outlined"
            size="small"
            :disabled="cancelling"
            @click="confirmCancel"
          >
            <CSpinner v-if="cancelling" size="sm" class="me-1" />
            <v-icon icon="mdi-undo" size="small" class="me-1" />
            기안 회수
          </v-btn>
        </div>
      </CCardHeader>

      <!-- 회수/임시저장 알림 배너 (결재자가 과거 알림/링크로 유입된 경우) -->
      <div v-if="document.status === 'draft' && !isMyDoc" class="px-3 pt-3">
        <CAlert color="warning" class="d-flex align-items-center mb-0 py-2 px-3">
          <CIcon name="cilInfo" class="flex-shrink-0 me-2 text-warning" size="lg" />
          <div class="small">
            <strong>기안 회수 문서 안내:</strong> 이 문서는 기안자가 내용을 수정/보완하기 위해
            <strong>회수한 상태(임시저장)</strong>입니다. 기안자가 수정 후 재상신하면 결재를
            진행하실 수 있습니다.
          </div>
        </CAlert>
      </div>

      <div v-else-if="document.status === 'cancelled'" class="px-3 pt-3">
        <CAlert color="secondary" class="d-flex align-items-center mb-0 py-2 px-3">
          <CIcon name="cilInfo" class="flex-shrink-0 me-2" size="lg" />
          <div class="small">이 문서는 기안자에 의해 <strong>취소(회수)</strong>되었습니다.</div>
        </CAlert>
      </div>

      <!-- 기본 정보 -->
      <CCardBody class="pb-2">
        <CTable small bordered responsive class="mb-0">
          <CTableBody>
            <CTableRow>
              <CTableHeaderCell class="text-center bg-more-light" style="width: 100px">
                문서 번호
              </CTableHeaderCell>
              <CTableDataCell class="fw-semibold text-primary ps-3">
                {{ document.doc_number || '(상신 후 채번)' }}
              </CTableDataCell>
              <CTableHeaderCell class="text-center bg-more-light" style="width: 100px">
                문서 유형
              </CTableHeaderCell>
              <CTableDataCell class="ps-3">{{ document.doc_type_detail?.name }}</CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell class="text-center bg-more-light">기안자</CTableHeaderCell>
              <CTableDataCell class="ps-3">
                <span class="fw-semibold">
                  {{ getUserDisplayName(document.drafter) }}
                </span>
                <v-chip
                  v-if="document.drafter_assignment_desc"
                  color="secondary"
                  variant="flat"
                  size="x-small"
                  class="ms-2"
                >
                  {{ document.drafter_assignment_desc }}
                </v-chip>
              </CTableDataCell>
              <CTableHeaderCell class="text-center bg-more-light">기안일시</CTableHeaderCell>
              <CTableDataCell class="ps-3">{{ fmtDatetime(document.created_at) }}</CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell class="text-center bg-more-light">상신일시</CTableHeaderCell>
              <CTableDataCell class="ps-3">{{ fmtDatetime(document.submitted_at) }}</CTableDataCell>
              <CTableHeaderCell class="text-center bg-more-light">완료일시</CTableHeaderCell>
              <CTableDataCell class="ps-3">{{ fmtDatetime(document.completed_at) }}</CTableDataCell>
            </CTableRow>
            <CTableRow v-if="document.observers?.length">
              <CTableHeaderCell class="text-center bg-more-light">참조자 (공람)</CTableHeaderCell>
              <CTableDataCell colspan="3" class="ps-3">
                <div class="d-flex flex-wrap gap-1 align-items-center">
                  <v-chip
                    v-for="obs in document.observers"
                    :key="obs.id"
                    color="info"
                    variant="outlined"
                    size="x-small"
                    class="py-1 px-2"
                  >
                    <v-icon icon="mdi-account-check" size="small" class="me-1" />
                    {{ getUserDisplayName(obs) }}
                  </v-chip>
                </div>
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCardBody>
    </CCard>

    <!-- ② 결재 내용 -->
    <CCard class="mb-3">
      <CCardHeader class="d-flex align-items-center justify-content-between">
        <strong>결재 내용</strong>
        <v-chip
          v-if="document.doc_type_detail?.category_name"
          color="secondary"
          variant="tonal"
          size="x-small"
        >
          {{ document.doc_type_detail.category_name }}
        </v-chip>
      </CCardHeader>
      <CCardBody>
        <component :is="detailComponent" :content="docContent" :document="document" />
      </CCardBody>
    </CCard>

    <!-- 첨부파일 목록 카드 -->
    <CCard v-if="document.attachments?.length || document.attachment" class="mb-3">
      <CCardHeader class="d-flex align-items-center justify-content-between">
        <div class="fw-semibold">
          <CIcon name="cilPaperclip" class="me-1 text-primary" />
          첨부파일
          <v-chip color="secondary" variant="flat" size="x-small" class="ms-1">
            {{
              (document.attachments?.length || 0) +
              (document.attachment && !document.attachments?.length ? 1 : 0)
            }}개
          </v-chip>
        </div>
      </CCardHeader>
      <CCardBody class="p-0">
        <CTable small hover class="mb-0">
          <CTableBody>
            <!-- 1. 다중 첨부파일 목록 -->
            <CTableRow v-for="att in document.attachments" :key="att.id" class="align-middle">
              <CTableDataCell class="ps-3" style="width: 35px">
                <CIcon name="cilFile" class="text-primary" />
              </CTableDataCell>
              <CTableDataCell>
                <a
                  v-if="getSafeExternalUrl(att.file_url || att.file)"
                  :href="getSafeExternalUrl(att.file_url || att.file)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-decoration-none fw-medium text-body"
                >
                  {{ att.file_name || '첨부파일' }}
                </a>
                <span v-else class="fw-medium text-body">{{ att.file_name || '첨부파일' }}</span>
                <span class="text-muted small ms-2"> ({{ formatFileSize(att.file_size) }}) </span>
              </CTableDataCell>
              <CTableDataCell class="text-end pe-3" style="width: 120px">
                <CButton
                  v-if="getSafeExternalUrl(att.file_url || att.file)"
                  size="sm"
                  color="primary"
                  variant="outline"
                  :href="getSafeExternalUrl(att.file_url || att.file)"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <CIcon name="cilCloudDownload" class="me-1" />다운로드
                </CButton>
                <span v-else class="small text-muted">-</span>
              </CTableDataCell>
            </CTableRow>

            <!-- 2. 레거시 단일 첨부파일 fallback -->
            <CTableRow
              v-if="document.attachment && !document.attachments?.length"
              class="align-middle"
            >
              <CTableDataCell class="ps-3" style="width: 35px">
                <CIcon name="cilFile" class="text-primary" />
              </CTableDataCell>
              <CTableDataCell>
                <a
                  v-if="getSafeExternalUrl(document.attachment)"
                  :href="getSafeExternalUrl(document.attachment)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-decoration-none fw-medium text-body"
                >
                  {{ document.attachment.split('/').pop() || '첨부파일' }}
                </a>
                <span v-else class="fw-medium text-body">
                  {{ document.attachment.split('/').pop() || '첨부파일' }}
                </span>
              </CTableDataCell>
              <CTableDataCell class="text-end pe-3" style="width: 120px">
                <CButton
                  v-if="getSafeExternalUrl(document.attachment)"
                  size="sm"
                  color="primary"
                  variant="outline"
                  :href="getSafeExternalUrl(document.attachment)"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <CIcon name="cilCloudDownload" class="me-1" />다운로드
                </CButton>
                <span v-else class="small text-muted">-</span>
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
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
            :color="progressPercent === 100 ? 'success' : 'warning'"
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
                  <v-chip
                    :color="step.condition === 'AND' ? 'success' : 'info'"
                    variant="flat"
                    size="x-small"
                    class="ms-2"
                  >
                    {{ step.condition === 'AND' ? '전원 승인' : '1인 승인' }}
                  </v-chip>
                </div>
              </div>
              <v-chip :color="STEP_STATUS_CHIP_COLOR[step.status]" variant="flat" size="x-small">
                {{ STEP_STATUS_LABEL[step.status] }}
              </v-chip>
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
                <div class="fw-semibold small mb-1">
                  {{ getUserDisplayName(approver) }}
                  <span
                    v-if="
                      approver.id !== myUser?.pk &&
                      !isStepDirectApprover(step) &&
                      isDelegateFor(approver.id)
                    "
                    class="badge bg-warning text-dark ms-1"
                    style="font-size: 0.65rem"
                  >
                    대결 대상
                  </span>
                </div>

                <template v-if="getAction(step, approver.id)">
                  <div class="d-flex align-items-center justify-content-center gap-1 mb-1">
                    <v-chip
                      :color="
                        getAction(step, approver.id)!.action === 'approved' ? 'success' : 'error'
                      "
                      variant="flat"
                      size="x-small"
                    >
                      {{
                        getAction(step, approver.id)!.action === 'approved' ? '✓ 승인' : '✗ 반려'
                      }}
                    </v-chip>
                    <v-chip
                      v-if="getAction(step, approver.id)!.is_delegated"
                      color="warning"
                      size="x-small"
                      variant="flat"
                      title="대리 결재"
                    >
                      대결: {{ getUserDisplayName(getAction(step, approver.id)!.approver) }}
                    </v-chip>
                  </div>
                  <div class="text-muted" style="font-size: 0.72rem">
                    {{ fmtDatetime(getAction(step, approver.id)!.acted_at) }}
                  </div>
                  <div
                    v-if="getAction(step, approver.id)!.comment"
                    class="mt-1 small fst-italic"
                    :class="
                      getAction(step, approver.id)!.action === 'rejected'
                        ? 'text-danger'
                        : 'text-medium-emphasis'
                    "
                  >
                    "{{ getAction(step, approver.id)!.comment }}"
                  </div>
                </template>
                <v-chip v-else color="secondary" variant="flat" size="x-small" class="mb-1">
                  대기중
                </v-chip>

                <!-- 내가 결재할 수 있는 경우 -->
                <div v-if="canAct(step, approver.id)" class="d-flex flex-column gap-1 mt-2">
                  <div class="d-flex gap-1">
                    <v-btn
                      size="small"
                      color="success"
                      class="flex-fill"
                      @click="openActModal('approved')"
                    >
                      승인
                    </v-btn>
                    <v-btn
                      size="small"
                      color="error"
                      variant="outlined"
                      class="flex-fill"
                      @click="openActModal('rejected')"
                    >
                      반려
                    </v-btn>
                  </div>
                  <v-btn
                    size="x-small"
                    color="info"
                    variant="tonal"
                    block
                    @click="openActModal('commented')"
                  >
                    의견 등록
                  </v-btn>
                </div>
              </div>
            </div>

            <!-- 단계 의견 내역 (commented) -->
            <div v-if="getStepComments(step).length" class="mt-2 pt-2 border-top small">
              <div
                v-for="cmt in getStepComments(step)"
                :key="cmt.id"
                class="text-medium-emphasis mb-1"
              >
                <v-icon icon="mdi-comment-text-outline" size="x-small" color="info" class="me-1" />
                <strong>{{ getUserDisplayName(cmt.approver) }}</strong>
                <span class="text-muted ms-1">({{ fmtDatetime(cmt.acted_at) }})</span>:
                {{ cmt.comment }}
              </div>
            </div>

            <!-- 스텝 연결선 (마지막 제외) -->
            <div v-if="idx < (document.steps?.length ?? 0) - 1" class="step-connector" />
          </div>
        </div>
      </CCardBody>
    </CCard>

    <CRow>
      <CCol class="text-end">
        <v-btn color="light" class="text-body" flat @click="toList"> 목록으로 </v-btn>
      </CCol>
    </CRow>
  </template>

  <!-- 결재 처리 모달 -->
  <CModal
    :visible="showModal"
    alignment="center"
    backdrop="static"
    @close="!acting && (showModal = false)"
  >
    <CModalHeader>
      <CModalTitle>
        {{
          pendingAction === 'approved'
            ? '✓ 승인 처리'
            : pendingAction === 'rejected'
              ? '✗ 반려 처리'
              : '💬 결재 의견 등록'
        }}
      </CModalTitle>
    </CModalHeader>
    <CModalBody>
      <CFormLabel class="fw-semibold">
        {{
          pendingAction === 'rejected'
            ? '반려 사유 (필수)'
            : pendingAction === 'commented'
              ? '결재 의견 (필수)'
              : '결재 의견 (선택)'
        }}
      </CFormLabel>
      <CFormTextarea
        v-model="actComment"
        rows="4"
        :placeholder="
          pendingAction === 'rejected'
            ? '반려 사유를 입력하세요.'
            : pendingAction === 'commented'
              ? '결재 의견을 입력하세요.'
              : '의견을 입력하세요. (선택)'
        "
      />
    </CModalBody>
    <CModalFooter class="d-flex justify-content-between">
      <v-btn color="light" flat :disabled="acting" @click="showModal = false">닫기</v-btn>
      <v-btn
        :color="
          pendingAction === 'approved'
            ? 'success'
            : pendingAction === 'rejected'
              ? 'error'
              : 'info'
        "
        :disabled="acting"
        @click="doAct"
      >
        <CSpinner v-if="acting" size="sm" class="me-1" />
        {{
          pendingAction === 'approved'
            ? '승인 확인'
            : pendingAction === 'rejected'
              ? '반려 확인'
              : '의견 등록'
        }}
      </v-btn>
    </CModalFooter>
  </CModal>

  <ConfirmModal ref="refCancelModal" @confirm-func="doCancel" />
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
  min-width: 140px;
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
