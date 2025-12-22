<script lang="ts" setup>
import { computed, ref } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { write_company_cash, write_project_cash } from '@/utils/pageAuth'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import Pagination from '@/components/Pagination'
import ProTrans from './ProTrans.vue'
import AccountManage from './AccountManage.vue'
import BankAcc from './BankAcc.vue'

const props = defineProps({
  project: { type: Number, default: null },
  highlightId: { type: Number, default: null },
  currentPage: { type: Number, default: 1 },
})
const emit = defineEmits(['page-select'])

const refAccountManage = ref()
const refBankAcc = ref()

const proLedgerStore = useProLedger()
const proTransPages = computed(() => proLedgerStore.proTransPages)
const proBankTransList = computed(() => proLedgerStore.proBankTransList)
const proCalculated = computed(() => proLedgerStore.proLedgerCalculated) // 최종 정산 일자

const pageSelect = (page: number) => emit('page-select', page)

const accCallModal = () => {
  if (props.project) refBankAcc.value.callModal()
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
      <ProTrans
        v-for="proTrans in proBankTransList"
        :key="proTrans.pk as number"
        :pro-trans="proTrans"
        :calculated="proCalculated?.calculated"
        :is-highlighted="props.highlightId === proTrans.pk"
      />
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="props.currentPage"
    :limit="8"
    :pages="proTransPages(15)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
  <AccountManage ref="refAccountManage" />

  <BankAcc ref="refBankAcc" />
</template>
