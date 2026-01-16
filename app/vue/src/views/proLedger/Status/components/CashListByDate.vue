<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useProLedger } from '@/store/pinia/proLedger'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import type { ProBankTrans } from '@/store/types/proLedger'

defineProps({ date: { type: String, default: '' } })

const dateIncSet = ref<ProBankTrans[]>([])
const dateOutSet = ref<ProBankTrans[]>([])
const dateIncTotal = ref<number>(0)
const dateOutTotal = ref<number>(0)

const proLedgerStore = useProLedger()
const dateLedgerTransactions = computed(() => proLedgerStore.dateLedgerTransactions)

watch(dateLedgerTransactions, () => setData())

onBeforeMount(() => setData())

const getFirstEntry = (tx: ProBankTrans) => tx.accounting_entries?.[0]

const setData = () => {
  // sort === 1: 입금, sort === 2: 출금
  dateIncSet.value = dateLedgerTransactions.value.filter((tx: ProBankTrans) => tx.sort === 1)
  dateOutSet.value = dateLedgerTransactions.value.filter((tx: ProBankTrans) => tx.sort === 2)
  dateIncTotal.value = dateIncSet.value.reduce(
    (sum: number, tx: ProBankTrans) => sum + tx.amount,
    0,
  )
  dateOutTotal.value = dateOutSet.value.reduce(
    (sum: number, tx: ProBankTrans) => sum + tx.amount,
    0,
  )
}
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 25%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 30%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="4">
          <strong>
            <CIcon name="cilFolderOpen" />
            프로젝트 당일 입금내역
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>계정 과목</CTableHeaderCell>
        <CTableHeaderCell>입금 금액</CTableHeaderCell>
        <CTableHeaderCell>거래 계좌</CTableHeaderCell>
        <CTableHeaderCell>거래처</CTableHeaderCell>
        <CTableHeaderCell>적요</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="inc in dateIncSet" :key="inc.pk" class="text-center">
        <CTableDataCell class="text-left">
          {{ getFirstEntry(inc)?.account_name ?? '' }}
        </CTableDataCell>
        <CTableDataCell class="text-right" color="success">
          {{ numFormat(inc.amount) }}
        </CTableDataCell>
        <CTableDataCell>{{ inc.bank_account_name }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ getFirstEntry(inc)?.trader ?? '' }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ inc.content }}</CTableDataCell>
      </CTableRow>

      <CTableRow class="text-center">
        <CTableDataCell>&nbsp;</CTableDataCell>
        <CTableDataCell color="success"></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell class="text-center">합계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateIncTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 25%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 30%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="4">
          <strong>
            <CIcon name="cilFolderOpen" />
            프로젝트 당일 출금내역
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>계정 과목</CTableHeaderCell>
        <CTableHeaderCell>출금 금액</CTableHeaderCell>
        <CTableHeaderCell>거래 계좌</CTableHeaderCell>
        <CTableHeaderCell>거래처</CTableHeaderCell>
        <CTableHeaderCell>적요</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="out in dateOutSet" :key="out.pk" class="text-center">
        <CTableDataCell class="text-left">
          {{ getFirstEntry(out)?.account_name ?? '' }}
        </CTableDataCell>
        <CTableDataCell class="text-right" color="danger">
          {{ numFormat(out.amount) }}
        </CTableDataCell>
        <CTableDataCell>{{ out.bank_account_name }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ getFirstEntry(out)?.trader ?? '' }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ out.content }}</CTableDataCell>
      </CTableRow>

      <CTableRow class="text-center">
        <CTableDataCell>&nbsp;</CTableDataCell>
        <CTableDataCell color="danger"></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell class="text-center">합계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateOutTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
