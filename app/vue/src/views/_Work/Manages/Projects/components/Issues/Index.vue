<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { Issue, IssueFilter } from '@/store/types/work_issue.ts'
import Loading from '@/components/Loading/Index.vue'
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

const accStore = useAccount()
const getUsers = computed(() => accStore.getUsers)

const workStore = useWork()
const getVersions = computed(() => workStore.getVersions)
const allProjects = computed(() => workStore.getAllProjects)
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)

const issueStore = useIssue()
const issue = computed<Issue | null>(() => issueStore.issue)
const issueList = computed(() => issueStore.issueList)
const issueCommentList = computed(() => issueStore.issueCommentList)
const timeEntryList = computed(() => issueStore.timeEntryList)

const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => issueStore.trackerList)
const priorityList = computed(() => issueStore.priorityList)
const getIssues = computed(() => issueStore.getIssues)

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

  if (pk) issueStore.updateIssue(pk, form)
  else {
    issueStore.createIssue(form)
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
  issueStore.fetchIssueList(payload)
}
const pageSelect = (page: number) => {
  listFilter.value.page = page
  issueStore.fetchIssueList(listFilter.value)
}

watch(
  () => projId.value,
  nVal => {
    if (nVal && nVal.length > 0)
      issueStore.fetchIssueList({ status__closed: '0', project: nVal as string })
  },
)
const logStore = useLogging()
watch(
  () => route.params.issueId,
  async nVal => {
    if (nVal) {
      await issueStore.fetchIssue(Number(nVal))
      await logStore.fetchIssueLogList({ issue: Number(nVal) })
      await issueStore.fetchTimeEntryList({ ordering: 'pk', issue: Number(nVal) })
    } else issueStore.removeIssue()
  },
  { deep: true },
)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await workStore.fetchIssueProject(projId.value)
  await issueStore.fetchAllIssueList(projId.value)
  await issueStore.fetchIssueList({ ...listFilter.value })

  if (issueId.value) {
    await issueStore.fetchIssue(Number(issueId.value))
    await logStore.fetchIssueLogList({ issue: Number(issueId.value) })
    await issueStore.fetchTimeEntryList({ ordering: 'pk', issue: Number(issueId.value) })
  }

  await workStore.fetchMemberList()
  await issueStore.fetchTrackerList()
  await issueStore.fetchStatusList()
  await issueStore.fetchPriorityList()
  await workStore.fetchVersionList({ project: projId.value })
  loading.value = false
})
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <Loading v-model:active="loading" />
      <IssueList
        v-if="route.name === '(업무)'"
        :proj-status="issueProject?.status"
        :issue-list="issueList as Issue[]"
        :all-projects="allProjects"
        :status-list="statusList"
        :tracker-list="trackerList"
        :get-issues="getIssues"
        :get-users="getUsers"
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
