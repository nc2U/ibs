<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { ALL_ISSUE_COLUMNS, DEFAULT_ISSUE_COLUMNS } from '@/views/_Work/Manages/Issues/constants.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import { usePerms } from '@/composables/usePerms'
import { useRoute, useRouter } from 'vue-router'
import { useTableColumns } from '@/composables/useTableColumns.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { Issue, IssueFilter } from '@/store/types/work_issue.ts'
import IssueHeader from '@/views/_Work/Manages/Issues/automics/IssueHeader.vue'
import IssueTable from '@/views/_Work/Manages/Issues/components/IssueTable.vue'
import IssueDetail from '@/views/_Work/Manages/Issues/components/IssueDetail.vue'
import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'
import IssueReport from '@/views/_Work/Manages/Issues/components/IssueReport.vue'
import IssueItemAside from '@/views/_Work/Manages/Issues/components/aside/IssueItemAside.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import Loading from '@/components/Loading/Index.vue'
import QuerySection from '@/views/_Work/Manages/Issues/components/QuerySection.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const { can, PERM } = usePerms()
const canPubQuery = computed(() => can(PERM.PROJECT_PUB_QUERY))

const [route, router] = [useRoute(), useRouter()]

const accStore = useAccount()
const getUsers = computed(() => accStore.getUsers)

const workStore = useWork()
const getVersions = computed(() => workStore.getVersions)
const allReadableProjects = computed(() => workStore.getAllReadableProjects)
const myProjects = computed(() => workStore.getMyProjects)
const currentProject = computed<IssueProject | null>(() => workStore.currentProject)

const issueStore = useIssue()
const issue = computed<Issue | null>(() => issueStore.issue)
const issueList = computed(() => issueStore.issueList)
const issueCommentList = computed(() => issueStore.issueCommentList)

const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => issueStore.trackerList)
const priorityList = computed(() => issueStore.priorityList)
const categoryList = computed(() => issueStore.categoryList)
const getIssues = computed(() => issueStore.getIssues)

const issueListRef = ref()
const activeQueryId = ref<number | undefined>(undefined)

const onQueryClick = (query: any) => {
  activeQueryId.value = query.pk
  issueListRef.value?.applyQuery(query)
}

const onResetQuery = () => {
  activeQueryId.value = undefined
  issueListRef.value?.resetFilter()
}

const onSubmit = async (payload: any) => {
  const { pk, ...getData } = payload
  const form = new FormData()

  for (const key in getData) {
    if (key === 'watchers' || key === 'files' || key === 'links')
      getData[key]?.forEach((val: any) => form.append(key, JSON.stringify(val)))
    else if (key === 'newFiles') {
      getData[key].forEach((val: any) => {
        form.append('new_files', val.file as string | Blob)
        form.append('descriptions', val.description ?? '')
      })
    } else if (key === 'newLinks') {
      getData[key].forEach((val: any) => {
        if (val.link && val.link.trim()) {
          form.append('newLinks', val.link.trim())
          form.append('newLinkNames', val.name ?? '')
        }
      })
    } else if (getData[key] !== null && getData[key] !== undefined) {
      form.append(key, getData[key])
    }
  }

  if (pk) await issueStore.updateIssue(pk, form)
  else {
    const newIssue = await issueStore.createIssue(form)
    if (newIssue && newIssue.pk) {
      const projId = (route.params.projId as string) || newIssue.project?.slug || newIssue.project

      // 하위 업무를 생성한 경우(부모 ID가 존재하면) 부모 상세 페이지로 복귀
      const parentId = (route.query.parent as string) || newIssue.parent

      if (parentId) {
        await router.replace({
          name: '(업무) - 보기',
          params: { projId, issueId: String(parentId) },
        })
      } else {
        await router.replace({
          name: '(업무) - 보기',
          params: { projId, issueId: String(newIssue.pk) },
        })
      }
    } else {
      if (route.params.projId) {
        if (route.query.parent)
          await router.replace({
            name: '(업무) - 보기',
            params: { projId: route.params.projId, issueId: route.query.parent as string },
          })
        else await router.replace({ name: '(업무)' })
      } else await router.replace({ name: '업무' })
    }
  }
}

const projId = computed(() => (route.params.projId as string) ?? '')
const issueId = computed(() => (route.params.issueId as string) ?? '')

const listFilter = ref<IssueFilter>({
  status__closed: '0',
  project_status: '1',
  project: projId.value,
})

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
      issueStore.fetchIssueList({
        status__closed: '0',
        project_status: '1',
        project: nVal as string,
      })
  },
)
const logStore = useLogging()
watch(
  () => route.params.issueId,
  async nVal => {
    if (nVal) {
      loading.value = true
      await issueStore.fetchIssue(Number(nVal))
      await logStore.fetchIssueLogList({ issue: Number(nVal) })
      loading.value = false
    } else issueStore.removeIssue()
  },
  { deep: true },
)

// Columns Selector Start
const { selectedColumns } = useTableColumns(
  'meeting-table-columns',
  ALL_ISSUE_COLUMNS,
  DEFAULT_ISSUE_COLUMNS,
)
// Columns Selector End!

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await workStore.fetchIssueProject(projId.value)

  if (issueId.value) {
    await issueStore.fetchIssue(Number(issueId.value))
    await logStore.fetchIssueLogList({ issue: Number(issueId.value) })
  }

  await Promise.all([
    workStore.fetchMemberList(),
    issueStore.fetchTrackerList(),
    issueStore.fetchStatusList(),
    issueStore.fetchPriorityList(),
    issueStore.fetchCategoryList(projId.value), // 프로젝트 카테고리(범주) 목록 로드
    workStore.fetchVersionList({ project: projId.value }),
    issueStore.fetchAllIssueList(projId.value),
  ])
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <IssueHeader :proj-status="currentProject?.status" />

      <QuerySection
        v-if="['업무', '(업무)'].includes(route.name as string)"
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
      />

      <IssueTable
        v-if="route.name === '(업무)'"
        ref="issueListRef"
        :issue-list="issueList as Issue[]"
        :search-projects="allReadableProjects"
        :status-list="statusList"
        :tracker-list="trackerList"
        :priority-list="priorityList"
        :get-issues="getIssues"
        :get-users="getUsers"
        :get-versions="getVersions"
        @filter-submit="filterSubmit"
        @page-select="pageSelect"
      />

      <IssueDetail
        v-if="route.name === '(업무) - 보기' && issue"
        :current-project="currentProject as IssueProject"
        :issue="issue"
        :all-readable-projects="allReadableProjects"
        :my-projects="myProjects"
        :status-list="statusList"
        :priority-list="priorityList"
        :issue-comment-list="issueCommentList"
        @on-submit="onSubmit"
      />

      <IssueForm
        v-if="route.name === '(업무) - 추가'"
        :current-project="currentProject as IssueProject"
        :my-projects="myProjects"
        :status-list="statusList"
        :priority-list="priorityList"
        :get-issues="getIssues"
        @on-submit="onSubmit"
        @close-form="router.push({ name: '(업무)' })"
      />

      <IssueReport v-if="route.name === '(업무) - 보고서'" />
    </template>

    <template v-slot:aside>
      <SavedQueryAside
        target-type="issue"
        :active-query-id="activeQueryId"
        :can-project-pub-query="canPubQuery"
        @on-query-click="onQueryClick"
        @on-reset-query="onResetQuery"
      />
      <IssueItemAside
        v-if="route.name === '(업무) - 보기'"
        :watchers="issue?.watchers"
        :issue="issue as any"
      />
    </template>
  </ContentBody>
</template>
