<script lang="ts" setup>
import ProTransForm from '@/views/proLedger/Manage/components/ProTransForm.vue'

defineProps<{
  project?: number | null
}>()
</script>

<template>
  <ProTransForm :project="project" is-imprest />
</template>
