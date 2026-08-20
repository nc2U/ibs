<script setup lang="ts">
import { onMounted } from 'vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const sendMethods = [
  { value: 'EMAIL', label: '전자우편 (이메일)' },
  { value: 'POST', label: '등기우편' },
  { value: 'DIRECT', label: '인편 (직접전달)' },
  { value: 'FAX', label: '팩스 (FAX)' },
  { value: 'OTHER', label: '기타' },
]

const sealTypes = [
  { value: 'CORP_SEAL', label: '법인인감 (대표이사 직인)' },
  { value: 'USAGE_SEAL_1', label: '사용인감 1호' },
  { value: 'USAGE_SEAL_2', label: '사용인감 2호' },
  { value: 'SIGN', label: '서명 (Sign)' },
  { value: 'OMIT', label: '직인생략' },
]

const updateField = (key: string, val: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: val,
  })
}

onMounted(() => {
  // 기본값 세팅
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.send_method) {
    initial.send_method = 'EMAIL'
    changed = true
  }
  if (!initial.seal_type) {
    initial.seal_type = 'CORP_SEAL'
    changed = true
  }
  if (initial.seal_count === undefined || initial.seal_count === null) {
    initial.seal_count = 1
    changed = true
  }
  if (!initial.send_due_date) {
    initial.send_due_date = new Date().toISOString().substring(0, 10)
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="official-letter-form p-3 border rounded bg-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilEnvelopeLetter" class="me-1" />
      공문 발신 / 대외 발송 정보
    </h6>

    <!-- 수신처 & 참조처 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">수신처</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.receiver ?? ''"
          placeholder="예: (주)한국건설 대표이사, 강남구청장"
          required
          @input="updateField('receiver', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label">참조처 (경유)</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.refer_to ?? ''"
          placeholder="예: 공무팀장, 건축과 담당자"
          @input="updateField('refer_to', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 발신명의 & 대외 문서번호 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">발신 명의</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.sender_name ?? ''"
          placeholder="미입력 시 회사 대표이사 명의로 발신"
          @input="updateField('sender_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label">대외 공문번호</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.doc_number_external ?? ''"
          placeholder="예: IBS-2026-001 (사후 기재 가능)"
          @input="updateField('doc_number_external', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 공문 제목 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">공문 제목</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.letter_subject ?? ''"
          placeholder="예: [00현장] 공사기간 연장 요청 및 승인의 건"
          required
          @input="updateField('letter_subject', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 공문 본문 / 요지 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">공문 본문 (요지)</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.letter_body ?? ''"
          rows="6"
          placeholder="대외 발송할 공문의 세부 본문 또는 발송 목적과 요지를 상세히 작성해 주세요."
          required
          @input="updateField('letter_body', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 붙임 (첨부 서류 목록) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">붙임 서류 내역</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.enclosed_files_desc ?? ''"
          rows="2"
          placeholder="예: 1. 설계변경 내역서 1부.&#10;2. 현장 감리 확인서 1부. 끝."
          @input="updateField('enclosed_files_desc', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <hr class="my-3 text-muted" />

    <h6 class="fw-bold mb-3 text-secondary">
      <CIcon name="cilPaperclip" class="me-1" />
      발송 및 인감 날인 요청 정보
    </h6>

    <!-- 발송 방법 & 발송 희망일 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">발송 방법</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.send_method ?? 'EMAIL'"
          required
          @change="updateField('send_method', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="m in sendMethods" :key="m.value" :value="m.value">
            {{ m.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required">발송 희망일</CFormLabel>
      <CCol sm="4">
        <CFormInput
          type="date"
          :value="modelValue.send_due_date ?? ''"
          required
          @input="updateField('send_due_date', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 날인 인감 구분 & 부수 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label required">날인 인감</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.seal_type ?? 'CORP_SEAL'"
          required
          @change="updateField('seal_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="s in sealTypes" :key="s.value" :value="s.value">
            {{ s.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required">날인 부수</CFormLabel>
      <CCol sm="4">
        <CFormInput
          type="number"
          min="1"
          :value="modelValue.seal_count ?? 1"
          required
          @input="updateField('seal_count', Number(($event.target as HTMLInputElement).value) || 1)"
        />
      </CCol>
    </CRow>
  </div>
</template>
