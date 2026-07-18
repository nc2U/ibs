<script setup lang="ts">
import { computed, onBeforeMount, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { Company } from '@/store/types/settings'
import type { Issue, IssueFilter } from '@/store/types/work_issue.ts'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'
import IssueList from './components/IssueList.vue'
import Loading from '@/components/Loading/Index.vue'

const cBody = ref()
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const accStore = useAccount()
const getUsers = computed(() => accStore.getUsers)

const workStore = useWork()
const allProjects = computed(() => workStore.getAllProjects)
const getVersions = computed(() => workStore.getVersions)

const issueStore = useIssue()
const issueList = computed(() => issueStore.issueList)
const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => issueStore.trackerList)
const priorityList = computed(() => issueStore.priorityList)
const getIssues = computed(() => issueStore.getIssues)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

const listFilter = ref<IssueFilter>({ status__closed: '0' })
const filterSubmit = (payload: IssueFilter) => {
  listFilter.value = payload
  issueStore.fetchIssueList(payload)
}
const pageSelect = (page: number) => {
  listFilter.value.page = page
  issueStore.fetchIssueList(listFilter.value)
}

// 쿼리 관련 핸들러 추가
const activeQueryId = ref<number | null>(null)
const onQueryClick = (query: any) => {
  activeQueryId.value = query.pk
  // 여기에 쿼리 적용 로직 필요 (필요시 구현)
}
const onResetQuery = () => {
  activeQueryId.value = null
  // 여기에 쿼리 초기화 로직 필요 (필요시 구현)
}

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await issueStore.fetchAllIssueList()
  if (!route.query) await issueStore.fetchIssueList({ status__closed: '0' })

  await workStore.fetchMemberList()
  await workStore.fetchVersionList() // 전역 목표단계(버전) 목록 로드
  await issueStore.fetchTrackerList()
  await issueStore.fetchStatusList()
  await issueStore.fetchPriorityList()
  await accStore.fetchUsersList()
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <!-- 전역 업무 인덱스는 항상 리스트 뷰만 노출 -->
      <IssueList
        :issue-list="issueList as Issue[]"
        :all-projects="allProjects"
        :status-list="statusList"
        :tracker-list="trackerList"
        :priority-list="priorityList"
        :get-issues="getIssues"
        :get-users="getUsers"
        :get-versions="getVersions"
        @filter-submit="filterSubmit"
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
