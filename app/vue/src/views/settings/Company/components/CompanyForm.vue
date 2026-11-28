<script lang="ts" setup>
import { computed, reactive, ref, watch, type PropType } from 'vue'
import type { Company } from '@/store/types/settings'
import { useAccount } from '@/store/pinia/account'
import { isValidate } from '@/utils/helper'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: Object as PropType<Company | null>, default: null },
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['on-submit', 'on-delete', 'reset-form'])

const account = useAccount()
const canManageCompany = computed(() => Boolean(account.superAuth))

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)
const refConfirmModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refPostCode = ref<InstanceType<typeof DaumPostcode> | null>(null)
const address2 = ref<{ $el?: HTMLElement } | null>(null)

const validated = ref(false)
const form = reactive({
  pk: null as number | null,
  name: '',
  en_name: '',
  short_name: '',
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
  phone: '',
  fax: '',
  email: '',
  is_default: false,
})

const addressCallback = (data: AddressData) => {
  const { formNum, zipcode, address1, address3 } = callAddress(data)
  if (formNum === 1) {
    form.zipcode = zipcode
    form.address1 = address1
    form.address2 = ''
    form.address3 = address3
    const el = address2.value?.$el
    const inputEl =
      el?.tagName === 'INPUT'
        ? el
        : (el?.querySelector?.('input') ?? (el?.nextElementSibling as HTMLElement | null))
    inputEl?.focus?.()
  }
}

const onSubmit = (event: Event) => {
  if (!canManageCompany.value) {
    refAlertModal.value?.callModal()
    return
  }
  if (isValidate(event)) {
    validated.value = true
    return
  }
  refConfirmModal.value?.callModal()
}

const modalAction = () => {
  if (props.submitting) return
  emit('on-submit', {
    ...form,
    es_date: form.es_date || null,
    op_date: form.op_date || null,
  } as Company)
  validated.value = false
  refConfirmModal.value?.close()
}

const deleteCompany = () => {
  if (canManageCompany.value) refDelModal.value?.callModal()
  else refAlertModal.value?.callModal()
}

const modalActionDelete = () => {
  if (props.submitting) return
  if (props.company?.pk) {
    emit('on-delete', props.company.pk)
  }
  refDelModal.value?.close()
}

const confirmText = computed(() => (props.company ? '변경' : '등록'))
const btnClass = computed(() => (props.company ? 'success' : 'primary'))

const norm = (val?: string | null) => val || ''

const formsCheck = computed(() => {
  if (!props.company) return false
  return (
    form.name === norm(props.company.name) &&
    form.en_name === norm(props.company.en_name) &&
    form.short_name === norm(props.company.short_name) &&
    form.ceo === norm(props.company.ceo) &&
    form.tax_number === norm(props.company.tax_number) &&
    form.org_number === norm(props.company.org_number) &&
    form.business_cond === norm(props.company.business_cond) &&
    form.business_even === norm(props.company.business_even) &&
    form.es_date === norm(props.company.es_date) &&
    form.op_date === norm(props.company.op_date) &&
    form.zipcode === norm(props.company.zipcode) &&
    form.address1 === norm(props.company.address1) &&
    form.address2 === norm(props.company.address2) &&
    form.address3 === norm(props.company.address3) &&
    form.phone === norm(props.company.phone) &&
    form.fax === norm(props.company.fax) &&
    form.email === norm(props.company.email) &&
    form.is_default === Boolean(props.company.is_default)
  )
})

