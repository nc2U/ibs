<script lang="ts" setup>
import Cookies from 'js-cookie'
import { ref, computed, onBeforeMount } from 'vue'
import { useProject } from '@/store/pinia/project'
import { useProCash } from '@/store/pinia/proCash'
import { getToday } from '@/utils/baseMixins'
import { pageTitle, navMenu } from '@/views/proCash/_menu/headermixin'
import type { ProCalculated } from '@/store/types/proCash'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import DateChoicer from '@/views/proCash/Status/components/DateChoicer.vue'
import TabSelect from '@/views/proCash/Status/components/TabSelect.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import StatusByAccount from '@/views/proCash/Status/components/StatusByAccount.vue'
import CashListByDate from '@/views/proCash/Status/components/CashListByDate.vue'
import SummaryForBudget from '@/views/proCash/Status/components/SummaryForBudget.vue'
import Calculated from '@/views/comCash/Status/components/Calculated.vue'

const date = ref(getToday())
const direct = ref('0')
const isBalance = ref('true')
const compName = ref('StatusByAccount')

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const fetchStatusOutBudgetList = (proj: number) => projStore.fetchStatusOutBudgetList(proj)

const patchStatusOutBudget = (payload: {
  pk: number
  project: number
  budget?: number
  revised_budget?: number
}) => projStore.patchStatusOutBudget(payload)

const fetchExecAmountList = (project: number, date?: string) =>
  projStore.fetchExecAmountList(project, date)

const pCashStore = useProCash()
const fetchProAllAccD2List = () => pCashStore.fetchProAllAccD2List()
const fetchProAllAccD3List = () => pCashStore.fetchProAllAccD3List()
const fetchProBankAccList = (proj: number) => pCashStore.fetchProBankAccList(proj)

const fetchBalanceByAccList = (payload: {
  project: number
  direct?: string
  date?: string
  is_balance?: '' | 'true'
}) => pCashStore.fetchBalanceByAccList(payload)
const fetchDateCashBookList = (payload: { project: number; date: string }) =>
  pCashStore.fetchDateCashBookList(payload)

const createProCashCalc = (payload: ProCalculated) => pCashStore.createProCashCalc(payload)
const patchProCashCalc = (payload: ProCalculated) => pCashStore.patchProCashCalc(payload)
const fetchProCashCalc = (proj: number) => pCashStore.fetchProCashCalc(proj)
const fetchProLastDeal = (proj: number) => pCashStore.fetchProLastDeal(proj)

const proCalculated = computed(() => pCashStore.proCalculated) // 최종 정산 일자
const proLastDealDate = computed(() => pCashStore.proLastDealDate) // 최종 거래 일자

const isCalculated = computed(
  () =>
    !!proCalculated.value &&
    proCalculated.value.calculated >= (proLastDealDate.value?.deal_date ?? 0),
) // 최종 정산 일자 이후에 거래 기록이 없음 === true

const checkBalance = () => {
  const payload = {
    project: project.value as number,
    calculated: proLastDealDate.value?.deal_date as string,
  }
  if (!!proCalculated.value) patchProCashCalc({ ...{ pk: proCalculated.value.pk }, ...payload })
  else createProCashCalc(payload)
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

const comp: { [key: number]: string } = {
  1: 'StatusByAccount',
  2: 'CashListByDate',
  3: 'SummaryForBudget',
}

const showTab = (num: number) => (compName.value = comp[num])

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
  fetchProCashCalc(pk)
  fetchProLastDeal(pk)
}

const dataReset = () => {
  projStore.statusOutBudgetList = []
  projStore.execAmountList = []
  pCashStore.proBankAccountList = []
  pCashStore.balanceByAccList = []
  pCashStore.proDateCashBook = []
  pCashStore.proCashCalc = []
  pCashStore.proLastDeal = []
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => {
  fetchProAllAccD2List()
  fetchProAllAccD3List()
  dataSetup(project.value || projStore.initProjId)
  compName.value = comp[Number(Cookies.get('proCashStatus') ?? 1)]
})
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
      <DateChoicer @set-date="setDate" />

      <TabSelect @tab-select="showTab" />

      <TableTitleRow excel :url="excelUrl" :disabled="!project" />

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
</template>
