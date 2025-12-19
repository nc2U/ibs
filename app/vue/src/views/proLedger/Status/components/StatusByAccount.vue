<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import { useProLedger } from '@/store/pinia/proLedger.ts'

defineProps({ date: { type: String, default: '' }, isBalance: { type: String, default: 'true' } })

const emit = defineEmits(['is-exist-balance', 'direct-balance'])

const preBalance = ref(0)
const dateIncSum = ref(0)
const dateOutSum = ref(0)
const dateBalance = ref(0)

const pLedgerStore = useProLedger()
const proBalanceByAccList = computed(() => pLedgerStore.proLedgerBalanceByAccList)

const getSumTotal = () => {
  const dateIncSumCalc =
    proBalanceByAccList.value.length !== 0
      ? proBalanceByAccList.value
          .map((i: any) => i.date_inc)
          .reduce((x: number, y: number) => x + y, 0)
      : 0
  const dateOutSumCalc =
    proBalanceByAccList.value.length !== 0
      ? proBalanceByAccList.value
          .map((o: any) => o.date_out)
          .reduce((x: number, y: number) => x + y, 0)
      : 0
  const dateIncTotalCalc =
    proBalanceByAccList.value.length !== 0
      ? proBalanceByAccList.value
          .filter((i: any) => i.inc_sum !== null)
          .map(i => i.inc_sum || 0)
          .reduce((x: number, y: number) => x + y, 0)
      : 0
  const dateOutTotalCalc =
    proBalanceByAccList.value.length !== 0
      ? proBalanceByAccList.value
          .filter((o: any) => o.out_sum !== null)
          .map(o => o.out_sum || 0)
          .reduce((x: number, y: number) => x + y, 0)
      : 0
  dateIncSum.value = dateIncSumCalc
  dateOutSum.value = dateOutSumCalc
  dateBalance.value = dateIncTotalCalc - dateOutTotalCalc
  preBalance.value = dateIncTotalCalc - dateOutTotalCalc - (dateIncSumCalc - dateOutSumCalc)
}

const isExistBalance = async (val: boolean) => emit('is-exist-balance', val)

const directBalance = (val: boolean) => emit('direct-balance', val)

watch(proBalanceByAccList, () => getSumTotal())

onBeforeMount(() => getSumTotal())
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 16%" />
      <col style="width: 16%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="2">
          <strong>
            <CIcon name="cilFolderOpen" />
            프로젝트 계좌별 자금현황
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 현재 </small>
        </CTableDataCell>
        <CTableDataCell>
          <CFormSwitch
            id="select-acc-sort"
            label="잔고 존재 계좌"
            :checked="!!isBalance"
            @change="isExistBalance($event.target.checked)"
          />
        </CTableDataCell>
        <CTableDataCell colspan="3">
          <CFormSwitch
            id="select-directpay"
            label="직불 용역비 계좌 포함"
            @change="directBalance($event.target.checked)"
          />
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell colspan="3">계좌 구분</CTableHeaderCell>
        <CTableHeaderCell>전일잔고</CTableHeaderCell>
        <CTableHeaderCell>금일입금(증가)</CTableHeaderCell>
        <CTableHeaderCell>금일출금(감소)</CTableHeaderCell>
        <CTableHeaderCell>금일잔고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="(bal, i) in proBalanceByAccList" :key="i" class="text-right">
        <CTableDataCell v-if="i === 0" class="text-center" :rowspan="proBalanceByAccList.length">
          보통예금
        </CTableDataCell>
        <CTableDataCell class="text-left">{{ bal.bank_acc }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ bal.bank_num }}</CTableDataCell>
        <CTableDataCell>
          {{ numFormat((bal.inc_sum || 0) - (bal.out_sum || 0) - (bal.date_inc - bal.date_out)) }}
        </CTableDataCell>
        <CTableDataCell>{{ numFormat(bal.date_inc) }}</CTableDataCell>
        <CTableDataCell>{{ numFormat(bal.date_out) }}</CTableDataCell>
        <CTableDataCell>
          {{ numFormat((bal.inc_sum || 0) - (bal.out_sum || 0)) }}
        </CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell colspan="3" class="text-center"> 현금성 자산 계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(preBalance) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateIncSum) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateOutSum) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateBalance) }}</CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
