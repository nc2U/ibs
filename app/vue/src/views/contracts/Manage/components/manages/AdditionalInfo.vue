<script lang="ts" setup>
import { ref } from 'vue'
import AddProofDocs from './AddProofDocs.vue'
import AddPledgeDocs from './AddPledgeDocs.vue'
import AddConsultation from './AddConsultation.vue'

// 토글 상태
const isProofDocsExpanded = ref(true)
const isConsultationExpanded = ref(true)

// 서류 탭 상태
const activeDocTab = ref<'proof' | 'pledge'>('proof')
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
      <CCardBody class="pt-2 pb-0">
        <v-tabs v-model="activeDocTab" color="primary">
          <v-tab value="proof">증명서류</v-tab>
          <v-tab value="pledge">동의서류</v-tab>
        </v-tabs>
      </CCardBody>

      <!-- 탭 컨텐츠 -->
      <v-window v-model="activeDocTab">
        <v-window-item value="proof">
          <AddProofDocs sort-filter="proof" />
        </v-window-item>
        <v-window-item value="pledge">
          <AddPledgeDocs sort-filter="pledge" />
        </v-window-item>
      </v-window>
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
