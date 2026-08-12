<script lang="ts" setup>
import { type PropType } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'

defineProps({
  issueProjectList: { type: Array as PropType<selectProject[]>, default: () => [] },
  defaultTitle: { type: String, default: '전체 워크스페이스' },
  defaultValue: { type: String, default: '' },
  valueType: { type: String as PropType<'pk' | 'slug'>, default: 'pk' },
  showBookMarkOption: { type: Boolean, default: false },
  showClosedOption: { type: Boolean, default: false },
})
</script>

<template>
  <CFormSelect>
    <option :value="defaultValue">{{ defaultTitle }}</option>
    <option v-if="showBookMarkOption" value="bookmark">&lt;&lt; 내 북마크 &gt;&gt;</option>
    <option v-if="showClosedOption" value="closed">닫힘</option>
    <option
      v-for="proj in issueProjectList"
      :value="valueType === 'slug' ? proj.slug : proj.value"
      :key="proj.slug"
    >
      {{ proj.label }}
    </option>
  </CFormSelect>
</template>
