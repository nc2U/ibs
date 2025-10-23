<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Contract } from '@/store/types/contract'
import { useContract } from '@/store/pinia/contract.ts'
import { CCard, CCardBody } from '@coreui/vue'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
})

const contStore = useContract()
// const contractFileList = computed(() => contStore.contractFileList as RequiredDocs[])
</script>

<template>
  <!-- 구비서류 제출 현황 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>구비서류 제출 현황</strong>
    </CCardHeader>
    <CCardBody>
      <!--      <div v-if="contractFileList.length > 0">-->
      <!--        <div v-for="file in contractFileList" :key="file">-->
      <!--          {{ file }}-->
      <!--        </div>-->
      <!--      </div>-->
      <div class="text-center text-muted py-3">
        <v-icon icon="mdi-file-document-check-outline" size="large" class="mb-2" />
        <div>구비서류 제출 현황 정보가 없습니다.</div>
      </div>
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
