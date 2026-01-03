<script lang="ts" setup>
import { computed } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import { usePayment } from '@/store/pinia/payment'
import type { OverallSummary as QS, OverallSummaryPayOrder as QSPO } from '@/store/types/payment'

defineProps({ date: { type: String, default: '' } })

const payStore = usePayment()
const payOrderList = computed<QSPO[]>(() => (payStore.ledgerOverallSummary as QS)?.pay_orders || [])
const contAggregate = computed(() => (payStore.ledgerOverallSummary as QS)?.aggregate)

const total_cont_amount = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + order.contract_amount, 0),
)
const total_non_cont_amount = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + order.non_contract_amount, 0),
)
const total_collected_amount = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + order.collection.collected_amount, 0),
)
const total_discount_amount = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + order.collection.discount_amount, 0),
)
const total_overdue_fee = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + order.collection.overdue_fee, 0),
)
const total_actual_collected = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + order.collection.actual_collected, 0),
)

const total_due_contract_amount = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.due_period?.contract_amount ?? 0), 0),
)
const total_due_unpaid_amount = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.due_period?.unpaid_amount ?? 0), 0),
)
const total_due_overdue_fee = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.due_period?.overdue_fee ?? 0), 0),
)
const total_due_subtotal = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.due_period?.subtotal ?? 0), 0),
)
const total_not_due_unpaid = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.not_due_unpaid ?? 0), 0),
)
const total_total_unpaid = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.total_unpaid ?? 0), 0),
)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <CTableHead>
      <CTableRow>
        <CTableDataCell :colspan="payOrderList.length ? payOrderList.length + 2 : 12">
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
          <CTableHeaderCell v-for="order in payOrderList" :key="order.pk as number">
            {{ order.pay_name }}
          </CTableHeaderCell>
        </template>
        <template v-else>
          <CTableHeaderCell v-for="i in 10" :key="i">{{ `${i}차 분담금` }}</CTableHeaderCell>
        </template>
        <CTableHeaderCell>합계</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="payOrderList.length">
      <CTableRow class="text-center">
        <CTableDataCell>기본</CTableDataCell>
        <CTableDataCell>약정일</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number">
          {{ order.pay_due_date }}
        </CTableDataCell>
        <CTableDataCell class="text-right"></CTableDataCell>
      </CTableRow>

      <CTableRow>
        <CTableDataCell rowspan="4" class="text-center">계약</CTableDataCell>
        <CTableDataCell class="text-center">
          계약({{ numFormat(contAggregate?.conts_num ?? 0) }})
        </CTableDataCell>

        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.contract_amount ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">{{ numFormat(total_cont_amount) }}</CTableDataCell>
      </CTableRow>

      <CTableRow>
        <CTableDataCell class="text-center">
          미계약({{ numFormat(contAggregate?.non_conts_num ?? 0) }})
        </CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.non_contract_amount ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">{{ numFormat(total_non_cont_amount) }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">
          총계({{ numFormat(contAggregate?.total_units ?? 0) }})
        </CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat((order.contract_amount ?? 0) + (order.non_contract_amount ?? 0)) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(total_cont_amount + total_non_cont_amount) }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">계약율</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.contract_rate ?? 0, 2) }}%
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(contAggregate?.contract_rate ?? 0, 2) }}%
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell rowspan="5" class="text-center">수납</CTableDataCell>
        <CTableDataCell class="text-center">수납액</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.collection?.collected_amount ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(total_collected_amount) }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">할인료</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.collection?.discount_amount ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(total_discount_amount) }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">연체료</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.collection?.overdue_fee ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(total_overdue_fee) }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">실수납액</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.collection?.actual_collected ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(total_actual_collected) }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">수납율</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.collection?.collection_rate ?? 0, 2) }}%
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat((total_actual_collected / total_cont_amount) * 100, 2) }}%
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell rowspan="5" class="text-center">기간도래</CTableDataCell>
        <CTableDataCell class="text-center">약정금액</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.due_period?.contract_amount ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(total_due_contract_amount) }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">미수금</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.due_period?.unpaid_amount ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">{{ numFormat(total_due_unpaid_amount) }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">미수율</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.due_period?.unpaid_rate ?? 0, 2) }}%
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat((total_due_unpaid_amount / total_due_contract_amount) * 100, 2) }}%
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">연체료</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.due_period?.overdue_fee ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">{{ numFormat(total_due_overdue_fee) }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">소계</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.due_period?.subtotal ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">{{ numFormat(total_due_subtotal) }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">기간미도래</CTableDataCell>
        <CTableDataCell class="text-center">미수금</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.not_due_unpaid ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">{{ numFormat(total_not_due_unpaid) }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell rowspan="2" class="text-center">총계</CTableDataCell>
        <CTableDataCell class="text-center">미수금</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.total_unpaid ?? 0) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">{{ numFormat(total_total_unpaid) }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableDataCell class="text-center">미수율</CTableDataCell>
        <CTableDataCell v-for="order in payOrderList" :key="order.pk as number" class="text-right">
          {{ numFormat(order.total_unpaid_rate ?? 0, 2) }}%
        </CTableDataCell>
        <CTableDataCell class="text-right">
          {{
            numFormat(
              total_cont_amount > 0 ? (total_total_unpaid / total_cont_amount) * 100 : 0,
              2,
            )
          }}%
        </CTableDataCell>
      </CTableRow>
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell colspan="13" style="height: 200px; text-align: center">
          [
          <router-link :to="{ name: '납부 회차 등록' }"> 납부 회차 등록</router-link>
          ] >> [ PR 등록 관리 ] > [ 분양 계약 조건 ]에서 데이터를 등록하세요.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
