<script setup lang="ts">
import { CTable, CTableBody, CTableDataCell, CTableHeaderCell, CTableRow } from '@coreui/vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import {
  asNum,
  asStr,
  firstStr,
  getLegalReviewTypeLabel,
  getLegalUrgencyLabel,
  getRiskLevelLabel,
} from '../utils/approvalMeta'

defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
}>()
</script>

<template>
  <CTable small bordered responsive class="mb-3">
    <CTableBody>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          검토 분야
        </CTableHeaderCell>
        <CTableDataCell class="ps-3">
          <v-chip color="info" variant="flat" size="x-small" class="me-1">
            {{ getLegalReviewTypeLabel(asStr(content.review_type, 'OTHER')) }}
          </v-chip>
          <v-chip
            :color="
              content.urgency === 'VERY_URGENT'
                ? 'error'
                : content.urgency === 'URGENT'
                  ? 'warning'
                  : 'secondary'
            "
            variant="flat"
            size="x-small"
          >
            {{ getLegalUrgencyLabel(asStr(content.urgency, 'NORMAL')) }}
          </v-chip>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          회신 희망일
        </CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-bold">{{ content.review_due_date || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">의뢰 건명</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3 fw-bold text-body">
          {{ content.case_title || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.counterparty || content.dispute_amount">
        <CTableHeaderCell class="text-center bg-more-light">상대방 / 가액</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3">
          <span v-if="content.counterparty" class="fw-semibold me-3">
            상대방: {{ content.counterparty }}
          </span>
          <span v-if="content.dispute_amount" class="text-danger fw-bold">
            관련 가액: {{ asNum(content.dispute_amount).toLocaleString() }} 원
          </span>
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">사실관계 및 배경</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{
            firstStr(
              content.background,
              content.purpose,
              content.reason,
              content.content,
              content.body,
            ) || '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">주요 쟁점 사항</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{ content.key_issues || '-' }}
        </CTableDataCell>
      </CTableRow>
      <!-- 법무팀 검토 결과 및 종합의견 -->
      <CTableRow v-if="content.legal_opinion || content.risk_level">
        <CTableHeaderCell class="text-center bg-primary bg-opacity-10 text-primary">
          법무 검토 결과
        </CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3 bg-more-light">
          <div class="mb-2">
            <span class="small fw-semibold me-2">법적 리스크 수준:</span>
            <v-chip
              :color="
                content.risk_level === 'HIGH'
                  ? 'error'
                  : content.risk_level === 'MEDIUM'
                    ? 'warning'
                    : 'success'
              "
              variant="flat"
              size="x-small"
            >
              {{ getRiskLevelLabel(asStr(content.risk_level, 'LOW')) }}
            </v-chip>
          </div>
          <div style="white-space: pre-wrap" class="fw-semibold text-body">
            {{ content.legal_opinion || '상세 검토 의견이 등록되지 않았습니다.' }}
          </div>
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.enclosed_docs || content.note">
        <CTableHeaderCell class="text-center bg-more-light">첨부서류 / 비고</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3 text-muted">
          {{ firstStr(content.enclosed_docs, content.note) }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
