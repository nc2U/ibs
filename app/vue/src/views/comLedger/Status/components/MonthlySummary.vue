<script lang="ts" setup>
import { computed, ref } from 'vue'
import api from '@/api'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary, TableInfo } from '@/utils/cssMixins'
import { errorHandle } from '@/utils/helper'
import { useComLedger } from '@/store/pinia/comLedger'
import type {
  BankTransaction,
  MonthlySummaryGroup,
  MonthlySummaryRow,
  PeriodAmounts,
} from '@/store/types/comLedger'

const props = withDefaults(
  defineProps<{
    date?: string
    company?: number | null
    periodMode?: 'mtd' | 'full'
  }>(),
  {
    date: '',
    company: null,
    periodMode: 'mtd',
  },
)

const emit = defineEmits<{
  (e: 'change-date', date: string): void
  (e: 'update:periodMode', mode: 'mtd' | 'full'): void
}>()

const ledgerStore = useComLedger()
const summary = computed(() => ledgerStore.comMonthlySummary)

const zeroAmounts: PeriodAmounts = { prev: 0, cur: 0, ytd: 0 }

const yearMonthLabel = computed(() => {
  const base = props.date || summary.value?.to_date || ''
  if (!/^\d{4}-\d{2}/.test(base)) return ''
  const [y, m] = base.split('-')
  return `${y}년 ${Number(m)}월`
})

const moveMonth = (delta: number) => {
  const base = props.date || summary.value?.to_date || ''
  if (!/^\d{4}-\d{2}-\d{2}$/.test(base)) return
  const [y, m] = base.split('-').map(Number)
  const target = new Date(y, m - 1 + delta + 1, 0) // 이동할 월의 말일
  const todayStr = new Date(new Date().getTime() + 32400000).toISOString().slice(0, 10)
  const yyyy = target.getFullYear()
  const mm = String(target.getMonth() + 1).padStart(2, '0')
  const dd = String(target.getDate()).padStart(2, '0')
  const candidate = `${yyyy}-${mm}-${dd}`
  emit('change-date', candidate > todayStr ? todayStr : candidate)
}

const formatSigned = (val: number) => {
  if (!val) return '-'
  const prefix = val > 0 ? '+' : ''
  return `${prefix}${numFormat(val)}`
}

const diffClass = (val: number, invertColor = false) => {
  if (!val) return 'text-muted'
  const isPositive = invertColor ? val < 0 : val > 0
  return isPositive ? 'text-primary fw-semibold' : 'text-danger fw-semibold'
}

const calcShare = (amount: number, total: number) => {
  if (!total || !amount) return '-'
  return `${((amount / total) * 100).toFixed(1)}%`
}

interface FlatSectionRow {
  subTitle: string
  isFirstInSub: boolean
  subRowSpan: number
  groupName: string
  isFirstInGroup: boolean
  groupRowSpan: number
  row: MonthlySummaryRow
}

const flattenBlock = (subTitle: string, groups: MonthlySummaryGroup[]): FlatSectionRow[] => {
  const activeGroups = groups
    .map(g => ({
      ...g,
      rows: g.rows.filter(r => r.prev !== 0 || r.cur !== 0 || r.ytd !== 0),
    }))
    .filter(g => g.rows.length > 0)

  const totalRows = activeGroups.reduce((acc, g) => acc + g.rows.length, 0)
  const result: FlatSectionRow[] = []
  let subIdx = 0

  for (const grp of activeGroups) {
    grp.rows.forEach((row, grpIdx) => {
      result.push({
        subTitle,
        isFirstInSub: subIdx === 0,
        subRowSpan: totalRows,
        groupName: grp.name,
        isFirstInGroup: grpIdx === 0,
        groupRowSpan: grp.rows.length,
        row,
      })
      subIdx += 1
    })
  }
  return result
}

const revenueRows = computed(() =>
  flattenBlock('수익 (영업·영업외)', summary.value?.income.revenue.groups ?? []),
)
const otherIncomeRows = computed(() =>
  flattenBlock('기타 수입 (비수익)', summary.value?.income.other.groups ?? []),
)
const costRows = computed(() =>
  flattenBlock('비용 (원가·판관·영업외)', summary.value?.expense.cost.groups ?? []),
)
const otherExpenseRows = computed(() =>
  flattenBlock('기타 지출 (비비용)', summary.value?.expense.other.groups ?? []),
)

const transferDiff = computed(() => {
  const trfIn = summary.value?.transfer.in ?? zeroAmounts
  const trfOut = summary.value?.transfer.out ?? zeroAmounts
  return {
    prev: trfIn.prev - trfOut.prev,
    cur: trfIn.cur - trfOut.cur,
    ytd: trfIn.ytd - trfOut.ytd,
  }
})

