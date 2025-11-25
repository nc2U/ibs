<script lang="ts" setup>
import { ref, computed, onBeforeMount, nextTick } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { navMenu, pageTitle } from '@/views/comLedger/_menu/headermixin'
import { cutString } from '@/utils/baseMixins'
import { useCompany } from '@/store/pinia/company'
import { useProject } from '@/store/pinia/project'
import { write_company_cash } from '@/utils/pageAuth'
import { useComLedger, type DataFilter as Filter, type DataFilter } from '@/store/pinia/comLedger'
import type { CashBook, CompanyBank, SepItems } from '@/store/types/comLedger'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComLedgerAuthGuard from '@/components/AuthGuard/ComLedgerAuthGuard.vue'
import ListController from '@/views/comLedger/CashManage/components/ListController.vue'
import AddCash from '@/views/comLedger/CashManage/components/AddCash.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import CashList from '@/views/comLedger/CashManage/components/CashList.vue'

const listControl = ref()
const route = useRoute()
const router = useRouter()

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
  account_d1: null,
  account_d2: null,
  account_d3: null,
  project: null,
  is_return: false,
  bank_account: null,
  search: '',
})

const excelUrl = computed(() => {
  const sd = dataFilter.value.from_date
  const ed = dataFilter.value.to_date
  const st = dataFilter.value.sort || ''
  const d1 = dataFilter.value.account_d1 || ''
  const d2 = dataFilter.value.account_d2 || ''
  const d3 = dataFilter.value.account_d3 || ''
  const pr = dataFilter.value.project || ''
  const re = dataFilter.value.is_return || ''
  const ba = dataFilter.value.bank_account || ''
  const q = dataFilter.value.search
  const url = `/excel/cashbook/?company=${company.value}`
  return `${url}&s_date=${sd}&e_date=${ed}&sort=${st}&account_d1=${d1}&account_d2=${d2}&account_d3=${d3}&project=${pr}&is_return=${re}&bank_account=${ba}&search_word=${q}`
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk)

const proStore = useProject()
const projectList = computed(() => proStore.projectList)
const fetchProjectList = async () => proStore.fetchProjectList()

const fetchCompany = async (pk: number) => await comStore.fetchCompany(pk)
const fetchAllDepartList = (com: number) => comStore.fetchAllDepartList(com)

const cashStore = useComLedger()
const fetchBankCodeList = () => cashStore.fetchBankCodeList()
const fetchAccSortList = () => cashStore.fetchAccSortList()
const fetchAllAccD1List = () => cashStore.fetchAllAccD1List()
const fetchAllAccD2List = () => cashStore.fetchAllAccD2List()
const fetchAllAccD3List = () => cashStore.fetchAllAccD3List()
const fetchFormAccD1List = (sort: number | null) => cashStore.fetchFormAccD1List(sort)
const fetchFormAccD2List = (sort: number | null, d1: number | null) =>
  cashStore.fetchFormAccD2List(sort, d1)
const fetchFormAccD3List = (sort: number | null, d1: number | null, d2: number | null) =>
  cashStore.fetchFormAccD3List(sort, d1, d2)
const fetchComBankAccList = (pk: number) => cashStore.fetchComBankAccList(pk)
const fetchAllComBankAccList = (pk: number) => cashStore.fetchAllComBankAccList(pk)

const createComBankAcc = (payload: CompanyBank) => cashStore.createComBankAcc(payload)
const patchComBankAcc = (payload: CompanyBank) => cashStore.patchComBankAcc(payload)

const fetchCashBookList = (payload: Filter) => cashStore.fetchCashBookList(payload)
const findCashBookPage = (highlightId: number, filters: Filter) =>
  cashStore.findCashBookPage(highlightId, filters)
const createCashBook = (payload: CashBook & { sepData: SepItems | null }) =>
  cashStore.createCashBook(payload)
const updateCashBook = (
  payload: CashBook & { sepData: SepItems | null } & { filters: DataFilter },
) => cashStore.updateCashBook(payload)
const deleteCashBook = (payload: CashBook & { filters: Filter }) =>
  cashStore.deleteCashBook(payload)
const patchAccD3 = (payload: { pk: number; is_hide: boolean }) => cashStore.patchAccD3(payload)
const fetchComLedgerCalc = (com: number) => cashStore.fetchComLedgerCalc(com)

const pageSelect = (page: number) => listControl.value.listFiltering(page)

const listFiltering = (payload: Filter) => {
  // 필터링 시 query string 정리
  clearQueryString()
  if (company.value) payload.company = company.value
  dataFilter.value = payload
  const sort = payload.sort || null
  const d1 = payload.account_d1 || null
  const d2 = payload.account_d2 || null
  fetchFormAccD1List(sort)
  fetchFormAccD2List(sort, d1)
  fetchFormAccD3List(sort, d1, d2)
  console.log(payload)
  if (company.value) fetchCashBookList(payload)
}

const chargeCreate = (payload: CashBook & { sepData: SepItems | null }, charge: number) => {
  payload.sort = 2
  payload.account_d1 = 5
  payload.account_d2 = 17
  payload.account_d3 = 118
  payload.content = cutString(payload.content, 8) + ' - 이체수수료'
  payload.trader = '지급수수료'
  payload.outlay = charge
  payload.income = null
  payload.evidence = '0'
  payload.note = ''

  createCashBook(payload)
}

const onCreate = (
  payload: CashBook & { sepData: SepItems | null } & {
    bank_account_to: null | number
    charge: null | number
  },
) => {
  payload.company = company.value || null
  if (payload.sort === 3 && payload.bank_account_to) {
    // 대체 거래일 때
    const { bank_account_to, charge, ...inputData } = payload

    inputData.sort = 2
    inputData.trader = '내부대체'
    inputData.account_d3 = 131
    createCashBook(inputData)

    inputData.sort = 1
    inputData.account_d3 = 132
    inputData.income = inputData.outlay
    inputData.outlay = null
    inputData.bank_account = bank_account_to

    setTimeout(() => createCashBook({ ...inputData }), 300)
    if (!!charge) {
      setTimeout(() => chargeCreate({ ...inputData }, charge), 600)
    }
  } else if (payload.sort === 4) {
    // 취소 거래일 때
    payload.sort = 2
    payload.account_d3 = 133
    payload.evidence = '0'
    createCashBook(payload)
    payload.sort = 1
    payload.account_d3 = 134
    payload.income = payload.outlay
    payload.outlay = null
    payload.evidence = ''
    setTimeout(() => createCashBook(payload), 300)
  } else {
    const { charge, ...inputData } = payload
    createCashBook(inputData)
    if (!!charge) chargeCreate(inputData, charge)
  }
}

const onUpdate = (payload: CashBook & { sepData: SepItems | null } & { filters: Filter }) =>
  updateCashBook(payload)

const multiSubmit = (payload: {
  formData: CashBook
  sepData: SepItems | null
  bank_account_to: null | number
  charge: null | number
}) => {
  const { formData, ...sepData } = payload
  const createData = { ...formData, ...sepData }
  const updateData = { ...{ filters: dataFilter.value }, ...createData }

  if (formData.pk) onUpdate(updateData)
  else onCreate(createData)
}

const onDelete = (payload: CashBook) =>
  deleteCashBook({ ...{ filters: dataFilter.value }, ...payload })

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => patchAccD3(payload)

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
  await fetchAllComBankAccList(pk)
  await fetchCashBookList({ company: pk })
  await fetchComLedgerCalc(pk)
  dataFilter.value.company = pk
}

