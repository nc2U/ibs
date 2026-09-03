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
  <div>
    <CTable small bordered responsive class="mb-3">
      <CTableBody>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            출장 구분
          </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            <CBadge color="primary">{{
              content.trip_type === 'OVERSEAS' ? '해외 출장' : '국내 출장'
            }}</CBadge>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            출장지
          </CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-semibold text-primary">
            {{ content.destination || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">출장 기간</CTableHeaderCell>
          <CTableDataCell class="pl-3">
            {{ content.start_date || '-' }} ~ {{ content.end_date || '-' }}
            <CBadge color="info" class="ms-2">
              {{ content.nights_count ?? 0 }}박 {{ content.days_count ?? 1 }}일
            </CBadge>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">교통편</CTableHeaderCell>
          <CTableDataCell class="pl-3">{{ content.transportation || '법인차량' }}</CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">출장 목적</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3 fw-bold">
            {{ content.purpose || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">동행자</CTableHeaderCell>
          <CTableDataCell class="pl-3">{{ content.companion || '-' }}</CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">업무 대행자</CTableHeaderCell>
          <CTableDataCell class="pl-3">{{ content.substitute_worker || '-' }}</CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">비상 연락처</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3">
            {{ content.emergency_contact || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">세부 여비 내역</CTableHeaderCell>
          <CTableDataCell colspan="3" class="p-2">
            <div class="d-flex gap-4 small">
              <span>
                교통비:
                <strong>{{ (Number(content.transport_cost) || 0).toLocaleString() }}</strong> 원
              </span>
              <span>
                숙박비:
                <strong>{{ (Number(content.lodging_cost) || 0).toLocaleString() }}</strong> 원
              </span>
              <span>
                일비/식비:
                <strong>{{ (Number(content.daily_allowance) || 0).toLocaleString() }}</strong> 원
              </span>
              <span>
                기타:
                <strong>{{ (Number(content.other_cost) || 0).toLocaleString() }}</strong> 원
              </span>
            </div>
          </CTableDataCell>
        </CTableRow>
        <CTableRow v-if="content.itinerary">
          <CTableHeaderCell class="text-center bg-more-light">세부 일정 계획</CTableHeaderCell>
          <CTableDataCell
            colspan="3"
            class="pl-3 py-3"
            style="white-space: pre-wrap; line-height: 1.6"
          >
            {{ content.itinerary }}
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>
    <div class="d-flex justify-content-end align-items-center p-2 bg-light border rounded">
      <span class="me-2 fw-semibold">총 예상 출장 여비:</span>
      <span class="fs-5 fw-bold text-danger">
        {{ (Number(content.total_cost ?? content.amount) || 0).toLocaleString() }} 원
      </span>
    </div>
  </div>
</template>
