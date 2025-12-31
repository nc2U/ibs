<script lang="ts" setup>
import Cookies from 'js-cookie'
import { ref, computed, onBeforeMount, onMounted, onUpdated, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/payments/_menu/headermixin'
import { dateFormat } from '@/utils/baseMixins'
import { downloadFile } from '@/utils/helper.ts'
import { write_payment } from '@/utils/pageAuth'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { type Contract } from '@/store/types/contract'
import type { Project } from '@/store/types/project.ts'
import { type ContFilter, useContract } from '@/store/pinia/contract'
import { useProCash } from '@/store/pinia/proCash'
import { type ProjectCashBook, type CashBookFilter } from '@/store/types/proCash'
import { type DownPayFilter, type PriceFilter, usePayment } from '@/store/pinia/payment'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PaymentAuthGuard from '@/components/AuthGuard/PaymentAuthGuard.vue'
import ContChoicer from '@/views/payments/Register/components/ContChoicer.vue'
import PaymentListAll from '@/views/payments/Register/components/PaymentListAll.vue'
import OrdersBoard from '@/views/payments/Register/components/OrdersBoard.vue'
import CreateButton from '@/views/payments/Register/components/CreateButton.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const paymentId = ref<string>('')
const date = ref(dateFormat(new Date()))

const isCalc = ref(Cookies.get('isCalc') ?? '1')
watch(isCalc, newVal => Cookies.set('isCalc', newVal))

const paymentUrl = computed(() => {
  const url = '/pdf/payments/'
  const proj = project.value ?? ''
  const cont = contract.value?.pk ?? ''
  return `${url}?project=${proj}&contract=${cont}&is_calc=${isCalc.value}&pub_date=${date.value ?? ''}`
})

const calcUrl = computed(() => {
  const url = '/pdf/calculation/'
  const proj = project.value ?? ''
  const cont = contract.value?.pk ?? ''
  return `${url}?project=${proj}&contract=${cont}&pub_date=${date.value ?? ''}`
})

const lateFeeUrl = computed(() => {
  const url = '/pdf/daily-late-fee/'
  const cont = contract.value?.pk ?? ''
  return `${url}?contract=${cont}&pub_date=${date.value ?? ''}`
})

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const contractStore = useContract()
const contract = computed(() => contractStore.contract as Contract | null)

const paymentStore = usePayment()
const AllPaymentList = computed(() => paymentStore.AllPaymentList)

const projectDataStore = useProjectData()
const fetchTypeList = (projId: number) => projectDataStore.fetchTypeList(projId)

const fetchAllPaymentList = (payload: CashBookFilter) => paymentStore.fetchAllPaymentList(payload)
const fetchPayOrderList = (projId: number) => paymentStore.fetchPayOrderList(projId)
const fetchDownPayList = (payload: DownPayFilter) => paymentStore.fetchDownPayList(payload)
const fetchPriceList = (payload: PriceFilter) => paymentStore.fetchPriceList(payload)

const proCashStore = useProCash()
const fetchAllProBankAccList = (projId: number) => proCashStore.fetchAllProBankAccList(projId)
const createPrCashBook = (
  payload: ProjectCashBook & { sepData: ProjectCashBook | null } & {
    filters: CashBookFilter
  },
) => proCashStore.createPrCashBook(payload)
const updatePrCashBook = (
  payload: ProjectCashBook & {
    sepData: ProjectCashBook | null
  } & { isPayment?: boolean } & {
    filters: CashBookFilter
  },
) => proCashStore.updatePrCashBook(payload)
const deletePrCashBook = (
  payload: { pk: number; project: number; contract: number } & {
    filters: CashBookFilter
  },
) => proCashStore.deletePrCashBook(payload)

const fetchContractList = (payload: ContFilter) => contractStore.fetchContractList(payload)
const fetchContract = (pk: number) => contractStore.fetchContract(pk)

const [route, router] = [useRoute(), useRouter()]

// contract와 project 모두 watch
watch(
  [contract, project],
  ([newContract, newProject], [oldContract, oldProject]) => {
    // 같은 contract와 project면 스킵 (중복 로드 방지)
    if (oldContract && newContract?.pk === oldContract?.pk && oldProject === newProject) {
      return
    }

    // 이미 로딩 중이면 스킵 (race condition 방지)
    if (isLoadingPaymentList.value) {
      return
    }

    if (newContract && newProject) {
      isLoadingPaymentList.value = true
      const order_group = newContract.order_group
      const unit_type = newContract.unit_type
      fetchPriceList({ project: newProject, order_group, unit_type })
      fetchDownPayList({ project: newProject, order_group, unit_type })
      fetchAllPaymentList({
        project: newProject,
        contract: newContract.pk,
        ordering: 'deal_date',
      }).finally(() => {
        isLoadingPaymentList.value = false
      })
    } else if (!newContract) {
      // contract가 null일 때만 clear (project가 없는 경우는 clear 하지 않음)
      paymentStore.priceList = []
      paymentStore.downPayList = []
      paymentStore.AllPaymentList = []
    }
  },
  { immediate: false, deep: false },
)

const onContFiltering = (payload: ContFilter) => {
  payload.project = project.value
  if (payload.project) fetchContractList({ ...payload })
}

const getContract = (cont: number) => {
  router.push({
    name: '건별 수납 관리 - 상세',
    params: { contractId: cont },
  })
}

const onCreate = (
  payload: ProjectCashBook & { sepData: ProjectCashBook | null } & {
    filters: CashBookFilter
  },
) => {
  if (project.value) payload.project = project.value
  createPrCashBook(payload)
}

const onUpdate = (
  payload: ProjectCashBook & { sepData: ProjectCashBook | null } & {
    filters: CashBookFilter
  },
) => {
  if (project.value) payload.project = project.value
  updatePrCashBook({ ...payload, isPayment: true })
}

const onDelete = (pk: number) => {
  const delFilter = {
    pk,
    project: project.value || 1,
    contract: contract.value?.pk || 1,
  }
  deletePrCashBook({ ...delFilter, ...{ filters: {} } })
}

const dataSetup = (pk: number) => {
  fetchTypeList(pk)
  fetchPayOrderList(pk)
  fetchAllProBankAccList(pk)
}

const dataReset = () => {
  contractStore.contract = null
  contractStore.contractList = []
  projectDataStore.unitTypeList = []
  paymentStore.AllPaymentList = []
  paymentStore.payOrderList = []
  proCashStore.proBankAccountList = []
}

const projSelect = (target: number | null) => {
  router.replace({ name: '건별 수납 관리' })
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
const isLoadingContract = ref(false)
const isLoadingPaymentList = ref(false)

onBeforeMount(async () => {
  dataSetup(project.value || projStore.initProjId)
  loading.value = false
})

onMounted(async () => {
  if (route.params.contractId) {
    const cont = Number(route.params.contractId)

    // 새로고침 시 데이터가 남아있을 수 있으므로 초기화
    contractStore.contract = null
    paymentStore.AllPaymentList = []

    isLoadingContract.value = true
    await fetchContract(cont)
    isLoadingContract.value = false

    // fetchContract 완료 후 명시적으로 데이터 로드
    // watch가 project 없어서 실행 안 했을 경우를 대비
    if (contract.value && project.value && !isLoadingPaymentList.value) {
      try {
        isLoadingPaymentList.value = true
        const order_group = contract.value.order_group
        const unit_type = contract.value.unit_type
        await fetchPriceList({ project: project.value, order_group, unit_type })
        await fetchDownPayList({ project: project.value, order_group, unit_type })
        await fetchAllPaymentList({
          project: project.value,
          contract: contract.value.pk,
          ordering: 'deal_date',
        })
      } finally {
        isLoadingPaymentList.value = false
      }
    }
  } else {
    contractStore.contract = null
    paymentStore.AllPaymentList = []
  }

  if (route.query.payment) paymentId.value = route.query.payment as string
})

onUpdated(async () => {
  // 이미 로딩 중이면 중복 호출 방지
  if (isLoadingContract.value) return

  if (route.params.contractId) {
    const cont = Number(route.params.contractId)
    // contract가 없거나, 다른 contract로 변경된 경우만 로드
    if (!contract.value || contract.value.pk !== cont) {
      isLoadingContract.value = true
      await fetchContract(cont)
      isLoadingContract.value = false
    }
  }
})

onBeforeRouteLeave(() => {
  contractStore.contract = null
  paymentStore.AllPaymentList = []
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
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <ContChoicer
          ref="listControl"
          :project="project || undefined"
          :contract="contract as Contract"
          :payment-url="paymentUrl"
          @list-filtering="onContFiltering"
          @get-contract="getContract"
        />
        <TableTitleRow
          :disabled="!project || !contract"
          pdf
          :url="paymentUrl"
          filename="납부_확인서.pdf"
        >
          <v-radio-group
            v-model="isCalc"
            inline
            size="sm"
            density="compact"
            color="success"
            style="font-size: 0.8em"
            class="d-flex flex-row-reverse"
            :disabled="!project || !contract"
          >
            <span v-show="project && contract" class="mr-3">
              <DatePicker v-model="date" placeholder="발행일자" />
              <v-tooltip activator="parent" location="top">발행일자</v-tooltip>
            </span>

            <v-btn
              v-if="project === 1"
              flat
              :disabled="!project || !contract"
              color="light"
              size="small"
              class="mt-1 mr-2"
              @click="downloadFile(calcUrl, '할인_가산금_내역.pdf')"
              style="text-decoration: none"
            >
              공급계약 미체결 연체료(동춘조합 한정)
            </v-btn>

            <v-btn
              flat
              :disabled="!project || !contract"
              color="light"
              size="small"
              class="mt-1 mr-2"
              @click="downloadFile(lateFeeUrl, '일자별_연체료_내역.pdf')"
              style="text-decoration: none"
            >
              일자별 연체료
            </v-btn>

            <span>
              <v-radio label="일반용(미납내역)" value="1" class="mt-1" />
              <v-tooltip activator="parent" location="top">연체/가산정보 포함</v-tooltip>
            </span>
            <span>
              <v-radio label="확인용" value="" class="mt-1" />
              <v-tooltip activator="parent" location="top">연체/가산정보 미포함</v-tooltip>
            </span>
          </v-radio-group>
        </TableTitleRow>
        <CRow>
          <CCol lg="7">
            <PaymentListAll
              :contract="contract as Contract"
              :payment-id="paymentId"
              :payment-list="AllPaymentList"
              @on-update="onUpdate"
              @on-delete="onDelete"
            />

            <CreateButton
              v-if="write_payment"
              :contract="contract as Contract"
              @on-create="onCreate"
            />
          </CCol>
          <CCol lg="5">
            <OrdersBoard :contract="contract as Contract" :payment-list="AllPaymentList" />
          </CCol>
        </CRow>
      </CCardBody>
    </ContentBody>
  </PaymentAuthGuard>
</template>
