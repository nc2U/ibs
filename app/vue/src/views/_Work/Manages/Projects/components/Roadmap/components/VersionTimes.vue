<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { numberToHour } from '@/utils/baseMixins'
import type { SimpleIssue } from '@/store/types/work_issue.ts'

const props = defineProps({
  issues: { type: Array as PropType<SimpleIssue[]>, default: () => [] },
  versionPk: { type: Number, required: true },
})

const get_total_estimated_hours = computed(
  () => props.issues?.reduce((sum, issue) => sum + Number(issue.estimated_hours ?? 0), 0) ?? 0,
)

const get_total_spent_times = computed(
  () => props.issues?.reduce((sum, issue) => sum + issue.spent_times, 0) ?? 0,
)
</script>

<template>
  <CRow class="mb-4">
    <CCol>
      <div class="p-2 border bold">
        <h6>시간추적</h6>
        <CRow class="my-2">
          <CCol class="col-6 text-center">추정시간</CCol>
          <CCol class="col-6 text-right pr-5">
            <!-- 목표버전 필터링 업무 리스트 구현-->
            <router-link :to="{ name: '(업무)', query: { version: versionPk } }">
              {{ numberToHour(get_total_estimated_hours) }} 시간
            </router-link>
          </CCol>
          <CCol class="col-6 text-center">소요시간</CCol>
          <CCol class="col-6 text-right pr-5">
            <!-- 목표버전 필터링 소요시간 리스트 구현-->
            <router-link :to="{ name: '(소요시간)', query: { version: versionPk } }">
              {{ numberToHour(get_total_spent_times) }} 시간
            </router-link>
          </CCol>
        </CRow>
      </div>
    </CCol>
  </CRow>
</template>
