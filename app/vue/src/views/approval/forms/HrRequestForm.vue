<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const eventDate = computed({
  get: () => props.modelValue.event_date ?? '',
  set: (val: string) => updateField('event_date', val),
})

const leaveStartDate = computed({
  get: () => props.modelValue.leave_start_date ?? '',
  set: (val: string) => updateField('leave_start_date', val),
})

const leaveEndDate = computed({
  get: () => props.modelValue.leave_end_date ?? '',
  set: (val: string) => updateField('leave_end_date', val),
})

const reinstatementDate = computed({
  get: () => props.modelValue.reinstatement_date ?? '',
  set: (val: string) => updateField('reinstatement_date', val),
})

const requestTypes = [
  { value: 'CERTIFICATE', label: '제증명서 발급 신청' },
  { value: 'CONGRATULATION_CONDOLENCE', label: '경조사 지원 / 경조금 신청' },
  { value: 'LEAVE_OF_ABSENCE', label: '휴직 신청원' },
  { value: 'REINSTATEMENT', label: '복직원 제출' },
  { value: 'ACCOUNT_CHANGE', label: '급여계좌 / 개인정보 변경' },
  { value: 'BENEFIT', label: '기타 복리후생 신청' },
  { value: 'OTHER', label: '기타 인사 신청' },
]

const certTypes = [
  { value: 'EMPLOYMENT', label: '재직증명서' },
  { value: 'CAREER', label: '경력증명서' },
  { value: 'RETIREMENT', label: '퇴직증명서' },
  { value: 'WITHHOLDING_TAX', label: '원천징수영수증' },
  { value: 'PAY_SLIP', label: '급여명세확인서' },
  { value: 'OTHER', label: '기타 증명서' },
]

const eventTypes = [
  { value: 'MARRIAGE_SELF', label: '본인 결혼' },
  { value: 'MARRIAGE_CHILD', label: '자녀 결혼' },
  { value: 'CHILSOON_PARENT', label: '부모 칠순/팔순' },
  { value: 'DEATH_PARENT', label: '부모/배우자부모 사망' },
  { value: 'DEATH_GRANDPARENT', label: '조부모 사망' },
  { value: 'CHILDBIRTH', label: '출산 축하' },
  { value: 'OTHER', label: '기타 경조사' },
]

const receiveMethods = [
  { value: 'PDF_EMAIL', label: '전자문서 (PDF 이메일 수신)' },
  { value: 'PRINT_DIRECT', label: '실물 원본 직접 수령' },
  { value: 'POST', label: '우편(등기) 수령' },
]

