<script setup lang="ts">
import { computed } from 'vue'
import { CTable } from '@coreui/vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import { asNum, asStr, firstStr, getBizTypeLabel } from '../utils/approvalMeta'

const props = defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
}>()

const totalRevenue = computed(() => asNum(props.content.total_revenue))
const totalCost = computed(() => asNum(props.content.total_cost))
const netProfit = computed(() =>
  props.content.net_profit !== undefined && props.content.net_profit !== null
    ? asNum(props.content.net_profit)
    : totalRevenue.value - totalCost.value,
)
const displayProfitRate = computed(() => {
  if (
    props.content.profit_rate !== undefined &&
    props.content.profit_rate !== null &&
    props.content.profit_rate !== ''
  ) {
    return props.content.profit_rate
  }
  if (totalCost.value > 0) {
    return Number(((netProfit.value / totalCost.value) * 100).toFixed(2))
  }
  return '-'
})
</script>

<template>
  <CTable small bordered responsive class="mb-3">
    <CTableBody>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          사업명 (프로젝트)
        </CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-bold text-body fs-6">
          {{ firstStr(content.project_name, content.case_title) || '-' }}
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          사업 유형
        </CTableHeaderCell>
        <CTableDataCell class="ps-3">
          <v-chip color="info" variant="flat" size="x-small">
            {{ getBizTypeLabel(asStr(content.biz_type, 'OTHER')) }}
          </v-chip>
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">사업 부지 위치</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3">{{ content.location || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.building_scale || content.land_area || content.gross_floor_area">
        <CTableHeaderCell class="text-center bg-more-light">사업 규모 / 면적</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3">
          <span v-if="content.building_scale" class="me-3 fw-semibold">
            {{ content.building_scale }}
          </span>
          <span v-if="content.land_area" class="me-3 text-muted">
            대지: {{ content.land_area }} ㎡
          </span>
          <span v-if="content.gross_floor_area" class="text-muted">
            연면적: {{ content.gross_floor_area }} ㎡
          </span>
        </CTableDataCell>
      </CTableRow>
      <!-- 수지 분석 요약 -->
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">총 분양/매출 수입</CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-bold text-primary">
          {{ totalRevenue.toLocaleString() }} 원
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">총 사업비(지출)</CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-bold text-danger">
          {{ totalCost.toLocaleString() }} 원
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">예상 세전 이익</CTableHeaderCell>
        <CTableDataCell
          class="ps-3 fw-bold fs-6"
          :class="netProfit >= 0 ? 'text-success' : 'text-danger'"
        >
          {{ netProfit.toLocaleString() }} 원
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">수익률 (ROI)</CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-bold text-body">
          {{ displayProfitRate }} %
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.required_equity || content.pf_loan_amount">
        <CTableHeaderCell class="text-center bg-more-light">금융 / 조달 계획</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3">
          <span v-if="content.required_equity" class="me-3">
            자기자본(Equity):
            <strong>{{ asNum(content.required_equity).toLocaleString() }} 원</strong>
          </span>
          <span v-if="content.pf_loan_amount">
            PF 조달:
            <strong>{{ asNum(content.pf_loan_amount).toLocaleString() }} 원</strong>
          </span>
        </CTableDataCell>
      </CTableRow>
      <!-- 사업 일정 -->
      <CTableRow
        v-if="
          content.land_secure_date ||
          content.approval_target_date ||
          content.start_date ||
          content.completion_date
        "
      >
        <CTableHeaderCell class="text-center bg-more-light">주요 추진 일정</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3 small">
          <span v-if="content.land_secure_date" class="me-2">
            토지확보: {{ content.land_secure_date }} |
          </span>
          <span v-if="content.approval_target_date" class="me-2">
            사업승인: {{ content.approval_target_date }} |
          </span>
          <span v-if="content.start_date" class="me-2">
            착공/분양: {{ content.start_date }} |
          </span>
          <span v-if="content.completion_date"> 준공: {{ content.completion_date }} </span>
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.market_analysis">
        <CTableHeaderCell class="text-center bg-more-light">입지 및 분양성</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{ content.market_analysis }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.risk_factors">
        <CTableHeaderCell class="text-center bg-more-light">리스크 및 대책</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{ content.risk_factors }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">종합 검토의견</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{
            firstStr(
              content.recommendation,
              content.purpose,
              content.reason,
              content.content,
              content.body,
            ) || '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.enclosed_docs || content.note">
        <CTableHeaderCell class="text-center bg-more-light">첨부 서류 / 비고</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3 text-muted">
          {{ firstStr(content.enclosed_docs, content.note) }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
