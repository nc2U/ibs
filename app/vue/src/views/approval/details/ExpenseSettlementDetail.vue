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
            정산 구분
          </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            <CBadge color="primary">{{
              content.settlement_type === 'PERSONAL_EXPENSE'
                ? '개인경비 실비환급'
                : content.settlement_type === 'BUSINESS_TRIP'
                  ? '출장경비 정산'
                  : content.settlement_type === 'ADVANCE_PAY'
                    ? '가지급금 정산'
                    : '법인카드 사용정산'
            }}</CBadge>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            귀속 연월
          </CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-bold">{{ content.target_month || '-' }}</CTableDataCell>
        </CTableRow>
        <CTableRow v-if="content.card_number">
          <CTableHeaderCell class="text-center bg-more-light">법인카드 정보</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3">{{ content.card_number }}</CTableDataCell>
        </CTableRow>
        <CTableRow v-else-if="content.bank_name || content.account_number">
          <CTableHeaderCell class="text-center bg-more-light">환급 계좌</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3">
            {{ content.bank_name }} {{ content.account_number }} (예금주:
            {{ content.account_holder || '-' }})
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">정산 개요/사유</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3">{{ content.reason || '-' }}</CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <!-- 영수증 세부 내역 그리드 -->
    <div v-if="content.items?.length" class="mb-2">
      <div class="small fw-semibold mb-1 text-primary">
        영수증 / 세부 사용 내역 (총 {{ content.items.length }}건)
      </div>
      <CTable small bordered responsive class="mb-0 text-center align-middle">
        <CTableHead color="light">
          <CTableRow class="small">
            <CTableHeaderCell style="width: 110px">사용일자</CTableHeaderCell>
            <CTableHeaderCell style="width: 150px">계정과목</CTableHeaderCell>
            <CTableHeaderCell style="width: 160px">가맹점</CTableHeaderCell>
            <CTableHeaderCell style="width: 130px">금액 (원)</CTableHeaderCell>
            <CTableHeaderCell>사용 목적 / 참석자</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody class="small">
          <CTableRow v-for="(item, idx) in content.items" :key="idx">
            <CTableDataCell>{{ item.date }}</CTableDataCell>
            <CTableDataCell>
              <CBadge color="secondary">{{ item.category }}</CBadge>
            </CTableDataCell>
            <CTableDataCell class="text-start fw-semibold">{{ item.merchant }}</CTableDataCell>
            <CTableDataCell class="text-end fw-bold text-body">
              {{ (Number(item.amount) || 0).toLocaleString() }}
            </CTableDataCell>
            <CTableDataCell class="text-start">{{ item.purpose || '-' }}</CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </div>

    <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded mb-2">
      <span class="me-2 fw-semibold">총 정산 합계 금액:</span>
      <span class="fs-5 fw-bold text-danger">
        {{ (Number(content.total_amount ?? content.amount) || 0).toLocaleString() }} 원
      </span>
    </div>

    <div v-if="content.note" class="p-2 bg-light border rounded small text-muted">
      <strong>비고 / 증빙 안내:</strong> {{ content.note }}
    </div>
  </div>
</template>
