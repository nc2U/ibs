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
  <CTable small bordered responsive class="mb-0">
    <CTableBody>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          휴가 구분
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge color="primary">{{ content.leave_type || '연차' }}</CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          신청 일수
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-bold text-primary">
          {{ content.days_count ?? 1 }} 일
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">휴가 기간</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">
          {{ content.start_date }} ~ {{ content.end_date || content.start_date }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">휴가 사유</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{ content.reason || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">업무 대행자</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.substitute_worker || '-' }}</CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">비상 연락처</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.emergency_contact || '-' }}</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
