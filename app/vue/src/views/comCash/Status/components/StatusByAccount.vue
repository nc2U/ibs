<script lang="ts" setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useComCash } from '@/store/pinia/comCash'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'

defineProps({ date: { type: String, default: '' } })

const emit = defineEmits(['is-exist-balance'])

const preBalance = ref(0)
const dateIncSum = ref(0)
const dateOutSum = ref(0)
const dateBalance = ref(0)

const comCashStore = useComCash()
const comBalanceByAccList = computed(() => comCashStore.comBalanceByAccList)

const getSumTotal = () => {
  const _dateIncSum =
    comBalanceByAccList.value.length !== 0
      ? comBalanceByAccList.value
          .map((i: { date_inc: number }) => i.date_inc)
          .reduce((x: number, y: number) => x + y)
      : 0
  const _dateOutSum =
    comBalanceByAccList.value.length !== 0
      ? comBalanceByAccList.value
          .map((o: { date_out: number }) => o.date_out)
          .reduce((x: number, y: number) => x + y)
      : 0
  const _dateIncTotal =
    comBalanceByAccList.value.length !== 0
      ? comBalanceByAccList.value
          .filter((i: { inc_sum: number | null }) => i.inc_sum !== null)
          .map(i => i.inc_sum || 0)
          .reduce((x: number, y: number) => x + y, 0)
      : 0
  const _dateOutTotal =
    comBalanceByAccList.value.length !== 0
      ? comBalanceByAccList.value
          .filter((o: { out_sum: number | null }) => o.out_sum !== null)
          .map(o => o.out_sum || 0)
          .reduce((x: number, y: number) => x + y, 0)
      : 0
  dateIncSum.value = _dateIncSum
  dateOutSum.value = _dateOutSum
  dateBalance.value = _dateIncTotal - _dateOutTotal
  preBalance.value = _dateIncTotal - _dateOutTotal - (_dateIncSum - _dateOutSum)
}

const isExistBalance = (val: boolean) => emit('is-exist-balance', val ? 'true' : '')

onMounted(() => getSumTotal())
watch(comBalanceByAccList, () => getSumTotal())
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
            본사 계좌별 자금현황
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 현재 </small>
        </CTableDataCell>
        <CTableDataCell colspan="4">
          <CFormSwitch
            id="select-acc-sort"
            label="잔고 존재 계좌"
            checked
            @change="isExistBalance($event.target.checked)"
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
      <CTableRow v-for="(bal, i) in comBalanceByAccList" :key="i" class="text-right">
        <CTableDataCell v-if="i === 0" class="text-center" :rowspan="comBalanceByAccList.length">
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
