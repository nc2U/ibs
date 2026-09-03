<script setup lang="ts">
import {
  CTable,
  CTableHead,
  CTableBody,
  CTableRow,
  CTableHeaderCell,
  CTableDataCell,
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
            구매 목적
          </CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3">{{ content.purpose || '-' }}</CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">납품 희망일</CTableHeaderCell>
          <CTableDataCell class="pl-3">{{ content.delivery_due_date || '-' }}</CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            납품 장소
          </CTableHeaderCell>
          <CTableDataCell class="pl-3">{{ content.delivery_location || '-' }}</CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <!-- 품목 내역 그리드 -->
    <div v-if="content.items?.length" class="mb-2">
      <div class="small fw-semibold mb-1">구매 품목 내역</div>
      <CTable small bordered responsive class="mb-0 text-center">
        <CTableHead color="light">
          <CTableRow>
            <CTableHeaderCell>품명</CTableHeaderCell>
            <CTableHeaderCell style="width: 120px">규격</CTableHeaderCell>
            <CTableHeaderCell style="width: 70px">수량</CTableHeaderCell>
            <CTableHeaderCell style="width: 110px">단가</CTableHeaderCell>
            <CTableHeaderCell style="width: 120px">공급가액</CTableHeaderCell>
            <CTableHeaderCell style="width: 100px">부가세</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow v-for="(item, idx) in content.items" :key="idx">
            <CTableDataCell class="text-start">{{ item.name }}</CTableDataCell>
            <CTableDataCell>{{ item.spec || '-' }}</CTableDataCell>
            <CTableDataCell>{{ item.quantity }}</CTableDataCell>
            <CTableDataCell class="text-end">
              {{ (Number(item.unit_price) || 0).toLocaleString() }}
            </CTableDataCell>
            <CTableDataCell class="text-end fw-semibold">
              {{ (Number(item.supply_price) || 0).toLocaleString() }}
            </CTableDataCell>
            <CTableDataCell class="text-end text-muted">
              {{ (Number(item.vat) || 0).toLocaleString() }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </div>

    <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded">
      <span class="me-2 fw-semibold">총 구매 품의 금액:</span>
      <span class="fs-5 fw-bold text-danger">
        {{ (Number(content.amount) || 0).toLocaleString() }} 원
      </span>
    </div>
  </div>
</template>
