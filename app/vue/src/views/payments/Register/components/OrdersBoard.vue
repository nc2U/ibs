<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { usePayment } from '@/store/pinia/payment'
import type { Contract } from '@/store/types/contract.ts'
import { type AllPayment, type DownPay, type PayOrder, type Price } from '@/store/types/payment'
import { numFormat, getToday } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import Order from '@/views/payments/Register/components/Order.vue'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, default: null },
  paymentList: { type: Array as PropType<AllPayment[]>, default: () => [] },
})

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)
const priceList = computed(() => paymentStore.priceList)
const downPayList = computed(() => paymentStore.downPayList)

const thisPrice = computed(() => {
  if (props.contract) {
    if (props.contract.contractprice) return props.contract.contractprice?.price
    else if (props.contract.key_unit?.houseunit && priceList.value.length)
      return priceList.value
        .filter((p: Price) => p.unit_floor_type === props.contract?.key_unit?.houseunit?.floor_type)
        .map((p: Price) => p.price)[0]
    else if (!!props.contract.unit_type_desc.average_price)
      return Math.ceil(props.contract.unit_type_desc.average_price / 10000) * 10000
    else return 0
  }
  return 0
})

const numDown = computed(
  () => payOrderList.value.filter((o: PayOrder) => o.pay_sort === '1').length,
)

const numMid = computed(() => payOrderList.value.filter((o: PayOrder) => o.pay_sort === '2').length)

const paidTotal = computed(() => {
  const paid = props.paymentList.map((p: AllPayment) => p.income)
  return paid.length === 0 ? 0 : paid.reduce((x: number, y: number) => x + y, 0)
})

// 납부해야할 총액
const dueTotal = computed(() => {
  const commitment: number[] = []
  const today = getToday()

  const dueOrder = payOrderList.value
    .filter(
      (o: PayOrder) =>
        (o.pay_code ?? 0) === 1 ||
        ((o.pay_code ?? 0) === 2 && o.days_since_prev) ||
        (o.pay_due_date && o.pay_due_date <= today && !o.extra_due_date) ||
        (o.extra_due_date && o.extra_due_date <= today),
    )
    .map((o: PayOrder) => o.pay_time)

  dueOrder.forEach((el: number | null | undefined) => {
    if (el) commitment.push(getCommits(el))
  })
  return commitment.length !== 0 ? commitment.reduce((x, y) => x + y) : 0
})

const getCommits = (el: number | undefined) => {
  // 약정금 구하기
  const down = downPayList.value
    .filter((d: DownPay) => d.order_group === props.contract?.order_group)
    .filter(d => d.unit_type === props.contract?.unit_type)
    .map(d => d.payment_amount)[0] // 1. downPayList, 2. payByOrder, 3. 분양가 / 총회차수

  const order = payOrderList.value.find((o: PayOrder) => o.pay_time === el)

  const payByOrder = order?.pay_ratio
    ? (thisPrice.value * Number(order.pay_ratio)) / 100
    : thisPrice.value * 0.1 // 1. payByOrder === '중도금' (지정된 비율이 없으면 회당 10%)
  const downPay = down ? down : payByOrder
  const balance = thisPrice.value - downPay * numDown.value - payByOrder * numMid.value // 분양가 - (계약금 + 중도금), 2. payByOrder
  const balancePay = balance ? balance : (payByOrder * Number(order?.pay_ratio)) / 100

  if (order?.pay_sort === '1') {
    return downPay // 계약금
  } else if (order?.pay_sort === '2') {
    return payByOrder // 중도금
  } else if (order?.pay_sort === '3') {
    return balancePay // 잔금
  } else return 0
}
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 20%" />
      <col style="width: 20%" />
      <col style="width: 20%" />
      <col style="width: 20%" />
      <col style="width: 20%" />
    </colgroup>

    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>납부기일</CTableHeaderCell>
        <CTableHeaderCell>구분</CTableHeaderCell>
        <CTableHeaderCell>약정금액</CTableHeaderCell>
        <CTableHeaderCell>수납금액</CTableHeaderCell>
        <CTableHeaderCell>미(과오)납</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="contract">
      <CTableRow v-for="po in payOrderList" :key="po.pk" class="text-right">
        <Order
          :contract="contract"
          :price="thisPrice"
          :order="po"
          :commit="getCommits(po.pay_time as number)"
          :payment-list="paymentList"
        />
      </CTableRow>
    </CTableBody>

    <CTableHead>
      <CTableRow class="text-right">
        <CTableHeaderCell :color="TableSecondary" class="text-center"> 합계</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(thisPrice || 0) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(paidTotal) }}</CTableHeaderCell>

        <CTableHeaderCell :class="paidTotal - dueTotal < 0 ? 'text-danger' : ''">
          {{ numFormat(paidTotal - dueTotal) }}
        </CTableHeaderCell>
      </CTableRow>
    </CTableHead>
  </CTable>
</template>
