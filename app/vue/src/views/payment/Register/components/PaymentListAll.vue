<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { numFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Contract } from '@/store/types/contract.ts'
import type { ContractPaymentPayload, OriginPayment } from '@/store/types/payment.ts'
import Payment from './Payment.vue'

const props = withDefaults(
  defineProps<{
    contract?: Contract | null
    paymentList?: OriginPayment[]
    paymentId?: string
  }>(),
  {
    contract: null,
    paymentList: () => [],
    paymentId: '',
  },
)

const emit = defineEmits<{
  (
    e: 'on-update',
    bankTransactionId: number,
    payload: ContractPaymentPayload,
    done?: (ok: boolean) => void,
  ): void
  (e: 'on-delete', bankTransactionId: number, done?: (ok: boolean) => void): void
}>()

const { can, PERM } = usePerms()
const canPaymentManage = computed(() => can(PERM.PAYMENT_UPDATE) || can(PERM.PAYMENT_DELETE))

const paymentSum = computed(() => {
  return props.paymentList.length !== 0
    ? props.paymentList
        .map((p: OriginPayment) => p.amount || 0)
        .reduce((x: number, y: number) => x + y, 0)
    : 0
})

const onUpdate = (
  bankTransactionId: number,
  payload: ContractPaymentPayload,
  done?: (ok: boolean) => void,
) => emit('on-update', bankTransactionId, payload, done)
const onDelete = (bankTransactionId: number, done?: (ok: boolean) => void) =>
  emit('on-delete', bankTransactionId, done)
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
      <CTableRow class="text-end">
        <CTableHeaderCell :color="TableSecondary" class="text-center"> 합계</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>
          {{ numFormat(paymentSum) }}
        </CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell v-if="canPaymentManage"></CTableHeaderCell>
      </CTableRow>
    </CTableHead>
  </CTable>
</template>
