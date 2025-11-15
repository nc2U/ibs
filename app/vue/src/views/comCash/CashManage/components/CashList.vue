<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useComCash } from '@/store/pinia/comCash'
import type { CompanyBank, CashBook } from '@/store/types/comCash'
import type { Project } from '@/store/types/project'
import { TableSecondary } from '@/utils/cssMixins'
import { write_company_cash } from '@/utils/pageAuth'
import Cash from '@/views/comCash/CashManage/components/Cash.vue'
import Pagination from '@/components/Pagination'
import AccDepth from './AccDepth.vue'
import BankAcc from './BankAcc.vue'

const props = defineProps({
  company: { type: Number, default: null },
  projects: { type: Array as PropType<Project[]>, default: () => [] },
  highlightId: { type: Number, default: null },
  currentPage: { type: Number, default: 1 },
})
const emit = defineEmits([
  'page-select',
  'multi-submit',
  'on-delete',
  'patch-d3-hide',
  'patch-bank-hide',
  'on-bank-create',
  'on-bank-update',
])

const refAccDepth = ref()
const refBankAcc = ref()

const comCashStore = useComCash()
const cashesPages = computed(() => comCashStore.cashesPages)
const cashBookList = computed(() => comCashStore.cashBookList)
const comCalculated = computed(() => comCashStore.comCalculated) // 최종 정산 일자

const pageSelect = (page: number) => emit('page-select', page)

const multiSubmit = (payload: { formData: CashBook; sepData: CashBook | null }) =>
  emit('multi-submit', payload)

const onDelete = (pk: number) => emit('on-delete', pk)

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => emit('patch-d3-hide', payload)

const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)

const accCallModal = () => {
  if (props.company) refBankAcc.value.callModal()
}
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 5%" />
      <col style="width: 10%" />
      <col style="width: 11%" />
      <col style="width: 15%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 5%" />
      <col style="width: 9%" />
      <col style="width: 11%" />
      <col v-if="write_company_cash" style="width: 6%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell scope="col">거래일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">
          거래계좌
          <a href="javascript:void(0)">
            <CIcon name="cilCog" @click="accCallModal" />
          </a>
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">거래처</CTableHeaderCell>
        <CTableHeaderCell scope="col">적요</CTableHeaderCell>
        <CTableHeaderCell scope="col">입금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">출금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">계정</CTableHeaderCell>
        <CTableHeaderCell scope="col">
          세부계정
          <a href="javascript:void(0)">
            <CIcon name="cilCog" @click="refAccDepth.callModal()" />
          </a>
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">지출증빙</CTableHeaderCell>
        <CTableHeaderCell v-if="write_company_cash" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Cash
        v-for="cash in cashBookList"
        :key="cash.pk as number"
        :cash="cash"
        :projects="projects"
        :calculated="comCalculated?.calculated"
        :is-highlighted="props.highlightId === cash.pk"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @patch-d3-hide="patchD3Hide"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
      />
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="props.currentPage"
    :limit="8"
    :pages="cashesPages(15)"
    class="mt-3"
    @active-page-change="pageSelect"
  />

  <AccDepth ref="refAccDepth" @patch-d3-hide="patchD3Hide" />

  <BankAcc ref="refBankAcc" @on-bank-create="onBankCreate" @on-bank-update="onBankUpdate" />
</template>
