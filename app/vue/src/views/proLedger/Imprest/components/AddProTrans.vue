<script lang="ts" setup>
import { AlertLight } from '@/utils/cssMixins'

defineProps({ project: { type: Number, default: null } })
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn
      color="primary"
      :disabled="!project"
      @click="$router.push({ name: 'PR 거래 내역 - 생성' })"
    >
      <v-icon icon="mdi-plus" start />
      새 거래 등록
    </v-btn>
  </CAlert>
</template>
