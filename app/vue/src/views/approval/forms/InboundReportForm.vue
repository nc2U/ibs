<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import type { ApprovalContent } from '@/store/types/approval'
import {
  INBOUND_ACTION_TYPE_OPTIONS,
  INBOUND_URGENCY_OPTIONS,
  asNum,
  asStr,
  firstStr,
} from '../utils/approvalMeta'

const props = defineProps<{
  modelValue: ApprovalContent
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: ApprovalContent): void
}>()

const updateField = (key: string, val: unknown) => {
  const updated: ApprovalContent = {
    ...props.modelValue,
    [key]: val,
  }

  // 예산 소요액 변경 시 amount 동기화 (전결 결재선 연동)
  if (key === 'action_budget') {
    updated.amount = asNum(val)
  }

  emit('update:modelValue', updated)
}

const replyPlannedDate = computed({
  get: () => asStr(props.modelValue.reply_planned_date),
  set: (val: string) => updateField('reply_planned_date', val),
})

const replyDueDate = computed({
  get: () => asStr(props.modelValue.reply_due_date),
  set: (val: string) => updateField('reply_due_date', val),
})

const receivedDate = computed({
  get: () => asStr(props.modelValue.received_date),
  set: (val: string) => updateField('received_date', val),
})

const formattedBudget = computed(() => {
  const b = props.modelValue.action_budget ?? props.modelValue.amount
  return b ? asNum(b).toLocaleString() : ''
})

onMounted(() => {
  const initial: ApprovalContent = { ...props.modelValue }
  let changed = false

  if (!asStr(initial.action_type)) {
    initial.action_type = 'REPLY_LETTER'
    changed = true
  }
  if (!asStr(initial.urgency)) {
    initial.urgency = 'NORMAL'
    changed = true
  }
  if (initial.action_budget === undefined && initial.amount) {
    initial.action_budget = initial.amount
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="inbound-report-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilEnvelopeClosed" class="me-1" />
      수신 공문 개요 및 대응 보고
    </h6>

    <!-- 수신 공문 기본 정보 (접수처 / 문서번호 / 접수번호) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">발신처</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.sender_name)"
          placeholder="예: 인천광역시 연수구청 도시계획과"
          required
          @input="updateField('sender_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label">발신 문서번호</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.document_number)"
          placeholder="예: 도시계획과-1234호"
          @input="updateField('document_number', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 사내 접수번호 & 접수일자 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">사내 접수번호</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.receipt_number)"
          placeholder="예: IBS-접수-2026-001"
          @input="updateField('receipt_number', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label">접수일자</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="receivedDate" placeholder="접수일자" />
      </CCol>
    </CRow>

    <!-- 처리 방향 & 긴급도 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">처리 방향</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="asStr(modelValue.action_type, 'REPLY_LETTER')"
          required
          @change="updateField('action_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in INBOUND_ACTION_TYPE_OPTIONS" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required">긴급도</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="asStr(modelValue.urgency, 'NORMAL')"
          required
          @change="updateField('urgency', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="u in INBOUND_URGENCY_OPTIONS" :key="u.value" :value="u.value">
            {{ u.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 회신 마감기한 & 회신 예정일 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">회신 마감기한</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="replyDueDate" placeholder="회신 마감기한" />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label">회신 예정일</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="replyPlannedDate" placeholder="회신 공문 발송 예정일" />
      </CCol>
    </CRow>

    <!-- 수신 공문 제목 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">수신공문 제목</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="asStr(modelValue.letter_subject)"
          placeholder="접수된 원본 공문의 제목"
          required
          @input="updateField('letter_subject', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 수신 공문 주요 내용 (요약) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">수신 내용 요약</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="firstStr(modelValue.letter_summary, modelValue.letter_content)"
          rows="3"
          placeholder="접수된 공문의 핵심 요구사항 및 주요 골자를 요약 기재합니다."
          @input="updateField('letter_summary', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <hr class="my-3 text-muted" />

    <!-- 내부 검토의견 및 대응 계획 (기안 핵심) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">검토 및 조치계획</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="firstStr(modelValue.review_opinion, modelValue.body)"
          rows="5"
          placeholder="공문 접수에 따른 내부 검토의견, 회신 방향, 조치 방안 및 추진 일정을 구체적으로 작성하십시오."
          required
          @input="updateField('review_opinion', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 소요 예산 (선택) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">조치 소요예산</CFormLabel>
      <CCol sm="4">
        <CInputGroup>
          <CFormInput
            type="number"
            min="0"
            :value="asStr(modelValue.action_budget)"
            placeholder="0"
            @input="updateField('action_budget', ($event.target as HTMLInputElement).value)"
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
        <div
          v-if="formattedBudget && formattedBudget !== '0'"
          class="form-text text-end text-primary fw-semibold"
        >
          {{ formattedBudget }} 원
        </div>
      </CCol>
    </CRow>
  </div>
</template>
