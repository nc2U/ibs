<script setup lang="ts">
import { computed } from 'vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import { asList, asStr, getAppointmentTypeLabel } from '../utils/approvalMeta'

interface AppointmentTargetDetail {
  name?: string
  current_dept?: string
  current_position?: string
  new_dept?: string
  new_position?: string
  type_desc?: string
  note?: string
}

const props = defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
}>()

const targets = computed(() => asList<AppointmentTargetDetail>(props.content.targets))
</script>

<template>
  <div>
    <CTable small bordered responsive class="mb-3">
      <CTableBody>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            발령 구분
          </CTableHeaderCell>
          <CTableDataCell class="ps-3">
            <v-chip color="info" variant="flat" size="x-small">
              {{ getAppointmentTypeLabel(asStr(content.appointment_type, 'PROMOTION')) }}
            </v-chip>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            발령 시행일
          </CTableHeaderCell>
          <CTableDataCell class="ps-3 fw-bold text-danger">
            {{ content.effective_date || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">발령 사유/배경</CTableHeaderCell>
          <CTableDataCell
            colspan="3"
            class="ps-3 py-2"
            style="white-space: pre-wrap; line-height: 1.6"
          >
            {{ content.reason || '-' }}
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <div v-if="targets.length" class="mb-3">
      <h6 class="fw-bold mb-2 small text-primary">
        <v-icon icon="mdi-account-group" class="me-1" />
        발령 대상자 세부 내역 (총 {{ targets.length }}명)
      </h6>
      <CTable small bordered responsive hover class="text-center mb-0 align-middle">
        <CTableHead class="bg-more-light small">
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
          <CTableRow v-for="(t, idx) in targets" :key="idx">
            <CTableDataCell class="text-muted">{{ idx + 1 }}</CTableDataCell>
            <CTableDataCell class="fw-bold">{{ t.name || '-' }}</CTableDataCell>
            <CTableDataCell class="text-muted">
              {{ t.current_dept || '-' }} / {{ t.current_position || '-' }}
            </CTableDataCell>
            <CTableDataCell class="fw-semibold text-primary">
              {{ t.new_dept || '-' }} / {{ t.new_position || '-' }}
            </CTableDataCell>
            <CTableDataCell>
              <v-chip color="info" variant="flat" size="x-small">
                {{ t.type_desc || '발령' }}
              </v-chip>
            </CTableDataCell>
            <CTableDataCell class="text-start">{{ t.note || '-' }}</CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </div>

    <div v-if="content.note" class="p-2 bg-more-light border rounded small text-muted">
      <strong>비고 / 특이사항:</strong> {{ content.note }}
    </div>
  </div>
</template>
