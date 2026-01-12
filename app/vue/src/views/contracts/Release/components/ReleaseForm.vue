<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, type PropType } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_contract } from '@/utils/pageAuth'
import { isValidate } from '@/utils/helper'
import { type Contractor, type ContractRelease } from '@/store/types/contract'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  release: { type: Object as PropType<ContractRelease>, default: null },
  contractor: { type: Object as PropType<Contractor>, default: null },
})

const emit = defineEmits(['on-submit', 'close'])

const refConfirmModal = ref()
const refAlertModal = ref()

const validated = ref(false)
const form = reactive({
  pk: null as number | null,
  contractor: null as number | null,
  status: '',
  refund_amount: null as number | null,
  refund_account_bank: '',
  refund_account_number: '',
  refund_account_depositor: '',
  request_date: null as string | null,
  completion_date: null as string | null,
  note: '',
})

const formsCheck = computed(() => {
  if (props.release) {
    const a = form.status === props.release.status
    const b = !form.refund_amount || form.refund_amount === props.release.refund_amount
    const c = form.refund_account_bank === props.release.refund_account_bank
    const d = form.refund_account_number === props.release.refund_account_number
    const e = form.refund_account_depositor === props.release.refund_account_depositor
    const f = form.request_date === props.release.request_date
    const g = form.completion_date === props.release.completion_date
    const h = form.note === props.release.note
    return a && b && c && d && e && f && g && h
  } else return false
})

const onSubmit = (event: Event) => {
  if (write_contract.value) {
    if (isValidate(event)) {
      validated.value = true
    } else emit('on-submit', { ...form })
  } else refAlertModal.value.callModal()
}

const deleteConfirm = () => {
  if (write_contract.value) refConfirmModal.value.callModal()
  else refAlertModal.value.callModal()
}

const modalAction = () => alert('this is ready!')

const formDataSet = () => {
  if (props.release) {
    form.pk = props.release.pk
    form.contractor = props.release.contractor
    form.status = props.release.status
    form.refund_amount = props.release.refund_amount
    form.refund_account_bank = props.release.refund_account_bank
    form.refund_account_number = props.release.refund_account_number
    form.refund_account_depositor = props.release.refund_account_depositor
    form.request_date = props.release.request_date
    form.completion_date = props.release.completion_date
    form.note = props.release.note
  } else form.contractor = props.contractor.pk
}

onBeforeMount(() => formDataSet())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label">계약자</CFormLabel>
            <CCol sm="8">
              <CFormSelect v-model="form.contractor" required readonly>
                <option :value="form.contractor">
                  {{ contractor ? contractor.name : release.__str__ }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required">구분</CFormLabel>
            <CCol sm="8" class="text-left">
              <CFormSelect v-model="form.status" required>
                <option value="">---------</option>
                <option v-if="release && release.status < '4'" value="0">신청 취소</option>
                <option v-if="!release || release.status < '4'" value="3">해지 신청</option>
                <option v-if="release" value="4">해지 완료</option>
                <option v-if="release" value="5">자격 상실</option>
              </CFormSelect>
              <small v-if="form.status >= '4' && release.status < '4'" class="text-danger">
                해지 완료, 자격 상실 처리된 계약 건은 계약상태로 되돌릴 수 없으므로 최종 확정된
                상태에서만 진행하십시요.
              </small>
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 환불(예정)금액</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model.number="form.refund_amount"
                type="number"
                min="0"
                placeholder="환불(예정)금액"
              />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 거래은행(환불계좌)</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model="form.refund_account_bank"
                maxlength="20"
                placeholder="거래은행(환불계좌)"
              />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-2">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 계좌번호(환불계좌)</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model="form.refund_account_number"
                maxlength="25"
                placeholder="계좌번호(환불계좌)"
              />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 예금주(환불계좌)</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model="form.refund_account_depositor"
                maxlength="20"
                placeholder="예금주(환불계좌)"
              />
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label required"> 해지신청일</CFormLabel>
            <CCol sm="8">
              <DatePicker v-model="form.request_date" required placeholder="해지신청일" />
            </CCol>
          </CRow>
        </CCol>

        <CCol xs="6">
          <CRow>
            <CFormLabel class="col-sm-4 col-form-label"> 해지(환불)처리일</CFormLabel>
            <CCol sm="8">
              <DatePicker
                v-model="form.completion_date"
                :required="form.status === '4'"
                placeholder="해지종결일"
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
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" :color="btnLight" size="small" @click="emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          type="submit"
          :color="release ? 'success' : 'primary'"
          size="small"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="release" type="button" color="warning" size="small" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 계약 해지 정보 - [삭제]</template>
    <template #default>
      삭제 후 복구할 수 없습니다. 해당 건별 수납 정보 삭제를 진행하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
