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
const { fetchDocument, submitDocument, actDocument, cancelDocument } = approvalStore
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
  step.actions.find(a => a.approver.id === userId || a.delegated_from?.id === userId)

const isDelegateFor = (approverId: number) => {
  const today = new Date().toISOString().split('T')[0]
  return approvalStore.delegationList.some(
    d =>
      d.is_active &&
      (d.delegator?.id === approverId || d.delegator_id === approverId) &&
      (d.delegatee?.id === myUser.value?.pk || d.delegatee_id === myUser.value?.pk) &&
      d.start_date <= today &&
      d.end_date >= today,
  )
}

const canAct = (step: ApprovalStep, approverId: number) => {
  if (!document.value || document.value.status !== 'pending') return false
  if (document.value.current_step !== step.step_order) return false
  const isDirect = approverId === myUser.value?.pk
  const isDelegate = isDelegateFor(approverId)
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

const confirmCancel = async () => {
  if (!confirm('결재 진행 중인 기안 문서를 회수(취소)하시겠습니까?')) return
  cancelling.value = true
  await cancelDocument(docId.value)
  await fetchDocument(docId.value)
  cancelling.value = false
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

const getBudgetAccountLabel = (code?: string) => {
  const map: Record<string, string> = {
    NONE: '예산 비소요 (0원)',
    GENERAL_EXPENSE: '일반관리비 / 경상운영비',
    PROJECT_COST: '사업비 / 현장 직접비',
    OUTSOURCING: '외주 용역비',
    MARKETING: '홍보 및 마케팅비',
    ASSET_PURCHASE: '자산 취득비',
    OTHER: '기타 예산',
  }
  return (code && map[code]) || code || '-'
}

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
          <v-chip
            v-if="document.security_level"
            variant="tonal"
            size="x-small"
            :color="
              document.security_level === '1'
                ? 'error'
                : document.security_level === '2'
                  ? 'primary'
                  : 'success'
            "
            class="me-2"
          >
            <v-icon
              start
              size="x-small"
              :icon="
                document.security_level === '1'
                  ? 'mdi-lock'
                  : document.security_level === '2'
                    ? 'mdi-account-group'
                    : 'mdi-earth'
              "
            />
            {{
              document.security_level === '1'
                ? '1등급 (비공개)'
                : document.security_level === '2'
                  ? '2등급 (부서공개)'
                  : '3등급 (전사공개)'
            }}
          </v-chip>
          <span class="fw-semibold fs-5">{{ document.title }}</span>
        </div>
        <div class="d-flex gap-2 flex-wrap">
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
                <CBadge
                  v-if="document.drafter_assignment_desc"
                  color="secondary"
                  size="sm"
                  class="ms-2"
                >
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
        <CBadge v-if="document.doc_type_detail?.category_name" color="light" class="text-body">
          {{ document.doc_type_detail.category_name }}
        </CBadge>
      </CCardHeader>
      <CCardBody>
        <!-- 1. 휴가/연차 신청서 (LEAVE_APPLICATION / LEAVE) -->
        <template
          v-if="
            document.doc_type_detail?.form_template_key === 'LEAVE_APPLICATION' ||
            document.doc_type_detail?.form_template_key === 'LEAVE'
          "
        >
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >휴가 구분</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">
                  <CBadge color="primary">{{ docContent.leave_type || '연차' }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >신청 일수</CTableHeaderCell
                >
                <CTableDataCell class="pl-3 fw-bold text-primary"
                  >{{ docContent.days_count ?? 1 }} 일</CTableDataCell
                >
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">휴가 기간</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.start_date }} ~ {{ docContent.end_date || docContent.start_date }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">휴가 사유</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">{{
                  docContent.reason || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">업무 대행자</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{
                  docContent.substitute_worker || '-'
                }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">비상 연락처</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{
                  docContent.emergency_contact || '-'
                }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 2. 지출결의서 (EXPENSE_REPORT / EXPENSE) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'EXPENSE_REPORT' ||
            document.doc_type_detail?.form_template_key === 'EXPENSE'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >지출 구분</CTableHeaderCell
                >
                <CTableDataCell class="pl-3"
                  ><CBadge color="success">{{
                    docContent.expense_type || '법인카드'
                  }}</CBadge></CTableDataCell
                >
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >지급 요청일</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">{{
                  docContent.payment_due_date || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.bank_name || docContent.account_number">
                <CTableHeaderCell class="text-center bg-more-light">입금 계좌</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.bank_name }} {{ docContent.account_number }} (예금주:
                  {{ docContent.account_holder }})
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
                  <CTableDataCell class="text-end fw-semibold">{{
                    (Number(item.amount) || 0).toLocaleString()
                  }}</CTableDataCell>
                  <CTableDataCell class="text-start text-muted">{{
                    item.note || '-'
                  }}</CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>

          <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded">
            <span class="me-2 fw-semibold">총 지출 결의 금액:</span>
            <span class="fs-5 fw-bold text-danger"
              >{{ (Number(docContent.amount) || 0).toLocaleString() }} 원</span
            >
          </div>
        </template>

        <!-- 3. 구매품의서 (PURCHASE_ORDER / PURCHASE) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'PURCHASE_ORDER' ||
            document.doc_type_detail?.form_template_key === 'PURCHASE'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >구매 목적</CTableHeaderCell
                >
                <CTableDataCell colspan="3" class="pl-3">{{
                  docContent.purpose || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">납품 희망일</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{
                  docContent.delivery_due_date || '-'
                }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >납품 장소</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">{{
                  docContent.delivery_location || '-'
                }}</CTableDataCell>
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
                  <CTableDataCell class="text-end">{{
                    (Number(item.unit_price) || 0).toLocaleString()
                  }}</CTableDataCell>
                  <CTableDataCell class="text-end fw-semibold">{{
                    (Number(item.supply_price) || 0).toLocaleString()
                  }}</CTableDataCell>
                  <CTableDataCell class="text-end text-muted">{{
                    (Number(item.vat) || 0).toLocaleString()
                  }}</CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>

          <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded">
            <span class="me-2 fw-semibold">총 구매 품의 금액:</span>
            <span class="fs-5 fw-bold text-danger"
              >{{ (Number(docContent.amount) || 0).toLocaleString() }} 원</span
            >
          </div>
        </template>

        <!-- 4. 공문 발신 (OFFICIAL_LETTER) -->
        <template v-else-if="document.doc_type_detail?.form_template_key === 'OFFICIAL_LETTER'">
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >수신처</CTableHeaderCell
                >
                <CTableDataCell class="pl-3 fw-semibold text-primary">{{
                  docContent.receiver || '-'
                }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >참조처</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">{{ docContent.refer_to || '-' }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">발신 명의</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{
                  docContent.sender_name || '대표이사'
                }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">대외 문서번호</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{
                  docContent.doc_number_external || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">공문 제목</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 fw-bold">{{
                  docContent.letter_subject || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light"
                  >공문 본문(요지)</CTableHeaderCell
                >
                <CTableDataCell
                  colspan="3"
                  class="pl-3 py-3"
                  style="white-space: pre-wrap; line-height: 1.6"
                  >{{ docContent.letter_body || '-' }}</CTableDataCell
                >
              </CTableRow>
              <CTableRow v-if="docContent.enclosed_files_desc">
                <CTableHeaderCell class="text-center bg-more-light"
                  >붙임 서류 내역</CTableHeaderCell
                >
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">{{
                  docContent.enclosed_files_desc
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">발송 방법</CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="info">{{ docContent.send_method || '이메일' }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">발송 희망일</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.send_due_date || '-' }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">날인 인감</CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="dark">{{ docContent.seal_type || '법인인감' }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">날인 부수</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.seal_count ?? 1 }} 부</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 5. 일반 업무 품의서 (GENERAL / BIZ_APPROVAL) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'GENERAL' ||
            document.doc_type_detail?.form_template_key === 'BIZ_APPROVAL'
          "
        >
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >품의 목적</CTableHeaderCell
                >
                <CTableDataCell colspan="3" class="pl-3 fw-bold text-primary">{{
                  docContent.purpose || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">추진 일정</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.schedule || '-' }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >예산 과목</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">{{
                  docContent.budget_account || '일반관리비'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">소요 예산</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  <span class="fs-6 fw-bold text-danger">
                    {{ (Number(docContent.budget ?? docContent.amount) || 0).toLocaleString() }} 원
                  </span>
                  <span
                    v-if="!docContent.budget && !docContent.amount"
                    class="text-muted small ms-2"
                    >(예산 비소요)</span
                  >
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light"
                  >세부 품의 내용</CTableHeaderCell
                >
                <CTableDataCell
                  colspan="3"
                  class="pl-3 py-3"
                  style="white-space: pre-wrap; line-height: 1.6"
                  >{{ docContent.content || '-' }}</CTableDataCell
                >
              </CTableRow>
              <CTableRow v-if="docContent.expected_effect">
                <CTableHeaderCell class="text-center bg-more-light">기대 효과</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">{{
                  docContent.expected_effect
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.note">
                <CTableHeaderCell class="text-center bg-more-light"
                  >비고 / 특이사항</CTableHeaderCell
                >
                <CTableDataCell colspan="3" class="pl-3 text-muted">{{
                  docContent.note
                }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 6. 출장 신청서 (BUSINESS_TRIP / TRIP) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'BUSINESS_TRIP' ||
            document.doc_type_detail?.form_template_key === 'TRIP'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >출장 구분</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">
                  <CBadge color="primary">{{
                    docContent.trip_type === 'OVERSEAS' ? '해외 출장' : '국내 출장'
                  }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >출장지</CTableHeaderCell
                >
                <CTableDataCell class="pl-3 fw-semibold text-primary">{{
                  docContent.destination || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">출장 기간</CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  {{ docContent.start_date || '-' }} ~ {{ docContent.end_date || '-' }}
                  <CBadge color="info" class="ms-2"
                    >{{ docContent.nights_count ?? 0 }}박 {{ docContent.days_count ?? 1 }}일</CBadge
                  >
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">교통편</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{
                  docContent.transportation || '법인차량'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">출장 목적</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 fw-bold">{{
                  docContent.purpose || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">동행자</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.companion || '-' }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">업무 대행자</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{
                  docContent.substitute_worker || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">비상 연락처</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">{{
                  docContent.emergency_contact || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light"
                  >세부 여비 내역</CTableHeaderCell
                >
                <CTableDataCell colspan="3" class="p-2">
                  <div class="d-flex gap-4 small">
                    <span
                      >교통비:
                      <strong>{{
                        (Number(docContent.transport_cost) || 0).toLocaleString()
                      }}</strong>
                      원</span
                    >
                    <span
                      >숙박비:
                      <strong>{{ (Number(docContent.lodging_cost) || 0).toLocaleString() }}</strong>
                      원</span
                    >
                    <span
                      >일비/식비:
                      <strong>{{
                        (Number(docContent.daily_allowance) || 0).toLocaleString()
                      }}</strong>
                      원</span
                    >
                    <span
                      >기타:
                      <strong>{{ (Number(docContent.other_cost) || 0).toLocaleString() }}</strong>
                      원</span
                    >
                  </div>
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.itinerary">
                <CTableHeaderCell class="text-center bg-more-light"
                  >세부 일정 계획</CTableHeaderCell
                >
                <CTableDataCell
                  colspan="3"
                  class="pl-3 py-3"
                  style="white-space: pre-wrap; line-height: 1.6"
                  >{{ docContent.itinerary }}</CTableDataCell
                >
              </CTableRow>
            </CTableBody>
          </CTable>
          <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded">
            <span class="me-2 fw-semibold">총 예상 출장 여비:</span>
            <span class="fs-5 fw-bold text-danger"
              >{{
                (Number(docContent.total_cost ?? docContent.amount) || 0).toLocaleString()
              }}
              원</span
            >
          </div>
        </template>

        <!-- 7. 연장/휴일근무 신청서 (OVERTIME / OVERTIME_WORK) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'OVERTIME' ||
            document.doc_type_detail?.form_template_key === 'OVERTIME_WORK'
          "
        >
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >근무 구분</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">
                  <CBadge
                    :color="
                      docContent.work_type === 'HOLIDAY'
                        ? 'danger'
                        : docContent.work_type === 'NIGHT'
                          ? 'dark'
                          : 'primary'
                    "
                  >
                    {{
                      docContent.work_type === 'HOLIDAY'
                        ? '휴일 근무'
                        : docContent.work_type === 'NIGHT'
                          ? '야간 근무'
                          : '평일 연장근무'
                    }}
                  </CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >근무 일자</CTableHeaderCell
                >
                <CTableDataCell class="pl-3 fw-semibold">{{
                  docContent.work_date || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">근무 시간</CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  {{ docContent.start_time || '-' }} ~ {{ docContent.end_time || '-' }}
                  <span v-if="docContent.break_hours" class="text-muted small ms-2"
                    >(휴게: {{ docContent.break_hours }}시간)</span
                  >
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">인정 시간</CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <span class="fs-6 fw-bold text-primary"
                    >{{ docContent.total_hours ?? 0 }} 시간</span
                  >
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">보상 방식</CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="info">{{
                    docContent.compensation_type === 'COMP_LEAVE'
                      ? '대체휴무 (보상휴가) 적립'
                      : '수당 지급'
                  }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">동반 근무자</CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.co_workers || '-' }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light"
                  >근무 사유 / 업무</CTableHeaderCell
                >
                <CTableDataCell
                  colspan="3"
                  class="pl-3 py-3"
                  style="white-space: pre-wrap; line-height: 1.6"
                  >{{ docContent.reason || '-' }}</CTableDataCell
                >
              </CTableRow>
              <CTableRow v-if="docContent.note">
                <CTableHeaderCell class="text-center bg-more-light"
                  >비고 / 특이사항</CTableHeaderCell
                >
                <CTableDataCell colspan="3" class="pl-3 text-muted">{{
                  docContent.note
                }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 8. 인사발령 (HR_APPOINTMENT / APPOINTMENT) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'HR_APPOINTMENT' ||
            document.doc_type_detail?.form_template_key === 'APPOINTMENT'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >발령 구분</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">
                  <CBadge color="primary">{{ docContent.appointment_type || '승진/전보' }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >발령 시행일</CTableHeaderCell
                >
                <CTableDataCell class="pl-3 fw-bold text-danger">{{
                  docContent.effective_date || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light"
                  >발령 사유/배경</CTableHeaderCell
                >
                <CTableDataCell
                  colspan="3"
                  class="pl-3 py-2"
                  style="white-space: pre-wrap; line-height: 1.6"
                  >{{ docContent.reason || '-' }}</CTableDataCell
                >
              </CTableRow>
            </CTableBody>
          </CTable>

          <div v-if="docContent.targets?.length" class="mb-3">
            <h6 class="fw-bold mb-2 small text-primary">
              <CIcon name="cilPeople" class="me-1" />
              발령 대상자 세부 내역 (총 {{ docContent.targets.length }}명)
            </h6>
            <CTable small bordered responsive hover class="text-center mb-0 align-middle">
              <CTableHead class="table-light small">
                <CTableRow>
                  <CTableHeaderCell style="width: 40px">#</CTableHeaderCell>
                  <CTableHeaderCell style="width: 90px">성명</CTableHeaderCell>
                  <CTableHeaderCell>현 소속 / 직급</CTableHeaderCell>
                  <CTableHeaderCell class="text-primary">발령 소속 / 직급</CTableHeaderCell>
                  <CTableHeaderCell style="width: 110px">발령 구분</CTableHeaderCell>
                  <CTableHeaderCell>비고</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody class="small">
                <CTableRow v-for="(t, idx) in docContent.targets" :key="idx">
                  <CTableDataCell class="text-muted">{{ Number(idx) + 1 }}</CTableDataCell>
                  <CTableDataCell class="fw-bold">{{ t.name }}</CTableDataCell>
                  <CTableDataCell class="text-muted"
                    >{{ t.current_dept || '-' }} / {{ t.current_position || '-' }}</CTableDataCell
                  >
                  <CTableDataCell class="fw-semibold text-primary"
                    >{{ t.new_dept || '-' }} / {{ t.new_position || '-' }}</CTableDataCell
                  >
                  <CTableDataCell
                    ><CBadge color="info">{{ t.type_desc || '발령' }}</CBadge></CTableDataCell
                  >
                  <CTableDataCell class="text-start">{{ t.note || '-' }}</CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>

          <div v-if="docContent.note" class="p-2 bg-light border rounded small text-muted">
            <strong>비고 / 특이사항:</strong> {{ docContent.note }}
          </div>
        </template>

        <!-- 9. 인사 관련 제신청서 (HR_REQUEST / CERT_REQUEST) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'HR_REQUEST' ||
            document.doc_type_detail?.form_template_key === 'CERT_REQUEST'
          "
        >
          <CTable small bordered responsive class="mb-0">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >신청 구분</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">
                  <CBadge color="primary">{{ docContent.request_type || '제증명서 발급' }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >수령 방법</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">{{
                  docContent.receive_method || 'PDF 이메일 수신'
                }}</CTableDataCell>
              </CTableRow>

              <!-- 증명서 전용 행 -->
              <template
                v-if="docContent.request_type === 'CERTIFICATE' || !docContent.request_type"
              >
                <CTableRow>
                  <CTableHeaderCell class="text-center bg-more-light">증명서 종류</CTableHeaderCell>
                  <CTableDataCell class="pl-3 fw-semibold text-primary">
                    {{ docContent.cert_type || '재직증명서' }} ({{
                      docContent.cert_language === 'ENGLISH' ? '영문' : '국문'
                    }}, {{ docContent.cert_count ?? 1 }}부)
                  </CTableDataCell>
                  <CTableHeaderCell class="text-center bg-more-light"
                    >제출처 / 용도</CTableHeaderCell
                  >
                  <CTableDataCell class="pl-3">
                    {{ docContent.submit_to || '-' }} / {{ docContent.usage_purpose || '-' }}
                  </CTableDataCell>
                </CTableRow>
                <CTableRow>
                  <CTableHeaderCell class="text-center bg-more-light"
                    >주민번호 표기</CTableHeaderCell
                  >
                  <CTableDataCell colspan="3" class="pl-3">
                    {{ docContent.include_resident_num ? '뒷자리 전체 표기' : '생년월일만 표기' }}
                  </CTableDataCell>
                </CTableRow>
              </template>

              <!-- 경조사 전용 행 -->
              <template v-else-if="docContent.request_type === 'CONGRATULATION_CONDOLENCE'">
                <CTableRow>
                  <CTableHeaderCell class="text-center bg-more-light">경조 구분</CTableHeaderCell>
                  <CTableDataCell class="pl-3 fw-semibold text-danger">{{
                    docContent.event_type || '-'
                  }}</CTableDataCell>
                  <CTableHeaderCell class="text-center bg-more-light">경조 일자</CTableHeaderCell>
                  <CTableDataCell class="pl-3">{{ docContent.event_date || '-' }}</CTableDataCell>
                </CTableRow>
                <CTableRow>
                  <CTableHeaderCell class="text-center bg-more-light">경조 장소</CTableHeaderCell>
                  <CTableDataCell class="pl-3">{{ docContent.event_place || '-' }}</CTableDataCell>
                  <CTableHeaderCell class="text-center bg-more-light"
                    >경조금 신청액</CTableHeaderCell
                  >
                  <CTableDataCell class="pl-3 fw-bold text-danger">
                    {{
                      (
                        Number(docContent.congratulation_amount ?? docContent.amount) || 0
                      ).toLocaleString()
                    }}
                    원
                  </CTableDataCell>
                </CTableRow>
                <CTableRow v-if="docContent.support_items">
                  <CTableHeaderCell class="text-center bg-more-light"
                    >물품 지원 요청</CTableHeaderCell
                  >
                  <CTableDataCell colspan="3" class="pl-3">{{
                    docContent.support_items
                  }}</CTableDataCell>
                </CTableRow>
              </template>

              <!-- 휴복직 전용 행 -->
              <template
                v-else-if="
                  docContent.request_type === 'LEAVE_OF_ABSENCE' ||
                  docContent.request_type === 'REINSTATEMENT'
                "
              >
                <CTableRow>
                  <CTableHeaderCell class="text-center bg-more-light"
                    >기간 / 희망일</CTableHeaderCell
                  >
                  <CTableDataCell colspan="3" class="pl-3 fw-semibold">
                    <span v-if="docContent.request_type === 'LEAVE_OF_ABSENCE'">
                      휴직: {{ docContent.leave_start_date || '-' }} ~
                      {{ docContent.leave_end_date || '-' }}
                    </span>
                    <span v-else> 복직 희망일: {{ docContent.reinstatement_date || '-' }} </span>
                  </CTableDataCell>
                </CTableRow>
              </template>

              <!-- 공통 사유 -->
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light"
                  >신청 사유 / 상세</CTableHeaderCell
                >
                <CTableDataCell
                  colspan="3"
                  class="pl-3 py-3"
                  style="white-space: pre-wrap; line-height: 1.6"
                >
                  {{ docContent.reason || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.note">
                <CTableHeaderCell class="text-center bg-more-light"
                  >비고 / 특이사항</CTableHeaderCell
                >
                <CTableDataCell colspan="3" class="pl-3 text-muted">{{
                  docContent.note
                }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 10. 경비 정산서 (EXPENSE_SETTLEMENT / SETTLEMENT) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'EXPENSE_SETTLEMENT' ||
            document.doc_type_detail?.form_template_key === 'SETTLEMENT'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >정산 구분</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">
                  <CBadge color="primary">{{
                    docContent.settlement_type === 'PERSONAL_EXPENSE'
                      ? '개인경비 실비환급'
                      : docContent.settlement_type === 'BUSINESS_TRIP'
                        ? '출장경비 정산'
                        : docContent.settlement_type === 'ADVANCE_PAY'
                          ? '가지급금 정산'
                          : '법인카드 사용정산'
                  }}</CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >귀속 연월</CTableHeaderCell
                >
                <CTableDataCell class="pl-3 fw-bold">{{
                  docContent.target_month || '-'
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.card_number">
                <CTableHeaderCell class="text-center bg-more-light">법인카드 정보</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">{{
                  docContent.card_number
                }}</CTableDataCell>
              </CTableRow>
              <CTableRow v-else-if="docContent.bank_name || docContent.account_number">
                <CTableHeaderCell class="text-center bg-more-light">환급 계좌</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.bank_name }} {{ docContent.account_number }} (예금주:
                  {{ docContent.account_holder || '-' }})
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light"
                  >정산 개요/사유</CTableHeaderCell
                >
                <CTableDataCell colspan="3" class="pl-3">{{
                  docContent.reason || '-'
                }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>

          <!-- 영수증 세부 내역 그리드 -->
          <div v-if="docContent.items?.length" class="mb-2">
            <div class="small fw-semibold mb-1 text-primary">
              영수증 / 세부 사용 내역 (총 {{ docContent.items.length }}건)
            </div>
            <CTable small bordered responsive class="mb-0 text-center align-middle">
              <CTableHead color="light">
                <CTableRow class="small">
                  <CTableHeaderCell style="width: 110px">사용일자</CTableHeaderCell>
                  <CTableHeaderCell style="width: 150px">계정과목</CTableHeaderCell>
                  <CTableHeaderCell style="width: 160px">가맹점</CTableHeaderCell>
                  <CTableHeaderCell style="width: 130px">금액 (원)</CTableHeaderCell>
                  <CTableHeaderCell>사용 목적 / 참석자</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody class="small">
                <CTableRow v-for="(item, idx) in docContent.items" :key="idx">
                  <CTableDataCell>{{ item.date }}</CTableDataCell>
                  <CTableDataCell>
                    <CBadge color="secondary">{{ item.category }}</CBadge>
                  </CTableDataCell>
                  <CTableDataCell class="text-start fw-semibold">
                    {{ item.merchant }}
                  </CTableDataCell>
                  <CTableDataCell class="text-end fw-bold text-body">
                    {{ (Number(item.amount) || 0).toLocaleString() }}
                  </CTableDataCell>
                  <CTableDataCell class="text-start">{{ item.purpose || '-' }}</CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </div>

          <div
            class="d-flex justify-content-end align-items-center p-2 bg-light border rounded mb-2"
          >
            <span class="me-2 fw-semibold">총 정산 합계 금액:</span>
            <span class="fs-5 fw-bold text-danger">
              {{ (Number(docContent.total_amount ?? docContent.amount) || 0).toLocaleString() }}
              원
            </span>
          </div>

          <div v-if="docContent.note" class="p-2 bg-light border rounded small text-muted">
            <strong>비고 / 증빙 안내:</strong> {{ docContent.note }}
          </div>
        </template>

        <!-- 11. 선급금 / 가지급금 신청서 (ADVANCE / ADVANCE_PAY / ADVANCE_REQUEST) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'ADVANCE' ||
            document.doc_type_detail?.form_template_key === 'ADVANCE_PAY' ||
            document.doc_type_detail?.form_template_key === 'ADVANCE_REQUEST'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >신청 구분</CTableHeaderCell
                >
                <CTableDataCell class="pl-3">
                  <CBadge color="danger">
                    {{
                      docContent.advance_type === 'PREPAYMENT'
                        ? '선급금 (계약상 대금 선지급)'
                        : docContent.advance_type === 'IMPREST_FUND'
                          ? '전도금 (상비 운영비)'
                          : docContent.advance_type === 'EVENT_FUND'
                            ? '행사/프로젝트 진행비'
                            : '가지급금 (업무용 선지급)'
                    }}
                  </CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px"
                  >지급 요청일</CTableHeaderCell
                >
                <CTableDataCell class="pl-3 fw-bold">
                  {{ docContent.payment_due_date || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">신청 금액</CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
                  {{
                    (Number(docContent.advance_amount ?? docContent.amount) || 0).toLocaleString()
                  }}
                  원
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">정산 예정일</CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-semibold text-primary">
                  {{ docContent.settlement_due_date || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.bank_name || docContent.account_number">
                <CTableHeaderCell class="text-center bg-more-light">
                  입금(수령) 계좌
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  <span class="badge bg-light text-body me-2">
                    {{ docContent.receiver_type === 'VENDOR' ? '거래처 지급' : '임직원 계좌' }}
                  </span>
                  {{ docContent.bank_name }} {{ docContent.account_number }} (예금주:
                  {{ docContent.account_holder || '-' }})
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  사용 목적 / 계획
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{
                    docContent.purpose ||
                    docContent.reason ||
                    docContent.content ||
                    docContent.body ||
                    '-'
                  }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.settlement_promise !== false">
                <CTableHeaderCell class="text-center bg-more-light">정산 확약</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-success fw-semibold">
                  <CIcon name="cilCheckCircle" class="me-1" />
                  상기 선급금/가지급금을 수령한 후, 정산 예정일까지 적격 증빙을 첨부하여 전액 정산할
                  것을 확약함
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.note">
                <CTableHeaderCell class="text-center bg-more-light">
                  비고 / 특이사항
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-muted">
                  {{ docContent.note }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 12. 계약 체결 품의서 (CONTRACT / CONTRACT_APPROVAL / CONTRACT_PROPOSAL) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'CONTRACT' ||
            document.doc_type_detail?.form_template_key === 'CONTRACT_APPROVAL' ||
            document.doc_type_detail?.form_template_key === 'CONTRACT_PROPOSAL'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  계약 구분
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="info" class="me-1">
                    {{
                      docContent.contract_type === 'CONSTRUCTION'
                        ? '공사 도급/하도급'
                        : docContent.contract_type === 'SERVICE'
                          ? '용역/설계/감리/PM'
                          : docContent.contract_type === 'PURCHASE'
                            ? '물품공급/자재구매'
                            : docContent.contract_type === 'LEASE'
                              ? '부동산 임대차'
                              : docContent.contract_type === 'MOU_NDA'
                                ? 'MOU/NDA'
                                : '일반 계약'
                    }}
                  </CBadge>
                  <CBadge color="secondary">
                    {{
                      docContent.contract_kind === 'CHANGE'
                        ? '변경 계약'
                        : docContent.contract_kind === 'RENEWAL'
                          ? '갱신 계약'
                          : '신규 계약'
                    }}
                  </CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  계약 건명
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-body">
                  {{ docContent.contract_name || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">계약 상대방</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  <span class="fw-bold">{{ docContent.contractor_name || '-' }}</span>
                  <span v-if="docContent.contractor_ceo" class="text-muted ms-2">
                    (대표: {{ docContent.contractor_ceo }})
                  </span>
                  <span v-if="docContent.contractor_reg_number" class="text-muted ms-2">
                    | 사업자: {{ docContent.contractor_reg_number }}
                  </span>
                  <span v-if="docContent.contractor_contact" class="text-muted ms-2">
                    | 연락처: {{ docContent.contractor_contact }}
                  </span>
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">계약 금액</CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
                  {{
                    (Number(docContent.contract_amount ?? docContent.amount) || 0).toLocaleString()
                  }}
                  원
                  <span class="small fw-normal text-muted ms-1">
                    ({{
                      docContent.vat_type === 'INCLUDED'
                        ? 'VAT 포함'
                        : docContent.vat_type === 'ZERO_TAX'
                          ? '면세'
                          : 'VAT 별도'
                    }})
                  </span>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">계약 기간</CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-semibold text-primary">
                  {{ docContent.contract_start_date || '-' }} ~
                  {{ docContent.contract_end_date || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.payment_terms">
                <CTableHeaderCell class="text-center bg-more-light">
                  대금 지급 조건
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.payment_terms }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.warranty_terms">
                <CTableHeaderCell class="text-center bg-more-light">
                  이행 / 하자보증
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.warranty_terms }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  체결 사유 / 배경
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{
                    docContent.purpose_reason ||
                    docContent.purpose ||
                    docContent.reason ||
                    docContent.content ||
                    docContent.body ||
                    '-'
                  }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.special_terms || docContent.note">
                <CTableHeaderCell class="text-center bg-more-light">특약 / 비고</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-muted" style="white-space: pre-wrap">
                  {{ docContent.special_terms || docContent.note }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 13. 계약 변경 / 해지 품의서 (CONTRACT_CHANGE / CONTRACT_TERMINATION / CONTRACT_AMENDMENT) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'CONTRACT_CHANGE' ||
            document.doc_type_detail?.form_template_key === 'CONTRACT_TERMINATION' ||
            document.doc_type_detail?.form_template_key === 'CONTRACT_AMENDMENT'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  변경/해지 구분
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge :color="docContent.change_type === 'TERMINATION' ? 'danger' : 'warning'">
                    {{
                      docContent.change_type === 'TERMINATION'
                        ? '계약 해지 / 합의 해제'
                        : docContent.change_type === 'AMOUNT_CHANGE'
                          ? '금액 변경(증감)'
                          : docContent.change_type === 'PERIOD_CHANGE'
                            ? '기간 변경(연장)'
                            : docContent.change_type === 'SCOPE_CHANGE'
                              ? '과업/조건 변경'
                              : '복합 변경 (금액+기간)'
                    }}
                  </CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  계약 상대방
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold">
                  {{ docContent.contractor_name || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">원 계약 건명</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  <span class="fw-bold">{{ docContent.original_contract_name || '-' }}</span>
                  <span v-if="docContent.original_contract_no" class="text-muted ms-2">
                    (계약번호: {{ docContent.original_contract_no }})
                  </span>
                  <span v-if="docContent.original_contract_date" class="text-muted ms-2">
                    | 체결일: {{ docContent.original_contract_date }}
                  </span>
                </CTableDataCell>
              </CTableRow>
              <!-- 변경 비교 (비 해지 시) -->
              <template v-if="docContent.change_type !== 'TERMINATION'">
                <CTableRow>
                  <CTableHeaderCell class="text-center bg-more-light">
                    원 계약 금액
                  </CTableHeaderCell>
                  <CTableDataCell class="pl-3">
                    {{ (Number(docContent.original_amount) || 0).toLocaleString() }}
                    원
                  </CTableDataCell>
                  <CTableHeaderCell class="text-center bg-more-light">증감 금액</CTableHeaderCell>
                  <CTableDataCell
                    class="pl-3 fw-bold"
                    :class="
                      (Number(docContent.change_amount) || 0) >= 0 ? 'text-danger' : 'text-primary'
                    "
                  >
                    {{ (Number(docContent.change_amount) || 0) >= 0 ? '+' : ''
                    }}{{ (Number(docContent.change_amount) || 0).toLocaleString() }} 원
                  </CTableDataCell>
                </CTableRow>
                <CTableRow>
                  <CTableHeaderCell class="text-center bg-more-light">
                    최종 변경 금액
                  </CTableHeaderCell>
                  <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
                    {{
                      (
                        Number(
                          docContent.final_amount ??
                            Number(docContent.original_amount || 0) +
                              Number(docContent.change_amount || 0),
                        ) || 0
                      ).toLocaleString()
                    }}
                    원
                  </CTableDataCell>
                  <CTableHeaderCell class="text-center bg-more-light">
                    변경 후 종료일
                  </CTableHeaderCell>
                  <CTableDataCell class="pl-3 fw-semibold text-primary">
                    {{ docContent.final_end_date || '-' }}
                    <span v-if="docContent.period_change_desc" class="small text-muted ms-1"
                      >({{ docContent.period_change_desc }})</span
                    >
                  </CTableDataCell>
                </CTableRow>
              </template>
              <!-- 해지 시 -->
              <template v-else>
                <CTableRow>
                  <CTableHeaderCell class="text-center bg-more-light">해지 기준일</CTableHeaderCell>
                  <CTableDataCell class="pl-3 fw-bold text-danger">
                    {{ docContent.termination_date || '-' }}
                  </CTableDataCell>
                  <CTableHeaderCell class="text-center bg-more-light">
                    타절 정산금액
                  </CTableHeaderCell>
                  <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
                    {{ (Number(docContent.settlement_amount) || 0).toLocaleString() }}
                    원
                  </CTableDataCell>
                </CTableRow>
                <CTableRow v-if="docContent.penalty_terms">
                  <CTableHeaderCell class="text-center bg-more-light">
                    위약 / 보증몰취
                  </CTableHeaderCell>
                  <CTableDataCell colspan="3" class="pl-3 text-danger">
                    {{ docContent.penalty_terms }}
                  </CTableDataCell>
                </CTableRow>
              </template>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  변경 / 해지 사유
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{
                    docContent.change_reason ||
                    docContent.purpose ||
                    docContent.reason ||
                    docContent.content ||
                    docContent.body ||
                    '-'
                  }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.subsequent_plan || docContent.note">
                <CTableHeaderCell class="text-center bg-more-light">
                  후속 대책 / 비고
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-muted" style="white-space: pre-wrap">
                  {{ docContent.subsequent_plan || docContent.note }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 14. 법무 검토서 (LEGAL_REVIEW / LEGAL_CONSULTATION / LEGAL_ADVICE) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'LEGAL_REVIEW' ||
            document.doc_type_detail?.form_template_key === 'LEGAL_CONSULTATION' ||
            document.doc_type_detail?.form_template_key === 'LEGAL_ADVICE'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  검토 분야
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="primary" class="me-1">
                    {{
                      docContent.review_type === 'CONTRACT_REVIEW'
                        ? '계약서/협약서 검토'
                        : docContent.review_type === 'LITIGATION_DISPUTE'
                          ? '소송/분쟁 대응'
                          : docContent.review_type === 'REGULATORY_COMPLIANCE'
                            ? '법령해석/인허가'
                            : docContent.review_type === 'INTERNAL_RULE'
                              ? '사규/내부규정'
                              : docContent.review_type === 'CLAIM_NOTICE'
                                ? '내용증명/공문'
                                : '법률 자문'
                    }}
                  </CBadge>
                  <CBadge
                    :color="
                      docContent.urgency === 'VERY_URGENT'
                        ? 'danger'
                        : docContent.urgency === 'URGENT'
                          ? 'warning'
                          : 'secondary'
                    "
                  >
                    {{
                      docContent.urgency === 'VERY_URGENT'
                        ? '당일 긴급'
                        : docContent.urgency === 'URGENT'
                          ? '긴급(1~2일)'
                          : '보통'
                    }}
                  </CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  회신 희망일
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold">
                  {{ docContent.review_due_date || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">의뢰 건명</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 fw-bold text-body">
                  {{ docContent.case_title || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.counterparty || docContent.dispute_amount">
                <CTableHeaderCell class="text-center bg-more-light">상대방 / 가액</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  <span v-if="docContent.counterparty" class="fw-semibold me-3">
                    상대방: {{ docContent.counterparty }}
                  </span>
                  <span v-if="docContent.dispute_amount" class="text-danger fw-bold">
                    관련 가액:
                    {{ (Number(docContent.dispute_amount) || 0).toLocaleString() }} 원
                  </span>
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  사실관계 및 배경
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{
                    docContent.background ||
                    docContent.purpose ||
                    docContent.reason ||
                    docContent.content ||
                    docContent.body ||
                    '-'
                  }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  주요 쟁점 사항
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{ docContent.key_issues || '-' }}
                </CTableDataCell>
              </CTableRow>
              <!-- 법무팀 검토 결과 및 종합의견 -->
              <CTableRow v-if="docContent.legal_opinion || docContent.risk_level">
                <CTableHeaderCell class="text-center bg-primary bg-opacity-10 text-primary">
                  법무 검토 결과
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 bg-light">
                  <div class="mb-2">
                    <span class="small fw-semibold me-2">법적 리스크 수준:</span>
                    <CBadge
                      :color="
                        docContent.risk_level === 'HIGH'
                          ? 'danger'
                          : docContent.risk_level === 'MEDIUM'
                            ? 'warning'
                            : 'success'
                      "
                    >
                      {{
                        docContent.risk_level === 'HIGH'
                          ? '높음 (중대 불리조항)'
                          : docContent.risk_level === 'MEDIUM'
                            ? '중간 (수정 권고)'
                            : '낮음 (체결 가능)'
                      }}
                    </CBadge>
                  </div>
                  <div style="white-space: pre-wrap" class="fw-semibold text-body">
                    {{ docContent.legal_opinion || '상세 검토 의견이 등록되지 않았습니다.' }}
                  </div>
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.enclosed_docs || docContent.note">
                <CTableHeaderCell class="text-center bg-more-light">
                  첨부서류 / 비고
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-muted">
                  {{ docContent.enclosed_docs || docContent.note }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 15. 사업 검토서 (BUSINESS_REVIEW / PROJECT_FEASIBILITY / BIZ_FEASIBILITY / PROJECT_REVIEW / INVESTMENT_REVIEW) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'BUSINESS_REVIEW' ||
            document.doc_type_detail?.form_template_key === 'PROJECT_FEASIBILITY' ||
            document.doc_type_detail?.form_template_key === 'BIZ_FEASIBILITY' ||
            document.doc_type_detail?.form_template_key === 'PROJECT_REVIEW' ||
            document.doc_type_detail?.form_template_key === 'INVESTMENT_REVIEW'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  사업명 (프로젝트)
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-body fs-6">
                  {{ docContent.project_name || docContent.case_title || '-' }}
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  사업 유형
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="info">
                    {{
                      docContent.biz_type === 'DEV_SELF'
                        ? '자체 개발사업'
                        : docContent.biz_type === 'DEV_TRUST'
                          ? '토지신탁'
                          : docContent.biz_type === 'CONTRACT_CIVIL'
                            ? '단순 도급(시공)'
                            : docContent.biz_type === 'REDEVELOPMENT'
                              ? '재개발/재건축'
                              : docContent.biz_type === 'PF_INVEST'
                                ? '지분투자/공동개발'
                                : '신규 사업'
                    }}
                  </CBadge>
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  사업 부지 위치
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.location || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow
                v-if="
                  docContent.building_scale || docContent.land_area || docContent.gross_floor_area
                "
              >
                <CTableHeaderCell class="text-center bg-more-light">
                  사업 규모 / 면적
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  <span v-if="docContent.building_scale" class="me-3 fw-semibold">
                    {{ docContent.building_scale }}
                  </span>
                  <span v-if="docContent.land_area" class="me-3 text-muted">
                    대지: {{ docContent.land_area }} ㎡
                  </span>
                  <span v-if="docContent.gross_floor_area" class="text-muted">
                    연면적: {{ docContent.gross_floor_area }} ㎡
                  </span>
                </CTableDataCell>
              </CTableRow>
              <!-- 수지 분석 요약 -->
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  총 분양/매출 수입
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-primary">
                  {{ (Number(docContent.total_revenue) || 0).toLocaleString() }} 원
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">
                  총 사업비(지출)
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-danger">
                  {{ (Number(docContent.total_cost) || 0).toLocaleString() }} 원
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  예상 세전 이익
                </CTableHeaderCell>
                <CTableDataCell
                  class="pl-3 fw-bold fs-6"
                  :class="
                    (Number(
                      docContent.net_profit ??
                        Number(docContent.total_revenue || 0) - Number(docContent.total_cost || 0),
                    ) || 0) >= 0
                      ? 'text-success'
                      : 'text-danger'
                  "
                >
                  {{
                    (
                      Number(
                        docContent.net_profit ??
                          Number(docContent.total_revenue || 0) -
                            Number(docContent.total_cost || 0),
                      ) || 0
                    ).toLocaleString()
                  }}
                  원
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">수익률 (ROI)</CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-body">
                  {{ docContent.profit_rate ?? '-' }} %
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.required_equity || docContent.pf_loan_amount">
                <CTableHeaderCell class="text-center bg-more-light">
                  금융 / 조달 계획
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  <span v-if="docContent.required_equity" class="me-3">
                    자기자본(Equity):
                    <strong>
                      {{ (Number(docContent.required_equity) || 0).toLocaleString() }} 원
                    </strong>
                  </span>
                  <span v-if="docContent.pf_loan_amount">
                    PF 조달:
                    <strong>
                      {{ (Number(docContent.pf_loan_amount) || 0).toLocaleString() }} 원
                    </strong>
                  </span>
                </CTableDataCell>
              </CTableRow>
              <!-- 사업 일정 -->
              <CTableRow
                v-if="
                  docContent.land_secure_date ||
                  docContent.approval_target_date ||
                  docContent.start_date ||
                  docContent.completion_date
                "
              >
                <CTableHeaderCell class="text-center bg-more-light">
                  주요 추진 일정
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 small">
                  <span v-if="docContent.land_secure_date" class="me-2">
                    토지확보: {{ docContent.land_secure_date }} |
                  </span>
                  <span v-if="docContent.approval_target_date" class="me-2">
                    사업승인: {{ docContent.approval_target_date }} |
                  </span>
                  <span v-if="docContent.start_date" class="me-2">
                    착공/분양: {{ docContent.start_date }} |
                  </span>
                  <span v-if="docContent.completion_date">
                    준공: {{ docContent.completion_date }}
                  </span>
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.market_analysis">
                <CTableHeaderCell class="text-center bg-more-light">
                  입지 및 분양성
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{ docContent.market_analysis }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.risk_factors">
                <CTableHeaderCell class="text-center bg-more-light">
                  리스크 및 대책
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{ docContent.risk_factors }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">종합 검토의견</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{
                    docContent.recommendation ||
                    docContent.purpose ||
                    docContent.reason ||
                    docContent.content ||
                    docContent.body ||
                    '-'
                  }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.enclosed_docs || docContent.note">
                <CTableHeaderCell class="text-center bg-more-light">
                  첨부 서류 / 비고
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-muted">
                  {{ docContent.enclosed_docs || docContent.note }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 16. 사업추진 승인서 (BUSINESS_APPROVAL / PROJECT_APPROVAL / DEV_APPROVAL / INVESTMENT_APPROVAL) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'BUSINESS_APPROVAL' ||
            document.doc_type_detail?.form_template_key === 'PROJECT_APPROVAL' ||
            document.doc_type_detail?.form_template_key === 'DEV_APPROVAL' ||
            document.doc_type_detail?.form_template_key === 'INVESTMENT_APPROVAL'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  사업명 (프로젝트)
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-body fs-6">
                  {{ docContent.project_name || docContent.case_title || '-' }}
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  승인 의결 구분
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="success">
                    {{
                      docContent.approval_type === 'NEW_LAUNCH'
                        ? '사업 공식 론칭'
                        : docContent.approval_type === 'LAND_ACQUISITION'
                          ? '토지 매매/계약금 집행'
                          : docContent.approval_type === 'SPC_ESTABLISH'
                            ? 'SPC/PFV 설립'
                            : docContent.approval_type === 'PF_EXECUTION'
                              ? '본 PF 약정/인출'
                              : docContent.approval_type === 'CONSTRUCTION_START'
                                ? '시공 도급/착공'
                                : '주요 사업 승인'
                    }}
                  </CBadge>
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  사업 부지 위치
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">{{ docContent.location || '-' }}</CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">
                  사업 규모 / 용도
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  {{ docContent.biz_scale_summary || '-' }}
                </CTableDataCell>
              </CTableRow>
              <!-- 금회 승인 요청 예산 및 전체 사업비 -->
              <CTableRow class="bg-success bg-opacity-10">
                <CTableHeaderCell class="text-center text-success fw-bold">
                  금회 승인 요청액
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-success fs-5">
                  {{
                    (
                      Number(
                        docContent.requested_amount ??
                          docContent.approval_budget ??
                          docContent.amount,
                      ) || 0
                    ).toLocaleString()
                  }}
                  원
                </CTableDataCell>
                <CTableHeaderCell class="text-center">전체 총사업비</CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
                  {{ (Number(docContent.total_project_cost) || 0).toLocaleString() }} 원
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.total_expected_revenue || docContent.expected_profit">
                <CTableHeaderCell class="text-center bg-more-light">
                  예상 총분양수입
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-semibold text-primary">
                  {{ (Number(docContent.total_expected_revenue) || 0).toLocaleString() }}
                  원
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light">
                  예상 세전 이익
                </CTableHeaderCell>
                <CTableDataCell
                  class="pl-3 fw-semibold"
                  :class="
                    (Number(
                      docContent.expected_profit ??
                        Number(docContent.total_expected_revenue || 0) -
                          Number(docContent.total_project_cost || 0),
                    ) || 0) >= 0
                      ? 'text-primary'
                      : 'text-danger'
                  "
                >
                  {{
                    (
                      Number(
                        docContent.expected_profit ??
                          Number(docContent.total_expected_revenue || 0) -
                            Number(docContent.total_project_cost || 0),
                      ) || 0
                    ).toLocaleString()
                  }}
                  원
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.budget_usage_plan">
                <CTableHeaderCell class="text-center bg-more-light">
                  예산 집행 내역
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 fw-semibold text-body">
                  {{ docContent.budget_usage_plan }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  승인 의결 사항
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{
                    docContent.resolution_matters ||
                    docContent.purpose ||
                    docContent.reason ||
                    docContent.content ||
                    docContent.body ||
                    '-'
                  }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.pm_lead || docContent.target_schedule">
                <CTableHeaderCell class="text-center bg-more-light">
                  총괄 PM / 일정
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  <span v-if="docContent.pm_lead" class="me-3 fw-semibold">
                    PM/부서: {{ docContent.pm_lead }}
                  </span>
                  <span v-if="docContent.target_schedule" class="text-muted">
                    추진일정: {{ docContent.target_schedule }}
                  </span>
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.expected_effects || docContent.risk_mitigation">
                <CTableHeaderCell class="text-center bg-more-light">
                  기대효과 / 대책
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{ docContent.expected_effects || docContent.risk_mitigation }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.enclosed_docs || docContent.note">
                <CTableHeaderCell class="text-center bg-more-light">
                  첨부 서류 / 비고
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-muted">
                  {{ docContent.enclosed_docs || docContent.note }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 17. 프로젝트 주요 의사결정서 (PROJECT_DECISION / PROJECT_KEY_DECISION / DECISION_PROPOSAL / KEY_DECISION) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'PROJECT_DECISION' ||
            document.doc_type_detail?.form_template_key === 'PROJECT_KEY_DECISION' ||
            document.doc_type_detail?.form_template_key === 'DECISION_PROPOSAL' ||
            document.doc_type_detail?.form_template_key === 'KEY_DECISION'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  현안 분야
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  <CBadge color="danger" class="me-1">
                    {{
                      docContent.decision_type === 'DESIGN_SPEC'
                        ? '설계변경/스펙'
                        : docContent.decision_type === 'SALES_PRICING'
                          ? '분양가/분양조건'
                          : docContent.decision_type === 'CONSTRUCTION_METHOD'
                            ? '시공공법/자재'
                            : docContent.decision_type === 'FINANCIAL_STRUCTURING'
                              ? '금융구조/PF'
                              : docContent.decision_type === 'CLAIM_DISPUTE'
                                ? '민원/분쟁대응'
                                : docContent.decision_type === 'CONTRACTOR_TERMINATION'
                                  ? '업체선정/타절'
                                  : '프로젝트 의사결정'
                    }}
                  </CBadge>
                  <CBadge
                    :color="
                      docContent.urgency === 'CRITICAL'
                        ? 'danger'
                        : docContent.urgency === 'URGENT'
                          ? 'warning'
                          : 'secondary'
                    "
                  >
                    {{
                      docContent.urgency === 'CRITICAL'
                        ? '즉시 결정'
                        : docContent.urgency === 'URGENT'
                          ? '긴급'
                          : '보통'
                    }}
                  </CBadge>
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  결정 목표일
                </CTableHeaderCell>
                <CTableDataCell class="pl-3 fw-bold">
                  {{ docContent.decision_due_date || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">심의 안건명</CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 fw-bold text-body fs-6">
                  {{ docContent.decision_subject || docContent.case_title || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.financial_impact">
                <CTableHeaderCell class="text-center bg-more-light">
                  재무적 영향(비용)
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 fw-bold text-danger fs-6">
                  {{ (Number(docContent.financial_impact) || 0).toLocaleString() }} 원
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  현안 배경 및 문제점
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{
                    docContent.background_issue ||
                    docContent.purpose ||
                    docContent.reason ||
                    docContent.content ||
                    docContent.body ||
                    '-'
                  }}
                </CTableDataCell>
              </CTableRow>
              <!-- 대안 비교 -->
              <CTableRow v-if="docContent.option_1">
                <CTableHeaderCell class="text-center bg-secondary bg-opacity-10 text-secondary">
                  대안 1 (원안)
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{ docContent.option_1 }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.option_2">
                <CTableHeaderCell class="text-center bg-primary bg-opacity-10 text-primary fw-bold">
                  대안 2 (추천안)
                </CTableHeaderCell>
                <CTableDataCell
                  colspan="3"
                  class="pl-3 bg-light fw-semibold text-body"
                  style="white-space: pre-wrap"
                >
                  {{ docContent.option_2 }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.option_3">
                <CTableHeaderCell class="text-center bg-more-light">
                  대안 3 (기타안)
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{ docContent.option_3 }}
                </CTableDataCell>
              </CTableRow>
              <!-- 추천안 -->
              <CTableRow class="bg-warning bg-opacity-10">
                <CTableHeaderCell class="text-center fw-bold text-body">
                  주관부서 추천안
                </CTableHeaderCell>
                <CTableDataCell
                  colspan="3"
                  class="pl-3 fw-bold text-body"
                  style="white-space: pre-wrap"
                >
                  {{ docContent.recommendation || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.action_plan">
                <CTableHeaderCell class="text-center bg-more-light">
                  향후 조치 계획
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3">
                  {{ docContent.action_plan }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.enclosed_docs || docContent.note">
                <CTableHeaderCell class="text-center bg-more-light">
                  첨부 서류 / 비고
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-muted">
                  {{ docContent.enclosed_docs || docContent.note }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 18. 일반 업무 품의서 (GENERAL / GENERAL_PROPOSAL / BIZ_APPROVAL / PROPOSAL / GENERAL_DRAFT) -->
        <template
          v-else-if="
            document.doc_type_detail?.form_template_key === 'GENERAL' ||
            document.doc_type_detail?.form_template_key === 'GENERAL_PROPOSAL' ||
            document.doc_type_detail?.form_template_key === 'BIZ_APPROVAL' ||
            document.doc_type_detail?.form_template_key === 'PROPOSAL' ||
            document.doc_type_detail?.form_template_key === 'GENERAL_DRAFT'
          "
        >
          <CTable small bordered responsive class="mb-3">
            <CTableBody>
              <CTableRow v-if="docContent.purpose">
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  품의 목적
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 fw-bold text-body fs-6">
                  {{ docContent.purpose }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.schedule || docContent.budget_account">
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  추진 일정
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  {{ docContent.schedule || '-' }}
                </CTableDataCell>
                <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
                  예산 과목
                </CTableHeaderCell>
                <CTableDataCell class="pl-3">
                  {{ getBudgetAccountLabel(docContent.budget_account) }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.budget !== undefined || docContent.amount !== undefined">
                <CTableHeaderCell class="text-center bg-more-light"> 소요 예산 </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 fw-bold text-danger fs-6">
                  {{ (Number(docContent.budget ?? docContent.amount) || 0).toLocaleString() }} 원
                </CTableDataCell>
              </CTableRow>
              <CTableRow>
                <CTableHeaderCell class="text-center bg-more-light">
                  세부 품의 내용
                </CTableHeaderCell>
                <CTableDataCell
                  colspan="3"
                  class="pl-3"
                  style="white-space: pre-wrap; line-height: 1.6"
                >
                  {{ docContent.content || docContent.body || docContent.description || '-' }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.expected_effect">
                <CTableHeaderCell class="text-center bg-more-light"> 기대 효과 </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
                  {{ docContent.expected_effect }}
                </CTableDataCell>
              </CTableRow>
              <CTableRow v-if="docContent.note">
                <CTableHeaderCell class="text-center bg-more-light">
                  비고 / 특이사항
                </CTableHeaderCell>
                <CTableDataCell colspan="3" class="pl-3 text-muted">
                  {{ docContent.note }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>

        <!-- 19. 기본 일반 본문 렌더링 fallback (body/content가 있거나 기타 동적 필드) -->
        <template v-else>
          <!-- body 또는 content 단독 텍스트인 경우 -->
          <div
            v-if="docContent.body || docContent.content || docContent.description"
            class="p-3 bg-more-light border rounded mb-3"
            style="white-space: pre-wrap; line-height: 1.6"
          >
            {{ docContent.body || docContent.content || docContent.description }}
          </div>

          <!-- 기타 다중 key-value 필드가 있는 경우 테이블로 렌더링 -->
          <CTable
            v-if="
              Object.keys(docContent).some(
                k => !['body', 'content', 'description'].includes(String(k)),
              )
            "
            small
            bordered
            responsive
            class="mb-0"
          >
            <CTableBody>
              <CTableRow
                v-for="(val, key) in docContent"
                :key="key"
                v-show="!['body', 'content', 'description'].includes(String(key))"
              >
                <CTableHeaderCell class="text-center bg-more-light" style="width: 140px">
                  {{ String(key) }}
                </CTableHeaderCell>
                <CTableDataCell class="pl-3" style="white-space: pre-wrap">
                  {{ typeof val === 'object' ? JSON.stringify(val, null, 2) : String(val) }}
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>

          <div v-if="!Object.keys(docContent).length" class="text-center text-muted py-3">
            등록된 상세 품의 내용이 없습니다.
          </div>
        </template>
      </CCardBody>
    </CCard>

    <!-- 첨부파일 목록 카드 -->
    <CCard v-if="document.attachments?.length || document.attachment" class="mb-3">
      <CCardHeader class="d-flex align-items-center justify-content-between">
        <div class="fw-semibold">
          <CIcon name="cilPaperclip" class="me-1 text-primary" />
          첨부파일
          <CBadge color="secondary" size="sm" class="ms-1">
            {{
              (document.attachments?.length || 0) +
              (document.attachment && !document.attachments?.length ? 1 : 0)
            }}개
          </CBadge>
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
                  :href="att.file_url || att.file"
                  target="_blank"
                  class="text-decoration-none fw-medium text-body"
                >
                  {{ att.file_name || '첨부파일' }}
                </a>
                <span class="text-muted small ms-2"> ({{ formatFileSize(att.file_size) }}) </span>
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
                  <div class="d-flex align-items-center gap-1 mb-1">
                    <CBadge
                      :color="
                        getAction(step, approver.id)!.action === 'approved' ? 'success' : 'danger'
                      "
                    >
                      {{
                        getAction(step, approver.id)!.action === 'approved' ? '✓ 승인' : '✗ 반려'
                      }}
                    </CBadge>
                    <CBadge
                      v-if="getAction(step, approver.id)!.is_delegated"
                      color="warning"
                      size="sm"
                      title="대리 결재"
                    >
                      대결: {{ getAction(step, approver.id)!.approver.full_name }}
                    </CBadge>
                  </div>
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

    <CRow>
      <CCol class="text-right">
        <v-btn color="light" class="text-body" @click="toList" flat> 목록으로 </v-btn>
      </CCol>
    </CRow>
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
