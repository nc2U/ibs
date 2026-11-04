<script lang="ts" setup>
import { AlertLight } from '@/utils/cssMixins'

defineProps<{
  project?: number | null
}>()
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="d-flex justify-end ga-2">
    <v-btn
      color="primary"
      :disabled="!project"
      prepend-icon="mdi-plus"
      @click="$router.push({ name: '운영비 내역 관리 - 생성' })"
    >
      새 거래 등록
    </v-btn>
  </CAlert>
</template>
