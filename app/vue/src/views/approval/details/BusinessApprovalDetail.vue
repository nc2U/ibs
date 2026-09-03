<script setup lang="ts">
import {
  CTable,
  CTableBody,
  CTableRow,
  CTableHeaderCell,
  CTableDataCell,
  CBadge,
} from '@coreui/vue'

defineProps<{
  content: Record<string, any>
  document?: any
}>()
</script>

<template>
  <CTable small bordered responsive class="mb-3">
    <CTableBody>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          사업명 (프로젝트)
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold text-body fs-6">
          {{ content.project_name || content.case_title || '-' }}
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          승인 의결 구분
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge color="success">
            {{
              content.approval_type === 'NEW_LAUNCH'
                ? '사업 공식 론칭'
                : content.approval_type === 'LAND_ACQUISITION'
                  ? '토지 매매/계약금 집행'
                  : content.approval_type === 'SPC_ESTABLISH'
                    ? 'SPC/PFV 설립'
                    : content.approval_type === 'PF_EXECUTION'
                      ? '본 PF 약정/인출'
                      : content.approval_type === 'CONSTRUCTION_START'
                        ? '시공 도급/착공'
                        : '주요 사업 승인'
            }}
          </CBadge>
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">사업 부지 위치</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.location || '-' }}</CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">사업 규모 / 용도</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.biz_scale_summary || '-' }}</CTableDataCell>
      </CTableRow>
      <!-- 금회 승인 요청 예산 및 전체 사업비 -->
      <CTableRow class="bg-success bg-opacity-10">
        <CTableHeaderCell class="text-center text-success fw-bold">
          금회 승인 요청액
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold text-success fs-5">
          {{
            (
              Number(content.requested_amount ?? content.approval_budget ?? content.amount) || 0
            ).toLocaleString()
          }}
          원
        </CTableDataCell>
        <CTableHeaderCell class="text-center">전체 총사업비</CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
          {{ (Number(content.total_project_cost) || 0).toLocaleString() }} 원
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.total_expected_revenue || content.expected_profit">
        <CTableHeaderCell class="text-center bg-more-light">예상 총분양수입</CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-semibold text-primary">
          {{ (Number(content.total_expected_revenue) || 0).toLocaleString() }} 원
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">예상 세전 이익</CTableHeaderCell>
        <CTableDataCell
          class="pl-3 fw-semibold"
          :class="
            (Number(
              content.expected_profit ??
                Number(content.total_expected_revenue || 0) -
                  Number(content.total_project_cost || 0),
            ) || 0) >= 0
              ? 'text-primary'
              : 'text-danger'
          "
        >
          {{
            (
              Number(
                content.expected_profit ??
                  Number(content.total_expected_revenue || 0) -
                    Number(content.total_project_cost || 0),
              ) || 0
            ).toLocaleString()
          }}
          원
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.budget_usage_plan">
        <CTableHeaderCell class="text-center bg-more-light">예산 집행 내역</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 fw-semibold text-body">
          {{ content.budget_usage_plan }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">승인 의결 사항</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{
            content.resolution_matters ||
            content.purpose ||
            content.reason ||
            content.content ||
            content.body ||
            '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.pm_lead || content.target_schedule">
        <CTableHeaderCell class="text-center bg-more-light">총괄 PM / 일정</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">
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
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{ content.expected_effects || content.risk_mitigation }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.enclosed_docs || content.note">
        <CTableHeaderCell class="text-center bg-more-light">첨부 서류 / 비고</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-muted">
          {{ content.enclosed_docs || content.note }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
