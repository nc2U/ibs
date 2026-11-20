<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useComLedger } from '@/store/pinia/comLedger'
import { TableSecondary, TableInfo } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins'
import { diffClass, formatSigned } from './monthlySummaryUtils'
import type { BankTransaction, MonthlySummaryRow, PeriodAmounts } from '@/store/types/comLedger'
import MonthlySummaryTable from './MonthlySummaryTable.vue'

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

const transferDiff = computed(() => {
  const trfIn = summary.value?.transfer.in ?? zeroAmounts
  const trfOut = summary.value?.transfer.out ?? zeroAmounts
  return {
    prev: trfIn.prev - trfOut.prev,
    cur: trfIn.cur - trfOut.cur,
    ytd: trfIn.ytd - trfOut.ytd,
  }
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

// 계정 클릭 드릴다운 모달 (페이지네이션 + 경합 방지)
const drillModalVisible = ref(false)
const drillLoading = ref(false)
const drillMoreLoading = ref(false)
const drillAccount = ref<{ account: number; code: string; name: string; sort: 1 | 2 } | null>(null)
const drillTransactions = ref<BankTransaction[]>([])
const drillCount = ref(0)
const drillPage = ref(1)
let drillSeq = 0

const hasMoreDrill = computed(() => drillTransactions.value.length < drillCount.value)

const fetchDrillPage = async (page: number) => {
  if (!props.company || !summary.value || !drillAccount.value) return
  const seq = ++drillSeq
  const isFirst = page === 1
  if (isFirst) drillLoading.value = true
  else drillMoreLoading.value = true
  const data = await ledgerStore.fetchComMonthlyDrilldown({
    company: props.company,
    from_deal_date: summary.value.from_date,
    to_deal_date: summary.value.to_date,
    account: drillAccount.value.account,
    sort: drillAccount.value.sort,
    page,
  })
  if (seq !== drillSeq) return // 더 최신 요청이 있으면 무시
  if (data) {
    const results = data.results ?? []
    drillTransactions.value = isFirst ? results : [...drillTransactions.value, ...results]
    drillCount.value = data.count ?? drillTransactions.value.length
    drillPage.value = page
  } else if (isFirst) {
    drillTransactions.value = []
    drillCount.value = 0
  }
  drillLoading.value = false
  drillMoreLoading.value = false
}

const openAccountDrilldown = async (row: MonthlySummaryRow, sort: 1 | 2) => {
  if (!props.company || !summary.value) return
  drillAccount.value = { account: row.account, code: row.code, name: row.name, sort }
  drillTransactions.value = []
  drillCount.value = 0
  drillModalVisible.value = true
  await fetchDrillPage(1)
}

const loadMoreDrill = () => fetchDrillPage(drillPage.value + 1)

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
  <CRow v-if="summary" class="mb-4 g-2 kpi-bridge">
    <CCol sm="6" lg="3" class="kpi-step">
      <CCard class="h-100 border-top-secondary border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="text-medium-emphasis small">기초 잔고 (전월 말)</div>
          <div class="fw-bold fs-6 text-end mt-1 tabular-nums">
            {{ numFormat(summary.opening_balance) }}원
          </div>
        </CCardBody>
      </CCard>
      <span class="kpi-op d-none d-lg-flex" aria-hidden="true">+</span>
    </CCol>

    <CCol sm="6" lg="2" class="kpi-step">
      <CCard class="h-100 border-top-primary border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="text-medium-emphasis small">당월 수입 계 (외부유입)</div>
          <div class="fw-bold fs-6 text-primary text-end mt-1 tabular-nums">
            +{{ numFormat(summary.income.total.cur) }}원
          </div>
          <div class="text-medium-emphasis text-end kpi-sub tabular-nums">
            수익 {{ numFormat(summary.income.revenue.total.cur) }} / 기타
            {{ numFormat(summary.income.other.total.cur) }}
          </div>
        </CCardBody>
      </CCard>
      <span class="kpi-op d-none d-lg-flex" aria-hidden="true">−</span>
    </CCol>

    <CCol sm="6" lg="2" class="kpi-step">
      <CCard class="h-100 border-top-danger border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="text-medium-emphasis small">당월 지출 계 (외부유출)</div>
          <div class="fw-bold fs-6 text-danger text-end mt-1 tabular-nums">
            -{{ numFormat(summary.expense.total.cur) }}원
          </div>
          <div class="text-medium-emphasis text-end kpi-sub tabular-nums">
            비용 {{ numFormat(summary.expense.cost.total.cur) }} / 기타
            {{ numFormat(summary.expense.other.total.cur) }}
          </div>
        </CCardBody>
      </CCard>
      <span class="kpi-op d-none d-lg-flex" aria-hidden="true">=</span>
    </CCol>

    <CCol sm="6" lg="2" class="kpi-step">
      <CCard class="h-100 border-top-info border-top-3">
        <CCardBody class="py-2 px-3">
          <div class="d-flex justify-content-between align-items-center">
            <span class="text-medium-emphasis small">손익 현금수지 (수익-비용)</span>
            <span class="tabular-nums" :class="diffClass(summary.operating_net.cur)">
              {{ formatSigned(summary.operating_net.cur) }}원
            </span>
          </div>
          <div class="d-flex justify-content-between align-items-center mt-1">
            <span class="text-medium-emphasis small">전체 순증감 (수입-지출)</span>
            <span class="fw-bold tabular-nums" :class="diffClass(summary.net.cur)">
              {{ formatSigned(summary.net.cur) }}원
            </span>
          </div>
        </CCardBody>
      </CCard>
      <span class="kpi-op d-none d-lg-flex" aria-hidden="true">→</span>
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
          <div class="fw-bold fs-6 text-end mt-1 tabular-nums">
            {{ numFormat(summary.closing_balance) }}원
          </div>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>

  <!-- 3. 수입 집계 테이블 -->
  <MonthlySummaryTable
    :summary="summary"
    direction="income"
    @drill="(r, s) => openAccountDrilldown(r, s)"
  />

  <!-- 4. 지출 집계 테이블 -->
  <MonthlySummaryTable
    :summary="summary"
    direction="expense"
    @drill="(r, s) => openAccountDrilldown(r, s)"
  />

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
        <CTableHeaderCell rowspan="2" class="align-middle">관계회사 / 프로젝트</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" class="align-middle">구분</CTableHeaderCell>
        <CTableHeaderCell colspan="2">자금 운용 (대여 · 회수)</CTableHeaderCell>
        <CTableHeaderCell colspan="2">자금 조달 (차입 · 상환)</CTableHeaderCell>
        <CTableHeaderCell rowspan="2" class="align-middle">당월 순유출입 (누계)</CTableHeaderCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>당월 대여(유출)</CTableHeaderCell>
        <CTableHeaderCell>당월 회수(유입)</CTableHeaderCell>
        <CTableHeaderCell>당월 차입(유입)</CTableHeaderCell>
        <CTableHeaderCell>당월 상환(유출)</CTableHeaderCell>
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
        <CTableDataCell class="tabular-nums" :class="{ 'text-muted opacity-50': !aff.cur.lend }">
          {{ aff.cur.lend ? numFormat(aff.cur.lend) : '-' }}
        </CTableDataCell>
        <CTableDataCell class="tabular-nums" :class="{ 'text-muted opacity-50': !aff.cur.collect }">
          {{ aff.cur.collect ? numFormat(aff.cur.collect) : '-' }}
        </CTableDataCell>
        <CTableDataCell class="tabular-nums" :class="{ 'text-muted opacity-50': !aff.cur.borrow }">
          {{ aff.cur.borrow ? numFormat(aff.cur.borrow) : '-' }}
        </CTableDataCell>
        <CTableDataCell class="tabular-nums" :class="{ 'text-muted opacity-50': !aff.cur.repay }">
          {{ aff.cur.repay ? numFormat(aff.cur.repay) : '-' }}
        </CTableDataCell>
        <CTableDataCell class="tabular-nums" :class="diffClass(aff.cur.net)">
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
              해당 기간의 거래 내역이 없습니다.
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
      <div
        v-if="!drillLoading && drillCount"
        class="d-flex justify-content-between align-items-center mt-2"
      >
        <span class="text-medium-emphasis small">
          총 {{ numFormat(drillCount) }}건 중 {{ numFormat(drillTransactions.length) }}건 표시
        </span>
        <v-btn
          v-if="hasMoreDrill"
          size="small"
          color="primary"
          variant="tonal"
          :loading="drillMoreLoading"
          @click="loadMoreDrill"
        >
          더 보기
        </v-btn>
      </div>
    </CModalBody>
    <CModalFooter>
      <v-btn size="small" color="secondary" variant="tonal" @click="drillModalVisible = false">
        닫기
      </v-btn>
    </CModalFooter>
  </CModal>
</template>

<style scoped>
.tabular-nums {
  font-variant-numeric: tabular-nums;
}

.kpi-sub {
  font-size: 0.75rem;
}

.kpi-step {
  position: relative;
}

.kpi-op {
  position: absolute;
  right: -0.45rem;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  width: 1.1rem;
  height: 1.1rem;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: var(--cui-body-bg, #fff);
  border: 1px solid rgba(128, 128, 128, 0.35);
  color: var(--cui-secondary-color, #6c757d);
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1;
}
</style>
