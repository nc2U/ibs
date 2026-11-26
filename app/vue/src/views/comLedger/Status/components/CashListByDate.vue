<script lang="ts" setup>
import { computed } from 'vue'
import { useComLedger } from '@/store/pinia/comLedger'
import { TableSecondary } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins'
import type { BankTransaction } from '@/store/types/comLedger'

interface Props {
  date?: string
}

withDefaults(defineProps<Props>(), {
  date: '',
})

const ledgerStore = useComLedger()
const dateLedgerTransactions = computed(() => ledgerStore.dateLedgerTransactions)

const dateIncSet = computed(() =>
  dateLedgerTransactions.value.filter((tx: BankTransaction) => tx.sort === 1),
)
const dateOutSet = computed(() =>
  dateLedgerTransactions.value.filter((tx: BankTransaction) => tx.sort === 2),
)

const dateIncTotal = computed(() =>
  dateIncSet.value.reduce((sum: number, tx: BankTransaction) => sum + (tx.amount || 0), 0),
)
const dateOutTotal = computed(() =>
  dateOutSet.value.reduce((sum: number, tx: BankTransaction) => sum + (tx.amount || 0), 0),
)

const getFirstEntry = (tx: BankTransaction) => tx.accounting_entries?.[0]
const getEntryCountSuffix = (tx: BankTransaction) =>
  tx.accounting_entries && tx.accounting_entries.length > 1
    ? ` 외 ${tx.accounting_entries.length - 1}건`
    : ''
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 15%" />
      <col style="width: 30%" />
      <col style="width: 15%" />
      <col style="width: 25%" />
      <col style="width: 15%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="4">
          <strong>
            <CIcon name="cilFolderOpen" />
            본사 당일 입금내역
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-end">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>거래 계좌</CTableHeaderCell>
        <CTableHeaderCell>적요</CTableHeaderCell>
        <CTableHeaderCell>입금 금액</CTableHeaderCell>
        <CTableHeaderCell>계정 과목</CTableHeaderCell>
        <CTableHeaderCell>거래처</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <template v-if="dateIncSet.length > 0">
        <CTableRow v-for="inc in dateIncSet" :key="inc.pk" class="text-center">
          <CTableDataCell>{{ inc.bank_account_name }}</CTableDataCell>
          <CTableDataCell class="text-start">{{ inc.content }}</CTableDataCell>
          <CTableDataCell class="text-end" color="success">
            {{ numFormat(inc.amount) }}
          </CTableDataCell>
          <CTableDataCell class="text-start">
            <template v-if="getFirstEntry(inc)">
              {{ getFirstEntry(inc)?.account_name ?? '' }}{{ getEntryCountSuffix(inc) }}
            </template>
            <span v-else class="text-muted">(미분류)</span>
          </CTableDataCell>
          <CTableDataCell class="text-start">
            {{ getFirstEntry(inc)?.trader ?? '' }}{{ getEntryCountSuffix(inc) }}
          </CTableDataCell>
        </CTableRow>
      </template>
      <CTableRow v-else>
        <CTableDataCell colspan="5" class="text-center py-4 text-muted">
          당일 입금 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-end">
        <CTableHeaderCell class="text-center">합계</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateIncTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 15%" />
      <col style="width: 30%" />
      <col style="width: 15%" />
      <col style="width: 25%" />
      <col style="width: 15%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="4">
          <strong>
            <CIcon name="cilFolderOpen" />
            본사 당일 출금내역
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-end">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>거래 계좌</CTableHeaderCell>
        <CTableHeaderCell>적요</CTableHeaderCell>
        <CTableHeaderCell>출금 금액</CTableHeaderCell>
        <CTableHeaderCell>계정 과목</CTableHeaderCell>
        <CTableHeaderCell>거래처</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <template v-if="dateOutSet.length > 0">
        <CTableRow v-for="out in dateOutSet" :key="out.pk" class="text-center">
          <CTableDataCell>{{ out.bank_account_name }}</CTableDataCell>
          <CTableDataCell class="text-start">{{ out.content }}</CTableDataCell>
          <CTableDataCell class="text-end" color="danger">
            {{ numFormat(out.amount) }}
          </CTableDataCell>
          <CTableDataCell class="text-start">
            <template v-if="getFirstEntry(out)">
              {{ getFirstEntry(out)?.account_name ?? '' }}{{ getEntryCountSuffix(out) }}
            </template>
            <span v-else class="text-muted">(미분류)</span>
          </CTableDataCell>
          <CTableDataCell class="text-start">
            {{ getFirstEntry(out)?.trader ?? '' }}{{ getEntryCountSuffix(out) }}
          </CTableDataCell>
        </CTableRow>
      </template>
      <CTableRow v-else>
        <CTableDataCell colspan="5" class="text-center py-4 text-muted">
          당일 출금 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-end">
        <CTableHeaderCell class="text-center">합계</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateOutTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
