<script lang="ts" setup>
import { computed } from 'vue'
import { useIbs } from '@/store/pinia/ibs.ts'
import { write_company_cash } from '@/utils/pageAuth.ts'

interface NewEntryForm {
  pk?: number
  account_d1?: number | null
  account_d2?: number | null
  account_d3?: number | null
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

const ibsStore = useIbs()
const formAccD1List = computed(() => ibsStore.formAccD1List)
const formAccD2List = computed(() => ibsStore.formAccD2List)
const formAccD3List = computed(() => ibsStore.formAccD3List)

const fetchFormAccD1List = (sort: number | null) => ibsStore.fetchFormAccD1List(sort)
const fetchFormAccD2List = (sort: number | null, d1: number | null) =>
  ibsStore.fetchFormAccD2List(sort, d1)
const fetchFormAccD3List = (sort: number | null, d1: number | null, d2: number | null) =>
  ibsStore.fetchFormAccD3List(sort, d1, d2)

const removeEntry = (index: number) => {
  emit('removeEntry', index)
}
</script>

<template>
  <CTable class="m-0">
    <col style="width: 13%" />
    <col style="width: 14%" />
    <col style="width: 14%" />
    <col style="width: 23%" />
    <col style="width: 15%" />
    <col style="width: 15%" />
    <col v-if="write_company_cash" style="width: 6%" />

    <!-- 모든 행을 수정 가능한 폼으로 렌더링 -->
    <CTableRow v-for="(row, idx) in displayRows" :key="row.pk || `new-${idx}`">
      <CTableDataCell class="px-1">
        <CFormSelect v-model="row.account_d1" size="sm" placeholder="계정[대분류]">
          <option value="">---------</option>
          <option v-for="d1 in formAccD1List" :value="d1.pk" :key="d1.pk">{{ d1.name }}</option>
        </CFormSelect>
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormSelect v-model="row.account_d2" size="sm" placeholder="계정[중분류]">
          <option value="">---------</option>
          <option v-for="d2 in formAccD2List" :value="d2.pk" :key="d2.pk">{{ d2.name }}</option>
        </CFormSelect>
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormSelect v-model="row.account_d3" size="sm" placeholder="계정[소분류]">
          <option value="">---------</option>
          <option v-for="d3 in formAccD3List" :value="d3.pk" :key="d3.pk">{{ d3.name }}</option>
        </CFormSelect>
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormInput v-model="row.trader" size="sm" placeholder="거래처" />
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormInput v-model="row.amount" size="sm" type="number" min="0" placeholder="분류 금액" />
      </CTableDataCell>
      <CTableDataCell class="px-1">
        <CFormSelect v-model="row.evidence_type" size="sm" placeholder="지출 증빙">
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
