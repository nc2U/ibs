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
import CIcon from '@coreui/icons-vue'

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
            발령 구분
          </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            <CBadge color="primary">{{ content.appointment_type || '승진/전보' }}</CBadge>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            발령 시행일
          </CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-bold text-danger">
            {{ content.effective_date || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light"> 발령 사유/배경 </CTableHeaderCell>
          <CTableDataCell
            colspan="3"
            class="pl-3 py-2"
            style="white-space: pre-wrap; line-height: 1.6"
          >
            {{ content.reason || '-' }}
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <div v-if="content.targets?.length" class="mb-3">
      <h6 class="fw-bold mb-2 small text-primary">
        <CIcon name="cilPeople" class="me-1" />
        발령 대상자 세부 내역 (총 {{ content.targets.length }}명)
      </h6>
      <CTable small bordered responsive hover class="text-center mb-0 align-middle">
        <CTableHead class="table-light small">
          <CTableRow>
            <CTableHeaderCell style="width: 40px">#</CTableHeaderCell>
            <CTableHeaderCell style="width: 90px">성명</CTableHeaderCell>
            <CTableHeaderCell>현 소속 / 직급</CTableHeaderCell>
            <CTableHeaderCell class="text-primary">발령 소속 / 직급</CTableHeaderCell>
            <CTableHeaderCell style="width: 110px">발령 구분</CTableHeaderCell>
            <CTableHeaderCell>비고</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody class="small">
          <CTableRow v-for="(t, idx) in content.targets" :key="idx">
            <CTableDataCell class="text-muted">{{ Number(idx) + 1 }}</CTableDataCell>
            <CTableDataCell class="fw-bold">{{ t.name }}</CTableDataCell>
            <CTableDataCell class="text-muted">
              {{ t.current_dept || '-' }} / {{ t.current_position || '-' }}
            </CTableDataCell>
            <CTableDataCell class="fw-semibold text-primary">
              {{ t.new_dept || '-' }} / {{ t.new_position || '-' }}
            </CTableDataCell>
            <CTableDataCell>
              <CBadge color="info">{{ t.type_desc || '발령' }}</CBadge>
            </CTableDataCell>
            <CTableDataCell class="text-start">{{ t.note || '-' }}</CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </div>

    <div v-if="content.note" class="p-2 bg-light border rounded small text-muted">
      <strong>비고 / 특이사항:</strong> {{ content.note }}
    </div>
  </div>
</template>
