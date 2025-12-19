<script lang="ts" setup>
import Cookies from 'js-cookie'
import { ref, computed, onBeforeMount } from 'vue'
import { useProject } from '@/store/pinia/project'
import { useProLedger } from '@/store/pinia/proLedger'
import { getToday } from '@/utils/baseMixins'
import { pageTitle, navMenu } from '@/views/proLedger/_menu/headermixin'
import type { Project } from '@/store/types/project.ts'
import type { ProCalculated } from '@/store/types/proLedger'
import { useDownload } from '@/utils/useDownload.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProLedgerAuthGuard from '@/components/AuthGuard/ProLedgerAuthGuard.vue'
import DateChoicer from '@/views/proLedger/Status/components/DateChoicer.vue'
import TabSelect from '@/views/proLedger/Status/components/TabSelect.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import StatusByAccount from '@/views/proLedger/Status/components/StatusByAccount.vue'
import CashListByDate from '@/views/proLedger/Status/components/CashListByDate.vue'
import SummaryForBudget from '@/views/proLedger/Status/components/SummaryForBudget.vue'
import Calculated from '@/views/comCash/Status/components/Calculated.vue'

const date = ref(getToday())
const direct = ref('0')
const isBalance = ref<'' | 'true'>('true')
const compName = ref('StatusByAccount')

const { downloadExcel } = useDownload()
const handleDownload = (url: string, fileName: string) => {
  downloadExcel(url, fileName)
}

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const fetchStatusOutBudgetList = (proj: number) => projStore.fetchStatusOutBudgetList(proj)

const patchStatusOutBudget = (payload: {
  pk: number
  project: number
  budget?: number
  revised_budget?: number
}) => projStore.patchStatusOutBudget(payload)

const fetchExecAmountList = (project: number, date?: string) =>
  projStore.fetchExecAmountList(project, date)

const pLedgerStore = useProLedger()
const fetchProAllAccD2List = () => pLedgerStore.fetchProAllAccD2List()
const fetchProAllAccD3List = () => pLedgerStore.fetchProAllAccD3List()
const fetchProBankAccList = (proj: number) => pLedgerStore.fetchProBankAccList(proj)

const fetchBalanceByAccList = (payload: {
  project: number
  direct?: string
  date?: string
  is_balance?: '' | 'true'
}) => pLedgerStore.fetchBalanceByAccList(payload)
const fetchDateCashBookList = (payload: { project: number; date: string }) =>
  pLedgerStore.fetchDateCashBookList(payload)

const createProLedgerCalc = (payload: ProCalculated) => pLedgerStore.createProLedgerCalc(payload)
const patchProLedgerCalc = (payload: ProCalculated) => pLedgerStore.patchProLedgerCalc(payload)
const fetchProLedgerCalc = (proj: number) => pLedgerStore.fetchProLedgerCalc(proj)
const fetchProLastDeal = (proj: number) => pLedgerStore.fetchProLastDeal(proj)

const proCalculated = computed(() => pLedgerStore.proCalculated) // 최종 정산 일자
const proLastDealDate = computed(() => pLedgerStore.proLastDealDate) // 최종 거래 일자

const isCalculated = computed(
  () =>
    !!proCalculated.value &&
    proCalculated.value.calculated >= (proLastDealDate.value?.deal_date ?? ''),
) // 최종 정산 일자 이후에 거래 기록이 없음 === true

const checkBalance = () => {
  const payload = {
    project: project.value as number,
    calculated: proLastDealDate.value?.deal_date as string,
  }
  if (!!proCalculated.value) patchProLedgerCalc({ ...{ pk: proCalculated.value.pk }, ...payload })
  else createProLedgerCalc(payload)
}

const revised = ref(1)
const updateRevised = (isRevised: number) => (revised.value = isRevised)

const excelUrl = computed(() => {
  const comp = compName.value
  const pj = project.value
  const dr = direct.value
  const dt = date.value
  let url = ''
  if (comp === 'StatusByAccount')
    url = `/excel/p-balance/?project=${pj}&date=${dt}&bank_account__directpay=${dr}`
  else if (comp === 'CashListByDate') url = `/excel/p-daily-cash/?project=${pj}&date=${dt}`
  else if (comp === 'SummaryForBudget')
    url = `/excel/p-budget/?project=${pj}&date=${dt}&revised=${revised.value}`
  return `${url}`
})

const cashFlowUrl = computed(
  () =>
    `/excel/cash-flow-form/?project=${project.value}&date=${date.value}&revised=${revised.value}`,
)

