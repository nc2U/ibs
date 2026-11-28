<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { useProject } from '@/store/pinia/project'
import { useProLedger } from '@/store/pinia/proLedger'
import { usePerms } from '@/composables/usePerms.ts'
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
import TransListByDate from '@/views/proLedger/Status/components/TransListByDate.vue'
import SummaryForBudget from '@/views/proLedger/Status/components/SummaryForBudget.vue'
import Calculated from '@/views/proLedger/Status/components/Calculated.vue'

const date = ref(getToday())
const direct = ref<'0' | 'i'>('0')
const isBalance = ref<'' | 'true'>('true')
const compName = ref('StatusByAccount')

const { downloadExcel } = useDownload()
const handleDownload = (url: string, fileName: string) => {
  downloadExcel(url, fileName)
}

const { can, PERM } = usePerms()
const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const canAccessProject = (projId?: number | null) =>
  projId ? can(PERM.LEDGER_READ, projId) : can(PERM.LEDGER_READ)
// ledger 기반 API 호출 (useLedger=true)
const fetchProject = (proj: number) => projStore.fetchProject(proj)
const fetchStatusOutBudgetList = (proj: number) => projStore.fetchStatusOutBudgetList(proj, true)
const patchStatusOutBudget = (payload: {
  pk: number
  project: number
  budget?: number
  revised_budget?: number
}) => projStore.patchStatusOutBudget(payload, true)
const fetchExecAmountList = (proj: number, dt?: string) => projStore.fetchExecAmountList(proj, dt, true)

const pLedgerStore = useProLedger()
const fetchProjectAccounts = () => pLedgerStore.fetchProjectAccounts()
const fetchProBankAccList = (proj: number) => pLedgerStore.fetchProBankAccList(proj)

const fetchProLedgerBalanceByAccList = (payload: {
  project: number
  direct?: string
  date?: string
  is_balance?: '' | 'true'
}) => pLedgerStore.fetchProLedgerBalanceByAccList(payload)
const fetchDateLedgerTransactionList = (payload: { project: number; date: string }) =>
  pLedgerStore.fetchDateLedgerTransactionList(payload)

const createProLedgerCalculation = (payload: ProCalculated) =>
  pLedgerStore.createProLedgerCalculation(payload)
const patchProLedgerCalculation = (payload: ProCalculated) =>
  pLedgerStore.patchProLedgerCalculation(payload)
const fetchProLedgerCalculation = (proj: number) => pLedgerStore.fetchProLedgerCalculation(proj)
const fetchProLedgerLastDealDate = (proj: number) => pLedgerStore.fetchProLedgerLastDealDate(proj)

const proLedgerCalculated = computed(() => pLedgerStore.proLedgerCalculated) // 최종 정산 일자
const proLedgerLastDealDate = computed(() => pLedgerStore.proLedgerLastDealDate) // 최종 거래 일자

const isCalculated = computed(
  () =>
    !!proLedgerCalculated.value &&
    proLedgerCalculated.value.calculated >= (proLedgerLastDealDate.value?.deal_date ?? ''),
) // 최종 정산 일자 이후에 거래 기록이 없음 === true

const checkBalance = async () => {
  if (!project.value || !proLedgerLastDealDate.value?.deal_date) return
  const payload = {
    project: project.value,
    calculated: proLedgerLastDealDate.value.deal_date,
  }
  const ok = proLedgerCalculated.value
    ? await patchProLedgerCalculation({ pk: proLedgerCalculated.value.pk, ...payload })
    : await createProLedgerCalculation(payload)
  if (ok) await fetchProLedgerCalculation(project.value)
}

const revised = ref(1)
const updateRevised = (isRevised: number) => (revised.value = isRevised)

const excelUrl = computed(() => {
  const pj = project.value ?? ''
  const dr = direct.value
  const dt = date.value
  if (compName.value === 'StatusByAccount')
    return `/excel/pro-balance/?project=${pj}&date=${dt}&bank_account__directpay=${dr}&is_balance=${isBalance.value}`
  if (compName.value === 'CashListByDate') return `/excel/pro-daily-cash/?project=${pj}&date=${dt}`
  if (compName.value === 'SummaryForBudget')
    return `/excel/pro-budget/?project=${pj}&date=${dt}&revised=${revised.value}`
  return ''
})

const cashFlowUrl = computed(
  () =>
    `/excel/ledger-cash-flow-form/?project=${project.value ?? ''}&date=${date.value}&revised=${revised.value}`,
)

const comp: Record<number, string> = {
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
  compName.value = comp[num] ?? 'StatusByAccount'
  localStorage.setItem('proLedgerStatus', `${num}`)
}

