<script setup lang="ts">
import { computed } from 'vue'
import {
  CTable,
  CTableHead,
  CTableBody,
  CTableRow,
  CTableHeaderCell,
  CTableDataCell,
} from '@coreui/vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import { TableSecondary } from '@/utils/cssMixins'
import { asList, asNum } from '../utils/approvalMeta'

interface PurchaseItemDetail {
  name?: string
  spec?: string
  quantity?: number | string
  unit_price?: number | string
  supply_price?: number | string
  vat?: number | string
}

const props = defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
}>()

const items = computed(() => asList<PurchaseItemDetail>(props.content.items))
</script>

<template>
  <div>
    <CTable small bordered responsive class="mb-3">
      <CTableBody>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            구매 목적
          </CTableHeaderCell>
          <CTableDataCell colspan="3" class="ps-3">{{ content.purpose || '-' }}</CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">납품 희망일</CTableHeaderCell>
          <CTableDataCell class="ps-3">{{ content.delivery_due_date || '-' }}</CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            납품 장소
          </CTableHeaderCell>
          <CTableDataCell class="ps-3">{{ content.delivery_location || '-' }}</CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <!-- 품목 내역 그리드 -->
    <div v-if="items.length" class="mb-2">
      <div class="small fw-semibold mb-1">구매 품목 내역</div>
      <CTable small bordered responsive class="mb-0 text-center">
        <CTableHead :color="TableSecondary">
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
          <CTableRow v-for="(item, idx) in items" :key="idx">
            <CTableDataCell class="text-start">{{ item.name || '-' }}</CTableDataCell>
            <CTableDataCell>{{ item.spec || '-' }}</CTableDataCell>
            <CTableDataCell>{{ asNum(item.quantity) }}</CTableDataCell>
            <CTableDataCell class="text-end">
              {{ asNum(item.unit_price).toLocaleString() }}
            </CTableDataCell>
            <CTableDataCell class="text-end fw-semibold">
              {{ asNum(item.supply_price).toLocaleString() }}
            </CTableDataCell>
            <CTableDataCell class="text-end text-muted">
              {{ asNum(item.vat).toLocaleString() }}
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </div>

    <div class="d-flex justify-content-end align-items-center p-2 bg-more-light border rounded">
      <span class="me-2 fw-semibold">총 구매 품의 금액:</span>
      <span class="fs-5 fw-bold text-danger">
        {{ asNum(content.amount).toLocaleString() }} 원
      </span>
    </div>
  </div>
</template>
