<script lang="ts" setup>
import { ref, reactive, computed, onMounted, onUpdated, type PropType } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { type SuitCase } from '@/store/types/docs'
import { courtChoices } from './components/court'
import MultiSelect from '@/components/MultiSelect/index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  sortName: { type: String, default: '[본사]' },
  getSuitCase: { type: Object, required: true },
  suitcase: { type: Object as PropType<SuitCase | null>, default: null },
  viewRoute: { type: String, required: true },
  writeAuth: { type: Boolean, default: true },
})
const emit = defineEmits(['on-submit', 'close'])

const refDelModal = ref()
const refConfirmModal = ref()
const refAlertModal = ref()

const validated = ref(false)
const form = reactive<SuitCase>({
  pk: null,
  issue_project: null,
  sort: '',
  level: '',
  related_case: null,
  court: '',
  other_agency: '',
  case_number: '',
  case_name: '',
  plaintiff: '',
  plaintiff_attorney: '',
  plaintiff_case_price: null,
  defendant: '',
  defendant_attorney: '',
  defendant_case_price: null,
  related_debtor: '',
  case_start_date: null,
  case_end_date: null,
  summary: '',
})

const formsCheck = computed(() => {
  if (props.suitcase) {
    const a = form.issue_project === props.suitcase.issue_project
    const b = form.sort === props.suitcase.sort
    const c = form.level === props.suitcase.level
    const d = form.related_case === props.suitcase.related_case
    const e = form.court === props.suitcase.court
    const f = form.other_agency === props.suitcase.other_agency
    const g = form.case_number === props.suitcase.case_number
    const h = form.case_name === props.suitcase.case_name
    const i = form.plaintiff === props.suitcase.plaintiff
    const j = form.plaintiff_attorney === props.suitcase.plaintiff_attorney
    const k = form.plaintiff_case_price === props.suitcase.plaintiff_case_price
    const l = form.defendant === props.suitcase.defendant
    const m = form.defendant_attorney === props.suitcase.defendant_attorney
    const n = form.defendant_case_price === props.suitcase.defendant_case_price
    const o = form.related_debtor === props.suitcase.related_debtor
    const p = form.case_start_date === props.suitcase.case_start_date
    const q = form.case_end_date === props.suitcase.case_end_date
    const r = form.summary === props.suitcase.summary

    const group1 = a && b && c && d && e && f && g && h && i
    const group2 = j && k && l && m && n && o && p && q && r
    return group1 && group2
  } else return false
})

const [route, router] = [useRoute(), useRouter()]
const btnClass = computed(() => (route.params.caseId ? 'success' : 'primary'))

const onSubmit = (event: Event) => {
  if (props.writeAuth) {
    const el = event.currentTarget as HTMLFormElement
    if (!el.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

      validated.value = true
    } else refConfirmModal.value.callModal()
  } else refAlertModal.value.callModal()
}

const modalAction = () => {
  emit('on-submit', { ...form })
  validated.value = false
  refConfirmModal.value.close()
}

const dataSetup = () => {
  if (props.suitcase) {
    form.pk = props.suitcase.pk
    form.issue_project = props.suitcase.issue_project
    form.sort = props.suitcase.sort
    form.level = props.suitcase.level
    form.related_case = props.suitcase.related_case
    form.court = props.suitcase.court
    form.other_agency = props.suitcase.other_agency
    form.case_number = props.suitcase.case_number
    form.case_name = props.suitcase.case_name
    form.plaintiff = props.suitcase.plaintiff
    form.plaintiff_attorney = props.suitcase.plaintiff_attorney
    form.plaintiff_case_price = props.suitcase.plaintiff_case_price
    form.defendant = props.suitcase.defendant
    form.defendant_attorney = props.suitcase.defendant_attorney
    form.defendant_case_price = props.suitcase.defendant_case_price
    form.related_debtor = props.suitcase.related_debtor
    form.case_start_date = props.suitcase.case_start_date
    form.case_end_date = props.suitcase.case_end_date
    form.summary = props.suitcase.summary
  }
}

onMounted(() => dataSetup())
onUpdated(() => dataSetup())
</script>

