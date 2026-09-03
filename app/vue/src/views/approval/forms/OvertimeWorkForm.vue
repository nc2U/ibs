<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const workTypes = [
  { value: 'OVERTIME', label: '평일 연장근무' },
  { value: 'NIGHT', label: '야간근무 (22시 이후)' },
  { value: 'HOLIDAY', label: '휴일 (주말/공휴일) 근무' },
]

const compensationTypes = [
  { value: 'ALLOWANCE', label: '연장/휴일 수당 지급' },
  { value: 'COMP_LEAVE', label: '대체휴무 (보상휴가) 적립' },
]

const calculateHours = (sTime: string, eTime: string, bHours: number): number => {
  if (!sTime || !eTime) return 0
  const [sH, sM] = sTime.split(':').map(Number)
  const [eH, eM] = eTime.split(':').map(Number)

  let startMin = sH * 60 + sM
  let endMin = eH * 60 + eM

  // 익일 넘어가는 경우
  if (endMin < startMin) {
    endMin += 24 * 60
  }

  const diffMin = endMin - startMin
  const rawHours = diffMin / 60
  const netHours = Math.max(0, rawHours - (Number(bHours) || 0))
  return Math.round(netHours * 10) / 10
}

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // 시간 자동 계산
  if (['start_time', 'end_time', 'break_hours', 'work_type'].includes(key)) {
    const sTime = updated.start_time
    const eTime = updated.end_time
    const bHours = Number(updated.break_hours) || 0
    if (sTime && eTime) {
      updated.total_hours = calculateHours(sTime, eTime, bHours)
    }
  }

  emit('update:modelValue', updated)
}

const workDate = computed({
  get: () => props.modelValue.work_date ?? '',
  set: (val: string) => updateField('work_date', val),
})

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.work_type) {
    initial.work_type = 'OVERTIME'
    changed = true
  }
  if (!initial.compensation_type) {
    initial.compensation_type = 'ALLOWANCE'
    changed = true
  }
  if (!initial.work_date) {
    initial.work_date = new Date().toISOString().substring(0, 10)
    changed = true
  }
  if (!initial.start_time) {
    initial.start_time = '18:30'
    changed = true
  }
  if (!initial.end_time) {
    initial.end_time = '21:30'
    changed = true
  }
  if (initial.break_hours === undefined || initial.break_hours === null) {
    initial.break_hours = 0
    changed = true
  }
  if (!initial.total_hours) {
    initial.total_hours = calculateHours(initial.start_time, initial.end_time, initial.break_hours)
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="overtime-work-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilClock" class="me-1" />
      연장 / 휴일근무 신청 정보
    </h6>

    <!-- 근무 구분 & 근무 일자 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">근무 구분</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.work_type ?? 'OVERTIME'"
          required
          @change="updateField('work_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in workTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">근무 일자</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="workDate" required placeholder="근무 일자 선택" />
      </CCol>
    </CRow>

    <!-- 근무 시간대 & 휴게시간 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">근무 시간</CFormLabel>
      <CCol sm="6">
        <div class="d-flex align-items-center gap-2">
          <CFormInput
            type="time"
            class="w-auto"
            :value="modelValue.start_time ?? '18:30'"
            required
            @input="updateField('start_time', ($event.target as HTMLInputElement).value)"
          />
          <span>~</span>
          <CFormInput
            type="time"
            class="w-auto"
            :value="modelValue.end_time ?? '21:30'"
            required
            @input="updateField('end_time', ($event.target as HTMLInputElement).value)"
          />
        </div>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">휴게/식사시간</CFormLabel>
      <CCol sm="2">
        <CInputGroup size="sm">
          <CFormInput
            type="number"
            min="0"
            step="0.5"
            :value="modelValue.break_hours ?? 0"
            @input="
              updateField('break_hours', Number(($event.target as HTMLInputElement).value) || 0)
            "
          />
          <CInputGroupText>시간</CInputGroupText>
        </CInputGroup>
      </CCol>
    </CRow>

    <!-- 실 근무시간 산출 & 보상 방식 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">총 인정 시간</CFormLabel>
      <CCol sm="4" class="d-flex align-items-center">
        <CBadge color="primary" class="fs-6 px-3 py-2">
          총 {{ modelValue.total_hours ?? 3 }} 시간 인정
        </CBadge>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">보상 방식</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.compensation_type ?? 'ALLOWANCE'"
          @change="updateField('compensation_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="c in compensationTypes" :key="c.value" :value="c.value">
            {{ c.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 구체적 근무 사유 및 업무 내용 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">근무 사유 / 업무</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.reason ?? ''"
          rows="4"
          placeholder="연장/휴일근무를 실시하는 구체적인 사유 및 수행할 세부 업무 내역을 상세히 작성해 주세요. (예: 분기 결산 세무 조정 및 외부 감사 대응 자료 작성)"
          required
          @input="updateField('reason', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 공동 근무자 & 비고 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">동반 근무자</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.co_workers ?? ''"
          placeholder="예: 홍길동 대리, 이순신 사원"
          @input="updateField('co_workers', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">비고 / 특이사항</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.note ?? ''"
          placeholder="추가 전달 사항"
          @input="updateField('note', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
