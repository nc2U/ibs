<script lang="ts" setup>
import Cookies from 'js-cookie'
import { ref, computed, onBeforeMount, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/payments/_menu/headermixin'
import type { CashBookFilter, ProjectCashBook } from '@/store/types/proCash'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import { usePayment } from '@/store/pinia/payment'
import { useProCash } from '@/store/pinia/proCash'
import { onBeforeRouteLeave } from 'vue-router'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PaymentSummary from '@/views/payments/List/components/PaymentSummary.vue'
import ListController from '@/views/payments/List/components/ListController.vue'
import PaymentList from '@/views/payments/List/components/PaymentList.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'

const listControl = ref()
const filterItems = ref<CashBookFilter>({
  page: 1,
  from_date: '',
  to_date: '',
  order_group: '',
  unit_type: '',
  pay_order: '',
  pay_account: '',
  no_contract: false,
  no_install: false,
  search: '',
})

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const fetchIncBudgetList = (proj: number) => projStore.fetchIncBudgetList(proj)

const contStore = useContract()
const fetchOrderGroupList = (projId: number) => contStore.fetchOrderGroupList(projId)
const fetchContSummaryList = (projId: number) => contStore.fetchContSummaryList(projId)

const proDataStore = useProjectData()
const fetchTypeList = (projId: number) => proDataStore.fetchTypeList(projId)

const paymentStore = usePayment()
const fetchPaySumList = (projId: number) => paymentStore.fetchPaySumList(projId)
const fetchPayOrderList = (projId: number) => paymentStore.fetchPayOrderList(projId)
const fetchPaymentList = (payload: CashBookFilter) => paymentStore.fetchPaymentList(payload)

const proCashStore = useProCash()
const fetchAllProBankAccList = (projId: number) => proCashStore.fetchAllProBankAccList(projId)
const patchPrCashBook = (
  payload: ProjectCashBook & { isPayment?: boolean } & {
    filters: CashBookFilter
  },
) => proCashStore.patchPrCashBook(payload)

const listFiltering = (payload: CashBookFilter) => {
  filterItems.value = payload
  if (project.value) {
    payload.project = project.value
    fetchPaymentList(payload)
  }
}

const payMatch = (payload: ProjectCashBook) =>
  patchPrCashBook({ ...payload, isPayment: true, filters: filterItems.value }) // const & payment 매칭

const pageSelect = (page: number) => {
  filterItems.value.page = page
  listControl.value.listFiltering(page)
}

const byPayment = computed(() => {
  let pUrl = project.value ? `/excel/payments/?project=${project.value}` : ''
  if (filterItems.value.from_date) pUrl += `&sd=${filterItems.value.from_date}`
  if (filterItems.value.to_date) pUrl += `&ed=${filterItems.value.to_date}`
  if (filterItems.value.order_group) pUrl += `&og=${filterItems.value.order_group}`
  if (filterItems.value.unit_type) pUrl += `&ut=${filterItems.value.unit_type}`
  if (filterItems.value.pay_order) pUrl += `&ipo=${filterItems.value.pay_order}`
  if (filterItems.value.pay_account) pUrl += `&ba=${filterItems.value.pay_account}`
  if (filterItems.value.no_contract) pUrl += `&nc=true`
  if (filterItems.value.no_install) pUrl += `&ni=true`
  if (filterItems.value.search) pUrl += `&q=${filterItems.value.search}`
  return pUrl
})

const byContract = computed(() =>
  project.value
    ? `/excel/paid-by-cont/?project=${project.value}&date=${filterItems.value.to_date}`
    : '',
)

const paymentBy = ref(Cookies.get('paymentBy') ?? '1') // 다운로드할 파일 선택

watch(paymentBy, newVal => Cookies.set('paymentBy', newVal))

const excelUrl = computed(() => (paymentBy.value === '1' ? byPayment.value : byContract.value))

const dataSetup = (pk: number) => {
  fetchOrderGroupList(pk)
  fetchTypeList(pk)
  fetchIncBudgetList(pk)
  fetchContSummaryList(pk)
  fetchPaySumList(pk)
  fetchPaymentList({ project: pk })
  fetchPayOrderList(pk)
  fetchAllProBankAccList(pk)
}

const dataReset = () => {
  contStore.orderGroupList = []
  proDataStore.unitTypeList = []
  proCashStore.proBankAccountList = []
  projStore.proIncBudgetList = []
  contStore.contSummaryList = []
  paymentStore.paySumList = []
  paymentStore.paymentList = []
  paymentStore.payOrderList = []
  paymentStore.paymentsCount = 0
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => dataSetup(project.value || projStore.initProjId))

const loading = ref(true)
onBeforeRouteLeave(async () => {
  paymentStore.paymentList = []
  paymentStore.paymentsCount = 0
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
  >
    <PaymentSummary :project="project as number" />
  </ContentHeader>

  <ContentBody>
    <CCardBody class="pb-5">
      <ListController
        ref="listControl"
        :by-cont="paymentBy === '2'"
        @payment-filtering="listFiltering"
      />
      <TableTitleRow excel :url="excelUrl" :disabled="!project">
        <v-radio-group
          v-model="paymentBy"
          inline
          size="sm"
          density="compact"
          color="success"
          class="d-flex flex-row-reverse"
          style="font-size: 0.8em"
          :disabled="!project"
        >
          <v-radio label="수납건별" value="1" class="pt-1 pr-3" />
          <v-radio label="계약자별" value="2" class="pt-1" />
        </v-radio-group>
      </TableTitleRow>
      <PaymentList
        :page="filterItems.page as number"
        :project="project as number"
        @pay-match="payMatch"
        @page-select="pageSelect"
      />
    </CCardBody>
  </ContentBody>
</template>
