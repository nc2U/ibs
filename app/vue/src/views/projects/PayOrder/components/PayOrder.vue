<script lang="ts" setup>
import { ref, reactive, computed, watch, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms'
import type { PayOrder } from '@/store/types/payment'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ payOrder: { type: Object as PropType<PayOrder>, required: true } })
const emit = defineEmits<{
  (e: 'on-update', payload: PayOrder): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

type PayOrderFormState = Omit<
  PayOrder,
  | 'pay_code'
  | 'pay_time'
  | 'pay_amt'
  | 'pay_ratio'
  | 'days_since_prev'
  | 'prep_discount_ratio'
  | 'late_penalty_ratio'
> & {
  pay_code: number | '' | null
  pay_time: number | '' | null
  pay_amt: number | '' | null
  pay_ratio: number | '' | null
  days_since_prev: number | '' | null
  prep_discount_ratio: number | '' | null
  late_penalty_ratio: number | '' | null
}

const form = reactive<PayOrderFormState>({
  type_sort: '1',
  pay_sort: '',
  calculation_method: 'auto',
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

const isExpand = ref(false)

const toNullableNumber = (val: number | '' | null | undefined) =>
  val !== null && val !== undefined && val !== '' ? Number(val) : null

const dataSetup = () => {
  if (props.payOrder) {
    form.type_sort = props.payOrder.type_sort ?? '1'
    form.pay_sort = props.payOrder.pay_sort ?? ''
    form.calculation_method = props.payOrder.calculation_method ?? 'auto'
    form.is_except_price = props.payOrder.is_except_price ?? false
    form.pay_code = props.payOrder.pay_code ?? null
    form.pay_time = props.payOrder.pay_time ?? null
    form.pay_name = props.payOrder.pay_name ?? ''
    form.alias_name = props.payOrder.alias_name ?? ''
    form.pay_amt = props.payOrder.pay_amt ?? null
    form.pay_ratio = props.payOrder.pay_ratio ?? null
    form.pay_due_date = props.payOrder.pay_due_date ?? null
    form.days_since_prev = props.payOrder.days_since_prev ?? null
    form.is_prep_discount = props.payOrder.is_prep_discount ?? false
    form.prep_discount_ratio = props.payOrder.prep_discount_ratio ?? null
    form.prep_ref_date = props.payOrder.prep_ref_date ?? null
    form.is_late_penalty = props.payOrder.is_late_penalty ?? false
    form.late_penalty_ratio = props.payOrder.late_penalty_ratio ?? null
    form.extra_due_date = props.payOrder.extra_due_date ?? null
  }
}

watch(
  () => props.payOrder,
  () => dataSetup(),
  { deep: true, immediate: true },
)

const areNumbersEqual = (a: number | '' | null | undefined, b: number | '' | null | undefined) =>
  toNullableNumber(a) === toNullableNumber(b)

const areStringsEqual = (a: string | null | undefined, b: string | null | undefined) => {
  return (a || '').trim() === (b || '').trim()
}

const isUnchanged = computed(() => {
  const a = form.type_sort === props.payOrder.type_sort
  const b = form.pay_sort === props.payOrder.pay_sort
  const c = form.calculation_method === props.payOrder.calculation_method
  const d = Boolean(form.is_except_price) === Boolean(props.payOrder.is_except_price)
  const e = areNumbersEqual(form.pay_code, props.payOrder.pay_code)
  const f = areNumbersEqual(form.pay_time, props.payOrder.pay_time)
  const g = areStringsEqual(form.pay_name, props.payOrder.pay_name)
  const h = areStringsEqual(form.alias_name, props.payOrder.alias_name)
  const i = areNumbersEqual(form.pay_amt, props.payOrder.pay_amt)
  const j = areNumbersEqual(form.pay_ratio, props.payOrder.pay_ratio)
  const k = areStringsEqual(form.pay_due_date, props.payOrder.pay_due_date)
  const l = areNumbersEqual(form.days_since_prev, props.payOrder.days_since_prev)
  const m = Boolean(form.is_prep_discount) === Boolean(props.payOrder.is_prep_discount)
  const n = areNumbersEqual(form.prep_discount_ratio, props.payOrder.prep_discount_ratio)
  const o = areStringsEqual(form.prep_ref_date, props.payOrder.prep_ref_date)
  const p = Boolean(form.is_late_penalty) === Boolean(props.payOrder.is_late_penalty)
  const q = areNumbersEqual(form.late_penalty_ratio, props.payOrder.late_penalty_ratio)
  const r = areStringsEqual(form.extra_due_date, props.payOrder.extra_due_date)

  return a && b && c && d && e && f && g && h && i && j && k && l && m && n && o && p && q && r
})

const isFormValid = computed(() => {
  const hasType = Boolean(form.type_sort)
  const hasSort = Boolean(form.pay_sort)
  const hasCode = typeof form.pay_code === 'number' && form.pay_code >= 0
  const hasTime = typeof form.pay_time === 'number' && form.pay_time >= 0
  const hasName = Boolean((form.pay_name || '').trim())

  const prepValid =
    !form.is_prep_discount || (form.prep_discount_ratio !== null && form.prep_discount_ratio !== '')
  const lateValid =
    !form.is_late_penalty || (form.late_penalty_ratio !== null && form.late_penalty_ratio !== '')

  return hasType && hasSort && hasCode && hasTime && hasName && prepValid && lateValid
})

const formsCheck = computed(() => {
  if (!canProjectUpdate.value) return true
  if (!isFormValid.value) return true
  return isUnchanged.value
})

const onPaySortChange = () => {
  if (form.pay_sort !== '1') {
    form.calculation_method = 'auto'
  }
  if (form.pay_sort === '2' || form.pay_sort === '3') {
    form.pay_amt = null
  }
  if (form.pay_sort === '3') {
    form.pay_ratio = null
  }
}

const onUpdatePayOrder = () => {
  if (formsCheck.value) return

  if (canProjectUpdate.value) {
    emit('on-update', {
      pk: props.payOrder.pk,
      project: props.payOrder.project,
      type_sort: form.type_sort,
      pay_sort: form.pay_sort,
      calculation_method: form.calculation_method,
      is_except_price: form.is_except_price,
      pay_code: toNullableNumber(form.pay_code),
      pay_time: toNullableNumber(form.pay_time),
      pay_name: (form.pay_name || '').trim(),
      alias_name: (form.alias_name || '').trim(),
      pay_amt: toNullableNumber(form.pay_amt),
      pay_ratio: toNullableNumber(form.pay_ratio),
      pay_due_date: form.pay_due_date || null,
      days_since_prev: toNullableNumber(form.days_since_prev),
      is_prep_discount: form.is_prep_discount,
      prep_discount_ratio: form.is_prep_discount
        ? toNullableNumber(form.prep_discount_ratio)
        : null,
      prep_ref_date: form.is_prep_discount ? form.prep_ref_date || null : null,
      is_late_penalty: form.is_late_penalty,
      late_penalty_ratio: form.is_late_penalty ? toNullableNumber(form.late_penalty_ratio) : null,
      extra_due_date: form.is_late_penalty ? form.extra_due_date || null : null,
      excluded_order_groups: props.payOrder.excluded_order_groups,
    })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeletePayOrder = () => {
  if (isSuperAuth.value) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  if (props.payOrder.pk) {
    emit('on-delete', props.payOrder.pk)
  }
  refConfirmModal.value.close()
}
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.type_sort" :disabled="!canProjectUpdate" required>
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
      <CFormSelect
        v-model="form.pay_sort"
        :disabled="!canProjectUpdate"
        required
        @change="onPaySortChange"
      >
        <option value="">종류선택</option>
        <option value="1">계약금</option>
        <option value="2">중도금</option>
        <option value="3">잔금</option>
        <option value="4">계약금 정산</option>
        <option value="5">미납 연체료</option>
        <option value="6">기타 부담금</option>
        <option value="7">제세 공과금</option>
        <option value="8">후불 이자</option>
        <option value="9">업무 대행비</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect
        v-model="form.calculation_method"
        :disabled="!canProjectUpdate || form.pay_sort !== '1'"
      >
        <option value="auto">---------</option>
        <option value="downpayment">등록 계약 금액 우선</option>
        <option value="ratio">분양가격 × 납부비율</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CCol class="pt-2 ps-3">
        <CFormSwitch
          v-model="form.is_except_price"
          :id="`iep-${payOrder.pk}`"
          label="불포함"
          :disabled="!canProjectUpdate"
        />
      </CCol>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.pay_code"
        placeholder="납입회차 코드"
        type="number"
        min="0"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.pay_time"
        placeholder="납부순서"
        type="number"
        min="0"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.pay_name"
        maxlength="20"
        placeholder="납부회차 명"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.alias_name"
        maxlength="20"
        placeholder="회차 별칭"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.pay_amt"
        placeholder="납부 약정액"
        type="number"
        min="0"
        :disabled="!canProjectUpdate || form.pay_sort === '2' || form.pay_sort === '3'"
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.pay_ratio"
        placeholder="납부비율"
        type="number"
        min="0"
        :disabled="!canProjectUpdate || form.pay_sort === '3'"
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>

    <CTableDataCell class="ps-lg-5 pt-3">
      <CFormSwitch v-model="isExpand" :id="`i-expand-${payOrder.pk}`" label="추가설정" />
    </CTableDataCell>

    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdatePayOrder">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeletePayOrder">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <CTableRow v-show="isExpand" color="warning">
    <CTableDataCell> </CTableDataCell>
    <CTableDataCell>
      <DatePicker
        v-model="form.pay_due_date"
        maxlength="10"
        placeholder="납부약정일"
        :required="false"
        :disabled="!canProjectUpdate"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.days_since_prev"
        type="number"
        min="0"
        maxlength="20"
        placeholder="전회 기준 경과일수"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>

    <CTableDataCell> </CTableDataCell>
    <CTableDataCell>
      <CCol class="pt-2 ps-3">
        <CFormSwitch
          v-model="form.is_prep_discount"
          :id="`ipd-${payOrder.pk}`"
          label="선납할인"
          :disabled="!canProjectUpdate"
        />
      </CCol>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.prep_discount_ratio"
        placeholder="선납할인율"
        type="number"
        min="0"
        :disabled="!canProjectUpdate || !form.is_prep_discount"
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>
    <CTableDataCell>
      <DatePicker
        v-model="form.prep_ref_date"
        maxlength="10"
        placeholder="선납기준일"
        :required="false"
        :disabled="!canProjectUpdate || !form.is_prep_discount"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CCol class="pt-2 ps-3">
        <CFormSwitch
          v-model="form.is_late_penalty"
          :id="`ilp-${payOrder.pk}`"
          label="연체가산"
          :disabled="!canProjectUpdate"
        />
      </CCol>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.late_penalty_ratio"
        placeholder="연체가산율"
        type="number"
        min="0"
        :disabled="!canProjectUpdate || !form.is_late_penalty"
        @keydown.enter.prevent="onUpdatePayOrder"
      />
    </CTableDataCell>
    <CTableDataCell>
      <DatePicker
        v-model="form.extra_due_date"
        maxlength="10"
        placeholder="연체기준일"
        :required="false"
        :disabled="!canProjectUpdate || !form.is_late_penalty"
      />
    </CTableDataCell>
    <CTableDataCell> </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate"></CTableDataCell>
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
