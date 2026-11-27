<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/payment/_menu/headermixin.ts'
import { useProject } from '@/store/pinia/project.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { usePayment } from '@/store/pinia/payment.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { getToday } from '@/utils/baseMixins.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PaymentAuthGuard from '@/components/AuthGuard/PaymentAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import DateChoicer from './components/DateChoicer.vue'
import PaymentStatus from './components/PaymentStatus.vue'
import OverallSummary from './components/OverallSummary.vue'

const { can, PERM } = usePerms()
const canPaymentRead = computed(() => can(PERM.PAYMENT_READ))

const date = ref(getToday())
const menu = ref('수납요약')

const excelUrl1 = computed(() =>
  project.value
    ? `/excel/ledger/paid-status/?project=${project.value}&date=${encodeURIComponent(date.value || '')}`
    : '',
)
const excelUrl2 = computed(() =>
  project.value
    ? `/excel/ledger/overall-sum/?project=${project.value}&date=${encodeURIComponent(date.value || '')}`
    : '',
)

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const contStore = useContract()
const fetchOrderGroupList = (proj: number) => contStore.fetchOrderGroupList(proj)

const payStore = usePayment()
const fetchPayOrderList = (proj: number) => payStore.fetchPayOrderList(proj)
const fetchLedgerOverallSummary = (proj: number, d?: string) =>
  payStore.fetchLedgerOverallSummary(proj, d)

const fetchTabData = async (proj: number) => {
  if (menu.value === '수납요약') {
    await payStore.fetchLedgerPaymentStatusByUnitType(proj, date.value)
  } else {
    await fetchLedgerOverallSummary(proj, date.value)
  }
}

const setDate = (d: string) => {
  date.value = d
  if (project.value && canPaymentRead.value) {
    fetchTabData(project.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    fetchOrderGroupList(pk),
    fetchPayOrderList(pk),
    contStore.fetchContAggregate(pk),
    fetchTabData(pk),
  ])
}

const dataReset = () => {
  contStore.orderGroupList = []
  payStore.payOrderList = []
  payStore.ledgerPaymentStatusByUnitType = []
  payStore.ledgerOverallSummary = null
  contStore.removeContAggregate()
}

// 메뉴 변경 시 필요한 API 호출
watch(menu, () => {
  if (project.value && canPaymentRead.value) {
    fetchTabData(project.value)
  }
})

const loading = ref(false)
watch(
  [project, canPaymentRead],
  async ([newProj, hasRead], [oldProj, oldRead]) => {
    if (newProj !== oldProj || hasRead !== oldRead) {
      dataReset()
      if (newProj && hasRead) {
        loading.value = true
        try {
          await dataSetup(newProj)
        } finally {
          loading.value = false
        }
      }
    }
  },
  { immediate: true },
)
</script>

<template>
  <PaymentAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

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
            filename="차수타입별_수납요약.xlsx"
            :disabled="!project"
          />
          <PaymentStatus :date="date" />
        </template>
        <template v-else>
          <TableTitleRow excel :url="excelUrl2" filename="총괄집계현황.xlsx" :disabled="!project" />
          <OverallSummary :date="date" />
        </template>
      </CCardBody>
    </ContentBody>
  </PaymentAuthGuard>
</template>
