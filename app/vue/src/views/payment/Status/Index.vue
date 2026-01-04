<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/payment/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { usePayment } from '@/store/pinia/payment'
import { getToday } from '@/utils/baseMixins'
import type { Project } from '@/store/types/project.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PaymentAuthGuard from '@/components/AuthGuard/PaymentAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import DateChoicer from './components/DateChoicer.vue'
import PaymentStatus from './components/PaymentStatus.vue'
import OverallSummary from './components/OverallSummary.vue'

const date = ref(getToday())
const menu = ref('수납요약')

const excelUrl1 = computed(
  () => `/excel/ledger/paid-status/?project=${project.value}&date=${date.value}`,
)
const excelUrl2 = computed(
  () => `/excel/ledger/overall-sum/?project=${project.value}&date=${date.value}`,
)

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const contStore = useContract()
const fetchOrderGroupList = (proj: number) => contStore.fetchOrderGroupList(proj)

const payStore = usePayment()
const fetchPayOrderList = (proj: number) => payStore.fetchPayOrderList(proj)
const fetchLedgerOverallSummary = (proj: number, date?: string) =>
  payStore.fetchLedgerOverallSummary(proj, date)

const setDate = (d: string) => {
  date.value = d
  if (project.value) {
    // 현재 선택된 메뉴에 따라 필요한 API만 호출
    if (menu.value === '수납요약') {
      payStore.fetchLedgerPaymentStatusByUnitType(project.value, date.value)
    } else if (menu.value === '총괄집계') {
      fetchLedgerOverallSummary(project.value, date.value)
    }
  }
}

const dataSetup = (pk: number) => {
  // 공통 데이터 로드
  fetchOrderGroupList(pk)
  fetchPayOrderList(pk)
  contStore.fetchContAggregate(pk)

  // 현재 선택된 메뉴에 따라 필요한 데이터만 로드
  if (menu.value === '수납요약') {
    payStore.fetchLedgerPaymentStatusByUnitType(pk, date.value)
  } else if (menu.value === '총괄집계') {
    fetchLedgerOverallSummary(pk, date.value)
  }
}

const dataReset = () => {
  contStore.orderGroupList = []
  payStore.paymentStatusByUnitType = []
  payStore.overallSummary = null
  contStore.removeContAggregate()
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

// 메뉴 변경 시 필요한 API 호출
watch(menu, newMenu => {
  if (project.value) {
    if (newMenu === '수납요약') {
      // 수납요약 탭으로 변경 시 새로운 API 호출
      payStore.fetchLedgerPaymentStatusByUnitType(project.value, date.value)
    } else if (newMenu === '총괄집계') {
      // 총괄집계 탭으로 변경 시 필요한 API 호출
      fetchLedgerOverallSummary(project.value, date.value)
    }
  }
})

const loading = ref(true)
onBeforeMount(async () => {
  dataSetup(project.value || projStore.initProjId)
  loading.value = false
})
</script>

<template>
  <PaymentAuthGuard>
    <Loading v-model:active="loading" />
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
          <TableTitleRow
            excel
            :url="excelUrl1"
            filename="차수타입별_수납요약.xls"
            :disabled="!project"
          />
          <PaymentStatus :date="date" />
        </template>
        <template v-else>
          <TableTitleRow excel :url="excelUrl2" filename="총괄집계현황.xls" :disabled="!project" />
          <OverallSummary :date="date" />
        </template>
      </CCardBody>
    </ContentBody>
  </PaymentAuthGuard>
</template>
