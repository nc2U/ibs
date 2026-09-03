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
          변경/해지 구분
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge :color="content.change_type === 'TERMINATION' ? 'danger' : 'warning'">
            {{
              content.change_type === 'TERMINATION'
                ? '계약 해지 / 합의 해제'
                : content.change_type === 'AMOUNT_CHANGE'
                  ? '금액 변경(증감)'
                  : content.change_type === 'PERIOD_CHANGE'
                    ? '기간 변경(연장)'
                    : content.change_type === 'SCOPE_CHANGE'
                      ? '과업/조건 변경'
                      : '복합 변경 (금액+기간)'
            }}
          </CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          계약 상대방
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold">{{ content.contractor_name || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">원 계약 건명</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">
          <span class="fw-bold">{{ content.original_contract_name || '-' }}</span>
          <span v-if="content.original_contract_no" class="text-muted ms-2">
            (계약번호: {{ content.original_contract_no }})
          </span>
          <span v-if="content.original_contract_date" class="text-muted ms-2">
            | 체결일: {{ content.original_contract_date }}
          </span>
        </CTableDataCell>
      </CTableRow>
      <!-- 변경 비교 (비 해지 시) -->
      <template v-if="content.change_type !== 'TERMINATION'">
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">원 계약 금액</CTableHeaderCell>
          <CTableDataCell class="pl-3">
            {{ (Number(content.original_amount) || 0).toLocaleString() }} 원
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">증감 금액</CTableHeaderCell>
          <CTableDataCell
            class="pl-3 fw-bold"
            :class="(Number(content.change_amount) || 0) >= 0 ? 'text-danger' : 'text-primary'"
          >
            {{ (Number(content.change_amount) || 0) >= 0 ? '+' : ''
            }}{{ (Number(content.change_amount) || 0).toLocaleString() }} 원
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">최종 변경 금액</CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
            {{
              (
                Number(
                  content.final_amount ??
                    Number(content.original_amount || 0) + Number(content.change_amount || 0),
                ) || 0
              ).toLocaleString()
            }}
            원
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">변경 후 종료일</CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-semibold text-primary">
            {{ content.final_end_date || '-' }}
            <span v-if="content.period_change_desc" class="small text-muted ms-1">
              ({{ content.period_change_desc }})
            </span>
          </CTableDataCell>
        </CTableRow>
      </template>
      <!-- 해지 시 -->
      <template v-else>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">해지 기준일</CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-bold text-danger">
            {{ content.termination_date || '-' }}
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">타절 정산금액</CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
            {{ (Number(content.settlement_amount) || 0).toLocaleString() }} 원
          </CTableDataCell>
        </CTableRow>
        <CTableRow v-if="content.penalty_terms">
          <CTableHeaderCell class="text-center bg-more-light">위약 / 보증몰취</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3 text-danger">
            {{ content.penalty_terms }}
          </CTableDataCell>
        </CTableRow>
      </template>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">변경 / 해지 사유</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{
            content.change_reason ||
            content.purpose ||
            content.reason ||
            content.content ||
            content.body ||
            '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.subsequent_plan || content.note">
        <CTableHeaderCell class="text-center bg-more-light">후속 대책 / 비고</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-muted" style="white-space: pre-wrap">
          {{ content.subsequent_plan || content.note }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
