<script lang="ts" setup>
import { type PropType, ref, watchEffect } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'
import type { Issue, IssueFilter, IssueStatus, Tracker } from '@/store/types/work_issue.ts'
import { useRoute } from 'vue-router'
import { useIssue } from '@/store/pinia/work_issue.ts'
import Pagination from '@/components/Pagination'
import NoData from '@/components/NoData/Index.vue'
import IssueItem from './IssueItem.vue'

const props = defineProps({
  issueList: { type: Array as PropType<Issue[]>, default: () => [] },
  searchProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  trackerList: { type: Array as PropType<Tracker[]>, default: () => [] },
  priorityList: { type: Array as PropType<any[]>, default: () => [] },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getUsers: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getVersions: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['filter-submit', 'page-select'])

const route = useRoute()

const selectedRow = ref<number | null>(null)
const handleClickOutside = (event: any) => {
  if (!event.target.closest('.table-row')) selectedRow.value = null
}

watchEffect(() => {
  if (selectedRow.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

const filterSubmit = (payload: IssueFilter) => emit('filter-submit', payload)

const querySectionRef = ref()
const applyQuery = (query: any) => querySectionRef.value?.applyQuery(query)
const resetFilter = () => querySectionRef.value?.resetFilter()

defineExpose({ applyQuery, resetFilter })

const issueStore = useIssue()
const issuePages = (pageNum: number) => issueStore.issuePages(pageNum)
const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <NoData v-if="!issueList.length" />

  <CCol v-else col="12">
    <v-divider class="mb-0" />
    <CTable striped hover small responsive>
      <CTableHead>
        <CTableRow class="text-center">
          <CTableHeaderCell scope="col">#</CTableHeaderCell>
          <CTableHeaderCell v-if="!route.params.projId" scope="col">프로젝트</CTableHeaderCell>
          <CTableHeaderCell scope="col">유형</CTableHeaderCell>
          <CTableHeaderCell scope="col">상태</CTableHeaderCell>
          <CTableHeaderCell scope="col">우선순위</CTableHeaderCell>
          <CTableHeaderCell scope="col">단계</CTableHeaderCell>
          <CTableHeaderCell scope="col">제목</CTableHeaderCell>
          <CTableHeaderCell scope="col">담당자</CTableHeaderCell>
          <CTableHeaderCell scope="col">변경</CTableHeaderCell>
          <CTableHeaderCell scope="col"></CTableHeaderCell>
        </CTableRow>
      </CTableHead>

      <CTableBody>
        <CTableRow
          v-for="issue in issueList"
          @click="selectedRow = issue.pk"
          :color="selectedRow === issue.pk ? 'primary' : ''"
          class="text-center table-row cursor-menu"
          :key="issue.pk"
        >
          <IssueItem :issue="issue" />
        </CTableRow>
      </CTableBody>
    </CTable>

    <Pagination
      :active-page="1"
      :limit="8"
      :pages="issuePages(20)"
      @active-page-change="pageSelect"
      class="mt-3"
    />
  </CCol>
</template>
