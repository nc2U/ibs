<script setup lang="ts">
import { computed, onBeforeMount, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { ALL_ISSUE_COLUMNS, DEFAULT_ISSUE_COLUMNS } from './constants.ts'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useRoute } from 'vue-router'
import { useTableColumns } from '@/composables/useTableColumns.ts'
import type { Company } from '@/store/types/settings'
import type { Issue, IssueFilter } from '@/store/types/work_issue.ts'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import IssueHeader from './automics/IssueHeader.vue'
import IssueTable from './components/IssueTable.vue'
import QuerySection from './components/QuerySection.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'
import Loading from '@/components/Loading/Index.vue'
import ColumnSelector from '@/views/_Work/components/atomics/ColumnSelector.vue'

const cBody = ref()
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const accStore = useAccount()
const getUsers = computed(() => accStore.getUsers)

const workStore = useWork()
const allReadableProjects = computed(() => workStore.getAllReadableProjects)
const getVersions = computed(() => workStore.getVersions)

const issueStore = useIssue()
const issueList = computed(() => issueStore.issueList)
const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => issueStore.trackerList)
const priorityList = computed(() => issueStore.priorityList)
const categoryList = computed(() => issueStore.categoryList)
const getIssues = computed(() => issueStore.getIssues)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

const listFilter = ref<IssueFilter>({ status__closed: '0', project_status: '1' })
const filterSubmit = (payload: IssueFilter) => {
  listFilter.value = payload
  issueStore.fetchIssueList(payload)
}
const pageSelect = (page: number) => {
  listFilter.value.page = page
  issueStore.fetchIssueList(listFilter.value)
}

const querySectionRef = ref()
const activeQueryId = ref<number | null>(null)
const onQueryClick = (query: any) => {
  activeQueryId.value = query.pk
  querySectionRef.value?.applyQuery(query)
}
const onResetQuery = () => {
  activeQueryId.value = null
  querySectionRef.value?.resetFilter()
}

// Columns Selector Start
const { selectedColumns } = useTableColumns('global-issue-table-columns', ALL_ISSUE_COLUMNS, [
  'project',
  ...DEFAULT_ISSUE_COLUMNS,
])
// Columns Selector End!

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await Promise.all([
    workStore.fetchMemberList(),
    workStore.fetchVersionList(),
    issueStore.fetchTrackerList(),
    issueStore.fetchStatusList(),
    issueStore.fetchPriorityList(),
    issueStore.fetchCategoryList(),
    issueStore.fetchAllIssueList(),
  ])
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <IssueHeader />

      <QuerySection
        ref="querySectionRef"
        :search-projects="allReadableProjects"
        :status-list="statusList"
        :tracker-list="trackerList"
        :priority-list="priorityList"
        :category-list="categoryList"
        :get-issues="getIssues"
        :get-users="getUsers"
        :get-versions="getVersions"
        @filter-submit="filterSubmit"
      >
        <template #option>
          <ColumnSelector v-model="selectedColumns" :all-columns="ALL_ISSUE_COLUMNS" />
        </template>
      </QuerySection>

      <IssueTable
        ref="issueListRef"
        :issue-list="issueList as Issue[]"
        :columns="selectedColumns"
        @page-select="pageSelect"
      />
    </template>

    <template v-slot:aside>
      <SavedQueryAside
        target-type="issue"
        :active-query-id="activeQueryId ?? undefined"
        @on-query-click="onQueryClick"
        @on-reset-query="onResetQuery"
      />
    </template>
  </ContentBody>
</template>
