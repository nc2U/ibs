<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { usePayment } from '@/store/pinia/payment'
import { numFormat } from '@/utils/baseMixins'

defineProps({
  date: { type: String, default: '' },
})

const payStore = usePayment()
const payOrderList = computed(() => payStore.payOrderList)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <CTableHead>
      <CTableRow>
        <CTableDataCell :colspan="payOrderList.length + 1">
          <strong>
            <CIcon name="cilFolderOpen" />
            총괄 집계 현황
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 현재 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-center" align="middle">
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>구분</CTableHeaderCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk">
          {{ order.pay_name }}
        </CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow>
        <CTableDataCell class="text-center">기본</CTableDataCell>
        <CTableDataCell class="text-center">약정일</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell rowspan="4" class="text-center">계약</CTableDataCell>
        <CTableDataCell class="text-center">계약(000)</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">미계약(000)</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">총계(000)</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">계약율(000)</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell rowspan="5" class="text-center">수납</CTableDataCell>
        <CTableDataCell class="text-center">수납액</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">할인료</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">연체료</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">실수납액</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">수납율</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell rowspan="5" class="text-center">기간도래</CTableDataCell>
        <CTableDataCell class="text-center">약정금액</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">미수금</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">미수율</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">연체료</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">소계</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">기간미도래</CTableDataCell>
        <CTableDataCell class="text-center">미수금</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell rowspan="2" class="text-center">총</CTableDataCell>
        <CTableDataCell class="text-center">미수금</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">미수율</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
