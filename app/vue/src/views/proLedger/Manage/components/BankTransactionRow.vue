<script lang="ts" setup>
import { computed, type ComputedRef, inject, provide, reactive, watch } from 'vue'
import { message } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms.ts'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ProAccountEntry, { type NewEntryForm } from './ProAccountEntry.vue'

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
  project?: number | null
  bankAccounts: { value: number | null | undefined; label: string }[]
  proAccounts: AccountPicker[]
  getContracts: { value: number; label: string }[]
  getAllContractors: { value: number; label: string }[]
}

const props = withDefaults(defineProps<Props>(), {
  project: null,
})

interface Emits {
  (e: 'update:transaction', value: BankTransactionData): void
  (e: 'remove'): void
  (e: 'detectTransferWithdraw', sourceData: BankTransactionData): void
  (e: 'downloadTemplate'): void
  (e: 'uploadEntries'): void
}

const emit = defineEmits<Emits>()

const { can, canGlobal, PERM } = usePerms()
const canLedgerManage = computed(() =>
  (props.project
    ? can(PERM.LEDGER_CREATE, props.project) ||
      can(PERM.LEDGER_UPDATE, props.project) ||
      can(PERM.LEDGER_MANAGE, props.project)
    : can(PERM.LEDGER_CREATE) || can(PERM.LEDGER_UPDATE) || can(PERM.LEDGER_MANAGE)) ||
  canGlobal(PERM.LEDGER_MANAGE),
)

// 로컬 상태 관리 - props를 직접 수정하지 않고 emit으로 업데이트
const localBankForm = reactive<BankForm>({ ...props.transaction.bankForm })

const isSameBankForm = (a: BankForm, b: BankForm): boolean =>
  a.deal_date === b.deal_date &&
  a.note === b.note &&
  a.bank_account === b.bank_account &&
  a.content === b.content &&
  a.sort === b.sort &&
  a.amount === b.amount

// props 변경 시 localBankForm 동기화 (자신이 방출한 동일 값에는 반응하지 않음)
watch(
  () => props.transaction.bankForm,
  newBankForm => {
    if (!isSameBankForm(localBankForm, newBankForm)) {
      Object.assign(localBankForm, newBankForm)
    }
  },
  { deep: true },
)

// bankForm 사용자에 의한 변경 시에만 부모에게 알림
watch(
  localBankForm,
  () => {
    if (!isSameBankForm(localBankForm, props.transaction.bankForm)) {
      emit('update:transaction', {
        uid: props.transaction.uid,
        bankForm: { ...localBankForm },
        entries: props.transaction.entries,
      })
    }
  },
  { deep: true },
)

// provide for ProAccountEntry
provide(
  'getContracts',
  computed(() => props.getContracts),
)
provide(
  'getAllContractors',
  computed(() => props.getAllContractors),
)
provide(
  'proAccounts',
  computed(() => props.proAccounts),
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

const onEntriesUpdate = (entries: NewEntryForm[]) => {
  emit('update:transaction', {
    uid: props.transaction.uid,
    bankForm: { ...localBankForm },
    entries,
  })
}

// 분개 행 추가
const addRow = () => {
  const newEntries = [...props.transaction.entries, {}]
  emit('update:transaction', {
    uid: props.transaction.uid,
    bankForm: { ...localBankForm },
    entries: newEntries,
  })
}

// 분개 행 삭제
const removeEntry = (index: number) => {
  const newEntries = [...props.transaction.entries]
  if (newEntries.length === 1) {
    newEntries[0] = { ...newEntries[0], amount: 0 }
  } else {
    newEntries.splice(index, 1)
  }
  emit('update:transaction', {
    uid: props.transaction.uid,
    bankForm: { ...localBankForm },
    entries: newEntries,
  })
}

const insertTransferFeeEntry = (index: number) => {
  if (!transferFeePk || transferFeePk.value === undefined) {
    message('warning', '알림!', '이체수수료 계정이 설정되지 않았습니다.')
    return
  }

  const currentRow = props.transaction.entries[index]
  const bankTransactionAmount = Number(props.transaction.bankForm.amount) || 0
  const newCurrentAmount = Math.max(0, bankTransactionAmount - 500)

  const newEntries = [...props.transaction.entries]
  newEntries[index] = {
    ...newEntries[index],
    amount: newCurrentAmount,
  }

  const currentTrader = currentRow.trader?.trim() || '[]'

  const newEntry: NewEntryForm = {
    pk: undefined,
    account: transferFeePk.value,
    trader: `[${currentTrader}]-이체수수료`,
    amount: 500,
    contract: null,
    contractor: null,
    evidence_type: '0',
  }

  newEntries.splice(index + 1, 0, newEntry)

  emit('update:transaction', {
    uid: props.transaction.uid,
    bankForm: { ...localBankForm },
    entries: newEntries,
  })
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
      const account = props.proAccounts.find(acc => acc.value === newAccounts[0])
      if (account && account.category === 'transfer' && account.direction === '출금') {
        emit('detectTransferWithdraw', {
          uid: props.transaction.uid,
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
      <CFormSelect v-model="localBankForm.bank_account" required>
        <option value="">---------</option>
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
        <CFormSelect v-model.number="localBankForm.sort" style="width: 70px" required class="me-2">
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

    <!-- 분류 내역 (ProAccountEntry) -->
    <CTableDataCell :colspan="canLedgerManage ? 5 : 4" class="p-0">
      <ProAccountEntry
        :sort="localBankForm.sort"
        :display-rows="displayRows"
        :trans-amount="localBankForm.amount"
        :project="project"
        @update:entries="onEntriesUpdate"
        @remove-entry="removeEntry"
        @insert-transfer-fee="insertTransferFeeEntry"
      />
    </CTableDataCell>
  </CTableRow>

  <!-- 금액 일치 여부 표시 행 (차액이 0이 아닐 때만) -->
  <CTableRow v-if="!isBalanced" class="bg-warning-lighten-5">
    <CTableDataCell :colspan="canLedgerManage ? 10 : 9" class="text-center py-1">
      <small class="text-danger">
        <v-icon icon="mdi-alert" size="16" />
        차액: {{ sortName }} {{ Math.abs(difference).toLocaleString() }}원 (거래 금액과 분류 금액이
        일치하지 않습니다)
      </small>
    </CTableDataCell>
  </CTableRow>
</template>

<style scoped lang="scss">
.dark-theme .bg-warning-lighten-5 {
  background-color: #4c422a !important;
  color: #fff !important;
}
</style>
