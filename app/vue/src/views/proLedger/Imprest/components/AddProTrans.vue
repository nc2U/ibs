<script lang="ts" setup>
import { AlertLight } from '@/utils/cssMixins'

defineProps({ project: { type: Number, default: null } })
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn
      color="primary"
      :disabled="!project"
      @click="$router.push({ name: '운영비 내역 관리 - 생성' })"
    >
      <v-icon icon="mdi-plus" start />
      새 거래 등록
    </v-btn>
  </CAlert>
</template>