const updateField = (key: string, val: any) => {
  const updated = {
    ...props.modelValue,
    [key]: val,
  }

  // 경조금 또는 지원금액 변경 시 amount 동기화 (전결 정책 연동)
  if (key === 'congratulation_amount') {
    updated.amount = Number(val) || 0
  }

  emit('update:modelValue', updated)
}

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.request_type) {
    initial.request_type = 'CERTIFICATE'
    changed = true
  }
  if (!initial.cert_type) {
    initial.cert_type = 'EMPLOYMENT'
    changed = true
  }
  if (!initial.cert_language) {
    initial.cert_language = 'KOREAN'
    changed = true
  }
  if (initial.cert_count === undefined || initial.cert_count === null) {
    initial.cert_count = 1
    changed = true
  }
  if (!initial.receive_method) {
    initial.receive_method = 'PDF_EMAIL'
    changed = true
  }
  if (initial.include_resident_num === undefined) {
    initial.include_resident_num = false
    changed = true
  }
  if (!initial.event_type) {
    initial.event_type = 'MARRIAGE_SELF'
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="hr-request-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilContact" class="me-1" />
      인사 관련 신청 정보
    </h6>

    <!-- 신청 구분 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">신청 구분</CFormLabel>
      <CCol sm="5">
        <CFormSelect
          :value="modelValue.request_type ?? 'CERTIFICATE'"
          required
          @change="updateField('request_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in requestTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">수령/처리 방법</CFormLabel>
      <CCol sm="3">
        <CFormSelect
          :value="modelValue.receive_method ?? 'PDF_EMAIL'"
          @change="updateField('receive_method', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="m in receiveMethods" :key="m.value" :value="m.value">
            {{ m.label }}
          </option>
        </CFormSelect>
      </CCol>
    </CRow>

    <!-- 1. 제증명서 발급 상세 섹션 -->
    <div
      v-if="modelValue.request_type === 'CERTIFICATE'"
      class="p-3 bg-more-white border rounded mb-3"
    >
      <h6 class="fw-bold text-secondary mb-3 small">
        <CIcon name="cilDescription" class="me-1" />
        증명서 발급 세부 정보
      </h6>
      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-form-label required">증명서 종류</CFormLabel>
        <CCol sm="4">
          <CFormSelect
            :value="modelValue.cert_type ?? 'EMPLOYMENT'"
            required
            @change="updateField('cert_type', ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="c in certTypes" :key="c.value" :value="c.value">
              {{ c.label }}
            </option>
          </CFormSelect>
        </CCol>
        <CFormLabel class="col-sm-2 col-form-label text-sm-end required"
          >발급 언어 / 부수</CFormLabel
        >
        <CCol sm="2">
          <CFormSelect
            :value="modelValue.cert_language ?? 'KOREAN'"
            @change="updateField('cert_language', ($event.target as HTMLSelectElement).value)"
          >
            <option value="KOREAN">국문</option>
            <option value="ENGLISH">영문</option>
          </CFormSelect>
        </CCol>
        <CCol sm="2">
          <CInputGroup size="sm">
            <CFormInput
              type="number"
              min="1"
              :value="modelValue.cert_count ?? 1"
              @input="
                updateField('cert_count', Number(($event.target as HTMLInputElement).value) || 1)
              "
            />
            <CInputGroupText>부</CInputGroupText>
          </CInputGroup>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-form-label required">제출처</CFormLabel>
        <CCol sm="4">
          <CFormInput
            :value="modelValue.submit_to ?? ''"
            placeholder="예: 국민은행 강남지점, 관공서"
            required
            @input="updateField('submit_to', ($event.target as HTMLInputElement).value)"
          />
        </CCol>
        <CFormLabel class="col-sm-2 col-form-label text-sm-end required">용도</CFormLabel>
        <CCol sm="4">
          <CFormInput
            :value="modelValue.usage_purpose ?? ''"
            placeholder="예: 금융기관 대출용, 비자 발급용"
            required
            @input="updateField('usage_purpose', ($event.target as HTMLInputElement).value)"
          />
        </CCol>
      </CRow>

      <CRow class="mb-1">
        <CFormLabel class="col-sm-2 col-form-label">주민등록번호</CFormLabel>
        <CCol sm="10" class="d-flex align-items-center">
          <CFormCheck
            id="residentNumCheck"
            label="주민등록번호 뒷자리 전체 표기 (미체크 시 생년월일만 표기됨)"
            :checked="modelValue.include_resident_num ?? false"
            @change="
              updateField('include_resident_num', ($event.target as HTMLInputElement).checked)
            "
          />
        </CCol>
      </CRow>
    </div>

    <!-- 2. 경조사 지원 / 경조금 상세 섹션 -->
    <div
      v-else-if="modelValue.request_type === 'CONGRATULATION_CONDOLENCE'"
      class="p-3 bg-white border rounded mb-3"
    >
      <h6 class="fw-bold text-secondary mb-3 small">
        <CIcon name="cilHeart" class="me-1 text-danger" />
        경조사 지원 및 경조금 신청 정보
      </h6>
      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-form-label required">경조 구분</CFormLabel>
        <CCol sm="4">
          <CFormSelect
            :value="modelValue.event_type ?? 'MARRIAGE_SELF'"
            required
            @change="updateField('event_type', ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="e in eventTypes" :key="e.value" :value="e.value">
              {{ e.label }}
            </option>
          </CFormSelect>
        </CCol>
        <CFormLabel class="col-sm-2 col-form-label text-sm-end required">경조 일자</CFormLabel>
        <CCol sm="4">
          <DatePicker v-model="eventDate" required placeholder="경조 일자 선택" />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel class="col-sm-2 col-form-label required">경조 장소</CFormLabel>
        <CCol sm="4">
          <CFormInput
            :value="modelValue.event_place ?? ''"
            placeholder="예: 서울 아펠가모 선릉 3층, 삼성서울병원 장례식장 5호"
            required
            @input="updateField('event_place', ($event.target as HTMLInputElement).value)"
          />
        </CCol>
        <CFormLabel class="col-sm-2 col-form-label text-sm-end">경조금 신청액</CFormLabel>
        <CCol sm="4">
          <CInputGroup>
            <CFormInput
              type="number"
              min="0"
              step="50000"
              :value="modelValue.congratulation_amount ?? modelValue.amount ?? 0"
              placeholder="0"
              @input="
                updateField(
                  'congratulation_amount',
                  Number(($event.target as HTMLInputElement).value) || 0,
                )
              "
            />
            <CInputGroupText>원</CInputGroupText>
          </CInputGroup>
        </CCol>
      </CRow>

      <CRow class="mb-1">
        <CFormLabel class="col-sm-2 col-form-label">물품 지원 요청</CFormLabel>
        <CCol sm="10">
          <CFormInput
            :value="modelValue.support_items ?? ''"
            placeholder="예: 축하 화환 1점, 근조 화환 1점 및 상조용품(종이컵/식기세트 300인분) 배송 요청"
            @input="updateField('support_items', ($event.target as HTMLInputElement).value)"
          />
        </CCol>
      </CRow>
    </div>

    <!-- 3. 휴직 / 복직 상세 섹션 -->
    <div
      v-else-if="
        modelValue.request_type === 'LEAVE_OF_ABSENCE' ||
        modelValue.request_type === 'REINSTATEMENT'
      "
      class="p-3 bg-white border rounded mb-3"
    >
      <h6 class="fw-bold text-secondary mb-3 small">
        <CIcon name="cilCalendar" class="me-1" />
        {{ modelValue.request_type === 'LEAVE_OF_ABSENCE' ? '휴직 신청' : '복직원' }} 기간 정보
      </h6>
      <CRow v-if="modelValue.request_type === 'LEAVE_OF_ABSENCE'" class="mb-2">
        <CFormLabel class="col-sm-2 col-form-label required">휴직 예정 기간</CFormLabel>
        <CCol sm="10">
          <div class="d-flex align-items-center gap-2 flex-wrap">
            <DatePicker v-model="leaveStartDate" required placeholder="휴직 시작일" />
            <span>~</span>
            <DatePicker v-model="leaveEndDate" required placeholder="휴직 종료일" />
          </div>
        </CCol>
      </CRow>
      <CRow v-else class="mb-2">
        <CFormLabel class="col-sm-2 col-form-label required">복직 희망일</CFormLabel>
        <CCol sm="4">
          <DatePicker v-model="reinstatementDate" required placeholder="복직 희망일 선택" />
        </CCol>
      </CRow>
    </div>

    <!-- 공통 신청 사유 및 상세 내용 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">신청 사유 / 상세</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.reason ?? ''"
          rows="4"
          placeholder="신청 사유 및 요청 사항을 상세히 기술해 주세요."
          required
          @input="updateField('reason', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 비고 / 특이사항 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">비고 / 특이사항</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="modelValue.note ?? ''"
          placeholder="추가 전달 사항 또는 첨부 서류 안내 (예: 청첩장/가족관계증명서 첨부)"
          @input="updateField('note', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
