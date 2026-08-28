<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'
import { type Contract } from '@/store/types/contract'
import { type OriginPayment } from '@/store/types/payment'
import Payment from './Payment.vue'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, default: null },
  paymentList: { type: Array as PropType<OriginPayment[]>, default: () => [] },
  paymentId: { type: String, default: '' },
})

const emit = defineEmits(['on-update', 'on-delete'])

const { can, PERM } = usePerms()
const canPaymentManage = computed(
  () => can(PERM.CONTRACT_CREATE) || can(PERM.CONTRACT_UPDATE) || can(PERM.PAYMENT_DELETE),
)

const paymentSum = computed(() => {
  return props.paymentList.length !== 0
    ? props.paymentList
        .map((p: OriginPayment) => p.amount! as number)
        .reduce((x: number, y: number) => x + y, 0)
    : 0
})

const onUpdate = (bankTransactionId: number, payload: any) =>
  emit('on-update', bankTransactionId, payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 16%" />
      <col style="width: 18%" />
      <col style="width: 16%" />
      <col style="width: 22%" />
      <col style="width: 18%" />
      <col v-if="canPaymentManage" style="width: 10%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center border-top">
        <CTableHeaderCell>수납일자</CTableHeaderCell>
        <CTableHeaderCell>납부회차</CTableHeaderCell>
        <CTableHeaderCell>수납금액</CTableHeaderCell>
        <CTableHeaderCell>수납계좌</CTableHeaderCell>
        <CTableHeaderCell>입금자명</CTableHeaderCell>
        <CTableHeaderCell v-if="canPaymentManage">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="contract">
      <Payment
        v-for="pay in paymentList"
        :key="pay.pk"
        :contract="contract"
        :payment-id="paymentId"
        :payment="pay"
        @on-update="onUpdate"
        @on-delete="onDelete"
      />
    </CTableBody>

    <CTableHead>
      <CTableRow class="text-right">
        <CTableHeaderCell :color="TableSecondary" class="text-center"> 합계</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>
          {{ numFormat(paymentSum as number) }}
        </CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableHead>
  </CTable>
</template>
