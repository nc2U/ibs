<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/payment/_menu/headermixin.ts'
import { useProject } from '@/store/pinia/project.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { useProjectData } from '@/store/pinia/project_data.ts'
import { usePayment } from '@/store/pinia/payment.ts'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { onBeforeRouteLeave } from 'vue-router'
import type { ContractPaymentPatchPayload, ContPayFilter } from '@/store/types/payment.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PaymentAuthGuard from '@/components/AuthGuard/PaymentAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import PaymentSummary from './components/PaymentSummary.vue'
import ListController from './components/ListController.vue'
import PaymentList from './components/PaymentList.vue'

type PayMatchPayload = ContractPaymentPatchPayload & { trans_id: number | null }

const { can, PERM } = usePerms()
const canPaymentRead = computed(() => can(PERM.PAYMENT_READ))
const canPaymentMatch = computed(() => can(PERM.PAYMENT_CREATE) || can(PERM.PAYMENT_UPDATE))

const listControl = ref<InstanceType<typeof ListController> | null>(null)
const createDefaultFilters = (): ContPayFilter => ({
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
const filterItems = ref<ContPayFilter>(createDefaultFilters())

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

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
const patchContractPayment = (transPk: number, payload: ContractPaymentPatchPayload) =>
  paymentStore.patchContractPayment(transPk, payload)

const proLedgerStore = useProLedger()
const fetchAllProBankAccList = (projId: number) => proLedgerStore.fetchAllProBankAccList(projId)

const listFiltering = (payload: ContPayFilter) => {
  filterItems.value = payload
  if (project.value && canPaymentRead.value) {
    payload.project = project.value
    fetchPaymentList(payload)
  }
}

const payMatch = async (payload: PayMatchPayload) => {
  if (!canPaymentMatch.value) return
  const { trans_id, ...patchData } = payload
  if (!trans_id) return
  await patchContractPayment(trans_id, patchData)
  if (project.value) await fetchPaymentSummaryList(project.value)
}

const pageSelect = (page: number) => {
  filterItems.value.page = page
  listControl.value?.listFiltering(page)
}

const byPayment = computed(() => {
  if (!project.value) return ''
  const params = new URLSearchParams({ project: String(project.value) })
  if (filterItems.value.from_date) params.set('sd', filterItems.value.from_date)
  if (filterItems.value.to_date) params.set('ed', filterItems.value.to_date)
  if (filterItems.value.order_group) params.set('og', filterItems.value.order_group)
  if (filterItems.value.unit_type) params.set('ut', filterItems.value.unit_type)
  if (filterItems.value.pay_order) params.set('ipo', filterItems.value.pay_order)
  if (filterItems.value.pay_account) params.set('ba', String(filterItems.value.pay_account))
  if (filterItems.value.no_contract) params.set('nc', 'true')
  if (filterItems.value.no_install) params.set('ni', 'true')
  if (filterItems.value.search) params.set('q', filterItems.value.search)
  return `/excel/ledger/payment/?${params.toString()}`
})

const byContract = computed(() => {
  if (!project.value) return ''
  const params = new URLSearchParams({ project: String(project.value) })
  if (filterItems.value.to_date) params.set('to_date', filterItems.value.to_date)
  return `/excel/ledger/paid-by-cont/?${params.toString()}`
})

const paymentBy = ref(localStorage.getItem('paymentBy') ?? '1') // 다운로드할 파일 선택

watch(paymentBy, newVal => localStorage.setItem('paymentBy', newVal))

const excelUrl = computed(() => (paymentBy.value === '1' ? byPayment.value : byContract.value))
const filename = computed(() =>
  paymentBy.value === '1' ? '수납건별_납부현황' : '계약자별_납부현황',
)

const dataSetup = async (pk: number) => {
  await Promise.all([
    fetchOrderGroupList(pk),
    fetchTypeList(pk),
    fetchIncBudgetList(pk),
    fetchContSummaryList(pk),
    fetchPaymentSummaryList(pk),
    fetchPaymentList({ project: pk }),
    fetchPayOrderList(pk),
    fetchAllProBankAccList(pk),
  ])
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
  filterItems.value = createDefaultFilters()
  listControl.value?.resetFilters()
}

const loading = ref(false)
watch(
  [project, canPaymentRead],
  async ([newProj, hasRead], [oldProj, oldRead]) => {
    if (newProj !== oldProj || hasRead !== oldRead) {
      dataReset()
      if (newProj && hasRead) {
        loading.value = true
        try {
          await dataSetup(newProj)
        } finally {
          loading.value = false
        }
      }
    }
  },
  { immediate: true },
)

onBeforeRouteLeave(async () => {
  paymentStore.ledgerPaymentList = []
  paymentStore.ledgerPaymentsCount = 0
})
</script>

<template>
  <PaymentAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect">
      <PaymentSummary :project="project" />
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
            <v-radio label="수납건별" value="1" class="pt-1 pe-3" />
            <v-radio label="계약자별" value="2" class="pt-1" />
          </v-radio-group>
        </TableTitleRow>
        <PaymentList
          :page="filterItems.page || 1"
          :project="project as number"
          @pay-match="payMatch"
          @page-select="pageSelect"
        />
      </CCardBody>
    </ContentBody>
  </PaymentAuthGuard>
</template>
