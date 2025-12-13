<script lang="ts" setup>
import { computed, type ComputedRef, inject, watch } from 'vue'
import { write_company_cash } from '@/utils/pageAuth.ts'
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
}
const props = defineProps<Props>() // Assign defineProps to a variable

interface Emits {
  (e: 'removeEntry', index: number): void
}
const emit = defineEmits<Emits>()

interface Account {
  value: number
  label: string
  parent: number | null
  is_cate_only: boolean
  depth?: number
  direction?: string
  req_affiliate?: boolean
}

const affiliates = inject<ComputedRef<{ value: number; label: string }[]>>('affiliates')
const comAccounts = inject<ComputedRef<Account[]>>('comAccounts')
const accountFilterType = computed(() => {
  if (props.sort === 1) return 'deposit' // 입금
  if (props.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

// 선택된 account가 affiliate를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): Account | undefined => {
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
</script>

<template>
  <CTable class="m-0">
    <colgroup>
      <col style="width: 26%" />
      <col style="width: 26%" />
      <col style="width: 20%" />
      <col style="width: 22%" />
      <col v-if="write_company_cash" style="width: 6%" />
    </colgroup>

    <!-- 모든 행을 수정 가능한 폼으로 렌더링 -->
    <CTableRow v-for="(row, idx) in displayRows" :key="row.pk || `new-${idx}`">
      <CTableDataCell>
        <LedgerAccount
          v-model="row.account"
          :options="comAccounts ?? []"
          :filter-type="accountFilterType"
        />
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
        <CFormSelect v-model="row.evidence_type" size="sm" placeholder="지출 증빙">
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
        <v-icon icon="mdi-close" size="small" class="ml-2 pointer" @click="removeEntry(idx)" />
      </CTableDataCell>
    </CTableRow>
  </CTable>
</template>
