import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import type { SimpleProject } from '@/store/types/work_project.ts'
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

export const useIssue = defineStore('issue', () => {
  const workStore = useWork()
  const logStore = useLogging()

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
      .catch(err => errorHandle(err))

  const fetchIssue = async (pk: number) => {
    try {
      const res = await api.get(`/issue/${pk}/`)
      issue.value = res.data
      return { pk: res.data.pk, project: res.data.project.slug }
    } catch (err: unknown) {
      errorHandle(err)
      return null
    }
  }

  const fetchIssueDetail = async (pk: number): Promise<Issue | null> => {
    try {
      const res = await api.get(`/issue/${pk}/`)
      return res.data
    } catch (err: unknown) {
      errorHandle(err)
      return null
    }
  }

  const removeIssue = () => (issue.value = null)

  const cachedProject = ref<string>('')

  const fetchAllIssueList = (project?: string, closed = '0', force = false) => {
    const currentKey = `${project ?? 'global'}_${closed}`
    if (!force && cachedProject.value === currentKey && allIssueList.value.length > 0) {
      return Promise.resolve()
    }
    return api
      .get('/issue/', {
        params: {
          ...(project ? { project__slug: project } : {}),
          ...(closed !== '' ? { status__closed: closed } : {}),
          limit: 1000,
        },
      })
      .then(res => {
        allIssueList.value = res.data.results
        cachedProject.value = currentKey
      })
      .catch(err => errorHandle(err))
  }

  const fetchIssueList = async (payload: IssueFilter) => {
    issueFilter.value = { ...payload }
    const params = new URLSearchParams()
    params.append('page', String(payload.page ?? 1))
    if (payload.limit) params.append('limit', String(payload.limit))

    const paramMap: Record<string, string> = {
      project: 'project__slug',
      project__search: 'project__search',
      project__exclude: 'project__exclude',
      project_status: 'project_status',
      project_status__exclude: 'project_status__exclude',
      sub_project: 'sub_project',
      sub_project__exclude: 'sub_project__exclude',
      sub_project__isnull: 'sub_project__isnull',
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
      updater: 'updater',
      updater__exclude: 'updater__exclude',
      last_updater: 'last_updater',
      last_updater__exclude: 'last_updater__exclude',
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
      subject: 'subject',
      subject__exclude: 'subject__exclude',
      description: 'description',
      description__exclude: 'description__exclude',
      comment: 'comment',
      comment__exclude: 'comment__exclude',
      any_searchable: 'any_searchable',
      any_searchable__exclude: 'any_searchable__exclude',
      file: 'file',
      file__exclude: 'file__exclude',
      file_desc: 'file_desc',
      file_desc__exclude: 'file_desc__exclude',
      creator_role: 'creator_role',
      creator_role__exclude: 'creator_role__exclude',
      assignee_role: 'assignee_role',
      assignee_role__exclude: 'assignee_role__exclude',
      version_date: 'version_date',
      version_date__gte: 'version_date__gte',
      version_date__lte: 'version_date__lte',
      version_date__between: 'version_date__between',
      version_date__isnull: 'version_date__isnull',
      version_status: 'version_status',
      version_status__exclude: 'version_status__exclude',
      created: 'created',
      created__gte: 'created__gte',
      created__lte: 'created__lte',
      created__between: 'created__between',
      updated: 'updated',
      updated__gte: 'updated__gte',
      updated__lte: 'updated__lte',
      updated__between: 'updated__between',
      start_date: 'start_date',
      start_date__gte: 'start_date__gte',
      start_date__lte: 'start_date__lte',
      start_date__between: 'start_date__between',
      due_date: 'due_date',
      due_date__gte: 'due_date__gte',
      due_date__lte: 'due_date__lte',
      due_date__between: 'due_date__between',
      due_date__isnull: 'due_date__isnull',
      parent: 'parent',
      parent__exclude: 'parent__exclude',
      parent__contains: 'parent__contains',
      parent__isnull: 'parent__isnull',
      parent_issue: 'parent_issue',
      parent_issue__exclude: 'parent_issue__exclude',
      parent_issue__contains: 'parent_issue__contains',
      parent_issue__isnull: 'parent_issue__isnull',
      follows_issue: 'follows_issue',
      follows_issue__exclude: 'follows_issue__exclude',
      follows_issue__isnull: 'follows_issue__isnull',
      precedes_issue: 'precedes_issue',
      precedes_issue__exclude: 'precedes_issue__exclude',
      precedes_issue__isnull: 'precedes_issue__isnull',
    }

    Object.entries(payload).forEach(([key, value]) => {
      if (
        value === undefined ||
        value === null ||
        value === '' ||
        key === 'page' ||
        key === 'limit'
      )
        return
      const apiParam = paramMap[key] || key
      params.append(apiParam, String(value))
    })

    return await api
      .get(`/issue/?${params.toString()}`)
      .then(res => {
        issueList.value = res.data.results
        issueCount.value = res.data.count
      })
      .catch(err => errorHandle(err))
  }

  const getRequestConfig = (payload: FormData | Record<string, unknown>) =>
    payload instanceof FormData ? { headers: { 'Content-Type': 'multipart/form-data' } } : undefined

  const refreshActiveIssueIfOpen = async (fallbackPk?: number) => {
    const activePk = issue.value?.pk
    const targetPk = activePk ?? fallbackPk
    if (activePk && targetPk) {
      await Promise.all([fetchIssue(activePk), logStore.fetchIssueLogList({ issue: activePk })])
    }
  }

  const createIssue = (payload: FormData | Record<string, unknown>) =>
    api
      .post(`/issue/`, payload, getRequestConfig(payload))
      .then(async res => {
        cachedProject.value = ''
        await fetchIssue(res.data.pk)
        await fetchIssueList(issueFilter.value)
        await logStore.fetchIssueLogList({ issue: res.data.pk })
        await fetchIssueByMember()
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateIssue = (pk: number, payload: FormData | Record<string, unknown>) =>
    api
      .put(`/issue/${pk}/`, payload, getRequestConfig(payload))
      .then(async res => {
        cachedProject.value = ''
        await fetchIssue(pk)
        await fetchIssueList(issueFilter.value)
        await logStore.fetchIssueLogList({ issue: pk })
        await fetchIssueByMember()
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchIssue = (pk: number, payload: FormData | Record<string, unknown>) =>
    api
      .patch(`/issue/${pk}/`, payload, getRequestConfig(payload))
      .then(async () => {
        cachedProject.value = ''
        await refreshActiveIssueIfOpen()
        await fetchIssueList(issueFilter.value)
        await fetchIssueByMember()
        message()
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const watchIssue = (pk: number) =>
    api
      .post(`/issue/${pk}/toggle_watch/`, {})
      .then(async () => {
        await refreshActiveIssueIfOpen()
        await fetchIssueList(issueFilter.value)
        message()
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const deleteIssue = (pk: number) =>
    api
      .delete(`/issue/${pk}/`)
      .then(async () => {
        cachedProject.value = ''
        if (issue.value?.pk === pk) {
          issue.value = null
        } else {
          await refreshActiveIssueIfOpen()
        }
        await fetchIssueList(issueFilter.value)
        await fetchIssueByMember()
        message('warning', '알림!', '해당 업무가 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  // issue-relations states & getters
  const issueRelation = ref<IssueRelation | null>(null)
  const issueRelationList = ref<IssueRelation[]>([])

  const fetchIssueRelation = (pk: number) =>
    api
      .get(`/issue-relation/${pk}/`)
      .then(res => (issueRelation.value = res.data))
      .catch(err => errorHandle(err))

  const fetchIssueRelationList = (payload: { issue?: number; source?: number }) =>
    api
      .get('/issue-relation/', {
        params: {
          ...(payload.source || payload.issue ? { source: payload.source ?? payload.issue } : {}),
        },
      })
      .then(res => (issueRelationList.value = res.data.results))
      .catch(err => errorHandle(err))

  const createIssueRelation = (payload: {
    source: number | null
    target: number | null
    delay?: number | null
  }) =>
    api
      .post(`/issue-relation/`, payload)
      .then(async res => {
        const targetRefreshPk = issue.value?.pk ?? res.data.source?.pk
        if (targetRefreshPk) {
          await Promise.all([
            fetchIssue(targetRefreshPk),
            logStore.fetchIssueLogList({ issue: targetRefreshPk }),
          ])
        }
        await fetchIssueList(issueFilter.value)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateIssueRelation = (pk: number, payload: IssueRelation) =>
    api
      .put(`/issue-relation/${pk}/`, payload)
      .then(async res => {
        const targetRefreshPk = issue.value?.pk ?? res.data.source?.pk
        if (targetRefreshPk) {
          await Promise.all([
            fetchIssue(targetRefreshPk),
            logStore.fetchIssueLogList({ issue: targetRefreshPk }),
          ])
        }
        await fetchIssueList(issueFilter.value)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteIssueRelation = (pk: number, issuePk: number) =>
    api
      .delete(`/issue-relation/${pk}/`)
      .then(async () => {
        const targetRefreshPk = issue.value?.pk ?? issuePk
        await Promise.all([
          fetchIssue(targetRefreshPk),
          logStore.fetchIssueLogList({ issue: targetRefreshPk }),
        ])
        await fetchIssueList(issueFilter.value)
        message('warning', '알림!', '해당 업무와 연결 관계가 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  // issue-comment states & getters
  const issueComment = ref<IssueComment | null>(null)
  const issueCommentList = ref<IssueComment[]>([])

  const fetchIssueComment = (pk: number) =>
    api
      .get(`/issue-comment/${pk}/`)
      .then(res => (issueComment.value = res.data))
      .catch(err => errorHandle(err))

  const fetchIssueCommentList = async (payload: {
    issue?: number
    user?: number
    creator?: number
  }) => {
    const params: Record<string, number> = {}
    if (payload.issue) params.issue = payload.issue
    const creatorId = payload.creator ?? payload.user
    if (creatorId) params.creator = creatorId

    return await api
      .get('/issue-comment/', { params })
      .then(res => (issueCommentList.value = res.data.results))
      .catch(err => errorHandle(err))
  }

  const createIssueComment = (payload: { issue: number; content: string; is_private?: boolean }) =>
    api
      .post('/issue-comment/', payload)
      .then(async res => {
        await Promise.all([
          fetchIssueCommentList({ issue: payload.issue }),
          logStore.fetchIssueLogList({ issue: payload.issue }),
        ])
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchIssueComment = (payload: { pk?: number; issue?: number; [key: string]: unknown }) =>
    api
      .patch(`/issue-comment/${payload.pk}/`, payload)
      .then(async res => {
        if (payload.pk) await fetchIssueComment(payload.pk)
        await fetchIssueCommentList({ issue: payload.issue })
        await logStore.fetchIssueLogList({ issue: payload.issue })
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteIssueComment = (pk: number, issuePk?: number) =>
    api
      .delete(`/issue-comment/${pk}/`)
      .then(async () => {
        if (issuePk) {
          await fetchIssueCommentList({ issue: issuePk })
          await logStore.fetchIssueLogList({ issue: issuePk })
        }
        message('warning', '알림!', '댓글이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

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

  const fetchTrackerList = (force = false) => {
    if (!force && trackerList.value.length > 0) return Promise.resolve()
    return api
      .get('/tracker/', { params: { limit: 500 } })
      .then(res => (trackerList.value = res.data.results))
      .catch(err => errorHandle(err))
  }

  const fetchTrackerSummary = async (projId?: number) => {
    const url = `/issue-by-tracker-summary/?projects=${projId ?? ''}`
    return await api
      .get(url)
      .then(res => (trackerSum.value = res.data.results))
      .catch(err => errorHandle(err))
  }

  // category states & getters
  const category = ref<IssueCategory | null>()
  const categoryList = ref<IssueCategory[]>([])
  const categoryCacheMap = ref<Record<string, IssueCategory[]>>({})

  const removeCategory = () => (category.value = null)
  const fetchCategory = (pk: number) =>
    api
      .get(`/issue-category/${pk}/`)
      .then(res => (category.value = res.data))
      .catch(err => errorHandle(err))

  const fetchCategoryList = (project = '', force = false) => {
    const cacheKey = project || 'global'

    // 1. 만약 'global' 캐시가 이미 존재하고 특정 project 조회가 들어온 경우, 전역 캐시에서 해당 프로젝트 항목 바로 추출
    if (!force && project && categoryCacheMap.value['global']) {
      categoryList.value = categoryCacheMap.value['global'].filter(
        c => c.project && c.project.slug === project,
      )
      return Promise.resolve()
    }

    // 2. 해당 cacheKey('global' 또는 project slug)의 캐시가 이미 존재하면 즉시 반환
    if (!force && categoryCacheMap.value[cacheKey]) {
      categoryList.value = categoryCacheMap.value[cacheKey]
      return Promise.resolve()
    }

    return api
      .get('/issue-category/', {
        params: {
          ...(project ? { project__slug: project } : {}),
          limit: 500,
        },
      })
      .then(async res => {
        categoryCacheMap.value[cacheKey] = res.data.results
        categoryList.value = res.data.results
      })
      .catch(err => errorHandle(err))
  }

  const createCategory = (
    payload: Partial<Omit<IssueCategory, 'project'>> & {
      project?: number | string | SimpleProject
    },
  ) =>
    api
      .post(`/issue-category/`, payload)
      .then(async res => {
        categoryCacheMap.value = {}
        await fetchCategory(res.data.pk)
        await fetchCategoryList(res.data.project.slug, true)
        if (workStore.currentProject?.slug === res.data.project.slug) {
          await workStore.fetchIssueProject(res.data.project.slug)
        }
        message()
        return res.data.pk
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateCategory = (
    payload: Partial<Omit<IssueCategory, 'project'>> & {
      project?: number | string | SimpleProject
    },
  ) =>
    api
      .put(`/issue-category/${payload.pk}/`, payload)
      .then(async res => {
        categoryCacheMap.value = {}
        await fetchCategory(res.data.pk)
        if (res.data.project?.slug) {
          await fetchCategoryList(res.data.project.slug, true)
          if (workStore.currentProject?.slug === res.data.project.slug) {
            await workStore.fetchIssueProject(res.data.project.slug)
          }
        }
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteCategory = (pk: number, project = '') =>
    api
      .delete(`/issue-category/${pk}/`)
      .then(async () => {
        categoryCacheMap.value = {}
        await fetchCategoryList(project, true)
        if (project && workStore.currentProject?.slug === project) {
          await workStore.fetchIssueProject(project)
        }
        message('warning', '알림!', '해당 업무 범주가 삭제되었습니다!')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  // status states & getters
  const statusList = ref<IssueStatus[]>([])

  const fetchStatusList = (force = false) => {
    if (!force && statusList.value.length > 0) return Promise.resolve()
    return api
      .get('/issue-status/', { params: { limit: 200 } })
      .then(res => (statusList.value = res.data.results))
      .catch(err => errorHandle(err))
  }

  // code-priority states & getters
  const priorityList = ref<CodeValue[]>([])

  const fetchPriorityList = (force = false) => {
    if (!force && priorityList.value.length > 0) return Promise.resolve()
    return api
      .get('/code-priority/', { params: { limit: 200 } })
      .then(res => (priorityList.value = res.data.results))
      .catch(err => errorHandle(err))
  }

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
    fetchIssueDetail,
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
    createIssueComment,
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
