<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const bizTypes = [
  { value: 'DEV_SELF', label: '자체 개발사업 (토지 매입 시행)' },
  { value: 'DEV_TRUST', label: '토지신탁 / 관리형 토지신탁' },
  { value: 'CONTRACT_CIVIL', label: '단순 도급 공사 (시공/수주)' },
  { value: 'REDEVELOPMENT', label: '재개발 / 재건축 정비사업' },
  { value: 'PF_INVEST', label: '지분 투자 / 공동 개발' },
  { value: 'OTHER', label: '기타 신규 사업' },
]

const landSecureDate = computed({
  get: () => props.modelValue.land_secure_date ?? '',
  set: (val: string) => updateField('land_secure_date', val),
})

const approvalTargetDate = computed({
  get: () => props.modelValue.approval_target_date ?? '',
  set: (val: string) => updateField('approval_target_date', val),
})

const startDate = computed({
  get: () => props.modelValue.start_date ?? '',
  set: (val: string) => updateField('start_date', val),
})

const completionDate = computed({
  get: () => props.modelValue.completion_date ?? '',
  set: (val: string) => updateField('completion_date', val),
})

const totalRevenue = computed(() => Number(props.modelValue.total_revenue) || 0)
const totalCost = computed(() => Number(props.modelValue.total_cost) || 0)

