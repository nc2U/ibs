<script setup lang="ts">
import {
  CTable,
  CTableBody,
  CTableRow,
  CTableHeaderCell,
  CTableDataCell,
  CBadge,
} from '@coreui/vue'
import CIcon from '@coreui/icons-vue'

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
          신청 구분
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge color="danger">
            {{
              content.advance_type === 'PREPAYMENT'
                ? '선급금 (계약상 대금 선지급)'
                : content.advance_type === 'IMPREST_FUND'
                  ? '전도금 (상비 운영비)'
                  : content.advance_type === 'EVENT_FUND'
                    ? '행사/프로젝트 진행비'
                    : '가지급금 (업무용 선지급)'
            }}
          </CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          지급 요청일
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold">
          {{ content.payment_due_date || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">신청 금액</CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold text-danger fs-6">
          {{ (Number(content.advance_amount ?? content.amount) || 0).toLocaleString() }} 원
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">정산 예정일</CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-semibold text-primary">
          {{ content.settlement_due_date || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.bank_name || content.account_number">
        <CTableHeaderCell class="text-center bg-more-light">입금(수령) 계좌</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">
          <span class="badge bg-light text-body me-2">
            {{ content.receiver_type === 'VENDOR' ? '거래처 지급' : '임직원 계좌' }}
          </span>
          {{ content.bank_name }} {{ content.account_number }} (예금주:
          {{ content.account_holder || '-' }})
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">사용 목적 / 계획</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{ content.purpose || content.reason || content.content || content.body || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.settlement_promise !== false">
        <CTableHeaderCell class="text-center bg-more-light">정산 확약</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-success fw-semibold">
          <CIcon name="cilCheckCircle" class="me-1" />
          상기 선급금/가지급금을 수령한 후, 정산 예정일까지 적격 증빙을 첨부하여 전액 정산할 것을
          확약함
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.note">
        <CTableHeaderCell class="text-center bg-more-light">비고 / 특이사항</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-muted">{{ content.note }}</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
