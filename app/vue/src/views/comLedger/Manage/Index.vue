<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, provide, ref } from 'vue'
import {
  onBeforeRouteLeave,
  type RouteLocationNormalizedLoaded as Loaded,
  useRoute,
  useRouter,
} from 'vue-router'
import { navMenu, pageTitle } from '@/views/comLedger/_menu/headermixin'
import { useCompany } from '@/store/pinia/company'
import { write_company_cash } from '@/utils/pageAuth'
import type { Company } from '@/store/types/settings.ts'
import { type DataFilter as Filter, useComLedger } from '@/store/pinia/comLedger'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComLedgerAuthGuard from '@/components/AuthGuard/ComLedgerAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddTransaction from './components/AddTransaction.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import TransactionList from './components/TransactionList.vue'
import TransForm from './components/TransForm.vue'

const listControl = ref()
const [route, router] = [useRoute() as Loaded & { name: string }, useRouter()]

const highlightId = computed(() => {
  const id = route.query.highlight_id
  return id ? parseInt(id as string, 10) : null
})

// URL에서 company 파라미터 읽기
const urlCompanyId = computed(() => {
  const id = route.query.company
  return id ? parseInt(id as string, 10) : null
})

const excelUrl = computed(() => {
  const from_deal_date = dataFilter.value.from_date || ''
  const to_deal_date = dataFilter.value.to_date || ''
  const sort = dataFilter.value.sort || ''
  const account = dataFilter.value.account || ''
  const affiliate = dataFilter.value.affiliate || ''
  const bank_account = dataFilter.value.bank_account || ''
  const search = dataFilter.value.search || ''
  const url = `/excel/com-trans/?company=${company.value}`
  return `${url}&from_deal_date=${from_deal_date}&to_deal_date=${to_deal_date}&sort=${sort}&account=${account}&affiliate=${affiliate}&bank_account=${bank_account}&search=${search}`
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)

const fetchCompany = async (pk: number) => await comStore.fetchCompany(pk)
const fetchAllDepartList = (com: number) => comStore.fetchAllDepartList(com)

const ledgerStore = useComLedger()
const affiliates = computed(() => ledgerStore.affiliates)
const comAccounts = computed(() => ledgerStore.comAccounts)
const transferFeePk = computed(() => ledgerStore.transferFeePk)
const allComBankList = computed(() => ledgerStore.allComBankList)
const dataFilter = computed(() => ledgerStore.bankTransactionFilter)
const bankTransactionCount = computed(() => ledgerStore.bankTransactionCount)

provide('affiliates', affiliates)
provide('comAccounts', comAccounts)
provide('transferFeePk', transferFeePk)
provide('allComBankList', allComBankList)
provide('bankTransactionCount', bankTransactionCount)

const fetchBankCodeList = () => ledgerStore.fetchBankCodeList()
const fetchAffiliateList = () => ledgerStore.fetchAffiliateList()
const fetchCompanyAccounts = () => ledgerStore.fetchCompanyAccounts()
const fetchComBankAccList = (pk: number) => ledgerStore.fetchComBankAccList(pk)
const fetchAllComBankAccList = (pk: number) => ledgerStore.fetchAllComBankAccList(pk)

const fetchBankTransactionList = (payload: Filter) => ledgerStore.fetchBankTransactionList(payload)
const findBankTransactionPage = (highlightId: number, filters: Filter) =>
  ledgerStore.findBankTransactionPage(highlightId, filters)
const fetchComLedgerCalc = (com: number) => ledgerStore.fetchComLedgerCalculation(com)

const pageSelect = (page: number) => listControl.value.listFiltering(page)

const listFiltering = (payload: Filter) => {
  // 필터링 시 query string 정리
  clearQueryString()
  if (company.value) payload.company = company.value
  if (company.value) fetchBankTransactionList(payload)
}

const dataSetup = async (pk: number) => {
  await fetchCompany(pk)
  await fetchAllDepartList(pk)
  await fetchComBankAccList(pk)
  await fetchAllComBankAccList(pk)
  await fetchBankTransactionList({ company: pk })
  await fetchComLedgerCalc(pk)
  ledgerStore.bankTransactionFilter.company = pk
}

const dataReset = () => {
  comStore.allDepartList = []
  comStore.removeCompany()
  ledgerStore.comBankList = []
  ledgerStore.allComBankList = []
  ledgerStore.bankTransactionList = []
  ledgerStore.bankTransactionCount = 0
  ledgerStore.bankTransactionFilter.company = null
}

const comSelect = async (target: number | null, skipClearQuery = false) => {
  // 회사 변경 시 query string 정리 (URL 파라미터로부터 자동 전환하는 경우는 제외)
  if (!skipClearQuery) {
    clearQueryString()
  }
  dataReset()
  if (!!target) {
    await fetchCompany(target)
    await dataSetup(target)
  }
}

// Query string 정리 함수
const clearQueryString = () => {
  if (route.query.highlight_id) {
    router
      .replace({
        name: route.name,
        params: route.params,
        // query를 빈 객체로 설정하여 모든 query string 제거
        query: {},
      })
      .catch(() => {
        // 같은 경로로의 이동에서 발생하는 NavigationDuplicated 에러 무시
      })
  }
}

const scrollToHighlight = async () => {
  if (highlightId.value) {
    await nextTick()
    const element = document.querySelector(`[data-cash-id="${highlightId.value}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // highlightId는 computed이므로 URL 파라미터가 있는 동안 자동으로 유지됩니다
    }
  }
}

const loadHighlightPage = async () => {
  if (highlightId.value && company.value) {
    try {
      // 현재 필터 조건으로 해당 항목이 몇 번째 페이지에 있는지 찾기
      const targetPage = await findBankTransactionPage(highlightId.value, {
        ...dataFilter.value,
        company: company.value,
        limit: 15, // Django에서 사용하는 페이지 크기와 동일하게 설정
      })
      // 해당 페이지로 이동 (1페이지여도 page 값 명시적 설정)
      ledgerStore.bankTransactionFilter.page = targetPage
      await fetchBankTransactionList({
        ...dataFilter.value,
        company: company.value,
      })
    } catch (error) {
      console.error('Error finding highlight page:', error)
    }
  }
}

const loading = ref(true)
onBeforeMount(async () => {
  // URL에서 회사 ID가 지정되어 있으면 해당 회사로 전환
  let companyId = company.value || comStore.initComId
  if (urlCompanyId.value && urlCompanyId.value !== companyId) {
    console.log(`Switching to company ${urlCompanyId.value} from URL parameter`)
    // 회사 전환 (query string 정리 건너뛰기)
    await comSelect(urlCompanyId.value, true)
    companyId = urlCompanyId.value
  }

  await fetchBankCodeList()
  await fetchAffiliateList()
  await fetchCompanyAccounts()

  // 하이라이트 항목이 있으면 해당 페이지로 이동 후 스크롤
  if (highlightId.value) {
    await loadHighlightPage()
  } else {
    await dataSetup(companyId)
  }
  await scrollToHighlight()

  loading.value = false
})

// 다른 라우트로 이동 시 query string 정리
onBeforeRouteLeave(() => {
  clearQueryString()
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
        <div v-if="route.name === '본사 거래 내역'">
          <ListController
            ref="listControl"
            :company="company as number"
            :data-filter="dataFilter"
            @list-filtering="listFiltering"
          />

          <AddTransaction v-if="write_company_cash" :company="company as number" />

          <TableTitleRow
            title="본사 입출금 관리"
            color="indigo"
            excel
            :url="excelUrl"
            filename="본사_출납내역.xls"
            :disabled="!company"
          />
          <TransactionList
            :company="company as number"
            :highlight-id="highlightId ?? undefined"
            :current-page="dataFilter.page || 1"
            @page-select="pageSelect"
          />
        </div>

        <div
          v-else-if="
            route.name === '본사 거래 내역 - 수정' || route.name === '본사 거래 내역 - 생성'
          "
        >
          <TransForm :company="company as number" />
        </div>
      </CCardBody>
    </ContentBody>
  </ComLedgerAuthGuard>
</template>
