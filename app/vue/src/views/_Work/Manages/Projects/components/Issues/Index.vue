<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import type { Issue, IssueFilter, IssueProject } from '@/store/types/work_project.ts'
import IssueList from '@/views/_Work/Manages/Issues/components/IssueList.vue'
import IssueView from '@/views/_Work/Manages/Issues/components/IssueView.vue'
import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'
import IssueReport from '@/views/_Work/Manages/Issues/components/IssueReport.vue'
import AsideIssue from '@/views/_Work/Manages/Issues/components/aside/AsideIssue.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const aside = ref(true)
const [route, router] = [useRoute(), useRouter()]

const workStore = useWork()
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)
const allProjects = computed(() => workStore.AllIssueProjects)
const issue = computed<Issue | null>(() => workStore.issue)
const issueList = computed(() => workStore.issueList)
const issueCommentList = computed(() => workStore.issueCommentList)
const timeEntryList = computed(() => workStore.timeEntryList)

const statusList = computed(() => workStore.statusList)
const trackerList = computed(() => workStore.trackerList)
const priorityList = computed(() => workStore.priorityList)
const getIssues = computed(() => workStore.getIssues)
const getVersions = computed(() => workStore.getVersions)

const onSubmit = (payload: any) => {
  const { pk, ...getData } = payload
  const form = new FormData()

  for (const key in getData) {
    if (key === 'watchers' || key === 'files')
      getData[key]?.forEach((val: number | string) => form.append(key, JSON.stringify(val)))
    else if (key === 'newFiles') {
      getData[key].forEach((val: any) => {
        form.append('new_files', val.file as string | Blob)
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

const projId = computed(() => (route.params.projId as string) ?? '')
const issueId = computed(() => (route.params.issueId as string) ?? '')

const listFilter = ref<IssueFilter>({ status__closed: '0', project: projId.value })

const filterSubmit = (payload: IssueFilter) => {
  listFilter.value = payload
  workStore.fetchIssueList(payload)
}
const pageSelect = (page: number) => {
  listFilter.value.page = page
  workStore.fetchIssueList(listFilter.value)
}

watch(
  () => projId.value,
  nVal => {
    if (nVal && nVal.length > 0)
      workStore.fetchIssueList({ status__closed: '0', project: nVal as string })
  },
)
const logStore = useLogging()
watch(
  () => route.params.issueId,
  async nVal => {
    if (nVal) {
      await workStore.fetchIssue(Number(nVal))
      await logStore.fetchIssueLogList({ issue: Number(nVal) })
      await workStore.fetchTimeEntryList({ ordering: 'pk', issue: Number(nVal) })
    } else workStore.removeIssue()
  },
  { deep: true },
)

onBeforeMount(async () => {
  await workStore.fetchAllIssueProjectList()

  await workStore.fetchIssueProject(projId.value)
  await workStore.fetchAllIssueList(projId.value)
  await workStore.fetchIssueList({ ...listFilter.value })

  if (issueId.value) {
    await workStore.fetchIssue(Number(issueId.value))
    await logStore.fetchIssueLogList({ issue: Number(issueId.value) })
    await workStore.fetchTimeEntryList({ ordering: 'pk', issue: Number(issueId.value) })
  }

  await workStore.fetchMemberList()
  await workStore.fetchTrackerList()
  await workStore.fetchStatusList()
  await workStore.fetchPriorityList()
  await workStore.fetchVersionList({ project: projId.value })
})
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <IssueList
        v-if="route.name === '(업무)'"
        :proj-status="issueProject?.status"
        :issue-list="issueList as Issue[]"
        :all-projects="allProjects"
        :status-list="statusList"
        :tracker-list="trackerList"
        :get-issues="getIssues"
        :get-versions="getVersions"
        @filter-submit="filterSubmit"
        @page-select="pageSelect"
      />

      <IssueView
        v-if="route.name === '(업무) - 보기' && issue"
        :issue-project="issueProject as IssueProject"
        :issue="issue"
        :all-projects="allProjects"
        :status-list="statusList"
        :priority-list="priorityList"
        :issue-comment-list="issueCommentList"
        :time-entry-list="timeEntryList"
        @on-submit="onSubmit"
      />

      <IssueForm
        v-if="route.name === '(업무) - 추가'"
        :issue-project="issueProject as IssueProject"
        :all-projects="allProjects"
        :status-list="statusList"
        :priority-list="priorityList"
        :get-issues="getIssues"
        @on-submit="onSubmit"
        @close-form="router.push({ name: '(업무)' })"
      />

      <IssueReport v-if="route.name === '(업무) - 보고서'" />
    </template>

    <template v-slot:aside>
      <AsideIssue :issue-pk="issue?.pk as number" :watchers="issue?.watchers" />
    </template>
  </ContentBody>
</template>
