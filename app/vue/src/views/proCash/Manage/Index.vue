<script lang="ts" setup>
import Cookies from 'js-cookie'
import { ref, computed, onBeforeMount, provide } from 'vue'
import { pageTitle, navMenu } from '@/views/proCash/_menu/headermixin'
import { useComCash } from '@/store/pinia/comCash'
import { useProCash } from '@/store/pinia/proCash'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { usePayment } from '@/store/pinia/payment'
import {
  type CashBookFilter,
  type ProBankAcc,
  type ProjectCashBook as PrCashBook,
} from '@/store/types/proCash'
import { cutString } from '@/utils/baseMixins'
import { write_project_cash } from '@/utils/pageAuth'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ListController from '@/views/proCash/Manage/components/ListController.vue'
import AddProCash from '@/views/proCash/Manage/components/AddProCash.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ProCashList from '@/views/proCash/Manage/components/ProCashList.vue'

const listControl = ref()

const bankFees = ref([14, 61]) // 은행수수료 d2(id), d3(id)
const transferD3 = ref([73, 74]) // 대체 출금(id), 입금(id)
const cancelD3 = ref([75, 76]) // 취소 출금(id), 입금(id)

provide('transfers', [17, 73]) // 대체 출금 d2(id), d3(id)
provide('cancels', [18, 75]) // 취소 출금 d2(id), d3(id)

const dataFilter = ref<CashBookFilter>({
  page: 1,
  from_date: '',
  to_date: '',
  sort: null,
  account_d1: null,
  pro_acc_d2: null,
  pro_acc_d3: null,
  is_imprest: 'false',
  bank_account: null,
  search: '',
})

const imprest = ref(false)

const setImprest = () => {
  dataFilter.value.page = 1
  imprest.value = !imprest.value
  dataFilter.value.is_imprest = imprest.value ? '' : '0'
  Cookies.set('get-imprest', dataFilter.value.is_imprest)
  fetchProjectCashList({
    ...{ project: project.value },
    ...dataFilter.value,
  })
}

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const pageSelect = (page: number) => {
  dataFilter.value.page = page
  fetchProjectCashList({
    ...{ project: project.value },
    ...dataFilter.value,
  })
}

const listFiltering = (payload: CashBookFilter) => {
  dataFilter.value = payload
  const sort = payload.sort ? payload.sort : null
  const d1 = payload.account_d1 ? payload.account_d1 : null
  const d2 = payload.pro_acc_d2 ? payload.pro_acc_d2 : null

  fetchFormAccD1List(sort)
  fetchProFormAccD2List(d1, sort)
  fetchProFormAccD3List(d2, sort)
  if (project.value) {
    fetchProjectCashList({
      ...{ project: project.value },
      ...payload,
    })
  }
}

const excelUrl = computed(() => {
  const pj = project.value
  const sd = dataFilter.value.from_date
  const ed = dataFilter.value.to_date
  const st = dataFilter.value.sort || ''
  const d1 = dataFilter.value.pro_acc_d2 || ''
  const d2 = dataFilter.value.pro_acc_d3 || ''
  const ba = dataFilter.value.bank_account || ''
  const q = dataFilter.value.search
  return `/excel/p-cashbook/?project=${pj}&sdate=${sd}&edate=${ed}&sort=${st}&d1=${d1}&d2=${d2}&bank_acc=${ba}&q=${q}`
})

const paymentStore = usePayment()
const fetchPayOrderList = (project: number) => paymentStore.fetchPayOrderList(project)

const comCashStore = useComCash()
const fetchBankCodeList = () => comCashStore.fetchBankCodeList()
const fetchFormAccD1List = (sort?: number | null) => comCashStore.fetchFormAccD1List(sort)

const proCashStore = useProCash()
const fetchProAccSortList = () => proCashStore.fetchProAccSortList()
const fetchProAllAccD2List = () => proCashStore.fetchProAllAccD2List()
const fetchProAllAccD3List = () => proCashStore.fetchProAllAccD3List()

const fetchProFormAccD2List = (d1?: number | null, sort?: number | null) =>
  proCashStore.fetchProFormAccD2List(d1, sort)
const fetchProFormAccD3List = (d2?: number | null, sort?: number | null) =>
  proCashStore.fetchProFormAccD3List(d2, sort)

const fetchProBankAccList = (projId: number) => proCashStore.fetchProBankAccList(projId)
const fetchAllProBankAccList = (projId: number) => proCashStore.fetchAllProBankAccList(projId)
const fetchProjectCashList = (payload: CashBookFilter) => proCashStore.fetchProjectCashList(payload)

const createProBankAcc = (payload: ProBankAcc) => proCashStore.createProBankAcc(payload)
const patchProBankAcc = (payload: ProBankAcc) => proCashStore.patchProBankAcc(payload)

const createPrCashBook = (
  payload: PrCashBook & { sepData: PrCashBook | null } & {
    filters: CashBookFilter
  },
) => proCashStore.createPrCashBook(payload)

const updatePrCashBook = (
  payload: PrCashBook & { sepData: PrCashBook | null } & {
    filters: CashBookFilter
  },
) => proCashStore.updatePrCashBook(payload)

