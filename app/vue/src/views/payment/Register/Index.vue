<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/payment/_menu/headermixin.ts'
import { downloadFile } from '@/utils/helper.ts'
import { useProject } from '@/store/pinia/project.ts'
import { useProjectData } from '@/store/pinia/project_data.ts'
import { usePayment } from '@/store/pinia/payment.ts'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { dateFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import type { Contract } from '@/store/types/contract.ts'
import type { ProAccountFilter } from '@/store/types/proLedger.ts'
import type {
  ContractPaymentPayload,
  ContPayFilter,
  DownPayFilter,
  PriceFilter,
} from '@/store/types/payment.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PaymentAuthGuard from '@/components/AuthGuard/PaymentAuthGuard.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ContChoicer from './components/ContChoicer.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import PaymentListAll from './components/PaymentListAll.vue'
import OrdersBoard from './components/OrdersBoard.vue'
import CreateButton from './components/CreateButton.vue'

const { can, PERM } = usePerms()
const canPaymentRead = computed(() => can(PERM.PAYMENT_READ))
const canPaymentCreate = computed(() => can(PERM.PAYMENT_CREATE))
const canPaymentUpdate = computed(() => can(PERM.PAYMENT_UPDATE))
const canPaymentDelete = computed(() => can(PERM.PAYMENT_DELETE))

const date = ref(dateFormat(new Date()))

const isCalc = ref(localStorage.getItem('isCalc') ?? '1')
watch(isCalc, newVal => localStorage.setItem('isCalc', newVal))

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const projectDataStore = useProjectData()
const fetchTypeList = (projId: number) => projectDataStore.fetchTypeList(projId)

const paymentStore = usePayment()
const ledgerAllPaymentList = computed(() => paymentStore.ledgerAllPaymentList)

const fetchLedgerAllPaymentList = (payload: ContPayFilter) =>
  paymentStore.fetchLedgerAllPaymentList(payload)
const fetchPayOrderList = (projId: number) => paymentStore.fetchPayOrderList(projId)
const fetchDownPayList = (payload: DownPayFilter) => paymentStore.fetchDownPayList(payload)
const fetchPriceList = (payload: PriceFilter) => paymentStore.fetchPriceList(payload)

const proLedgerStore = useProLedger()
const fetchAllProBankAccList = (projId: number) => proLedgerStore.fetchAllProBankAccList(projId)
const fetchProjectAccounts = (payload: ProAccountFilter) =>
  proLedgerStore.fetchProjectAccounts(payload)

const contractStore = useContract()
const contract = computed(() => contractStore.contract)
const fetchContract = (pk: number) => contractStore.fetchContract(pk)

const [route, router] = [useRoute(), useRouter()]
const paymentId = computed(() => (route.query.payment ? String(route.query.payment) : ''))

const paymentUrl = computed(() => {
  const url = '/pdf/ledger/payment/'
  const proj = project.value ?? ''
  const cont = contract.value?.pk ?? ''
  return `${url}?project=${proj}&contract=${cont}&is_calc=${isCalc.value}&pub_date=${date.value ?? ''}`
})

const calcUrl = computed(() => {
  const url = '/pdf/ledger/calculation/'
  const proj = project.value ?? ''
  const cont = contract.value?.pk ?? ''
  return `${url}?project=${proj}&contract=${cont}&pub_date=${date.value ?? ''}`
})

const lateFeeUrl = computed(() => {
  const url = '/pdf/ledger/daily-late-fee/'
  const cont = contract.value?.pk ?? ''
  return `${url}?contract=${cont}&pub_date=${date.value ?? ''}`
})

const isLoadingContract = ref(false)
const isLoadingPaymentList = ref(false)

// contract와 project 모두 watch — 단일 진입점으로 중복 요청 및 race condition 방지
watch(
  [contract, project, canPaymentRead],
  async ([newContract, newProject, hasRead], [oldContract, oldProject]) => {
    if (!hasRead) return
    if (oldContract && newContract?.pk === oldContract?.pk && oldProject === newProject) {
      return
    }

    if (newContract && newProject) {
      if (isLoadingPaymentList.value) return
      isLoadingPaymentList.value = true
      const order_group = newContract.order_group
      const unit_type = newContract.unit_type ?? undefined
      try {
        await Promise.all([
          fetchPriceList({ project: newProject, order_group, unit_type }),
          fetchDownPayList({ project: newProject, order_group, unit_type }),
          fetchLedgerAllPaymentList({
            project: newProject,
            contract: newContract.pk,
            ordering: 'deal_date',
          }),
        ])
      } finally {
        isLoadingPaymentList.value = false
      }
    } else if (!newContract) {
      paymentStore.priceList = []
      paymentStore.downPayList = []
      paymentStore.ledgerAllPaymentList = []
    }
  },
  { immediate: false, deep: false },
)

const getContract = (cont: number) => {
  router.push({
    name: '건별 납부 관리 - 상세',
    params: { contractId: cont },
  })
}

const createContractPayment = (payload: ContractPaymentPayload) =>
  paymentStore.createContractPayment(payload)
const updateContractPayment = (bankTransactionId: number, payload: ContractPaymentPayload) =>
  paymentStore.updateContractPayment(bankTransactionId, payload)
const deleteContractPayment = (bankTransactionId: number) =>
  paymentStore.deleteContractPayment(bankTransactionId)

const onCreate = async (payload: ContractPaymentPayload, done?: (ok: boolean) => void) => {
  if (!canPaymentCreate.value) {
    done?.(false)
    return
  }
  try {
    if (project.value) payload.project = project.value
    await createContractPayment(payload)
    if (contract.value?.pk) await fetchContract(contract.value.pk)
    done?.(true)
  } catch {
    done?.(false)
  }
}

const onUpdate = async (
  bankTransactionId: number,
  payload: ContractPaymentPayload,
  done?: (ok: boolean) => void,
) => {
  if (!canPaymentUpdate.value) {
    done?.(false)
    return
  }
  try {
    if (project.value) payload.project = project.value
    await updateContractPayment(bankTransactionId, payload)
    if (contract.value?.pk) await fetchContract(contract.value.pk)
    done?.(true)
  } catch {
    done?.(false)
  }
}

const onDelete = async (bankTransactionId: number, done?: (ok: boolean) => void) => {
  if (!canPaymentDelete.value) {
    done?.(false)
    return
  }
  try {
    await deleteContractPayment(bankTransactionId)
    if (contract.value?.pk) await fetchContract(contract.value.pk)
    done?.(true)
  } catch {
    done?.(false)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    fetchTypeList(pk),
    fetchPayOrderList(pk),
    fetchAllProBankAccList(pk),
    fetchProjectAccounts({ is_payment: true, is_active: true }),
  ])
}

