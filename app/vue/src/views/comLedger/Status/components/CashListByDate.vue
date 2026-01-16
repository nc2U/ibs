<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useComLedger } from '@/store/pinia/comLedger'
import { TableSecondary } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins'
import type { BankTransaction } from '@/store/types/comLedger'

defineProps({ date: { type: String, default: '' } })

const dateIncSet = ref<BankTransaction[]>([])
const dateOutSet = ref<BankTransaction[]>([])
const dateIncTotal = ref<number>(0)
const dateOutTotal = ref<number>(0)

const ledgerStore = useComLedger()
const dateLedgerTransactions = computed(() => ledgerStore.dateLedgerTransactions)

watch(dateLedgerTransactions, () => setData())

onBeforeMount(() => setData())

const getFirstEntry = (tx: BankTransaction) => tx.accounting_entries?.[0]

const setData = () => {
  // sort === 1: 입금, sort === 2: 출금
  dateIncSet.value = dateLedgerTransactions.value.filter((tx: BankTransaction) => tx.sort === 1)
  dateOutSet.value = dateLedgerTransactions.value.filter((tx: BankTransaction) => tx.sort === 2)
  dateIncTotal.value = dateIncSet.value.reduce(
    (sum: number, tx: BankTransaction) => sum + tx.amount,
    0,
  )
  dateOutTotal.value = dateOutSet.value.reduce(
    (sum: number, tx: BankTransaction) => sum + tx.amount,
    0,
  )
}
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
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
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
      <CTableRow v-for="inc in dateIncSet" :key="inc.pk" class="text-center">
        <CTableDataCell>{{ inc.bank_account_name }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ inc.content }}</CTableDataCell>
        <CTableDataCell class="text-right" color="success">
          {{ numFormat(inc.amount) }}
        </CTableDataCell>
        <CTableDataCell class="text-left">
          {{ getFirstEntry(inc)?.account_name ?? '' }}
        </CTableDataCell>
        <CTableDataCell class="text-left">{{ getFirstEntry(inc)?.trader ?? '' }}</CTableDataCell>
      </CTableRow>

      <CTableRow class="text-center">
        <CTableDataCell>&nbsp;</CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell color="success"></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
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
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
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
      <CTableRow v-for="out in dateOutSet" :key="out.pk" class="text-center">
        <CTableDataCell>{{ out.bank_account_name }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ out.content }}</CTableDataCell>
        <CTableDataCell class="text-right" color="danger">
          {{ numFormat(out.amount) }}
        </CTableDataCell>
        <CTableDataCell class="text-left">
          {{ getFirstEntry(out)?.account_name ?? '' }}
        </CTableDataCell>
        <CTableDataCell class="text-left">{{ getFirstEntry(out)?.trader ?? '' }}</CTableDataCell>
      </CTableRow>

      <CTableRow class="text-center">
        <CTableDataCell>&nbsp;</CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell color="danger"></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell class="text-center">합계</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateOutTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
