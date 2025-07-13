<script lang="ts" setup>
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_company_settings } from '@/utils/pageAuth'
import { type Company } from '@/store/types/settings'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { callAddress, type AddressData } from '@/components/DaumPostcode/address'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const emit = defineEmits(['fetch-company', 'on-submit', 'reset-form'])

const account = useAccount()

const props = defineProps({
  company: { type: Object, default: null },
})

const refDelModal = ref()
const refAlertModal = ref()
const refConfirmModal = ref()
const refPostCode = ref()

const address2 = ref()

const validated = ref(false)
const form = reactive<Company>({
  pk: null,
  name: '',
  ceo: '',
  tax_number: '',
  org_number: '',
  business_cond: '',
  business_even: '',
  es_date: '',
  op_date: '',
  zipcode: '',
  address1: '',
  address2: '',
  address3: '',
})

const addressCallback = (data: AddressData) => {
  const { formNum, zipcode, address1, address3 } = callAddress(data)
  if (formNum === 1) {
    // 입력할 데이터와 focus 폼 지정
    form.zipcode = zipcode
    form.address1 = address1
    form.address2 = ''
    form.address3 = address3
    address2.value.$el.nextElementSibling.focus()
  }
}

const onSubmit = (event: Event) => {
  if (write_company_settings.value) {
    const e = event.currentTarget as HTMLSelectElement
    if (!e.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

      validated.value = true
    } else {
      refConfirmModal.value.callModal()
    }
  } else {
    refAlertModal.value.callModal()
  }
}
const modalAction = () => {
  emit('on-submit', { ...form })
  validated.value = false
  refConfirmModal.value.close()
}

