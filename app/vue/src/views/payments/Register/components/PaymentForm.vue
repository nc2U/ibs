<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePayment } from '@/store/pinia/payment'
import { useProCash } from '@/store/pinia/proCash'
import { getToday, diffDate } from '@/utils/baseMixins'
import { isValidate } from '@/utils/helper'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_payment } from '@/utils/pageAuth'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  contract: { type: Object, default: null },
  payment: { type: Object, default: null },
})

const emit = defineEmits(['on-submit', 'on-delete', 'close'])

const refAlertModal = ref()
const delConfirmModal = ref()
const cngConfirmModal = ref()

const validated = ref(false)

const removeCont = ref(false)
const form = reactive({
  project: null, // hidden -> index 에서 처리
  sort: 1, // hidden -> always
  project_account_d2: null as null | number, // hidden
  project_account_d3: null as null | number, // hidden
  contract: null, //  hidden -> 예외 및 신규 매칭 시 코드 확인
  content: '', // hidden
  installment_order: null,
  trader: '',
  bank_account: null,
  income: null,
  note: '',
  deal_date: getToday(),
})

const formsCheck = computed(() => {
  if (props.payment) {
    const io = props.payment.installment_order ? props.payment.installment_order.pk : null
    const a = form.installment_order === io
    const b = form.trader === props.payment.trader
    const c = form.bank_account === props.payment.bank_account.pk
    const d = form.income === props.payment.income
    const e = form.note === props.payment.note
    const f = form.deal_date === props.payment.deal_date
    const g = removeCont.value === false

    return a && b && c && d && e && f && g
  } else return false
})

const allowedPeriod = computed(() => {
  return props.payment ? useAccount().superAuth || diffDate(props.payment.deal_date) <= 90 : true
})

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)

const proCashStore = useProCash()
const allProBankAccountList = computed(() => proCashStore.allProBankAccountList)

const onSubmit = (event: Event) => {
  if (write_payment.value) {
    if (allowedPeriod.value) {
      if (isValidate(event)) {
        validated.value = true
      } else {
        if (!props.payment) modalAction()
        else {
          if (removeCont.value) {
            cngConfirmModal.value.callModal()
          } else modalAction()
        }
      }
    } else
      refAlertModal.value.callModal(
        null,
        '수납일로부터 90일이 경과한 건은 수정할 수 없습니다. 관리자에게 문의바랍니다.',
      )
  } else refAlertModal.value.callModal()
}

const modalAction = () => emit('on-submit', { rmCont: removeCont.value, ...form })

const deleteConfirm = () => {
  if (write_payment.value) {
    if (allowedPeriod.value) {
      delConfirmModal.value.callModal()
    } else
      refAlertModal.value.callModal(
        null,
        '수납일로부터 90일이 경과한 건은 삭제할 수 없습니다. 관리자에게 문의바랍니다.',
      )
  } else refAlertModal.value.callModal()
}

const onDelete = () => {
  emit('on-delete')
  emit('close')
}

const formDataSet = () => {
  if (props.payment) {
    form.installment_order = props.payment.installment_order
      ? props.payment.installment_order.pk
      : null
    form.trader = props.payment.trader
    form.bank_account = props.payment.bank_account.pk
    form.income = props.payment.income
    form.note = props.payment.note
    form.deal_date = props.payment.deal_date
  }
  form.project_account_d2 = props.contract.order_group_desc.sort
  form.project_account_d3 = props.contract.order_group_desc.sort === '1' ? 1 : 4
  form.contract = props.contract.pk
  form.content = `${props.contract.contractor.name}[${props.contract.serial_number}] 대금납부`
}

onBeforeMount(() => formDataSet())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 수납일자</CFormLabel>
            <CCol sm="8">
              <DatePicker v-model="form.deal_date" required placeholder="거래일자" />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">납부회차</CFormLabel>
            <CCol sm="8">
              <CFormSelect v-model="form.installment_order" required>
                <option value="">---------</option>
                <option v-for="po in payOrderList" :key="po.pk as number" :value="po.pk">
                  {{ po.__str__ }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>
        </CCol>
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">수납계좌</CFormLabel>
            <CCol sm="8">
              <CFormSelect v-model="form.bank_account" required>
                <option value="">---------</option>
                <option v-for="pb in allProBankAccountList" :key="pb.pk as number" :value="pb.pk">
                  {{ pb.alias_name }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">수납금액</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model.number="form.income"
                type="number"
                min="0"
                placeholder="수납금액"
                required
              />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">입금자명</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model="form.trader"
                maxlength="20"
                required
                placeholder="입금자명 (필히 계좌 입금자 기재)"
              />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol>
          <CRow>
            <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
            <CCol sm="10">
              <CFormTextarea v-model="form.note" placeholder="기타 특이사항" />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow v-if="payment">
        <CCol>
          <CRow>
            <CFormLabel class="col-sm-2 col-form-label"></CFormLabel>
            <CCol sm="10">
              <CFormCheck
                :id="`cont-change`"
                v-model="removeCont"
                label="계약건 변경 (현재 계약 건 귀속에서 해제 되며 전체 수납 내역에서 재 지정요)"
              />
            </CCol>
          </CRow>
        </CCol>
      </CRow>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" size="small" :color="btnLight" @click="$emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          type="submit"
          size="small"
          :color="payment ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="payment" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="cngConfirmModal">
    <template #header> 건별 수납 정보 - [변경]</template>
    <template #default>
      이 수납 건에 대한 현재 계약 건 귀속을 해제합니다. <br /><br />
      해당 건별 수납 정보 계약 건 귀속 해제(변경)를 진행하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="success" size="small" @click="modalAction">변경</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="delConfirmModal">
    <template #header> 건별 수납 정보 - [삭제]</template>
    <template #default>
      삭제 후 복구할 수 없습니다. 해당 건별 수납 정보 삭제를 진행하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="onDelete">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