const setDate = async (dt: string) => {
  date.value = dt
  if (project.value && canAccessProject(project.value)) {
    await Promise.all([
      fetchStatusOutBudgetList(project.value),
      fetchExecAmountList(project.value, dt),
      fetchProLedgerBalanceByAccList({
        project: project.value,
        direct: direct.value,
        date: dt,
        is_balance: isBalance.value,
      }),
      fetchDateLedgerTransactionList({ project: project.value, date: dt }),
    ])
  }
}

const patchBudget = async (pk: number, budget: number, isRevised: boolean) => {
  if (!project.value) return
  if (!isRevised) await patchStatusOutBudget({ project: project.value, pk, budget })
  else await patchStatusOutBudget({ project: project.value, pk, revised_budget: budget })
}

const isExistBalance = async (val: boolean | 'true' | '') => {
  isBalance.value = val ? 'true' : ''
  if (project.value && canAccessProject(project.value)) {
    await fetchProLedgerBalanceByAccList({
      project: project.value,
      direct: direct.value,
      is_balance: isBalance.value,
      date: date.value,
    })
  }
}

const directBalance = async (val: boolean) => {
  isBalance.value = val ? '' : isBalance.value
  direct.value = val ? 'i' : '0'
  if (project.value && canAccessProject(project.value)) {
    await fetchProLedgerBalanceByAccList({
      project: project.value,
      direct: direct.value,
      is_balance: isBalance.value,
      date: date.value,
    })
  }
}

const dataSetup = async (pk: number) => {
  if (!canAccessProject(pk)) return
  await Promise.all([
    fetchProject(pk),
    fetchStatusOutBudgetList(pk),
    fetchExecAmountList(pk, date.value),
    fetchProBankAccList(pk),
    fetchProLedgerBalanceByAccList({
      project: pk,
      direct: direct.value,
      date: date.value,
      is_balance: isBalance.value,
    }),
    fetchDateLedgerTransactionList({ project: pk, date: date.value }),
    fetchProLedgerCalculation(pk),
    fetchProLedgerLastDealDate(pk),
  ])
}

const dataReset = () => {
  projStore.removeProject()
  projStore.statusOutBudgetList = []
  projStore.execAmountList = []
  projStore.ledgerExecAmountList = []
  pLedgerStore.proBankList = []
  pLedgerStore.proLedgerBalanceByAccList = []
  pLedgerStore.dateLedgerTransactions = []
  pLedgerStore.proLedgerCalculation = []
  pLedgerStore.proLedgerLastDealList = []
}

const projSelect = async (target: number | null) => {
  dataReset()
  if (target) await dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  try {
    const savedTab = Number(localStorage.getItem('proLedgerStatus') ?? 1)
    compName.value = comp[savedTab] ?? 'StatusByAccount'
    const projId = project.value || projStore.currentProject
    if (!canAccessProject(projId)) return
    await fetchProjectAccounts()
    if (projId) await dataSetup(projId)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <ProLedgerAuthGuard :project="project">
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

        <TableTitleRow
          title="프로젝트 자금 및 예산 현황"
          excel
          :url="excelUrl"
          :filename="filename"
          :disabled="!project"
        >
          <template #tail>
            <v-btn
              v-if="compName === 'SummaryForBudget'"
              size="small"
              color="primary"
              variant="tonal"
              :disabled="!project"
              @click="handleDownload(cashFlowUrl, '월별_자금집행_현황.xlsx')"
              class="mt-1 mx-1"
              style="text-decoration: none"
            >
              <v-icon icon="mdi-microsoft-excel" color="green" class="me-2" />
              캐시플로우 폼
              <v-icon icon="mdi-download" color="grey" class="ms-2" />
            </v-btn>
          </template>
        </TableTitleRow>

        <StatusByAccount
          v-if="compName === 'StatusByAccount'"
          :date="date"
          :is-balance="isBalance"
          :direct="direct"
          @is-exist-balance="isExistBalance"
          @direct-balance="directBalance"
        />
        <TransListByDate v-if="compName === 'CashListByDate'" :date="date" />

        <SummaryForBudget
          v-if="compName === 'SummaryForBudget'"
          :project="project"
          :date="date"
          @patch-budget="patchBudget"
          @update-revised="updateRevised"
        />

        <Calculated
          :project="project"
          :calc-date="proLedgerCalculated?.calculated"
          :is-calculated="isCalculated"
          :has-transactions="!!proLedgerLastDealDate?.deal_date"
          @to-calculate="checkBalance"
        />
      </CCardBody>
    </ContentBody>
  </ProLedgerAuthGuard>
</template>
