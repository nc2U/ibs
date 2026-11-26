<script lang="ts" setup>
import { computed, type ComputedRef, inject, nextTick, provide, reactive, watch } from 'vue'
import type { AccountPicker } from '@/store/types/comLedger'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import JournalRow, { type NewEntryForm } from './JournalRow.vue'

// 은행 거래 폼 데이터
interface BankForm {
  deal_date: string
  note: string
  bank_account: number | null | ''
  content: string
  sort: 1 | 2
  amount: number | null
}

// 전체 거래건 데이터 구조
export interface BankTransactionData {
  uid?: string | number
  bankForm: BankForm
  entries: NewEntryForm[]
}

interface Props {
  transaction: BankTransactionData
  index: number
  bankAccounts: { value: number | null | undefined; label: string }[]
  comAccounts: AccountPicker[]
  affiliates: { value: number; label: string }[]
}

const props = defineProps<Props>()

interface Emits {
  (e: 'update:transaction', value: BankTransactionData): void
  (e: 'remove'): void
  (e: 'detectTransferWithdraw', sourceData: BankTransactionData): void
  (e: 'downloadTemplate'): void
  (e: 'uploadEntries'): void
  (e: 'alert', title: string, message: string): void
}

const emit = defineEmits<Emits>()

// 로컬 상태 관리 - props를 직접 수정하지 않고 emit으로 업데이트
const localBankForm = reactive<BankForm>({ ...props.transaction.bankForm })
let isSyncingFromProps = false

const emitTransaction = (entries: NewEntryForm[] = props.transaction.entries) => {
  emit('update:transaction', {
    uid: props.transaction.uid,
    bankForm: { ...localBankForm },
    entries: entries.map(e => ({ ...e })),
  })
}

// props 변경 시 localBankForm 동기화
watch(
  () => props.transaction.bankForm,
  newBankForm => {
    isSyncingFromProps = true
    Object.assign(localBankForm, newBankForm)
    nextTick(() => {
      isSyncingFromProps = false
    })
  },
  { deep: true },
)

// bankForm 변경 시 부모에게 알림 (props로 인한 변경 시 루프 방지)
watch(
  localBankForm,
  () => {
    if (!isSyncingFromProps) {
      emitTransaction()
    }
  },
  { deep: true },
)

// provide for JournalRow
provide(
  'affiliates',
  computed(() => props.affiliates),
)
provide(
  'comAccounts',
  computed(() => props.comAccounts),
)

const transferFeePk = inject<ComputedRef<number | undefined>>(
  'transferFeePk',
  computed(() => undefined),
)

// 거래 구분 이름
const sortName = computed(() => (localBankForm.sort === 1 ? '입금' : '출금'))

// 은행 거래 금액
const bankAmount = computed(() => localBankForm.amount || 0)

// 분류 금액 합계
const totalEntryAmount = computed(() => {
  return props.transaction.entries.reduce((sum, row) => {
    const amount = Number(row.amount) || 0
    return sum + amount
  }, 0)
})

// 차액 계산
const difference = computed(() => bankAmount.value - totalEntryAmount.value)

// 금액 일치 여부
const isBalanced = computed(() => difference.value === 0)

// 표시할 분개 행 목록
const displayRows = computed(() => props.transaction.entries)

const updateEntries = (newEntries: NewEntryForm[]) => {
  emitTransaction(newEntries)
}

// 분개 행 추가
const addRow = () => {
  emitTransaction([...props.transaction.entries, {}])
}

// 분개 행 삭제
const removeEntry = (index: number) => {
  const newEntries = props.transaction.entries.map(e => ({ ...e }))
  if (newEntries.length === 1) {
    newEntries[0] = { ...newEntries[0], amount: 0 }
  } else {
    newEntries.splice(index, 1)
  }
  emitTransaction(newEntries)
}

const insertTransferFeeEntry = (index: number) => {
  if (!transferFeePk || transferFeePk.value === undefined) {
    emit('alert', '계정 안내', '이체수수료 계정이 설정되지 않았습니다.')
    return
  }

  const currentRow = props.transaction.entries[index]
  const baseAmount =
    currentRow.amount !== undefined && currentRow.amount !== null && currentRow.amount > 0
      ? Number(currentRow.amount)
      : Number(props.transaction.bankForm.amount) || 0

  const newCurrentAmount = Math.max(0, baseAmount - 500)

  const newEntries = props.transaction.entries.map(e => ({ ...e }))
  newEntries[index] = {
    ...newEntries[index],
    amount: newCurrentAmount,
  }

  const currentTrader = currentRow.trader?.trim() || ''

  const newEntry: NewEntryForm = {
    pk: undefined,
    account: transferFeePk.value,
    trader: `[${currentTrader}]-이체수수료`,
    amount: 500,
    affiliate: null,
    evidence_type: '0',
  }

  newEntries.splice(index + 1, 0, newEntry)
  emitTransaction(newEntries)
}

