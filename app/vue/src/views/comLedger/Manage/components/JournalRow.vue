<script lang="ts" setup>
import { computed, type ComputedRef, inject, watch } from 'vue'
import { usePerms } from '@/composables/usePerms'
import type { AccountPicker, EvidenceTypeCode } from '@/store/types/comLedger.ts'
import LedgerAccount from '@/components/LedgerAccount/Index.vue'

export interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  evidence_type?: EvidenceTypeCode | ''
  affiliate?: number | null
}

interface Props {
  sort: 1 | 2
  displayRows: NewEntryForm[]
  transAmount: number | null
}

const props = defineProps<Props>()

interface Emits {
  (e: 'removeEntry', index: number): void
  (e: 'insertTransferFee', index: number): void
  (e: 'update:entries', value: NewEntryForm[]): void
  (e: 'alert', title: string, message: string): void
}

const emit = defineEmits<Emits>()

const cloneRows = (rows: NewEntryForm[] = props.displayRows) => rows.map(row => ({ ...row }))

const updateRowField = (index: number, patch: Partial<NewEntryForm>) => {
  const next = cloneRows()
  next[index] = { ...next[index], ...patch }
  emit('update:entries', next)
}

watch(
  () => props.transAmount,
  (newValue, oldValue) => {
    if (
      oldValue !== undefined &&
      newValue !== oldValue &&
      props.displayRows.length === 1
    ) {
      const normalized = newValue || undefined
      if (props.displayRows[0].amount !== normalized) {
        updateRowField(0, { amount: normalized })
      }
    }
  },
)

// props.sort 변경을 감지하여 account와 evidence_type을 초기화
watch(
  () => props.sort,
  (newValue, oldValue) => {
    if (oldValue !== undefined && newValue !== oldValue) {
      const next = props.displayRows.map(row => ({
        ...row,
        account: null,
        affiliate: null,
        evidence_type: '' as const,
      }))
      emit('update:entries', next)
    }
  },
)

const { canGlobal, PERM } = usePerms()
const canComLedgerUpdate = computed(
  () =>
    canGlobal(PERM.HQ_LEDGER_UPDATE) ||
    canGlobal(PERM.HQ_LEDGER_CREATE) ||
    canGlobal(PERM.HQ_LEDGER_MANAGE),
)

const affiliates = inject<ComputedRef<{ value: number; label: string }[]>>('affiliates')
const comAccounts = inject<ComputedRef<AccountPicker[]>>('comAccounts')
const transferFeePk = inject<ComputedRef<number | undefined>>(
  'transferFeePk',
  computed(() => undefined),
)

