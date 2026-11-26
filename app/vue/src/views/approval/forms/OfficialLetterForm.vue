<script setup lang="ts">
import { computed, watch } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import { useCompany } from '@/store/pinia/company'
import type { ApprovalContent } from '@/store/types/approval'
import type { CompanySeal } from '@/store/types/settings'
import {
  FALLBACK_SEAL_TYPE_OPTIONS,
  SEND_METHOD_OPTIONS,
  asNum,
  asOptNum,
  asStr,
  getLocalToday,
  getSafeExternalUrl,
} from '../utils/approvalMeta'

const props = defineProps<{
  modelValue: ApprovalContent
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: ApprovalContent): void
}>()

const comStore = useCompany()
const sealList = computed<CompanySeal[]>(() => comStore.sealList)

const safeSealImageUrl = computed(() => getSafeExternalUrl(asStr(props.modelValue.seal_image)))

const hasFallbackSealOption = computed(() => {
  const sid = asOptNum(props.modelValue.seal_id)
  return !!sid && sealList.value.length > 0 && !sealList.value.some(s => s.pk === sid)
})

const updateField = (key: string, val: unknown) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: val,
  })
}

const onSelectSeal = (sealPkStr: string) => {
  const sealPk = Number(sealPkStr) || null
  const selected = sealList.value.find(s => s.pk === sealPk)
  if (selected) {
    emit('update:modelValue', {
      ...props.modelValue,
      seal_id: selected.pk,
      seal_name: selected.name,
      seal_type: selected.seal_type,
      seal_image: selected.seal_image,
    })
  } else {
    emit('update:modelValue', {
      ...props.modelValue,
      seal_id: null,
      seal_name: '',
      seal_type: sealPkStr || 'OMIT',
      seal_image: null,
    })
  }
}

const sendDueDate = computed({
  get: () => asStr(props.modelValue.send_due_date),
  set: (val: string) => updateField('send_due_date', val),
})

const syncSealListAndDefaults = async (companyId?: number | null, resetInvalidSeal = false) => {
  await comStore.fetchCompanySealList(companyId ?? undefined)

  // 기본값 세팅 및 회사 변경 시 비호환 인장 초기화
  const initial: ApprovalContent = { ...props.modelValue }
  let changed = false

  if (!asStr(initial.send_method)) {
    initial.send_method = 'EMAIL'
    changed = true
  }

  const currentSealId = asOptNum(initial.seal_id)
  if (resetInvalidSeal && currentSealId && !sealList.value.some(s => s.pk === currentSealId)) {
    initial.seal_id = null
    initial.seal_name = ''
    initial.seal_type = ''
    initial.seal_image = null
    changed = true
  }

  if (!initial.seal_id && !asStr(initial.seal_type)) {
    if (sealList.value.length > 0) {
      const firstSeal = sealList.value[0]
      initial.seal_id = firstSeal.pk
      initial.seal_name = firstSeal.name
      initial.seal_type = firstSeal.seal_type
      initial.seal_image = firstSeal.seal_image
    } else {
      initial.seal_type = 'CORP_SEAL'
    }
    changed = true
  }
  if (initial.seal_count === undefined || initial.seal_count === null) {
    initial.seal_count = 1
    changed = true
  }
  if (!asStr(initial.send_due_date)) {
    initial.send_due_date = getLocalToday()
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
}

watch(
  () => comStore.company?.pk,
  (newComId, oldComId) => {
    void syncSealListAndDefaults(newComId, oldComId !== undefined && newComId !== oldComId)
  },
  { immediate: true },
)
</script>

<template>
  <div class="official-letter-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilEnvelopeLetter" class="me-1" />
      공문 발신 / 대외 발송 정보
    </h6>

    <!-- 수신처 & 참조처 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">수신처</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.receiver)"
          placeholder="예: (주)한국건설 대표이사, 강남구청장"
          required
          @input="updateField('receiver', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label">참조처 (경유)</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.refer_to)"
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
          :value="asStr(modelValue.sender_name)"
          placeholder="미입력 시 회사 대표이사 명의로 발신"
          @input="updateField('sender_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label">대외 공문번호</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.doc_number_external)"
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
          :value="asStr(modelValue.letter_subject)"
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
          :value="asStr(modelValue.letter_body)"
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
          :value="asStr(modelValue.enclosed_files_desc)"
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
          :value="asStr(modelValue.send_method, 'EMAIL')"
          required
          @change="updateField('send_method', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="m in SEND_METHOD_OPTIONS" :key="m.value" :value="m.value">
            {{ m.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required">발송 희망일</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="sendDueDate" required placeholder="발송 희망일 선택" />
      </CCol>
    </CRow>

    <!-- 날인 인감 구분 & 부수 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label required">날인 인감</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="
            modelValue.seal_id
              ? String(modelValue.seal_id)
              : asStr(modelValue.seal_type, 'CORP_SEAL')
          "
          required
          @change="onSelectSeal(($event.target as HTMLSelectElement).value)"
        >
          <template v-if="sealList.length > 0">
            <option v-if="hasFallbackSealOption" :value="String(modelValue.seal_id)">
              {{ asStr(modelValue.seal_name, '기존 선택 인장') }}
              <template v-if="modelValue.seal_type"> ({{ asStr(modelValue.seal_type) }})</template>
            </option>
            <option v-for="s in sealList" :key="s.pk" :value="String(s.pk)">
              {{ s.name }} ({{ s.seal_type_desc || s.seal_type }})
            </option>
            <option value="OMIT">직인생략</option>
          </template>
          <template v-else>
            <option v-for="s in FALLBACK_SEAL_TYPE_OPTIONS" :key="s.value" :value="s.value">
              {{ s.label }}
            </option>
          </template>
        </CFormSelect>

        <!-- 인장 미리보기 (이미지가 등록되어 있는 경우) -->
        <div v-if="safeSealImageUrl" class="mt-2 d-flex align-items-center">
          <img
            :src="safeSealImageUrl"
            alt="인장 미리보기"
            style="
              width: 42px;
              height: 42px;
              object-fit: contain;
              border: 1px dashed #ccc;
              border-radius: 4px;
              padding: 2px;
            "
            class="me-2 bg-more-white"
          />
          <small class="text-muted">{{ modelValue.seal_name }} (인장 등록됨)</small>
        </div>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required">날인 부수</CFormLabel>
      <CCol sm="4">
        <CFormInput
          type="number"
          min="1"
          :value="asNum(modelValue.seal_count, 1)"
          required
          @input="updateField('seal_count', Number(($event.target as HTMLInputElement).value) || 1)"
        />
      </CCol>
    </CRow>
  </div>
</template>
