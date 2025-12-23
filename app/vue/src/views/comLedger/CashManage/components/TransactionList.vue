<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useComLedger } from '@/store/pinia/comLedger'
import { TableSecondary } from '@/utils/cssMixins'
import { write_company_cash } from '@/utils/pageAuth'
import Pagination from '@/components/Pagination'
import BankAcc from './BankAcc.vue'
import AccountManage from './AccountManage.vue'
import Transaction from './Transaction.vue'

const props = defineProps({
  company: { type: Number, default: null },
  highlightId: { type: Number, default: null },
  currentPage: { type: Number, default: 1 },
})

const emit = defineEmits(['page-select'])

const refAccountManage = ref()
const refBankAcc = ref()

const ledgerStore = useComLedger()
const transPages = computed(() => ledgerStore.transPages)
const bankTransactionList = computed(() => ledgerStore.bankTransactionList)
const comCalculated = computed(() => ledgerStore.comLedgerCalculated) // 최종 정산 일자

const pageSelect = (page: number) => emit('page-select', page)

const accCallModal = () => {
  if (props.company) refBankAcc.value.callModal()
}
</script>

<template>
  <hr class="my-0" />
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 7%" />
      <col style="width: 12%" />
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 9%" />
      <col style="width: 2%" />

      <col style="width: 14%" />
      <col style="width: 13%" />
      <col style="width: 8%" />
      <col style="width: 12%" />
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
            <CIcon name="cilCog" @click="refAccountManage.callModal()" />
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
      />
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="props.currentPage"
    :limit="8"
    :pages="transPages(15)"
    class="mt-3"
    @active-page-change="pageSelect"
  />

  <AccountManage ref="refAccountManage" />

  <BankAcc ref="refBankAcc" />
</template>
