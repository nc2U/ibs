<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { pageTitle, navMenu } from '@/views/comLedger/_menu/headermixin'
import { useCompany } from '@/store/pinia/company'
import { useComLedger } from '@/store/pinia/comLedger'
import { getToday } from '@/utils/baseMixins'
import { message } from '@/utils/helper'
import type { Company } from '@/store/types/settings.ts'
import type { ComCalculated } from '@/store/types/comLedger'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComLedgerAuthGuard from '@/components/AuthGuard/ComLedgerAuthGuard.vue'
import DateChoicer from './components/DateChoicer.vue'
import TabSelect from './components/TabSelect.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import StatusByAccount from './components/StatusByAccount.vue'
import CashListByDate from './components/CashListByDate.vue'
import MonthlySummary from './components/MonthlySummary.vue'
import Calculated from './components/Calculated.vue'

const route = useRoute()
const urlCompanyId = computed(() => {
  const id = route.query.company
  return id ? parseInt(id as string, 10) : null
})

const date = ref(getToday())
const periodMode = ref<'mtd' | 'full'>('mtd')
const isBalance = ref<'' | 'true'>('true')
const compName = ref('StatusByAccount')

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)

const ledgerStore = useComLedger()
const fetchComBankAccList = (com: number) => ledgerStore.fetchComBankAccList(com)
const fetchComLedgerBalanceByAccList = (com: {
  company: number
  date: string
  is_balance?: 'true' | ''
}) => ledgerStore.fetchComLedgerBalanceByAccList(com)
const fetchDateLedgerTransactionList = (payload: { company: number; date: string }) =>
  ledgerStore.fetchDateLedgerTransactionList(payload)
const fetchComMonthlySummary = (payload: {
  company: number
  from_date: string
  to_date: string
}) => ledgerStore.fetchComMonthlySummary(payload)

const monthlyPeriodRange = computed(() => {
  const raw = date.value || getToday()
  const [yStr, mStr] = raw.split('-')
  const y = Number(yStr)
  const m = Number(mStr)
  if (!y || !m) return { from_date: raw, to_date: raw }
  const from_date = `${yStr}-${mStr}-01`
  if (periodMode.value === 'full') {
    const lastDay = new Date(y, m, 0).getDate()
    return { from_date, to_date: `${yStr}-${mStr}-${String(lastDay).padStart(2, '0')}` }
  }
  return { from_date, to_date: raw }
})

const fetchComLedgerCalc = (com: number) => ledgerStore.fetchComLedgerCalculation(com)
const createComLedgerCalc = (payload: ComCalculated) =>
  ledgerStore.createComLedgerCalculation(payload)
const patchComLedgerCalc = (payload: ComCalculated) =>
  ledgerStore.patchComLedgerCalculation(payload)
const fetchComLedgerLastDeal = (com: number) => ledgerStore.fetchComLedgerLastDealDate(com)

const comLedgerCalculated = computed(() => ledgerStore.comLedgerCalculated) // 최종 정산 일자
const comLedgerLastDealDate = computed(() => ledgerStore.comLedgerLastDealDate) // 최종 거래 일자

const isCalculated = computed(
  () =>
    !!comLedgerCalculated.value &&
    comLedgerCalculated.value.calculated >= (comLedgerLastDealDate.value?.deal_date ?? ''),
) // 최종 정산 일자 이후에 거래 기록이 없음 === true

const checkBalance = async () => {
  if (!company.value) return
  const lastDealDate = comLedgerLastDealDate.value?.deal_date
  if (!lastDealDate) {
    message('warning', '알림!', '정산할 거래 내역이 없습니다.')
    return
  }
  const payload: ComCalculated = {
    company: company.value as number,
    calculated: lastDealDate,
  }
  if (comLedgerCalculated.value?.pk) {
    await patchComLedgerCalc({ pk: comLedgerCalculated.value.pk, ...payload })
  } else {
    await createComLedgerCalc(payload)
  }
}

const excelUrl = computed(() => {
  const comp = compName.value
  if (comp === 'StatusByAccount') {
    return `/excel/com-balance/?company=${company.value}&date=${date.value}&is_balance=${isBalance.value}`
  }
  if (comp === 'CashListByDate') {
    return `/excel/com-daily-cash/?company=${company.value}&date=${date.value}`
  }
  if (comp === 'MonthlySummary') {
    const { from_date, to_date } = monthlyPeriodRange.value
    return `/excel/com-monthly-summary/?company=${company.value}&from_date=${from_date}&to_date=${to_date}`
  }
  return ''
})