const comp: { [key: number]: string } = {
  1: 'StatusByAccount',
  2: 'CashListByDate',
  3: 'SummaryForBudget',
}

const filename = computed(() => {
  switch (compName.value) {
    case 'StatusByAccount':
      return '계좌별_자금현황.xlsx'
    case 'CashListByDate':
      return '당일_입출금내역.xlsx'
    case 'SummaryForBudget':
      return '예산대비_집계.xlsx'
    default:
      return ''
  }
})

const showTab = (num: number) => {
  compName.value = comp[num]
  Cookies.set('proLedgerStatus', `${num}`)
}

const setDate = (dt: string) => {
  date.value = dt
  if (project.value) {
    fetchStatusOutBudgetList(project.value as number)
    fetchExecAmountList(project.value as number, dt)
    fetchBalanceByAccList({ project: project.value as number, date: dt })
    fetchDateCashBookList({ project: project.value as number, date: dt })
  }
}

const patchBudget = (pk: number, budget: number, isRevised: boolean) => {
  if (project.value) {
    if (!isRevised) patchStatusOutBudget({ project: project.value as number, pk, budget })
    else patchStatusOutBudget({ project: project.value as number, pk, revised_budget: budget })
  }
}

const isExistBalance = (val: 'true' | '') => {
  isBalance.value = val ? 'true' : ''
  if (project.value) {
    fetchBalanceByAccList({
      project: project.value as number,
      direct: direct.value,
      is_balance: isBalance.value,
      date: date.value,
    })
  }
}

const directBalance = (val: boolean) => {
  isBalance.value = ''
  direct.value = val ? 'i' : '0'
  if (project.value)
    fetchBalanceByAccList({
      project: project.value as number,
      direct: direct.value,
      is_balance: isBalance.value,
      date: date.value,
    })
}

const dataSetup = (pk: number) => {
  fetchStatusOutBudgetList(pk)
  fetchExecAmountList(pk, date.value)
  fetchProBankAccList(pk)
  fetchBalanceByAccList({ project: pk, date: date.value, is_balance: 'true' })
  fetchDateCashBookList({ project: pk, date: date.value })
  fetchProLedgerCalc(pk)
  fetchProLastDeal(pk)
}

const dataReset = () => {
  projStore.statusOutBudgetList = []
  projStore.execAmountList = []
  pLedgerStore.proBankAccountList = []
  pLedgerStore.balanceByAccList = []
  pLedgerStore.proDateCashBook = []
  pLedgerStore.proLedgerCalc = []
  pLedgerStore.proLastDeal = []
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await fetchProAllAccD2List()
  await fetchProAllAccD3List()
  dataSetup(project.value || projStore.initProjId)
  compName.value = comp[Number(Cookies.get('proLedgerStatus') ?? 1)]
  loading.value = false
})
</script>

<template>
  <ProLedgerAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />
    <ContentBody>
      <CCardBody class="pb-5">
        <DateChoicer @set-date="setDate" />

        <TabSelect @tab-select="showTab" />

        <TableTitleRow excel :url="excelUrl" :filename="filename" :disabled="!project">
          <template #tail>
            <v-btn
              v-if="compName === 'SummaryForBudget'"
              size="small"
              color="primary"
              variant="tonal"
              @click="handleDownload(cashFlowUrl, '월별_자금집행_현황.xlsx')"
              flat
              :disabled="false"
              class="mt-1 mx-1"
              style="text-decoration: none"
            >
              <v-icon icon="mdi-microsoft-excel" color="green" class="mr-2" />
              캐시플로우 폼
              <v-icon icon="mdi-download" color="grey" class="ml-2" />
            </v-btn>
          </template>
        </TableTitleRow>

        <StatusByAccount
          v-if="compName === 'StatusByAccount'"
          :date="date"
          :is-balance="isBalance"
          @is-exist-balance="isExistBalance"
          @direct-balance="directBalance"
        />
        <CashListByDate v-if="compName === 'CashListByDate'" :date="date" />

        <SummaryForBudget
          v-if="compName === 'SummaryForBudget'"
          :date="date"
          @patch-budget="patchBudget"
          @update-revised="updateRevised"
        />

        <Calculated
          :calc-date="proCalculated?.calculated"
          :is-calculated="isCalculated"
          @to-calculate="checkBalance"
        />
      </CCardBody>
    </ContentBody>
  </ProLedgerAuthGuard>
</template>
