<script lang="ts" setup>
import { type PropType } from 'vue'
import type { Project } from '@/store/types/project'
import { AlertLight } from '@/utils/cssMixins'

defineProps({
  company: { type: Number, default: null },
})
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn
      color="primary"
      :disabled="!company"
      @click="$router.push({ name: '본사 거래 내역 - 생성' })"
    >
      <v-icon icon="mdi-plus" start />
      새 거래 등록
    </v-btn>
  </CAlert>
</template>