const hasUnclassifiedIn = computed(() => {
  const u = summary.value?.unclassified.in
  return !!(u && (u.prev !== 0 || u.cur !== 0 || u.ytd !== 0))
})

const hasUnclassifiedOut = computed(() => {
  const u = summary.value?.unclassified.out
  return !!(u && (u.prev !== 0 || u.cur !== 0 || u.ytd !== 0))
})

const isReconciled = computed(() => {
  if (!summary.value) return true
  const expected =
    summary.value.opening_balance + summary.value.bank_flow.in.cur - summary.value.bank_flow.out.cur
  return (
    expected === summary.value.closing_balance &&
    summary.value.unclassified.in.cur === 0 &&
    summary.value.unclassified.out.cur === 0
  )
})

// 계정 클릭 드릴다운 모달
const drillModalVisible = ref(false)
const drillLoading = ref(false)
const drillAccount = ref<{ account: number; code: string; name: string; sort: 1 | 2 } | null>(null)
const drillTransactions = ref<BankTransaction[]>([])

const openAccountDrilldown = async (row: MonthlySummaryRow, sort: 1 | 2) => {
  if (!props.company || !summary.value) return
  drillAccount.value = { account: row.account, code: row.code, name: row.name, sort }
  drillModalVisible.value = true
  drillLoading.value = true
  try {
    const res = await api.get('/ledger/company-transaction/', {
      params: {
        company: props.company,
        from_deal_date: summary.value.from_date,
        to_deal_date: summary.value.to_date,
        account: row.account,
        sort,
        page: 1,
      },
    })
    drillTransactions.value = res.data.results ?? []
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: unknown } }
    errorHandle(axiosErr.response?.data ?? err)
    drillTransactions.value = []
  } finally {
    drillLoading.value = false
  }
}

const getMatchedEntryAmount = (tx: BankTransaction, accountId?: number) => {
  if (!accountId || !tx.accounting_entries?.length) return tx.amount
  return tx.accounting_entries
    .filter(e => e.account === accountId)
    .reduce((sum, e) => sum + (e.amount || 0), 0)
}

const getMatchedEntryTrader = (tx: BankTransaction, accountId?: number) => {
  if (!accountId || !tx.accounting_entries?.length) return ''
  return (
    tx.accounting_entries
      .filter(e => e.account === accountId && e.trader)
      .map(e => e.trader)
      .join(', ') || ''
  )
}
</script>

