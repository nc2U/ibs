<script lang="ts" setup>
import { computed, ref, type PropType } from 'vue'
import type { Issue, SimpleIssue } from '@/store/types/work_issue.ts'

const props = defineProps({
  issues: {
    type: Array as PropType<(SimpleIssue | Issue | any)[]>,
    default: () => [],
  },
})

type GroupType = 'tracker' | 'status' | 'priority' | 'creator' | 'assigned_to' | 'category'

const selectedGroup = ref<GroupType>('tracker')

interface SummaryItem {
  name: string
  closedCount: number
  totalCount: number
  ratio: number
}

const groupedSummary = computed<SummaryItem[]>(() => {
  if (!props.issues || props.issues.length === 0) return []

  const groupMap = new Map<string, { closed: number; total: number }>()

  props.issues.forEach(issue => {
    let key = '미지정'

    switch (selectedGroup.value) {
      case 'tracker':
        key = issue.tracker && typeof issue.tracker === 'object' ? issue.tracker.name : (issue.tracker ? String(issue.tracker) : '미지정')
        break
      case 'status':
        key = issue.status && typeof issue.status === 'object' ? issue.status.name : (issue.status ? String(issue.status) : '미지정')
        break
      case 'priority':
        key = issue.priority && typeof issue.priority === 'object' ? issue.priority.name : (issue.priority ? String(issue.priority) : '미지정')
        break
      case 'creator':
        key = issue.creator && typeof issue.creator === 'object' ? (issue.creator.username || issue.creator.name || '미지정') : (issue.creator ? String(issue.creator) : '미지정')
        break
      case 'assigned_to':
        key = issue.assigned_to && typeof issue.assigned_to === 'object' ? (issue.assigned_to.username || issue.assigned_to.name || '미지정') : (issue.assigned_to ? String(issue.assigned_to) : '미지정')
        break
      case 'category':
        key = issue.category && typeof issue.category === 'object' ? (issue.category.name || '미지정') : ((issue as any).category_name || '미지정')
        break
    }

    if (!key || key === 'undefined' || key === 'null' || key.trim() === '') {
      key = '미지정'
    }

    if (!groupMap.has(key)) {
      groupMap.set(key, { closed: 0, total: 0 })
    }

    const item = groupMap.get(key)!
    item.total += 1
    if (issue.closed || issue.status?.closed) {
      item.closed += 1
    }
  })

  const result: SummaryItem[] = []
  groupMap.forEach((val, key) => {
    result.push({
      name: key,
      closedCount: val.closed,
      totalCount: val.total,
      ratio: val.total > 0 ? Math.round((val.closed / val.total) * 100) : 0,
    })
  })

  return result
})
</script>

<template>
  <CRow class="mb-4">
    <CCol>
      <div class="p-3 border rounded bg-white">
        <CRow class="mb-3 align-items-center">
          <CCol class="col-7 col-lg-8">
            <CFormSelect v-model="selectedGroup" size="sm">
              <option value="tracker">유형</option>
              <option value="status">상태</option>
              <option value="priority">우선순위</option>
              <option value="creator">작성자</option>
              <option value="assigned_to">담당자</option>
              <option value="category">범주</option>
            </CFormSelect>
          </CCol>
          <CCol class="pl-0 text-muted small">별 업무</CCol>
        </CRow>

        <div v-if="!groupedSummary.length" class="text-muted small text-center py-3">
          업무 데이터가 없습니다.
        </div>

        <div v-else>
          <CRow v-for="item in groupedSummary" :key="item.name" class="my-2 align-items-center">
            <CCol class="col-4 text-truncate text-right small fw-bold" :title="item.name">
              {{ item.name }}
            </CCol>
            <CCol class="col-5">
              <CProgress
                :value="item.ratio"
                color="success"
                height="14px"
                class="rounded-pill"
              />
            </CCol>
            <CCol class="col-3 small text-muted">
              {{ item.closedCount }}/{{ item.totalCount }}
            </CCol>
          </CRow>
        </div>
      </div>
    </CCol>
  </CRow>
</template>
