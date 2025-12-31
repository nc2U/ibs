<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins'
import { usePayment } from '@/store/pinia/payment'

defineProps({ project: { type: Number, default: null } })

const paymentStore = usePayment()
const paymentSummaryList = computed(() => paymentStore.paymentSummaryList)

const getTotalBudget = computed(() =>
  paymentSummaryList.value.reduce((sum, item) => sum + item.total_budget, 0),
)

const getTotalCont = computed(() =>
  paymentSummaryList.value.reduce((sum, item) => sum + item.total_contract_amount, 0),
)

const getTotalPaid = computed(() =>
  paymentSummaryList.value.reduce((sum, item) => sum + item.total_paid_amount, 0),
)
</script>

<template>
  <CTable hover responsive bordered class="mt-3">
    <CTableHead class="text-center" :color="TableSecondary">
      <CTableRow align="middle">
        <CTableHeaderCell>타 입</CTableHeaderCell>
        <CTableHeaderCell>총 매출예산(A)</CTableHeaderCell>
        <CTableHeaderCell>총 분양금액(B)</CTableHeaderCell>
        <CTableHeaderCell>총 수납금액(C)</CTableHeaderCell>
        <CTableHeaderCell>미 수납금액(B-C)</CTableHeaderCell>
        <CTableHeaderCell>미 분양금액(A-B)</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="project">
      <CTableRow v-for="item in paymentSummaryList" :key="item.unit_type_id" class="text-right">
        <CTableHeaderCell class="text-left pl-5">
          <CIcon
            name="cib-node-js"
            :style="{ color: item.unit_type_color }"
            size="sm"
            class="mr-1"
          />
          {{ item.unit_type_name }}
        </CTableHeaderCell>
        <CTableDataCell>
          {{ numFormat(item.total_budget) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(item.total_contract_amount) }}
        </CTableDataCell>
        <CTableDataCell class="text-primary">
          {{ numFormat(item.total_paid_amount) }}
        </CTableDataCell>
        <CTableDataCell class="text-danger">
          {{ numFormat(item.unpaid_amount) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(item.unsold_amount) }}
        </CTableDataCell>
      </CTableRow>

      <CTableRow class="text-right" color="light">
        <CTableHeaderCell class="text-center">합 계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(getTotalBudget) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(getTotalCont) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(getTotalPaid) }}</CTableHeaderCell>
        <CTableHeaderCell>
          {{ numFormat(getTotalCont - getTotalPaid) }}
        </CTableHeaderCell>
        <CTableHeaderCell>
          {{ numFormat(getTotalBudget - getTotalCont) }}
        </CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
