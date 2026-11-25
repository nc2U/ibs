<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { ALL_ISSUE_COLUMNS, DEFAULT_ISSUE_COLUMNS } from '@/views/_Work/Manages/Issues/constants'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import { useIssue } from '@/store/pinia/work_issue'
import { useIssueFilter } from '@/store/pinia/work_issue_filter'
import { useLogging } from '@/store/pinia/work_logging'
import { usePerms } from '@/composables/usePerms'
import { useRoute, useRouter } from 'vue-router'
import { useTableColumns } from '@/composables/useTableColumns'
import type { IssueProject } from '@/store/types/work_project'
import type { Issue, IssueFilter } from '@/store/types/work_issue'
import type { CustomQuery } from '@/store/types/work_inform'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import IssueHeader from '@/views/_Work/Manages/Issues/automics/IssueHeader.vue'
import IssueTable from '@/views/_Work/Manages/Issues/components/IssueTable.vue'
import IssueKanban from '@/views/_Work/Manages/Issues/components/IssueKanban.vue'
import IssueDetail from '@/views/_Work/Manages/Issues/components/IssueDetail.vue'
import IssueForm from '@/views/_Work/Manages/Issues/components/IssueForm.vue'
import IssueReport from '@/views/_Work/Manages/Issues/components/IssueReport.vue'
import IssueItemAside from '@/views/_Work/Manages/Issues/components/aside/IssueItemAside.vue'
import QuerySection from '@/views/_Work/Manages/Issues/components/QuerySection.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'
import ColumnSelector from '@/components/ColumnSelector/Index.vue'
import Loading from '@/components/Loading/Index.vue'

const props = defineProps<{
  navMenu?: string[]
  currentProject?: IssueProject | null
}>()

const viewMode = ref<'list' | 'kanban'>(
  (localStorage.getItem('ibs_work_issue_view_mode') as 'list' | 'kanban') || 'list',
)
const onViewModeChange = (mode: 'list' | 'kanban') => {
  viewMode.value = mode
  localStorage.setItem('ibs_work_issue_view_mode', mode)
  page.value = 1
  const payload: IssueFilter = {
    ...listFilter.value,
    page: 1,
    limit: mode === 'kanban' ? 200 : undefined,
  }
  listFilter.value = payload
  issueStore.fetchIssueList(payload)
}

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)
const toggle = () => cBody.value?.toggle()
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
const currentProject = computed<IssueProject | null>(
  () => props.currentProject || workStore.currentProject,
)

const issueStore = useIssue()
const issue = computed<Issue | null>(() => issueStore.issue)
const issueList = computed(() => issueStore.issueList)

const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => issueStore.trackerList)
const priorityList = computed(() => issueStore.priorityList)
const categoryList = computed(() => issueStore.categoryList)
const getIssues = computed(() => issueStore.getIssues)

const querySectionRef = ref<InstanceType<typeof QuerySection> | null>(null)
const issueFilterStore = useIssueFilter()
const activeQueryId = computed(() => issueFilterStore.activeQueryId)

const onQueryClick = (query: CustomQuery) => {
  querySectionRef.value?.applyQuery(query)
}

const onResetQuery = () => {
  querySectionRef.value?.resetFilter()
}

const onSubmit = async (payload: Record<string, unknown>, done?: (ok: boolean) => void) => {
  const { pk, commentOnly, ...getData } = payload
  const issuePk = typeof pk === 'number' ? pk : null

  // 댓글 작성 전용 권한자(issue.comment_create만 보유)는 직접 댓글 엔드포인트 호출
  if (issuePk && commentOnly) {
    const content = String(getData.comment_content ?? '').trim()
    if (!content) {
      done?.(false)
      return
    }
    const createdComment = await issueStore.createIssueComment({
      issue: issuePk,
      content,
      is_private: Boolean(getData.comment_is_private),
    })
    done?.(Boolean(createdComment))
    return
  }

  const form = new FormData()

  const nullableClearable = [
    'parent',
    'assigned_to',
    'fixed_version',
    'category',
    'due_date',
    'expected_duration',
  ]

  const currentParentPk = issue.value?.parent?.pk ?? null

  for (const key in getData) {
    // 수정 모드에서 parent 값이 기존과 동일하면 불필요한 parent 필드 전송을 생략 (sub_manage 오판 방지)
    if (issuePk && key === 'parent') {
      const nextParent = getData.parent === '' ? null : (getData.parent ?? null)
      if (String(nextParent ?? '') === String(currentParentPk ?? '')) continue
    }
    if (
      issuePk &&
      nullableClearable.includes(key) &&
      (getData[key] === null || getData[key] === '')
    ) {
      form.append(key, '')
    } else if (key === 'watchers' && Array.isArray(getData[key])) {
      getData[key].forEach(val => form.append(key, String(val)))
    } else if ((key === 'files' || key === 'links') && Array.isArray(getData[key])) {
      getData[key].forEach(val => form.append(key, JSON.stringify(val)))
    } else if (key === 'newFiles' && Array.isArray(getData[key])) {
      ;(getData[key] as { file: string | Blob; description?: string }[]).forEach(val => {
        form.append('new_files', val.file)
        form.append('descriptions', val.description ?? '')
      })
    } else if (key === 'newLinks' && Array.isArray(getData[key])) {
      ;(getData[key] as { link?: string; name?: string }[]).forEach(val => {
        if (val.link && val.link.trim()) {
          form.append('newLinks', val.link.trim())
          form.append('newLinkNames', val.name ?? '')
        }
      })
    } else if (getData[key] !== null && getData[key] !== undefined) {
      form.append(key, getData[key] as string | Blob)
    }
  }

  if (issuePk) {
    const updated = await issueStore.updateIssue(issuePk, form)
    done?.(Boolean(updated))
  } else {
    const newIssue = await issueStore.createIssue(form)
    if (newIssue && newIssue.pk) {
      done?.(true)
      const projSlug = (route.params.projId as string) || newIssue.project?.slug || newIssue.project

      // 하위 업무를 생성한 경우(부모 ID가 존재하면) 부모 상세 페이지로 복귀
      const parentId =
        (route.query.parent as string) ||
        (typeof newIssue.parent === 'object' && newIssue.parent !== null
          ? newIssue.parent.pk
          : newIssue.parent)

      if (parentId) {
        await router.replace({
          name: '(업무) - 보기',
          params: { projId: projSlug, issueId: String(parentId) },
        })
      } else {
        await router.replace({
          name: '(업무) - 보기',
          params: { projId: projSlug, issueId: String(newIssue.pk) },
        })
      }
    } else {
      done?.(false)
    }
  }
}

