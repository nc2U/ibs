<script lang="ts" setup>
import AddProofDocs from './AddProofDocs.vue'
import AddPledgeDocs from './AddPledgeDocs.vue'
import AddConsultation from './AddConsultation.vue'
</script>

<template>
  <!-- 구비서류 제출 현황 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong>구비서류 제출 현황</strong>
        </div>
      </div>
    </CCardHeader>

    <AddProofDocs />

    <AddPledgeDocs />
  </CCard>

  <!-- 상담 내역 카드 -->
  <AddConsultation />
</template>
