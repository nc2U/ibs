<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useComLedger } from '@/store/pinia/comLedger'
import { type LedgerTransactionForDisplay } from '@/store/types/comLedger'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'

defineProps({ date: { type: String, default: '' } })

const dateIncSet = ref<Array<LedgerTransactionForDisplay> | null>(null)
const dateOutSet = ref<Array<LedgerTransactionForDisplay> | null>(null)
const dateIncTotal = ref(0)
const dateOutTotal = ref(0)

const ledgerStore = useComLedger()
const comBankList = computed(() => ledgerStore.comBankList)
const dateCashBook = computed(() => ledgerStore.dateLedgerForDisplay)

const getBankAcc = (num: number) => {
  return comBankList.value
    .filter((b: { pk?: number }) => b.pk === num)
    .map((b: { alias_name: string }) => b.alias_name)[0]
}
const setData = () => {
  dateIncSet.value = dateCashBook.value.filter((i: LedgerTransactionForDisplay) => !!i.income)
  dateOutSet.value = dateCashBook.value.filter((o: LedgerTransactionForDisplay) => !!o.outlay)
  dateIncTotal.value = dateIncSet.value
    ? dateIncSet.value
        .map((i: LedgerTransactionForDisplay) => i.income || 0)
        .reduce((x: number, y: number) => x + y, 0)
    : 0
  dateOutTotal.value = dateOutSet.value
    ? dateOutSet.value
        .map((o: LedgerTransactionForDisplay) => o.outlay || 0)
        .reduce((x: number, y: number) => x + y, 0)
    : 0
}

watch(dateCashBook, () => setData())
onBeforeMount(() => setData())
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 14%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 20%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="6">
          <strong>
            <CIcon name="cilFolderOpen" />
            본사 당일 입금내역
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>구분</CTableHeaderCell>
        <CTableHeaderCell>계정</CTableHeaderCell>
        <CTableHeaderCell>세부 계정</CTableHeaderCell>
        <CTableHeaderCell>입금 금액</CTableHeaderCell>
        <CTableHeaderCell>거래 계좌</CTableHeaderCell>
        <CTableHeaderCell>거래처</CTableHeaderCell>
        <CTableHeaderCell>적요</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="inc in dateIncSet" :key="inc.pk" class="text-center">
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell class="text-right" color="success">
          {{ numFormat(inc.income || 0) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ getBankAcc(inc.bank_account as number) }}
        </CTableDataCell>
        <CTableDataCell class="text-left">{{ inc.trader }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ inc.content }}</CTableDataCell>
      </CTableRow>

      <CTableRow class="text-center">
        <CTableDataCell>&nbsp;</CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell color="success"></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell colspan="3" class="text-center"> 합계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateIncTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 14%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 20%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="6">
          <strong>
            <CIcon name="cilFolderOpen" />
            본사 당일 출금내역
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>구분</CTableHeaderCell>
        <CTableHeaderCell>계정</CTableHeaderCell>
        <CTableHeaderCell>세부 계정</CTableHeaderCell>
        <CTableHeaderCell>출금 금액</CTableHeaderCell>
        <CTableHeaderCell>거래 계좌</CTableHeaderCell>
        <CTableHeaderCell>거래처</CTableHeaderCell>
        <CTableHeaderCell>적요</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="out in dateOutSet" :key="out.pk" class="text-center">
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell class="text-right" color="danger">
          {{ numFormat(out.outlay || 0) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ getBankAcc(out.bank_account as number) }}
        </CTableDataCell>
        <CTableDataCell class="text-left">{{ out.trader }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ out.content }}</CTableDataCell>
      </CTableRow>
      <CTableRow class="text-center">
        <CTableDataCell>&nbsp;</CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell color="danger"></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell colspan="3" class="text-center"> 합계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateOutTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
