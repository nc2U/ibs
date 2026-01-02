<script lang="ts" setup>
import Cookies from 'js-cookie'
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/payment/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import { usePayment } from '@/store/pinia/payment'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { onBeforeRouteLeave } from 'vue-router'
import type { Project } from '@/store/types/project.ts'
import type { CompositeTransactionPayload, ContPayFilter } from '@/store/types/payment.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PaymentAuthGuard from '@/components/AuthGuard/PaymentAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import PaymentSummary from './components/PaymentSummary.vue'
import ListController from './components/ListController.vue'
import PaymentList from './components/PaymentList.vue'

const listControl = ref()
const filterItems = ref<ContPayFilter>({
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
const project = computed(() => (projStore.project as Project)?.pk)

const fetchIncBudgetList = (proj: number) => projStore.fetchIncBudgetList(proj)

const contStore = useContract()
const fetchOrderGroupList = (projId: number) => contStore.fetchOrderGroupList(projId)
const fetchContSummaryList = (projId: number) => contStore.fetchContSummaryList(projId)

const proDataStore = useProjectData()
const fetchTypeList = (projId: number) => proDataStore.fetchTypeList(projId)

const paymentStore = usePayment()
const fetchPaymentSummaryList = (projId: number) =>
  paymentStore.fetchLedgerPaymentSummaryList(projId)
const fetchPayOrderList = (projId: number) => paymentStore.fetchPayOrderList(projId)
const fetchPaymentList = (payload: ContPayFilter) => paymentStore.fetchLedgerPaymentList(payload)
const patchContractPayment = (transPk: number, payload: Partial<CompositeTransactionPayload>) =>
  paymentStore.patchContractPayment(transPk, payload)

const proLedgerStore = useProLedger()
const fetchAllProBankAccList = (projId: number) => proLedgerStore.fetchAllProBankAccList(projId)

const listFiltering = (payload: ContPayFilter) => {
  filterItems.value = payload
  if (project.value) {
    payload.project = project.value
    fetchPaymentList(payload)
  }
}

const payMatch = (payload: any) => {
  const { trans_id, ...patchData } = payload
  patchContractPayment(trans_id, patchData)
}

const pageSelect = (page: number) => {
  filterItems.value.page = page
  listControl.value.listFiltering(page)
}

const byPayment = computed(() => {
  let pUrl = project.value ? `/excel/ledger-payment/?project=${project.value}` : ''
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
const filename = computed(() =>
  paymentBy.value === '1' ? '수납건별_납부현황' : '계약자별_납부현황',
)

const dataSetup = async (pk: number) => {
  await fetchOrderGroupList(pk)
  await fetchTypeList(pk)
  await fetchIncBudgetList(pk)
  await fetchContSummaryList(pk)
  await fetchPaymentSummaryList(pk)
  await fetchPaymentList({ project: pk })
  await fetchPayOrderList(pk)
  await fetchAllProBankAccList(pk)
}

const dataReset = () => {
  contStore.orderGroupList = []
  proDataStore.unitTypeList = []
  proLedgerStore.allProBankList = []
  projStore.proIncBudgetList = []
  contStore.contSummaryList = []
  paymentStore.ledgerPaymentSummaryList = []
  paymentStore.ledgerPaymentList = []
  paymentStore.payOrderList = []
  paymentStore.ledgerPaymentsCount = 0
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup(project.value || projStore.initProjId)
  loading.value = false
})

onBeforeRouteLeave(async () => {
  paymentStore.ledgerPaymentList = []
  paymentStore.ledgerPaymentsCount = 0
})
</script>

<template>
  <PaymentAuthGuard>
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
        <TableTitleRow
          title="대금 납부 현황"
          excel
          :url="excelUrl"
          :filename="`${filename}.xlsx`"
          :disabled="!project"
        >
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
  </PaymentAuthGuard>
</template>
