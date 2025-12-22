<script lang="ts" setup>
import { computed, type ComputedRef, inject, watch } from 'vue'
import { write_project_cash } from '@/utils/pageAuth.ts'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import LedgerAccount from '@/components/LedgerAccount/Index.vue'

interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
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

interface Emits {
  (e: 'removeEntry', index: number): void
}
const emit = defineEmits<Emits>()

const proAccounts = inject<ComputedRef<AccountPicker[]>>('proAccounts')
const sortType = computed(() => {
  if (props.sort === 1) return 'deposit' // 입금
  if (props.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

const removeEntry = (index: number) => {
  emit('removeEntry', index)
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
          :required="sort === 2"
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
