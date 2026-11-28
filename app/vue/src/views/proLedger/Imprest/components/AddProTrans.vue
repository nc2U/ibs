<script lang="ts" setup>
import AddProTrans from '@/views/proLedger/Manage/components/AddProTrans.vue'

defineProps<{
  project?: number | null
}>()
</script>

<template>
  <AddProTrans :project="project" route-name="운영비 내역 관리 - 생성" />
</template>