const formDataSetup = () => {
  validated.value = false
  if (props.company) {
    form.pk = props.company.pk
    form.name = norm(props.company.name)
    form.en_name = norm(props.company.en_name)
    form.short_name = norm(props.company.short_name)
    form.ceo = norm(props.company.ceo)
    form.tax_number = norm(props.company.tax_number)
    form.org_number = norm(props.company.org_number)
    form.business_cond = norm(props.company.business_cond)
    form.business_even = norm(props.company.business_even)
    form.es_date = norm(props.company.es_date)
    form.op_date = norm(props.company.op_date)
    form.zipcode = norm(props.company.zipcode)
    form.address1 = norm(props.company.address1)
    form.address2 = norm(props.company.address2)
    form.address3 = norm(props.company.address3)
    form.phone = norm(props.company.phone)
    form.fax = norm(props.company.fax)
    form.email = norm(props.company.email)
    form.is_default = Boolean(props.company.is_default)
  } else {
    form.pk = null
    form.name = ''
    form.en_name = ''
    form.short_name = ''
    form.ceo = ''
    form.tax_number = ''
    form.org_number = ''
    form.business_cond = ''
    form.business_even = ''
    form.es_date = ''
    form.op_date = ''
    form.zipcode = ''
    form.address1 = ''
    form.address2 = ''
    form.address3 = ''
    form.phone = ''
    form.fax = ''
    form.email = ''
    form.is_default = false
  }
}
defineExpose({ formDataSetup })

