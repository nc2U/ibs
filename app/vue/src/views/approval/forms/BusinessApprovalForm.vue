<script setup lang="ts">
import { computed, onMounted } from 'vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const approvalTypes = [
  { value: 'NEW_LAUNCH', label: '신규 사업 공식 론칭 / 부지 매입 착수 승인' },
  { value: 'LAND_ACQUISITION', label: '토지 매매계약 체결 및 계약금 집행 승인' },
  { value: 'SPC_ESTABLISH', label: '시행 법인(SPC / PFV) 설립 및 출자 승인' },
  { value: 'PF_EXECUTION', label: '본 PF 금융약정 체결 및 사업비 인출 승인' },
  { value: 'CONSTRUCTION_START', label: '시공사 도급계약 및 본 착공 승인' },
  { value: 'OTHER', label: '기타 주요 사업 마일스톤 승인' },
]

const requestedAmount = computed(
  () => Number(props.modelValue.requested_amount) || Number(props.modelValue.approval_budget) || 0,
)
const totalCost = computed(() => Number(props.modelValue.total_project_cost) || 0)
const totalRevenue = computed(() => Number(props.modelValue.total_expected_revenue) || 0)
const expectedProfit = computed(() => totalRevenue.value - totalCost.value)

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // 금회 승인 요청 금액 변경 시 amount 동기화 (전결 결재선 연동)
  if (key === 'requested_amount' || key === 'approval_budget') {
    const amt = Number(val) || 0
    updated.requested_amount = amt
    updated.approval_budget = amt
    updated.amount = amt
  } else if (key === 'total_expected_revenue' || key === 'total_project_cost') {
    const rev = key === 'total_expected_revenue' ? Number(val) || 0 : totalRevenue.value
    const cst = key === 'total_project_cost' ? Number(val) || 0 : totalCost.value
    updated.expected_profit = rev - cst
  }

  emit('update:modelValue', updated)
}

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.approval_type) {
    initial.approval_type = 'NEW_LAUNCH'
    changed = true
  }
  if (initial.requested_amount === undefined && initial.amount) {
    initial.requested_amount = initial.amount
    initial.approval_budget = initial.amount
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="business-approval-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-success">
      <CIcon name="cilCheckCircle" class="me-1 text-success" />
      사업추진 및 투자 집행 승인
    </h6>

    <!-- 사업명 & 승인 의결 구분 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">사업명 (프로젝트)</CFormLabel>
      <CCol sm="5">
        <CFormInput
          :value="modelValue.project_name ?? modelValue.case_title ?? ''"
          placeholder="예: 00시 00동 복합시설 개발사업 추진 및 초기 집행 승인의 건"
          required
          @input="updateField('project_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">승인 의결 구분</CFormLabel>
      <CCol sm="3">
        <CFormSelect
          :value="modelValue.approval_type ?? 'NEW_LAUNCH'"
          required
          @change="updateField('approval_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in approvalTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 사업 위치 & 사업 규모 요약 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">사업 부지 위치</CFormLabel>
      <CCol sm="5">
        <CFormInput
          :value="modelValue.location ?? ''"
          placeholder="사업부지 소재지 지번/도로명 주소"
          required
          @input="updateField('location', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">사업 규모 / 용도</CFormLabel>
      <CCol sm="3">
        <CFormInput
          :value="modelValue.biz_scale_summary ?? ''"
          placeholder="예: 공동주택 450세대, 연면적 42,000㎡"
          @input="updateField('biz_scale_summary', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 금회 승인 요청 예산 및 전체 사업비 카드 -->
    <div class="card mb-3 border border-success">
      <div class="card-header bg-success bg-opacity-10 py-2 fw-semibold small text-success">
        <CIcon name="cilMoney" class="me-1 text-success" />
        금회 승인 요청 예산 및 전체 사업비 요약 (단위: 원)
      </div>
      <div class="card-body p-2">
        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small required text-success fw-bold"
            >금회 승인 요청액</CFormLabel
          >
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000000"
                class="text-end fw-bold text-success fs-6"
                :value="
                  modelValue.requested_amount ??
                  modelValue.approval_budget ??
                  modelValue.amount ??
                  0
                "
                required
                @input="
                  updateField(
                    'requested_amount',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText class="fw-bold text-success">원</CInputGroupText>
            </CInputGroup>
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end">전체 총사업비</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000000"
                class="text-end fw-semibold text-danger"
                :value="modelValue.total_project_cost ?? 0"
                @input="
                  updateField(
                    'total_project_cost',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>

        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label small">예상 총분양수입</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                min="0"
                step="10000000"
                class="text-end fw-semibold text-primary"
                :value="modelValue.total_expected_revenue ?? 0"
                @input="
                  updateField(
                    'total_expected_revenue',
                    Number(($event.target as HTMLInputElement).value) || 0,
                  )
                "
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end">예상 세전 이익</CFormLabel>
          <CCol sm="4">
            <CInputGroup size="sm">
              <CFormInput
                type="number"
                readonly
                class="text-end fw-bold bg-light"
                :class="expectedProfit >= 0 ? 'text-primary' : 'text-danger'"
                :value="expectedProfit"
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>

        <!-- 금회 승인 예산 집행 세부 내역 -->
        <CRow>
          <CFormLabel class="col-sm-2 col-form-label small required">예산 집행 내역</CFormLabel>
          <CCol sm="10">
            <CFormInput
              size="sm"
              :value="modelValue.budget_usage_plan ?? ''"
              placeholder="예: 토지 매매계약금 50억원, 계약이행보증보험료 1억원, 초기 인허가 설계 착수금 2억원"
              required
              @input="updateField('budget_usage_plan', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
        </CRow>
      </div>
    </div>

    <!-- 주요 승인 의결 요청 사항 (핵심) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">승인 의결 사항</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.resolution_matters ?? modelValue.purpose ?? ''"
          rows="4"
          placeholder="이사회 / 대표이사 승인을 요청하는 주요 의결 안건을 번호를 매겨 상세히 기술해 주세요.&#10;예:&#10;1) 대상 부지(00시 00동 일원) 매매계약 체결 및 계약금(50억원) 집행 승인의 건&#10;2) 건축설계 및 인허가 용역계약 체결 승인의 건&#10;3) 본 사업 추진을 위한 프로젝트 TF팀 발족 승인의 건"
          required
          @input="updateField('resolution_matters', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 사업 총괄 PM / 조직 & 추진 일정 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">총괄 PM / 담당</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.pm_lead ?? ''"
          placeholder="예: 개발사업본부 1팀 / 홍길동 팀장"
          @input="updateField('pm_lead', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">향후 추진 일정</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.target_schedule ?? ''"
          placeholder="예: 2026.09 토지잔금 -> 2026.12 사업승인 -> 2027.03 착공/분양"
          @input="updateField('target_schedule', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 기대 효과 및 리스크 대책 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">기대효과/리스크</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.expected_effects ?? modelValue.risk_mitigation ?? ''"
          rows="2"
          placeholder="예상 수익 창출 효과, 자금 회수 계획 및 주요 리스크 요인 헷지 방안"
          @input="updateField('expected_effects', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 첨부 서류 및 비고 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">첨부 서류 / 비고</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.enclosed_docs ?? modelValue.note ?? ''"
          placeholder="예: 사업수지표 최종안 1부, 토지매매계약서 초안 1부, 감정평가서 1부"
          @input="updateField('enclosed_docs', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
