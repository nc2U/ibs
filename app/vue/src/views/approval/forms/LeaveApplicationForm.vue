<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import type { ApprovalContent } from '@/store/types/approval'
import { LEAVE_TYPE_OPTIONS, asStr, calcInclusiveDays, getLocalToday } from '../utils/approvalMeta'

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

  // 일수 자동 계산 로직
  if (key === 'leave_type' || key === 'start_date' || key === 'end_date') {
    const lType = asStr(updated.leave_type, 'ANNUAL')
    const sDate = asStr(updated.start_date)
    const eDate = asStr(updated.end_date)

    if (lType === 'HALF_AM' || lType === 'HALF_PM') {
      updated.days_count = 0.5
      if (sDate) updated.end_date = sDate
    } else if (sDate && eDate) {
      updated.days_count = calcInclusiveDays(sDate, eDate)
    } else {
      updated.days_count = 0
    }
  }

  emit('update:modelValue', updated)
}

const startDate = computed({
  get: () => asStr(props.modelValue.start_date),
  set: (val: string) => updateField('start_date', val),
})

const endDate = computed({
  get: () => asStr(props.modelValue.end_date),
  set: (val: string) => updateField('end_date', val),
})

onMounted(() => {
  const initial: ApprovalContent = { ...props.modelValue }
  let changed = false

  if (!asStr(initial.leave_type)) {
    initial.leave_type = 'ANNUAL'
    changed = true
  }
  if (!asStr(initial.start_date)) {
    const today = getLocalToday()
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
      휴가 신청 기본 정보
    </h6>

    <!-- 휴가 구분 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label required">휴가 구분</CFormLabel>
      <CCol sm="9">
        <CFormSelect
          :value="asStr(modelValue.leave_type, 'ANNUAL')"
          required
          @change="updateField('leave_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in LEAVE_TYPE_OPTIONS" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 기간 선택 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label required">휴가 기간</CFormLabel>
      <CCol sm="9">
        <div class="d-flex align-items-center gap-2 flex-wrap">
          <DatePicker v-model="startDate" required placeholder="휴가 시작일" />
          <span v-if="modelValue.leave_type !== 'HALF_AM' && modelValue.leave_type !== 'HALF_PM'"
            >~</span
          >
          <DatePicker
            v-if="modelValue.leave_type !== 'HALF_AM' && modelValue.leave_type !== 'HALF_PM'"
            v-model="endDate"
            required
            placeholder="휴가 종료일"
          />
          <v-chip color="primary" variant="flat" size="x-small" class="p-2 text-nowrap">
            신청일수: {{ modelValue.days_count ?? 1 }}일
          </v-chip>
        </div>
      </CCol>
    </CRow>

    <!-- 사유 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label required">휴가 사유</CFormLabel>
      <CCol sm="9">
        <CFormTextarea
          :value="asStr(modelValue.reason)"
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
          :value="asStr(modelValue.substitute_worker)"
          placeholder="인수인계자 성명"
          @input="updateField('substitute_worker', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">비상연락처</CFormLabel>
      <CCol sm="3">
        <CFormInput
          :value="asStr(modelValue.emergency_contact)"
          placeholder="010-XXXX-XXXX"
          @input="updateField('emergency_contact', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