watch(
  () => props.company,
  () => formDataSetup(),
  { immediate: true, deep: true },
)
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CCardBody class="p-3 p-md-4">
      <CRow class="mb-3">
        <CFormLabel for="name" class="col-md-2 col-form-label required">회사명</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="name"
            v-model="form.name"
            type="text"
            placeholder="회사명을 입력하세요"
            maxlength="30"
            required
          />
          <CFormFeedback invalid>회사명을 입력하세요.</CFormFeedback>
        </CCol>

        <CFormLabel for="ceo" class="col-md-2 col-form-label required">대표자명</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="ceo"
            v-model="form.ceo"
            type="text"
            placeholder="대표자명을 입력하세요"
            maxlength="20"
            required
          />
          <CFormFeedback invalid>대표자명을 입력하세요.</CFormFeedback>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="en_name" class="col-md-2 col-form-label">영문 회사명</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="en_name"
            v-model="form.en_name"
            type="text"
            placeholder="영문 회사명을 입력하세요"
            maxlength="50"
          />
        </CCol>

        <CFormLabel for="short_name" class="col-md-2 col-form-label">회사 약칭</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="short_name"
            v-model="form.short_name"
            type="text"
            placeholder="공문 등에 표기될 약칭 (예: 대영IBS)"
            maxlength="20"
          />
          <small class="text-muted">
            공문서 번호 접두사 등으로 활용됩니다. (미입력 시 회사명에서 자동 추출)
          </small>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="tax_number" class="col-md-2 col-form-label required">
          사업자등록번호
        </CFormLabel>
        <CCol md="4">
          <input
            id="tax_number"
            v-model="form.tax_number"
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

        <CFormLabel for="org_number" class="col-md-2 col-form-label required">
          법인등록번호
        </CFormLabel>
        <CCol md="4">
          <input
            id="org_number"
            v-model="form.org_number"
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
        <CFormLabel for="business_cond" class="col-md-2 col-form-label">업태</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="business_cond"
            v-model="form.business_cond"
            type="text"
            placeholder="업태를 입력하세요"
            maxlength="20"
          />
        </CCol>

        <CFormLabel for="business_even" class="col-md-2 col-form-label">종목</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="business_even"
            v-model="form.business_even"
            type="text"
            placeholder="종목을 입력하세요"
            maxlength="20"
          />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="es_date" class="col-md-2 col-form-label">설립일자</CFormLabel>
        <CCol md="4">
          <DatePicker
            id="es_date"
            v-model="form.es_date"
            maxlength="10"
            placeholder="설립일자를 입력하세요"
          />
        </CCol>

        <CFormLabel for="op_date" class="col-md-2 col-form-label">개업일자</CFormLabel>
        <CCol md="4">
          <DatePicker
            id="op_date"
            v-model="form.op_date"
            maxlength="10"
            placeholder="개업일자를 입력하세요"
          />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="phone" class="col-md-2 col-form-label">대표전화</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="phone"
            v-model="form.phone"
            type="text"
            placeholder="대표전화번호"
            maxlength="15"
          />
        </CCol>

        <CFormLabel for="fax" class="col-md-2 col-form-label">대표팩스</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="fax"
            v-model="form.fax"
            type="text"
            placeholder="대표팩스번호"
            maxlength="15"
          />
        </CCol>
      </CRow>

      <CRow class="mb-3 align-items-center">
        <CFormLabel for="email" class="col-md-2 col-form-label">대표이메일</CFormLabel>
        <CCol md="4">
          <CFormInput
            id="email"
            v-model="form.email"
            type="email"
            placeholder="대표이메일 주소"
          />
          <CFormFeedback invalid>올바른 이메일 형식을 입력하세요.</CFormFeedback>
        </CCol>

        <CFormLabel for="is_default" class="col-md-2 col-form-label">메인 회사 여부</CFormLabel>
        <CCol md="4">
          <CFormCheck
            id="is_default"
            v-model="form.is_default"
            label="시스템 기본(메인) 회사로 지정"
          />
        </CCol>
      </CRow>

      <v-divider />

      <CRow>
        <CFormLabel for="zipcode" class="col-md-2 col-form-label">회사주소</CFormLabel>
        <CCol md="4" xl="2" class="mb-3">
          <CInputGroup>
            <CInputGroupText style="cursor: pointer" @click="refPostCode?.initiate()">
              우편번호
            </CInputGroupText>
            <CFormInput
              id="zipcode"
              v-model="form.zipcode"
              type="text"
              placeholder="우편번호"
              maxlength="5"
              @focus="refPostCode?.initiate()"
            />
          </CInputGroup>
        </CCol>

        <CCol md="6" xl="4" class="mb-3">
          <CFormInput
            id="address1"
            v-model="form.address1"
            type="text"
            placeholder="회사주소를 입력하세요"
            maxlength="35"
            @focus="refPostCode?.initiate()"
          />
        </CCol>
        <CCol xs="2" class="d-none d-sm-block d-lg-none"></CCol>
        <CCol md="5" lg="6" xl="2" class="mb-3">
          <CFormInput
            id="address2"
            ref="address2"
            v-model="form.address2"
            type="text"
            placeholder="상세주소를 입력하세요"
            maxlength="50"
          />
        </CCol>
        <CCol md="5" lg="4" xl="2" class="mb-3">
          <CFormInput
            id="address3"
            v-model="form.address3"
            type="text"
            placeholder="나머지 주소를 입력하세요"
            maxlength="30"
          />
        </CCol>
      </CRow>
    </CCardBody>

    <CCardFooter class="text-end">
      <v-btn type="submit" :color="btnClass" :disabled="formsCheck || submitting" :loading="submitting">
        <v-icon icon="mdi-check-circle-outline" size="small" class="me-1" />
        저장
      </v-btn>
      <v-btn
        v-if="company && canManageCompany"
        type="button"
        color="warning"
        class="ms-2"
        :disabled="submitting"
        @click="deleteCompany"
      >
        삭제
      </v-btn>
      <v-btn
        type="button"
        color="light"
        class="ms-2"
        :disabled="submitting"
        flat
        @click="emit('reset-form')"
      >
        취소
      </v-btn>
    </CCardFooter>
  </CForm>

  <DaumPostcode ref="refPostCode" @address-callback="addressCallback" />

  <ConfirmModal ref="refDelModal">
    <template #header>회사정보 삭제 확인</template>
    <template #default>
      <p class="mb-0">
        정말로 <strong>[{{ company?.name }}]</strong> 회사 정보를 삭제하시겠습니까?
      </p>
      <small class="text-danger">(관련된 하위 데이터가 함께 영향을 받을 수 있습니다)</small>
    </template>
    <template #footer>
      <v-btn color="danger" size="small" :disabled="submitting" @click="modalActionDelete">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refConfirmModal" checked>
    <template #header>회사정보</template>
    <template #default> 회사정보 {{ confirmText }}을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn :color="btnClass" size="small" :disabled="submitting" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
