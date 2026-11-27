<script lang="ts" setup>
import { ref, reactive, computed, nextTick, onBeforeMount, watch } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import { usePayment } from '@/store/pinia/payment.ts'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { getToday, diffDate } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { isValidate } from '@/utils/helper.ts'
import type { Contract } from '@/store/types/contract.ts'
import type {
  ContractPaymentPayload,
  OriginPayment,
  PaymentAccEntryInput,
  SiblingEntry,
} from '@/store/types/payment.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = withDefaults(
  defineProps<{
    contract?: Contract | null
    payment?: OriginPayment | null
  }>(),
  {
    contract: null,
    payment: null,
  },
)

const emit = defineEmits<{
  (e: 'on-submit', payload: ContractPaymentPayload, done?: (ok: boolean) => void): void
  (
    e: 'on-submit',
    bankTransactionId: number,
    payload: ContractPaymentPayload,
    done?: (ok: boolean) => void,
  ): void
  (e: 'on-delete', bankTransactionId: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { can, PERM } = usePerms()
const canPaymentManage = computed(() =>
  !props.payment ? can(PERM.PAYMENT_CREATE) : can(PERM.PAYMENT_UPDATE),
)

const refAlertModal = ref()
const delConfirmModal = ref()
const cngConfirmModal = ref()

const validated = ref(false)
const isSaving = ref(false)
const removeCont = ref(false)
const isInitializingForm = ref(false)
let nextEntryUid = 1

// ============================================
// Data Interfaces
// ============================================
interface BankTransactionForm {
  deal_date: string
  bank_account: number | null
  amount: number | null
  note: string
  sort: 1 // Always 입금 for payment
  content: string // Auto-generated from contract or preserved from existing tx
}

interface PaymentEntryForm {
  _uid: number
  pk?: number | null
  account: number | null
  amount: number | null
  trader: string
  contract: number | null
  installment_order: number | null
}

interface ReadonlyEntryForm {
  pk: number
  account: number
  account_name: string
  amount: number
  trader: string
}

// ============================================
// Form State - Separated Structure
// ============================================
const bankForm = reactive<BankTransactionForm>({
  deal_date: getToday(),
  bank_account: null,
  amount: null,
  note: '',
  sort: 1,
  content: '',
})

const paymentEntries = ref<PaymentEntryForm[]>([
  {
    _uid: nextEntryUid++,
    pk: null,
    account: null,
    amount: null,
    trader: '',
    contract: null,
    installment_order: null,
  },
])

const readonlyEntries = ref<ReadonlyEntryForm[]>([])
const canPaymentDelete = computed(
  () => can(PERM.PAYMENT_DELETE) && (readonlyEntries.value.length === 0 || can(PERM.LEDGER_DELETE)),
)

// ============================================
// Store & Data
// ============================================
const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)

const proLedgerStore = useProLedger()
const proAccounts = computed(() => proLedgerStore.proAccounts)
const allProBankList = computed(() => proLedgerStore.allProBankList)

// ============================================
// Computed - Mode Detection
// ============================================
const isCreateMode = computed(() => !props.payment)

const allowedPeriod = computed(() => {
  return props.payment ? useAccount().superAuth || diffDate(props.payment.deal_date) <= 90 : true
})

// ============================================
// Helper Functions
// ============================================
const generateContent = (): string => {
  if (!props.contract?.contractor) return ''
  return `${props.contract.contractor.name}[${props.contract.serial_number}] 대금납부`
}

const paymentAccount = computed<number | null>(() => {
  if (!props.contract) return null
  // 분담금 또는 분양대금 계정을 ProjectAccount(is_payment=true)에서 조회하여 매핑
  const accCategory = props.contract.order_group_sort === '1' ? 'equity' : 'revenue'
  return (
    proAccounts.value.find(acc => acc.is_payment && acc.category === accCategory)?.value ??
    proAccounts.value.find(acc => acc.category === accCategory)?.value ??
    null
  )
})

const createEmptyEntry = (contractPk: number | null, trader = ''): PaymentEntryForm => ({
  _uid: nextEntryUid++,
  pk: null,
  account: paymentAccount.value,
  amount: null,
  trader,
  contract: contractPk,
  installment_order: null,
})

// ============================================
// Entry Management Functions
// ============================================
const addEntry = () => {
  paymentEntries.value.push(
    createEmptyEntry(props.contract?.pk || null, paymentEntries.value[0]?.trader || ''),
  )
}

const removeEntry = (index: number) => {
  if (paymentEntries.value.length === 1) {
    Object.assign(paymentEntries.value[0], {
      pk: null,
      amount: null,
      trader: '',
      installment_order: null,
    })
  } else {
    paymentEntries.value.splice(index, 1)
  }
}

// ============================================
// Initialization Functions
// ============================================
const initializeCreateForm = () => {
  isInitializingForm.value = true
  validated.value = false
  removeCont.value = false
  isSaving.value = false
  readonlyEntries.value = []

  Object.assign(bankForm, {
    deal_date: getToday(),
    bank_account: null,
    amount: null,
    note: '',
    sort: 1,
    content: generateContent(),
  })

  paymentEntries.value = [createEmptyEntry(props.contract?.pk || null)]
  nextTick(() => {
    isInitializingForm.value = false
  })
}

const initializeEditForm = () => {
  if (!props.payment) return
  isInitializingForm.value = true
  validated.value = false
  removeCont.value = false
  isSaving.value = false

  const existingContent = props.payment.accounting_entry?.related_transaction?.content

  Object.assign(bankForm, {
    deal_date: props.payment.deal_date,
    bank_account: props.payment.bank_account?.pk ?? null,
    amount: props.payment.bank_transaction_amount || props.payment.amount,
    note: props.payment.note || '',
    sort: 1,
    content: existingContent || generateContent(),
  })

  if (props.payment.sibling_entries && props.payment.sibling_entries.length > 0) {
    const editableEntries = props.payment.sibling_entries.filter(
      (entry: SiblingEntry) => entry.is_contract_payment === true,
    )
    const readonlyEntriesData = props.payment.sibling_entries.filter(
      (entry: SiblingEntry) => entry.is_contract_payment !== true,
    )

    if (editableEntries.length > 0) {
      paymentEntries.value = editableEntries.map((entry: SiblingEntry) => ({
        _uid: nextEntryUid++,
        pk: entry.pk,
        account: entry.account?.pk ?? paymentAccount.value,
        amount: entry.amount,
        trader: entry.trader || '',
        contract: entry.contract ?? null,
        installment_order: entry.installment_order ?? null,
      }))
    } else {
      paymentEntries.value = [createEmptyEntry(props.contract?.pk || null)]
    }

    readonlyEntries.value = readonlyEntriesData.map((entry: SiblingEntry) => ({
      pk: entry.pk,
      account: entry.account?.pk || 0,
      account_name: entry.account?.name || '',
      amount: entry.amount,
      trader: entry.trader || '',
    }))
  } else {
    paymentEntries.value = [
      {
        _uid: nextEntryUid++,
        pk: props.payment.accounting_entry?.pk || null,
        account: props.payment.accounting_entry?.account ?? paymentAccount.value,
        amount: props.payment.amount,
        trader: props.payment.trader || '',
        contract: props.contract?.pk || null,
        installment_order: props.payment.installment_order?.pk || null,
      },
    ]
    readonlyEntries.value = []
  }

  nextTick(() => {
    isInitializingForm.value = false
  })
}

// ============================================
// Computed - Amount Validation
// ============================================
const bankAmount = computed(() => bankForm.amount || 0)

const totalEntryAmount = computed(() => {
  const editableTotal = paymentEntries.value.reduce((sum, entry) => {
    return sum + (entry.amount || 0)
  }, 0)

  const readonlyTotal = readonlyEntries.value.reduce((sum, entry) => {
    return sum + (entry.amount || 0)
  }, 0)

  return editableTotal + readonlyTotal
})

const difference = computed(() => {
  return bankAmount.value - totalEntryAmount.value
})

const isBalanced = computed(() => {
  return difference.value === 0
})

const isSaveDisabled = computed(() => {
  return isSaving.value || !isBalanced.value || formsCheck.value
})

const formsCheck = computed(() => {
  if (!props.payment) return false

  const bankUnchanged =
    bankForm.bank_account === (props.payment.bank_account?.pk ?? null) &&
    bankForm.deal_date === props.payment.deal_date &&
    bankForm.amount === (props.payment.bank_transaction_amount || props.payment.amount) &&
    bankForm.note === (props.payment.note || '')

  let entryUnchanged = false

  if (props.payment.sibling_entries && props.payment.sibling_entries.length > 0) {
    const originalEditableEntries = props.payment.sibling_entries.filter(
      (entry: SiblingEntry) => entry.is_contract_payment === true,
    )
    if (originalEditableEntries.length > 0) {
      entryUnchanged =
        paymentEntries.value.length === originalEditableEntries.length &&
        paymentEntries.value.every((entry, idx) => {
          const original = originalEditableEntries[idx]
          return (
            entry.pk === original.pk &&
            entry.amount === original.amount &&
            entry.trader === (original.trader || '') &&
            entry.installment_order === (original.installment_order ?? null)
          )
        })
    } else {
      entryUnchanged = paymentEntries.value.every(
        entry => !entry.amount && !entry.trader && !entry.installment_order,
      )
    }
  } else {
    entryUnchanged =
      paymentEntries.value.length === 1 &&
      paymentEntries.value[0].amount === props.payment.amount &&
      paymentEntries.value[0].trader === (props.payment.trader || '') &&
      paymentEntries.value[0].installment_order === (props.payment.installment_order?.pk ?? null)
  }

  const noContractChange = removeCont.value === false

  return bankUnchanged && entryUnchanged && noContractChange
})

// ============================================
// Payload Building Functions
// ============================================
const resolveEntryAccount = (entryAccount: number | null): number => {
  const accountId = entryAccount ?? paymentAccount.value
  if (!accountId) {
    throw new Error('수납 계정 과목 정보를 불러오지 못했습니다. 새로고침 후 다시 시도해주세요.')
  }
  return accountId
}

const buildCreatePayload = (): ContractPaymentPayload => {
  if (!isBalanced.value) {
    throw new Error('은행 거래 금액과 분류 금액 합계가 일치하지 않습니다.')
  }

  if (!props.contract?.pk) {
    throw new Error('계약 정보가 없습니다.')
  }

  const validEntries = paymentEntries.value
    .filter(entry => (entry.amount || 0) > 0)
    .map(entry => ({
      account: resolveEntryAccount(entry.account),
      amount: entry.amount!,
      trader: entry.trader || '',
      contract: props.contract!.pk,
      installment_order: entry.installment_order!,
    }))

  if (validEntries.length === 0) {
    throw new Error('최소 하나 이상의 납부 항목이 필요합니다.')
  }

  return {
    project: null,
    bank_account: bankForm.bank_account!,
    deal_date: bankForm.deal_date,
    amount: bankForm.amount!,
    sort: 1,
    content: bankForm.content,
    note: bankForm.note,
    accounting_entries: validEntries,
  }
}

const buildUpdatePayload = (): ContractPaymentPayload => {
  if (!props.payment) {
    throw new Error('수정할 납부 정보가 없습니다.')
  }

  if (!isBalanced.value) {
    throw new Error('은행 거래 금액과 분류 금액 합계가 일치하지 않습니다.')
  }

  const validEntries = paymentEntries.value
    .filter(entry => (entry.amount || 0) > 0)
    .map(entry => {
      const baseEntry: PaymentAccEntryInput = {
        account: resolveEntryAccount(entry.account),
        amount: entry.amount!,
        trader: entry.trader || '',
        installment_order: removeCont.value ? null : entry.installment_order!,
      }

      baseEntry.contract = removeCont.value ? null : props.contract?.pk || null

      if (entry.pk) {
        baseEntry.pk = entry.pk
      }

      return baseEntry
    })

  if (validEntries.length === 0) {
    throw new Error('최소 하나 이상의 납부 항목이 필요합니다.')
  }

  const readonlyEntriesData = readonlyEntries.value.map(entry => ({
    pk: entry.pk,
    account: entry.account,
    amount: entry.amount,
    trader: entry.trader || '',
  }))

  const allEntries = [...validEntries, ...readonlyEntriesData]

  const existingContent = props.payment.accounting_entry?.related_transaction?.content
  const resolvedContent =
    removeCont.value && readonlyEntries.value.length === 0 && bankForm.content === generateContent()
      ? existingContent && existingContent !== generateContent()
        ? existingContent
        : '대금납부(계약해제)'
      : bankForm.content

  return {
    project: null,
    bank_account: bankForm.bank_account!,
    deal_date: bankForm.deal_date,
    amount: bankForm.amount!,
    sort: 1,
    content: resolvedContent,
    note: bankForm.note,
    accounting_entries: allEntries,
  }
}

// ============================================
// Event Handlers (Phase 5: CRUD Integration)
// ============================================
const onSubmit = (event: Event) => {
  if (canPaymentManage.value) {
    if (allowedPeriod.value) {
      if (isValidate(event)) {
        validated.value = true
      } else {
        if (isCreateMode.value) modalAction()
        else {
          if (removeCont.value) {
            cngConfirmModal.value.callModal()
          } else modalAction()
        }
      }
    } else
      refAlertModal.value.callModal(
        null,
        '수납일로부터 90일이 경과한 건은 수정할 수 없습니다. 관리자에게 문의바랍니다.',
      )
  } else refAlertModal.value.callModal()
}

const modalAction = () => {
  cngConfirmModal.value?.close()
  try {
    isSaving.value = true
    const finishSave = () => {
      isSaving.value = false
    }

    if (isCreateMode.value) {
      const payload = buildCreatePayload()
      emit('on-submit', payload, finishSave)
    } else {
      const payload = buildUpdatePayload()
      const bankTransactionId = props.payment?.bank_transaction_id

      if (!bankTransactionId) {
        throw new Error('은행 거래 ID를 찾을 수 없습니다.')
      }

      emit('on-submit', bankTransactionId, payload, finishSave)
    }
  } catch (error) {
    isSaving.value = false
    const errorMessage = error instanceof Error ? error.message : '저장 중 오류가 발생했습니다.'
    refAlertModal.value.callModal(null, errorMessage)
  }
}

const deleteConfirm = () => {
  if (canPaymentDelete.value) {
    if (allowedPeriod.value) {
      delConfirmModal.value.callModal()
    } else
      refAlertModal.value.callModal(
        null,
        '수납일로부터 90일이 경과한 건은 삭제할 수 없습니다. 관리자에게 문의바랍니다.',
      )
  } else refAlertModal.value.callModal()
}

const onDelete = () => {
  delConfirmModal.value?.close()
  try {
    isSaving.value = true
    const bankTransactionId = props.payment?.bank_transaction_id

    if (!bankTransactionId) {
      throw new Error('은행 거래 ID를 찾을 수 없습니다.')
    }

    emit('on-delete', bankTransactionId, () => {
      isSaving.value = false
    })
  } catch (error) {
    isSaving.value = false
    const errorMessage = error instanceof Error ? error.message : '삭제 중 오류가 발생했습니다.'
    refAlertModal.value.callModal(null, errorMessage)
  }
}

// ============================================
// Watchers - Auto-copy functionality
// ============================================
watch(
  () => bankForm.amount,
  newAmount => {
    if (!isCreateMode.value || isInitializingForm.value) return

    const otherEntriesEmpty = paymentEntries.value
      .slice(1)
      .every(entry => !entry.amount || entry.amount === 0)

    if (newAmount !== null && otherEntriesEmpty) {
      paymentEntries.value[0].amount = newAmount
    }
  },
)

watch(
  () => paymentEntries.value[0]?.trader,
  newTrader => {
    if (isInitializingForm.value) return
    if (paymentEntries.value.length > 1) {
      for (let i = 1; i < paymentEntries.value.length; i++) {
        paymentEntries.value[i].trader = newTrader || ''
      }
    }
  },
)

watch(
  () => props.payment,
  () => {
    if (isCreateMode.value) initializeCreateForm()
    else initializeEditForm()
  },
)

// ============================================
// Lifecycle
// ============================================
onBeforeMount(() => {
  if (isCreateMode.value) {
    initializeCreateForm()
  } else {
    initializeEditForm()
  }
})
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <!-- Section 1: 은행 거래 정보 -->
      <CRow class="mb-3">
        <CCol>
          <h6 class="border-bottom pb-2 mb-3">은행 거래 정보</h6>
          <CRow class="mb-2">
            <CCol xs="6">
              <CRow>
                <CFormLabel class="col-sm-4 col-form-label required">납부일자</CFormLabel>
                <CCol sm="8">
                  <DatePicker v-model="bankForm.deal_date" required placeholder="거래일자" />
                </CCol>
              </CRow>
            </CCol>
          </CRow>
          <CRow class="mb-2">
            <CCol xs="6">
              <CRow>
                <CFormLabel class="col-sm-4 col-form-label required">거래계좌</CFormLabel>
                <CCol sm="8">
                  <CFormSelect
                    :model-value="
                      bankForm.bank_account !== null ? String(bankForm.bank_account) : ''
                    "
                    required
                    @update:model-value="val => (bankForm.bank_account = val ? Number(val) : null)"
                  >
                    <option value="">---------</option>
                    <option v-for="pb in allProBankList" :key="pb.pk as number" :value="pb.pk">
                      {{ pb.alias_name }}
                    </option>
                  </CFormSelect>
                </CCol>
              </CRow>
            </CCol>
            <CCol xs="6">
              <CRow>
                <CFormLabel class="col-sm-4 col-form-label required">거래금액</CFormLabel>
                <CCol sm="8">
                  <CFormInput
                    v-model.number="bankForm.amount as number"
                    type="number"
                    min="0"
                    placeholder="은행 거래 금액"
                    required
                  />
                </CCol>
              </CRow>
            </CCol>
          </CRow>
          <CRow>
            <CCol xs="12">
              <CRow>
                <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
                <CCol sm="10">
                  <CFormTextarea v-model="bankForm.note" placeholder="기타 특이사항" />
                </CCol>
              </CRow>
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <v-divider class="mb-4" />
      <!-- Section 2: 납부 내역 -->
      <CRow class="mb-3">
        <CCol>
          <h6 class="pb-0 mb-3">
            대금 납부 정보
            <v-btn size="x-small" color="info" class="ms-2" @click="addEntry">
              차수 분할 등록
            </v-btn>
          </h6>

          <!-- 편집 가능한 납부 항목들 -->
          <div class="mb-3 px-3 border rounded">
            <CRow class="mb-0">
              <CTable borderless small>
                <colgroup>
                  <col width="32%" />
                  <col width="32%" />
                  <col width="32%" />
                  <col width="4%" />
                </colgroup>
                <CTableHead>
                  <CTableRow class="text-center border-bottom">
                    <CTableHeaderCell class="py-0">
                      <CFormLabel class="col-sm-12 col-form-label required">납부회차</CFormLabel>
                    </CTableHeaderCell>
                    <CTableHeaderCell class="py-0">
                      <CFormLabel class="col-sm-12 col-form-label required">
                        납부(분류)금액
                      </CFormLabel>
                    </CTableHeaderCell>
                    <CTableHeaderCell class="py-0">
                      <CFormLabel class="col-sm-12 col-form-label required">입금자명</CFormLabel>
                    </CTableHeaderCell>
                    <CTableHeaderCell class="text-center"></CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  <CTableRow v-for="(entry, idx) in paymentEntries" :key="entry._uid">
                    <CTableDataCell :class="idx === 0 ? 'pt-3' : ''">
                      <CFormSelect
                        :model-value="
                          entry.installment_order !== null ? String(entry.installment_order) : ''
                        "
                        required
                        @update:model-value="
                          val => (entry.installment_order = val ? Number(val) : null)
                        "
                      >
                        <option value="">---------</option>
                        <option v-for="po in payOrderList" :key="po.pk as number" :value="po.pk">
                          {{ po.str_display }}
                        </option>
                      </CFormSelect>
                    </CTableDataCell>
                    <CTableDataCell :class="idx === 0 ? 'pt-3' : ''">
                      <CFormInput
                        v-model.number="entry.amount as number"
                        type="number"
                        min="0"
                        placeholder="회차별 납부 금액"
                        required
                      />
                    </CTableDataCell>
                    <CTableDataCell :class="idx === 0 ? 'pt-3' : ''">
                      <CFormInput
                        v-model="entry.trader"
                        maxlength="20"
                        required
                        :readonly="idx !== 0"
                        placeholder="실제 입금자명"
                      />
                    </CTableDataCell>
                    <CTableDataCell class="text-center">
                      <v-icon
                        v-if="paymentEntries.length > 1 && idx !== 0"
                        icon="mdi-close"
                        color="grey"
                        class="mt-2"
                        size="small"
                        @click="removeEntry(idx)"
                      />
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CRow>
          </div>

          <!-- 읽기 전용 분개 항목들 (is_payment: false) -->
          <div v-if="readonlyEntries.length > 0" class="mb-3 px-3 border rounded bg-body-tertiary">
            <CRow class="mb-0">
              <div class="py-2">
                <small class="text-muted fw-bold">기타 분개 항목 (참조용)</small>
              </div>
              <CTable borderless small>
                <colgroup>
                  <col width="25%" />
                  <col width="25%" />
                  <col width="25%" />
                </colgroup>
                <CTableHead>
                  <CTableRow class="text-center border-bottom">
                    <CTableHeaderCell class="py-1">
                      <small class="text-muted">계정과목</small>
                    </CTableHeaderCell>
                    <CTableHeaderCell class="py-1">
                      <small class="text-muted">금액</small>
                    </CTableHeaderCell>
                    <CTableHeaderCell class="py-1">
                      <small class="text-muted">거래처</small>
                    </CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody class="text-center">
                  <CTableRow v-for="entry in readonlyEntries" :key="entry.pk">
                    <CTableDataCell class="py-2">
                      <small class="text-muted">{{ entry.account_name }}</small>
                    </CTableDataCell>
                    <CTableDataCell class="py-2">
                      <small class="text-muted fw-bold">
                        {{ entry.amount?.toLocaleString() }}원
                      </small>
                    </CTableDataCell>
                    <CTableDataCell class="py-2">
                      <small class="text-muted">{{ entry.trader }}</small>
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CRow>
          </div>
        </CCol>
      </CRow>

      <!-- Section 3: 금액 검증 표시 -->
      <CRow class="mb-3">
        <CCol>
          <div class="p-3 bg-body-tertiary border rounded">
            <strong>금액 검증 :</strong>
            은행 거래금액 - <strong>{{ bankAmount.toLocaleString() }}</strong
            >원 · 납부 합계금액 - <strong>{{ totalEntryAmount.toLocaleString() }}</strong
            >원 ·
            <span :class="{ 'text-danger fw-bold': !isBalanced, 'text-success': isBalanced }">
              차액: {{ Math.abs(difference).toLocaleString() }}원
              <v-icon v-if="isBalanced" size="small" color="success">mdi-check-circle</v-icon>
              <v-icon v-else size="small" color="error">mdi-alert-circle</v-icon>
            </span>
          </div>
        </CCol>
      </CRow>

      <!-- Section 4: 계약건 변경 (edit mode only) -->
      <CRow v-if="payment" class="mb-2">
        <CCol>
          <CRow>
            <CCol sm="12">
              <CFormCheck
                :id="`cont-change`"
                v-model="removeCont"
                label="계약 건 변경 (현재 계약 건 귀속에서 해제 되며 납부 내역 관리에서 재 지정요)"
                class="text-grey"
              />
            </CCol>
          </CRow>
        </CCol>
      </CRow>
    </CModalBody>

    <CModalFooter>
      <slot name="footer">
        <v-btn
          v-if="canPaymentManage"
          type="submit"
          variant="flat"
          size="small"
          :color="payment ? 'success' : 'primary'"
          :disabled="isSaveDisabled"
        >
          저장
        </v-btn>
        <v-btn
          v-if="payment && canPaymentDelete"
          type="button"
          variant="flat"
          size="small"
          color="warning"
          :disabled="isSaving"
          @click="deleteConfirm"
        >
          삭제
        </v-btn>
        <v-btn type="button" size="small" variant="flat" color="light" @click="$emit('close')">
          닫기
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="cngConfirmModal" checked>
    <template #header> 건별 납부 정보 - [변경]</template>
    <template #default>
      이 수납 건에 대한 현재 계약 건 귀속을 해제합니다. <br /><br />
      해당 건별 수납 정보 계약 건 귀속 해제(변경)를 진행하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="success" variant="flat" size="small" @click="modalAction">변경</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="delConfirmModal">
    <template #header> 건별 납부 정보 - [삭제]</template>
    <template #default>
      삭제 후 복구할 수 없습니다. 해당 건별 수납 정보 삭제를 진행하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" variant="flat" size="small" @click="onDelete">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
