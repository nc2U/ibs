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
          근무 구분
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge
            :color="
              content.work_type === 'HOLIDAY'
                ? 'danger'
                : content.work_type === 'NIGHT'
                  ? 'dark'
                  : 'primary'
            "
          >
            {{
              content.work_type === 'HOLIDAY'
                ? '휴일 근무'
                : content.work_type === 'NIGHT'
                  ? '야간 근무'
                  : '평일 연장근무'
            }}
          </CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          근무 일자
        </CTableHeaderCell>
        <CTableDataCell class="pl-3 fw-semibold">{{ content.work_date || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">근무 시간</CTableHeaderCell>
        <CTableDataCell class="pl-3">
          {{ content.start_time || '-' }} ~ {{ content.end_time || '-' }}
          <span v-if="content.break_hours" class="text-muted small ms-2">
            (휴게: {{ content.break_hours }}시간)
          </span>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">인정 시간</CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <span class="fs-6 fw-bold text-primary">{{ content.total_hours ?? 0 }} 시간</span>
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">보상 방식</CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge color="info">
            {{
              content.compensation_type === 'COMP_LEAVE' ? '대체휴무 (보상휴가) 적립' : '수당 지급'
            }}
          </CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">동반 근무자</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.co_workers || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">근무 사유 / 업무</CTableHeaderCell>
        <CTableDataCell
          colspan="3"
          class="pl-3 py-3"
          style="white-space: pre-wrap; line-height: 1.6"
        >
          {{ content.reason || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.note">
        <CTableHeaderCell class="text-center bg-more-light">비고 / 특이사항</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-muted">{{ content.note }}</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