const netProfit = computed(() => totalRevenue.value - totalCost.value)
const profitRate = computed(() => {
  if (totalCost.value <= 0) return 0
  return Number(((netProfit.value / totalCost.value) * 100).toFixed(2))
})

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // 총매출 또는 총사업비 변경 시 이익 및 수익률, 결재선용 amount 자동 반영
  if (key === 'total_revenue' || key === 'total_cost') {
    const rev = key === 'total_revenue' ? Number(val) || 0 : totalRevenue.value
    const cst = key === 'total_cost' ? Number(val) || 0 : totalCost.value
    const np = rev - cst
    const pr = cst > 0 ? Number(((np / cst) * 100).toFixed(2)) : 0

    updated.net_profit = np
    updated.profit_rate = pr
    updated.amount = cst // 총사업비 기준으로 결재선 연동
  }

  emit('update:modelValue', updated)
}

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.biz_type) {
    initial.biz_type = 'DEV_SELF'
    changed = true
  }
  if (initial.total_revenue === undefined) {
    initial.total_revenue = 0
    changed = true
  }
  if (initial.total_cost === undefined) {
    initial.total_cost = 0
    changed = true
  }
  if (initial.net_profit === undefined) {
    initial.net_profit = 0
    changed = true
  }
  if (initial.profit_rate === undefined) {
    initial.profit_rate = 0
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="business-review-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-info">
      <CIcon name="cilBuilding" class="me-1 text-primary" />
      사업 타당성 및 수지 검토
    </h6>

    <!-- 사업 개요: 사업명 & 사업 유형 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">사업명 (프로젝트)</CFormLabel>
      <CCol sm="6">
        <CFormInput
          :value="modelValue.project_name ?? modelValue.case_title ?? ''"
          placeholder="예: 00시 00동 주상복합 신축사업 타당성 검토"
          required
          @input="updateField('project_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">사업 유형</CFormLabel>
      <CCol sm="2">
        <CFormSelect
          :value="modelValue.biz_type ?? 'DEV_SELF'"
          required
          @change="updateField('biz_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in bizTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 위치 및 규모 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">사업 부지 위치</CFormLabel>
      <CCol sm="6">
        <CFormInput
          :value="modelValue.location ?? ''"
          placeholder="지번 / 도로명 주소 (예: 경기도 성남시 분당구 00동 123번지 일원)"
          required
          @input="updateField('location', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">건축 규모 / 세대</CFormLabel>
      <CCol sm="2">
        <CFormInput
          :value="modelValue.building_scale ?? ''"
          placeholder="예: 지하 4층~지상 29층, 450세대"
          @input="updateField('building_scale', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 대지면적 & 연면적 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">대지 / 연면적</CFormLabel>
      <CCol sm="5">
        <CInputGroup size="sm">
          <CInputGroupText>대지면적</CInputGroupText>
          <CFormInput
            :value="modelValue.land_area ?? ''"
            placeholder="예: 3,500.00"
            @input="updateField('land_area', ($event.target as HTMLInputElement).value)"
          />
          <CInputGroupText>㎡</CInputGroupText>
        </CInputGroup>
      </CCol>
      <CCol sm="5">
        <CInputGroup size="sm">
          <CInputGroupText>연면적</CInputGroupText>
          <CFormInput
            :value="modelValue.gross_floor_area ?? ''"
            placeholder="예: 42,000.00"
            @input="updateField('gross_floor_area', ($event.target as HTMLInputElement).value)"
          />
          <CInputGroupText>㎡</CInputGroupText>
        </CInputGroup>
      </CCol>
    </CRow>

    <!-- 사업 수지 및 재무 분석 카드 -->
    <div class="card mb-3 border border-primary">
      <div class="card-header bg-primary bg-opacity-10 py-2 fw-semibold small text-primary">
        <CIcon name="cilChartPie" class="me-1 text-primary" />
        사업 수지 및 재무 분석 요약 (단위: 원)
      </div>
      <div class="card-body p-2">
        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small required">총 분양/매출 수입</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000000"
                class="text-end fw-bold text-primary"
                :value="modelValue.total_revenue ?? 0"
                required
                @input="
                  updateField(
                    'total_revenue',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small required text-sm-end"
            >총 사업비(지출)</CFormLabel
          >
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000000"
                class="text-end fw-bold text-danger"
                :value="modelValue.total_cost ?? 0"
                required
                @input="
                  updateField('total_cost', Number(($event.target as HTMLInputElement).value) || 0)
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>

        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small">예상 세전 이익</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                readonly
                class="text-end fw-bold bg-light"
                :class="netProfit >= 0 ? 'text-success' : 'text-danger'"
                :value="netProfit"
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end">수익률 (ROI)</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                readonly
                class="text-end fw-bold bg-light text-body"
                :value="profitRate"
              />
              <CInputGroupText>%</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>

        <CRow>
          <CFormLabel class="col-sm-2 col-form-label small">자기자본 (Equity)</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000000"
                class="text-end"
                :value="modelValue.required_equity ?? 0"
                @input="
                  updateField(
                    'required_equity',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end">PF 조달 규모</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000000"
                class="text-end"
                :value="modelValue.pf_loan_amount ?? 0"
                @input="
                  updateField(
                    'pf_loan_amount',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </div>
    </div>

    <!-- 사업 추진 일정 계획 -->
    <div class="card mb-3 border">
      <div class="card-header bg-more-white py-2 fw-semibold small text-secondary">
        <CIcon name="cilCalendar" class="me-1" />
        주요 사업 일정 계획
      </div>
      <div class="card-body p-2">
        <CRow>
          <CCol sm="3">
            <CFormLabel class="small mb-1">토지 확보/계약</CFormLabel>
            <DatePicker v-model="landSecureDate" placeholder="토지계약일 선택" />
          </CCol>
          <CCol sm="3">
            <CFormLabel class="small mb-1">인허가/사업승인</CFormLabel>
            <DatePicker v-model="approvalTargetDate" placeholder="사업승인일 선택" />
          </CCol>
          <CCol sm="3">
            <CFormLabel class="small mb-1">착공 및 분양</CFormLabel>
            <DatePicker v-model="startDate" placeholder="착공/분양일 선택" />
          </CCol>
          <CCol sm="3">
            <CFormLabel class="small mb-1">준공 및 입주</CFormLabel>
            <DatePicker v-model="completionDate" placeholder="준공/입주일 선택" />
          </CCol>
        </CRow>
      </div>
    </div>

    <!-- 입지 및 시장성 분석 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">입지 및 분양성</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.market_analysis ?? ''"
          rows="3"
          placeholder="교통, 학군, 상권 등 입지 특성 및 인근 경쟁 단지 분양가/시세 분석 요약"
          @input="updateField('market_analysis', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 주요 리스크 요인 및 대책 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">주요 리스크 및 대책</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.risk_factors ?? ''"
          rows="3"
          placeholder="인허가 난이도, PF 대출 금리 리스크, 시공비 상승 리스크 및 리스크 헷지 방안"
          @input="updateField('risk_factors', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 종합 검토의견 및 추진 전략 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">종합 검토의견</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.recommendation ?? modelValue.purpose ?? ''"
          rows="4"
          placeholder="사업 추진 타당성 평가, 단계별 추진 전략, 수주/시행 의사결정 요청 의견을 상세히 기술해 주세요."
          required
          @input="updateField('recommendation', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 첨부 서류 및 비고 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">첨부 서류 / 비고</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.enclosed_docs ?? modelValue.note ?? ''"
          placeholder="예: 사업수지분석표(Excel) 1부, 건축기획설계도서 1부, 토지조서 1부"
          @input="updateField('enclosed_docs', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
