<script setup lang="ts">
import { computed } from 'vue'
import { CTable } from '@coreui/vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import { TableSecondary } from '@/utils/cssMixins'
import { asList, asNum, asStr, getSettlementTypeLabel } from '../utils/approvalMeta'

interface SettlementItemDetail {
  date?: string
  merchant?: string
  category?: string
  amount?: number | string
  purpose?: string
}

const props = defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
}>()

const items = computed(() => asList<SettlementItemDetail>(props.content.items))
</script>

<template>
  <div>
    <CTable small bordered responsive class="mb-3">
      <CTableBody>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            정산 구분
          </CTableHeaderCell>
          <CTableDataCell class="ps-3">
            <v-chip color="info" variant="flat" size="x-small">
              {{ getSettlementTypeLabel(asStr(content.settlement_type, 'CORP_CARD')) }}
            </v-chip>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
            귀속 연월
          </CTableHeaderCell>
          <CTableDataCell class="ps-3 fw-bold">{{ content.target_month || '-' }}</CTableDataCell>
        </CTableRow>
        <CTableRow v-if="content.card_number">
          <CTableHeaderCell class="text-center bg-more-light">법인카드 정보</CTableHeaderCell>
          <CTableDataCell colspan="3" class="ps-3">{{ content.card_number }}</CTableDataCell>
        </CTableRow>
        <CTableRow v-else-if="content.bank_name || content.account_number">
          <CTableHeaderCell class="text-center bg-more-light">환급 계좌</CTableHeaderCell>
          <CTableDataCell colspan="3" class="ps-3">
            {{ content.bank_name }} {{ content.account_number }} (예금주:
            {{ content.account_holder || '-' }})
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">정산 개요/사유</CTableHeaderCell>
          <CTableDataCell colspan="3" class="ps-3">{{ content.reason || '-' }}</CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>

    <!-- 영수증 세부 내역 그리드 -->
    <div v-if="items.length" class="mb-2">
      <div class="small fw-semibold mb-1 text-primary">
        영수증 / 세부 사용 내역 (총 {{ items.length }}건)
      </div>
      <CTable small bordered responsive class="mb-0 text-center align-middle">
        <CTableHead :color="TableSecondary">
          <CTableRow class="small">
            <CTableHeaderCell style="width: 110px">사용일자</CTableHeaderCell>
            <CTableHeaderCell style="width: 150px">계정과목</CTableHeaderCell>
            <CTableHeaderCell style="width: 160px">가맹점</CTableHeaderCell>
            <CTableHeaderCell style="width: 130px">금액 (원)</CTableHeaderCell>
            <CTableHeaderCell>사용 목적 / 참석자</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody class="small">
          <CTableRow v-for="(item, idx) in items" :key="idx">
            <CTableDataCell>{{ item.date || '-' }}</CTableDataCell>
            <CTableDataCell>
              <v-chip color="secondary" variant="flat" size="x-small">
                {{ item.category || '-' }}
              </v-chip>
            </CTableDataCell>
            <CTableDataCell class="text-start fw-semibold">
              {{ item.merchant || '-' }}
            </CTableDataCell>
            <CTableDataCell class="text-end fw-bold text-body">
              {{ asNum(item.amount).toLocaleString() }}
            </CTableDataCell>
            <CTableDataCell class="text-start">{{ item.purpose || '-' }}</CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </div>

    <div
      class="d-flex justify-content-end align-items-center p-2 bg-more-light border rounded mb-2"
    >
      <span class="me-2 fw-semibold">총 정산 합계 금액:</span>
      <span class="fs-5 fw-bold text-danger">
        {{ asNum(content.total_amount ?? content.amount).toLocaleString() }} 원
      </span>
    </div>

    <div v-if="content.note" class="p-2 bg-more-light border rounded small text-muted">
      <strong>비고 / 증빙 안내:</strong> {{ content.note }}
    </div>
  </div>
</template>
