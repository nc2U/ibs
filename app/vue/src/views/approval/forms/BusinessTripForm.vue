<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import type { ApprovalContent } from '@/store/types/approval'
import {
  TRANSPORT_METHOD_OPTIONS,
  TRIP_TYPE_OPTIONS,
  asNum,
  asStr,
  calcInclusiveDays,
  getLocalToday,
  parseNonNegativeNumberInput,
} from '../utils/approvalMeta'

const props = defineProps<{
  modelValue: ApprovalContent
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: ApprovalContent): void
}>()

const calculateTotal = (val: ApprovalContent) => {
  const tCost = asNum(val.transport_cost)
  const lCost = asNum(val.lodging_cost)
  const dCost = asNum(val.daily_allowance)
  const oCost = asNum(val.other_cost)
  return tCost + lCost + dCost + oCost
}

const updateField = (key: string, val: unknown) => {
  const updated: ApprovalContent = {
    ...props.modelValue,
    [key]: val,
  }

  // 출장 일수 계산
  if (key === 'start_date' || key === 'end_date') {
    const sDate = asStr(updated.start_date)
    const eDate = asStr(updated.end_date)
    if (sDate && eDate) {
      const diffDays = calcInclusiveDays(sDate, eDate)
      updated.days_count = diffDays
      updated.nights_count = Math.max(0, diffDays - 1)
    } else {
      updated.days_count = 0
      updated.nights_count = 0
    }
  }

  // 출장 경비 합계 및 amount 동기화 (전결 규정 자동 계산용)
  if (['transport_cost', 'lodging_cost', 'daily_allowance', 'other_cost'].includes(key)) {
    const total = calculateTotal(updated)
    updated.total_cost = total
    updated.amount = total
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

const formattedTotal = computed(() => {
  const t = props.modelValue.total_cost ?? props.modelValue.amount ?? 0
  return asNum(t).toLocaleString()
})

onMounted(() => {
  const initial: ApprovalContent = { ...props.modelValue }
  let changed = false

  if (!asStr(initial.trip_type)) {
    initial.trip_type = 'DOMESTIC'
    changed = true
  }
  if (!asStr(initial.transportation)) {
    initial.transportation = 'CORP_CAR'
    changed = true
  }
  if (!asStr(initial.start_date)) {
    const today = getLocalToday()
    initial.start_date = today
    initial.end_date = today
    initial.days_count = 1
    initial.nights_count = 0
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="business-trip-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilFlightTakeoff" class="me-1" />
      출장 신청 기본 정보
    </h6>

    <!-- 출장 구분 & 출장지 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">출장 구분</CFormLabel>
      <CCol sm="3">
        <CFormSelect
          :value="asStr(modelValue.trip_type, 'DOMESTIC')"
          required
          @change="updateField('trip_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in TRIP_TYPE_OPTIONS" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">출장지 / 행선지</CFormLabel>
      <CCol sm="5">
        <CFormInput
          :value="asStr(modelValue.destination)"
          placeholder="예: 부산 해운대 현장 및 부산시청"
          required
          @input="updateField('destination', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 출장 기간 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">출장 기간</CFormLabel>
      <CCol sm="10">
        <div class="d-flex align-items-center gap-2 flex-wrap">
          <DatePicker v-model="startDate" required placeholder="출장 시작일" />
          <span>~</span>
          <DatePicker v-model="endDate" required placeholder="출장 종료일" />
          <v-chip color="primary" variant="flat" size="x-small" class="p-2 text-nowrap">
            {{ modelValue.nights_count ?? 0 }}박 {{ modelValue.days_count ?? 1 }}일
          </v-chip>
        </div>
      </CCol>
    </CRow>

    <!-- 출장 목적 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">출장 목적</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="asStr(modelValue.purpose)"
          placeholder="예: 토공사 착공 전 현장 감리단 합동 실사 및 관공서 인허가 협의"
          required
          @input="updateField('purpose', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 동행자 & 업무 대행자 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">동행자 명단</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.companion)"
          placeholder="예: 김철수 부장, 이영희 대리 (외 1명)"
          @input="updateField('companion', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">업무 대행자</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.substitute_worker)"
          placeholder="인수인계자 성명"
          @input="updateField('substitute_worker', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 주요 교통편 & 비상연락처 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">주요 교통편</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="asStr(modelValue.transportation, 'CORP_CAR')"
          @change="updateField('transportation', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="m in TRANSPORT_METHOD_OPTIONS" :key="m.value" :value="m.value">
            {{ m.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">비상 연락처</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.emergency_contact)"
          placeholder="010-XXXX-XXXX"
          @input="updateField('emergency_contact', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <hr class="my-3 text-muted" />

    <h6 class="fw-bold mb-3 text-secondary">
      <CIcon name="cilMoney" class="me-1" />
      예상 출장 여비 (원)
    </h6>

    <!-- 여비 세부 항목 -->
    <CRow class="mb-3">
      <CCol sm="3">
        <CFormLabel class="small text-muted mb-1">교통비 (KTX/유류대 등)</CFormLabel>
        <CInputGroup size="sm">
          <CFormInput
            type="number"
            min="0"
            :value="modelValue.transport_cost ?? 0"
            placeholder="0"
            @input="
              updateField(
                'transport_cost',
                parseNonNegativeNumberInput(($event.target as HTMLInputElement).value),
              )
            "
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
      <CCol sm="3">
        <CFormLabel class="small text-muted mb-1">숙박비</CFormLabel>
        <CInputGroup size="sm">
          <CFormInput
            type="number"
            min="0"
            :value="modelValue.lodging_cost ?? 0"
            placeholder="0"
            @input="
              updateField(
                'lodging_cost',
                parseNonNegativeNumberInput(($event.target as HTMLInputElement).value),
              )
            "
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
      <CCol sm="3">
        <CFormLabel class="small text-muted mb-1">일비 / 식비</CFormLabel>
        <CInputGroup size="sm">
          <CFormInput
            type="number"
            min="0"
            :value="modelValue.daily_allowance ?? 0"
            placeholder="0"
            @input="
              updateField(
                'daily_allowance',
                parseNonNegativeNumberInput(($event.target as HTMLInputElement).value),
              )
            "
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
      <CCol sm="3">
        <CFormLabel class="small text-muted mb-1">기타 경비</CFormLabel>
        <CInputGroup size="sm">
          <CFormInput
            type="number"
            min="0"
            :value="modelValue.other_cost ?? 0"
            placeholder="0"
            @input="
              updateField(
                'other_cost',
                parseNonNegativeNumberInput(($event.target as HTMLInputElement).value),
              )
            "
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
    </CRow>

    <!-- 총 여비 표시 -->
    <div
      class="d-flex justify-content-between align-items-center p-2 bg-more-white border rounded mb-3"
    >
      <span class="small text-muted">* 예상 여비 총액에 따라 전결 결재선이 자동 적용됩니다.</span>
      <div>
        <span class="me-2 fw-semibold">총 예상 여비:</span>
        <span class="fs-5 fw-bold text-danger">{{ formattedTotal }} 원</span>
      </div>
    </div>

    <!-- 세부 일정 및 계획 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">세부 일정 계획</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="asStr(modelValue.itinerary)"
          rows="4"
          placeholder="일자별 방문 기관 및 주요 업무 추진 일정을 기재해 주세요."
          @input="updateField('itinerary', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
