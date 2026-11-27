<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/notices/_menu/headermixin.ts'
import { useNotice } from '@/store/pinia/notice.ts'
import { useProject } from '@/store/pinia/project.ts'
import { usePayment } from '@/store/pinia/payment.ts'
import { useProjectData } from '@/store/pinia/project_data.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { getToday } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { PayOrder } from '@/store/types/payment'
import type { SalesBillIssue } from '@/store/types/notice'
import type { ContFilter } from '@/store/types/contract'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import Loading from '@/components/Loading/Index.vue'
import NoticeAuthGuard from '@/components/AuthGuard/NoticeAuthGuard.vue'
import SalesBillIssueForm from './components/SalesBillIssueForm.vue'
import ListController from './components/ListController.vue'
import DownloadButton from './components/DownloadButton.vue'
import ContractList from './components/ContractList.vue'

const { can, PERM } = usePerms()
const canNoticeRead = computed(() => can(PERM.NOTICE_READ))

const listControl = ref()
const contractListRef = ref()
const limit = ref(10)

const cont_ids = ref<number[]>([])
const printData = reactive({
  is_bill_issue: false,
  project: null as null | number,
  pub_date: getToday(),
})

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const noticeStore = useNotice()
const billIssue = computed(() => noticeStore.billIssue)

const fetchSalesBillIssue = (projId: number) => noticeStore.fetchSalesBillIssue(projId)
const createSalesBillIssue = (payload: SalesBillIssue) => noticeStore.createSalesBillIssue(payload)
const patchSalesBillIssue = (payload: SalesBillIssue) => noticeStore.patchSalesBillIssue(payload)

const paymentStore = usePayment()
const payOrder = computed(() => paymentStore.payOrder as PayOrder | null)

const payOrderCode = computed(() => payOrder.value?.pay_code ?? payOrder.value?.pay_time ?? 0)
const payOrderName = computed(() => (payOrder.value ? payOrder.value.str_display : ''))

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

watch(billIssue, (val: SalesBillIssue | null) => {
  printData.is_bill_issue = !!val
  if (val) {
    printData.project = val.project
    if (val.now_payment_order) fetchPayOrder(val.now_payment_order)
    else paymentStore.payOrder = null
  } else {
    paymentStore.payOrder = null
  }
})

const pageSelect = (page: number) => {
  cont_ids.value = []
  listControl.value?.listFiltering(page)
}

const listFiltering = (payload: ContFilter) => {
  cont_ids.value = []
  if ((payload.page ?? 1) === 1) {
    contractListRef.value?.resetSelection(1)
  }
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
    if (i > -1) contractors.splice(i, 1)
  }
}

const allUnChecked = () => (cont_ids.value = [])

const getNowOrder = (orderPk: number | null) => {
  if (orderPk) fetchPayOrder(orderPk)
  else paymentStore.payOrder = null
}

const setPubDate = (payload: string) => (printData.pub_date = payload)

const onSubmit = async (payload: SalesBillIssue & { now_due_date: string | null }) => {
  const { pk, now_payment_order } = payload
  const { now_due_date, ...bill_data } = payload

  if (now_payment_order && (payOrder.value?.pay_due_date || null) !== (now_due_date || null)) {
    await patchPayOrder({
      pk: now_payment_order,
      pay_due_date: now_due_date || undefined,
    })
  }

  if (pk) await patchSalesBillIssue(bill_data)
  else await createSalesBillIssue(bill_data)
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
  paymentStore.payOrder = null
  projectDataStore.unitTypeList = []
  projectDataStore.buildingList = []
  cont_ids.value = []
  limit.value = 10
  printData.is_bill_issue = false
  printData.project = null
  listControl.value?.clearFilters()
  contractListRef.value?.resetSelection(1)
}

watch(
  [project, canNoticeRead],
  ([newProj, hasRead], [oldProj, oldRead]) => {
    if (newProj !== oldProj || hasRead !== oldRead) {
      dataReset()
      if (newProj && hasRead) dataSetup(newProj)
    }
  },
  { immediate: true },
)
</script>

<template>
  <NoticeAuthGuard>
    <Loading v-model:active="isLoading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="pb-5">
        <SalesBillIssueForm
          :project="project || undefined"
          :bill-issue="billIssue"
          @get-now-order="getNowOrder"
          @set-pub-date="setPubDate"
          @on-submit="onSubmit"
        />
        <ListController
          ref="listControl"
          :now-order-name="payOrderName"
          @list-filtering="listFiltering"
        />
        <DownloadButton v-if="canNoticeRead" :print-data="printData" :contracts="cont_ids" />
        <ContractList
          ref="contractListRef"
          :now-order="payOrderCode || undefined"
          :limit="limit"
          @on-cont-chk="onContChk"
          @page-select="pageSelect"
          @all-un-checked="allUnChecked"
        />
      </CCardBody>
    </ContentBody>
  </NoticeAuthGuard>
</template>
