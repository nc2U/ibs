<script lang="ts" setup>
import { computed, type ComputedRef, inject, watch } from 'vue'
import { write_project_cash } from '@/utils/pageAuth.ts'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import LedgerAccount from '@/components/LedgerAccount/Index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'

interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
  contract?: number | null
  contractor?: number | null
}

interface Props {
  sort: 1 | 2
  displayRows: NewEntryForm[]
  transAmount: number | null
}
const props = defineProps<Props>() // Assign defineProps to a variable

watch(
  () => props.transAmount,
  newValue => {
    if (props.displayRows.length === 1) {
      props.displayRows[0].amount = newValue || undefined
    }
  },
)

// props.sort 변경을 감지하여 account와 evidence_type을 초기화하는 watch 추가
watch(
  () => props.sort,
  () => {
    props.displayRows.forEach(row => {
      row.account = null // account 초기화
      row.evidence_type = '' // evidence_type 초기화
    })
  },
)

interface Emits {
  (e: 'removeEntry', index: number): void
}
const emit = defineEmits<Emits>()

const getContracts = inject<ComputedRef<{ value: number; label: string }[]>>('getContracts')
const getContractors = inject<ComputedRef<{ value: number; label: string }[]>>('getAllContractors')
const proAccounts = inject<ComputedRef<AccountPicker[]>>('proAccounts')
const sortType = computed(() => {
  if (props.sort === 1) return 'deposit' // 입금
  if (props.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

// 선택된 account가 contract를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): AccountPicker | undefined => {
  if (!accountId || !proAccounts?.value) return undefined
  return proAccounts.value.find(acc => acc.value === accountId)
}

// account 변경 시 requires_contract 가 false면 contract 를 null로 초기화
// is_related_contractor 가 false면 contractor 를 null로 초기화
watch(
  () => props.displayRows.map(row => row.account),
  (newAccounts, oldAccounts) => {
    props.displayRows.forEach((row, index) => {
      // account가 변경된 경우에만 처리
      if (newAccounts[index] !== oldAccounts?.[index]) {
        const account = getAccountById(row.account)

        // account가 없거나 requires_contract가 false인 경우 contract를 null로 초기화
        if (!account || !account.requires_contract) {
          row.contract = null
        }

        // account가 없거나 is_related_contractor가 false인 경우 contractor를 null로 초기화
        if (!account || !account.is_related_contractor) {
          row.contractor = null
        }
      }
    })
  },
  { deep: true },
)

const removeEntry = (index: number) => {
  emit('removeEntry', index)
}

// 지출증빙이 필수인지 확인하는 헬퍼 함수
// 출금(sort===2)이지만 대체(출금) 계정일 경우 지출증빙이 필요하지 않음
const isEvidenceRequired = (row: NewEntryForm): boolean => {
  if (props.sort === 1) return false // 입금은 지출증빙 불필요

  // 출금(sort===2)인 경우
  const account = getAccountById(row.account)
  if (!account) return true // 계정이 선택되지 않았으면 일단 required

  // 대체(출금) 계정인 경우 지출증빙 불필요
  if (account.category === 'transfer' && account.direction === '출금') {
    return false
  }

  return true // 일반 출금 계정은 지출증빙 필수
}
</script>

<template>
  <CTable class="m-0">
    <colgroup>
      <col style="width: 32%" />
      <col style="width: 24%" />
      <col style="width: 16%" />
      <col style="width: 22%" />
      <col v-if="write_project_cash" style="width: 6%" />
    </colgroup>

    <!-- 모든 행을 수정 가능한 폼으로 렌더링 -->
    <CTableRow v-for="(row, idx) in displayRows" :key="row.pk || `new-${idx}`">
      <CTableDataCell>
        <LedgerAccount v-model="row.account" :options="proAccounts ?? []" :sort-type="sortType" />
        <!-- contract 필드가 필요한 경우 추가 드롭다운 표시 -->
        <div v-if="row.account && getAccountById(row.account)?.requires_contract" class="pt-0 px-2">
          <MultiSelect
            v-model.number="row.contract"
            mode="single"
            :options="getContracts"
            placeholder="계약 정보 선택"
          />
        </div>
        <div
          v-if="row.account && getAccountById(row.account)?.is_related_contractor"
          class="pt-0 px-2"
        >
          <MultiSelect
            v-model.number="row.contractor"
            mode="single"
            :options="getContractors"
            placeholder="계약자 정보 선택"
          />
        </div>
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormInput v-model="row.trader" size="sm" placeholder="거래처" />
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormInput
          v-model.number="row.amount"
          size="sm"
          type="number"
          min="0"
          placeholder="분류 금액"
        />
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormSelect
          v-model="row.evidence_type"
          :disabled="sort === 1"
          :required="isEvidenceRequired(row)"
          size="sm"
          placeholder="지출 증빙"
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
      <CTableDataCell v-if="write_project_cash" class="text-right pr-2">
        <v-icon icon="mdi-close" size="small" class="ml-2 pointer" @click="removeEntry(idx)" />
      </CTableDataCell>
    </CTableRow>
  </CTable>
</template>
