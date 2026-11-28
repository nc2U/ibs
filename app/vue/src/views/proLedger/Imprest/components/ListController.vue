<script lang="ts" setup>
import { ref } from 'vue'
import type { DataFilter } from '@/store/types/proLedger'
import ListController from '@/views/proLedger/Manage/components/ListController.vue'

defineProps<{
  project?: number | null
  dataFilter?: DataFilter
}>()
const emit = defineEmits(['list-filtering'])

const innerRef = ref<InstanceType<typeof ListController> | null>(null)
const listFiltering = (page = 1) => innerRef.value?.listFiltering(page)
defineExpose({ listFiltering })
</script>

<template>
  <ListController
    ref="innerRef"
    :project="project"
    :data-filter="dataFilter"
    imprest-only
    @list-filtering="emit('list-filtering', $event)"
  />
</template>
