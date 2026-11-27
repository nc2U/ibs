<script lang="ts" setup>
import { computed } from 'vue'
import { usePayment } from '@/store/pinia/payment.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import type { ContractPaymentPatchPayload } from '@/store/types/payment.ts'
import Pagination from '@/components/Pagination'
import Payment from './Payment.vue'

type PayMatchPayload = ContractPaymentPatchPayload & { trans_id: number | null }

defineProps<{
  page: number
  project: number
}>()

const emit = defineEmits<{
  (e: 'page-select', page: number): void
  (e: 'pay-match', payload: PayMatchPayload): void
}>()

const paymentStore = usePayment()
const getPayments = computed(() => paymentStore.ledgerGetPayments)
const paymentPages = computed(() => paymentStore.ledgerPaymentPages)

const payMatch = (payload: PayMatchPayload) => emit('pay-match', payload)
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
      <col style="width: 6%" />
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
        <CTableHeaderCell scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Payment
        v-for="payment in getPayments"
        :key="payment.pk"
        :project="project"
        :payment="payment"
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
