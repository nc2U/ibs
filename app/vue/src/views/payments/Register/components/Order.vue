<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Contract } from '@/store/types/contract.ts'
import { type AllPayment, type PayOrder } from '@/store/types/payment'
import { numFormat, getToday, addDaysToDate } from '@/utils/baseMixins'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, default: null },
  order: { type: Object as PropType<PayOrder>, default: null },
  commit: { type: Number, default: 0 },
  price: { type: Number, default: 0 },
  paymentList: { type: Array as PropType<AllPayment[]>, default: () => [] },
})

const dueDate = computed(() => {
  const contDate = props.contract?.contractor?.contract_date
  if (props.order?.pay_code === 1) return contDate
  else {
    if (props.order?.days_since_prev)
      return addDaysToDate(contDate as Date | string, props.order?.days_since_prev as number)
    else return props.order?.extra_due_date || props.order?.pay_due_date || '-'
  }
})

const paidByOrder = computed(() => {
  // 당회차 납부 총액
  const paid = props.paymentList
    .filter((p: AllPayment) => !!p.installment_order)
    .filter(p => p.installment_order.pk === props.order?.pk)
    .map(p => p.income)

  return paid.length === 0 ? 0 : paid.reduce((x: number, y: number) => x + y, 0)
})

const calculated = computed(() => {
  const duePay = paidByOrder.value - props.commit
  return dueDate.value !== '-' && (dueDate.value as Date | string) <= getToday() ? duePay : 0
})

const calcClass = () => {
  const calc = calculated.value > 0 ? 'text-primary' : 'text-danger'
  return calculated.value === 0 ? '' : calc
}
</script>

<template>
  <CTableDataCell class="text-center"> {{ dueDate }}</CTableDataCell>
  <CTableDataCell class="text-center">
    {{ order.pay_name }}
  </CTableDataCell>
  <CTableDataCell>
    {{ numFormat(commit) }}
  </CTableDataCell>
  <CTableDataCell :class="paidByOrder > 0 ? 'text-primary' : ''">
    {{ numFormat(paidByOrder) }}
  </CTableDataCell>
  <CTableDataCell :class="calcClass">
    {{ numFormat(calculated) }}
  </CTableDataCell>
</template>
