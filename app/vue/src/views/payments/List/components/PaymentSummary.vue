<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import type { UnitType } from '@/store/types/project.ts'
import { numFormat } from '@/utils/baseMixins'
import { usePayment } from '@/store/pinia/payment'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'

defineProps({ project: { type: Number, default: null } })

const proStore = useProject()
const budgetList = computed(() => proStore.proIncBudgetList)

const contStore = useContract()
const contSum = computed(() => contStore.contSummaryList)

const proDataStore = useProjectData()
const unitTypeList = computed<UnitType[]>(() => proDataStore.unitTypeList)

const paymentStore = usePayment()
const paySumList = computed(() => paymentStore.paySumList)

const getTotalBudget = computed(() =>
  budgetList.value.map(b => b.budget).reduce((x, y) => x + y, 0),
)

const getTotalCont = computed(() =>
  contSum.value.map(s => s.price_sum || 0).reduce((x, y) => x + y, 0),
)

const getTotalPaid = computed(() =>
  paySumList.value.map(b => b.paid_sum).reduce((x, y) => x + y, 0),
)

const getBudgetByType = (ut: number) =>
  budgetList.value
    .filter(b => b.unit_type === ut)
    .map(b => b.budget)
    .reduce((x, y) => x + y, 0)

const getContByType = (ut: number) =>
  contSum.value
    .filter(s => s.unit_type === ut)
    .map(s => s.price_sum || 0)
    .reduce((x, y) => x + y, 0)

const getPaidByType = (ut: number) =>
  paySumList.value
    .filter(b => b.unit_type === ut)
    .map(b => b.paid_sum)
    .reduce((x, y) => x + y, 0)
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
      <CTableRow v-for="type in unitTypeList" :key="type.pk" class="text-right">
        <CTableHeaderCell class="text-left pl-5">
          <CIcon name="cib-node-js" :style="{ color: type.color }" size="sm" class="mr-1" />
          {{ type.name }}
        </CTableHeaderCell>
        <CTableDataCell>
          {{ numFormat(getBudgetByType(type.pk as number)) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(getContByType(type.pk as number)) }}
        </CTableDataCell>
        <CTableDataCell class="text-primary">
          {{ numFormat(getPaidByType(type.pk as number)) }}
        </CTableDataCell>
        <CTableDataCell class="text-danger">
          {{ numFormat(getContByType(type.pk as number) - getPaidByType(type.pk as number)) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(getBudgetByType(type.pk as number) - getContByType(type.pk as number)) }}
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
