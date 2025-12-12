<script lang="ts" setup>
import { type ComputedRef, inject } from 'vue'
import { write_company_cash } from '@/utils/pageAuth.ts'
import LedgerAccount from '@/components/LedgerAccount/Index.vue'

interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  affiliated?: number | null
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
}

interface Props {
  displayRows: NewEntryForm[]
}

interface Emits {
  (e: 'removeEntry', index: number): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

interface Account {
  value: number
  label: string
  parent: number | null
  is_cate_only: boolean
  depth?: number
  direction?: string
}

const comAccounts = inject<ComputedRef<Account[]>>('comAccounts')
// const accountFilterType = computed(() => {
//   if (form.value.sort === 1) return 'deposit' // 입금
//   if (form.value.sort === 2) return 'withdraw' // 출금
//   return null // 전체
// })

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
      <CTableDataCell class="px-1">
        <LedgerAccount v-model="row.account" :options="comAccounts ?? []" />
        <!--          :filter-type="accountFilterType"-->
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

<style lang="scss" scoped>
:deep(.form-control-sm),
:deep(.form-select-sm) {
  padding: 0.25rem 0.5rem !important;
}
:deep(input) {
  margin: 2px !important;
}

/* 드롭다운이 td 외부에도 렌더링되도록 설정 */
:deep(table),
:deep(tbody),
:deep(tr),
:deep(td) {
  overflow: visible !important;
}

:deep(.dropdown) {
  overflow: visible !important;
}

:deep(.dropdown-menu) {
  position: absolute !important;
  z-index: 1050 !important;
}
</style>
