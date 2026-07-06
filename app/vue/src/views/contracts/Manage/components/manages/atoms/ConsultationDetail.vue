<script lang="ts" setup>
import type { ConsultationLog } from '@/store/types/contract'
import { timeFormat } from '@/utils/baseMixins.ts'

// Props
defineProps<{
  log: ConsultationLog
}>()
</script>

<template>
  <div class="p-3">
    <CRow>
      <CCol :md="12" class="mb-2">
        <strong>[{{ log.title }}]</strong>
      </CCol>
    </CRow>
    <CRow>
      <CCol :md="12" class="mb-2">
        <div class="mt-1">{{ log.content || '내용 없음' }}</div>
      </CCol>
    </CRow>
    <CRow v-if="log.follow_up_note" class="mt-2">
      <CCol :md="12">
        <strong>후속조치:</strong>
        <div class="mt-1">{{ log.follow_up_note }}</div>
      </CCol>
    </CRow>
    <CRow class="mt-2">
      <CCol :md="12" class="text-end">
        <small class="text-muted">
          등록자 :: {{ (log.consultant as any)?.username || '미지정' }}
          <span class="ml-2">{{ timeFormat(log.created) }}</span>
        </small>
      </CCol>
    </CRow>
  </div>
</template>