const comp: { [key: number]: string } = {
  1: 'StatusByAccount',
  2: 'CashListByDate',
  3: 'MonthlySummary',
}

const filename = computed(() => {
  switch (compName.value) {
    case 'StatusByAccount':
      return '계좌별-원장현황.xlsx'
    case 'CashListByDate':
      return '일별-원장내역.xlsx'
    case 'MonthlySummary':
      return '월별-자금집계.xlsx'
    default:
      return ''
  }
})

const showTab = (num: number) => {
  compName.value = comp[num] || 'StatusByAccount'
  localStorage.setItem('comLedgerStatus', `${num}`)
}

const loadMonthlySummary = (comId?: number | null) => {
  const targetCom = comId ?? company.value
  if (!targetCom) return Promise.resolve(null)
  const { from_date, to_date } = monthlyPeriodRange.value
  return fetchComMonthlySummary({ company: targetCom, from_date, to_date })
}

const setDate = (dt: string) => {
  date.value = dt
  if (company.value) {
    fetchComLedgerBalanceByAccList({ company: company.value, date: dt, is_balance: isBalance.value })
    fetchDateLedgerTransactionList({ company: company.value, date: dt })
    loadMonthlySummary(company.value)
  }
}

const onChangePeriodMode = (mode: 'mtd' | 'full') => {
  periodMode.value = mode
  loadMonthlySummary()
}

const isExistBalance = (val: boolean | 'true' | '') => {
  isBalance.value = val ? 'true' : ''
  if (company.value) {
    fetchComLedgerBalanceByAccList({
      company: company.value as number,
      is_balance: isBalance.value,
      date: date.value,
    })
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    fetchComBankAccList(pk),
    fetchComLedgerBalanceByAccList({ company: pk, date: date.value, is_balance: isBalance.value }),
    fetchDateLedgerTransactionList({ company: pk, date: date.value }),
    loadMonthlySummary(pk),
    fetchComLedgerCalc(pk),
    fetchComLedgerLastDeal(pk),
  ])
}

const dataReset = () => {
  ledgerStore.comBankList = []
  ledgerStore.comLedgerBalanceByAccList = []
  ledgerStore.dateLedgerTransactions = []
  ledgerStore.comMonthlySummary = null
  ledgerStore.comLedgerCalculation = []
  ledgerStore.comLedgerLastDealList = []
}

const comSelect = async (target: number | null) => {
  dataReset()
  if (target) await dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  try {
    const savedTab = Number(localStorage.getItem('comLedgerStatus'))
    compName.value = [1, 2, 3].includes(savedTab) ? comp[savedTab] : 'StatusByAccount'
    const comId = urlCompanyId.value || company.value || comStore.initComId
    if (urlCompanyId.value && urlCompanyId.value !== company.value) {
      await comStore.fetchCompany(urlCompanyId.value)
    }
    if (comId) {
      await dataSetup(comId)
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <ComLedgerAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />
    <ContentBody>
      <CCardBody class="pb-5">
        <DateChoicer :value="date" @set-date="setDate" />

        <TabSelect @tab-select="showTab" />

        <TableTitleRow
          title="본사 계좌 및 자금 현황"
          excel
          :url="excelUrl"
          :filename="filename"
          :disabled="!company"
        />

        <StatusByAccount
          v-if="compName === 'StatusByAccount'"
          :date="date"
          :is-balance="isBalance"
          @is-exist-balance="isExistBalance"
        />

        <CashListByDate v-if="compName === 'CashListByDate'" :date="date" />

        <MonthlySummary
          v-if="compName === 'MonthlySummary'"
          :date="date"
          :company="company"
          :period-mode="periodMode"
          @change-date="setDate"
          @update:period-mode="onChangePeriodMode"
        />

        <Calculated
          :calc-date="comLedgerCalculated?.calculated"
          :is-calculated="isCalculated"
          :has-transactions="!!comLedgerLastDealDate?.deal_date"
          @to-calculate="checkBalance"
        />
      </CCardBody>
    </ContentBody>
  </ComLedgerAuthGuard>
</template>
