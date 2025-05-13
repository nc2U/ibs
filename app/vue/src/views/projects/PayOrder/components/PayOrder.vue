<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, nextTick, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { write_project } from '@/utils/pageAuth'
import type { PayOrder } from '@/store/types/payment'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const emit = defineEmits(['on-update', 'on-delete'])
const props = defineProps({ payOrder: { type: Object as PropType<PayOrder>, required: true } })

const form = reactive<PayOrder>({
  type_sort: '1',
  pay_sort: '',
  is_except_price: false,
  pay_code: null,
  pay_time: null,
  pay_name: '',
  alias_name: '',
  pay_amt: null,
  pay_ratio: null,
  pay_due_date: null,
  days_since_prev: null,
  is_prep_discount: false,
  prep_discount_ratio: null,
  prep_ref_date: null,
  is_late_penalty: false,
  late_penalty_ratio: null,
  extra_due_date: null,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const formsCheck = computed(() => {
  const a = form.type_sort === props.payOrder?.type_sort
  const b = form.pay_sort === props.payOrder?.pay_sort
  const c = form.is_except_price === props.payOrder?.is_except_price
  const d = form.pay_code === props.payOrder?.pay_code
  const e = form.pay_time === props.payOrder?.pay_time
  const f = form.pay_name === props.payOrder?.pay_name
  const g = form.alias_name === props.payOrder?.alias_name
  const h = form.pay_amt === props.payOrder?.pay_amt
  const i = form.pay_ratio === props.payOrder?.pay_ratio
  const j = form.pay_due_date === props.payOrder?.pay_due_date
  const k = form.days_since_prev === props.payOrder?.days_since_prev
  const l = form.is_prep_discount === props.payOrder?.is_prep_discount
  const m = form.prep_discount_ratio === props.payOrder?.prep_discount_ratio
  const n = form.prep_ref_date === props.payOrder?.prep_ref_date
  const o = form.is_late_penalty === props.payOrder?.is_late_penalty
  const p = form.late_penalty_ratio === props.payOrder?.late_penalty_ratio
  const q = form.extra_due_date === props.payOrder?.extra_due_date
  return a && b && c && d && e && f && g && h && i && j && k && l && m && n && o && p && q
})

const formCheck = (bool: boolean) => {
  if (bool) onUpdatePayOrder()
  return
}
const remainChk = () => {
  nextTick(() => {
    if (form.pay_sort === '3') form.pay_ratio = null
  })
}
const onUpdatePayOrder = () => {
  if (write_project.value) {
    const pk = props.payOrder.pk
    emit('on-update', { ...{ pk }, ...form })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}
const onDeletePayOrder = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}
const modalAction = () => {
  emit('on-delete', props.payOrder?.pk)
  refConfirmModal.value.close()
}

const dataSetup = () => {
  form.type_sort = props.payOrder?.type_sort
  form.pay_sort = props.payOrder?.pay_sort
  form.is_except_price = props.payOrder?.is_except_price
  form.pay_code = props.payOrder?.pay_code
  form.pay_time = props.payOrder?.pay_time
  form.pay_name = props.payOrder?.pay_name
  form.alias_name = props.payOrder?.alias_name
  form.pay_amt = props.payOrder?.pay_amt
  form.pay_ratio = props.payOrder?.pay_ratio
  form.pay_due_date = props.payOrder?.pay_due_date
  form.days_since_prev = props.payOrder?.days_since_prev
  form.is_prep_discount = props.payOrder?.is_prep_discount
  form.prep_discount_ratio = props.payOrder?.prep_discount_ratio
  form.prep_ref_date = props.payOrder?.prep_ref_date
  form.is_late_penalty = props.payOrder?.is_late_penalty
  form.late_penalty_ratio = props.payOrder?.late_penalty_ratio
  form.extra_due_date = props.payOrder?.extra_due_date
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.type_sort" required>
        <option value="">타입 종류</option>
        <option value="1">공동주택</option>
        <option value="2">오피스텔</option>
        <option value="3">숙박시설</option>
        <option value="4">지식산업센터</option>
        <option value="5">근린생활시설</option>
        <option value="6">기타</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.pay_sort" required @change="remainChk">
        <option value="">종류선택</option>
        <option value="1">계약금</option>
        <option value="2">중도금</option>
        <option value="3">잔금</option>
        <option value="4">기타 부담금</option>
        <option value="5">제세 공과금</option>
        <option value="6">금융 비용</option>
        <option value="7">업무 대행비</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CCol class="pt-2 pl-3">
        <CFormSwitch v-model="form.is_except_price" :id="`ipd-${payOrder.pk}`" label="불포함" />
      </CCol>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.pay_code"
        placeholder="납입회차 코드"
        type="number"
        min="0"
        required
        @keypress.enter="formCheck(form.pay_code !== payOrder.pay_code)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.pay_time"
        placeholder="납부순서"
        type="number"
        min="0"
        required
        @keypress.enter="formCheck(form.pay_time !== payOrder.pay_time)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.pay_name"
        maxlength="20"
        placeholder="납부회차 명"
        required
        @keypress.enter="formCheck(form.pay_name !== payOrder.pay_name)"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.alias_name"
        maxlength="20"
        placeholder="회차 별칭"
        required
        @keypress.enter="formCheck(form.alias_name !== payOrder.alias_name)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.pay_amt"
        placeholder="납부 약정액"
        type="number"
        min="0"
        @keypress.enter="formCheck(form.pay_amt !== payOrder.pay_amt)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.pay_ratio"
        placeholder="납부비율"
        type="number"
        min="0"
        @keypress.enter="formCheck(form.pay_ratio !== payOrder.pay_ratio)"
        :disabled="form.pay_sort === '3'"
      />
    </CTableDataCell>
    <CTableDataCell>
      <DatePicker
        v-model="form.pay_due_date"
        maxlength="10"
        placeholder="납부약정일"
        :required="false"
        @keypress.enter="formCheck(form.pay_due_date !== payOrder.pay_due_date)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.days_since_prev"
        type="number"
        maxlength="20"
        placeholder="전회 기준 경과일수"
        required
        @keypress.enter="formCheck(form.days_since_prev !== payOrder.days_since_prev)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CCol class="pt-2 pl-3">
        <CFormSwitch v-model="form.is_prep_discount" :id="`ipd-${payOrder.pk}`" label="선납할인" />
      </CCol>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.prep_discount_ratio"
        placeholder="선납할인율"
        type="number"
        min="0"
        @keypress.enter="formCheck(form.prep_discount_ratio !== payOrder.prep_discount_ratio)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <DatePicker
        v-model="form.prep_ref_date"
        maxlength="10"
        placeholder="선납기준일"
        :required="false"
        @keypress.enter="formCheck(form.prep_ref_date !== payOrder.prep_ref_date)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CCol class="pt-2 pl-3">
        <CFormSwitch v-model="form.is_late_penalty" :id="`ilp-${payOrder.pk}`" label="연체가산" />
      </CCol>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.late_penalty_ratio"
        placeholder="연체가산율"
        type="number"
        min="0"
        @keypress.enter="formCheck(form.late_penalty_ratio !== payOrder.late_penalty_ratio)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <DatePicker
        v-model="form.extra_due_date"
        maxlength="10"
        placeholder="연체기준일"
        :required="false"
        @keypress.enter="formCheck(form.extra_due_date !== payOrder.extra_due_date)"
      />
    </CTableDataCell>

    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdatePayOrder">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" @click="onDeletePayOrder">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 납부 회차 삭제</template>
    <template #default>
      프로젝트 입출금 데이터에 이 납부 회차 정보가 등록되어 있는 경우 해당 데이터에서 납부 회차
      정보가 삭제됩니다. 이 납부 회차 정보를 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
