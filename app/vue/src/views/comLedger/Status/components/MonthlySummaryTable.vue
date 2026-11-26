<script lang="ts" setup>
import { computed } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary, TableInfo } from '@/utils/cssMixins'
import type {
  ComMonthlySummary,
  MonthlySummaryBlock,
  MonthlySummaryGroup,
  MonthlySummaryRow,
  PeriodAmounts,
} from '@/store/types/comLedger'
import { calcShare, diffClass, formatSigned } from './monthlySummaryUtils'

const props = defineProps<{
  summary: ComMonthlySummary | null
  direction: 'income' | 'expense'
}>()

const emit = defineEmits<{
  (e: 'drill', row: MonthlySummaryRow, sort: 1 | 2): void
}>()

const zero: PeriodAmounts = { prev: 0, cur: 0, ytd: 0 }
const isIncome = computed(() => props.direction === 'income')
// 입금=1, 출금=2 (드릴다운 조회용 sort)
const sort = computed<1 | 2>(() => (isIncome.value ? 1 : 2))
// 지출은 감소가 긍정 신호
const invert = computed(() => !isIncome.value)

const cfg = computed(() =>
  isIncome.value
    ? {
        title: '1. 본사 월별 수입 집계 (입금)',
        mainTitle: '수익 (영업·영업외)',
        mainLabel: '수익 집계 소계 (A)',
        mainEmpty: '조회 기간 내 수익(매출·영업외수익·배당금) 입금 내역이 없습니다.',
        otherTitle: '기타 수입 (비수익)',
        otherLabel: '수익 외 기타 수입 소계 (B)',
        otherEmpty:
          '조회 기간 내 기타 수입(차입·대여금회수·보증금·선수금·투자금 등) 내역이 없습니다.',
        unclassLabel: '미분류 입금 (은행거래 대비 분개 미완료)',
        totalLabel: '수입 합계 (A + B)',
        totalColor: 'primary',
      }
    : {
        title: '2. 본사 월별 지출 집계 (출금)',
        mainTitle: '비용 (원가·판관·영업외)',
        mainLabel: '비용 집계 소계 (C)',
        mainEmpty: '조회 기간 내 비용(매출원가·판관비·영업외비용) 출금 내역이 없습니다.',
        otherTitle: '기타 지출 (비비용)',
        otherLabel: '비용 외 기타 지출 소계 (D)',
        otherEmpty:
          '조회 기간 내 기타 지출(대여금지급·차입상환·법인카드대금·자산취득·보증금 등) 내역이 없습니다.',
        unclassLabel: '미분류 출금 (은행거래 대비 분개 미완료)',
        totalLabel: '지출 합계 (C + D)',
        totalColor: 'danger',
      },
)

const section = computed(() => {
  const s = props.summary
  if (!s) return null
  return isIncome.value
    ? { main: s.income.revenue, other: s.income.other, total: s.income.total }
    : { main: s.expense.cost, other: s.expense.other, total: s.expense.total }
})

const unclassified = computed(() => {
  const u = props.summary?.unclassified
  return (isIncome.value ? u?.in : u?.out) ?? zero
})
const hasUnclassified = computed(
  () =>
    unclassified.value.prev !== 0 || unclassified.value.cur !== 0 || unclassified.value.ytd !== 0,
)

interface FlatSectionRow {
  subTitle: string
  isFirstInSub: boolean
  subRowSpan: number
  groupName: string
  isFirstInGroup: boolean
  groupRowSpan: number
  row: MonthlySummaryRow
}

// 대분류/계정 rowspan 계산을 위해 중첩 구조를 평탄화 (값이 모두 0인 행은 제외)
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

// 첫 번째 블록(수익/비용)은 구분 셀에 강조 색상 적용
const blocks = computed(() => {
  if (!section.value) return []
  const { main, other } = section.value
  const make = (
    key: string,
    block: MonthlySummaryBlock,
    title: string,
    label: string,
    empty: string,
    highlight: boolean,
  ) => ({
    key,
    rows: flattenBlock(title, block.groups),
    total: block.total,
    label,
    empty,
    highlight,
  })
  return [
    make('main', main, cfg.value.mainTitle, cfg.value.mainLabel, cfg.value.mainEmpty, true),
    make('other', other, cfg.value.otherTitle, cfg.value.otherLabel, cfg.value.otherEmpty, false),
  ]
})

const grandTotal = computed(() => section.value?.total ?? zero)
const delta = (a: PeriodAmounts) => a.cur - a.prev
</script>

