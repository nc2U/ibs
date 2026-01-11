<script lang="ts" setup>
import { computed, type ComputedRef, inject, ref, watch } from 'vue'
import { write_company_cash } from '@/utils/pageAuth.ts'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import LedgerAccount from '@/components/LedgerAccount/Index.vue'

interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
  affiliate?: number | null
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
  (newValue, oldValue) => {
    // 실제로 값이 변경되었을 때만 초기화 (초기 로드 시 oldValue는 undefined)
    if (oldValue !== undefined && newValue !== oldValue) {
      props.displayRows.forEach(row => {
        row.account = null // account 초기화
        row.evidence_type = '' // evidence_type 초기화
      })
    }
  },
)

interface Emits {
  (e: 'removeEntry', index: number): void
  (e: 'insertTransferFee', index: number): void
}
const emit = defineEmits<Emits>()

const affiliates = inject<ComputedRef<{ value: number; label: string }[]>>('affiliates')
const comAccounts = inject<ComputedRef<AccountPicker[]>>('comAccounts')
const transferFeePk = inject('transferFeePk')

// Track which row indexes have already inserted transfer fees
const insertedTransferFees = ref<Set<number>>(new Set())

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
    props.displayRows.forEach((row, index) => {
      // account가 변경된 경우에만 처리
      if (newAccounts[index] !== oldAccounts?.[index]) {
        const account = getAccountById(row.account)
        // account가 없거나 req_affiliate가 false인 경우 affiliate를 null로 초기화
        if (!account || !account.req_affiliate) {
          row.affiliate = null
        }
      }
    })
  },
  { deep: true },
)

const removeEntry = (index: number) => {
  emit('removeEntry', index)
}

// Check if transfer fee already inserted for this row
const hasInsertedFee = (index: number): boolean => {
  return insertedTransferFees.value.has(index)
}

const insertTransferFee = (index: number) => {
  // Check if already inserted for this row
  if (hasInsertedFee(index)) {
    return // Silently ignore (icon should be disabled)
  }

  const currentRow = props.displayRows[index]

  // Validate transferFeePk exists
  if (transferFeePk === undefined) {
    alert('이체수수료 계정이 설정되지 않았습니다. 관리자에게 문의하세요.')
    return
  }

  // Mark as inserted
  insertedTransferFees.value.add(index)

  emit('insertTransferFee', index)
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
      <col v-if="write_company_cash" style="width: 6%" />
    </colgroup>

    <!-- 모든 행을 수정 가능한 폼으로 렌더링 -->
    <CTableRow v-for="(row, idx) in displayRows" :key="row.pk || `new-${idx}`">
      <CTableDataCell>
        <LedgerAccount v-model="row.account" :options="comAccounts ?? []" :sort-type="sortType" />
        <!-- affiliate 필드가 필요한 경우 추가 드롭다운 표시 -->
        <div v-if="row.account && getAccountById(row.account)?.req_affiliate" class="pt-0 px-2">
          <CFormSelect v-model.number="row.affiliate" class="" placeholder="관계회사 선택">
            <option :value="null">관계회사를 선택하세요</option>
            <option v-for="aff in affiliates" :value="aff.value" :key="aff.value">
              {{ aff.label }}
            </option>
          </CFormSelect>
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
      <CTableDataCell v-if="write_company_cash" class="text-right pr-2">
        <v-icon
          v-if="sort === 2 && row.account !== transferFeePk"
          icon="mdi-playlist-plus"
          size="small"
          :color="hasInsertedFee(idx) ? 'grey' : 'indigo-lighten-1'"
          :class="hasInsertedFee(idx) ? 'cursor-not-allowed' : 'pointer'"
          :disabled="hasInsertedFee(idx)"
          v-tooltip="hasInsertedFee(idx) ? '이미 이체수수료가 추가되었습니다' : '이체수수료 추가'"
          @click="insertTransferFee(idx)"
        />
        <v-icon
          icon="mdi-close"
          size="small"
          class="ml-2 pointer"
          v-tooltip="'닫기'"
          @click="removeEntry(idx)"
        />
      </CTableDataCell>
    </CTableRow>
  </CTable>
</template>
