<script lang="ts" setup>
import { ref } from 'vue'

const msg = ref('')
</script>

<template>
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
