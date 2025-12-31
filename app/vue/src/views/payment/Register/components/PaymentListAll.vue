<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { type Contract } from '@/store/types/contract'
import { type AllPayment } from '@/store/types/payment'
import { type ProjectCashBook } from '@/store/types/proCash'
import { numFormat } from '@/utils/baseMixins'
import { write_payment } from '@/utils/pageAuth'
import { TableSecondary } from '@/utils/cssMixins'
import Payment from '@/views/payments/Register/components/Payment.vue'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, default: null },
  paymentList: { type: Array as PropType<AllPayment[]>, default: () => [] },
  paymentId: { type: String, default: '' },
})

const emit = defineEmits(['on-update', 'on-delete'])

const paymentSum = computed(() => {
  return props.paymentList.length !== 0
    ? props.paymentList.map((p: AllPayment) => p.income).reduce((x: number, y: number) => x + y, 0)
    : 0
})

const onUpdate = (payload: ProjectCashBook) => emit('on-update', payload)
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
      <col v-if="write_payment" style="width: 10%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center">
        <CTableHeaderCell>수납일자</CTableHeaderCell>
        <CTableHeaderCell>납부회차</CTableHeaderCell>
        <CTableHeaderCell>수납금액</CTableHeaderCell>
        <CTableHeaderCell>수납계좌</CTableHeaderCell>
        <CTableHeaderCell>입금자명</CTableHeaderCell>
        <CTableHeaderCell v-if="write_payment">비고</CTableHeaderCell>
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
          {{ numFormat(paymentSum) }}
        </CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableHead>
  </CTable>
</template>
