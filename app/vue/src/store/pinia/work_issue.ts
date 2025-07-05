import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import type {
  CodeValue,
  GanttProject,
  Gantts,
  Issue,
  IssueCategory,
  IssueComment,
  IssueFilter,
  IssueRelation,
  IssueStatus,
  TimeEntry,
  TimeEntryFilter,
  Tracker,
} from '@/store/types/work_issue.ts'

const workStore = useWork()
const logStore = useLogging()

export const useIssue = defineStore('issue', () => {
  // issue states & getters
  const issue = ref<Issue | null>(null)
  const issueList = ref<Issue[]>([])
  const issueCount = ref<number>(0)

  const issuePages = (itemPerPage: number) => Math.ceil(issueCount.value / itemPerPage)

  const allIssueList = ref<Issue[]>([])
  const getIssues = computed(() =>
    allIssueList.value.map(i => ({
      value: i.pk,
      label: i.subject,
    })),
  )

  const issueNums = computed(() => issueList.value.map(i => i.pk) as number[])

  const issueNumByMember = ref<{
    open_charged: number
    closed_charged: number
    all_charged: number
    open_created: number
    closed_created: number
    all_created: number
  }>({
    open_charged: 0,
    closed_charged: 0,
    all_charged: 0,
    open_created: 0,
    closed_created: 0,
    all_created: 0,
  })

  const fetchIssueByMember = (userId?: string) =>
    api
      .get(`/issue-by-member/?user=${userId ?? ''}`)
      .then(res => (issueNumByMember.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchIssue = async (pk: number) => {
    try {
      const res = await api.get(`/issue/${pk}/`)
      issue.value = res.data
      return { pk: res.data.pk, project: res.data.project.slug }
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const removeIssue = () => (issue.value = null)

  const fetchAllIssueList = (project?: string) =>
    api
      .get(`/issue/?project__slug=${project ?? ''}`)
      .then(res => (allIssueList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchIssueList = async (payload: IssueFilter) => {
    let url = `/issue/?page=${payload.page ?? 1}`
    if (payload.status__closed) url += `&status__closed=${payload.status__closed}`
    if (payload.status) url += `&status=${payload.status}`
    if (payload.status__exclude) url += `&status__exclude=${payload.status__exclude}`
    if (payload.project) url += `&project__slug=${payload.project}`
    if (payload.project__search) url += `&project__search=${payload.project__search}`
    if (payload.project__exclude) url += `&project__exclude=${payload.project__exclude}`
    if (payload.tracker) url += `&tracker=${payload.tracker}`
    if (payload.tracker__exclude) url += `&tracker__exclude=${payload.tracker__exclude}`
    if (payload.author) url += `&creator=${payload.author}`
    if (payload.author__exclude) url += `&creator__exclude=${payload.author__exclude}`
    if (payload.assignee) url += `&assigned_to=${payload.assignee}`
    if (payload.assignee__exclude) url += `&assigned_to__exclude=${payload.assignee__exclude}`
    if (payload.assignee__isnull) url += `&assigned_to__isnull=${payload.assignee__isnull}`
    if (payload.version) url += `&fixed_version=${payload.version}`
    if (payload.version__exclude) url += `&fixed_version__exclude=${payload.version__exclude}`
    if (payload.version__isnull) url += `&fixed_version__isnull=${payload.version__isnull}`
    if (payload.parent) url += `&parent=${payload.parent}`
    if (payload.parent__subject) url += `&parent__subject=${payload.parent__subject}`
    if (payload.parent__isnull) url += `&parent__isnull=${payload.parent__isnull}`

    return await api
      .get(url)
      .then(res => {
        issueList.value = res.data.results
        issueCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const config_headers = { headers: { 'Content-Type': 'multipart/form-data' } }

  const createIssue = (payload: any) =>
    api
      .post(`/issue/`, payload, config_headers)
      .then(async res => {
        await fetchIssue(res.data.pk)
        await fetchIssueList({ status__closed: '0', project: res.data.project.slug })
        await logStore.fetchIssueLogList({ issue: res.data.pk })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateIssue = (pk: number, payload: any) =>
    api
      .put(`/issue/${pk}/`, payload, config_headers)
      .then(async () => {
        await fetchIssue(pk)
        await logStore.fetchIssueLogList({ issue: pk })
        await fetchTimeEntryList({ issue: pk, ordering: 'pk' })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchIssue = (pk: number, payload: any) =>
    api
      .patch(`/issue/${pk}/`, payload, config_headers)
      .then(async () => {
        await fetchIssue(pk)
        await logStore.fetchIssueLogList({ issue: pk })
        await fetchTimeEntryList({ issue: pk, ordering: 'pk' })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteIssue = (pk: number) =>
    api
      .delete(`/issue/${pk}/`)
      .then(async () => {
        await fetchIssueList({})
        message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // issue-relations states & getters
  const issueRelation = ref<IssueRelation | null>(null)
  const issueRelationList = ref<IssueRelation[]>([])

  const fetchIssueRelation = (pk: number) =>
    api
      .get(`/issue-relation/${pk}/`)
      .then(res => (issueRelation.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchIssueRelationList = (payload: { issue?: number }) =>
    api
      .get(`/issue-relation/?issue=${payload.issue ?? ''}`)
      .then(res => (issueRelationList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createIssueRelation = (payload: IssueRelation) =>
    api
      .post(`/issue-relation/`, payload)
      .then(async res => {
        await fetchIssue(res.data.issue)
        await logStore.fetchIssueLogList({ issue: res.data.issue })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateIssueRelation = (pk: number, payload: IssueRelation) =>
    api
      .put(`/issue-relation/${pk}/`, payload)
      .then(async res => {
        await fetchIssue(res.data.issue)
        await logStore.fetchIssueLogList({ issue: res.data.issue })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteIssueRelation = (pk: number, issue: number) =>
    api
      .delete(`/issue-relation/${pk}/`)
      .then(async () => {
        await fetchIssue(issue)
        await logStore.fetchIssueLogList({ issue })
        message('warning', '알림!', '해당 업무와 연결 관계가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // issue-comment states & getters
  const issueComment = ref<IssueComment | null>(null)
  const issueCommentList = ref<IssueComment[]>([])

  const fetchIssueComment = (pk: number) =>
    api
      .get(`/issue-comment/${pk}/`)
      .then(res => (issueComment.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchIssueCommentList = async (payload: any) => {
    let url = `/issue-comment/?1=1`
    if (payload.issue) url += `&issue=${payload.issue}`
    if (payload.user) url += `&user=${payload.user}`

    return await api
      .get(url)
      .then(res => (issueCommentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const patchIssueComment = (payload: any) =>
    api
      .patch(`/issue-comment/${payload.pk}/`, payload)
      .then(async () => {
        await fetchIssueComment(payload.pk)
        await fetchIssueCommentList({ issue: payload.issue })
        await logStore.fetchIssueLogList({ issue: payload.issue })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteIssueComment = (pk: number, issue?: number) =>
    api
      .delete(`/issue-comment/${pk}/`)
      .then(async () => {
        if (issue) {
          await fetchIssueCommentList({ issue })
          await logStore.fetchIssueLogList({ issue })
        }
        message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // time-entry states & getters
  const timeEntry = ref<TimeEntry | null>(null)
  const timeEntryList = ref<TimeEntry[]>([])
  const timeEntryCount = ref<number>(0)

  const timeEntryPages = (itemsPerPage: number) => Math.ceil(timeEntryCount.value / itemsPerPage)

  const fetchTimeEntry = (pk: number) =>
    api
      .get(`/time-entry/${pk}/`)
      .then(res => (timeEntry.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchTimeEntryList = async (payload: TimeEntryFilter) => {
    let url = `/time-entry/?ordering=${payload.ordering ?? ''}&page=${payload.page ?? 1}`
    if (payload.project) url += `&project__slug=${payload.project}`
    if (payload.project__search) url += `&project__search=${payload.project__search}`
    if (payload.project__exclude) url += `&project__exclude=${payload.project__exclude}`
    if (payload.spent_on) url += `&spent_on=${payload.spent_on}`
    if (payload.from_spent_on) url += `&from_spent_on=${payload.from_spent_on}`
    if (payload.to_spent_on) url += `&to_spent_on=${payload.to_spent_on}`
    if (payload.issue) url += `&issue=${payload.issue}`
    if (payload.issue__keyword) url += `&search=${payload.issue__keyword}`
    if (payload.user) url += `&user=${payload.user}`
    if (payload.user__exclude) url += `&user__exclude=${payload.user__exclude}`
    // if (payload.activity) url += `&activity=${payload.activity}`
    // if (payload.hours) url += `&hours=${payload.hours}`
    // if (payload.from_spent_on) url += `&from_spent_on=${payload.from_spent_on}`
    // if (payload.to_spent_on) url += `&to_spent_on=${payload.to_spent_on}`
    // if (payload.issue__tracker) url += `&issue__tracker=${payload.issue__tracker}`
    // if (payload.issue__parent) url += `&issue__parent=${payload.issue__parent}`
    // if (payload.issue__status) url += `&issue__status=${payload.issue__status}`
    if (payload.version) url += `&issue__fixed_version=${payload.version}`
    if (payload.version__exclude)
      url += `&issue__fixed_version__exclude=${payload.version__exclude}`
    // if (payload.issue__category) url += `&issue__category=${payload.issue__category}`

    return await api
      .get(url)
      .then(res => {
        timeEntryList.value = res.data.results
        timeEntryCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const createTimeEntry = (payload: TimeEntry, ord = '') =>
    api
      .post(`/time-entry/`, payload)
      .then(async res => {
        await fetchTimeEntry(res.data.pk)
        await fetchTimeEntryList({ ordering: ord })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateTimeEntry = (payload: TimeEntry, ord = '') =>
    api
      .put(`/time-entry/${payload.pk}/`, payload)
      .then(async () => {
        await fetchTimeEntry(payload.pk)
        await fetchTimeEntryList({ ordering: ord })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteTimeEntry = (pk: number, ord = '') =>
    api
      .delete(`/time-entry/${pk}/`)
      .then(async () => {
        await fetchTimeEntryList({ ordering: ord })
        message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // tracker states & getters
  const trackerList = ref<Tracker[]>([])
  const getTrackers = computed(() => trackerList.value.map(t => ({ value: t.pk, label: t.name })))
  const trackerSum = ref<
    {
      pk: number
      name: string
      open: number
      closed: number
    }[]
  >([])

  const fetchTrackerList = () =>
    api
      .get(`/tracker/`)
      .then(res => (trackerList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchTrackerSummary = async (projId?: number) => {
    const url = `/issue-by-tracker-summary/?projects=${projId ?? ''}`
    return await api
      .get(url)
      .then(res => (trackerSum.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  // category states & getters
  const category = ref<IssueCategory | null>()
  const categoryList = ref<IssueCategory[]>([])

  const removeCategory = () => (category.value = null)
  const fetchCategory = (pk: number) =>
    api
      .get(`/issue-category/${pk}/`)
      .then(res => (category.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchCategoryList = (project = '') =>
    api
      .get(`/issue-category/?project__slug=${project}`)
      .then(async res => (categoryList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createCategory = (payload: IssueCategory) =>
    api
      .post(`/issue-category/`, payload)
      .then(async res => {
        await fetchCategory(res.data.pk)
        await fetchCategoryList(res.data.project.slug)
        await workStore.fetchIssueProject(res.data.project.slug)
        message()
        return res.data.pk
      })
      .catch(err => errorHandle(err.response.data))

  const updateCategory = (payload: IssueCategory) =>
    api
      .put(`/issue-category/${payload.pk}/`, payload)
      .then(async res => {
        await fetchCategory(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteCategory = (pk: number, project = '') =>
    api
      .delete(`/issue-category/${pk}/`)
      .then(async () => {
        await workStore.fetchVersionList({ project, status: '', exclude: '' })
        await workStore.fetchIssueProject(project)
        message('warning', '알림!', '해당 업무 범주가 삭제되었습니다!')
      })
      .catch(err => errorHandle(err.response.data))

  // status states & getters
  const statusList = ref<IssueStatus[]>([])

  const fetchStatusList = () =>
    api
      .get(`/issue-status/`)
      .then(res => (statusList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // code-activity states & getters
  const activityList = ref<CodeValue[]>([])
  const getActivities = computed(() =>
    activityList.value.map(a => ({ value: a.pk, label: a.name })),
  )

  const fetchActivityList = () =>
    api
      .get(`/code-activity/`)
      .then(res => (activityList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // code-priority states & getters
  const priorityList = ref<CodeValue[]>([])

  const fetchPriorityList = () =>
    api
      .get(`/code-priority/`)
      .then(res => (priorityList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // code-docs-categories
  const codeCategoryList = ref<CodeValue[]>([])

  const fetchCodeCategoryList = () =>
    api
      .get(`/code-docs-category/`)
      .then(res => (codeCategoryList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // Gantt issues
  const ganttIssues = ref<GanttProject[]>([])

  const getBgColor = (ratio: number) => {
    let color = ''
    if (ratio > 80) color = '#C5E1A5'
    else if (ratio >= 60) color = '#DCEDC8'
    else if (ratio >= 40) color = '#F1F8E9'
    else if (ratio >= 20) color = '#FFEBEE'
    else color = '#FFCDD2'
    return color
  }

  const getGantts = computed(() => {
    const gantts = [] as Gantts[][]

    ganttIssues.value.forEach(pj => {
      if (pj.issues.length) {
        gantts.push([
          {
            isProj: true,
            depth: pj.depth,
            name: pj.name,
            start: pj.start_first,
            due: pj.due_last ?? '',
            ganttBarConfig: {
              id: pj.pk,
              label: pj.name,
              immobile: false,
              html: '',
              style: {
                color: '#fff',
              },
            },
          },
        ])

        pj.issues.forEach(issue => {
          gantts.push([
            {
              isProj: false,
              depth: pj.depth,
              name: `${issue.tracker} #${issue.pk}: ${issue.subject}`,
              start: issue.start_date,
              due: issue.due_date ?? '',
              done_ratio: issue.done_ratio,
              ganttBarConfig: {
                id: issue.pk,
                label: `${issue.done_ratio}%`,
                immobile: false,
                html: '',
                style: {
                  background: getBgColor(issue.done_ratio ?? 0),
                },
              },
            },
          ])
        })
      }

      if (pj.sub_projects.length) {
        pj.sub_projects.forEach(sub => {
          gantts.push([
            {
              isProj: true,
              depth: sub.depth,
              name: sub.name,
              start: sub.start_first,
              due: sub.due_last ?? '',
              ganttBarConfig: {
                id: sub.pk,
                label: sub.name,
                immobile: false,
                html: '',
                style: {
                  color: '#fff',
                },
              },
            },
          ])

          sub.issues.forEach(issue => {
            gantts.push([
              {
                isProj: false,
                depth: sub.depth,
                name: `${issue.tracker} #${issue.pk}: ${issue.subject}`,
                start: issue.start_date,
                due: issue.due_date ?? '',
                done_ratio: issue.done_ratio,
                ganttBarConfig: {
                  id: issue.pk,
                  label: `${issue.done_ratio}%`,
                  immobile: false,
                  html: '',
                  style: {
                    background: getBgColor(issue.done_ratio ?? 0),
                  },
                },
              },
            ])
          })
        })
      }
    })

    return gantts
  })

  const fetchGanttIssues = async (proj?: string) =>
    api
      .get(`/gantt-issues/?project=${proj || ''}`)
      .then(res => (ganttIssues.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  return {
    issue,
    issueList,
    issueCount,
    issueNums,
    getIssues,
    issueNumByMember,
    fetchIssueByMember,
    issuePages,
    fetchIssue,
    removeIssue,
    fetchAllIssueList,
    fetchIssueList,
    createIssue,
    updateIssue,
    patchIssue,
    deleteIssue,

    issueRelation,
    issueRelationList,
    fetchIssueRelation,
    fetchIssueRelationList,
    createIssueRelation,
    updateIssueRelation,
    deleteIssueRelation,

    issueComment,
    issueCommentList,
    fetchIssueComment,
    fetchIssueCommentList,
    patchIssueComment,
    deleteIssueComment,

    timeEntry,
    timeEntryList,
    timeEntryCount,
    timeEntryPages,
    fetchTimeEntry,
    fetchTimeEntryList,
    createTimeEntry,
    updateTimeEntry,
    deleteTimeEntry,

    trackerList,
    getTrackers,
    trackerSum,
    fetchTrackerList,
    fetchTrackerSummary,

    category,
    categoryList,
    removeCategory,
    fetchCategory,
    fetchCategoryList,
    createCategory,
    updateCategory,
    deleteCategory,

    statusList,
    fetchStatusList,

    activityList,
    getActivities,
    fetchActivityList,

    priorityList,
    fetchPriorityList,

    codeCategoryList,
    fetchCodeCategoryList,

    ganttIssues,
    getGantts,
    fetchGanttIssues,
  }
})
