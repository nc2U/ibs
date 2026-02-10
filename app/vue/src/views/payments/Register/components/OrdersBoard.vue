<script lang="ts" setup>
import { computed, ref, watch, type PropType } from 'vue'
import { usePayment } from '@/store/pinia/payment'
import { useContract } from '@/store/pinia/contract'
import type { Contract, ContractPriceWithPaymentPlan } from '@/store/types/contract.ts'
import { type AllPayment, type PayOrder, type Price } from '@/store/types/payment'
import { numFormat, getToday } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import Order from '@/views/payments/Register/components/Order.vue'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, default: null },
  paymentList: { type: Array as PropType<AllPayment[]>, default: () => [] },
})

const paymentStore = usePayment()
const contractStore = useContract()
const payOrderList = computed(() => paymentStore.payOrderList)
const priceList = computed(() => paymentStore.priceList)

// Payment plan data from API (using high-performance price_payment_plan)
const contractPriceData = ref<ContractPriceWithPaymentPlan | null>(null)
const isLoadingPaymentPlan = ref(false)

// Fetch payment plan for contract (using high-performance API)
const fetchPaymentPlan = async () => {
  if (!props.contract?.pk) {
    contractPriceData.value = null
    return
  }

  try {
    isLoadingPaymentPlan.value = true
    contractPriceData.value = await contractStore.fetchContractPricePaymentPlan(props.contract.pk)
  } catch (error) {
    console.error('Failed to fetch payment plan:', error)
    contractPriceData.value = null
  } finally {
    isLoadingPaymentPlan.value = false
  }
}

// Watch for contract changes and fetch payment plan
watch(() => props.contract?.pk, fetchPaymentPlan, { immediate: true })

const thisPrice = computed(() => {
  if (props.contract) {
    if (props.contract.contractprice) return props.contract.contractprice?.price
    else if (props.contract.key_unit?.houseunit && priceList.value.length)
      return priceList.value
        .filter((p: Price) => p.unit_floor_type === props.contract?.key_unit?.houseunit?.floor_type)
        .map((p: Price) => p.price)[0]
    else if (!!props.contract.unit_type_desc?.average_price)
      return Math.ceil(props.contract.unit_type_desc.average_price / 10000) * 10000
    else return 0
  }
  return 0
})

const paidTotal = computed(() => {
  const paid = props.paymentList.map((p: AllPayment) => p.income)
  return paid.length === 0 ? 0 : paid.reduce((x: number, y: number) => x + y, 0)
})

// 납부해야할 총액
const dueTotal = computed(() => {
  // contractPriceData가 로드되지 않은 경우 0 반환
  if (!contractPriceData.value?.payment_plan?.length) return 0

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
    if (el) commitment.push(getCommitsFromAPI(el))
  })
  return commitment.length !== 0 ? commitment.reduce((x, y) => x + y) : 0
})

// Get payment amount from API data (high-performance JSON cache)
const getCommitsFromAPI = (payTime: number | undefined) => {
  if (!payTime || !contractPriceData.value) return 0

  // Use cached payment_amounts for fastest lookup (6.7x performance improvement)
  const amount = contractPriceData.value.payment_amounts[payTime.toString()]
  return amount || 0
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
          :commit="getCommitsFromAPI(po.pay_time as number)"
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
