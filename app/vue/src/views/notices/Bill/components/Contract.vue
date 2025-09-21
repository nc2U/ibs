<script lang="ts" setup>
import { ref, computed, watch, onMounted, type PropType } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { useContract } from '@/store/pinia/contract'
import { type Contract, type ContractPaymentPlan } from '@/store/types/contract'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
  page: { type: Number, default: 1 },
  nowOrder: { type: Number, default: null },
  allChecked: { type: Boolean, default: false },
})

const emit = defineEmits(['on-cont-chk'])

const checked = ref(false)
const contractStore = useContract()

// Payment plan data from API
const paymentPlan = ref<ContractPaymentPlan>([])
const isLoadingPaymentPlan = ref(false)

// Fetch payment plan for contract
const fetchPaymentPlan = async () => {
  if (!props.contract?.pk) {
    paymentPlan.value = []
    return
  }

  try {
    isLoadingPaymentPlan.value = true
    paymentPlan.value = await contractStore.fetchContractPaymentPlan(props.contract.pk)
  } catch (error) {
    console.error('Failed to fetch payment plan:', error)
    paymentPlan.value = []
  } finally {
    isLoadingPaymentPlan.value = false
  }
}

// 정확한 납부 완료 여부 계산 (payment plan 기반)
const paidCompleted = computed(() => {
  const nowOrderCode: number = props.nowOrder || 2
  const totalPaid = props.contract?.total_paid || 0

  if (!paymentPlan.value.length || totalPaid === 0) {
    return false
  }

  // 현재 회차까지의 약정금 총액 계산
  let dueAmountUpToNow = 0
  for (const planItem of paymentPlan.value) {
    if (planItem.installment_order.pay_code <= nowOrderCode) {
      dueAmountUpToNow += planItem.amount
    }
  }

  // 납부 총액이 현재 회차까지의 약정금 이상이면 완납
  return totalPaid >= dueAmountUpToNow
})

// 실제 완납된 회차명 계산 (payment plan 기반)
const get_paid_name = computed(() => {
  const totalPaid = props.contract?.total_paid || 0

  if (!paymentPlan.value.length || totalPaid === 0) {
    return '계약금미납'
  }

  let cumulativeAmount = 0
  let lastCompletedOrder: any = null

  // 납부 총액으로 어느 회차까지 완납되었는지 계산
  for (const planItem of paymentPlan.value) {
    cumulativeAmount += planItem.amount

    if (totalPaid >= cumulativeAmount) {
      lastCompletedOrder = planItem.installment_order
    } else {
      break
    }
  }

  return lastCompletedOrder ? lastCompletedOrder.pay_name : '계약금미납'
})

// Watch for contract changes and fetch payment plan
watch(() => props.contract?.pk, fetchPaymentPlan, { immediate: true })

watch(props, (n, o) => {
  if (!paidCompleted.value) {
    checked.value = !n.allChecked
    contChk(n.contract?.pk as number)
  }
  if (n.page !== o.page) checked.value = false
})

// Initialize payment plan on component mount
onMounted(() => {
  fetchPaymentPlan()
})

const contChk = (ctorPk: number) => {
  checked.value = !checked.value
  emit('on-cont-chk', { chk: checked.value, pk: ctorPk })
}
</script>

<template>
  <CTableRow v-if="contract" class="text-center" :color="checked ? 'secondary' : ''">
    <CTableDataCell>
      <CFormCheck
        :id="'check_' + contract.pk"
        v-model="checked"
        :value="contract.pk"
        :disabled="paidCompleted"
        label="선택"
        @change="contChk(contract.pk as number)"
      />
    </CTableDataCell>

    <CTableDataCell>
      {{ contract.order_group_desc.name }}
    </CTableDataCell>

    <CTableDataCell class="text-left">
      <CIcon
        name="cibDiscover"
        :style="'color:' + contract.unit_type_desc.color"
        size="sm"
        class="mr-1"
      />
      {{ contract.unit_type_desc.name }}
    </CTableDataCell>
    <CTableDataCell>
      {{ contract.serial_number }}
    </CTableDataCell>
    <CTableDataCell :class="contract.key_unit?.houseunit ? '' : 'text-danger'" class="text-left">
      {{ contract.key_unit?.houseunit ? contract.key_unit.houseunit.__str__ : '미정' }}
    </CTableDataCell>
    <CTableDataCell>
      <router-link
        :to="{
          name: '계약 등록 수정',
          query: { contractor: contract.contractor?.pk },
        }"
      >
        {{ contract.contractor?.name }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      <router-link :to="{ name: '건별 수납 관리', query: { contract: contract.pk } }">
        {{ numFormat(contract?.total_paid || 0) }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>
      <span v-if="isLoadingPaymentPlan" class="text-muted">계산중...</span>
      <template v-else>
        <span v-if="paidCompleted" class="text-success">완납중</span>
        <span v-else class="text-danger">미납중</span>
        ({{ get_paid_name }})
      </template>
    </CTableDataCell>
    <CTableDataCell>{{ contract.contractor?.contract_date }}</CTableDataCell>
  </CTableRow>
</template>
