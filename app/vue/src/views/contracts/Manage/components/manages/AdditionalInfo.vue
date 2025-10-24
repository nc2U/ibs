<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Contract } from '@/store/types/contract'
import { useContract } from '@/store/pinia/contract.ts'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
})

const contStore = useContract()
const requiredDocsList = computed(() => contStore.requiredDocsList)
</script>

<template>
  <!-- 구비서류 제출 현황 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>구비서류 제출 현황</strong>
    </CCardHeader>
    <CCardBody>
      <CTable>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>해당서류</CTableHeaderCell>
            <CTableHeaderCell>필요수량</CTableHeaderCell>
            <CTableHeaderCell>필수여부</CTableHeaderCell>
            <CTableHeaderCell>제출여부</CTableHeaderCell>
            <CTableHeaderCell>파일</CTableHeaderCell>
            <CTableHeaderCell>관리</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow v-for="doc in requiredDocsList" :key="doc.pk">
            <CTableDataCell>
              {{ doc.document_name }}
              <v-tooltip>{{ doc.description }}</v-tooltip>
            </CTableDataCell>
            <CTableDataCell class="text-center">{{ doc.quantity }}</CTableDataCell>
            <CTableDataCell>{{ doc.required }}</CTableDataCell>
            <CTableDataCell class="text-center">완료</CTableDataCell>
            <CTableDataCell class="text-center">
              <v-icon v-if="1 == 1" icon="mdi-download-box" color="primary" size="18" />
              <v-icon v-else icon="mdi-download-box-outline" color="grey" size="18" />
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <v-icon icon="mdi-pencil" color="warning" size="16" />
              <v-icon icon="mdi-trash-can" color="grey" size="16" />
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCardBody>
  </CCard>

  <!-- 상담 내역 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>상담 내역</strong>
    </CCardHeader>
    <CCardBody>
      <div class="text-center text-muted py-3">
        <v-icon icon="mdi-message-text-outline" size="large" class="mb-2" />
        <div>상담 내역이 없습니다.</div>
      </div>
    </CCardBody>
  </CCard>
</template>
