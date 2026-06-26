<script lang="ts" setup="">
import { computed, type PropType } from 'vue'
import { useStore } from '@/store'
import type { IssueProject } from '@/store/types/work_project.ts'

defineProps({
  subProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
})

const store = useStore()
const isDark = computed(() => store.theme === 'dark')
</script>

<template>
  <CCard :color="isDark ? '' : 'light'" class="mb-3">
    <CCardBody>
      <CCardSubtitle class="mb-2">
        <v-icon icon="mdi-subdirectory-arrow-right" size="sm" class="mr-1" />
        하위 프로젝트
      </CCardSubtitle>
      <CCardText>
        <router-link
          v-for="(sub, i) in subProjects"
          :to="{ name: '(개요)', params: { projId: sub.slug } }"
          :key="sub.pk"
        >
          {{ sub.name }}<span v-if="i + 1 < subProjects?.length">, </span>
        </router-link>
      </CCardText>
    </CCardBody>
  </CCard>
</template>