// 대체(출금) 계정 감지 watch
watch(
  () => props.transaction.entries.map(e => e.account),
  (newAccounts, oldAccounts) => {
    if (
      props.transaction.entries.length === 1 &&
      localBankForm.sort === 2 &&
      newAccounts[0] !== oldAccounts?.[0]
    ) {
      const account = props.comAccounts.find(acc => acc.value === newAccounts[0])
      if (account && account.category === 'transfer' && account.direction === '출금') {
        emit('detectTransferWithdraw', {
          uid: props.transaction.uid,
          bankForm: { ...localBankForm },
          entries: props.transaction.entries.map(e => ({ ...e })),
        })
      }
    }
  },
  { deep: true },
)
</script>

<template>
  <CTableRow class="sticky-bank-row">
    <!-- 거래일자 -->
    <CTableDataCell>
      <DatePicker v-model="localBankForm.deal_date" required />
    </CTableDataCell>

    <!-- 메모 -->
    <CTableDataCell>
      <CFormInput v-model="localBankForm.note" placeholder="메모" maxlength="50" />
    </CTableDataCell>

    <!-- 거래계좌 -->
    <CTableDataCell>
      <CFormSelect
        :model-value="localBankForm.bank_account ? String(localBankForm.bank_account) : ''"
        required
        @update:model-value="val => (localBankForm.bank_account = val ? Number(val) : '')"
      >
        <option value="">---------</option>
        <option v-for="ba in bankAccounts" :key="ba.value ?? ''" :value="ba.value ?? ''">
          {{ ba.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>

    <!-- 적요 -->
    <CTableDataCell>
      <CFormInput v-model="localBankForm.content" placeholder="적요" maxlength="100" required />
    </CTableDataCell>

    <!-- 입출금액 -->
    <CTableDataCell>
      <div class="d-flex align-items-center">
        <CFormSelect
          :model-value="String(localBankForm.sort)"
          style="width: 70px"
          required
          class="me-2"
          @update:model-value="val => (localBankForm.sort = Number(val) as 1 | 2)"
        >
          <option :value="1">입금</option>
          <option :value="2">출금</option>
        </CFormSelect>
        <CFormInput
          v-model.number="localBankForm.amount"
          type="number"
          min="0"
          placeholder="금액"
          required
          style="width: 120px"
          class="text-end me-2"
        />
        <v-icon
          icon="mdi-download"
          size="16"
          color="info"
          class="ms-auto me-1 pointer"
          @click="emit('downloadTemplate')"
          v-tooltip="'이 거래건의 회계 계정 템플릿 다운로드'"
        />
        <v-icon
          icon="mdi-upload"
          size="16"
          color="success"
          class="me-1 pointer"
          @click="emit('uploadEntries')"
          v-tooltip="'이 거래건의 회계 계정 엑셀 업로드'"
        />
        <v-btn
          v-if="index > 0"
          density="compact"
          rounded="1"
          size="22"
          class="pointer"
          @click="emit('remove')"
        >
          <v-icon icon="mdi-minus" color="error" />
        </v-btn>
        <v-btn
          density="compact"
          rounded="1"
          size="22"
          class="ms-1 pointer"
          @click="addRow"
        >
          <v-icon icon="mdi-plus" color="success" />
        </v-btn>
      </div>
    </CTableDataCell>

    <!-- 분류 내역 (JournalRow) -->
    <CTableDataCell colspan="5" class="p-0">
      <JournalRow
        :sort="localBankForm.sort"
        :display-rows="displayRows"
        :trans-amount="localBankForm.amount"
        @update:entries="updateEntries"
        @remove-entry="removeEntry"
        @insert-transfer-fee="insertTransferFeeEntry"
        @alert="(title, msg) => emit('alert', title, msg)"
      />
    </CTableDataCell>
  </CTableRow>

  <!-- 금액 일치 여부 표시 행 (차액이 0이 아닐 때만) -->
  <CTableRow v-if="!isBalanced" class="bg-warning-lighten-5">
    <CTableDataCell colspan="10" class="text-center py-1">
      <small class="text-danger">
        <v-icon icon="mdi-alert" size="16" />
        차액: {{ sortName }} {{ Math.abs(difference).toLocaleString() }}원 (거래 금액과 분류 금액이
        일치하지 않습니다)
      </small>
    </CTableDataCell>
  </CTableRow>
</template>
