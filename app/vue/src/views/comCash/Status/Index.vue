<script lang="ts" setup>
import Cookies from 'js-cookie'
import { ref, computed, onBeforeMount } from 'vue'
import { pageTitle, navMenu } from '@/views/comCash/_menu/headermixin'
import { useCompany } from '@/store/pinia/company'
import { useComCash } from '@/store/pinia/comCash'
import { getToday } from '@/utils/baseMixins'
import type { Company } from '@/store/types/settings.ts'
import type { ComCalculated } from '@/store/types/comCash'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComCashAuthGuard from '@/components/AuthGuard/ComCashAuthGuard.vue'
import DateChoicer from '@/views/comCash/Status/components/DateChoicer.vue'
import TabSelect from '@/views/comCash/Status/components/TabSelect.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import StatusByAccount from '@/views/comCash/Status/components/StatusByAccount.vue'
import CashListByDate from '@/views/comCash/Status/components/CashListByDate.vue'
import Calculated from '@/views/comCash/Status/components/Calculated.vue'

const date = ref(getToday())
const compName = ref('StatusByAccount')

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)

const cashStore = useComCash()
const fetchAccSortList = () => cashStore.fetchAccSortList()
const fetchAllAccD1List = () => cashStore.fetchAllAccD1List()
const fetchAllAccD2List = () => cashStore.fetchAllAccD2List()
const fetchAllAccD3List = () => cashStore.fetchAllAccD3List()

const fetchComBankAccList = (com: number) => cashStore.fetchComBankAccList(com)
const fetchComBalanceByAccList = (com: {
  company: number
  date: string
  is_balance?: 'true' | ''
}) => cashStore.fetchComBalanceByAccList(com)
const fetchDateCashBookList = (payload: { company: number; date: string }) =>
  cashStore.fetchDateCashBookList(payload)

const createComCashCalc = (payload: ComCalculated) => cashStore.createComCashCalc(payload)
const patchComCashCalc = (payload: ComCalculated) => cashStore.patchComCashCalc(payload)
const fetchComCashCalc = (com: number) => cashStore.fetchComCashCalc(com)
const fetchComLastDeal = (com: number) => cashStore.fetchComLastDeal(com)

const comCalculated = computed(() => cashStore.comCalculated) // 최종 정산 일자
const comLastDealDate = computed(() => cashStore.comLastDealDate) // 최종 거래 일자

const isCalculated = computed(
  () =>
    !!comCalculated.value &&
    comCalculated.value.calculated >= (comLastDealDate.value?.deal_date ?? ''),
) // 최종 정산 일자 이후에 거래 기록이 없음 === true

const checkBalance = () => {
  const payload = {
    company: company.value as number,
    calculated: comLastDealDate.value?.deal_date as string,
  }
  if (!!comCalculated.value) patchComCashCalc({ ...{ pk: comCalculated.value.pk }, ...payload })
  else createComCashCalc(payload)
}

const excelUrl = computed(() => {
  const comp = compName.value
  let url = ''
  if (comp === 'StatusByAccount') url = `/excel/balance/?company=${company.value}`
  else if (comp === 'CashListByDate') url = `/excel/daily-cash/?company=${company.value}`
  return `${url}&date=${date.value}`
})

const comp: { [key: number]: string } = {
  1: 'StatusByAccount',
  2: 'CashListByDate',
}

const filename = computed(() => {
  switch (compName.value) {
    case 'StatusByAccount':
      return '계좌별-자금현황.xlsx'
    case 'CashListByDate':
      return '일별-입출금내역.xlsx'
    default:
      return ''
  }
})

const showTab = (num: number) => (compName.value = comp[num])

const setDate = (dt: string) => {
  date.value = dt
  if (company.value) {
    fetchComBalanceByAccList({ company: company.value, date: dt })
    fetchDateCashBookList({ company: company.value, date: dt })
  }
}

const isExistBalance = (val: 'true' | '') => {
  if (company.value) {
    fetchComBalanceByAccList({
      company: company.value as number,
      is_balance: val,
      date: date.value,
    })
  }
}

const dataSetup = (pk: number) => {
  fetchComBankAccList(pk)
  fetchComBalanceByAccList({ company: pk, date: date.value, is_balance: 'true' })
  fetchDateCashBookList({ company: pk, date: date.value })
  fetchComCashCalc(pk)
  fetchComLastDeal(pk)
}

const dataReset = () => {
  cashStore.comBankList = []
  cashStore.comBalanceByAccList = []
  cashStore.dateCashBook = []
  cashStore.comCashCalc = []
  cashStore.comLastDeal = []
}

const comSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await fetchAccSortList()
  await fetchAllAccD1List()
  await fetchAllAccD2List()
  await fetchAllAccD3List()
  dataSetup(company.value || comStore.initComId)
  compName.value = comp[Number(Cookies.get('comCashStatus') ?? 1)]
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
          :calc-date="comCalculated?.calculated"
          :is-calculated="isCalculated"
          @to-calculate="checkBalance"
        />
      </CCardBody>
    </ContentBody>
  </ComCashAuthGuard>
</template>
