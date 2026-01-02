<script lang="ts" setup>
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/notices/_menu/headermixin'
import { getToday } from '@/utils/baseMixins'
import { useNotice } from '@/store/pinia/notice'
import { useProject } from '@/store/pinia/project'
import { usePayment } from '@/store/pinia/payment'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import { type PayOrder } from '@/store/types/payment'
import { type SalesBillIssue } from '@/store/types/notice'
import type { ContFilter } from '@/store/types/contract'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import Loading from '@/components/Loading/Index.vue'
import NoticeAuthGuard from '@/components/AuthGuard/NoticeAuthGuard.vue'
import SalesBillIssueForm from '@/views/notices/Bill/components/SalesBillIssueForm.vue'
import ListController from '@/views/notices/Bill/components/ListController.vue'
import DownloadButton from '@/views/notices/Bill/components/DownloadButton.vue'
import ContractList from '@/views/notices/Bill/components/ContractList.vue'

const listControl = ref()
const limit = ref(10)

const cont_ids = ref([])
const printData = reactive({
  is_bill_issue: false,
  project: null as null | number,
  pub_date: getToday(),
})

const projStore = useProject()
const project = computed(() => (projStore.project as any)?.pk)

const noticeStore = useNotice()
const billIssue = computed(() => noticeStore.billIssue)

const fetchSalesBillIssue = (projId: number) => noticeStore.fetchSalesBillIssue(projId)
const createSalesBillIssue = (payload: SalesBillIssue) => noticeStore.createSalesBillIssue(payload)
const patchSalesBillIssue = (payload: SalesBillIssue) => noticeStore.patchSalesBillIssue(payload)

const paymentStore = usePayment()
const payOrder = computed(() => paymentStore.payOrder as PayOrder | null)

const payOrderTime = computed(() => (payOrder.value ? payOrder.value.pay_time : 0))
const payOrderName = computed(() => (payOrder.value ? payOrder.value.__str__ : ''))

const fetchPayOrder = (pk: number) => paymentStore.fetchPayOrder(pk)
const patchPayOrder = (payload: PayOrder) => paymentStore.patchPayOrder(payload)
const fetchPayOrderList = (projId: number) => paymentStore.fetchPayOrderList(projId)

const projectDataStore = useProjectData()
const fetchTypeList = (projId: number) => projectDataStore.fetchTypeList(projId)
const fetchBuildingList = (projId: number) => projectDataStore.fetchBuildingList(projId)

const contractStore = useContract()
const isLoading = computed(() => contractStore.isLoading)
const fetchOrderGroupList = (projId: number) => contractStore.fetchOrderGroupList(projId)
const fetchContractList = (payload: ContFilter) => contractStore.fetchContractList(payload)
const fetchSalePriceList = (payload: { project: number }) =>
  contractStore.fetchSalePriceList(payload)
const fetchDownPayList = (payload: { project: number }) => contractStore.fetchDownPayList(payload)

watch(billIssue, (val: any) => {
  if (val) {
    printData.is_bill_issue = !!val
    printData.project = val.project
    if (val.now_payment_order) fetchPayOrder(val.now_payment_order)
  }
})

const pageSelect = (page: number) => {
  cont_ids.value = []
  listControl.value.listFiltering(page)
}

const listFiltering = (payload: ContFilter) => {
  cont_ids.value = []
  payload.project = project.value
  payload.limit = payload.limit || 10
  limit.value = payload.limit
  if (payload.project) fetchContractList(payload)
}

const onContChk = (payload: { chk: boolean; pk: number }) => {
  const contractors: number[] = cont_ids.value
  if (payload.chk) {
    if (!contractors.includes(payload.pk)) contractors.push(payload.pk)
  } else {
    const i = contractors.indexOf(payload.pk)
    contractors.splice(i, 1)
  }
}

const allUnChecked = () => (cont_ids.value = [])

const getNowOrder = (orderPk: number) => fetchPayOrder(orderPk)

const setPubDate = (payload: string) => (printData.pub_date = payload)

const onSubmit = (payload: SalesBillIssue & { now_due_date: string }) => {
  const { pk, now_payment_order } = payload
  const { now_due_date, ...bill_data } = payload

  if (payOrder.value?.pay_due_date !== now_due_date) {
    patchPayOrder({
      pk: now_payment_order,
      pay_due_date: now_due_date,
    })
  }

  if (pk) patchSalesBillIssue(bill_data)
  else createSalesBillIssue(bill_data)
}

const dataSetup = (pk: number) => {
  fetchSalesBillIssue(pk)
  fetchPayOrderList(pk)
  fetchOrderGroupList(pk)
  fetchTypeList(pk)
  fetchBuildingList(pk)
  fetchContractList({
    project: pk,
    ordering: 'contractor__name',
  })
  fetchSalePriceList({ project: pk })
  fetchDownPayList({ project: pk })
  printData.project = pk
}

const dataReset = () => {
  contractStore.orderGroupList = []
  contractStore.contractList = []
  contractStore.contractsCount = 0
  contractStore.salesPriceList = []
  contractStore.downPaymentList = []
  noticeStore.billIssue = null
  paymentStore.payOrderList = []
  projectDataStore.unitTypeList = []
  projectDataStore.buildingList = []
  printData.project = null
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => dataSetup(project.value || projStore.initProjId))
</script>

<template>
  <NoticeAuthGuard>
    <Loading v-model:active="isLoading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <SalesBillIssueForm
          :project="project || undefined"
          :bill-issue="billIssue as SalesBillIssue"
          @get-now-order="getNowOrder"
          @set-pub-date="setPubDate"
          @on-submit="onSubmit"
        />
        <ListController
          ref="listControl"
          :now-order-name="payOrderName"
          @list-filtering="listFiltering"
        />
        <DownloadButton :print-data="printData" :contracts="cont_ids" />
        <ContractList
          :now-order="payOrderTime || undefined"
          :limit="limit"
          @on-cont-chk="onContChk"
          @page-select="pageSelect"
          @all-un-checked="allUnChecked"
        />
      </CCardBody>
    </ContentBody>
  </NoticeAuthGuard>
</template>
