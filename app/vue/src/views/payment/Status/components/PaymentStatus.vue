<script lang="ts" setup>
import { computed, onMounted, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import type { Project } from '@/store/types/project.ts'
import { useProject } from '@/store/pinia/project'
import { usePayment } from '@/store/pinia/payment'
import { TableSecondary } from '@/utils/cssMixins'

const props = defineProps({
  date: { type: String, default: '' },
})

const proStore = useProject()
const paymentStore = usePayment()
const paymentStatusData = computed<any[]>(() => paymentStore.ledgerPaymentStatusByUnitType)

// Fetch payment status data on component mount
onMounted(async () => {
  const currentProject = (proStore.project as Project)?.pk
  if (currentProject) {
    await paymentStore.fetchLedgerPaymentStatusByUnitType(currentProject, props.date)
  }
})

// Watch date changes and refetch data
watch(
  () => props.date,
  async newDate => {
    const currentProject = (proStore.project as Project)?.pk
    if (currentProject) {
      await paymentStore.fetchLedgerPaymentStatusByUnitType(currentProject, newDate)
    }
  },
)

// 차수별 첫번째 타입인지 확인
const isFirstTypeInOrderGroup = (item: any) => {
  const sameOrderGroupItems = paymentStatusData.value.filter(
    d => d.order_group_id === item.order_group_id,
  )
  return sameOrderGroupItems[0]?.unit_type_id === item.unit_type_id
}

// 차수별 타입 수
const getUnitTypeCountByOrderGroup = (orderGroupId: number) => {
  return paymentStatusData.value.filter(d => d.order_group_id === orderGroupId).length
}

// 총계 계산
const totals = computed(() => ({
  totalSalesAmount: paymentStatusData.value.reduce((sum, item) => sum + item.total_sales_amount, 0),
  totalPlannedUnits: paymentStatusData.value.reduce((sum, item) => sum + item.planned_units, 0),
  totalContractUnits: paymentStatusData.value.reduce((sum, item) => sum + item.contract_units, 0),
  totalNonContractUnits: paymentStatusData.value.reduce(
    (sum, item) => sum + item.non_contract_units,
    0,
  ),
  totalContractAmount: paymentStatusData.value.reduce((sum, item) => sum + item.contract_amount, 0),
  totalPaidAmount: paymentStatusData.value.reduce((sum, item) => sum + item.paid_amount, 0),
  totalUnpaidAmount: paymentStatusData.value.reduce((sum, item) => sum + item.unpaid_amount, 0),
  totalNonContractAmount: paymentStatusData.value.reduce(
    (sum, item) => sum + item.non_contract_amount,
    0,
  ),
  totalBudget: paymentStatusData.value.reduce((sum, item) => sum + item.total_budget, 0),
}))
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 7%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 7%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="9">
          <strong>
            <CIcon name="cilFolderOpen" />
            차수 및 타입별 수납 요약
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 현재 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-center" align="middle">
        <CTableHeaderCell rowspan="2">차수</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">타입</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">전체 매출액</CTableHeaderCell>
        <CTableHeaderCell colspan="4">계약 현황</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">미계약 세대(실)수</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">미계약 금액</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">합 계</CTableHeaderCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>계약 세대(실)수</CTableHeaderCell>
        <CTableHeaderCell>계약 금액</CTableHeaderCell>
        <CTableHeaderCell>실수납 금액</CTableHeaderCell>
        <CTableHeaderCell>미수 금액</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="paymentStatusData.length">
      <CTableRow
        v-for="item in paymentStatusData"
        :key="`${item.order_group_id}-${item.unit_type_id}`"
        class="text-right"
      >
        <CTableDataCell
          v-if="isFirstTypeInOrderGroup(item)"
          :rowspan="getUnitTypeCountByOrderGroup(item.order_group_id)"
          class="text-center"
          :color="TableSecondary"
        >
          <!-- 차수명 -->
          {{ item.order_group_name }}
        </CTableDataCell>
        <CTableDataCell class="text-left pl-4">
          <v-icon icon="mdi mdi-square" :color="item.unit_type_color" size="sm" />
          <!-- 타입명 -->
          {{ item.unit_type_name }}
        </CTableDataCell>
        <!-- 전체 매출액 -->
        <CTableDataCell>
          {{ numFormat(item.total_sales_amount) }}
        </CTableDataCell>
        <CTableDataCell>
          <!-- 계약 세대수 -->
          {{ numFormat(item.contract_units) }}
        </CTableDataCell>
        <CTableDataCell>
          <!-- 계약 금액 -->
          {{ numFormat(item.contract_amount) }}
        </CTableDataCell>
        <CTableDataCell>
          <!-- 실수납 금액 -->
          {{ numFormat(item.paid_amount) }}
        </CTableDataCell>
        <CTableDataCell>
          <!-- 미수 금액 -->
          {{ numFormat(item.unpaid_amount) }}
        </CTableDataCell>
        <!-- 미계약 세대수 -->
        <CTableDataCell>{{ numFormat(item.non_contract_units) }}</CTableDataCell>
        <CTableDataCell
          :class="{
            'text-danger': item.non_contract_amount < 0,
          }"
        >
          <!-- 미계약 금액 -->
          {{ numFormat(item.non_contract_amount) }}
        </CTableDataCell>
        <!-- 합계 -->
        <CTableDataCell>{{ numFormat(item.total_budget) }}</CTableDataCell>
      </CTableRow>
    </CTableBody>

    <CTableBody v-else>
      <CTableRow class="text-center text-danger" style="height: 200px">
        <CTableDataCell colspan="10">
          [
          <router-link :to="{ name: '수입 예산 등록' }"> 수입 예산 등록</router-link>
          ] >> [ PR 등록 관리 ] > [ 예산 등록 관리 ]에서 데이터를 등록하세요.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>

    <CTableHead>
      <CTableRow class="text-right" :color="TableSecondary">
        <CTableHeaderCell colspan="2" class="text-center"> 총 계</CTableHeaderCell>
        <CTableHeaderCell class="text-right">
          <!-- 전체 매출액 합계 -->
          {{ numFormat(totals.totalSalesAmount) }}
        </CTableHeaderCell>
        <!-- 계약 세대(실)수 합계 -->
        <CTableHeaderCell>{{ numFormat(totals.totalContractUnits) }}</CTableHeaderCell>
        <CTableHeaderCell>
          <!-- 계약 금액 합계 -->
          {{ numFormat(totals.totalContractAmount) }}
        </CTableHeaderCell>
        <CTableHeaderCell>
          <!-- 실수납 금액 합계 -->
          {{ numFormat(totals.totalPaidAmount) }}
        </CTableHeaderCell>
        <CTableHeaderCell>
          <!-- 미수 금액 합계 -->
          {{ numFormat(totals.totalUnpaidAmount) }}
        </CTableHeaderCell>
        <!-- 미계약 세대(실)수 합계 -->
        <CTableHeaderCell>{{ numFormat(totals.totalNonContractUnits) }}</CTableHeaderCell>
        <CTableHeaderCell>
          <!-- 미계약 금액 합계 -->
          {{ numFormat(totals.totalNonContractAmount) }}
        </CTableHeaderCell>
        <!-- 총계 -->
        <CTableHeaderCell>{{ numFormat(totals.totalBudget) }}</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
  </CTable>
</template>
