<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { numFormat } from '@/utils/baseMixins.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { write_company_cash } from '@/utils/pageAuth.ts'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { CTable } from '@coreui/vue'

const is_balanced = ref(true)

const [route, router] = [useRoute(), useRouter()]

const transId = computed(() => Number(route.params.transId) || null)

const ledgerStore = useComLedger()
const transaction = computed(() => ledgerStore.bankTransaction)

onBeforeMount(() => {
  if (transId.value) ledgerStore.fetchBankTransaction(transId.value)
  if (transaction.value) {
    is_balanced.value = transaction.value.is_balanced
  }
})
</script>

<template>
  <CRow class="text-right py-1 mb-1 bg-light-green-lighten-5">
    <CCol class="text-left">25-10-15 12:40 ∙ 대영[농협] ∙ 농협 4953 ∙ ∙ 찬혜원 분할 중...</CCol>
    <CCol col="2">
      <span>거래내역 금액: {{ transaction?.sort_name }} {{ transaction?.amount }}</span> ∙
      <span>분류 금액 합계: 출금 41,000</span> ∙
      <span class="strong" :class="{ 'text-danger': !is_balanced }">차액: 출금 0</span>
      <v-btn size="x-small" class="ml-3" disabled>증빙으로 분할</v-btn>
      <v-btn size="x-small" @click="router.push({ name: '본사 거래 내역' })">취소</v-btn>
      <v-btn color="success" size="x-small">저장</v-btn>
    </CCol>
  </CRow>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
      <col style="width: 12%" />
      <col style="width: 8%" />
      <col style="width: 5%" />
      <col style="width: 11%" />
      <col style="width: 13%" />
      <col style="width: 11%" />
      <col style="width: 8%" />
      <col v-if="write_company_cash" style="width: 5%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary">
        <CTableHeaderCell class="pl-3" colspan="5">은행거래내역</CTableHeaderCell>
        <CTableHeaderCell class="pl-0" :colspan="write_company_cash ? 6 : 5">
          <span class="text-grey mr-2">|</span> 분류 내역
        </CTableHeaderCell>
      </CTableRow>

      <CTableRow :color="TableSecondary">
        <CTableHeaderCell scope="col">거래일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">메모</CTableHeaderCell>
        <CTableHeaderCell scope="col">
          거래계좌
          <!--          <a href="javascript:void(0)">-->
          <!--            <CIcon name="cilCog" @click="accCallModal" />-->
          <!--          </a>-->
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">적요</CTableHeaderCell>
        <CTableHeaderCell scope="col">입출금액</CTableHeaderCell>
        <CTableHeaderCell class="text-left pl-0" scope="col">
          <span class="text-grey mr-2">|</span> 계정
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">
          세부계정
          <!--          <a href="javascript:void(0)">-->
          <!--            <CIcon name="cilCog" @click="refAccDepth.callModal()" />-->
          <!--          </a>-->
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">거래처</CTableHeaderCell>
        <CTableHeaderCell scope="col">분류 금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">지출증빙</CTableHeaderCell>
        <CTableHeaderCell v-if="write_company_cash" scope="col"></CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow>
        <CTableDataCell>{{ transaction?.deal_date ?? '' }}</CTableDataCell>
        <CTableDataCell>{{ transaction?.note }}</CTableDataCell>
        <CTableDataCell>{{ transaction?.bank_account_name }}</CTableDataCell>
        <CTableDataCell>{{ transaction?.content }}</CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(transaction?.amount ?? 0) }}
          <v-btn icon="mdi-plus" density="compact" rounded="1" size="22" class="ml-2 pointer" />
        </CTableDataCell>
        <CTableDataCell colspan="6">
          <CTable class="m-0">
            <col style="width: 9%" />
            <col style="width: 20%" />
            <col style="width: 24%" />
            <col style="width: 18%" />
            <col style="width: 18%" />
            <col v-if="write_company_cash" style="width: 6%" />
            <CTableRow v-for="entry in transaction?.accounting_entries" :key="entry.pk">
              <CTableDataCell class="pl-2">{{ entry.account_d1_name }}</CTableDataCell>
              <CTableDataCell>{{ entry.account_d3_name }}</CTableDataCell>
              <CTableDataCell>{{ entry.trader }}</CTableDataCell>
              <CTableDataCell>{{ numFormat(entry.amount) }}</CTableDataCell>
              <CTableDataCell>{{ entry.evidence_type_display }}</CTableDataCell>
              <CTableDataCell class="text-right pr-2">
                <v-icon icon="mdi-close" size="small" class="ml-2 pointer" />
              </CTableDataCell>
            </CTableRow>
          </CTable>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
