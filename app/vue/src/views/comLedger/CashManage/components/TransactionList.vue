<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useComLedger } from '@/store/pinia/comLedger'
import type { AccountingEntry, BankTransaction, CompanyBank } from '@/store/types/comLedger'
import { TableSecondary } from '@/utils/cssMixins'
import { write_company_cash } from '@/utils/pageAuth'
import Pagination from '@/components/Pagination'
import BankAcc from './BankAcc.vue'
import AccDepth from './AccDepth.vue'
import Transaction from './Transaction.vue'

const props = defineProps({
  company: { type: Number, default: null },
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

const ledgerStore = useComLedger()
const cashesPages = computed(() => ledgerStore.cashesPages)
const bankTransactionList = computed(() => ledgerStore.bankTransactionList)
const comCalculated = computed(() => ledgerStore.comCalculated) // 최종 정산 일자

const pageSelect = (page: number) => emit('page-select', page)

const multiSubmit = (payload: { formData: BankTransaction; sepData: AccountingEntry | null }) =>
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
  <hr class="mb-0" />
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 7%" />
      <col style="width: 12%" />
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 9%" />
      <col style="width: 2%" />

      <col style="width: 10%" />
      <col style="width: 16%" />
      <col style="width: 8%" />
      <col style="width: 13%" />
      <col v-if="write_company_cash" style="width: 3%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary">
        <CTableHeaderCell class="pl-3" colspan="6">은행거래내역</CTableHeaderCell>
        <CTableHeaderCell class="pl-0" :colspan="write_company_cash ? 6 : 5">
          <span class="text-grey mr-2">|</span> 분류 내역
        </CTableHeaderCell>
      </CTableRow>

      <CTableRow :color="TableSecondary">
        <CTableHeaderCell scope="col">거래일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">메모</CTableHeaderCell>
        <CTableHeaderCell scope="col">
          거래계좌
          <a href="javascript:void(0)" class="ml-1">
            <CIcon name="cilCog" @click="accCallModal" />
          </a>
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">적요</CTableHeaderCell>
        <CTableHeaderCell scope="col">입출금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">확인</CTableHeaderCell>
        <CTableHeaderCell class="pl-0" scope="col">
          <span class="text-grey mr-2">|</span> 계정
          <a href="javascript:void(0)" class="ml-1">
            <CIcon name="cilCog" @click="refAccDepth.callModal()" />
          </a>
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">거래처</CTableHeaderCell>
        <CTableHeaderCell scope="col">분류 금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">지출증빙</CTableHeaderCell>
        <CTableHeaderCell v-if="write_company_cash" scope="col"></CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Transaction
        v-for="transaction in bankTransactionList"
        :key="transaction.pk as number"
        :transaction="transaction"
        :calculated="comCalculated?.calculated"
        :is-highlighted="props.highlightId === transaction.pk"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @patch-d3-hide="patchD3Hide"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
      />
      <!--        :has-children="transaction.has_children || false"-->
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
