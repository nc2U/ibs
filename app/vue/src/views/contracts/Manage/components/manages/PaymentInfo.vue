<script lang="ts" setup>
import { type PropType } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import type { Contract } from '@/store/types/contract'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
})
</script>

<template>
  <!-- 금액 정보 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>금액 정보</strong>
    </CCardHeader>
    <CCardBody>
      <div class="mb-3">
        <strong class="d-block mb-2">분양가</strong>
        <div class="display-6 text-primary">
          {{ numFormat(contract.contractprice?.price || 0) }} 원
        </div>
      </div>
      <CRow class="mb-2">
        <CCol :cols="6">
          <small class="text-muted">건물가:</small>
          <div>{{ numFormat(contract.contractprice?.price_build || 0) }}</div>
        </CCol>
        <CCol :cols="6">
          <small class="text-muted">토지가:</small>
          <div>{{ numFormat(contract.contractprice?.price_land || 0) }}</div>
        </CCol>
      </CRow>
      <CRow class="mb-3">
        <CCol :cols="6">
          <small class="text-muted">세금:</small>
          <div>{{ numFormat(contract.contractprice?.price_tax || 0) }}</div>
        </CCol>
      </CRow>
      <hr />
      <CRow class="mb-2">
        <CCol :cols="6">
          <strong>총 납부액:</strong>
        </CCol>
        <CCol :cols="6" class="text-end">
          <strong class="text-success">{{ numFormat(contract.total_paid) }} 원</strong>
        </CCol>
      </CRow>
      <CRow>
        <CCol :cols="6">
          <strong>마지막 납부:</strong>
        </CCol>
        <CCol :cols="6" class="text-end">
          <span>{{ contract.last_paid_order?.__str__ || '-' }}</span>
        </CCol>
      </CRow>
    </CCardBody>
  </CCard>

  <!-- 납부 내역 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>납부 내역</strong>
    </CCardHeader>
    <CCardBody>
      <div v-if="contract.payments && contract.payments.length > 0">
        <CTable small striped hover>
          <CTableHead>
            <CTableRow>
              <CTableHeaderCell>납부일</CTableHeaderCell>
              <CTableHeaderCell>회차</CTableHeaderCell>
              <CTableHeaderCell class="text-end">금액</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow v-for="payment in contract.payments" :key="payment.pk">
              <CTableDataCell>{{ payment.deal_date }}</CTableDataCell>
              <CTableDataCell>{{ payment.installment_order.__str__ }}</CTableDataCell>
              <CTableDataCell class="text-end">
                {{ numFormat(payment.income) }}
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </div>
      <div v-else class="text-center text-muted py-3">납부 내역이 없습니다.</div>
    </CCardBody>
  </CCard>
</template>
