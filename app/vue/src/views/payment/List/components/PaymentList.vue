<script lang="ts" setup>
import { computed } from 'vue'
import { usePayment } from '@/store/pinia/payment'
import { type ProjectCashBook, type PaymentPaid } from '@/store/types/proCash'
import { write_payment } from '@/utils/pageAuth'
import { TableSecondary } from '@/utils/cssMixins'
import Pagination from '@/components/Pagination'
import Payment from './Payment.vue'

const emit = defineEmits(['page-select', 'pay-match'])

defineProps({
  page: { type: Number, required: true },
  project: { type: Number, required: true },
})

const paymentStore = usePayment()
const getPayments = computed(() => paymentStore.legerGetPayments)
const paymentPages = computed(() => paymentStore.ledgerPaymentPages)

const payMatch = (payload: ProjectCashBook) => emit('pay-match', payload)
const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 8%" />
      <col style="width: 9%" />
      <col style="width: 8%" />
      <col style="width: 9%" />
      <col style="width: 14%" />
      <col style="width: 13%" />
      <col style="width: 13%" />
      <col v-if="write_payment" style="width: 6%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell scope="col">거래일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">차수</CTableHeaderCell>
        <CTableHeaderCell scope="col">타입</CTableHeaderCell>
        <CTableHeaderCell scope="col">일련번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">계약자</CTableHeaderCell>
        <CTableHeaderCell scope="col">수납금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">납입회차</CTableHeaderCell>
        <CTableHeaderCell scope="col">수납계좌</CTableHeaderCell>
        <CTableHeaderCell scope="col">입금자</CTableHeaderCell>
        <CTableHeaderCell v-if="write_payment" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Payment
        v-for="payment in getPayments"
        :key="payment.pk"
        :project="project"
        :payment="payment as PaymentPaid"
        @pay-match="payMatch"
      />
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="page"
    :limit="8"
    :pages="paymentPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
