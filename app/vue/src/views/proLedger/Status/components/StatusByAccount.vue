<script lang="ts" setup>
import { computed } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import { useProLedger } from '@/store/pinia/proLedger.ts'

interface Props {
  date?: string
  isBalance?: string
  direct?: string
}

withDefaults(defineProps<Props>(), {
  date: '',
  isBalance: 'true',
  direct: '0',
})

const emit = defineEmits<{
  (e: 'is-exist-balance', val: boolean): void
  (e: 'direct-balance', val: boolean): void
}>()

const pLedgerStore = useProLedger()
const proBalanceByAccList = computed(() => pLedgerStore.proLedgerBalanceByAccList)

const totals = computed(() => {
  let dateIncSum = 0
  let dateOutSum = 0
  let dateIncTotal = 0
  let dateOutTotal = 0

  for (const bal of proBalanceByAccList.value) {
    dateIncSum += bal.date_inc || 0
    dateOutSum += bal.date_out || 0
    if (bal.inc_sum !== null && bal.inc_sum !== undefined) {
      dateIncTotal += bal.inc_sum || 0
    }
    if (bal.out_sum !== null && bal.out_sum !== undefined) {
      dateOutTotal += bal.out_sum || 0
    }
  }

  const dateBalance = dateIncTotal - dateOutTotal
  const preBalance = dateBalance - (dateIncSum - dateOutSum)

  return {
    preBalance,
    dateIncSum,
    dateOutSum,
    dateBalance,
  }
})

const handleExistBalanceChange = (val: boolean) => {
  emit('is-exist-balance', Boolean(val))
}

const handleDirectBalanceChange = (val: boolean) => {
  emit('direct-balance', Boolean(val))
}
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
            :model-value="!!isBalance"
            @update:model-value="handleExistBalanceChange"
          />
        </CTableDataCell>
        <CTableDataCell colspan="3">
          <CFormSwitch
            id="select-directpay"
            label="직불 용역비 계좌 포함"
            :model-value="direct === 'i'"
            @update:model-value="handleDirectBalanceChange"
          />
        </CTableDataCell>
        <CTableDataCell class="text-end">(단위: 원)</CTableDataCell>
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
      <template v-if="proBalanceByAccList.length > 0">
        <CTableRow v-for="(bal, i) in proBalanceByAccList" :key="bal.bank_id ?? i" class="text-end">
          <CTableDataCell v-if="i === 0" class="text-center" :rowspan="proBalanceByAccList.length">
            보통예금
          </CTableDataCell>
          <CTableDataCell class="text-start">{{ bal.bank_acc }}</CTableDataCell>
          <CTableDataCell class="text-start">{{ bal.bank_num }}</CTableDataCell>
          <CTableDataCell>
            {{
              numFormat(
                (bal.inc_sum || 0) - (bal.out_sum || 0) - ((bal.date_inc || 0) - (bal.date_out || 0)),
              )
            }}
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(bal.date_inc || 0) }}</CTableDataCell>
          <CTableDataCell>{{ numFormat(bal.date_out || 0) }}</CTableDataCell>
          <CTableDataCell>
            {{ numFormat((bal.inc_sum || 0) - (bal.out_sum || 0)) }}
          </CTableDataCell>
        </CTableRow>
      </template>
      <CTableRow v-else>
        <CTableDataCell colspan="7" class="text-center py-4 text-muted">
          조회된 계좌별 자금 현황이 없습니다.
        </CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-end">
        <CTableHeaderCell colspan="3" class="text-center"> 현금성 자산 계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(totals.preBalance) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(totals.dateIncSum) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(totals.dateOutSum) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(totals.dateBalance) }}</CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
