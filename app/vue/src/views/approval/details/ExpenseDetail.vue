<script setup lang="ts">
import {
  CTable,
  CTableHead,
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
  <div>
    <CTable small bordered responsive class="mb-3">
      <CTableBody>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            지출 구분
          </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            <CBadge color="success">{{ content.expense_type || '법인카드' }}</CBadge>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            지급 요청일
          </CTableHeaderCell>
          <CTableDataCell class="pl-3">{{ content.payment_due_date || '-' }}</CTableDataCell>
        </CTableRow>
        <CTableRow v-if="content.bank_name || content.account_number">
          <CTableHeaderCell class="text-center bg-more-light">입금 계좌</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3">
            {{ content.bank_name }} {{ content.account_number }} (예금주:
            {{ content.account_holder }})
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <!-- 품목 내역 그리드 -->
    <div v-if="content.items?.length" class="mb-2">
      <div class="small fw-semibold mb-1">지출 내역 목록</div>
      <CTable small bordered responsive class="mb-0 text-center">
        <CTableHead color="light">
          <CTableRow>
            <CTableHeaderCell style="width: 120px">일자</CTableHeaderCell>
            <CTableHeaderCell>사용 내역 / 항목명</CTableHeaderCell>
            <CTableHeaderCell style="width: 140px">금액 (원)</CTableHeaderCell>
            <CTableHeaderCell style="width: 150px">비고</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow v-for="(item, idx) in content.items" :key="idx">
            <CTableDataCell>{{ item.date }}</CTableDataCell>
            <CTableDataCell class="text-start">{{ item.description }}</CTableDataCell>
            <CTableDataCell class="text-end fw-semibold">
              {{ (Number(item.amount) || 0).toLocaleString() }}
            </CTableDataCell>
            <CTableDataCell class="text-start text-muted">{{ item.note || '-' }}</CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </div>

    <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded">
      <span class="me-2 fw-semibold">총 지출 결의 금액:</span>
      <span class="fs-5 fw-bold text-danger">
        {{ (Number(content.amount) || 0).toLocaleString() }} 원
      </span>
    </div>
  </div>
</template>
