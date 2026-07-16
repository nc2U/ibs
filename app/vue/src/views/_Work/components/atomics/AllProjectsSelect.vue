<script lang="ts" setup>
import { type PropType } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'

defineProps({
  allProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  defaultTitle: { type: String, default: '전체 프로젝트' },
  defaultValue: { type: String, default: '' },
})
</script>

<template>
  <CFormSelect>
    <option :value="defaultValue">{{ defaultTitle }}</option>
    <option v-for="proj in allProjects" :value="proj.value" :key="proj.slug">
      {{ proj.label }}
    </option>
  </CFormSelect>
</template>
