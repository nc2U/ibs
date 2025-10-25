<script lang="ts" setup>
import { ref } from 'vue'
import AddProofDocs from './AddProofDocs.vue'
import AddPledgeDocs from './AddPledgeDocs.vue'
import AddConsultation from './AddConsultation.vue'

// 토글 상태
const isProofDocsExpanded = ref(true)
const isConsultationExpanded = ref(true)
</script>

<template>
  <!-- 구비서류 제출 현황 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong>구비서류 제출 현황</strong>
        </div>
        <v-btn
          size="x-small"
          :icon="isProofDocsExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down'"
          variant="text"
          @click="isProofDocsExpanded = !isProofDocsExpanded"
        />
      </div>
    </CCardHeader>

    <CCollapse :visible="isProofDocsExpanded">
      <!-- 탭 -->
      <AddProofDocs />

      <AddPledgeDocs />
    </CCollapse>
  </CCard>

  <!-- 상담 내역 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong>상담 내역</strong>
        </div>
        <v-btn
          size="x-small"
          :icon="isConsultationExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down'"
          variant="text"
          @click="isConsultationExpanded = !isConsultationExpanded"
        />
      </div>
    </CCardHeader>
    <CCollapse :visible="isConsultationExpanded">
      <AddConsultation />
    </CCollapse>
  </CCard>
</template>