const sortType = computed(() => {
  if (props.sort === 1) return 'deposit' // 입금
  if (props.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

// 선택된 account가 affiliate를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): AccountPicker | undefined => {
  if (!accountId || !comAccounts?.value) return undefined
  return comAccounts.value.find(acc => acc.value === accountId)
}

// account 변경 시 req_affiliate가 false면 affiliate를 null로 초기화
watch(
  () => props.displayRows.map(row => row.account),
  (newAccounts, oldAccounts) => {
    let changed = false
    const next = cloneRows()
    next.forEach((row, index) => {
      if (newAccounts[index] !== oldAccounts?.[index]) {
        const account = getAccountById(row.account)
        if ((!account || !account.req_affiliate) && row.affiliate !== null) {
          row.affiliate = null
          changed = true
        }
      }
    })
    if (changed) {
      emit('update:entries', next)
    }
  },
  { deep: true },
)

const removeEntry = (index: number) => {
  emit('removeEntry', index)
}

const isTransferFeeRow = (row: NewEntryForm | undefined): boolean => {
  if (!row) return false
  return Boolean(
    (transferFeePk?.value !== undefined && row.account === transferFeePk.value) ||
      row.trader?.includes('이체수수료'),
  )
}

// Check if transfer fee already exists immediately after this row
const hasInsertedFee = (index: number): boolean => {
  return isTransferFeeRow(props.displayRows[index]) || isTransferFeeRow(props.displayRows[index + 1])
}

const insertTransferFee = (index: number) => {
  if (hasInsertedFee(index)) return

  if (!transferFeePk || transferFeePk.value === undefined) {
    emit('alert', '계정 안내', '이체수수료 계정이 설정되지 않았습니다. 관리자에게 문의하세요.')
    return
  }

  emit('insertTransferFee', index)
}

// 지출증빙이 필수인지 확인하는 헬퍼 함수
// 출금(sort===2)이지만 대체(출금) 계정일 경우 지출증빙이 필요하지 않음
const isEvidenceRequired = (row: NewEntryForm): boolean => {
  if (props.sort === 1) return false

  const account = getAccountById(row.account)
  if (!account) return true

  if (account.category === 'transfer' && account.direction === '출금') {
    return false
  }

  return true
}
</script>

<template>
  <CTable class="m-0">
    <colgroup>
      <col style="width: 32%" />
      <col style="width: 24%" />
      <col style="width: 16%" />
      <col style="width: 22%" />
      <col v-if="canComLedgerUpdate" style="width: 6%" />
    </colgroup>

    <!-- 모든 행을 수정 가능한 폼으로 렌더링 -->
    <CTableRow v-for="(row, idx) in displayRows" :key="row.pk || `new-${idx}`">
      <CTableDataCell>
        <LedgerAccount
          :model-value="row.account"
          :options="comAccounts ?? []"
          :sort-type="sortType"
          required
          @update:model-value="val => updateRowField(idx, { account: val })"
        />
        <!-- affiliate 필드가 필요한 경우 추가 드롭다운 표시 -->
        <div v-if="row.account && getAccountById(row.account)?.req_affiliate" class="pt-0 px-2">
          <CFormSelect
            :model-value="row.affiliate ? String(row.affiliate) : ''"
            required
            placeholder="관계회사 선택"
            @update:model-value="val => updateRowField(idx, { affiliate: val ? Number(val) : null })"
          >
            <option value="">관계회사를 선택하세요</option>
            <option v-for="aff in affiliates" :value="aff.value" :key="aff.value">
              {{ aff.label }}
            </option>
          </CFormSelect>
        </div>
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormInput
          :model-value="row.trader ?? ''"
          size="sm"
          placeholder="거래처"
          @update:model-value="val => updateRowField(idx, { trader: String(val ?? '') })"
        />
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormInput
          :model-value="row.amount"
          size="sm"
          type="number"
          min="0"
          placeholder="분류 금액"
          @update:model-value="
            val =>
              updateRowField(idx, {
                amount: val === '' || val === null ? undefined : Number(val),
              })
          "
        />
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormSelect
          :model-value="row.evidence_type ?? ''"
          :disabled="sort === 1"
          :required="isEvidenceRequired(row)"
          size="sm"
          placeholder="지출 증빙"
          @update:model-value="
            val => updateRowField(idx, { evidence_type: (val ?? '') as NewEntryForm['evidence_type'] })
          "
        >
          <option value="">---------</option>
          <option value="0">증빙없음</option>
          <option value="1">세금계산서</option>
          <option value="2">계산서(면세)</option>
          <option value="3">신용/체크카드 매출전표</option>
          <option value="4">현금영수증</option>
          <option value="5">원천징수영수증/지급명세서</option>
          <option value="6">지로용지 및 청구서</option>
        </CFormSelect>
      </CTableDataCell>
      <CTableDataCell v-if="canComLedgerUpdate" class="text-end pe-2">
        <v-icon
          v-if="sort === 2 && !isTransferFeeRow(row)"
          icon="mdi-playlist-plus"
          size="small"
          :color="hasInsertedFee(idx) ? 'grey' : 'indigo-lighten-1'"
          :class="hasInsertedFee(idx) ? 'cursor-not-allowed' : 'pointer'"
          :disabled="hasInsertedFee(idx)"
          v-tooltip="'이체수수료 추가'"
          @click="insertTransferFee(idx)"
        />
        <v-icon
          icon="mdi-close"
          size="small"
          class="ms-2 pointer"
          v-tooltip="'닫기'"
          @click="removeEntry(idx)"
        />
      </CTableDataCell>
    </CTableRow>
  </CTable>
</template>
