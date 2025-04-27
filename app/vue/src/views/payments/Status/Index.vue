<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { navMenu, pageTitle } from '@/views/payments/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import { usePayment } from '@/store/pinia/payment'
import { getToday } from '@/utils/baseMixins'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import DateChoicer from '@/views/payments/Status/components/DateChoicer.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import PaymentStatus from './components/PaymentStatus.vue'
import OverallSummary from './components/OverallSummary.vue'

const date = ref(getToday())
const menu = ref('수납요약')

const excelUrl1 = computed(() => `/excel/paid-status/?project=${project.value}&date=${date.value}`)
const excelUrl2 = computed(() => `/excel/paid-status/?project=${project.value}&date=${date.value}`)

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const fetchIncBudgetList = (proj: number) => projStore.fetchIncBudgetList(proj)

const prDataStore = useProjectData()
const fetchTypeList = (proj: number) => prDataStore.fetchTypeList(proj)

const contStore = useContract()
const fetchOrderGroupList = (proj: number) => contStore.fetchOrderGroupList(proj)
const fetchContSummaryList = (proj: number, date?: string) =>
  contStore.fetchContSummaryList(proj, date)
const fetchContAggregate = (proj: number) => contStore.fetchContAggregate(proj)

const payStore = usePayment()
const fetchPaySumList = (proj: number, date?: string) => payStore.fetchPaySumList(proj, date)
const fetchPayOrderList = (proj: number) => payStore.fetchPayOrderList(proj)

const setDate = (d: string) => {
  date.value = d
  if (project.value) {
    fetchPaySumList(project.value, date.value)
    fetchContSummaryList(project.value, date.value)
  }
}

const dataSetup = (pk: number) => {
  fetchTypeList(pk)
  fetchOrderGroupList(pk)
  fetchContSummaryList(pk)
  fetchIncBudgetList(pk)
  fetchPaySumList(pk)
  fetchPayOrderList(pk)
  fetchContAggregate(pk)
}

const dataReset = () => {
  prDataStore.unitTypeList = []
  contStore.orderGroupList = []
  contStore.contSummaryList = []
  projStore.proIncBudgetList = []
  payStore.paySumList = []
  contStore.removeContAggregate()
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => dataSetup(project.value || projStore.initProjId))
</script>

<template>
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  />

  <ContentBody>
    <CCardBody class="pb-5">
      <DateChoicer @set-date="setDate" class="mb-4" />

      <v-tabs v-model="menu" density="compact">
        <v-tab
          v-for="m in ['수납요약', '총괄집계']"
          :value="m"
          :key="m"
          variant="tonal"
          :active="menu === m"
        >
          {{ m }}
        </v-tab>
      </v-tabs>

      <template v-if="menu === '수납요약'">
        <TableTitleRow excel :url="excelUrl1" :disabled="!project" />
        <PaymentStatus :date="date" />
      </template>
      <template v-else>
        <TableTitleRow excel :url="excelUrl2" :disabled="true" />
        <OverallSummary :date="date" />
      </template>
    </CCardBody>
  </ContentBody>
</template>
