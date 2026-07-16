import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import type {
  CodeValue,
  Issue,
  IssueCategory,
  IssueComment,
  IssueFilter,
  IssueRelation,
  IssueStatus,
  Tracker,
} from '@/store/types/work_issue.ts'

const workStore = useWork()
const logStore = useLogging()

export const useIssue = defineStore('issue', () => {
  // issue states & getters
  const issue = ref<Issue | null>(null)
  const issueList = ref<Issue[]>([])
  const issueCount = ref<number>(0)
  const issueFilter = ref<IssueFilter>({})

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

  const fetchAllIssueList = (project?: string, closed = '0') =>
    api
      .get(`/issue/?project__slug=${project ?? ''}&status__closed=${closed}&limit=1000`)
      .then(res => (allIssueList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchIssueList = async (payload: IssueFilter) => {
    issueFilter.value = payload
    const params = new URLSearchParams()
    params.append('page', String(payload.page ?? 1))

    const paramMap: Record<string, string> = {
      project: 'project__slug',
      project__search: 'project__search',
      project__exclude: 'project__exclude',
      status: 'status',
      status__closed: 'status__closed',
      status__exclude: 'status__exclude',
      tracker: 'tracker',
      tracker__exclude: 'tracker__exclude',
      category: 'category',
      category__exclude: 'category__exclude',
      category__isnull: 'category__isnull',
      is_private: 'is_private',
      watcher: 'watcher',
      watcher__exclude: 'watcher__exclude',
      author: 'creator',
      author__exclude: 'creator__exclude',
      assignee: 'assigned_to',
      assignee__exclude: 'assigned_to__exclude',
      assignee__isnull: 'assigned_to__isnull',
      version: 'fixed_version',
      version__exclude: 'fixed_version__exclude',
      version__isnull: 'fixed_version__isnull',
      id: 'id',
      id__gte: 'id__gte',
      id__lte: 'id__lte',
      id__between: 'id__between',
      id__any: 'id__any',
      done_ratio: 'done_ratio',
      done_ratio__gte: 'done_ratio__gte',
      done_ratio__lte: 'done_ratio__lte',
      done_ratio__between: 'done_ratio__between',
      done_ratio__isnull: 'done_ratio__isnull',
      parent: 'parent',
      parent__subject: 'parent__subject',
      parent__isnull: 'parent__isnull',
      parent_issue: 'parent_issue',
      follows_issue: 'follows_issue',
      precedes_issue: 'precedes_issue',
    }

    Object.entries(payload).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '' || key === 'page') return
      const apiParam = paramMap[key] || key
      params.append(apiParam, String(value))
    })

    return await api
      .get(`/issue/?${params.toString()}`)
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
        await fetchIssueList(issueFilter.value)
        await logStore.fetchIssueLogList({ issue: res.data.pk })
        message()
        return res.data
      })
      .catch(err => errorHandle(err.response.data))

  const updateIssue = (pk: number, payload: any) =>
    api
      .put(`/issue/${pk}/`, payload, config_headers)
      .then(async () => {
        await fetchIssue(pk)
        await fetchIssueList(issueFilter.value)
        await logStore.fetchIssueLogList({ issue: pk })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchIssue = (pk: number, payload: any) =>
    api
      .patch(`/issue/${pk}/`, payload, config_headers)
      .then(async () => {
        await fetchIssue(pk)
        await fetchIssueList(issueFilter.value)
        await logStore.fetchIssueLogList({ issue: pk })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const watchIssue = (pk: number) =>
    api
      .post(`/issue/${pk}/toggle_watch/`, {}, config_headers)
      .then(async () => {
        await fetchIssue(pk)
        await fetchIssueList(issueFilter.value)
        await logStore.fetchIssueLogList({ issue: pk })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteIssue = (pk: number) =>
    api
      .delete(`/issue/${pk}/`)
      .then(async () => {
        await fetchIssueList(issueFilter.value)
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

  const createIssueRelation = (payload: any) =>
    api
      .post(`/issue-relation/`, payload)
      .then(async res => {
        await fetchIssue(res.data.source.pk)
        await fetchIssueList(issueFilter.value)
        await logStore.fetchIssueLogList({ issue: res.data.source.pk })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateIssueRelation = (pk: number, payload: IssueRelation) =>
    api
      .put(`/issue-relation/${pk}/`, payload)
      .then(async res => {
        await fetchIssue(res.data.issue)
        await fetchIssueList(issueFilter.value)
        await logStore.fetchIssueLogList({ issue: res.data.issue })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteIssueRelation = (pk: number, issue: number) =>
    api
      .delete(`/issue-relation/${pk}/`)
      .then(async () => {
        await fetchIssue(issue)
        await fetchIssueList(issueFilter.value)
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

  // code-priority states & getters
  const priorityList = ref<CodeValue[]>([])

  const fetchPriorityList = () =>
    api
      .get(`/code-priority/`)
      .then(res => (priorityList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  return {
    issue,
    issueList,
    issueCount,
    issueFilter,
    issueNums,
    getIssues,
    issueNumByMember,
    fetchIssueByMember,
    issuePages,
    fetchIssue,
    removeIssue,
    allIssueList,
    fetchAllIssueList,
    fetchIssueList,
    createIssue,
    updateIssue,
    patchIssue,
    watchIssue,
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

    priorityList,
    fetchPriorityList,
  }
})