<template>
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
            {{ cfg.title }}
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
      <template v-for="blk in blocks" :key="blk.key">
        <template v-if="blk.rows.length">
          <CTableRow
            v-for="item in blk.rows"
            :key="`${blk.key}-${item.row.account}`"
            class="text-end"
          >
            <CTableDataCell
              v-if="item.isFirstInSub"
              :rowspan="item.subRowSpan"
              class="text-center fw-semibold"
              :color="blk.highlight ? TableInfo : undefined"
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
              class="text-start pointer text-primary drill-cell"
              @click="emit('drill', item.row, sort)"
            >
              <span class="acc-code text-medium-emphasis small me-1">[{{ item.row.code }}]</span>
              <span class="text-decoration-underline">{{ item.row.name }}</span>
              <v-icon icon="mdi-magnify" size="x-small" class="drill-icon ms-1" />
            </CTableDataCell>
            <CTableDataCell
              class="tabular-nums"
              :class="{ 'text-muted opacity-50': !item.row.prev }"
            >
              {{ item.row.prev ? numFormat(item.row.prev) : '-' }}
            </CTableDataCell>
            <CTableDataCell
              class="tabular-nums fw-semibold"
              :class="{ 'text-muted opacity-50': !item.row.cur }"
            >
              {{ item.row.cur ? numFormat(item.row.cur) : '-' }}
            </CTableDataCell>
            <CTableDataCell class="tabular-nums">
              <span
                v-if="delta(item.row) !== 0"
                class="diff-pill"
                :class="diffClass(delta(item.row), invert)"
              >
                {{ delta(item.row) > 0 ? '▲' : '▼' }}
                {{ formatSigned(delta(item.row)) }}
              </span>
              <span v-else class="text-muted opacity-50">-</span>
            </CTableDataCell>
            <CTableDataCell
              class="tabular-nums"
              :class="{ 'text-muted opacity-50': !item.row.ytd }"
            >
              {{ item.row.ytd ? numFormat(item.row.ytd) : '-' }}
            </CTableDataCell>
            <CTableDataCell class="text-center small text-medium-emphasis tabular-nums">
              <div>{{ calcShare(item.row.cur, grandTotal.cur) }}</div>
              <div v-if="grandTotal.cur && item.row.cur" class="share-track mt-1">
                <div
                  class="share-fill"
                  :class="isIncome ? 'bg-primary' : 'bg-danger'"
                  :style="{
                    width: `${Math.max(0, Math.min(100, (item.row.cur / grandTotal.cur) * 100))}%`,
                  }"
                />
              </div>
            </CTableDataCell>
          </CTableRow>
        </template>
        <CTableRow v-else>
          <CTableDataCell colspan="8" class="text-center py-3 text-muted">
            {{ blk.empty }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow :color="TableSecondary" class="text-end fw-semibold subtotal-row">
          <CTableHeaderCell colspan="3" class="text-center">{{ blk.label }}</CTableHeaderCell>
          <CTableHeaderCell class="tabular-nums">{{ numFormat(blk.total.prev) }}</CTableHeaderCell>
          <CTableHeaderCell class="tabular-nums">{{ numFormat(blk.total.cur) }}</CTableHeaderCell>
          <CTableHeaderCell class="tabular-nums" :class="diffClass(delta(blk.total), invert)">
            {{ formatSigned(delta(blk.total)) }}
          </CTableHeaderCell>
          <CTableHeaderCell class="tabular-nums">{{ numFormat(blk.total.ytd) }}</CTableHeaderCell>
          <CTableHeaderCell class="text-center small tabular-nums">
            {{ calcShare(blk.total.cur, grandTotal.cur) }}
          </CTableHeaderCell>
        </CTableRow>
      </template>

      <!-- 미분류 (존재 시) -->
      <CTableRow v-if="hasUnclassified" color="warning" class="text-end">
        <CTableDataCell colspan="3" class="text-center fw-semibold">
          {{ cfg.unclassLabel }}
        </CTableDataCell>
        <CTableDataCell>{{ numFormat(unclassified.prev) }}</CTableDataCell>
        <CTableDataCell class="fw-bold">{{ numFormat(unclassified.cur) }}</CTableDataCell>
        <CTableDataCell>{{ formatSigned(delta(unclassified)) }}</CTableDataCell>
        <CTableDataCell>{{ numFormat(unclassified.ytd) }}</CTableDataCell>
        <CTableDataCell class="text-center">-</CTableDataCell>
      </CTableRow>

      <!-- 합계 -->
      <CTableRow :color="cfg.totalColor" class="text-end fw-bold total-row">
        <CTableHeaderCell colspan="3" class="text-center">{{ cfg.totalLabel }}</CTableHeaderCell>
        <CTableHeaderCell class="tabular-nums">{{ numFormat(grandTotal.prev) }}</CTableHeaderCell>
        <CTableHeaderCell class="tabular-nums">{{ numFormat(grandTotal.cur) }}</CTableHeaderCell>
        <CTableHeaderCell class="tabular-nums">{{
          formatSigned(delta(grandTotal))
        }}</CTableHeaderCell>
        <CTableHeaderCell class="tabular-nums">{{ numFormat(grandTotal.ytd) }}</CTableHeaderCell>
        <CTableHeaderCell class="text-center tabular-nums">
          {{ grandTotal.cur ? '100%' : '-' }}
        </CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>

<style scoped>
.tabular-nums {
  font-variant-numeric: tabular-nums;
}

.acc-code {
  display: inline-block;
  min-width: 3.2rem;
  font-variant-numeric: tabular-nums;
}

.drill-cell .drill-icon {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.drill-cell:hover .drill-icon {
  opacity: 0.85;
}

.diff-pill {
  display: inline-block;
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  font-size: 0.85em;
}

.diff-pill.text-primary {
  background-color: rgba(var(--cui-primary-rgb, 50, 31, 219), 0.08);
}

.diff-pill.text-danger {
  background-color: rgba(var(--cui-danger-rgb, 229, 83, 83), 0.08);
}

.share-track {
  width: 100%;
  height: 4px;
  background-color: rgba(128, 128, 128, 0.16);
  border-radius: 2px;
  overflow: hidden;
}

.share-fill {
  height: 100%;
  border-radius: 2px;
  opacity: 0.75;
}

.subtotal-row > * {
  border-top: 2px solid rgba(128, 128, 128, 0.35) !important;
}

.total-row > * {
  border-top: 2px solid rgba(128, 128, 128, 0.55) !important;
}
</style>
