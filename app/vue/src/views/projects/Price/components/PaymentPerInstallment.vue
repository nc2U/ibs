<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { usePayment } from '@/store/pinia/payment'
import type { PaymentPerInstallment, PayOrder } from '@/store/types/payment'

const props = defineProps<{
  salesPriceId: number
  projectId: number
  payOrders: PayOrder[]
}>()

const emit = defineEmits<{
  (e: 'editRequested', item: PaymentPerInstallment): void
  (e: 'deleteRequested', item: PaymentPerInstallment): void
  (e: 'createRequested'): void
  (e: 'usedPayOrdersChanged', usedPayOrderIds: number[]): void
}>()

const payStore = usePayment()
const { getPaymentPerInstallmentData } = payStore

// 로컬 상태로 변경 (전역 상태 대신)
const localPaymentPerInstallmentList = ref<PaymentPerInstallment[]>([])

// Available pay orders (filtering out 중도금=2, 잔금=3)
const availablePayOrders = computed(() =>
  props.payOrders.filter(order => order.pay_sort && !['2', '3'].includes(order.pay_sort)),
)

// 사용된 pay_order ID들 계산
const usedPayOrderIds = computed(() => {
  return localPaymentPerInstallmentList.value
    .map(ppi => ppi.pay_order)
    .filter(id => id !== null) as number[]
})

// 데이터 변경 시 부모에게 알림
watch(
  usedPayOrderIds,
  newIds => {
    emit('usedPayOrdersChanged', newIds)
  },
  { immediate: true },
)

// Load data on mount and when salesPriceId changes
onMounted(() => {
  loadData()
})

watch(
  () => props.salesPriceId,
  () => {
    loadData()
  },
)

const loadData = async () => {
  if (props.salesPriceId) {
    try {
      // Pinia 메서드를 통해 로컬 상태 업데이트
      const data = await getPaymentPerInstallmentData({ sales_price: props.salesPriceId })
      localPaymentPerInstallmentList.value = data
    } catch (error) {
      console.error('Error loading PaymentPerInstallment data:', error)
      localPaymentPerInstallmentList.value = []
    }
  } else {
    localPaymentPerInstallmentList.value = []
  }
}

const handleCreate = () => emit('createRequested')

const handleEdit = (item: PaymentPerInstallment) => emit('editRequested', item as any)

const handleDelete = (item: PaymentPerInstallment) => emit('deleteRequested', item as any)

const getPayOrderName = (payOrderId: number) => {
  const payOrder = availablePayOrders.value.find(order => order.pk === payOrderId)
  return payOrder ? payOrder.pay_name : '알 수 없음'
}

// 부모 컴포넌트에서 데이터 새로고침을 위한 함수 노출
defineExpose({
  loadData,
})
</script>

<template>
  <CRow class="p-3" style="background: lightyellow">
    <CCol v-if="!availablePayOrders.length" class="text-center py-4 text-grey">
      사용 가능한 납부 회차가 없습니다.
    </CCol>

    <CCol v-else-if="!localPaymentPerInstallmentList.length" class="text-center py-4 text-grey">
      등록된 특별 약정금액이 없습니다.
    </CCol>

    <CCol v-else class="px-5">
      <CRow v-for="item in localPaymentPerInstallmentList" :key="item.pk" class="p-1 text-center">
        <CCol class="text-right">
          <span class="strong">납부 회차</span>
          :
          <u>{{ item.pay_order_info?.pay_name || getPayOrderName(item.pay_order as number) }}</u>
        </CCol>

        <CCol class="text-center">
          <span class="strong">약정금액</span> : <u>{{ numFormat(item.amount as number) }}원</u>
        </CCol>
        <CCol class="text-left">
          <v-btn size="x-small" color="success" class="mr-1" @click="handleEdit(item)">
            수정
          </v-btn>
          <v-btn size="x-small" color="warning" @click="handleDelete(item)"> 삭제 </v-btn>
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>
