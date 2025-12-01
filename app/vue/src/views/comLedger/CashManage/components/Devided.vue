<script lang="ts" setup>
import { write_company_cash } from '@/utils/pageAuth.ts'

interface NewEntryForm {
  pk?: number
  account_d1?: number
  account_d3?: number
  trader?: string
  amount?: number
  evidence_type?: string | number | null
}

interface Props {
  displayRows: NewEntryForm[]
}

interface Emits {
  (e: 'removeEntry', index: number): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const removeEntry = (index: number) => {
  emit('removeEntry', index)
}
</script>

<template>
  <CTable class="m-0">
    <col style="width: 9%" />
    <col style="width: 20%" />
    <col style="width: 24%" />
    <col style="width: 18%" />
    <col style="width: 18%" />
    <col v-if="write_company_cash" style="width: 6%" />

    <!-- 모든 행을 수정 가능한 폼으로 렌더링 -->
    <CTableRow v-for="(row, idx) in displayRows" :key="row.pk || `new-${idx}`">
      <CTableDataCell class="px-1">
        <CFormSelect v-model="row.account_d1" size="sm" placeholder="계정">
          <option value="">---------</option>
        </CFormSelect>
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormSelect v-model="row.account_d3" size="sm" placeholder="세부계정">
          <option value="">---------</option>
        </CFormSelect>
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormInput v-model="row.trader" size="sm" placeholder="거래처" />
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormInput v-model="row.amount" size="sm" type="number" min="0" placeholder="금액" />
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormSelect v-model="row.evidence_type" size="sm" placeholder="증빙">
          <option value="">---------</option>
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
</style>