const deletePrCashBook = (
  payload: { pk: number; project: number } & {
    filters?: CashBookFilter
  },
) => proCashStore.deletePrCashBook(payload)
const fetchProCashCalc = (proj: number) => proCashStore.fetchProCashCalc(proj)

const chargeCreate = (
  payload: PrCashBook & { sepData: PrCashBook | null } & {
    filters: CashBookFilter
  },
  charge: number,
) => {
  payload.sort = 2
  payload.project_account_d2 = bankFees.value[0]
  payload.project_account_d3 = bankFees.value[1]
  payload.content = cutString(payload.content, 8) + ' - 이체수수료'
  payload.trader = '지급수수료'
  payload.outlay = charge
  payload.income = null
  payload.evidence = '0'
  payload.note = ''

  createPrCashBook(payload)
}

const onCreate = (
  payload: PrCashBook & { sepData: PrCashBook | null } & {
    filters: CashBookFilter
  } & { bank_account_to: null | number; charge: null | number },
) => {
  if (project.value) payload.project = project.value
  if (payload.sort === 3 && payload.bank_account_to) {
    // 대체 거래일 때
    const { bank_account_to, charge, ...inputData } = payload

    inputData.sort = 2
    inputData.trader = '내부대체'
    inputData.project_account_d3 = transferD3.value[0]
    createPrCashBook({ ...inputData })

    inputData.sort = 1
    inputData.project_account_d3 = transferD3.value[1]
    inputData.income = inputData.outlay
    inputData.outlay = null
    inputData.bank_account = bank_account_to

    setTimeout(() => createPrCashBook({ ...inputData }), 300)
    if (!!charge) {
      setTimeout(() => chargeCreate({ ...inputData }, charge), 600)
    }
  } else if (payload.sort === 4) {
    // 취소 거래일 때
    payload.sort = 2
    payload.project_account_d3 = cancelD3.value[0]
    payload.evidence = '0'
    createPrCashBook(payload)
    payload.sort = 1
    payload.project_account_d3 = cancelD3.value[1]
    payload.income = payload.outlay
    delete payload.outlay
    payload.evidence = ''
    setTimeout(() => createPrCashBook(payload), 300)
  } else {
    const { charge, ...inputData } = payload
    createPrCashBook(inputData)
    if (!!charge) chargeCreate(inputData, charge)
  }
}

const onUpdate = (
  payload: PrCashBook & { sepData: PrCashBook | null } & {
    filters: CashBookFilter
  },
) => updatePrCashBook(payload)

const multiSubmit = (payload: {
  formData: PrCashBook
  sepData: PrCashBook | null
  bank_account_to: null | number
  charge: null | number
}) => {
  const { formData, ...sepData } = payload
  const submitData = {
    ...formData,
    ...sepData,
    ...{ filters: dataFilter.value },
  }

  if (formData.pk) onUpdate(submitData)
  else onCreate(submitData)
}

const onDelete = (payload: { pk: number; project: number }) =>
  deletePrCashBook({ ...{ filters: dataFilter.value }, ...payload })

const onBankCreate = (payload: ProBankAcc) => {
  payload.project = project.value as number
  createProBankAcc(payload)
}
const onBankUpdate = (payload: ProBankAcc) => patchProBankAcc(payload)

const dataSetup = (pk: number) => {
  fetchProBankAccList(pk)
  fetchAllProBankAccList(pk)
  fetchProjectCashList({ project: pk, ...dataFilter.value })
  fetchProCashCalc(pk)
}

const dataReset = () => {
  proCashStore.proBankAccountList = []
  proCashStore.allProBankAccountList = []
  proCashStore.proCashBookList = []
  proCashStore.proCashesCount = 0
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const contStore = useContract()
const fetchAllContracts = (projId: number) => contStore.fetchAllContracts(projId)

const loading = ref(true)
onBeforeMount(async () => {
  imprest.value = Cookies.get('get-imprest') === ''
  dataFilter.value.is_imprest = imprest.value ? '' : '0'
  await fetchBankCodeList()
  await fetchProAccSortList()
  await fetchFormAccD1List()
  await fetchProAllAccD2List()
  await fetchProAllAccD3List()
  await fetchProFormAccD2List()
  await fetchProFormAccD3List()
  await fetchPayOrderList(project.value || projStore.initProjId)
  await fetchAllContracts(project.value || projStore.initProjId)
  dataSetup(project.value || projStore.initProjId)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  />

  <ContentBody>
    <CCardBody class="pb-5">
      <ListController ref="listControl" @list-filtering="listFiltering" />
      <AddProCash
        v-if="write_project_cash"
        :project="project"
        @multi-submit="multiSubmit"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
      />
      <TableTitleRow
        title="프로젝트 입출금 내역"
        color="indigo"
        excel
        :disabled="!project"
        :url="excelUrl"
      >
        <v-tooltip activator="parent" location="top">
          엑셀은 항상 전체(운영비용 포함) 내역 출력
        </v-tooltip>
        <div style="padding-top: 7px">
          <CFormSwitch
            v-model="imprest"
            label="전체(운영비용 포함) 보기"
            id="all-list-view"
            @click="setImprest"
            :disabled="!project"
          ></CFormSwitch>
        </div>
      </TableTitleRow>
      <ProCashList
        :project="project as number"
        @page-select="pageSelect"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
      />
    </CCardBody>
  </ContentBody>
</template>
