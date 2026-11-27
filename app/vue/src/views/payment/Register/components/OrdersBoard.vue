<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { usePayment } from '@/store/pinia/payment.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { useProjectData } from '@/store/pinia/project_data.ts'
import type { Contract, ContractPriceWithPaymentPlan } from '@/store/types/contract.ts'
import type { OriginPayment, PayOrder, Price } from '@/store/types/payment.ts'
import { numFormat, getToday } from '@/utils/baseMixins.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import Order from './Order.vue'

const props = withDefaults(
  defineProps<{
    contract?: Contract | null
    paymentList?: OriginPayment[]
  }>(),
  {
    contract: null,
    paymentList: () => [],
  },
)

const paymentStore = usePayment()
const contractStore = useContract()
const projectDataStore = useProjectData()
const payOrderList = computed(() => paymentStore.payOrderList)
const priceList = computed(() => paymentStore.priceList)

// 계약의 차수(order_group) 및 타입종류(type_sort)에 따라 회차를 필터링한 리스트
const filteredPayOrderList = computed(() => {
  const orderGroup = props.contract?.order_group
  const matchedUnitType = props.contract?.unit_type
    ? projectDataStore.unitTypeList.find(ut => ut.pk === props.contract?.unit_type)
    : undefined
  const typeSort = props.contract?.unit_type_desc?.sort ?? matchedUnitType?.sort
  return payOrderList.value.filter((po: PayOrder) => {
    if (orderGroup && po.excluded_order_groups?.includes(orderGroup)) return false
    if (typeSort && po.type_sort && po.type_sort !== typeSort) return false
    return true
  })
})

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
  const paid = props.paymentList.map((p: OriginPayment) => p.amount!)
  return paid.length === 0 ? 0 : paid.reduce((x: number, y: number) => x + y, 0)
})

// 납부해야할 총액
const dueTotal = computed(() => {
  // contractPriceData가 로드되지 않은 경우 0 반환
  if (!contractPriceData.value?.payment_plan?.length) return 0

  const today = getToday()
  return filteredPayOrderList.value
    .filter(po => {
      const adjustedDate = getDueDateFromAPI(po)
      return adjustedDate && adjustedDate <= today
    })
    .reduce((sum, po) => sum + getCommitsFromAPI(po), 0)
})

const findPlanItem = (order: PayOrder) => {
  const plan = contractPriceData.value?.payment_plan
  if (!plan?.length) return undefined
  if (order.pk) {
    const byPk = plan.find(item => item.installment_order.pk === order.pk)
    if (byPk) return byPk
  }
  if (order.pay_time) {
    return plan.find(item => item.installment_order.pay_time === order.pay_time)
  }
  return undefined
}

// Get payment amount from API data (high-performance JSON cache)
const getCommitsFromAPI = (order: PayOrder) => {
  if (!contractPriceData.value) return 0

  // 1. payment_plan에서 해당 회차의 조정된 금액을 먼저 찾음 (pk 우선 매칭으로 동일 pay_time 충돌 방지)
  const planItem = findPlanItem(order)
  if (planItem) return planItem.amount

  // 2. plan에 없으면 payment_amounts 캐시 확인
  if (order.pay_time) {
    return contractPriceData.value.payment_amounts[order.pay_time.toString()] || 0
  }
  return 0
}

// Get adjusted due date from API data
const getDueDateFromAPI = (order: PayOrder) => {
  if (!contractPriceData.value) return null
  return findPlanItem(order)?.due_date || null
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

    <CTableHead :color="TableSecondary" class="text-center border-top">
      <CTableRow>
        <CTableHeaderCell>납부기일</CTableHeaderCell>
        <CTableHeaderCell>구분</CTableHeaderCell>
        <CTableHeaderCell>약정금액</CTableHeaderCell>
        <CTableHeaderCell>수납금액</CTableHeaderCell>
        <CTableHeaderCell>미(과오)납</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="contract">
      <CTableRow v-for="po in filteredPayOrderList" :key="po.pk" class="text-end">
        <Order
          :contract="contract"
          :price="thisPrice"
          :order="po"
          :commit="getCommitsFromAPI(po)"
          :adjusted-due-date="getDueDateFromAPI(po)"
          :payment-list="paymentList"
        />
      </CTableRow>
    </CTableBody>

    <CTableHead>
      <CTableRow class="text-end">
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
