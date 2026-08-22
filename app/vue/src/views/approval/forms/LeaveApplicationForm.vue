<script setup lang="ts">
import { computed, onMounted } from 'vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const leaveTypes = [
  { value: 'ANNUAL', label: '연차' },
  { value: 'HALF_AM', label: '오전 반차 (0.5일)' },
  { value: 'HALF_PM', label: '오후 반차 (0.5일)' },
  { value: 'SPECIAL', label: '경조사 휴가' },
  { value: 'SICK', label: '병가' },
  { value: 'REWARD', label: '포상 휴가' },
  { value: 'OTHER', label: '기타 휴가' },
]

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // 일수 자동 계산 로직
  if (key === 'leave_type' || key === 'start_date' || key === 'end_date') {
    const lType = updated.leave_type ?? 'ANNUAL'
    const sDate = updated.start_date
    const eDate = updated.end_date

    if (lType === 'HALF_AM' || lType === 'HALF_PM') {
      updated.days_count = 0.5
      if (sDate) updated.end_date = sDate
    } else if (sDate && eDate) {
      const d1 = new Date(sDate)
      const d2 = new Date(eDate)
      if (d2 >= d1) {
        const diffTime = Math.abs(d2.getTime() - d1.getTime())
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1
        updated.days_count = diffDays
      } else {
        updated.days_count = 0
      }
    }
  }

  emit('update:modelValue', updated)
}

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.leave_type) {
    initial.leave_type = 'ANNUAL'
    changed = true
  }
  if (!initial.start_date) {
    const today = new Date().toISOString().substring(0, 10)
    initial.start_date = today
    initial.end_date = today
    initial.days_count = 1
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="leave-application-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilCalendar" class="me-1" />
      휴가 / 연차 신청 정보
    </h6>

    <!-- 휴가 구분 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label required">휴가 구분</CFormLabel>
      <CCol sm="9">
        <CFormSelect
          :value="modelValue.leave_type ?? 'ANNUAL'"
          required
          @change="updateField('leave_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in leaveTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 기간 선택 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label required">휴가 기간</CFormLabel>
      <CCol sm="9">
        <div class="d-flex align-items-center gap-2">
          <CFormInput
            type="date"
            :value="modelValue.start_date ?? ''"
            required
            @input="updateField('start_date', ($event.target as HTMLInputElement).value)"
          />
          <span v-if="modelValue.leave_type !== 'HALF_AM' && modelValue.leave_type !== 'HALF_PM'"
            >~</span
          >
          <CFormInput
            v-if="modelValue.leave_type !== 'HALF_AM' && modelValue.leave_type !== 'HALF_PM'"
            type="date"
            :value="modelValue.end_date ?? ''"
            required
            @input="updateField('end_date', ($event.target as HTMLInputElement).value)"
          />
          <CBadge color="primary" class="p-2 text-nowrap">
            신청일수: {{ modelValue.days_count ?? 1 }}일
          </CBadge>
        </div>
      </CCol>
    </CRow>

    <!-- 사유 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label required">휴가 사유</CFormLabel>
      <CCol sm="9">
        <CFormTextarea
          :value="modelValue.reason ?? ''"
          rows="3"
          placeholder="구체적인 사유를 입력하세요. (예: 개인 사정, 가족 행사 등)"
          required
          @input="updateField('reason', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 업무 대행자 / 비상연락처 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label">업무 대행자</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.substitute_worker ?? ''"
          placeholder="인수인계자 성명"
          @input="updateField('substitute_worker', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">비상연락처</CFormLabel>
      <CCol sm="3">
        <CFormInput
          :value="modelValue.emergency_contact ?? ''"
          placeholder="010-XXXX-XXXX"
          @input="updateField('emergency_contact', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