const projId = computed(() => (route.params.projId as string) ?? '')
const issueId = computed(() => (route.params.issueId as string) ?? '')

const listFilter = ref<IssueFilter>(issueFilterStore.buildFilterPayload(projId.value))
const page = ref(1)

const filterSubmit = (payload: IssueFilter) => {
  page.value = 1
  const enriched: IssueFilter = {
    ...payload,
    limit: viewMode.value === 'kanban' ? 200 : undefined,
  }
  listFilter.value = enriched
  issueStore.fetchIssueList(enriched)
}
const pageSelect = (p: number) => {
  page.value = p
  listFilter.value.page = p
  issueStore.fetchIssueList(listFilter.value)
}

watch(
  () => projId.value,
  async nVal => {
    if (nVal && nVal.length > 0) {
      page.value = 1
      const payload: IssueFilter = {
        ...issueFilterStore.resetFilter(nVal as string),
        limit: viewMode.value === 'kanban' ? 200 : undefined,
      }
      listFilter.value = payload
      await Promise.all([
        issueStore.fetchIssueList(payload),
        issueStore.fetchCategoryList(nVal, true),
        workStore.fetchVersionList({ project: nVal }),
        issueStore.fetchAllIssueList(nVal, '0', true),
      ])
    }
  },
)
const logStore = useLogging()
watch(
  () => route.params.issueId,
  async nVal => {
    if (nVal) {
      loading.value = true
      try {
        await Promise.all([
          issueStore.fetchIssue(Number(nVal)),
          logStore.fetchIssueLogList({ issue: Number(nVal) }),
        ])
      } catch (err) {
        console.error('Failed to load issue detail:', err)
      } finally {
        loading.value = false
      }
    } else issueStore.removeIssue()
  },
)

// Columns Selector Start
const { selectedColumns } = useTableColumns(
  'project-issue-table-columns',
  ALL_ISSUE_COLUMNS,
  DEFAULT_ISSUE_COLUMNS,
)
// Columns Selector End!

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  try {
    if (workStore.currentProject?.slug !== projId.value) {
      await workStore.fetchIssueProject(projId.value)
    }

    const tasks: Promise<unknown>[] = [
      issueStore.fetchCategoryList(projId.value),
      workStore.fetchVersionList({ project: projId.value }),
      issueStore.fetchAllIssueList(projId.value),
    ]
    if (issueId.value) {
      tasks.push(
        issueStore.fetchIssue(Number(issueId.value)),
        logStore.fetchIssueLogList({ issue: Number(issueId.value) }),
      )
    }
    await Promise.all(tasks)
  } catch (err) {
    console.error('Failed to load project issues data:', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :nav-menu="navMenu">
    <template v-slot:default>
      <IssueHeader
        :proj-status="currentProject?.status"
        :view-mode="viewMode"
        @update:view-mode="onViewModeChange"
      />

      <QuerySection
        v-if="route.name === '(업무)'"
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
        v-if="route.name === '(업무)' && viewMode === 'list'"
        :issue-list="issueList as Issue[]"
        :columns="selectedColumns"
        :page="page"
        @page-select="pageSelect"
      />

      <IssueKanban
        v-if="route.name === '(업무)' && viewMode === 'kanban'"
        :issue-list="issueList as Issue[]"
        :status-list="statusList"
        :priority-list="priorityList"
        :tracker-list="trackerList"
      />

      <IssueDetail
        v-if="route.name === '(업무) - 보기' && issue"
        :key="issue.pk"
        :current-project="currentProject as IssueProject"
        :issue="issue"
        :my-projects="myProjects"
        :status-list="statusList"
        :priority-list="priorityList"
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
        v-if="route.name === '(업무)'"
        target-type="issue"
        :active-query-id="activeQueryId ?? undefined"
        :can-project-pub-query="canPubQuery"
        @on-query-click="onQueryClick"
        @on-reset-query="onResetQuery"
      />
      <IssueItemAside
        v-if="route.name === '(업무) - 보기' && issue"
        :watchers="issue.watchers"
        :issue="issue"
      />
    </template>
  </ContentBody>
</template>
