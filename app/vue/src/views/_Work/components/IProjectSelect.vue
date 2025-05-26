<script lang="ts" setup="">
import { type PropType } from 'vue'
import type { IssueProject } from '@/store/types/work_project.ts'

defineProps({
  allProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
  required: { type: Boolean, default: false },
  size: { type: String, default: '' },
})
</script>

<template>
  <CFormSelect :required="required" :size="size">
    <option value="">---------</option>
    <option v-for="proj in allProjects" :value="proj.slug" :key="proj.slug">
      <span v-if="!!proj.depth && proj.parent_visible"> {{ '&nbsp;'.repeat(proj.depth) }} » </span>
      {{ proj.name }}
    </option>
  </CFormSelect>
</template>
