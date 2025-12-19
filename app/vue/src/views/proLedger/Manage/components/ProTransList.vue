<script lang="ts" setup>
import { computed, ref } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { write_project_cash } from '@/utils/pageAuth'
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
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 6%" />
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col style="width: 12%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 7%" />
      <col style="width: 10%" />
      <col style="width: 9%" />
      <col v-if="write_project_cash" style="width: 6%" />
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
            <CIcon name="cilCog" @click="refAccountManage.callModal()" />
          </a>
        </CTableHeaderCell>

        <CTableHeaderCell scope="col">지출증빙</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project_cash" scope="col">비고</CTableHeaderCell>
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
      <!--        :has-children="proTrans.has_children || false"-->
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
