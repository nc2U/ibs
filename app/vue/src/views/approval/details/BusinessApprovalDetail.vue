<script setup lang="ts">
import { computed } from 'vue'
import { CTable } from '@coreui/vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import { asNum, asStr, firstStr, getBizApprovalTypeLabel } from '../utils/approvalMeta'

const props = defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
}>()

const expectedProfit = computed(() =>
  props.content.expected_profit !== undefined && props.content.expected_profit !== null
    ? asNum(props.content.expected_profit)
    : asNum(props.content.total_expected_revenue) - asNum(props.content.total_project_cost),
)
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
          승인 의결 구분
        </CTableHeaderCell>
        <CTableDataCell class="ps-3">
          <v-chip color="success" variant="flat" size="x-small">
            {{ getBizApprovalTypeLabel(asStr(content.approval_type, 'OTHER')) }}
          </v-chip>
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">사업 부지 위치</CTableHeaderCell>
        <CTableDataCell class="ps-3">{{ content.location || '-' }}</CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">사업 규모 / 용도</CTableHeaderCell>
        <CTableDataCell class="ps-3">{{ content.biz_scale_summary || '-' }}</CTableDataCell>
      </CTableRow>
      <!-- 금회 승인 요청 예산 및 전체 사업비 -->
      <CTableRow class="bg-success bg-opacity-10">
        <CTableHeaderCell class="text-center text-success fw-bold">
          금회 승인 요청액
        </CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-bold text-success fs-5">
          {{
            asNum(
              content.requested_amount ?? content.approval_budget ?? content.amount,
            ).toLocaleString()
          }}
          원
        </CTableDataCell>
        <CTableHeaderCell class="text-center">전체 총사업비</CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-bold text-danger fs-6">
          {{ asNum(content.total_project_cost).toLocaleString() }} 원
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.total_expected_revenue || content.expected_profit">
        <CTableHeaderCell class="text-center bg-more-light">예상 총분양수입</CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-semibold text-primary">
          {{ asNum(content.total_expected_revenue).toLocaleString() }} 원
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">예상 세전 이익</CTableHeaderCell>
        <CTableDataCell
          class="ps-3 fw-semibold"
          :class="expectedProfit >= 0 ? 'text-primary' : 'text-danger'"
        >
          {{ expectedProfit.toLocaleString() }} 원
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.budget_usage_plan">
        <CTableHeaderCell class="text-center bg-more-light">예산 집행 내역</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3 fw-semibold text-body">
          {{ content.budget_usage_plan }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">승인 의결 사항</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{
            firstStr(
              content.resolution_matters,
              content.purpose,
              content.reason,
              content.content,
              content.body,
            ) || '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.pm_lead || content.target_schedule">
        <CTableHeaderCell class="text-center bg-more-light">총괄 PM / 일정</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3">
          <span v-if="content.pm_lead" class="me-3 fw-semibold">
            PM/부서: {{ content.pm_lead }}
          </span>
          <span v-if="content.target_schedule" class="text-muted">
            추진일정: {{ content.target_schedule }}
          </span>
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.expected_effects || content.risk_mitigation">
        <CTableHeaderCell class="text-center bg-more-light">기대효과 / 대책</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{ firstStr(content.expected_effects, content.risk_mitigation) }}
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
