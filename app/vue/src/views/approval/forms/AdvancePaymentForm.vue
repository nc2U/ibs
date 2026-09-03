<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const advanceTypes = [
  { value: 'ADVANCE_PAY', label: '가지급금 (업무용 선지급 경비)' },
  { value: 'PREPAYMENT', label: '선급금 (계약상 대금 선지급)' },
  { value: 'IMPREST_FUND', label: '전도금 (현장/부서 상비 운영비)' },
  { value: 'EVENT_FUND', label: '행사 / 프로젝트 진행비' },
  { value: 'OTHER', label: '기타 선급금' },
]

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // advance_amount 변경 시 amount 동기화 (전결 결재선 연동)
  if (key === 'advance_amount') {
    updated.amount = Number(val) || 0
  }

  emit('update:modelValue', updated)
}

const paymentDueDate = computed({
  get: () => props.modelValue.payment_due_date ?? '',
  set: (val: string) => updateField('payment_due_date', val),
})

const settlementDueDate = computed({
  get: () => props.modelValue.settlement_due_date ?? '',
  set: (val: string) => updateField('settlement_due_date', val),
})

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.advance_type) {
    initial.advance_type = 'ADVANCE_PAY'
    changed = true
  }
  if (!initial.payment_due_date) {
    initial.payment_due_date = new Date().toISOString().substring(0, 10)
    changed = true
  }
  if (!initial.settlement_due_date) {
    // 기본 지급일로부터 14일 후
    const d = new Date()
    d.setDate(d.getDate() + 14)
    initial.settlement_due_date = d.toISOString().substring(0, 10)
    changed = true
  }
  if (initial.advance_amount === undefined && initial.amount) {
    initial.advance_amount = initial.amount
    changed = true
  }
  if (initial.receiver_type === undefined) {
    initial.receiver_type = 'EMPLOYEE'
    changed = true
  }
  if (initial.settlement_promise === undefined) {
    initial.settlement_promise = true
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="advance-payment-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-danger">
      <CIcon name="cilCash" class="me-1" />
      선급금 / 가지급금 신청 정보
    </h6>

    <!-- 구분 & 지급요청일 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">신청 구분</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.advance_type ?? 'ADVANCE_PAY'"
          required
          @change="updateField('advance_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in advanceTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">지급 요청일</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="paymentDueDate" required placeholder="지급 요청일 선택" />
      </CCol>
    </CRow>

    <!-- 신청 금액 & 정산 예정일 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">신청 금액</CFormLabel>
      <CCol sm="4">
        <CInputGroup>
          <CFormInput
            type="number"
            min="0"
            step="10000"
            class="text-end fw-bold text-danger fs-6"
            :value="modelValue.advance_amount ?? modelValue.amount ?? 0"
            placeholder="0"
            required
            @input="
              updateField('advance_amount', Number(($event.target as HTMLInputElement).value) || 0)
            "
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">정산 예정일</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="settlementDueDate" required placeholder="정산 예정일 선택" />
      </CCol>
    </CRow>

    <!-- 입금(수령) 계좌 정보 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">입금 계좌</CFormLabel>
      <CCol sm="2">
        <CFormSelect
          :value="modelValue.receiver_type ?? 'EMPLOYEE'"
          @change="updateField('receiver_type', ($event.target as HTMLSelectElement).value)"
        >
          <option value="EMPLOYEE">임직원 계좌</option>
          <option value="VENDOR">거래처 직접지급</option>
          <option value="OTHER">기타 계좌</option>
        </CFormSelect>
      </CCol>
      <CCol sm="2">
        <CFormInput
          :value="modelValue.bank_name ?? ''"
          placeholder="은행명"
          required
          @input="updateField('bank_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CCol sm="3">
        <CFormInput
          :value="modelValue.account_number ?? ''"
          placeholder="계좌번호"
          required
          @input="updateField('account_number', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CCol sm="3">
        <CFormInput
          :value="modelValue.account_holder ?? ''"
          placeholder="예금주명"
          required
          @input="updateField('account_holder', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 사용 목적 및 세부 집행 계획 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">사용 목적 / 계획</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.purpose ?? ''"
          rows="4"
          placeholder="선급금/가지급금을 신청하는 구체적 사유 및 세부 자금 집행 계획을 상세히 기술해 주세요."
          required
          @input="updateField('purpose', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 정산 확약 동의 체크 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">정산 확약</CFormLabel>
      <CCol sm="10" class="d-flex align-items-center">
        <CFormCheck
          id="settlementPromiseCheck"
          label="상기 가지급금/선급금을 수령한 후, 정산 예정일까지 적격 증빙을 첨부하여 전액 정산할 것을 확약합니다."
          :checked="modelValue.settlement_promise ?? true"
          @change="updateField('settlement_promise', ($event.target as HTMLInputElement).checked)"
        />
      </CCol>
    </CRow>

    <!-- 비고 / 특이사항 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">비고 / 특이사항</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.note ?? ''"
          placeholder="추가 전달 사항 또는 계약서 첨부 안내"
          @input="updateField('note', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
