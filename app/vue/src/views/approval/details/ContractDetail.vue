<script setup lang="ts">
import { CTable } from '@coreui/vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import {
  asNum,
  asStr,
  firstStr,
  getContractKindLabel,
  getContractTypeLabel,
  getVatTypeLabel,
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
          계약 구분
        </CTableHeaderCell>
        <CTableDataCell class="ps-3">
          <v-chip color="info" variant="flat" size="x-small" class="me-1">
            {{ getContractTypeLabel(asStr(content.contract_type, 'OTHER')) }}
          </v-chip>
          <v-chip color="secondary" variant="flat" size="x-small">
            {{ getContractKindLabel(asStr(content.contract_kind, 'NEW')) }}
          </v-chip>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          계약 건명
        </CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-bold text-body">
          {{ content.contract_name || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">계약 상대방</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3">
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
        <CTableDataCell class="ps-3 fw-bold text-danger fs-6">
          {{ asNum(content.contract_amount ?? content.amount).toLocaleString() }} 원
          <span class="small fw-normal text-muted ms-1">
            ({{ getVatTypeLabel(asStr(content.vat_type, 'EXCLUDED')) }})
          </span>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">계약 기간</CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-semibold text-primary">
          {{ content.contract_start_date || '-' }} ~
          {{ content.contract_end_date || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.payment_terms">
        <CTableHeaderCell class="text-center bg-more-light">대금 지급 조건</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3">{{ content.payment_terms }}</CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.warranty_terms">
        <CTableHeaderCell class="text-center bg-more-light">이행 / 하자보증</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3">{{ content.warranty_terms }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">체결 사유 / 배경</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{
            firstStr(
              content.purpose_reason,
              content.purpose,
              content.reason,
              content.content,
              content.body,
            ) || '-'
          }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.special_terms || content.note">
        <CTableHeaderCell class="text-center bg-more-light">특약 / 비고</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3 text-muted" style="white-space: pre-wrap">
          {{ firstStr(content.special_terms, content.note) }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
