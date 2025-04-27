<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { usePayment } from '@/store/pinia/payment'
import type { PayOrder } from '@/store/types/payment'
import { numFormat } from '@/utils/baseMixins'
import { useContract } from '@/store/pinia/contract'

defineProps({
  date: { type: String, default: '' },
})

const payStore = usePayment()
const payOrderList = computed<PayOrder[]>(() => payStore.payOrderList)

const contStore = useContract()
const contAggregate = computed(() => contStore.contAggregate)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <CTableHead>
      <CTableRow>
        <CTableDataCell :colspan="payOrderList.length ? payOrderList.length + 1 : 11">
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
        <template v-if="payOrderList.length">
          <CTableHeaderCell v-for="order in payOrderList" :key="order.pk">
            {{ order.pay_name }}
          </CTableHeaderCell>
        </template>
        <template v-else>
          <CTableHeaderCell v-for="i in 10" :key="i">{{ `${i}차 분담금` }}</CTableHeaderCell>
        </template>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="payOrderList.length">
      <CTableRow class="text-center">
        <CTableDataCell>기본</CTableDataCell>
        <CTableDataCell>약정일</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk">
          {{ order.pay_due_date }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell rowspan="4" class="text-center">계약</CTableDataCell>
        <CTableDataCell class="text-center">
          계약({{ numFormat(contAggregate?.conts_num ?? 0) }})
        </CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">
          미계약({{ numFormat(contAggregate?.non_conts_num ?? 0) }})
        </CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">
          총계({{ numFormat(contAggregate?.total_units ?? 0) }})
        </CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">계약율</CTableDataCell>
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
        <CTableDataCell rowspan="2" class="text-center">총계</CTableDataCell>
        <CTableDataCell class="text-center">미수금</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">미수율</CTableDataCell>
        <CTableHeaderCell v-for="order in payOrderList" :key="order.pk"></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell colspan="12" style="height: 200px; text-align: center">
          [
          <router-link :to="{ name: '납부 회차 등록' }"> 납부 회차 등록</router-link>
          ] >> [ 현장 등록 관리 ] > [ 분양 계약 조건 ]에서 데이터를 등록하세요.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
