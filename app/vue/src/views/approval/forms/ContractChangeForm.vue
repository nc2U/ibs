<script setup lang="ts">
import { computed, onMounted } from 'vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const changeTypes = [
  { value: 'COMPREHENSIVE', label: '복합 변경 (금액 + 기간 변경)' },
  { value: 'AMOUNT_CHANGE', label: '금액 변경 (증액 / 감액)' },
  { value: 'PERIOD_CHANGE', label: '기간 변경 (공기 / 과업기간 연장)' },
  { value: 'SCOPE_CHANGE', label: '과업 범위 및 조건 변경' },
  { value: 'TERMINATION', label: '계약 중도 해지 / 합의 해제' },
]

const originalAmount = computed(() => Number(props.modelValue.original_amount) || 0)
const changeAmount = computed(() => Number(props.modelValue.change_amount) || 0)

const finalCalculatedAmount = computed(() => {
  if (props.modelValue.change_type === 'TERMINATION') {
    return Number(props.modelValue.settlement_amount) || 0
  }
  return originalAmount.value + changeAmount.value
})

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // 금액 변경 시 final_amount 및 결재선용 amount 자동 계산
  if (key === 'original_amount' || key === 'change_amount') {
    const orig = key === 'original_amount' ? Number(val) || 0 : originalAmount.value
    const chg = key === 'change_amount' ? Number(val) || 0 : changeAmount.value
    const fin = orig + chg
    updated.final_amount = fin
    updated.amount = Math.abs(chg) > 0 ? Math.abs(chg) : fin // 변경 증감액 또는 최종액을 결재선 기준으로 반영
  } else if (key === 'settlement_amount') {
    updated.amount = Number(val) || 0
  }

  emit('update:modelValue', updated)
}

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.change_type) {
    initial.change_type = 'COMPREHENSIVE'
    changed = true
  }
  if (!initial.original_contract_date) {
    initial.original_contract_date = new Date().toISOString().substring(0, 10)
    changed = true
  }
  if (initial.original_amount === undefined) {
    initial.original_amount = 0
    changed = true
  }
  if (initial.change_amount === undefined) {
    initial.change_amount = 0
    changed = true
  }
  if (initial.final_amount === undefined) {
    initial.final_amount = 0
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="contract-change-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-warning">
      <CIcon name="cilSync" class="me-1" />
      계약 변경 및 해지 정보
    </h6>

    <!-- 변경 구분 & 원 계약명 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">변경/해지 구분</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.change_type ?? 'COMPREHENSIVE'"
          required
          @change="updateField('change_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in changeTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">계약 상대방</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.contractor_name ?? ''"
          placeholder="상대방 상호/법인명"
          required
          @input="updateField('contractor_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 원 계약 건명 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">원 계약 건명</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.original_contract_name ?? ''"
          placeholder="예: 00현장 토공사 및 흙막이 가시설 도급계약"
          required
          @input="updateField('original_contract_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 원 계약 조건 (변경 전) -->
    <div class="card mb-3 border">
      <div class="card-header bg-more-white py-2 fw-semibold small text-secondary">
        <CIcon name="cilHistory" class="me-1" />
        원 계약 내용 (변경 전)
      </div>
      <div class="card-body p-2">
        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small">원 계약 체결일</CFormLabel>
          <CCol sm="4">
            <CFormInput
              type="date"
              size="sm"
              :value="modelValue.original_contract_date ?? ''"
              @input="
                updateField('original_contract_date', ($event.target as HTMLInputElement).value)
              "
            />
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end">원 계약 종료일</CFormLabel>
          <CCol sm="4">
            <CFormInput
              type="date"
              size="sm"
              :value="modelValue.original_end_date ?? ''"
              @input="updateField('original_end_date', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
        </CRow>
        <CRow>
          <CFormLabel class="col-sm-2 col-form-label small required">원 계약 금액</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000"
                class="text-end fw-semibold"
                :value="modelValue.original_amount ?? 0"
                @input="
                  updateField(
                    'original_amount',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end">원 계약번호</CFormLabel>
          <CCol sm="4">
            <CFormInput
              size="sm"
              :value="modelValue.original_contract_no ?? ''"
              placeholder="관리 계약번호"
              @input="
                updateField('original_contract_no', ($event.target as HTMLInputElement).value)
              "
            />
          </CCol>
        </CRow>
      </div>
    </div>

    <!-- 변경 조건 (금액 / 기간 변경의 경우) -->
    <div v-if="modelValue.change_type !== 'TERMINATION'" class="card mb-3 border border-warning">
      <div class="card-header bg-warning bg-opacity-10 py-2 fw-semibold small text-body">
        <CIcon name="cilCheckCircle" class="me-1 text-warning" />
        변경 후 계약 조건 대조
      </div>
      <div class="card-body p-2">
        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small required">증감 금액</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                step="10000"
                class="text-end fw-bold"
                :class="changeAmount >= 0 ? 'text-danger' : 'text-primary'"
                :value="modelValue.change_amount ?? 0"
                placeholder="증액: 양수(+), 감액: 음수(-)"
                @input="
                  updateField(
                    'change_amount',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small required text-sm-end"
            >최종 계약금액</CFormLabel
          >
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                readonly
                class="text-end fw-bold text-dark bg-light"
                :value="finalCalculatedAmount"
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>

        <CRow>
          <CFormLabel class="col-sm-2 col-form-label small">변경 후 종료일</CFormLabel>
          <CCol sm="4">
            <CFormInput
              type="date"
              size="sm"
              :value="modelValue.final_end_date ?? ''"
              @input="updateField('final_end_date', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end"
            >연장 / 단축 일수</CFormLabel
          >
          <CCol sm="4">
            <CFormInput
              size="sm"
              :value="modelValue.period_change_desc ?? ''"
              placeholder="예: 30일 연장, 2026-12-31까지"
              @input="updateField('period_change_desc', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
        </CRow>
      </div>
    </div>

    <!-- 계약 해지 조건 (해지의 경우) -->
    <div v-else class="card mb-3 border border-danger">
      <div class="card-header bg-danger bg-opacity-10 py-2 fw-semibold small text-danger">
        <CIcon name="cilWarning" class="me-1 text-danger" />
        계약 해지 및 타절 정산 조건
      </div>
      <div class="card-body p-2">
        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small required">해지 기준일</CFormLabel>
          <CCol sm="4">
            <CFormInput
              type="date"
              size="sm"
              :value="modelValue.termination_date ?? ''"
              required
              @input="updateField('termination_date', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small required text-sm-end"
            >타절 정산금액</CFormLabel
          >
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000"
                class="text-end fw-bold text-danger"
                :value="modelValue.settlement_amount ?? 0"
                required
                @input="
                  updateField(
                    'settlement_amount',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
        <CRow>
          <CFormLabel class="col-sm-2 col-form-label small">위약금 / 보증몰취</CFormLabel>
          <CCol sm="10">
            <CFormInput
              size="sm"
              :value="modelValue.penalty_terms ?? ''"
              placeholder="예: 계약보증금 10% 몰취 또는 손해배상 청구 내역"
              @input="updateField('penalty_terms', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
        </CRow>
      </div>
    </div>

    <!-- 변경 / 해지 사유 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">변경/해지 사유</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.change_reason ?? modelValue.purpose ?? ''"
          rows="4"
          placeholder="설계 변경, 물량 증감, 공기 연장, 또는 해지 사유 및 귀책사유를 구체적으로 상세히 기술해 주세요."
          required
          @input="updateField('change_reason', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 후속 조치 계획 및 비고 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">후속 대책 / 비고</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.subsequent_plan ?? modelValue.note ?? ''"
          rows="2"
          placeholder="변경계약 체결 일정, 대체업체 선정 방안 또는 정산서 첨부 안내"
          @input="updateField('subsequent_plan', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
