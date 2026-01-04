<script lang="ts" setup>
import { ref, reactive, computed, onMounted, onUpdated, type PropType } from 'vue'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import type { ProjectBank } from '@/store/types/proLedger.ts'
import { write_project_cash } from '@/utils/pageAuth'
import { isValidate } from '@/utils/helper'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  bankAcc: { type: Object as PropType<ProjectBank>, default: () => null },
})
const emit = defineEmits(['on-bank-create', 'on-bank-update'])

const refConfirmModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = reactive<ProjectBank>({
  pk: null,
  project: null,
  bankcode: null,
  alias_name: '',
  number: '',
  holder: '',
  open_date: null,
  note: '',
  is_hide: false,
  inactive: false,
  directpay: false,
  is_imprest: false,
})

const formsCheck = computed(() => {
  if (props.bankAcc) {
    const a = form.bankcode === props.bankAcc.bankcode
    const b = form.alias_name === props.bankAcc.alias_name
    const c = form.number === props.bankAcc.number
    const d = form.holder === props.bankAcc.holder
    const e = form.open_date === props.bankAcc.open_date
    const f = form.note === props.bankAcc.note
    const g = form.is_hide === props.bankAcc.is_hide
    const h = form.inactive === props.bankAcc.inactive
    const i = form.directpay === props.bankAcc.directpay
    const j = form.is_imprest === props.bankAcc.is_imprest

    return a && b && c && d && e && f && g && h && i && j
  } else return false
})

const comLedgerStore = useComLedger()
const bankCodeList = computed(() => comLedgerStore.bankCodeList)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_project_cash.value) {
      refConfirmModal.value.callModal()
    } else refAlertModal.value.callModal()
    validated.value = false
  }
}

const onBankAccSubmit = () => {
  if (props.bankAcc) emit('on-bank-update', { ...form })
  else emit('on-bank-create', { ...form })
  refConfirmModal.value.close()
  formDataReset()
}

const formDataSetup = () => {
  if (props.bankAcc) {
    form.pk = props.bankAcc.pk
    form.project = props.bankAcc.project
    form.bankcode = props.bankAcc.bankcode
    form.alias_name = props.bankAcc.alias_name
    form.number = props.bankAcc.number
    form.holder = props.bankAcc.holder
    form.open_date = props.bankAcc.open_date
    form.note = props.bankAcc.note
    form.is_hide = props.bankAcc.is_hide
    form.inactive = props.bankAcc.inactive
    form.directpay = props.bankAcc.directpay
    form.is_imprest = props.bankAcc.is_imprest
  }
}

const formDataReset = () => {
  form.pk = null
  form.project = null
  form.bankcode = null
  form.alias_name = ''
  form.number = ''
  form.holder = ''
  form.open_date = null
  form.note = ''
  form.is_hide = false
  form.inactive = false
  form.directpay = false
  form.is_imprest = false
}

onMounted(() => formDataSetup())
onUpdated(() => formDataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">거래은행</CFormLabel>
              <CCol sm="8">
                <CFormSelect v-model.number="form.bankcode" required>
                  <option value="">---------</option>
                  <option v-for="bank in bankCodeList" :key="bank.pk" :value="bank.pk">
                    {{ bank.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 계좌별칭</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.alias_name"
                  maxlength="20"
                  placeholder="계좌별칭"
                  required
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 계좌번호</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.number" maxlength="30" placeholder="계좌번호" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 예금주</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.holder" maxlength="20" placeholder="예금주" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">개설일자</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.open_date" maxlength="10" placeholder="개설일자" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
              <CCol sm="10">
                <CFormTextarea v-model="form.note" maxlength="50" placeholder="비고" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"></CFormLabel>
              <CCol sm="8">
                <v-switch
                  v-model="form.is_imprest"
                  label="운영비용 계좌"
                  color="success"
                  hide-details
                />
                <v-tooltip activator="parent" location="start"> 운영비용(전도금) 계좌"</v-tooltip>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"></CFormLabel>
              <CCol sm="8">
                <v-switch
                  v-model="form.directpay"
                  label="용역비 직불 계좌"
                  color="info"
                  hide-details
                />
                <v-tooltip activator="parent" location="start"> 용역비 직불 계좌</v-tooltip>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"></CFormLabel>
              <CCol sm="8">
                <v-switch
                  v-model="form.is_hide"
                  label="입출금 등록시 숨김"
                  color="indigo"
                  hide-details
                />
                <v-tooltip activator="parent" location="end">
                  입출금 등록 시 이 계좌 항목을 숨김.
                </v-tooltip>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"></CFormLabel>
              <CCol sm="8">
                <v-switch
                  v-model="form.inactive"
                  label="사용종료 계좌"
                  color="danger"
                  hide-details
                />
                <v-tooltip activator="parent" location="start">
                  해지된 계좌로 내역만 확인 가능.
                </v-tooltip>
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="12" class="text-right pt-1">
            <v-btn :color="bankAcc ? 'success' : 'primary'" type="submit" :disabled="formsCheck">
              거래계좌 정보 <span v-if="bankAcc">저장</span><span v-else>추가</span>하기
            </v-btn>
          </CCol>
        </CRow>
      </div>
    </CModalBody>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header>
      거래계좌 정보 <span v-if="bankAcc">저장</span><span v-else>추가</span>
    </template>
    <template #default>
      거래계좌 정보를 <span v-if="bankAcc">저장</span><span v-else>추가</span>하시겠습니까?
    </template>
    <template #footer>
      <v-btn :color="bankAcc ? 'success' : 'primary'" @click="onBankAccSubmit">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
