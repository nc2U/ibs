<script lang="ts" setup>
import { ref, computed, onBeforeMount, provide } from 'vue'
import { pageTitle, navMenu } from '@/views/proCash/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useProCash } from '@/store/pinia/proCash'
import { useComCash } from '@/store/pinia/comCash'
import { useContract } from '@/store/pinia/contract'
import { usePayment } from '@/store/pinia/payment'
import { cutString } from '@/utils/baseMixins'
import {
  type CashBookFilter,
  type ProBankAcc,
  type ProjectCashBook as PrCashBook,
} from '@/store/types/proCash'
import { write_project_cash } from '@/utils/pageAuth'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProCashAuthGuard from '@/components/AuthGuard/ProCashAuthGuard.vue'
import ListController from '@/views/proCash/Imprest/components/ListController.vue'
import AddProImprest from '@/views/proCash/Imprest/components/AddProImprest.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ProImprestList from '@/views/proCash/Imprest/components/ProImprestList.vue'

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
  bank_account: null,
  search: '',
})

const excelUrl = computed(() => {
  const pj = project.value
  const sd = dataFilter.value.from_date
  const ed = dataFilter.value.to_date
  const st = dataFilter.value.sort || ''
  const d2 = dataFilter.value.pro_acc_d2 || ''
  const d3 = dataFilter.value.pro_acc_d3 || ''
  const ba = dataFilter.value.bank_account || ''
  const q = dataFilter.value.search
  return `/excel/pro-cashbook/?project=${pj}&imp=1&sdate=${sd}&edate=${ed}&sort=${st}&d2=${d2}&d3=${d3}&bank_acc=${ba}&q=${q}`
})

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const paymentStore = usePayment()
const fetchPayOrderList = (project: number) => paymentStore.fetchPayOrderList(project)

const comCashStore = useComCash()
const fetchBankCodeList = () => comCashStore.fetchBankCodeList()
const fetchFormAccD1List = (sort?: number | null) => comCashStore.fetchFormAccD1List(sort)

const pCashStore = useProCash()
const fetchProAccSortList = () => pCashStore.fetchProAccSortList()
const fetchProAllAccD2List = () => pCashStore.fetchProAllAccD2List()
const fetchProAllAccD3List = () => pCashStore.fetchProAllAccD3List()

const fetchProFormAccD2List = (d1?: number | null, sort?: number | null) =>
  pCashStore.fetchProFormAccD2List(d1, sort)
const fetchProFormAccD3List = (d2?: number | null, sort?: number | null) =>
  pCashStore.fetchProFormAccD3List(d2, sort)

const fetchProBankAccList = (projId: number) => pCashStore.fetchProBankAccList(projId)
const fetchAllProBankAccList = (projId: number) => pCashStore.fetchAllProBankAccList(projId)
const fetchProjectImprestList = (payload: CashBookFilter) =>
  pCashStore.fetchProjectImprestList(payload)

const createProBankAcc = (payload: ProBankAcc) => pCashStore.createProBankAcc(payload)
const patchProBankAcc = (payload: ProBankAcc) => pCashStore.patchProBankAcc(payload)

const createPrCashBook = (
  payload: PrCashBook & { sepData: PrCashBook | null } & {
    filters: CashBookFilter
  },
) => pCashStore.createPrCashBook(payload)

const updatePrImprestBook = (
  payload: PrCashBook & { sepData: PrCashBook | null } & {
    filters: CashBookFilter
  },
) => pCashStore.updatePrImprestBook(payload)

const deletePrImprestBook = (
  payload: { pk: number; project: number } & {
    filters?: CashBookFilter
  },
) => pCashStore.deletePrImprestBook(payload)
const fetchProCashCalc = (proj: number) => pCashStore.fetchProCashCalc(proj)

const pageSelect = (page: number) => {
  dataFilter.value.page = page
  listControl.value.listFiltering(page)
}

const listFiltering = (payload: CashBookFilter) => {
  dataFilter.value = payload
  const sort = payload.sort ? payload.sort : null
  const d1 = payload.account_d1 ? payload.account_d1 : null
  const d2 = payload.pro_acc_d2 ? payload.pro_acc_d2 : null
  fetchProFormAccD2List(d1, sort)
  fetchProFormAccD3List(d2, sort)
  if (project.value) fetchProjectImprestList({ ...{ project: project.value }, ...payload })
}

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
  } & {
    bank_account_to: null | number
    ba_is_imprest: boolean
    charge: null | number
  },
) => {
  if (project.value) payload.project = project.value || null
  if (payload.sort === 3 && payload.bank_account_to) {
    const { bank_account, bank_account_to, ba_is_imprest, charge, ...inputData } = payload

    inputData.sort = 2
    inputData.trader = '내부대체'
    inputData.project_account_d3 = transferD3.value[0]
    createPrCashBook({ bank_account, ...inputData })

    inputData.sort = 1
    inputData.project_account_d3 = transferD3.value[1]
    if (!ba_is_imprest) inputData.is_imprest = ba_is_imprest
    inputData.income = inputData.outlay
    inputData.outlay = null

    setTimeout(() => createPrCashBook({ bank_account: bank_account_to, ...inputData }), 300)
    if (!!charge) {
      setTimeout(() => chargeCreate({ bank_account, ...inputData }, charge), 600)
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
) => updatePrImprestBook(payload)

const multiSubmit = (payload: {
  formData: PrCashBook & {
    bank_account_to: null | number
    ba_is_imprest: boolean
    charge: null | number
  }
  sepData: PrCashBook | null
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
  deletePrImprestBook({ ...{ filters: dataFilter.value }, ...payload })

const onBankCreate = (payload: ProBankAcc) => {
  payload.project = project.value as number
  createProBankAcc(payload)
}
const onBankUpdate = (payload: ProBankAcc) => patchProBankAcc(payload)

const dataSetup = (pk: number) => {
  fetchProBankAccList(pk)
  fetchAllProBankAccList(pk)
  fetchProjectImprestList({ project: pk })
  fetchProCashCalc(pk)
}

const dataReset = () => {
  pCashStore.balanceByAccList = []
  pCashStore.allProBankAccountList = []
  pCashStore.proImprestList = []
  pCashStore.proImprestCount = 0
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const contStore = useContract()
const fetchAllContracts = (projId: number) => contStore.fetchAllContracts(projId)

const loading = ref(true)
onBeforeMount(async () => {
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
  <ProCashAuthGuard>
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
        <AddProImprest
          v-if="write_project_cash"
          :project="project"
          @multi-submit="multiSubmit"
          @on-bank-update="onBankUpdate"
        />
        <TableTitleRow
          title="운영비용(전도금) 사용 내역"
          color="success"
          excel
          filename="운영비_입출금_내역.xls"
          :url="excelUrl"
          :disabled="!project"
        />
        <ProImprestList
          :project="project"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
          @on-bank-create="onBankCreate"
          @on-bank-update="onBankUpdate"
        />
      </CCardBody>
    </ContentBody>
  </ProCashAuthGuard>
</template>
