<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work'
import type { TimeEntryFilter } from '@/store/types/work'
import TimeEntryList from '@/views/_Work/Manages/SpentTime/components/TimeEntryList.vue'
import TimeEntryForm from '@/views/_Work/Manages/SpentTime/components/TimeEntryForm.vue'

const emit = defineEmits(['aside-visible'])

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject)
const allProjects = computed(() => workStore.AllIssueProjects)
const timeEntryList = computed(() => workStore.timeEntryList)
const getIssues = computed(() => workStore.getIssues)
const getMembers = computed(() =>
  issueProject.value?.all_members?.map(m => ({
    value: m.user.pk,
    label: m.user.username,
  })),
)
const getVersions = computed(() => workStore.getVersions)

const createTimeEntry = (payload: any) => workStore.createTimeEntry(payload)
const updateTimeEntry = (payload: any) => workStore.updateTimeEntry(payload)
const deleteTimeEntry = (pk: number) => workStore.deleteTimeEntry(pk)

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
  workStore.fetchTimeEntryList(payload)
  console.log(payload)
}

const pageSelect = (page: number) => {
  listFilter.value.page = page
  workStore.fetchTimeEntryList(listFilter.value)
}

const delSubmit = (pk: number) => deleteTimeEntry(pk)

watch(route, async nVal => {
  if (nVal.params.projId || nVal.params.issueId)
    await workStore.fetchTimeEntryList({ project: project.value, issue: Number(issue.value) })
})

onBeforeMount(() => {
  emit('aside-visible', true)
  workStore.fetchAllIssueProjectList()
  workStore.fetchAllIssueList(project.value)
  workStore.fetchTimeEntryList({ ...listFilter.value })
  workStore.fetchVersionList({ project: project.value })
})
</script>

<template>
  <TimeEntryList
    v-if="route.name === '(소요시간)'"
    :proj-status="issueProject?.status"
    :time-entry-list="timeEntryList"
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
