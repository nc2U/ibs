<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval'
import { useAccount } from '@/store/pinia/account'
import type {
  ApprovalStep,
  ApprovalActionRecord,
  DocumentStatus,
  StepStatus,
  ApprovalActionType,
} from '@/store/types/approval'
import { CCard } from '@coreui/vue'

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
  draft: 'blue-grey-lighten-2',
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

const toList = () => {
  const name = route.name as string
  const go_route = name.replace(/\s*-\s*보기$/, '')
  router.replace({ name: go_route })
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

const formatFileSize = (bytes: number | null | undefined) => {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const docContent = computed<Record<string, any>>(() => {
  return (document.value?.content || {}) as Record<string, any>
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
          <v-chip
            variant="elevated"
            size="x-small"
            :color="STATUS_COLOR[document.status]"
            class="me-2"
          >
            {{ STATUS_LABEL[document.status] }}
          </v-chip>
          <span class="fw-semibold fs-5">{{ document.title }}</span>
        </div>
        <div class="d-flex gap-2 flex-wrap">
          <v-btn color="light" size="small" @click="toList" flat> 목록 </v-btn>
          <v-btn
            v-if="document.pdf_url"
            color="light"
            size="small"
            :href="document.pdf_url"
            target="_blank"
            class="no-underline text-muted"
          >
            <v-icon icon="mdi-download" color="error" class="me-1" />PDF
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
        </div>
      </CCardHeader>

      <!-- 기본 정보 -->
      <CCardBody class="pb-2">
        <CTable small bordered responsive class="mb-0">
          <CTableBody>
            <CTableRow>
              <CTableHeaderCell class="text-center bg-more-light" style="width: 100px">
                문서 번호
              </CTableHeaderCell>
              <CTableDataCell class="fw-semibold text-primary pl-3">
                {{ document.doc_number || '(상신 후 채번)' }}
              </CTableDataCell>
              <CTableHeaderCell class="text-center bg-more-light" style="width: 100px">
                문서 유형
              </CTableHeaderCell>
              <CTableDataCell class="pl-3">{{ document.doc_type_detail?.name }}</CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell class="text-center bg-more-light">기안자</CTableHeaderCell>
              <CTableDataCell class="pl-3">
                <span class="fw-semibold">{{ document.drafter?.full_name }}</span>
                <CBadge v-if="document.drafter_assignment_desc" color="secondary" size="sm" class="ms-2">
                  {{ document.drafter_assignment_desc }}
                </CBadge>
              </CTableDataCell>
              <CTableHeaderCell class="text-center bg-more-light">기안일시</CTableHeaderCell>
              <CTableDataCell class="pl-3">{{ fmtDatetime(document.created_at) }}</CTableDataCell>
            </CTableRow>
            <CTableRow>
              <CTableHeaderCell class="text-center bg-more-light">상신일시</CTableHeaderCell>
              <CTableDataCell class="pl-3">{{ fmtDatetime(document.submitted_at) }}</CTableDataCell>
              <CTableHeaderCell class="text-center bg-more-light">완료일시</CTableHeaderCell>
              <CTableDataCell class="pl-3">{{ fmtDatetime(document.completed_at) }}</CTableDataCell>
            </CTableRow>
            <CTableRow v-if="document.observers?.length">
              <CTableHeaderCell class="text-center bg-more-light">참조자 (공람)</CTableHeaderCell>
              <CTableDataCell colspan="3" class="pl-3">
                <div class="d-flex flex-wrap gap-1 align-items-center">
                  <CBadge
                    v-for="obs in document.observers"
                    :key="obs.id"
                    color="info"
                    variant="outline"
                    class="py-1 px-2"
                  >
                    <CIcon name="cilUser" size="sm" class="me-1" />
                    {{ obs.full_name }}
                  </CBadge>
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
        <CBadge v-if="document.doc_type_detail?.category_name" color="light" class="text-dark">
          {{ document.doc_type_detail.category_name }}
        </CBadge>
      </CCardHeader>
      <CCardBody>
        <!-- 1. 휴가/연차 신청서 (LEAVE_APPLICATION) -->
        <template v-if="document.doc_type_detail?.form_template_key === 'LEAVE_APPLICATION'">
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">휴가 구분</CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="primary">{{ docContent.leave_type || '연차' }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">신청 일수</CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-primary">{{ docContent.days_count ?? 1 }} 일</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">휴가 기간</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.start_date }} ~ {{ docContent.end_date || docContent.start_date }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">휴가 사유</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">{{ docContent.reason || '-' }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">업무 대행자</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.substitute_worker || '-' }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">비상 연락처</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.emergency_contact || '-' }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 2. 지출결의서 (EXPENSE_REPORT) -->
        <template v-else-if="document.doc_type_detail?.form_template_key === 'EXPENSE_REPORT'">
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">지출 구분</CTableHeaderCell>
                <CTableDataCell class="pl-3"><CBadge color="success">{{ docContent.expense_type || '법인카드' }}</CBadge></CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">지급 요청일</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.payment_due_date || '-' }}</CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.bank_name || docContent.account_number">
                <CTableHeaderCell class="text-center bg-more-light">입금 계좌</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.bank_name }} {{ docContent.account_number }} (예금주: {{ docContent.account_holder }})
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>

          <!-- 품목 내역 그리드 -->
          <div v-if="docContent.items?.length" class="mb-2">
            <div class="small fw-semibold mb-1">지출 내역 목록</div>
            <CTable small bordered responsive class="mb-0 text-center">
              <CTableHead color="light">
                <CTableRow>
                  <CTableHeaderCell style="width: 120px">일자</CTableHeaderCell>
                  <CTableHeaderCell>사용 내역 / 항목명</CTableHeaderCell>
                  <CTableHeaderCell style="width: 140px">금액 (원)</CTableHeaderCell>
                  <CTableHeaderCell style="width: 150px">비고</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                <CTableRow v-for="(item, idx) in docContent.items" :key="idx">
                  <CTableDataCell>{{ item.date }}</CTableDataCell>
                  <CTableDataCell class="text-start">{{ item.description }}</CTableDataCell>
                  <CTableDataCell class="text-end fw-semibold">{{ (Number(item.amount) || 0).toLocaleString() }}</CTableDataCell>
                  <CTableDataCell class="text-start text-muted">{{ item.note || '-' }}</CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>

          <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded">
            <span class="me-2 fw-semibold">총 지출 결의 금액:</span>
            <span class="fs-5 fw-bold text-danger">{{ (Number(docContent.amount) || 0).toLocaleString() }} 원</span>
          </div>
        </template>

        <!-- 3. 구매품의서 (PURCHASE_ORDER) -->
        <template v-else-if="document.doc_type_detail?.form_template_key === 'PURCHASE_ORDER'">
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">구매 목적</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">{{ docContent.purpose || '-' }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">납품 희망일</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.delivery_due_date || '-' }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">납품 장소</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.delivery_location || '-' }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>

          <!-- 품목 내역 그리드 -->
          <div v-if="docContent.items?.length" class="mb-2">
            <div class="small fw-semibold mb-1">구매 품목 내역</div>
            <CTable small bordered responsive class="mb-0 text-center">
              <CTableHead color="light">
                <CTableRow>
                  <CTableHeaderCell>품명</CTableHeaderCell>
                  <CTableHeaderCell style="width: 120px">규격</CTableHeaderCell>
                  <CTableHeaderCell style="width: 70px">수량</CTableHeaderCell>
                  <CTableHeaderCell style="width: 110px">단가</CTableHeaderCell>
                  <CTableHeaderCell style="width: 120px">공급가액</CTableHeaderCell>
                  <CTableHeaderCell style="width: 100px">부가세</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                <CTableRow v-for="(item, idx) in docContent.items" :key="idx">
                  <CTableDataCell class="text-start">{{ item.name }}</CTableDataCell>
                  <CTableDataCell>{{ item.spec || '-' }}</CTableDataCell>
                  <CTableDataCell>{{ item.quantity }}</CTableDataCell>
                  <CTableDataCell class="text-end">{{ (Number(item.unit_price) || 0).toLocaleString() }}</CTableDataCell>
                  <CTableDataCell class="text-end fw-semibold">{{ (Number(item.supply_price) || 0).toLocaleString() }}</CTableDataCell>
                  <CTableDataCell class="text-end text-muted">{{ (Number(item.vat) || 0).toLocaleString() }}</CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>

          <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded">
            <span class="me-2 fw-semibold">총 구매 품의 금액:</span>
            <span class="fs-5 fw-bold text-danger">{{ (Number(docContent.amount) || 0).toLocaleString() }} 원</span>
          </div>
        </template>

        <!-- 4. 일반 동적 폼 (DYNAMIC Schema) -->
        <template v-else-if="document.doc_type_detail?.form_schema?.length">
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow v-for="field in document.doc_type_detail.form_schema" :key="field.key">
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  {{ field.label }}
                </CTableHeaderCell>
                <CTableDataCell class="pl-3" style="white-space: pre-wrap">
                  {{ docContent[field.key] || '-' }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 5. 기본 JSON fallback -->
        <pre v-else class="mb-0 text-muted small">
          {{ JSON.stringify(docContent, null, 2) }}
        </pre>
      </CCardBody>
    </CCard>

    <!-- 첨부파일 목록 카드 -->
    <CCard v-if="document.attachments?.length || document.attachment" class="mb-3">
      <CCardHeader class="d-flex align-items-center justify-content-between">
        <div class="fw-semibold">
          <CIcon name="cilPaperclip" class="me-1 text-primary" />
          첨부파일
          <CBadge color="secondary" size="sm" class="ms-1">
            {{ (document.attachments?.length || 0) + (document.attachment && !document.attachments?.length ? 1 : 0) }}개
          </CBadge>
        </div>
      </CCardHeader>
      <CCardBody class="p-0">
        <CTable small hover class="mb-0">
          <CTableBody>
            <!-- 1. 다중 첨부파일 목록 -->
            <CTableRow
              v-for="att in document.attachments"
              :key="att.id"
              class="align-middle"
            >
              <CTableDataCell class="ps-3" style="width: 35px">
                <CIcon name="cilFile" class="text-primary" />
              </CTableDataCell>
              <CTableDataCell>
                <a
                  :href="att.file_url || att.file"
                  target="_blank"
                  class="text-decoration-none fw-medium text-body"
                >
                  {{ att.file_name || '첨부파일' }}
                </a>
                <span class="text-muted small ms-2">
                  ({{ formatFileSize(att.file_size) }})
                </span>
              </CTableDataCell>
              <CTableDataCell class="text-end pe-3" style="width: 120px">
                <CButton
                  size="sm"
                  color="primary"
                  variant="outline"
                  :href="att.file_url || att.file"
                  target="_blank"
                >
                  <CIcon name="cilCloudDownload" class="me-1" />다운로드
                </CButton>
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
                  :href="document.attachment"
                  target="_blank"
                  class="text-decoration-none fw-medium text-body"
                >
                  {{ document.attachment.split('/').pop() || '첨부파일' }}
                </a>
              </CTableDataCell>
              <CTableDataCell class="text-end pe-3" style="width: 120px">
                <CButton
                  size="sm"
                  color="primary"
                  variant="outline"
                  :href="document.attachment"
                  target="_blank"
                >
                  <CIcon name="cilCloudDownload" class="me-1" />다운로드
                </CButton>
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
      <v-btn color="light" @click="showModal = false" flat>닫기</v-btn>
      <v-btn
        :color="pendingAction === 'approved' ? 'success' : 'error'"
        :disabled="acting"
        @click="doAct"
      >
        <CSpinner v-if="acting" size="sm" class="me-1" />
        {{ pendingAction === 'approved' ? '승인 확인' : '반려 확인' }}
      </v-btn>
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
