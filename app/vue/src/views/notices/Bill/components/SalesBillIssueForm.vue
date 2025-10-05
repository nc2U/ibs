<script lang="ts" setup>
import { ref, reactive, computed, watch, onMounted, onUpdated, type PropType } from 'vue'
import { usePayment } from '@/store/pinia/payment'
import { type SalesBillIssue } from '@/store/types/notice'
import { write_notice } from '@/utils/pageAuth'
import { isValidate } from '@/utils/helper'
import { getToday } from '@/utils/baseMixins'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  project: { type: Number, default: null },
  billIssue: { type: Object as PropType<SalesBillIssue>, default: null },
})

const emit = defineEmits(['on-submit', 'get-now-order', 'set-pub-date'])

const address2 = ref()
const postCode = ref()
const refConfirmModal = ref()
const refAlertModal = ref()

const visible = ref(false)
const validated = ref(false)

const published_date = ref(getToday()) // 발행일자
watch(published_date, val => emit('set-pub-date', val))

const form = reactive<SalesBillIssue & { now_due_date: string | null }>({
  pk: null,
  project: null,
  now_payment_order: null,
  now_due_date: null, // 납부기한
  host_name: '',
  host_tel: '',
  agency: '',
  agency_tel: '',
  bank_account1: '',
  bank_number1: '',
  bank_host1: '',
  bank_account2: '',
  bank_number2: '',
  bank_host2: '',
  zipcode: '',
  address1: '',
  address2: '',
  address3: '',
  title: '',
  content: '',
})

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)
const payOrder = computed(() => paymentStore.payOrder)

watch(payOrder, val => {
  if (val?.pay_due_date) form.now_due_date = val.pay_due_date
  else form.now_due_date = null
})

const confirmText = computed(() => (props.billIssue ? '업데이트' : '신규등록'))
const btnClass = computed(() => (props.billIssue ? 'success' : 'primary'))

const formsCheck = computed(() => {
  if (props.billIssue) {
    const a = form.now_payment_order === props.billIssue.now_payment_order
    const b = form.now_due_date === payOrder.value?.pay_due_date
    const c = form.host_name === props.billIssue.host_name
    const d = form.host_tel === props.billIssue.host_tel
    const e = form.agency === props.billIssue.agency
    const f = form.agency_tel === props.billIssue.agency_tel
    const g = form.bank_account1 === props.billIssue.bank_account1
    const h = form.bank_number1 === props.billIssue.bank_number1
    const i = form.bank_host1 === props.billIssue.bank_host1
    const j = form.bank_account2 === props.billIssue.bank_account2
    const k = form.bank_number2 === props.billIssue.bank_number2
    const l = form.bank_host2 === props.billIssue.bank_host2
    const m = form.zipcode === props.billIssue.zipcode
    const n = form.address1 === props.billIssue.address1
    const o = form.address2 === props.billIssue.address2
    const p = form.address3 === props.billIssue.address3
    const q = form.title === props.billIssue.title
    const r = form.content === props.billIssue.content
    const sky = a && b && c && d && e && f && g && h && i
    const land = j && k && l && m && n && o && p && q && r
    return sky && land
  } else return false
})

