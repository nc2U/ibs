<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import type { ApprovalContent } from '@/store/types/approval'
import {
  COMPENSATION_TYPE_OPTIONS,
  WORK_TYPE_OPTIONS,
  asNum,
  asStr,
  getLocalToday,
  parseNonNegativeNumberInput,
} from '../utils/approvalMeta'

const props = defineProps<{
  modelValue: ApprovalContent
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: ApprovalContent): void
}>()

const calculateHours = (sTime: string, eTime: string, bHours: number): number => {
  if (!sTime || !eTime) return 0
  const startParts = sTime.split(':')
  const endParts = eTime.split(':')
  if (startParts.length < 2 || endParts.length < 2) return 0

  const sH = Number(startParts[0])
  const sM = Number(startParts[1])
  const eH = Number(endParts[0])
  const eM = Number(endParts[1])
  if (
    !Number.isFinite(sH) ||
    !Number.isFinite(sM) ||
    !Number.isFinite(eH) ||
    !Number.isFinite(eM)
  ) {
    return 0
  }

  const startMin = sH * 60 + sM
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

const updateField = (key: string, val: unknown) => {
  const updated: ApprovalContent = {
    ...props.modelValue,
    [key]: val,
  }

  // 시간 자동 계산
  if (['start_time', 'end_time', 'break_hours', 'work_type'].includes(key)) {
    const sTime = asStr(updated.start_time)
    const eTime = asStr(updated.end_time)
    const bHours = asNum(updated.break_hours)
    updated.total_hours = sTime && eTime ? calculateHours(sTime, eTime, bHours) : 0
  }

  emit('update:modelValue', updated)
}

const workDate = computed({
  get: () => asStr(props.modelValue.work_date),
  set: (val: string) => updateField('work_date', val),
})

onMounted(() => {
  const initial: ApprovalContent = { ...props.modelValue }
  let changed = false

  if (!asStr(initial.work_type)) {
    initial.work_type = 'OVERTIME'
    changed = true
  }
  if (!asStr(initial.compensation_type)) {
    initial.compensation_type = 'ALLOWANCE'
    changed = true
  }
  if (!asStr(initial.work_date)) {
    initial.work_date = getLocalToday()
    changed = true
  }
  if (!asStr(initial.start_time)) {
    initial.start_time = '18:30'
    changed = true
  }
  if (!asStr(initial.end_time)) {
    initial.end_time = '21:30'
    changed = true
  }
  if (initial.break_hours === undefined || initial.break_hours === null) {
    initial.break_hours = 0
    changed = true
  }
  if (!initial.total_hours) {
    initial.total_hours = calculateHours(
      asStr(initial.start_time),
      asStr(initial.end_time),
      asNum(initial.break_hours),
    )
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
          :value="asStr(modelValue.work_type, 'OVERTIME')"
          required
          @change="updateField('work_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in WORK_TYPE_OPTIONS" :key="t.value" :value="t.value">
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
            :value="asStr(modelValue.start_time, '18:30')"
            required
            @input="updateField('start_time', ($event.target as HTMLInputElement).value)"
          />
          <span>~</span>
          <CFormInput
            type="time"
            class="w-auto"
            :value="asStr(modelValue.end_time, '21:30')"
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
            step="any"
            :value="modelValue.break_hours ?? 0"
            @input="
              updateField(
                'break_hours',
                parseNonNegativeNumberInput(($event.target as HTMLInputElement).value),
              )
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
        <v-chip color="info" variant="flat" size="x-small" class="fs-6 px-3 py-2">
          총 {{ modelValue.total_hours ?? 3 }} 시간 인정
        </v-chip>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">보상 방식</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="asStr(modelValue.compensation_type, 'ALLOWANCE')"
          @change="updateField('compensation_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="c in COMPENSATION_TYPE_OPTIONS" :key="c.value" :value="c.value">
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
          :value="asStr(modelValue.reason)"
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
          :value="asStr(modelValue.co_workers)"
          placeholder="예: 홍길동 대리, 이순신 사원"
          @input="updateField('co_workers', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">비고 / 특이사항</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.note)"
          placeholder="추가 전달 사항"
          @input="updateField('note', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
