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
          현안 분야
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge color="danger" class="me-1">
            {{
              content.decision_type === 'DESIGN_SPEC'
                ? '설계변경/스펙'
                : content.decision_type === 'SALES_PRICING'
                  ? '분양가/분양조건'
                  : content.decision_type === 'CONSTRUCTION_METHOD'
                    ? '시공공법/자재'
                    : content.decision_type === 'FINANCIAL_STRUCTURING'
                      ? '금융구조/PF'
                      : content.decision_type === 'CLAIM_DISPUTE'
                        ? '민원/분쟁대응'
                        : content.decision_type === 'CONTRACTOR_TERMINATION'
                          ? '업체선정/타절'
                          : '프로젝트 의사결정'
            }}
          </CBadge>
          <CBadge
            :color="
              content.urgency === 'CRITICAL'
                ? 'danger'
                : content.urgency === 'URGENT'
                  ? 'warning'
                  : 'secondary'
            "
          >
            {{
              content.urgency === 'CRITICAL'
                ? '즉시 결정'
                : content.urgency === 'URGENT'
                  ? '긴급'
                  : '보통'
            }}
          </CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          결정 목표일
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold">{{ content.decision_due_date || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">심의 안건명</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 fw-bold text-body fs-6">
          {{ content.decision_subject || content.case_title || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.financial_impact">
        <CTableHeaderCell class="text-center bg-more-light">재무적 영향(비용)</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 fw-bold text-danger fs-6">
          {{ (Number(content.financial_impact) || 0).toLocaleString() }} 원
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">현안 배경 및 문제점</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{
            content.background_issue ||
            content.purpose ||
            content.reason ||
            content.content ||
            content.body ||
            '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <!-- 대안 비교 -->
      <CTableRow v-if="content.option_1">
        <CTableHeaderCell class="text-center bg-secondary bg-opacity-10 text-secondary">
          대안 1 (원안)
        </CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{ content.option_1 }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.option_2">
        <CTableHeaderCell class="text-center bg-primary bg-opacity-10 text-primary fw-bold">
          대안 2 (추천안)
        </CTableHeaderCell>
        <CTableDataCell
          colspan="3"
          class="pl-3 bg-light fw-semibold text-body"
          style="white-space: pre-wrap"
        >
          {{ content.option_2 }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.option_3">
        <CTableHeaderCell class="text-center bg-more-light">대안 3 (기타안)</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{ content.option_3 }}
        </CTableDataCell>
      </CTableRow>
      <!-- 추천안 -->
      <CTableRow class="bg-warning bg-opacity-10">
        <CTableHeaderCell class="text-center fw-bold text-body">주관부서 추천안</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 fw-bold text-body" style="white-space: pre-wrap">
          {{ content.recommendation || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.action_plan">
        <CTableHeaderCell class="text-center bg-more-light">향후 조치 계획</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">{{ content.action_plan }}</CTableDataCell>
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
