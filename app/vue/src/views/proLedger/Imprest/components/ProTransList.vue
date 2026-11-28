<script lang="ts" setup>
import type { ProjectBank } from '@/store/types/proLedger.ts'
import ProTransList from '@/views/proLedger/Manage/components/ProTransList.vue'

defineProps<{
  project?: number | null
  highlightId?: number | null
  currentPage?: number
}>()
const emit = defineEmits(['page-select', 'on-bank-create', 'on-bank-update'])
</script>

<template>
  <ProTransList
    :project="project"
    :highlight-id="highlightId"
    :current-page="currentPage"
    is-imprest
    @page-select="emit('page-select', $event)"
    @on-bank-create="emit('on-bank-create', $event as ProjectBank)"
    @on-bank-update="emit('on-bank-update', $event as ProjectBank)"
  />
</template>
