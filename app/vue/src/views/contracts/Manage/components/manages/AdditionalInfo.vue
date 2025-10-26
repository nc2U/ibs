<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue'
import AddRequiredDocs from './AddRequiredDocs.vue'
import AddConsultation from './AddConsultation.vue'

// 로컬 스토리지 키
const PROOF_DOCS_EXPANDED_KEY = 'contract_proof_docs_expanded'
const CONSULTATION_EXPANDED_KEY = 'contract_consultation_expanded'

// 토글 상태 (기본값)
const isProofDocsExpanded = ref(true)
const isConsultationExpanded = ref(true)

// 로컬 스토리지에서 토글 상태 불러오기
const loadExpandedState = () => {
  const proofDocs = localStorage.getItem(PROOF_DOCS_EXPANDED_KEY)
  const consultation = localStorage.getItem(CONSULTATION_EXPANDED_KEY)

  if (proofDocs !== null) {
    isProofDocsExpanded.value = proofDocs === 'true'
  }
  if (consultation !== null) {
    isConsultationExpanded.value = consultation === 'true'
  }
}

// 상태 변경 시 로컬 스토리지에 저장
watch(isProofDocsExpanded, newValue => {
  localStorage.setItem(PROOF_DOCS_EXPANDED_KEY, String(newValue))
})

watch(isConsultationExpanded, newValue => {
  localStorage.setItem(CONSULTATION_EXPANDED_KEY, String(newValue))
})

// 서류 탭 상태
const activeDocTab = ref<'proof' | 'pledge'>('proof')

// 컴포넌트 마운트 시 로컬 스토리지에서 상태 불러오기
onMounted(() => {
  loadExpandedState()
})
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
          <AddRequiredDocs sort-filter="proof" />
        </v-window-item>
        <v-window-item value="pledge">
          <AddRequiredDocs sort-filter="pledge" />
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
