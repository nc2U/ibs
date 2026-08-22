<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const decisionTypes = [
  { value: 'DESIGN_SPEC', label: '설계 변경 / 마감재 / 상품 스펙 결정' },
  { value: 'SALES_PRICING', label: '분양가 책정 / 분양 시기 및 조건 결정' },
  { value: 'CONSTRUCTION_METHOD', label: '시공 공법 / 가설 / 주요 자재 선정' },
  { value: 'FINANCIAL_STRUCTURING', label: '금융 구조 / PF 대주단 조건 / 자금 조달 변경' },
  { value: 'CLAIM_DISPUTE', label: '중대 민원 / 행정처분 / 소송·분쟁 대응 방향' },
  { value: 'CONTRACTOR_TERMINATION', label: '주요 협력업체 선정 및 타절·대체 결정' },
  { value: 'OTHER', label: '기타 프로젝트 주요 의사결정' },
]

const urgencyLevels = [
  { value: 'NORMAL', label: '보통 (정기 검토)' },
  { value: 'URGENT', label: '긴급 (금주 내 결정)' },
  { value: 'CRITICAL', label: '즉시 결정 (공정/인허가 지연 임박)' },
]

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // financial_impact 변경 시 amount 동기화 (전결 결재선 연동)
  if (key === 'financial_impact') {
    updated.amount = Number(val) || 0
  }

  emit('update:modelValue', updated)
}

const decisionDueDate = computed({
  get: () => props.modelValue.decision_due_date ?? '',
  set: (val: string) => updateField('decision_due_date', val),
})

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.decision_type) {
    initial.decision_type = 'DESIGN_SPEC'
    changed = true
  }
  if (!initial.urgency) {
    initial.urgency = 'NORMAL'
    changed = true
  }
  if (!initial.decision_due_date) {
    const d = new Date()
    d.setDate(d.getDate() + 7)
    initial.decision_due_date = d.toISOString().substring(0, 10)
    changed = true
  }
  if (initial.financial_impact === undefined && initial.amount) {
    initial.financial_impact = initial.amount
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="project-decision-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-danger">
      <CIcon name="cilLightbulb" class="me-1 text-danger" />
      프로젝트 주요 현안 및 의사결정 심의
    </h6>

    <!-- 분야 & 긴급도 & 프로젝트명 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">현안 분야</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.decision_type ?? 'DESIGN_SPEC'"
          required
          @change="updateField('decision_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in decisionTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">긴급도</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.urgency ?? 'NORMAL'"
          required
          @change="updateField('urgency', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="u in urgencyLevels" :key="u.value" :value="u.value">
            {{ u.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 안건명 & 결정 목표일 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">심의 안건명</CFormLabel>
      <CCol sm="6">
        <CFormInput
          :value="modelValue.decision_subject ?? modelValue.case_title ?? ''"
          placeholder="예: 00현장 흙막이 가시설 공법 변경에 따른 공기 및 원가 영향 심의의 건"
          required
          @input="updateField('decision_subject', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">의사결정 목표일</CFormLabel>
      <CCol sm="4">
        <DatePicker
          v-model="decisionDueDate"
          placeholder="의사결정 목표일 선택"
        />
      </CCol>
    </CRow>

    <!-- 재무적 영향 / 증감액 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">재무적 영향(비용)</CFormLabel>
      <CCol sm="4">
        <CInputGroup>
          <CFormInput
            type="number"
            step="10000"
            class="text-end fw-semibold"
            :value="modelValue.financial_impact ?? modelValue.amount ?? 0"
            placeholder="0"
            @input="
              updateField(
                'financial_impact',
                Number(($event.target as HTMLInputElement).value) || 0,
              )
            "
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
      <CCol sm="6" class="form-text text-muted d-flex align-items-center">
        * 비용 증감이나 손실/투자 금액이 있는 경우 입력 시 전결 결재선에 실시간 반영됩니다.
      </CCol>
    </CRow>

    <!-- 현안 배경 및 문제점 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">현안 배경 및 문제점</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.background_issue ?? modelValue.purpose ?? ''"
          rows="3"
          placeholder="현안 발생 경위, 기존 방식 유지 시의 문제점 및 의사결정이 필요한 핵심 사유를 상세히 기술해 주세요."
          required
          @input="updateField('background_issue', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 대안 비교 분석 (Option 1 vs Option 2 vs Option 3) -->
    <div class="card mb-3 border border-secondary">
      <div class="card-header bg-secondary bg-opacity-10 py-2 fw-semibold small text-body">
        <CIcon name="cilColumns" class="me-1" />
        검토 대안별 비교 분석 (Alternatives Comparison)
      </div>
      <div class="card-body p-2">
        <!-- 대안 1 (원안) -->
        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small fw-semibold text-secondary">
            대안 1 (원안)
          </CFormLabel>
          <CCol sm="10">
            <CFormTextarea
              rows="2"
              size="sm"
              :value="modelValue.option_1 ?? ''"
              placeholder="대안 1 내용, 장점/단점, 예상 비용, 공기 영향 (예: 원안 유지 - 추가비용 없음, 단 민원 발생 및 공기 1개월 지연 위험)"
              @input="updateField('option_1', ($event.target as HTMLTextAreaElement).value)"
            />
          </CCol>
        </CRow>

        <!-- 대안 2 (추천안 / 변경안) -->
        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small fw-bold text-primary">
            대안 2 (변경/추천안)
          </CFormLabel>
          <CCol sm="10">
            <CFormTextarea
              rows="2"
              size="sm"
              :value="modelValue.option_2 ?? ''"
              placeholder="대안 2 내용, 장점/단점, 예상 비용, 공기 영향 (예: 공법 변경 - 5천만원 추가 소요되나 민원 해소 및 공기 20일 단축 가능)"
              @input="updateField('option_2', ($event.target as HTMLTextAreaElement).value)"
            />
          </CCol>
        </CRow>

        <!-- 대안 3 (선택 대안) -->
        <CRow>
          <CFormLabel class="col-sm-2 col-form-label small text-muted">
            대안 3 (기타 대안)
          </CFormLabel>
          <CCol sm="10">
            <CFormTextarea
              rows="2"
              size="sm"
              :value="modelValue.option_3 ?? ''"
              placeholder="(선택사항) 대안 3 내용 및 비교 분석"
              @input="updateField('option_3', ($event.target as HTMLTextAreaElement).value)"
            />
          </CCol>
        </CRow>
      </div>
    </div>

    <!-- 주관부서 최종 추천안 및 선정 사유 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required text-primary fw-bold"
        >주관부서 추천안</CFormLabel
      >
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.recommendation ?? ''"
          rows="3"
          placeholder="주관부서가 최종 추천하는 대안(예: 대안 2안 채택)과 그 구체적인 선정 사유 및 기대 효과를 기술해 주세요."
          required
          @input="updateField('recommendation', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 향후 조치 계획 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">향후 조치 계획</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.action_plan ?? ''"
          placeholder="결정 후 후속 조치 일정 (예: 변경계약 체결, 설계도서 수정 납품, 감리단 보고 등)"
          @input="updateField('action_plan', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 첨부 서류 및 비고 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">첨부 서류 / 비고</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.enclosed_docs ?? modelValue.note ?? ''"
          placeholder="예: 공법 비교 검토서 1부, 원가 계산서 1부, 전문가 기술자문 의견서 1부"
          @input="updateField('enclosed_docs', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
