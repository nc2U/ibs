<script setup lang="ts">
import { computed, onMounted } from 'vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const budgetAccounts = [
  { value: 'NONE', label: '예산 비소요 (0원)' },
  { value: 'GENERAL_EXPENSE', label: '일반관리비 / 경상운영비' },
  { value: 'PROJECT_COST', label: '사업비 / 현장 직접비' },
  { value: 'OUTSOURCING', label: '외주 용역비' },
  { value: 'MARKETING', label: '홍보 및 마케팅비' },
  { value: 'ASSET_PURCHASE', label: '자산 취득비' },
  { value: 'OTHER', label: '기타 예산' },
]

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // 예산/금액 변경 시 최상위 amount 동기화 (전결 규정 및 결재선 자동 계산용)
  if (key === 'budget') {
    updated.amount = Number(val) || 0
  }

  emit('update:modelValue', updated)
}

const formattedBudget = computed(() => {
  const b = props.modelValue.budget ?? props.modelValue.amount
  return b ? Number(b).toLocaleString() : ''
})

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.budget_account) {
    initial.budget_account = 'GENERAL_EXPENSE'
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="general-proposal-form p-3 border rounded bg-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilNotes" class="me-1" />
      일반 업무 품의 정보
    </h6>

    <!-- 품의 목적 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">품의 목적</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.purpose ?? ''"
          placeholder="예: 2026년 하반기 사내 정보보안 솔루션 도입 및 교체의 건"
          required
          @input="updateField('purpose', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 추진 일정 & 예산 과목 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">추진 일정/기간</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.schedule ?? ''"
          placeholder="예: 2026.09.01 ~ 2026.10.31 (2개월)"
          @input="updateField('schedule', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label">예산 과목</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.budget_account ?? 'GENERAL_EXPENSE'"
          @change="updateField('budget_account', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="acc in budgetAccounts" :key="acc.value" :value="acc.value">
            {{ acc.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 소요 예산 (원) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">소요 예산 (원)</CFormLabel>
      <CCol sm="4">
        <CInputGroup>
          <CFormInput
            type="number"
            min="0"
            step="10000"
            :value="modelValue.budget ?? modelValue.amount ?? 0"
            placeholder="0"
            @input="updateField('budget', Number(($event.target as HTMLInputElement).value) || 0)"
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
      <CCol sm="6" class="d-flex align-items-center">
        <span v-if="formattedBudget && formattedBudget !== '0'" class="badge bg-secondary p-2">
          금액 확인: <strong>{{ formattedBudget }}</strong> 원 (전결 규정 자동 적용)
        </span>
        <span v-else class="small text-muted">
          * 예산이 소요되지 않는 품의는 0원으로 기재하십시오.
        </span>
      </CCol>
    </CRow>

    <!-- 세부 품의 내용 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">세부 품의 내용</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.content ?? ''"
          rows="6"
          placeholder="추진 배경, 현황 및 문제점, 주요 추진 계획, 세부 산출 내역 등을 상세히 기술해 주세요."
          required
          @input="updateField('content', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 기대 효과 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">기대 효과</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.expected_effect ?? ''"
          rows="2"
          placeholder="업무 효율성 증대, 비용 절감 효과, 리스크 예방 등 기대 효과를 기술해 주세요."
          @input="updateField('expected_effect', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 특이사항 / 비고 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">비고 / 특이사항</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.note ?? ''"
          placeholder="관련 부서 협의 사항 또는 추가 참고 사항을 기재해 주세요."
          @input="updateField('note', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
