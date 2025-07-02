<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { TimeEntryFilter } from '@/store/types/work_issue.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import TimeEntryList from '@/views/_Work/Manages/SpentTime/components/TimeEntryList.vue'
import TimeEntryForm from '@/views/_Work/Manages/SpentTime/components/TimeEntryForm.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workStore = useWork()
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)
const allProjects = computed(() => workStore.getAllProjects)
const getVersions = computed(() => workStore.getVersions)
const getMembers = computed(() =>
  issueProject.value?.all_members?.map(m => ({
    value: m.user.pk,
    label: m.user.username,
  })),
)

const issueStore = useIssue()
const timeEntryList = computed(() => issueStore.timeEntryList)
const getIssues = computed(() => issueStore.getIssues)

const createTimeEntry = (payload: any) => issueStore.createTimeEntry(payload)
const updateTimeEntry = (payload: any) => issueStore.updateTimeEntry(payload)
const deleteTimeEntry = (pk: number) => issueStore.deleteTimeEntry(pk)

const [route, router] = [useRoute(), useRouter()]

const onSubmit = async (payload: any) => {
  if (payload.pk) await updateTimeEntry(payload)
  else {
    await createTimeEntry(payload)
    await router.replace({ name: '(소요시간)' })
  }
}

const project = computed(() => (route.params.projId ? (route.params.projId as string) : ''))
const issue = computed(() => (route.query.issue_id ? (route.query.issue_id as string) : ''))

const listFilter = ref<TimeEntryFilter>({ project: project.value, issue: Number(issue.value) })
const filterSubmit = (payload: TimeEntryFilter) => {
  listFilter.value = payload
  issueStore.fetchTimeEntryList(payload)
  console.log(payload)
}

const pageSelect = (page: number) => {
  listFilter.value.page = page
  issueStore.fetchTimeEntryList(listFilter.value)
}

const delSubmit = (pk: number) => deleteTimeEntry(pk)

watch(route, async nVal => {
  if (nVal.params.projId || nVal.params.issueId)
    await issueStore.fetchTimeEntryList({ project: project.value, issue: Number(issue.value) })
})

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await issueStore.fetchAllIssueList(project.value)
  await issueStore.fetchTimeEntryList({ ...listFilter.value })
  await workStore.fetchVersionList({ project: project.value })
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <TimeEntryList
        v-if="route.name === '(소요시간)'"
        :proj-status="issueProject?.status"
        :time-entry-list="timeEntryList as any"
        :sub-projects="issueProject?.sub_projects"
        :all-projects="allProjects"
        :get-issues="getIssues"
        :get-members="getMembers"
        :get-versions="getVersions"
        @filter-submit="filterSubmit"
        @page-select="pageSelect"
        @del-submit="delSubmit"
      />

      <TimeEntryForm
        v-if="route.name === '(소요시간) - 추가'"
        :all-projects="allProjects"
        @on-submit="onSubmit"
        @close-form="router.push({ name: '(소요시간)' })"
      />

      <TimeEntryForm
        v-if="route.name === '(소요시간) - 편집'"
        :all-projects="allProjects"
        @on-submit="onSubmit"
        @close-form="router.push({ name: '(소요시간)' })"
      />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
