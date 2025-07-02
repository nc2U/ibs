<script setup lang="ts">
import { ref, computed, inject, onBeforeMount, type ComputedRef, provide } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useAccount } from '@/store/pinia/account'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import type { Company } from '@/store/types/settings'
import type { TimeEntryFilter } from '@/store/types/work_issue.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import TimeEntryList from '@/views/_Work/Manages/SpentTime/components/TimeEntryList.vue'
import TimeEntryForm from '@/views/_Work/Manages/SpentTime/components/TimeEntryForm.vue'

const cBody = ref()
const company = inject<ComputedRef<Company | null>>('company')
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const workStore = useWork()
const allProjects = computed(() => workStore.getAllProjects)
const getMembers = computed(() => accStore.getUsers)
const getVersions = computed(() => workStore.getVersions)

const issueStore = useIssue()
const timeEntryList = computed(() => issueStore.timeEntryList)
const getIssues = computed(() => issueStore.getIssues)

const createTimeEntry = (payload: any) => issueStore.createTimeEntry(payload)
const updateTimeEntry = (payload: any) => issueStore.updateTimeEntry(payload)

const [route, router] = [useRoute(), useRouter()]

provide('navMenu', navMenu)
provide('query', route?.query)

const onSubmit = async (payload: any) => {
  if (payload.pk) await updateTimeEntry(payload)
  else {
    await createTimeEntry(payload)
    await router.replace({ name: '소요시간' })
  }
}

const listFilter = ref<TimeEntryFilter>({})
const filterSubmit = (payload: TimeEntryFilter) => {
  listFilter.value = payload
  issueStore.fetchTimeEntryList(payload)
  console.log(payload)
}

const pageSelect = (page: number) => {
  listFilter.value.page = page
  issueStore.fetchTimeEntryList(listFilter.value)
}

const delSubmit = (pk: number) => alert(pk)

const accStore = useAccount()
const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await issueStore.fetchTimeEntryList({})
  await issueStore.fetchAllIssueList()
  await workStore.fetchVersionList({ project: '' })
  await accStore.fetchUsersList()
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <TimeEntryList
        v-if="route.name === '소요시간'"
        :time-entry-list="timeEntryList"
        :all-projects="allProjects"
        :get-issues="getIssues"
        :get-members="getMembers"
        :get-versions="getVersions"
        @filter-submit="filterSubmit"
        @page-select="pageSelect"
        @del-submit="delSubmit"
      />

      <TimeEntryForm
        v-if="route.name === '소요시간 - 추가'"
        :all-projects="allProjects"
        @on-submit="onSubmit"
        @close-form="router.push({ name: '소요시간' })"
      />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