const dataReset = () => {
  comStore.allDepartList = []
  comStore.removeCompany()
  cashStore.comBankList = []
  cashStore.allComBankList = []
  cashStore.cashBookList = []
  cashStore.cashBookCount = 0
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
      const targetPage = await findCashBookPage(highlightId.value, {
        ...dataFilter.value,
        company: company.value,
        limit: 15, // Django에서 사용하는 페이지 크기와 동일하게 설정
      })

      // 해당 페이지로 이동 (1페이지여도 page 값 명시적 설정)
      dataFilter.value.page = targetPage
      await fetchCashBookList({
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
  await fetchAccSortList()
  await fetchAllAccD1List()
  await fetchAllAccD2List()
  await fetchAllAccD3List()
  await fetchFormAccD1List(null)
  await fetchFormAccD2List(null, null)
  await fetchFormAccD3List(null, null, null)

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
        <!--        <ListController ref="listControl" :projects="projectList" @list-filtering="listFiltering" />-->
        <!--        <AddCash-->
        <!--          v-if="write_company_cash"-->
        <!--          :company="company as number"-->
        <!--          :projects="projectList"-->
        <!--          @multi-submit="multiSubmit"-->
        <!--          @patch-d3-hide="patchD3Hide"-->
        <!--          @on-bank-create="onBankCreate"-->
        <!--          @on-bank-update="onBankUpdate"-->
        <!--        />-->
        <!--        <TableTitleRow-->
        <!--          title="본사 입출금 관리"-->
        <!--          color="indigo"-->
        <!--          excel-->
        <!--          :url="excelUrl"-->
        <!--          filename="본사_출납내역.xls"-->
        <!--          :disabled="!company"-->
        <!--        />-->
        <CashList
          :company="company as number"
          :projects="projectList"
          :highlight-id="highlightId ?? undefined"
          :current-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
          @patch-d3-hide="patchD3Hide"
          @on-bank-create="onBankCreate"
          @on-bank-update="onBankUpdate"
        />
      </CCardBody>
    </ContentBody>
  </ComLedgerAuthGuard>
</template>
