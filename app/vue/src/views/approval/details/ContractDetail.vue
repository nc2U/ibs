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
          계약 구분
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge color="info" class="me-1">
            {{
              content.contract_type === 'CONSTRUCTION'
                ? '공사 도급/하도급'
                : content.contract_type === 'SERVICE'
                  ? '용역/설계/감리/PM'
                  : content.contract_type === 'PURCHASE'
                    ? '물품공급/자재구매'
                    : content.contract_type === 'LEASE'
                      ? '부동산 임대차'
                      : content.contract_type === 'MOU_NDA'
                        ? 'MOU/NDA'
                        : '일반 계약'
            }}
          </CBadge>
          <CBadge color="secondary">
            {{
              content.contract_kind === 'CHANGE'
                ? '변경 계약'
                : content.contract_kind === 'RENEWAL'
                  ? '갱신 계약'
                  : '신규 계약'
            }}
          </CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          계약 건명
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold text-body">
          {{ content.contract_name || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">계약 상대방</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">
          <span class="fw-bold">{{ content.contractor_name || '-' }}</span>
          <span v-if="content.contractor_ceo" class="text-muted ms-2">
            (대표: {{ content.contractor_ceo }})
          </span>
          <span v-if="content.contractor_reg_number" class="text-muted ms-2">
            | 사업자: {{ content.contractor_reg_number }}
          </span>
          <span v-if="content.contractor_contact" class="text-muted ms-2">
            | 연락처: {{ content.contractor_contact }}
          </span>
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">계약 금액</CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
          {{ (Number(content.contract_amount ?? content.amount) || 0).toLocaleString() }} 원
          <span class="small fw-normal text-muted ms-1">
            ({{
              content.vat_type === 'INCLUDED'
                ? 'VAT 포함'
                : content.vat_type === 'ZERO_TAX'
                  ? '면세'
                  : 'VAT 별도'
            }})
          </span>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">계약 기간</CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-semibold text-primary">
          {{ content.contract_start_date || '-' }} ~
          {{ content.contract_end_date || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.payment_terms">
        <CTableHeaderCell class="text-center bg-more-light">대금 지급 조건</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">{{ content.payment_terms }}</CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.warranty_terms">
        <CTableHeaderCell class="text-center bg-more-light">이행 / 하자보증</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">{{ content.warranty_terms }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">체결 사유 / 배경</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{
            content.purpose_reason ||
            content.purpose ||
            content.reason ||
            content.content ||
            content.body ||
            '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.special_terms || content.note">
        <CTableHeaderCell class="text-center bg-more-light">특약 / 비고</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-muted" style="white-space: pre-wrap">
          {{ content.special_terms || content.note }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
