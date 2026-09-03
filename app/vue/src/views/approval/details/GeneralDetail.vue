<script setup lang="ts">
import { CTable, CTableBody, CTableRow, CTableHeaderCell, CTableDataCell } from '@coreui/vue'

defineProps<{
  content: Record<string, any>
  document?: any
}>()

const getBudgetAccountLabel = (code?: string) => {
  const map: Record<string, string> = {
    NONE: '예산 비소요 (0원)',
    GENERAL_EXPENSE: '일반관리비 / 경상운영비',
    PROJECT_COST: '사업비 / 현장 직접비',
    OUTSOURCING: '외주 용역비',
    MARKETING: '홍보 및 마케팅비',
    ASSET_PURCHASE: '자산 취득비',
    OTHER: '기타 예산',
  }
  return (code && map[code]) || code || '-'
}
</script>

<template>
  <CTable small bordered responsive class="mb-0">
    <CTableBody>
      <CTableRow v-if="content.purpose">
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          품의 목적
        </CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 fw-bold text-primary">
          {{ content.purpose }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.schedule || content.budget_account">
        <CTableHeaderCell class="text-center bg-more-light">추진 일정</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.schedule || '-' }}</CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          예산 과목
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          {{ getBudgetAccountLabel(content.budget_account) }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.budget !== undefined || content.amount !== undefined">
        <CTableHeaderCell class="text-center bg-more-light">소요 예산</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3">
          <span class="fs-6 fw-bold text-danger">
            {{ (Number(content.budget ?? content.amount) || 0).toLocaleString() }} 원
          </span>
          <span v-if="!content.budget && !content.amount" class="text-muted small ms-2">
            (예산 비소요)
          </span>
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">세부 품의 내용</CTableHeaderCell>
        <CTableDataCell
          colspan="3"
          class="pl-3 py-3"
          style="white-space: pre-wrap; line-height: 1.6"
        >
          {{ content.content || content.body || content.description || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.expected_effect">
        <CTableHeaderCell class="text-center bg-more-light">기대 효과</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{ content.expected_effect }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.note">
        <CTableHeaderCell class="text-center bg-more-light">비고 / 특이사항</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-muted">{{ content.note }}</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