const onSubmit = (event: Event) => {
  if (write_notice.value) {
    if (isValidate(event)) {
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

const addressCallback = (data: AddressData) => {
  const { formNum, zipcode, address1, address3 } = callAddress(data)
  if (formNum === 1) {
    form.zipcode = zipcode
    form.address1 = address1
    form.address2 = ''
    form.address3 = address3
    address2.value.$el.nextElementSibling.focus()
  }
}

const formDataReset = () => {
  form.pk = null
  form.project = props.project
  form.now_payment_order = null
  form.host_name = ''
  form.host_tel = ''
  form.agency = ''
  form.agency_tel = ''
  form.bank_account1 = ''
  form.bank_number1 = ''
  form.bank_host1 = ''
  form.bank_account2 = ''
  form.bank_number2 = ''
  form.bank_host2 = ''
  form.zipcode = ''
  form.address1 = ''
  form.address2 = ''
  form.address3 = ''
  form.title = ''
  form.content = ''
}

const formDataSetup = () => {
  if (props.billIssue) {
    const val = props.billIssue
    emit('get-now-order', val.now_payment_order)
    form.pk = val.pk
    form.project = val.project
    form.now_payment_order = val.now_payment_order
    form.host_name = val.host_name
    form.host_tel = val.host_tel
    form.agency = val.agency
    form.agency_tel = val.agency_tel
    form.bank_account1 = val.bank_account1
    form.bank_number1 = val.bank_number1
    form.bank_host1 = val.bank_host1
    form.bank_account2 = val.bank_account2
    form.bank_number2 = val.bank_number2
    form.bank_host2 = val.bank_host2
    form.zipcode = val.zipcode
    form.address1 = val.address1
    form.address2 = val.address2
    form.address3 = val.address3
    form.title = val.title
    form.content = val.content
  } else formDataReset()
}

onMounted(() => formDataSetup())
onUpdated(() => formDataSetup())
</script>

<template>
  <CAlert color="info">
    <CRow>
      <CCol xs="6" sm="7" md="8" lg="9" xl="10">
        <CIcon name="cibAddthis" />
        <strong class="title"> 수납 고지서 발행</strong>
      </CCol>
      <CCol>
        <CFormSwitch
          id="formSwitch"
          label="고지서 관련정보 설정"
          :model-value="visible"
          @click="visible = !visible"
        />
      </CCol>
    </CRow>
  </CAlert>

  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CRow class="mb-1">
      <CCol sm="4" md="2" xl="1">
        <CFormLabel for="" class="col-form-label">발행일자</CFormLabel>
      </CCol>
      <CCol sm="8" md="4" xl="2">
        <DatePicker v-model="published_date" placeholder="발행일자" maxlength="10" required />
      </CCol>
    </CRow>

    <CCollapse :visible="visible">
      <CRow class="mb-1">
        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">발행회차</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="2">
          <CFormSelect v-model="form.now_payment_order" placeholder="발행회차" required>
            <option value="">--------</option>
            <option v-for="po in payOrderList" :key="po.pk as number" :value="po.pk">
              {{ po.__str__ }}
            </option>
          </CFormSelect>
        </CCol>

        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">당회 납부기한</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="2">
          <DatePicker
            v-model="form.now_due_date"
            placeholder="당회 납부기한"
            maxlength="10"
            :required="false"
          />
        </CCol>
      </CRow>

      <CRow class="mb-1">
        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">시행자명</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="2">
          <CFormInput v-model="form.host_name" placeholder="시행자명" maxlength="20" required />
        </CCol>

        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">시행자 전화</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="2">
          <input
            v-model="form.host_tel"
            v-maska
            data-maska="['###-###-####', '###-####-####']"
            type="text"
            class="form-control"
            placeholder="시행자 전화"
            maxlength="13"
            required
          />
        </CCol>

        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">대행사명</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="2">
          <CFormInput v-model="form.agency" placeholder="대행사명" maxlength="20" />
        </CCol>

        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">대행사 전화</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="2">
          <input
            v-model="form.agency_tel"
            v-maska
            data-maska="['###-###-####', '###-####-####']"
            type="text"
            class="form-control"
            placeholder="대행사 전화"
            maxlength="13"
          />
        </CCol>
      </CRow>

      <CRow class="mb-1">
        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">수납은행[1]</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="3">
          <CFormInput
            v-model="form.bank_account1"
            placeholder="수납은행[1]"
            maxlength="20"
            required
          />
        </CCol>

        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">계좌번호[1]</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="3">
          <CFormInput
            v-model="form.bank_number1"
            placeholder="계좌번호[1]"
            maxlength="25"
            required
          />
        </CCol>

        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">예금주[1]</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="3">
          <CFormInput v-model="form.bank_host1" placeholder="예금주[1]" maxlength="20" required />
        </CCol>
      </CRow>

      <CRow class="mb-1">
        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">수납은행[2]</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="3">
          <CFormInput v-model="form.bank_account2" placeholder="수납은행[2]" maxlength="20" />
        </CCol>

        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">계좌번호[2]</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="3">
          <CFormInput v-model="form.bank_number2" placeholder="계좌번호[2]" maxlength="25" />
        </CCol>

        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">예금주[2]</CFormLabel>
        </CCol>
        <CCol sm="8" md="4" xl="3">
          <CFormInput v-model="form.bank_host2" placeholder="예금주[2]" maxlength="20" />
        </CCol>
      </CRow>

      <CRow class="mb-1">
        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">시행자 주소</CFormLabel>
        </CCol>

        <CCol xs="12" sm="8" md="4" xl="2" class="mb-1">
          <CInputGroup>
            <CInputGroupText @click="postCode.initiate()"> 우편번호</CInputGroupText>
            <CFormInput
              v-model="form.zipcode"
              v-maska
              data-maska="#####"
              type="text"
              placeholder="우편번호"
              maxlength="5"
              required
              @focus="postCode.initiate()"
            />
            <!--            <CFormFeedback invalid>우편번호를 입력하세요.</CFormFeedback>-->
          </CInputGroup>
        </CCol>

        <CCol class="d-none d-sm-block d-md-none" sm="4" />

        <CCol sm="8" md="6" xl="4" class="mb-1">
          <CFormInput
            v-model="form.address1"
            placeholder="메인 주소"
            maxlength="35"
            required
            @click="postCode.initiate()"
          />
        </CCol>

        <CCol class="d-none d-sm-block d-md-block d-xl-none" sm="4" md="2" />

        <CCol sm="8" md="5" xl="2" class="mb-1">
          <CFormInput
            ref="address2"
            v-model="form.address2"
            placeholder="상세 주소"
            maxlngth="50"
            required
          />
        </CCol>

        <CCol class="d-none d-sm-block d-md-none" sm="4" />

        <CCol sm="8" md="5" xl="3" class="mb-1">
          <CFormInput v-model="form.address3" placeholder="참고항목" maxlength="30" required />
        </CCol>
      </CRow>

      <CRow class="mb-1">
        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">고지서 제목</CFormLabel>
        </CCol>

        <CCol sm="8" md="10" lg="12" xl="11">
          <CFormInput v-model="form.title" placeholder="고재서 제목" maxlength="80" required />
        </CCol>
        <CCol class="d-none d-md-block d-lg-none" md="6" />
      </CRow>

      <CRow class="mb-3">
        <CCol sm="4" md="2" xl="1">
          <CFormLabel for="" class="col-form-label">고지서 내용</CFormLabel>
        </CCol>
        <CCol sm="8" md="10" lg="12" xl="11">
          <CFormTextarea v-model="form.content" placeholder="고지서 내용" rows="4" />
        </CCol>
        <CCol class="d-none d-md-block d-lg-none" md="6" />
      </CRow>

      <CAlert v-if="write_notice" color="secondary" class="text-right">
        <v-btn type="submit" :color="btnClass" :disabled="!project || formsCheck">
          {{ confirmText }}
        </v-btn>
      </CAlert>
    </CCollapse>
  </CForm>

  <DaumPostcode ref="postCode" @address-callback="addressCallback" />

  <ConfirmModal ref="refConfirmModal">
    <template #header> 수납 고지서 발행 정보</template>
    <template #default> 수납 고지서 발행 정보 {{ confirmText }}을(를) 진행하시겠습니까?</template>
    <template #footer>
      <v-btn :color="btnClass" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
