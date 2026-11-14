<script lang="ts" setup>
import { onUnmounted, type PropType, ref, watchEffect } from 'vue'
import {
  DEFAULT_ISSUE_COLUMNS,
  ISSUE_COLUMN_LABEL_MAP,
} from '@/views/_Work/Manages/Issues/constants'
import { useIssue } from '@/store/pinia/work_issue'
import type { Issue } from '@/store/types/work_issue'
import Pagination from '@/components/Pagination'
import NoData from '@/components/NoData/Index.vue'
import IssueItem from './IssueItem.vue'

defineProps({
  issueList: { type: Array as PropType<Issue[]>, default: () => [] },
  columns: {
    type: Array as PropType<string[]>,
    default: () => DEFAULT_ISSUE_COLUMNS,
  },
  page: { type: Number, default: 1 },
})

const emit = defineEmits(['page-select'])

const selectedRow = ref<number | null>(null)
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null
  if (!target?.closest('.table-row')) selectedRow.value = null
}

watchEffect(() => {
  if (selectedRow.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

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
          <template v-for="colKey in columns" :key="'head-' + colKey">
            <CTableHeaderCell
              scope="col"
              :class="{
                'text-start': colKey === 'status' || colKey === 'subject',
              }"
            >
              {{ ISSUE_COLUMN_LABEL_MAP[colKey] || colKey }}
            </CTableHeaderCell>
          </template>
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
          <IssueItem :issue="issue" :columns="columns" />
        </CTableRow>
      </CTableBody>
    </CTable>

    <Pagination
      :active-page="page"
      :limit="8"
      :pages="issuePages(20)"
      @active-page-change="pageSelect"
      class="mt-3"
    />
  </CCol>
</template>