const deleteCompany = () => {
  if (account.superAuth) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const confirmText = computed(() => (props.company ? '변경' : '등록'))
const btnClass = computed(() => (props.company ? 'success' : 'primary'))

const formsCheck = computed(() => {
  if (props.company) {
    const a = form.name === props.company.name
    const b = form.ceo === props.company.ceo
    const c = form.tax_number === props.company.tax_number
    const d = form.org_number === props.company.org_number
    const e = form.business_cond === props.company.business_cond
    const f = form.business_even === props.company.business_even
    const g = form.es_date === props.company.es_date
    const h = form.op_date === props.company.op_date
    const i = form.zipcode === props.company.zipcode
    const j = form.address1 === props.company.address1
    const k = form.address2 === props.company.address2
    const l = form.address3 === props.company.address3

    return a && b && c && d && e && f && g && h && i && j && k && l
  } else return false
})

const formDataSetup = () => {
  if (props.company) {
    form.pk = props.company.pk
    form.name = props.company.name
    form.ceo = props.company.ceo
    form.tax_number = props.company.tax_number
    form.org_number = props.company.org_number
    form.business_cond = props.company.business_cond
    form.business_even = props.company.business_even
    form.es_date = props.company.es_date
    form.op_date = props.company.op_date
    form.zipcode = props.company.zipcode
    form.address1 = props.company.address1
    form.address2 = props.company.address2
    form.address3 = props.company.address3
  }
}
defineExpose({ formDataSetup })
onBeforeMount(() => formDataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CCardBody>
      <CRow class="mb-3">
        <CFormLabel for="companyName" class="col-md-2 col-form-label required"> 회사명</CFormLabel>

        <CCol md="4">
          <CFormInput
            v-model="form.name"
            id="name"
            type="text"
            placeholder="회사명을 입력하세요"
            maxlength="30"
            required
          />
          <CFormFeedback invalid>회사명을 입력하세요.</CFormFeedback>
        </CCol>

        <CFormLabel for="companyCeo" class="col-md-2 col-form-label required"> 대표자명</CFormLabel>

        <CCol md="4">
          <CFormInput
            v-model="form.ceo"
            id="ceo"
            type="text"
            placeholder="대표자명을 입력하세요"
            maxlength="20"
            required
          />
          <CFormFeedback invalid>대표자명을 입력하세요.</CFormFeedback>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="taxNumber" class="col-md-2 col-form-label required">
          사업자등록번호
        </CFormLabel>
        <CCol md="4">
          <input
            v-model="form.tax_number"
            id="tax_number"
            v-maska
            data-maska="###-##-#####"
            type="text"
            class="form-control"
            placeholder="사업자번호를 입력하세요"
            maxlength="12"
            required
          />
          <CFormFeedback invalid>사업자등록번호를 입력하세요.</CFormFeedback>
        </CCol>
        <CFormLabel for="orgNumber" class="col-md-2 col-form-label required">
          법인등록번호
        </CFormLabel>
        <CCol md="4">
          <input
            v-model="form.org_number"
            id="org_number"
            v-maska
            data-maska="######-#######"
            type="text"
            class="form-control"
            placeholder="법인등록번호를 입력하세요"
            maxlength="14"
            required
          />
          <CFormFeedback invalid>법인등록번호를 입력하세요.</CFormFeedback>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="businessCond" class="col-md-2 col-form-label required"> 업태</CFormLabel>
        <CCol md="4">
          <CFormInput
            v-model="form.business_cond"
            id="business_cond"
            type="text"
            placeholder="업태를 입력하세요"
            maxlength="20"
            required
          />
          <CFormFeedback invalid>업태를 입력하세요.</CFormFeedback>
        </CCol>
        <CFormLabel for="businessEven" class="col-md-2 col-form-label required"> 종목</CFormLabel>
        <CCol md="4">
          <CFormInput
            v-model="form.business_even"
            id="business_even"
            type="text"
            placeholder="종목을 입력하세요"
            maxlength="20"
            required
          />
          <CFormFeedback invalid>종목을 입력하세요.</CFormFeedback>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="esDate" class="col-md-2 col-form-label required"> 설립일자</CFormLabel>
        <CCol md="4">
          <DatePicker
            v-model="form.es_date"
            id="es_date"
            maxlength="10"
            placeholder="설립일자를 입력하세요"
            required
          />
          <CFormFeedback invalid>설립일자를 입력하세요.</CFormFeedback>
        </CCol>
        <CFormLabel for="opDate" class="col-md-2 col-form-label required"> 개업일자</CFormLabel>
        <CCol md="4">
          <DatePicker
            v-model="form.op_date"
            id="op_date"
            maxlength="10"
            placeholder="개업일자를 입력하세요"
            required
          />
          <CFormFeedback invalid>개업일자를 입력하세요.</CFormFeedback>
        </CCol>
      </CRow>

      <v-divider />

      <CRow>
        <CFormLabel for="zipcode" class="col-md-2 col-form-label required"> 회사주소</CFormLabel>
        <CCol md="4" xl="2" class="mb-3">
          <CInputGroup>
            <CInputGroupText @click="refPostCode.initiate()"> 우편번호</CInputGroupText>
            <CFormInput
              v-model="form.zipcode"
              id="zipcode"
              type="text"
              placeholder="우편번호"
              maxlength="5"
              required
              @focus="refPostCode.initiate()"
            />
            <CFormFeedback invalid>우편번호를 입력하세요.</CFormFeedback>
          </CInputGroup>
        </CCol>

        <CCol md="6" xl="4" class="mb-3">
          <CFormInput
            v-model="form.address1"
            id="address1"
            type="text"
            placeholder="회사주소를 입력하세요"
            maxlength="35"
            required
            @focus="refPostCode.initiate()"
          />
          <CFormFeedback invalid>회사주소를 입력하세요.</CFormFeedback>
        </CCol>
        <CCol xs="2" class="d-none d-sm-block d-lg-none"></CCol>
        <CCol md="5" lg="6" xl="2" class="mb-3">
          <CFormInput
            ref="address2"
            v-model="form.address2"
            id="address2"
            type="text"
            placeholder="상세주소를 입력하세요"
            maxlength="50"
            required
          />
          <CFormFeedback invalid>상세주소를 입력하세요.</CFormFeedback>
        </CCol>
        <CCol md="5" lg="4" xl="2" class="mb-3">
          <CFormInput
            v-model="form.address3"
            id="address3"
            type="text"
            placeholder="나머지 주소를 입력하세요"
            maxlength="30"
          />
          <CFormFeedback invalid>나머지 주소를 입력하세요.</CFormFeedback>
        </CCol>
      </CRow>
    </CCardBody>

    <CCardFooter class="text-right">
      <v-btn type="button" :color="btnLight" @click="emit('reset-form')"> 취소</v-btn>
      <v-btn v-if="company" type="button" color="warning" @click="deleteCompany"> 삭제</v-btn>
      <v-btn type="submit" :color="btnClass" :disabled="formsCheck">
        <v-icon icon="mdi mdi-check-circle-outline" size="small" />
        저장
      </v-btn>
    </CCardFooter>
  </CForm>

  <DaumPostcode ref="refPostCode" @address-callback="addressCallback" />

  <ConfirmModal ref="refDelModal">
    <template #header> 회사정보</template>
    <template #default>현재 삭제 기능이 구현되지 않았습니다.</template>
    <template #footer>
      <v-btn color="warning" size="small" disabled>삭제</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header>회사정보</template>
    <template #default> 회사정보 {{ confirmText }}을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn :color="btnClass" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
