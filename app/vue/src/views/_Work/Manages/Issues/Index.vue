<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import type { Company } from '@/store/types/settings'
import { useWork } from '@/store/pinia/work_project.ts'
import { useAccount } from '@/store/pinia/account'
import { useRoute, useRouter } from 'vue-router'
import type { IssueFilter } from '@/store/types/work_project.ts'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import IssueList from './components/IssueList.vue'
import IssueForm from './components/IssueForm.vue'

const cBody = ref()
const company = inject<ComputedRef<Company>>('company')
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const accStore = useAccount()
const getUsers = computed(() => accStore.getUsers)

const workStore = useWork()
const issueList = computed(() => workStore.issueList)
const allProjects = computed(() => workStore.AllIssueProjects)

const statusList = computed(() => workStore.statusList)
const trackerList = computed(() => workStore.trackerList)
const priorityList = computed(() => workStore.priorityList)
const getIssues = computed(() => workStore.getIssues)
const getVersions = computed(() => workStore.getVersions)

const [route, router] = [useRoute(), useRouter()]

provide('navMenu', navMenu)
provide('query', route?.query)

const onSubmit = (payload: any) => {
  const { pk, ...getData } = payload
  const form = new FormData()

  for (const key in getData) {
    if (key === 'watchers' || key === 'files')
      getData[key]?.forEach((val: number | string) => form.append(key, JSON.stringify(val)))
    else if (key === 'newFiles') {
      getData[key].forEach((val: any) => {
        form.append('files', val.file as string | Blob)
        form.append('descriptions', val.description ?? '')
      })
    } else form.append(key, getData[key] === null ? '' : (getData[key] as string))
  }

  if (pk) workStore.updateIssue(pk, form)
  else {
    workStore.createIssue(form)
    if (route.params.projId) {
      if (route.query.parent)
        router.replace({
          name: '(업무) - 보기',
          params: { projId: route.params.projId, issueId: route.query.parent as string },
        })
      else router.replace({ name: '(업무)' })
    } else router.replace({ name: '업무' })
  }
}

const listFilter = ref<IssueFilter>({ status__closed: '0' })
const filterSubmit = (payload: IssueFilter) => {
  listFilter.value = payload
  workStore.fetchIssueList(payload)
}
const pageSelect = (page: number) => {
  listFilter.value.page = page
  workStore.fetchIssueList(listFilter.value)
}

onBeforeMount(async () => {
  await workStore.fetchAllIssueProjectList()
  await workStore.fetchAllIssueList()
  if (!route.query) await workStore.fetchIssueList({ status__closed: '0' })

  await workStore.fetchMemberList()
  await workStore.fetchTrackerList()
  await workStore.fetchStatusList()
  await workStore.fetchPriorityList()
  if (route.params.projId)
    await workStore.fetchVersionList({ project: route.params.projId as string })

  await accStore.fetchUsersList()
})
</script>

<template>
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <IssueList
        v-if="route.name === '업무'"
        :issue-list="issueList"
        :all-projects="allProjects"
        :status-list="statusList"
        :tracker-list="trackerList"
        :get-issues="getIssues"
        :get-users="getUsers"
        :get-versions="getVersions"
        @filter-submit="filterSubmit"
        @page-select="pageSelect"
      />

      <IssueForm
        v-if="route.name === '업무 - 추가'"
        :all-projects="allProjects"
        :status-list="statusList"
        :priority-list="priorityList"
        :get-issues="getIssues"
        @on-submit="onSubmit"
        @close-form="router.push({ name: '업무' })"
      />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
