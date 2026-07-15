<script lang="ts" setup>
import { type PropType } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'

defineProps({
  allProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  defaultTitle: { type: String, default: '전체 프로젝트' },
  required: { type: Boolean, default: false },
  size: { type: String, default: '' },
})
</script>

<template>
  <CFormSelect :required="required" :size="size">
    <option value="">{{ defaultTitle }}</option>
    <option v-for="proj in allProjects" :value="proj.pk" :key="proj.pk">
      <span v-if="!!proj.depth && proj.parent_visible"> {{ '&nbsp;'.repeat(proj.depth) }} » </span>
      {{ proj.label }}
    </option>
  </CFormSelect>
</template>
