<script lang="ts" setup>
import { AlertLight } from '@/utils/cssMixins'

defineProps<{
  company?: number | null
}>()
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="d-flex justify-end ga-2">
    <v-btn
      color="primary"
      :disabled="!company"
      prepend-icon="mdi-plus"
      @click="$router.push({ name: '본사 거래 내역 - 생성' })"
    >
      새 거래 등록
    </v-btn>
  </CAlert>
</template>