<template>
  <CRow class="mt-5">
    <CCol>
      <h5>
        {{ sortName }}
        <v-icon icon="mdi-chevron-double-right" size="xs" />
        소송 사건
      </h5>
    </CCol>
  </CRow>

  <v-divider />

  <CForm
    enctype="multipart/form-data"
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="onSubmit"
  >
    <CRow class="mb-3">
      <CFormLabel for="sort" class="col-md-2 col-form-label required">유형</CFormLabel>
      <CCol md="4">
        <CFormSelect id="sort" v-model="form.sort" required>
          <option value="">사건유형 선택</option>
          <option value="1">민사</option>
          <option value="2">형사</option>
          <option value="3">행정</option>
          <option value="4">신청</option>
          <option value="5">집행</option>
        </CFormSelect>
      </CCol>

      <CFormLabel for="level" class="col-md-2 col-form-label required">심급</CFormLabel>
      <CCol md="4">
        <CFormSelect id="level" v-model="form.level" required>
          <option value="">사건심급 선택</option>
          <option v-if="!form.sort || form.sort <= '3'" value="1">1심</option>
          <option v-if="!form.sort || form.sort <= '3'" value="2">2심</option>
          <option v-if="!form.sort || form.sort <= '3'" value="3">3심</option>
          <option v-if="!form.sort || form.sort === '2'" value="4">고소/수사</option>
          <option v-if="!form.sort || form.sort === '4'" value="5">신청</option>
          <option v-if="!form.sort || form.sort === '4'" value="6">항고/이의</option>
          <option v-if="!form.sort || form.sort === '5'" value="7">압류/추심</option>
          <option v-if="!form.sort || form.sort === '5'" value="8">정지/이의</option>
        </CFormSelect>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="related_case" class="col-md-2 col-form-label"> 관련사건</CFormLabel>
      <CCol md="4">
        <MultiSelect
          v-model="form.related_case"
          mode="single"
          :options="getSuitCase"
          placeholder="관련 사건"
        />
        <small class="text-blue-grey-lighten-2">
          본안 사건인 경우 원심(1심) 사건, 신청/집행 사건인 경우 관련 본안 사건 지정
        </small>
      </CCol>
      <CFormLabel for="related_debtor" class="col-md-2 col-form-label"> 제3채무자</CFormLabel>
      <CCol md="4">
        <CFormInput
          id="related_debtor"
          v-model="form.related_debtor"
          maxlength="30"
          placeholder="제3채무자"
        />
        <small class="text-blue-grey-lighten-2">
          압류/가압류 등 집행(압류/추심) 사건에서 제3채무자가 있는 경우 기재
        </small>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="related_case" class="col-md-2 col-form-label required"> 법원명</CFormLabel>
      <CCol md="4">
        <MultiSelect
          v-model="form.court"
          mode="single"
          :options="courtChoices"
          placeholder="법원 선택"
          :attrs="form.court || form.other_agency ? {} : { required: true }"
        />
      </CCol>

      <CFormLabel for="other_agency" class="col-md-2 col-form-label"> 기타 처리기관</CFormLabel>
      <CCol md="4">
        <CFormInput
          id="other_agency"
          v-model="form.other_agency"
          maxlength="30"
          placeholder="법원 외 사건 처리기관"
        />
        <small class="text-blue-grey-lighten-2">
          사건 유형이 기소 전 형사 사건인 경우 해당 수사기관을 기재
        </small>
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="case_number" class="col-md-2 col-form-label required"> 사건번호</CFormLabel>
      <CCol md="4">
        <CFormInput
          id="case_number"
          v-model="form.case_number"
          maxlength="20"
          placeholder="사건번호"
          required
        />
      </CCol>

      <CFormLabel for="case_name" class="col-md-2 col-form-label required"> 사건명</CFormLabel>
      <CCol md="4">
        <CFormInput
          id="case_name"
          v-model="form.case_name"
          maxlength="30"
          placeholder="사건명"
          required
        />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="plaintiff" class="col-md-2 col-form-label required">
        원고(채권자)
      </CFormLabel>
      <CCol md="4">
        <CFormInput
          id="plaintiff"
          v-model="form.plaintiff"
          maxlength="30"
          placeholder="원고(채권자)"
          required
        />
      </CCol>

      <CFormLabel for="defendant" class="col-md-2 col-form-label required">
        피고(채무자)
      </CFormLabel>
      <CCol md="4">
        <CFormInput
          id="defendant"
          v-model="form.defendant"
          maxlength="30"
          placeholder="피고(채무자)"
          required
        />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="plaintiff_attorney" class="col-md-2 col-form-label">
        원고측 대리인
      </CFormLabel>
      <CCol md="4">
        <CFormInput
          id="plaintiff_attorney"
          v-model="form.plaintiff_attorney"
          maxlength="50"
          placeholder="원고측 대리인"
        />
      </CCol>

      <CFormLabel for="defendant_attorney" class="col-md-2 col-form-label">
        피고측 대리인
      </CFormLabel>
      <CCol md="4">
        <CFormInput
          id="defendant_attorney"
          v-model="form.defendant_attorney"
          maxlength="50"
          placeholder="피고측 대리인"
        />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="plaintiff_attorney" class="col-md-2 col-form-label"> 원고 소가</CFormLabel>
      <CCol md="4">
        <CFormInput
          id="plaintiff_case_price"
          v-model.number="form.plaintiff_case_price"
          type="number"
          min="0"
          placeholder="원고 소가"
        />
      </CCol>

      <CFormLabel for="defendant_attorney" class="col-md-2 col-form-label"> 피고 소가</CFormLabel>
      <CCol md="4">
        <CFormInput
          id="defendant_case_price"
          v-model.number="form.defendant_case_price"
          type="number"
          min="0"
          placeholder="피고 소가"
        />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="case_start_date" class="col-md-2 col-form-label required">
        사건개시일
      </CFormLabel>
      <CCol md="4">
        <DatePicker
          id="case_start_date"
          v-model="form.case_start_date"
          placeholder="사건개시일"
          required
        />
      </CCol>

      <CFormLabel for="case_end_date" class="col-md-2 col-form-label"> 사건종결일</CFormLabel>
      <CCol md="4">
        <DatePicker id="case_end_date" v-model="form.case_end_date" placeholder="사건종결일" />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel for="summary" class="col-md-2 col-form-label"> 개요 및 경과</CFormLabel>
      <CCol>
        <CFormTextarea id="summary" v-model="form.summary" rows="4" placeholder="개요 및 경과" />
      </CCol>
    </CRow>

    <CRow>
      <CCol class="text-right">
        <v-btn color="light" @click="router.push({ name: `${viewRoute}` })"> 목록으로</v-btn>
        <v-btn v-if="route.params.caseId" color="light" @click="router.go(-1)"> 뒤로</v-btn>
        <v-btn :color="btnClass" type="submit" :disabled="formsCheck"> 저장하기</v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> {{ viewRoute }}</template>
    <template #default>현재 삭제 기능이 구현되지 않았습니다.</template>
    <template #footer>
      <v-btn color="warning" disabled>삭제</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header> {{ viewRoute }}</template>
    <template #default> {{ viewRoute }} 저장을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn :color="btnClass" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
