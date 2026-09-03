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
          검토 분야
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge color="primary" class="me-1">
            {{
              content.review_type === 'CONTRACT_REVIEW'
                ? '계약서/협약서 검토'
                : content.review_type === 'LITIGATION_DISPUTE'
                  ? '소송/분쟁 대응'
                  : content.review_type === 'REGULATORY_COMPLIANCE'
                    ? '법령해석/인허가'
                    : content.review_type === 'INTERNAL_RULE'
                      ? '사규/내부규정'
                      : content.review_type === 'CLAIM_NOTICE'
                        ? '내용증명/공문'
                        : '법률 자문'
            }}
          </CBadge>
          <CBadge
            :color="
              content.urgency === 'VERY_URGENT'
                ? 'danger'
                : content.urgency === 'URGENT'
                  ? 'warning'
                  : 'secondary'
            "
          >
            {{
              content.urgency === 'VERY_URGENT'
                ? '당일 긴급'
                : content.urgency === 'URGENT'
                  ? '긴급(1~2일)'
                  : '보통'
            }}
          </CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          회신 희망일
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold">{{ content.review_due_date || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">의뢰 건명</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 fw-bold text-body">
          {{ content.case_title || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.counterparty || content.dispute_amount">
        <CTableHeaderCell class="text-center bg-more-light">상대방 / 가액</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">
          <span v-if="content.counterparty" class="fw-semibold me-3">
            상대방: {{ content.counterparty }}
          </span>
          <span v-if="content.dispute_amount" class="text-danger fw-bold">
            관련 가액: {{ (Number(content.dispute_amount) || 0).toLocaleString() }} 원
          </span>
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">사실관계 및 배경</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{
            content.background ||
            content.purpose ||
            content.reason ||
            content.content ||
            content.body ||
            '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">주요 쟁점 사항</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{ content.key_issues || '-' }}
        </CTableDataCell>
      </CTableRow>
      <!-- 법무팀 검토 결과 및 종합의견 -->
      <CTableRow v-if="content.legal_opinion || content.risk_level">
        <CTableHeaderCell class="text-center bg-primary bg-opacity-10 text-primary">
          법무 검토 결과
        </CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 bg-light">
          <div class="mb-2">
            <span class="small fw-semibold me-2">법적 리스크 수준:</span>
            <CBadge
              :color="
                content.risk_level === 'HIGH'
                  ? 'danger'
                  : content.risk_level === 'MEDIUM'
                    ? 'warning'
                    : 'success'
              "
            >
              {{
                content.risk_level === 'HIGH'
                  ? '높음 (중대 불리조항)'
                  : content.risk_level === 'MEDIUM'
                    ? '중간 (수정 권고)'
                    : '낮음 (체결 가능)'
              }}
            </CBadge>
          </div>
          <div style="white-space: pre-wrap" class="fw-semibold text-body">
            {{ content.legal_opinion || '상세 검토 의견이 등록되지 않았습니다.' }}
          </div>
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.enclosed_docs || content.note">
        <CTableHeaderCell class="text-center bg-more-light">첨부서류 / 비고</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-muted">
          {{ content.enclosed_docs || content.note }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