<template>
  <!-- 1. 상단 기간 컨트롤 바 -->
  <CRow class="align-items-center justify-content-between mb-3 g-2">
    <CCol xs="12" md="auto" class="d-flex align-items-center gap-2">
      <v-btn size="small" variant="outlined" color="secondary" @click="moveMonth(-1)">
        <v-icon icon="mdi-chevron-left" size="small" /> 전월
      </v-btn>
      <span class="fw-bold fs-6 px-2">{{ yearMonthLabel }}</span>
      <v-btn size="small" variant="outlined" color="secondary" @click="moveMonth(1)">
        익월 <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
      <span v-if="summary" class="text-medium-emphasis small ms-2">
        집계 기간: <strong>{{ summary.from_date }} ~ {{ summary.to_date }}</strong>
        <span class="ms-1">
          (전월 동기: {{ summary.periods.prev.from }} ~ {{ summary.periods.prev.to }})
        </span>
      </span>
    </CCol>

    <CCol xs="12" md="auto" class="text-md-end">
      <v-btn-toggle
        :model-value="periodMode"
        mandatory
        density="compact"
        variant="outlined"
        color="primary"
        class="text-muted"
        @update:model-value="val => emit('update:periodMode', val)"
      >
        <v-btn value="mtd" size="small">기준일 누계 (MTD)</v-btn>
        <v-btn value="full" size="small">해당 월 전체 (말일)</v-btn>
      </v-btn-toggle>
    </CCol>
  </CRow>

  <!-- 2. 상단 5-카드 현금흐름 브릿지 KPI -->
  <CRow v-if="summary" class="mb-4 g-2">
    <CCol sm="6" lg="2">
      <CCard class="h-100 border-top-secondary border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="text-medium-emphasis small">기초 잔고 (전월 말)</div>
          <div class="fw-bold fs-6 text-end mt-1">{{ numFormat(summary.opening_balance) }}원</div>
        </CCardBody>
      </CCard>
    </CCol>

    <CCol sm="6" lg="2">
      <CCard class="h-100 border-top-primary border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="text-medium-emphasis small">당월 수입 계 (외부유입)</div>
          <div class="fw-bold fs-6 text-primary text-end mt-1">
            +{{ numFormat(summary.income.total.cur) }}원
          </div>
          <div class="text-medium-emphasis text-end" style="font-size: 0.75rem">
            수익 {{ numFormat(summary.income.revenue.total.cur) }} / 기타
            {{ numFormat(summary.income.other.total.cur) }}
          </div>
        </CCardBody>
      </CCard>
    </CCol>

    <CCol sm="6" lg="2">
      <CCard class="h-100 border-top-danger border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="text-medium-emphasis small">당월 지출 계 (외부유출)</div>
          <div class="fw-bold fs-6 text-danger text-end mt-1">
            -{{ numFormat(summary.expense.total.cur) }}원
          </div>
          <div class="text-medium-emphasis text-end" style="font-size: 0.75rem">
            비용 {{ numFormat(summary.expense.cost.total.cur) }} / 기타
            {{ numFormat(summary.expense.other.total.cur) }}
          </div>
        </CCardBody>
      </CCard>
    </CCol>

    <CCol sm="6" lg="3">
      <CCard class="h-100 border-top-info border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="d-flex justify-content-between align-items-center">
            <span class="text-medium-emphasis small">손익 현금수지 (수익-비용)</span>
            <span :class="diffClass(summary.operating_net.cur)">
              {{ formatSigned(summary.operating_net.cur) }}원
            </span>
          </div>
          <div class="d-flex justify-content-between align-items-center mt-1">
            <span class="text-medium-emphasis small">전체 순증감 (수입-지출)</span>
            <span class="fw-bold" :class="diffClass(summary.net.cur)">
              {{ formatSigned(summary.net.cur) }}원
            </span>
          </div>
        </CCardBody>
      </CCard>
    </CCol>

    <CCol sm="12" lg="3">
      <CCard class="h-100 border-top-success border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="d-flex justify-content-between align-items-center">
            <span class="text-medium-emphasis small">기말 잔고 ({{ summary.to_date }})</span>
            <v-chip size="x-small" :color="isReconciled ? 'success' : 'warning'" variant="flat">
              {{ isReconciled ? '계좌잔고 일치' : '미분류 확인 필요' }}
            </v-chip>
          </div>
          <div class="fw-bold fs-6 text-end mt-1">{{ numFormat(summary.closing_balance) }}원</div>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>

  <!-- 3. 수입 집계 테이블 -->
  <CTable hover responsive bordered align="middle" class="mb-4">
    <colgroup>
      <col style="width: 14%" />
      <col style="width: 14%" />
      <col style="width: 18%" />
      <col style="width: 13%" />
      <col style="width: 14%" />
      <col style="width: 11%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="7">
          <strong>
            <CIcon name="cilFolderOpen" />
            1. 본사 월별 수입 집계 (입금)
          </strong>
          <small class="text-medium-emphasis ms-1">
            ({{ summary?.from_date }} ~ {{ summary?.to_date }}) — 계정 클릭 시 상세 거래내역 조회
          </small>
        </CTableDataCell>
        <CTableDataCell class="text-end">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>구분</CTableHeaderCell>
        <CTableHeaderCell>대분류</CTableHeaderCell>
        <CTableHeaderCell>계정 과목</CTableHeaderCell>
        <CTableHeaderCell>전월 동기</CTableHeaderCell>
        <CTableHeaderCell>당월 실적</CTableHeaderCell>
        <CTableHeaderCell>전월 대비</CTableHeaderCell>
        <CTableHeaderCell>당해 누계(YTD)</CTableHeaderCell>
        <CTableHeaderCell>구성비</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <!-- 1-A. 수익 집계 -->
      <template v-if="revenueRows.length">
        <CTableRow v-for="item in revenueRows" :key="`rev-${item.row.account}`" class="text-end">
          <CTableDataCell
            v-if="item.isFirstInSub"
            :rowspan="item.subRowSpan"
            class="text-center fw-semibold"
            :color="TableInfo"
          >
            {{ item.subTitle }}
          </CTableDataCell>
          <CTableDataCell
            v-if="item.isFirstInGroup"
            :rowspan="item.groupRowSpan"
            class="text-center"
          >
            {{ item.groupName }}
          </CTableDataCell>
          <CTableDataCell
            class="text-start pointer text-primary"
            @click="openAccountDrilldown(item.row, 1)"
          >
            <span class="text-medium-emphasis small me-1">[{{ item.row.code }}]</span>
            <span class="text-decoration-underline">{{ item.row.name }}</span>
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(item.row.prev) }}</CTableDataCell>
          <CTableDataCell class="fw-semibold">{{ numFormat(item.row.cur) }}</CTableDataCell>
          <CTableDataCell :class="diffClass(item.row.cur - item.row.prev)">
            {{ formatSigned(item.row.cur - item.row.prev) }}
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(item.row.ytd) }}</CTableDataCell>
          <CTableDataCell class="text-center small text-medium-emphasis">
            {{ calcShare(item.row.cur, summary?.income.total.cur || 0) }}
          </CTableDataCell>
        </CTableRow>
      </template>
      <CTableRow v-else>
        <CTableDataCell colspan="8" class="text-center py-3 text-muted">
          조회 기간 내 수익(매출·영업외수익·배당금) 입금 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-end fw-semibold">
        <CTableHeaderCell colspan="3" class="text-center">수익 집계 소계 (A)</CTableHeaderCell>
        <CTableHeaderCell>{{
          numFormat(summary?.income.revenue.total.prev || 0)
        }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.income.revenue.total.cur || 0) }}</CTableHeaderCell>
        <CTableHeaderCell
          :class="
            diffClass(
              (summary?.income.revenue.total.cur || 0) - (summary?.income.revenue.total.prev || 0),
            )
          "
        >
          {{
            formatSigned(
              (summary?.income.revenue.total.cur || 0) - (summary?.income.revenue.total.prev || 0),
            )
          }}
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.income.revenue.total.ytd || 0) }}</CTableHeaderCell>
        <CTableHeaderCell class="text-center small">
          {{ calcShare(summary?.income.revenue.total.cur || 0, summary?.income.total.cur || 0) }}
        </CTableHeaderCell>
      </CTableRow>

      <!-- 1-B. 수익 외 기타 수입 -->
      <template v-if="otherIncomeRows.length">
        <CTableRow
          v-for="item in otherIncomeRows"
          :key="`inc-oth-${item.row.account}`"
          class="text-end"
        >
          <CTableDataCell
            v-if="item.isFirstInSub"
            :rowspan="item.subRowSpan"
            class="text-center fw-semibold"
          >
            {{ item.subTitle }}
          </CTableDataCell>
          <CTableDataCell
            v-if="item.isFirstInGroup"
            :rowspan="item.groupRowSpan"
            class="text-center"
          >
            {{ item.groupName }}
          </CTableDataCell>
          <CTableDataCell
            class="text-start pointer text-primary"
            @click="openAccountDrilldown(item.row, 1)"
          >
            <span class="text-medium-emphasis small me-1">[{{ item.row.code }}]</span>
            <span class="text-decoration-underline">{{ item.row.name }}</span>
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(item.row.prev) }}</CTableDataCell>
          <CTableDataCell class="fw-semibold">{{ numFormat(item.row.cur) }}</CTableDataCell>
          <CTableDataCell :class="diffClass(item.row.cur - item.row.prev)">
            {{ formatSigned(item.row.cur - item.row.prev) }}
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(item.row.ytd) }}</CTableDataCell>
          <CTableDataCell class="text-center small text-medium-emphasis">
            {{ calcShare(item.row.cur, summary?.income.total.cur || 0) }}
          </CTableDataCell>
        </CTableRow>
      </template>
      <CTableRow v-else>
        <CTableDataCell colspan="8" class="text-center py-3 text-muted">
          조회 기간 내 기타 수입(차입·대여금회수·보증금·선수금·투자금 등) 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-end fw-semibold">
        <CTableHeaderCell colspan="3" class="text-center">
          수익 외 기타 수입 소계 (B)
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.income.other.total.prev || 0) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.income.other.total.cur || 0) }}</CTableHeaderCell>
        <CTableHeaderCell
          :class="
            diffClass(
              (summary?.income.other.total.cur || 0) - (summary?.income.other.total.prev || 0),
            )
          "
        >
          {{
            formatSigned(
              (summary?.income.other.total.cur || 0) - (summary?.income.other.total.prev || 0),
            )
          }}
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.income.other.total.ytd || 0) }}</CTableHeaderCell>
        <CTableHeaderCell class="text-center small">
          {{ calcShare(summary?.income.other.total.cur || 0, summary?.income.total.cur || 0) }}
        </CTableHeaderCell>
      </CTableRow>

      <!-- 미분류 입금 (존재 시) -->
      <CTableRow v-if="hasUnclassifiedIn" color="warning" class="text-end">
        <CTableDataCell colspan="3" class="text-center fw-semibold">
          미분류 입금 (은행거래 대비 분개 미완료)
        </CTableDataCell>
        <CTableDataCell>{{ numFormat(summary?.unclassified.in.prev || 0) }}</CTableDataCell>
        <CTableDataCell class="fw-bold">
          {{ numFormat(summary?.unclassified.in.cur || 0) }}
        </CTableDataCell>
        <CTableDataCell>
          {{
            formatSigned((summary?.unclassified.in.cur || 0) - (summary?.unclassified.in.prev || 0))
          }}
        </CTableDataCell>
        <CTableDataCell>{{ numFormat(summary?.unclassified.in.ytd || 0) }}</CTableDataCell>
        <CTableDataCell class="text-center">-</CTableDataCell>
      </CTableRow>

      <!-- 수입 총계 -->
      <CTableRow color="primary" class="text-end fw-bold">
        <CTableHeaderCell colspan="3" class="text-center"> 수입 합계 (A + B) </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.income.total.prev || 0) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.income.total.cur || 0) }}</CTableHeaderCell>
        <CTableHeaderCell>
          {{ formatSigned((summary?.income.total.cur || 0) - (summary?.income.total.prev || 0)) }}
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.income.total.ytd || 0) }}</CTableHeaderCell>
        <CTableHeaderCell class="text-center">100%</CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <!-- 4. 지출 집계 테이블 -->
  <CTable hover responsive bordered align="middle" class="mb-4">
    <colgroup>
      <col style="width: 14%" />
      <col style="width: 14%" />
      <col style="width: 18%" />
      <col style="width: 13%" />
      <col style="width: 14%" />
      <col style="width: 11%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="7">
          <strong>
            <CIcon name="cilFolderOpen" />
            2. 본사 월별 지출 집계 (출금)
          </strong>
          <small class="text-medium-emphasis ms-1">
            ({{ summary?.from_date }} ~ {{ summary?.to_date }}) — 계정 클릭 시 상세 거래내역 조회
          </small>
        </CTableDataCell>
        <CTableDataCell class="text-end">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>구분</CTableHeaderCell>
        <CTableHeaderCell>대분류</CTableHeaderCell>
        <CTableHeaderCell>계정 과목</CTableHeaderCell>
        <CTableHeaderCell>전월 동기</CTableHeaderCell>
        <CTableHeaderCell>당월 실적</CTableHeaderCell>
        <CTableHeaderCell>전월 대비</CTableHeaderCell>
        <CTableHeaderCell>당해 누계(YTD)</CTableHeaderCell>
        <CTableHeaderCell>구성비</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <!-- 2-A. 비용 항목 집계 -->
      <template v-if="costRows.length">
        <CTableRow v-for="item in costRows" :key="`cost-${item.row.account}`" class="text-end">
          <CTableDataCell
            v-if="item.isFirstInSub"
            :rowspan="item.subRowSpan"
            class="text-center fw-semibold"
            :color="TableInfo"
          >
            {{ item.subTitle }}
          </CTableDataCell>
          <CTableDataCell
            v-if="item.isFirstInGroup"
            :rowspan="item.groupRowSpan"
            class="text-center"
          >
            {{ item.groupName }}
          </CTableDataCell>
          <CTableDataCell
            class="text-start pointer text-primary"
            @click="openAccountDrilldown(item.row, 2)"
          >
            <span class="text-medium-emphasis small me-1">[{{ item.row.code }}]</span>
            <span class="text-decoration-underline">{{ item.row.name }}</span>
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(item.row.prev) }}</CTableDataCell>
          <CTableDataCell class="fw-semibold">{{ numFormat(item.row.cur) }}</CTableDataCell>
          <CTableDataCell :class="diffClass(item.row.cur - item.row.prev, true)">
            {{ formatSigned(item.row.cur - item.row.prev) }}
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(item.row.ytd) }}</CTableDataCell>
          <CTableDataCell class="text-center small text-medium-emphasis">
            {{ calcShare(item.row.cur, summary?.expense.total.cur || 0) }}
          </CTableDataCell>
        </CTableRow>
      </template>
      <CTableRow v-else>
        <CTableDataCell colspan="8" class="text-center py-3 text-muted">
          조회 기간 내 비용(매출원가·판관비·영업외비용) 출금 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-end fw-semibold">
        <CTableHeaderCell colspan="3" class="text-center">비용 집계 소계 (C)</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.cost.total.prev || 0) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.cost.total.cur || 0) }}</CTableHeaderCell>
        <CTableHeaderCell
          :class="
            diffClass(
              (summary?.expense.cost.total.cur || 0) - (summary?.expense.cost.total.prev || 0),
              true,
            )
          "
        >
          {{
            formatSigned(
              (summary?.expense.cost.total.cur || 0) - (summary?.expense.cost.total.prev || 0),
            )
          }}
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.cost.total.ytd || 0) }}</CTableHeaderCell>
        <CTableHeaderCell class="text-center small">
          {{ calcShare(summary?.expense.cost.total.cur || 0, summary?.expense.total.cur || 0) }}
        </CTableHeaderCell>
      </CTableRow>

      <!-- 2-B. 비용 외 기타 지출 -->
      <template v-if="otherExpenseRows.length">
        <CTableRow
          v-for="item in otherExpenseRows"
          :key="`exp-oth-${item.row.account}`"
          class="text-end"
        >
          <CTableDataCell
            v-if="item.isFirstInSub"
            :rowspan="item.subRowSpan"
            class="text-center fw-semibold"
          >
            {{ item.subTitle }}
          </CTableDataCell>
          <CTableDataCell
            v-if="item.isFirstInGroup"
            :rowspan="item.groupRowSpan"
            class="text-center"
          >
            {{ item.groupName }}
          </CTableDataCell>
          <CTableDataCell
            class="text-start pointer text-primary"
            @click="openAccountDrilldown(item.row, 2)"
          >
            <span class="text-medium-emphasis small me-1">[{{ item.row.code }}]</span>
            <span class="text-decoration-underline">{{ item.row.name }}</span>
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(item.row.prev) }}</CTableDataCell>
          <CTableDataCell class="fw-semibold">{{ numFormat(item.row.cur) }}</CTableDataCell>
          <CTableDataCell :class="diffClass(item.row.cur - item.row.prev, true)">
            {{ formatSigned(item.row.cur - item.row.prev) }}
          </CTableDataCell>
          <CTableDataCell>{{ numFormat(item.row.ytd) }}</CTableDataCell>
          <CTableDataCell class="text-center small text-medium-emphasis">
            {{ calcShare(item.row.cur, summary?.expense.total.cur || 0) }}
          </CTableDataCell>
        </CTableRow>
      </template>
      <CTableRow v-else>
        <CTableDataCell colspan="8" class="text-center py-3 text-muted">
          조회 기간 내 기타 지출(대여금지급·차입상환·법인카드대금·자산취득·보증금 등) 내역이
          없습니다.
        </CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-end fw-semibold">
        <CTableHeaderCell colspan="3" class="text-center">
          비용 외 기타 지출 소계 (D)
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.other.total.prev || 0) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.other.total.cur || 0) }}</CTableHeaderCell>
        <CTableHeaderCell
          :class="
            diffClass(
              (summary?.expense.other.total.cur || 0) - (summary?.expense.other.total.prev || 0),
              true,
            )
          "
        >
          {{
            formatSigned(
              (summary?.expense.other.total.cur || 0) - (summary?.expense.other.total.prev || 0),
            )
          }}
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.other.total.ytd || 0) }}</CTableHeaderCell>
        <CTableHeaderCell class="text-center small">
          {{ calcShare(summary?.expense.other.total.cur || 0, summary?.expense.total.cur || 0) }}
        </CTableHeaderCell>
      </CTableRow>

      <!-- 미분류 출금 (존재 시) -->
      <CTableRow v-if="hasUnclassifiedOut" color="warning" class="text-end">
        <CTableDataCell colspan="3" class="text-center fw-semibold">
          미분류 출금 (은행거래 대비 분개 미완료)
        </CTableDataCell>
        <CTableDataCell>{{ numFormat(summary?.unclassified.out.prev || 0) }}</CTableDataCell>
        <CTableDataCell class="fw-bold">
          {{ numFormat(summary?.unclassified.out.cur || 0) }}
        </CTableDataCell>
        <CTableDataCell>
          {{
            formatSigned(
              (summary?.unclassified.out.cur || 0) - (summary?.unclassified.out.prev || 0),
            )
          }}
        </CTableDataCell>
        <CTableDataCell>{{ numFormat(summary?.unclassified.out.ytd || 0) }}</CTableDataCell>
        <CTableDataCell class="text-center">-</CTableDataCell>
      </CTableRow>

      <!-- 지출 총계 -->
      <CTableRow color="danger" class="text-end fw-bold">
        <CTableHeaderCell colspan="3" class="text-center"> 지출 합계 (C + D) </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.total.prev || 0) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.total.cur || 0) }}</CTableHeaderCell>
        <CTableHeaderCell>
          {{ formatSigned((summary?.expense.total.cur || 0) - (summary?.expense.total.prev || 0)) }}
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(summary?.expense.total.ytd || 0) }}</CTableHeaderCell>
        <CTableHeaderCell class="text-center">100%</CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <!-- 5. 현금수지 요약 및 내부대체/거래취소 참고표 -->
  <CTable hover responsive bordered align="middle" class="mb-4">
    <colgroup>
      <col style="width: 46%" />
      <col style="width: 13%" />
      <col style="width: 14%" />
      <col style="width: 11%" />
      <col style="width: 16%" />
    </colgroup>
    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>3. 현금수지 요약 및 참고 항목 (내부대체 · 거래취소)</CTableHeaderCell>
        <CTableHeaderCell>전월 동기</CTableHeaderCell>
        <CTableHeaderCell>당월 실적</CTableHeaderCell>
        <CTableHeaderCell>전월 대비</CTableHeaderCell>
        <CTableHeaderCell>당해 누계(YTD)</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody class="text-end">
      <CTableRow class="fw-bold">
        <CTableDataCell class="text-start"> 손익 현금수지 (수익 A - 비용 C) </CTableDataCell>
        <CTableDataCell :class="diffClass(summary?.operating_net.prev || 0)">
          {{ formatSigned(summary?.operating_net.prev || 0) }}
        </CTableDataCell>
        <CTableDataCell :class="diffClass(summary?.operating_net.cur || 0)">
          {{ formatSigned(summary?.operating_net.cur || 0) }}
        </CTableDataCell>
        <CTableDataCell
          :class="diffClass((summary?.operating_net.cur || 0) - (summary?.operating_net.prev || 0))"
        >
          {{ formatSigned((summary?.operating_net.cur || 0) - (summary?.operating_net.prev || 0)) }}
        </CTableDataCell>
        <CTableDataCell :class="diffClass(summary?.operating_net.ytd || 0)">
          {{ formatSigned(summary?.operating_net.ytd || 0) }}
        </CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableInfo" class="fw-bold">
        <CTableDataCell class="text-start">
          전체 순현금증감 (수입 합계 - 지출 합계)
        </CTableDataCell>
        <CTableDataCell :class="diffClass(summary?.net.prev || 0)">
          {{ formatSigned(summary?.net.prev || 0) }}
        </CTableDataCell>
        <CTableDataCell :class="diffClass(summary?.net.cur || 0)">
          {{ formatSigned(summary?.net.cur || 0) }}
        </CTableDataCell>
        <CTableDataCell :class="diffClass((summary?.net.cur || 0) - (summary?.net.prev || 0))">
          {{ formatSigned((summary?.net.cur || 0) - (summary?.net.prev || 0)) }}
        </CTableDataCell>
        <CTableDataCell :class="diffClass(summary?.net.ytd || 0)">
          {{ formatSigned(summary?.net.ytd || 0) }}
        </CTableDataCell>
      </CTableRow>

      <CTableRow class="text-medium-emphasis small">
        <CTableDataCell class="text-start">
          [참고 / 합계 제외] 내부 자금이동 — 대체 입금 / 대체 출금 (차액)
          <v-chip
            v-if="transferDiff.cur !== 0"
            size="x-small"
            color="warning"
            variant="flat"
            class="ms-1"
          >
            대체 차액 확인
          </v-chip>
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(summary?.transfer.in.prev || 0) }} /
          {{ numFormat(summary?.transfer.out.prev || 0) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(summary?.transfer.in.cur || 0) }} /
          {{ numFormat(summary?.transfer.out.cur || 0) }}
          <span v-if="transferDiff.cur !== 0" class="text-danger fw-bold">
            ({{ formatSigned(transferDiff.cur) }})
          </span>
        </CTableDataCell>
        <CTableDataCell>{{ formatSigned(transferDiff.cur - transferDiff.prev) }}</CTableDataCell>
        <CTableDataCell>
          {{ numFormat(summary?.transfer.in.ytd || 0) }} /
          {{ numFormat(summary?.transfer.out.ytd || 0) }}
        </CTableDataCell>
      </CTableRow>

      <CTableRow class="text-medium-emphasis small">
        <CTableDataCell class="text-start">
          [참고 / 합계 제외] 거래 취소 — 취소 입금 / 취소 출금
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(summary?.cancel.in.prev || 0) }} /
          {{ numFormat(summary?.cancel.out.prev || 0) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(summary?.cancel.in.cur || 0) }} /
          {{ numFormat(summary?.cancel.out.cur || 0) }}
        </CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
        <CTableDataCell>
          {{ numFormat(summary?.cancel.in.ytd || 0) }} /
          {{ numFormat(summary?.cancel.out.ytd || 0) }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <!-- 6. 관계회사·프로젝트(Affiliate)별 자금 이동 요약 -->
  <CTable v-if="summary?.affiliates?.length" hover responsive bordered align="middle" class="mb-4">
    <colgroup>
      <col style="width: 24%" />
      <col style="width: 10%" />
      <col style="width: 13%" />
      <col style="width: 13%" />
      <col style="width: 13%" />
      <col style="width: 13%" />
      <col style="width: 14%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="6">
          <strong>
            <CIcon name="cilFolderOpen" />
            4. 관계회사 · 프로젝트별 자금 이동 요약 (대여 · 회수 · 차입 · 상환)
          </strong>
        </CTableDataCell>
        <CTableDataCell class="text-end">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>관계회사 / 프로젝트</CTableHeaderCell>
        <CTableHeaderCell>구분</CTableHeaderCell>
        <CTableHeaderCell>당월 대여(유출)</CTableHeaderCell>
        <CTableHeaderCell>당월 회수(유입)</CTableHeaderCell>
        <CTableHeaderCell>당월 차입(유입)</CTableHeaderCell>
        <CTableHeaderCell>당월 상환(유출)</CTableHeaderCell>
        <CTableHeaderCell>당월 순유출입 (누계)</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="aff in summary.affiliates" :key="aff.affiliate" class="text-end">
        <CTableDataCell class="text-start fw-semibold">{{ aff.label }}</CTableDataCell>
        <CTableDataCell class="text-center">
          <v-chip size="x-small" :color="aff.sort === 'company' ? 'primary' : 'info'">
            {{ aff.sort === 'company' ? '관계회사' : '프로젝트' }}
          </v-chip>
        </CTableDataCell>
        <CTableDataCell>{{ numFormat(aff.cur.lend) }}</CTableDataCell>
        <CTableDataCell>{{ numFormat(aff.cur.collect) }}</CTableDataCell>
        <CTableDataCell>{{ numFormat(aff.cur.borrow) }}</CTableDataCell>
        <CTableDataCell>{{ numFormat(aff.cur.repay) }}</CTableDataCell>
        <CTableDataCell :class="diffClass(aff.cur.net)">
          {{ formatSigned(aff.cur.net) }}
          <span class="text-medium-emphasis small ms-1">({{ formatSigned(aff.ytd.net) }})</span>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <!-- 7. 계정별 거래내역 드릴다운 모달 -->
  <CModal
    :visible="drillModalVisible"
    size="xl"
    alignment="center"
    @close="drillModalVisible = false"
  >
    <CModalHeader>
      <CModalTitle>
        <span v-if="drillAccount">
          [{{ drillAccount.code }}] {{ drillAccount.name }} — 상세 거래내역 ({{
            summary?.from_date
          }}
          ~ {{ summary?.to_date }})
        </span>
      </CModalTitle>
    </CModalHeader>
    <CModalBody>
      <div v-if="drillLoading" class="text-center py-4 text-medium-emphasis">
        거래 내역을 불러오는 중입니다...
      </div>
      <CTable v-else hover responsive bordered small align="middle" class="mb-0">
        <CTableHead>
          <CTableRow :color="TableSecondary" class="text-center">
            <CTableHeaderCell>거래일자</CTableHeaderCell>
            <CTableHeaderCell>거래계좌</CTableHeaderCell>
            <CTableHeaderCell>적요</CTableHeaderCell>
            <CTableHeaderCell>거래처</CTableHeaderCell>
            <CTableHeaderCell>해당 계정 분개금액</CTableHeaderCell>
            <CTableHeaderCell>은행 거래원금액</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <template v-if="drillTransactions.length">
            <CTableRow v-for="tx in drillTransactions" :key="tx.pk" class="text-center">
              <CTableDataCell>{{ tx.deal_date }}</CTableDataCell>
              <CTableDataCell>{{ tx.bank_account_name }}</CTableDataCell>
              <CTableDataCell class="text-start">{{ tx.content }}</CTableDataCell>
              <CTableDataCell class="text-start">
                {{ getMatchedEntryTrader(tx, drillAccount?.account) }}
              </CTableDataCell>
              <CTableDataCell class="text-end fw-semibold">
                {{ numFormat(getMatchedEntryAmount(tx, drillAccount?.account)) }}
              </CTableDataCell>
              <CTableDataCell class="text-end text-medium-emphasis">
                {{ numFormat(tx.amount) }}
              </CTableDataCell>
            </CTableRow>
          </template>
          <CTableRow v-else>
            <CTableDataCell colspan="6" class="text-center py-4 text-muted">
              해당 기간의 거래 내역이 없습니다. (최대 15건까지 우선 표시되며 전체 내역은 본사 거래
              관리에서 확인할 수 있습니다.)
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CModalBody>
    <CModalFooter>
      <v-btn size="small" color="secondary" variant="tonal" @click="drillModalVisible = false">
        닫기
      </v-btn>
    </CModalFooter>
  </CModal>
</template>
