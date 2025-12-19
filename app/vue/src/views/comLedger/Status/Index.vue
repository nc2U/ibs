<script lang="ts" setup>
import Cookies from 'js-cookie'
import { ref, computed, onBeforeMount } from 'vue'
import { pageTitle, navMenu } from '@/views/comLedger/_menu/headermixin'
import { useCompany } from '@/store/pinia/company'
import { useComLedger } from '@/store/pinia/comLedger'
import { getToday } from '@/utils/baseMixins'
import type { Company } from '@/store/types/settings.ts'
import type { ComCalculated } from '@/store/types/comLedger'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComCashAuthGuard from '@/components/AuthGuard/ComCashAuthGuard.vue'
import DateChoicer from './components/DateChoicer.vue'
import TabSelect from './components/TabSelect.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import StatusByAccount from './components/StatusByAccount.vue'
import CashListByDate from './components/CashListByDate.vue'
import Calculated from './components/Calculated.vue'

const date = ref(getToday())
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

const createComLedgerCalc = (payload: ComCalculated) => ledgerStore.createComLedgerCalc(payload)
const patchComLedgerCalc = (payload: ComCalculated) => ledgerStore.patchComLedgerCalc(payload)
const fetchComLedgerCalc = (com: number) => ledgerStore.fetchComLedgerCalc(com)
const fetchComLedgerLastDeal = (com: number) => ledgerStore.fetchComLedgerLastDealDate(com)

const comLedgerCalculated = computed(() => ledgerStore.comLedgerCalculated) // 최종 정산 일자
const comLedgerLastDealDate = computed(() => ledgerStore.comLedgerLastDealDate) // 최종 거래 일자

const isCalculated = computed(
  () =>
    !!comLedgerCalculated.value &&
    comLedgerCalculated.value.calculated >= (comLedgerLastDealDate.value?.deal_date ?? ''),
) // 최종 정산 일자 이후에 거래 기록이 없음 === true

const checkBalance = () => {
  const payload = {
    company: company.value as number,
    calculated: comLedgerLastDealDate.value?.deal_date as string,
  }
  if (!!comLedgerCalculated.value)
    patchComLedgerCalc({ ...{ pk: comLedgerCalculated.value.pk }, ...payload })
  else createComLedgerCalc(payload)
}

const excelUrl = computed(() => {
  const comp = compName.value
  let url = ''
  if (comp === 'StatusByAccount') url = `/excel/ledger-balance/?company=${company.value}`
  else if (comp === 'CashListByDate') url = `/excel/ledger-daily/?company=${company.value}`
  return `${url}&date=${date.value}`
})

const comp: { [key: number]: string } = {
  1: 'StatusByAccount',
  2: 'CashListByDate',
}

const filename = computed(() => {
  switch (compName.value) {
    case 'StatusByAccount':
      return '계좌별-원장현황.xlsx'
    case 'CashListByDate':
      return '일별-원장내역.xlsx'
    default:
      return ''
  }
})

const showTab = (num: number) => (compName.value = comp[num])

const setDate = (dt: string) => {
  date.value = dt
  if (company.value) {
    fetchComLedgerBalanceByAccList({ company: company.value, date: dt })
    fetchDateLedgerTransactionList({ company: company.value, date: dt })
  }
}

const isExistBalance = (val: 'true' | '') => {
  if (company.value) {
    fetchComLedgerBalanceByAccList({
      company: company.value as number,
      is_balance: val,
      date: date.value,
    })
  }
}

const dataSetup = (pk: number) => {
  fetchComBankAccList(pk)
  fetchComLedgerBalanceByAccList({ company: pk, date: date.value, is_balance: 'true' })
  fetchDateLedgerTransactionList({ company: pk, date: date.value })
  fetchComLedgerCalc(pk)
  fetchComLedgerLastDeal(pk)
}

const dataReset = () => {
  ledgerStore.comBankList = []
  ledgerStore.comLedgerBalanceByAccList = []
  ledgerStore.dateLedgerTransactions = []
  ledgerStore.comLedgerCalc = []
  ledgerStore.comLedgerLastDealList = []
}

const comSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  dataSetup(company.value || comStore.initComId)
  compName.value = comp[Number(Cookies.get('comLedgerStatus') ?? 1)]
  loading.value = false
})
</script>

<template>
  <ComCashAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />
    <ContentBody>
      <CCardBody class="pb-5">
        <DateChoicer @set-date="setDate" />

        <TabSelect @tab-select="showTab" />

        <TableTitleRow excel :url="excelUrl" :filename="filename" :disabled="!company" />

        <StatusByAccount
          v-if="compName === 'StatusByAccount'"
          :date="date"
          @is-exist-balance="isExistBalance"
        />

        <CashListByDate v-if="compName === 'CashListByDate'" :date="date" />

        <Calculated
          :calc-date="comLedgerCalculated?.calculated"
          :is-calculated="isCalculated"
          @to-calculate="checkBalance"
        />
      </CCardBody>
    </ContentBody>
  </ComCashAuthGuard>
</template>
