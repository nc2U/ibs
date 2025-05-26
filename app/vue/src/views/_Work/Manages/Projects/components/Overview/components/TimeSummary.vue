<script lang="ts" setup>
import { inject, type PropType } from 'vue'
import type { IssueProject } from '@/store/types/work_project.ts'
import { numberToHour } from '@/utils/baseMixins'

defineProps({ project: { type: Object as PropType<IssueProject>, required: true } })

const isDark = inject('isDark')
</script>

<template>
  <CCard :color="isDark ? '' : 'light'">
    <CCardBody>
      <CCardSubtitle class="mb-2">
        <v-icon icon="mdi-clock-outline" size="small" class="mr-1" />
        시간 추적
      </CCardSubtitle>

      <ul class="pl-4 mb-0">
        <li>추정시간 : {{ numberToHour(project?.total_estimated_hours ?? 0) }} 시간</li>
        <li>소요시간 : {{ numberToHour(project?.total_time_spent ?? 0) }} 시간</li>
      </ul>
    </CCardBody>

    <CCardText class="mx-3 mb-2 form-text">
      <router-link v-if="project?.status === '1'" :to="{ name: '(소요시간) - 추가' }">
        작업시간 기록
      </router-link>
      <span v-if="project?.status === '1'" class="px-2">|</span>
      <router-link :to="{ name: '(소요시간)' }">자세히</router-link>
      <span class="px-2">|</span>
      <router-link :to="{ name: '(소요시간)', query: { report: '1' } }">보고서</router-link>
    </CCardText>
  </CCard>
</template>
