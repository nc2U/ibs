<script setup lang="ts">
import { onMounted } from 'vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const reviewTypes = [
  { value: 'CONTRACT_REVIEW', label: '계약서 / 협약서 사전 법률 검토' },
  { value: 'LITIGATION_DISPUTE', label: '소송 / 지급명령 / 분쟁 대응 검토' },
  { value: 'REGULATORY_COMPLIANCE', label: '법령 해석 / 규제 및 인허가 자문' },
  { value: 'INTERNAL_RULE', label: '사규 / 취업규칙 / 내부규정 검토' },
  { value: 'CLAIM_NOTICE', label: '내용증명 / 공문 / 대외 발송문 검토' },
  { value: 'OTHER', label: '기타 법률 자문' },
]

const urgencyLevels = [
  { value: 'NORMAL', label: '보통 (3~5영업일)' },
  { value: 'URGENT', label: '긴급 (1~2영업일)' },
  { value: 'VERY_URGENT', label: '당일 긴급' },
]

const riskLevels = [
  { value: 'LOW', label: '낮음 (원안 체결/진행 가능)' },
  { value: 'MEDIUM', label: '중간 (수정 권고 조항 반영 후 진행)' },
  { value: 'HIGH', label: '높음 (중대한 불리 조항 존재 / 진행 재검토)' },
]

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // dispute_amount 변경 시 amount 동기화 (전결 결재선 연동)
  if (key === 'dispute_amount') {
    updated.amount = Number(val) || 0
  }

  emit('update:modelValue', updated)
}

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.review_type) {
    initial.review_type = 'CONTRACT_REVIEW'
    changed = true
  }
  if (!initial.urgency) {
    initial.urgency = 'NORMAL'
    changed = true
  }
  if (!initial.review_due_date) {
    const d = new Date()
    d.setDate(d.getDate() + 5)
    initial.review_due_date = d.toISOString().substring(0, 10)
    changed = true
  }
  if (!initial.risk_level) {
    initial.risk_level = 'LOW'
    changed = true
  }
  if (initial.dispute_amount === undefined && initial.amount) {
    initial.dispute_amount = initial.amount
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="legal-review-form p-3 border rounded bg-light mb-3">
    <h6 class="fw-bold mb-3 text-secondary">
      <CIcon name="cilBalanceScale" class="me-1 text-primary" />
      법무 검토 의뢰 및 결과 보고
    </h6>

    <!-- 검토 구분 & 긴급도 & 회신희망일 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">검토 분야</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.review_type ?? 'CONTRACT_REVIEW'"
          required
          @change="updateField('review_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in reviewTypes" :key="t.value" :value="t.value">
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

    <!-- 검토 의뢰 건명 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">의뢰 건명</CFormLabel>
      <CCol sm="6">
        <CFormInput
          :value="modelValue.case_title ?? ''"
          placeholder="예: 00프로젝트 토지매매계약서 특약 조항 법률 리스크 검토의 건"
          required
          @input="updateField('case_title', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">회신 희망일</CFormLabel>
      <CCol sm="2">
        <CFormInput
          type="date"
          :value="modelValue.review_due_date ?? ''"
          @input="updateField('review_due_date', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 상대방 / 관련 프로젝트 / 관련 가액 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">상대방 (당사자)</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.counterparty ?? ''"
          placeholder="거래 상대방 / 피신청인 / 원고·피고"
          @input="updateField('counterparty', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">관련 가액/금액</CFormLabel>
      <CCol sm="4">
        <CInputGroup>
          <CFormInput
            type="number"
            min="0"
            step="10000"
            class="text-end fw-semibold"
            :value="modelValue.dispute_amount ?? modelValue.amount ?? 0"
            placeholder="0"
            @input="updateField('dispute_amount', Number(($event.target as HTMLInputElement).value) || 0)"
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
    </CRow>

    <!-- 사실관계 및 검토 배경 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">사실관계 및 배경</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.background ?? modelValue.purpose ?? ''"
          rows="3"
          placeholder="본 건의 추진 배경, 거래 경위, 분쟁 발생 경위 등 기초 사실관계를 명확히 기재해 주세요."
          required
          @input="updateField('background', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 주요 쟁점 사항 (의뢰 부서 핵심 요청) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">주요 쟁점 사항</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.key_issues ?? ''"
          rows="4"
          placeholder="법률 검토를 집중적으로 요청하는 핵심 쟁점 및 의문 사항을 조항별로 번호를 매겨 기재해 주세요.&#10;예:&#10;1) 계약서 제8조(손해배상)의 지체상금율이 관련 법령상 과다하여 무효가 될 위험 여부&#10;2) 제15조(관할법원) 상대방 본사 소재지 관할 조항 수정 필요성"
          required
          @input="updateField('key_issues', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 법무 검토 종합 의견 (법무팀/자문변호사 회신 영역) -->
    <div class="card mb-3 border border-primary">
      <div class="card-header bg-primary bg-opacity-10 py-2 fw-semibold small text-primary d-flex justify-content-between align-items-center">
        <span>
          <CIcon name="cilCheckCircle" class="me-1 text-primary" />
          법무 검토 결과 및 종합의견 (법무팀 작성 / 회신)
        </span>
        <div class="d-flex align-items-center">
          <span class="me-2 small text-dark fw-normal">법적 리스크:</span>
          <CFormSelect
            size="sm"
            style="width: 210px"
            :value="modelValue.risk_level ?? 'LOW'"
            @change="updateField('risk_level', ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="r in riskLevels" :key="r.value" :value="r.value">
              {{ r.label }}
            </option>
          </CFormSelect>
        </div>
      </div>
      <div class="card-body p-2">
        <CFormTextarea
          :value="modelValue.legal_opinion ?? ''"
          rows="4"
          placeholder="법무팀 또는 자문변호사의 법률 검토 종합 의견, 조항별 수정 권고사항 및 대안 조항을 기술해 주세요."
          @input="updateField('legal_opinion', ($event.target as HTMLTextAreaElement).value)"
        />
      </div>
    </div>

    <!-- 첨부 서류 및 비고 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">첨부 서류 / 비고</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.enclosed_docs ?? modelValue.note ?? ''"
          placeholder="예: 계약서 초안 1부, 상대방 사업자등록증 1부, 내용증명 사본 1부"
          @input="updateField('enclosed_docs', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