const dataReset = () => {
  contractStore.contract = null
  contractStore.contractList = []
  projectDataStore.unitTypeList = []
  proLedgerStore.allProBankList = []
  paymentStore.priceList = []
  paymentStore.downPayList = []
  paymentStore.ledgerAllPaymentList = []
  paymentStore.payOrderList = []
}

const loadContractData = async (contractId: number) => {
  if (isLoadingContract.value || !canPaymentRead.value) return
  isLoadingContract.value = true
  try {
    await fetchContract(contractId)
  } finally {
    isLoadingContract.value = false
  }
}

const loading = ref(false)
watch(
  [project, canPaymentRead],
  async ([newProj, hasRead], [oldProj, oldRead]) => {
    if (newProj !== oldProj || hasRead !== oldRead) {
      if (oldProj !== undefined && newProj !== oldProj && route.params.contractId) {
        router.replace({ name: '건별 납부 관리' })
      }
      dataReset()
      if (newProj && hasRead) {
        loading.value = true
        try {
          await dataSetup(newProj)
          const contId = route.params.contractId ? Number(route.params.contractId) : null
          if (contId) await loadContractData(contId)
        } finally {
          loading.value = false
        }
      }
    }
  },
  { immediate: true },
)

watch(
  () => route.params.contractId,
  async newId => {
    if (!canPaymentRead.value) return
    if (newId) {
      const contId = Number(newId)
      if (!contract.value || contract.value.pk !== contId) {
        await loadContractData(contId)
      }
    } else {
      contractStore.contract = null
      paymentStore.ledgerAllPaymentList = []
    }
  },
)

onBeforeRouteLeave(() => {
  contractStore.contract = null
  paymentStore.ledgerAllPaymentList = []
})
</script>

<template>
  <PaymentAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      :selectable="!contract"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <ContChoicer
          :project="project || undefined"
          :contract="contract as Contract"
          :payment-url="paymentUrl"
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
            <span v-show="project && contract" class="me-3">
              <DatePicker v-model="date" placeholder="발행일자" />
              <v-tooltip activator="parent" location="top">발행일자</v-tooltip>
            </span>

            <v-btn
              v-if="project === 1"
              :disabled="!project || !contract"
              variant="tonal"
              size="small"
              class="mt-1 me-2"
              @click="downloadFile(calcUrl, '할인_가산금_내역.pdf')"
              style="text-decoration: none"
            >
              선납할인 · 연체가산 내역서
            </v-btn>

            <v-btn
              :disabled="!project || !contract"
              variant="tonal"
              size="small"
              class="mt-1 me-2"
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
              :payment-list="ledgerAllPaymentList"
              @on-update="onUpdate"
              @on-delete="onDelete"
            />

            <CreateButton
              v-if="canPaymentCreate"
              :contract="contract as Contract"
              @on-create="onCreate"
            />
          </CCol>
          <CCol lg="5">
            <OrdersBoard :contract="contract as Contract" :payment-list="ledgerAllPaymentList" />
          </CCol>
        </CRow>
      </CCardBody>
    </ContentBody>
  </PaymentAuthGuard>
</template>
