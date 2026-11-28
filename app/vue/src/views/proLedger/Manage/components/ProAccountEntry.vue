<script lang="ts" setup>
import { computed, type ComputedRef, inject, watch } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { message } from '@/utils/helper'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import LedgerAccount from '@/components/LedgerAccount/Index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'

export interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
  contract?: number | null
  contractor?: number | null
  installment_order?: number | null
}

interface Props {
  sort: 1 | 2
  displayRows: NewEntryForm[]
  transAmount: number | null
  project?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  project: null,
})

interface Emits {
  (e: 'update:entries', rows: NewEntryForm[]): void
  (e: 'removeEntry', index: number): void
  (e: 'insertTransferFee', index: number): void
}

const emit = defineEmits<Emits>()

const updateRowField = (index: number, patch: Partial<NewEntryForm>) => {
  const nextRows = props.displayRows.map((row, i) => (i === index ? { ...row, ...patch } : row))
  emit('update:entries', nextRows)
}

watch(
  () => props.transAmount,
  newValue => {
    const normalized = newValue || undefined
    if (props.displayRows.length === 1 && props.displayRows[0]?.amount !== normalized) {
      updateRowField(0, { amount: normalized })
    }
  },
)

// props.sort 변경을 감지하여 account와 evidence_type, contract/contractor 초기화
watch(
  () => props.sort,
  (newValue, oldValue) => {
    if (oldValue !== undefined && newValue !== oldValue) {
      const nextRows = props.displayRows.map(row => ({
        ...row,
        account: null,
        contract: null,
        contractor: null,
        evidence_type: '' as const,
      }))
      emit('update:entries', nextRows)
    }
  },
)

const { can, canGlobal, PERM } = usePerms()
const canLedgerManage = computed(() =>
  (props.project
    ? can(PERM.LEDGER_CREATE, props.project) ||
      can(PERM.LEDGER_UPDATE, props.project) ||
      can(PERM.LEDGER_MANAGE, props.project)
    : can(PERM.LEDGER_CREATE) || can(PERM.LEDGER_UPDATE) || can(PERM.LEDGER_MANAGE)) ||
  canGlobal(PERM.LEDGER_MANAGE),
)

const getContracts = inject<ComputedRef<{ value: number; label: string }[]>>('getContracts')
const getContractors = inject<ComputedRef<{ value: number; label: string }[]>>('getAllContractors')
const proAccounts = inject<ComputedRef<AccountPicker[]>>('proAccounts')
const transferFeePk = inject<ComputedRef<number | undefined>>('transferFeePk')

const sortType = computed(() => {
  if (props.sort === 1) return 'deposit' // 입금
  if (props.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

// 선택된 account가 contract/contractor를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): AccountPicker | undefined => {
  if (!accountId || !proAccounts?.value) return undefined
  return proAccounts.value.find(acc => acc.value === accountId)
}

const onAccountChange = (index: number, accId: number | null) => {
  const account = getAccountById(accId)
  const current = props.displayRows[index]
  updateRowField(index, {
    account: accId,
    contract: account?.requires_contract ? (current?.contract ?? null) : null,
    contractor: account?.is_related_contractor ? (current?.contractor ?? null) : null,
  })
}

const removeEntry = (index: number) => {
  emit('removeEntry', index)
}

const hasInsertedFee = (index: number): boolean => {
  const nextRow = props.displayRows[index + 1]
  return Boolean(
    nextRow &&
      transferFeePk?.value !== undefined &&
      nextRow.account === transferFeePk.value &&
      nextRow.trader?.includes('이체수수료'),
  )
}

const insertTransferFee = (index: number) => {
  if (hasInsertedFee(index)) return

  if (!transferFeePk || transferFeePk.value === undefined) {
    message('warning', '알림!', '이체수수료 계정이 설정되지 않았습니다. 관리자에게 문의하세요.')
    return
  }

  emit('insertTransferFee', index)
}

// 지출증빙이 필수인지 확인하는 헬퍼 함수
// 출금(sort===2)이지만 대체(출금) 계정일 경우 지출증빙이 필요하지 않음
const isEvidenceRequired = (row: NewEntryForm): boolean => {
  if (props.sort === 1) return false // 입금은 지출증빙 불필요

  const account = getAccountById(row.account)
  if (!account) return true // 계정이 선택되지 않았으면 일단 required

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
      <col v-if="canLedgerManage" style="width: 6%" />
    </colgroup>

    <!-- 모든 행을 수정 가능한 폼으로 렌더링 -->
    <CTableRow v-for="(row, idx) in displayRows" :key="row.pk || `new-${idx}`">
      <CTableDataCell>
        <LedgerAccount
          :model-value="row.account ?? null"
          :options="proAccounts ?? []"
          :sort-type="sortType"
          required
          @update:model-value="val => onAccountChange(idx, val)"
        />
        <!-- contract 필드가 필요한 경우 추가 드롭다운 표시 -->
        <div v-if="row.account && getAccountById(row.account)?.requires_contract" class="pt-0 px-2">
          <MultiSelect
            :model-value="row.contract ?? null"
            mode="single"
            :options="getContracts"
            placeholder="계약 정보 선택 (선택)"
            @update:model-value="val => updateRowField(idx, { contract: val ? Number(val) : null })"
          />
        </div>
        <div
          v-if="row.account && getAccountById(row.account)?.is_related_contractor"
          class="pt-0 px-2"
        >
          <MultiSelect
            :model-value="row.contractor ?? null"
            mode="single"
            :options="getContractors"
            placeholder="계약자 정보 선택"
            @update:model-value="val => updateRowField(idx, { contractor: val ? Number(val) : null })"
          />
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
            val => updateRowField(idx, { amount: val === '' || val === null ? undefined : Number(val) })
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
      <CTableDataCell v-if="canLedgerManage" class="text-end pe-2">
        <v-icon
          v-if="sort === 2 && !row.trader?.includes('이체수수료')"
          icon="mdi-playlist-plus"
          size="small"
          :color="hasInsertedFee(idx) ? 'grey' : 'indigo-lighten-1'"
          :class="hasInsertedFee(idx) ? 'cursor-not-allowed' : 'pointer'"
          :disabled="hasInsertedFee(idx)"
          v-tooltip="'이체수수료 추가'"
          @click="insertTransferFee(idx)"
        />
        <v-icon icon="mdi-close" size="small" class="ms-2 pointer" @click="removeEntry(idx)" />
      </CTableDataCell>
    </CTableRow>
  </CTable>
</template>
