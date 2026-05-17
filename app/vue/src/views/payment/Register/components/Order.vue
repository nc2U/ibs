<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Contract } from '@/store/types/contract.ts'
import { type OriginPayment, type PayOrder } from '@/store/types/payment'
import { numFormat, getToday, addDaysToDate } from '@/utils/baseMixins'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, default: null },
  order: { type: Object as PropType<PayOrder>, default: null },
  commit: { type: Number, default: 0 },
  price: { type: Number, default: 0 },
  adjustedDueDate: { type: String as PropType<string | null>, default: null },
  paymentList: { type: Array as PropType<OriginPayment[]>, default: () => [] },
})

const dueDate = computed(() => {
  // 1. 백엔드에서 조정된 날짜가 전달된 경우 최우선 사용
  if (props.adjustedDueDate) return props.adjustedDueDate

  // 2. 계약 정보가 없으면 계산 불가
  const contDate = props.contract?.contractor?.contract_date
  if (!contDate) return '-'

  // 3. 계약금(pay_code=1)은 계약일을 기본값으로 사용
  if (props.order?.pay_code === 1) return contDate

  // 4. 그 외(중도금/잔금)는 백엔드 데이터(adjustedDueDate) 없이는 표시하지 않음
  // (DB의 pay_due_date는 프로젝트 전체 일정이지 개인별 약정일이 아니기 때문)
  return '-'
})

const paidByOrder = computed(() => {
  // 당회차 납부 총액
  const paid = props.paymentList
    .filter((p: OriginPayment) => !!p.installment_order)
    .filter(p => p.installment_order.pk === props.order?.pk)
    .map(p => p.amount)

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
