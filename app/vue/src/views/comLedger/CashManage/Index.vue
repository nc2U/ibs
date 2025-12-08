<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, ref } from 'vue'
import {
  onBeforeRouteLeave,
  type RouteLocationNormalizedLoaded as Loaded,
  useRoute,
  useRouter,
} from 'vue-router'
import { navMenu, pageTitle } from '@/views/comLedger/_menu/headermixin'
import { useIbs } from '@/store/pinia/ibs.ts'
import { useCompany } from '@/store/pinia/company'
import { useProject } from '@/store/pinia/project'
import { write_company_cash } from '@/utils/pageAuth'
import type { Company } from '@/store/types/settings.ts'
import type { AccountingEntry, BankTransaction, CompanyBank } from '@/store/types/comLedger'
import { type DataFilter as Filter, type DataFilter, useComLedger } from '@/store/pinia/comLedger'
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

const dataFilter = ref<Filter>({
  page: 1,
  company: null,
  from_date: '',
  to_date: '',
  sort: null,
  account: null,
  affiliated: null,
  bank_account: null,
  search: '',
})

const excelUrl = computed(() => {
  const sd = dataFilter.value.from_date
  const ed = dataFilter.value.to_date
  const st = dataFilter.value.sort || ''
  const ac = dataFilter.value.account || ''
  const af = dataFilter.value.affiliated || ''
  const ba = dataFilter.value.bank_account || ''
  const q = dataFilter.value.search
  const url = `/excel/cashbook/?company=${company.value}`
  return `${url}&s_date=${sd}&e_date=${ed}&sort=${st}&account=${ac}&affiliated=${af}&bank_account=${ba}&search_word=${q}`
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)

const proStore = useProject()
const projectList = computed(() => proStore.projectList)
const fetchProjectList = async () => proStore.fetchProjectList()

const fetchCompany = async (pk: number) => await comStore.fetchCompany(pk)
const fetchAllDepartList = (com: number) => comStore.fetchAllDepartList(com)

const ledgerStore = useComLedger()
const fetchBankCodeList = () => ledgerStore.fetchBankCodeList()
const fetchCompanyAccounts = () => ledgerStore.fetchCompanyAccounts()
const fetchComBankAccList = (pk: number) => ledgerStore.fetchComBankAccList(pk)
const fetchAllComBankAccList = (pk: number) => ledgerStore.fetchAllComBankAccList(pk)

const createComBankAcc = (payload: CompanyBank) => ledgerStore.createComBankAcc(payload)
const patchComBankAcc = (payload: CompanyBank) => ledgerStore.patchComBankAcc(payload)

const fetchBankTransactionList = (payload: Filter) => ledgerStore.fetchBankTransactionList(payload)
const findBankTransactionPage = (highlightId: number, filters: Filter) =>
  ledgerStore.findBankTransactionPage(highlightId, filters)
const createBankTransaction = (payload: BankTransaction & { accData: AccountingEntry | null }) =>
  ledgerStore.createBankTransaction(payload)
const updateBankTransaction = (
  payload: BankTransaction & { accData: AccountingEntry | null } & { filters: DataFilter },
) => ledgerStore.updateBankTransaction(payload)
const deleteBankTransaction = (payload: BankTransaction & { filters: Filter }) =>
  ledgerStore.deleteBankTransaction(payload)
const fetchComLedgerCalc = (com: number) => ledgerStore.fetchComLedgerCalc(com)

const pageSelect = (page: number) => listControl.value.listFiltering(page)

const listFiltering = (payload: Filter) => {
  // 필터링 시 query string 정리
  clearQueryString()
  if (company.value) payload.company = company.value
  dataFilter.value = payload
  const sort = payload.sort || null
  const ac = payload.account || null
  fetchCompanyAccounts()
  if (company.value) fetchBankTransactionList(payload)
}

// const chargeCreate = (
//   payload: BankTransaction & { accData: AccountingEntry | null },
//   charge: number,
// ) => {
//   payload.sort = 2
//   payload.account_d1 = 5
//   payload.account_d2 = 17
//   payload.account_d3 = 118
//   payload.content = cutString(payload.content, 8) + ' - 이체수수료'
//   payload.trader = '지급수수료'
//   payload.outlay = charge
//   payload.income = null
//   payload.evidence = '0'
//   payload.note = ''
//
//   createBankTransaction(payload)
// }

const onCreate = (
  payload: BankTransaction & { accData: AccountingEntry | null } & {
    bank_account_to: null | number
    charge: null | number
  },
) => {
  payload.company = company.value as number
  // if (payload.sort === 3 && payload.bank_account_to) {
  //   // 대체 거래일 때
  //   const { bank_account_to, charge, ...inputData } = payload
  //
  //   inputData.sort = 2
  //   inputData.trader = '내부대체'
  //   inputData.account_d3 = 131
  //   createBankTransaction(inputData)
  //
  //   inputData.sort = 1
  //   inputData.account_d3 = 132
  //   inputData.income = inputData.outlay
  //   inputData.outlay = null
  //   inputData.bank_account = bank_account_to
  //
  //   setTimeout(() => createBankTransaction({ ...inputData }), 300)
  //   if (!!charge) {
  //     // setTimeout(() => chargeCreate({ ...inputData }, charge), 600)
  //   }
  // } else if (payload.sort === 4) {
  //   // 취소 거래일 때
  //   payload.sort = 2
  //   payload.account_d3 = 133
  //   payload.evidence = '0'
  //   createBankTransaction(payload)
  //   payload.sort = 1
  //   payload.account_d3 = 134
  //   payload.income = payload.outlay
  //   payload.outlay = null
  //   payload.evidence = ''
  //   setTimeout(() => createBankTransaction(payload), 300)
  // } else {
  //   const { charge, ...inputData } = payload
  //   createBankTransaction(inputData)
  //   if (!!charge) chargeCreate(inputData, charge)
  // }
}

const onUpdate = (
  payload: BankTransaction & { accData: AccountingEntry | null } & { filters: Filter },
) => updateBankTransaction(payload)

const multiSubmit = (payload: {
  formData: BankTransaction
  accData: AccountingEntry | null
  bank_account_to: null | number
  charge: null | number
}) => {
  const { formData, ...accData } = payload
  const createData = { ...formData, ...accData }
  const updateData = { ...{ filters: dataFilter.value }, ...createData }

  // if (formData.pk) onUpdate(updateData)
  // else onCreate(createData)
}

const onDelete = (payload: BankTransaction) =>
  deleteBankTransaction({ ...{ filters: dataFilter.value }, ...payload })

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => 1 // patchAccD3(payload)

const onBankCreate = (payload: CompanyBank) => {
  payload.company = company.value as number
  createComBankAcc(payload)
}
const onBankUpdate = (payload: CompanyBank) => patchComBankAcc(payload)

const dataSetup = async (pk: number) => {
  await fetchCompany(pk)
  await fetchProjectList()
  await fetchAllDepartList(pk)
  await fetchComBankAccList(pk)
  await fetchCompanyAccounts()
  await fetchAllComBankAccList(pk)
  await fetchBankTransactionList({ company: pk })
  await fetchComLedgerCalc(pk)
  dataFilter.value.company = pk
}

const dataReset = () => {
  comStore.allDepartList = []
  comStore.removeCompany()
  ledgerStore.comBankList = []
  ledgerStore.allComBankList = []
  ledgerStore.bankTransactionList = []
  ledgerStore.bankTransactionCount = 0
  dataFilter.value.company = null
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
      dataFilter.value.page = targetPage
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
            :projects="projectList"
            @list-filtering="listFiltering"
          />

          <AddTransaction
            v-if="write_company_cash"
            :company="company as number"
            :projects="projectList"
            @multi-submit="multiSubmit"
            @on-bank-create="onBankCreate"
            @on-bank-update="onBankUpdate"
          />
          <!--          @patch-d3-hide="patchD3Hide"-->

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
            :projects="projectList"
            :highlight-id="highlightId ?? undefined"
            :current-page="dataFilter.page || 1"
            @page-select="pageSelect"
            @multi-submit="multiSubmit"
            @on-delete="onDelete"
            @on-bank-create="onBankCreate"
            @on-bank-update="onBankUpdate"
          />
          <!--          @patch-d3-hide="patchD3Hide"-->
        </div>

        <div
          v-else-if="
            route.name === '본사 거래 내역 - 수정' || route.name === '본사 거래 내역 - 생성'
          "
        >
          <TransForm
            :company="company as number"
            @on-bank-create="onBankCreate"
            @on-bank-update="onBankUpdate"
          />
          <!--          @patch-d3-hide="patchD3Hide"-->
        </div>
      </CCardBody>
    </ContentBody>
  </ComLedgerAuthGuard>
</template>
