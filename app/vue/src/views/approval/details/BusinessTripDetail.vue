<script setup lang="ts">
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import {
  asNum,
  asStr,
  getTransportMethodLabel,
  getTripTypeLabel,
} from '../utils/approvalMeta'

defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
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
          <CTableDataCell class="ps-3">
            <v-chip color="info" variant="flat" size="x-small">
              {{ getTripTypeLabel(asStr(content.trip_type, 'DOMESTIC')) }}
            </v-chip>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            출장지
          </CTableHeaderCell>
          <CTableDataCell class="ps-3 fw-semibold text-primary">
            {{ content.destination || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">출장 기간</CTableHeaderCell>
          <CTableDataCell class="ps-3">
            {{ content.start_date || '-' }} ~ {{ content.end_date || '-' }}
            <v-chip color="info" variant="flat" size="x-small" class="ms-2">
              {{ content.nights_count ?? 0 }}박 {{ content.days_count ?? 1 }}일
            </v-chip>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">교통편</CTableHeaderCell>
          <CTableDataCell class="ps-3">
            {{ getTransportMethodLabel(asStr(content.transportation, 'CORP_CAR')) }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">출장 목적</CTableHeaderCell>
          <CTableDataCell colspan="3" class="ps-3 fw-bold">
            {{ content.purpose || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">동행자</CTableHeaderCell>
          <CTableDataCell class="ps-3">{{ content.companion || '-' }}</CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">업무 대행자</CTableHeaderCell>
          <CTableDataCell class="ps-3">{{ content.substitute_worker || '-' }}</CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">비상 연락처</CTableHeaderCell>
          <CTableDataCell colspan="3" class="ps-3">
            {{ content.emergency_contact || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">세부 여비 내역</CTableHeaderCell>
          <CTableDataCell colspan="3" class="p-2">
            <div class="d-flex gap-4 small">
              <span>
                교통비:
                <strong>{{ asNum(content.transport_cost).toLocaleString() }}</strong> 원
              </span>
              <span>
                숙박비:
                <strong>{{ asNum(content.lodging_cost).toLocaleString() }}</strong> 원
              </span>
              <span>
                일비/식비:
                <strong>{{ asNum(content.daily_allowance).toLocaleString() }}</strong> 원
              </span>
              <span>
                기타:
                <strong>{{ asNum(content.other_cost).toLocaleString() }}</strong> 원
              </span>
            </div>
          </CTableDataCell>
        </CTableRow>
        <CTableRow v-if="content.itinerary">
          <CTableHeaderCell class="text-center bg-more-light">세부 일정 계획</CTableHeaderCell>
          <CTableDataCell
            colspan="3"
            class="ps-3 py-3"
            style="white-space: pre-wrap; line-height: 1.6"
          >
            {{ content.itinerary }}
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>
    <div class="d-flex justify-content-end align-items-center p-2 bg-more-light border rounded">
      <span class="me-2 fw-semibold">총 예상 출장 여비:</span>
      <span class="fs-5 fw-bold text-danger">
        {{ asNum(content.total_cost ?? content.amount).toLocaleString() }} 원
      </span>
    </div>
  </div>
</template>
