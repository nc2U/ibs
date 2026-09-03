<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const contractTypes = [
  { value: 'CONSTRUCTION', label: '공사 도급 / 하도급 계약' },
  { value: 'SERVICE', label: '용역 / 설계 / 감리 / PM 계약' },
  { value: 'PURCHASE', label: '물품 공급 / 자재 구매 계약' },
  { value: 'LEASE', label: '부동산 임대차 / 시설물 계약' },
  { value: 'MOU_NDA', label: '업무협약(MOU) / 비밀유지(NDA)' },
  { value: 'OTHER', label: '기타 일반 계약' },
]

const contractKinds = [
  { value: 'NEW', label: '신규 계약' },
  { value: 'CHANGE', label: '변경 (증액 / 감액 / 연장)' },
  { value: 'RENEWAL', label: '갱신 / 연장 계약' },
]

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // contract_amount 변경 시 amount 동기화 (전결 결재선 연동)
  if (key === 'contract_amount') {
    updated.amount = Number(val) || 0
  }

  emit('update:modelValue', updated)
}

const contractStartDate = computed({
  get: () => props.modelValue.contract_start_date ?? '',
  set: (val: string) => updateField('contract_start_date', val),
})

const contractEndDate = computed({
  get: () => props.modelValue.contract_end_date ?? '',
  set: (val: string) => updateField('contract_end_date', val),
})

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.contract_type) {
    initial.contract_type = 'SERVICE'
    changed = true
  }
  if (!initial.contract_kind) {
    initial.contract_kind = 'NEW'
    changed = true
  }
  if (!initial.vat_type) {
    initial.vat_type = 'EXCLUDED'
    changed = true
  }
  if (!initial.contract_start_date) {
    initial.contract_start_date = new Date().toISOString().substring(0, 10)
    changed = true
  }
  if (!initial.contract_end_date) {
    const d = new Date()
    d.setFullYear(d.getFullYear() + 1)
    initial.contract_end_date = d.toISOString().substring(0, 10)
    changed = true
  }
  if (initial.contract_amount === undefined && initial.amount) {
    initial.contract_amount = initial.amount
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="contract-proposal-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-info">
      <CIcon name="cilDescription" class="me-1" />
      계약 체결 품의 정보
    </h6>

    <!-- 계약 구분 & 계약 형태 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">계약 구분</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.contract_type ?? 'SERVICE'"
          required
          @change="updateField('contract_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in contractTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">계약 형태</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.contract_kind ?? 'NEW'"
          required
          @change="updateField('contract_kind', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="k in contractKinds" :key="k.value" :value="k.value">
            {{ k.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 계약명 (건명) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">계약 건명</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.contract_name ?? ''"
          placeholder="예: 00프로젝트 현장 토목설계 및 인허가 용역 계약 체결의 건"
          required
          @input="updateField('contract_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 계약 상대방 정보 -->
    <div class="card mb-3 border">
      <div class="card-header bg-more-white py-2 fw-semibold small text-primary">
        <CIcon name="cilBuilding" class="me-1" />
        계약 상대방 (업체 / 거래처 정보)
      </div>
      <div class="card-body p-2">
        <CRow class="mb-2">
          <CFormLabel class="col-sm-2 col-form-label required small">상호 (법인명)</CFormLabel>
          <CCol sm="4">
            <CFormInput
              size="sm"
              :value="modelValue.contractor_name ?? ''"
              placeholder="상호 / 법인명 (예: (주)한국건설엔지니어링)"
              required
              @input="updateField('contractor_name', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end">대표자명</CFormLabel>
          <CCol sm="4">
            <CFormInput
              size="sm"
              :value="modelValue.contractor_ceo ?? ''"
              placeholder="대표자 성명"
              @input="updateField('contractor_ceo', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
        </CRow>
        <CRow>
          <CFormLabel class="col-sm-2 col-form-label small">사업자등록번호</CFormLabel>
          <CCol sm="4">
            <CFormInput
              size="sm"
              :value="modelValue.contractor_reg_number ?? ''"
              placeholder="000-00-00000"
              @input="
                updateField('contractor_reg_number', ($event.target as HTMLInputElement).value)
              "
            />
          </CCol>
          <CFormLabel class="col-sm-2 col-form-label small text-sm-end">담당자 / 연락처</CFormLabel>
          <CCol sm="4">
            <CFormInput
              size="sm"
              :value="modelValue.contractor_contact ?? ''"
              placeholder="홍길동 부장 (010-0000-0000)"
              @input="updateField('contractor_contact', ($event.target as HTMLInputElement).value)"
            />
          </CCol>
        </CRow>
      </div>
    </div>

    <!-- 계약 금액 & 부가세 & 계약 기간 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">계약 금액</CFormLabel>
      <CCol sm="4">
        <CInputGroup>
          <CFormInput
            type="number"
            min="0"
            step="10000"
            class="text-end fw-bold text-danger fs-6"
            :value="modelValue.contract_amount ?? modelValue.amount ?? 0"
            placeholder="0"
            required
            @input="
              updateField('contract_amount', Number(($event.target as HTMLInputElement).value) || 0)
            "
          />
          <CInputGroupText>원</CInputGroupText>
        </CInputGroup>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">부가세 구분</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.vat_type ?? 'EXCLUDED'"
          @change="updateField('vat_type', ($event.target as HTMLSelectElement).value)"
        >
          <option value="EXCLUDED">VAT 별도</option>
          <option value="INCLUDED">VAT 포함</option>
          <option value="ZERO_TAX">면세 / 영세율</option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 계약 기간 (시작일 ~ 종료일) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">계약 기간</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="contractStartDate" required placeholder="계약 시작일" />
      </CCol>
      <CCol sm="1" class="text-center pt-2 fw-bold text-muted">~</CCol>
      <CCol sm="4">
        <DatePicker v-model="contractEndDate" required placeholder="계약 종료일" />
      </CCol>
    </CRow>

    <!-- 대금 지급 조건 & 보증 조건 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">대금 지급 조건</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.payment_terms ?? ''"
          placeholder="예: 계약금 10%, 1차 중도금 40%, 잔금 50% (세금계산서 발행 후 30일 이내 현금 지급)"
          @input="updateField('payment_terms', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">이행 / 하자보증</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.warranty_terms ?? ''"
          placeholder="예: 계약이행보증증권 10%, 하자보수보증증권 5% (준공일로부터 2년간)"
          @input="updateField('warranty_terms', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 계약 체결 사유 / 배경 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">계약 체결 사유</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.purpose_reason ?? modelValue.purpose ?? ''"
          rows="4"
          placeholder="계약 체결의 목적, 배경, 업체 선정 경위 및 계약에 따른 기대 효과를 상세히 기재해 주세요."
          required
          @input="updateField('purpose_reason', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 주요 특약 및 특이사항 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">특약 / 비고</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.special_terms ?? modelValue.note ?? ''"
          rows="2"
          placeholder="계약서 상 특별 조항, 지체상금율, 해지 조건 또는 기타 특이사항 (계약서 초안 첨부 요망)"
          @input="updateField('special_terms', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
