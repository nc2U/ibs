<script lang="ts" setup>
import { computed, type ComputedRef, inject, provide, reactive, watch } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import JournalRow from './JournalRow.vue'

// 은행 거래 폼 데이터
interface BankForm {
  deal_date: string
  note: string
  bank_account: number | null
  content: string
  sort: 1 | 2
  amount: number | null
}

// 회계 분개 데이터
interface EntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  affiliate?: number | null
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
}

// 전체 거래건 데이터 구조
export interface BankTransactionData {
  bankForm: BankForm
  entries: EntryForm[]
}

interface Props {
  transaction: BankTransactionData
  index: number
  bankAccounts: { value: number | null | undefined; label: string }[]
  comAccounts: any[]
  affiliates: { value: number; label: string }[]
}

const props = defineProps<Props>()

interface Emits {
  (e: 'update:transaction', value: BankTransactionData): void
  (e: 'remove'): void
  (e: 'detectTransferWithdraw', sourceData: BankTransactionData): void
}

const emit = defineEmits<Emits>()

// 로컬 상태 관리 - props를 직접 수정하지 않고 emit으로 업데이트
const localBankForm = reactive<BankForm>({ ...props.transaction.bankForm })
const localEntries = computed({
  get: () => props.transaction.entries,
  set: value => {
    emit('update:transaction', { bankForm: localBankForm, entries: value })
  },
})

// bankForm 변경 시 부모에게 알림
watch(
  localBankForm,
  () => {
    emit('update:transaction', { bankForm: localBankForm, entries: props.transaction.entries })
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

const transferFeePk = inject<ComputedRef<number | undefined>>('transferFeePk')

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

// 분개 행 추가
const addRow = () => {
  const newEntries = [...props.transaction.entries, {}]
  emit('update:transaction', { bankForm: localBankForm, entries: newEntries })
}

// 분개 행 삭제
const removeEntry = (index: number) => {
  const newEntries = [...props.transaction.entries]
  if (newEntries.length === 1) {
    // 1개일 때는 amount를 0으로 설정
    newEntries[index].amount = 0
  } else {
    // 2개 이상일 때는 배열에서 제거
    newEntries.splice(index, 1)
  }
  emit('update:transaction', { bankForm: localBankForm, entries: newEntries })
}

const insertTransferFeeEntry = (index: number) => {
  if (!transferFeePk || transferFeePk.value === undefined) {
    alert('이체수수료 계정이 설정되지 않았습니다.')
    return
  }

  const currentRow = props.transaction.entries[index]
  const bankTransactionAmount = Number(props.transaction.bankForm.amount) || 0

  // Calculate a new amount based on bank transaction amount (minimum 0)
  const newCurrentAmount = Math.max(0, bankTransactionAmount - 500)

  // Create new entries array (immutable pattern)
  const newEntries = [...props.transaction.entries]

  // Modify the current row amount
  newEntries[index] = {
    ...newEntries[index],
    amount: newCurrentAmount,
  }

  // Create a trader name (default to [] if empty)
  const currentTrader = currentRow.trader?.trim() || '[]'

  // Create a new transfer fee entry
  const newEntry: EntryForm = {
    pk: undefined,
    account: transferFeePk.value,
    trader: `${currentTrader}-이체수수료`,
    amount: 500,
    affiliate: null,
    evidence_type: '0',
  }

  // Insert immediately after the current row
  newEntries.splice(index + 1, 0, newEntry)

  // Emit to parent
  emit('update:transaction', { bankForm: localBankForm, entries: newEntries })
}

// 대체(출금) 계정 감지 watch
watch(
  () => props.transaction.entries.map(e => e.account),
  (newAccounts, oldAccounts) => {
    // 단일 분개 & 출금 구분 & 대체(출금) 계정 선택 시
    if (
      props.transaction.entries.length === 1 &&
      localBankForm.sort === 2 &&
      newAccounts[0] !== oldAccounts?.[0]
    ) {
      const account = props.comAccounts.find(acc => acc.value === newAccounts[0])
      if (account && account.category === 'transfer' && account.direction === '출금') {
        // 대체 거래 자동 추가 이벤트 발생
        emit('detectTransferWithdraw', {
          bankForm: { ...localBankForm },
          entries: [...props.transaction.entries],
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
      <CFormSelect v-model.number="localBankForm.bank_account" required>
        <option :value="null">---------</option>
        <option v-for="ba in bankAccounts" :key="ba.value!" :value="ba.value">
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
        <CFormSelect v-model.number="localBankForm.sort" style="width: 70px" required class="mr-2">
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
          class="text-right"
        />
        <v-btn density="compact" rounded="1" size="22" class="ml-2 pointer" @click="addRow">
          <v-icon icon="mdi-plus" color="success" />
        </v-btn>
        <v-btn
          v-if="index > 0"
          density="compact"
          rounded="1"
          size="22"
          class="ml-1 pointer"
          @click="emit('remove')"
        >
          <v-icon icon="mdi-minus" color="error" />
        </v-btn>
      </div>
    </CTableDataCell>

    <!-- 분류 내역 (JournalRow) -->
    <CTableDataCell colspan="7" class="p-0">
      <JournalRow
        :sort="localBankForm.sort"
        :display-rows="displayRows"
        :trans-amount="localBankForm.amount"
        @remove-entry="removeEntry"
        @insert-transfer-fee="insertTransferFeeEntry"
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
