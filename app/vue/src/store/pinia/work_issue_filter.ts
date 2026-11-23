import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { IssueFilter } from '@/store/types/work_issue.ts'

type SavedUserFilterVal = number | 'me' | null

interface SavedIssueQuery {
  pk?: number
  filters?: {
    searchCond?: string[]
    cond?: Record<string, string>
    form?: Record<string, string | number | boolean | null | undefined> & {
      watcher?: SavedUserFilterVal
      creator?: SavedUserFilterVal
      author?: SavedUserFilterVal
      updater?: SavedUserFilterVal
      assigned_to?: SavedUserFilterVal
      assignee?: SavedUserFilterVal
      project?: string
    }
    watcher?: SavedUserFilterVal
    creator?: SavedUserFilterVal
    author?: SavedUserFilterVal
    updater?: SavedUserFilterVal
    assigned_to?: SavedUserFilterVal
    assignee?: SavedUserFilterVal
  }
}

export const useIssueFilter = defineStore('issueFilter', () => {
  // 1. 활성화된 필터 조건 및 체크박스 상태
  const searchCond = ref<string[]>(['status'])
  const enabledFields = ref<string[]>(['status'])

  // 2. 연산자 조건 (is, exclude, gte, lte, between, none, any 등)
  const defaultCond: Record<string, string> = {
    status: 'open',
    project: 'is',
    tracker: 'is',
    priority: 'is',
    author: 'is',
    assignee: 'is',
    version: 'is',
    category: 'is',
    done_ratio: 'is',
    is_private: 'is',
    watcher: 'is',
    updater: 'is',
    last_updater: 'is',
    version_status: 'is',
    project_status: 'is',
    sub_project: 'any',
    issue: 'is',
    subject: 'contains',
    description: 'contains',
    comment: 'contains',
    any_searchable: 'contains',
    created: 'is',
    updated: 'is',
    start_date: 'is',
    due_date: 'is',
    file: 'contains',
    file_desc: 'contains',
    creator_role: 'is',
    assignee_role: 'is',
    version_date: 'is',
    follows_issue: 'is',
    precedes_issue: 'is',
    parent_issue: 'is',
    parent: 'is',
  }

  const cond = ref<Record<string, string>>({ ...defaultCond })

  // 3. 폼 필드 입력값
  const defaultForm: IssueFilter & Record<string, unknown> = {
    status__closed: '',
    status: null,
    status__exclude: null,
    project: '',
    project__search: '',
    project__exclude: '',
    tracker: null,
    tracker__exclude: null,
    priority: null,
    priority__exclude: null,
    category: null,
    category__exclude: null,
    category__isnull: '0',
    is_private: null,
    watcher: null,
    watcher__exclude: null,
    done_ratio: null,
    done_ratio__gte: null,
    done_ratio__lte: null,
    done_ratio__between: '',
    done_ratio__between_min: null,
    done_ratio__between_max: null,
    done_ratio__isnull: '0',
    author: null,
    author__exclude: null,
    updater: null,
    updater__exclude: null,
    last_updater: null,
    last_updater__exclude: null,
    assignee: null,
    assignee__exclude: null,
    version: null,
    version__exclude: null,
    version__isnull: '0',
    id: null,
    id__gte: null,
    id__lte: null,
    id__between: '',
    id__between_min: null,
    id__between_max: null,
    id__any: '',
    subject: '',
    subject__exclude: '',
    description: '',
    description__exclude: '',
    comment: '',
    comment__exclude: '',
    any_searchable: '',
    any_searchable__exclude: '',
    file: '',
    file__exclude: '',
    file_desc: '',
    file_desc__exclude: '',
    parent_issue: null, // 상위업무
    parent_issue__exclude: null,
    parent_issue__contains: '',
    parent_issue__isnull: '0',
    parent: null, // 하위업무
    parent__exclude: null,
    parent__contains: '',
    parent__isnull: '0',
    follows_issue: null, // 선행업무
    follows_issue__exclude: null,
    follows_issue__isnull: '0',
    precedes_issue: null, // 후속업무
    precedes_issue__exclude: null,
    precedes_issue__isnull: '0',
    project__my_project: undefined,
    project__bookmark: undefined,
    created: '',
    created__gte: '',
    created__lte: '',
    created__between_min: '',
    created__between_max: '',
    updated: '',
    updated__gte: '',
    updated__lte: '',
    updated__between_min: '',
    updated__between_max: '',
    start_date: '',
    start_date__gte: '',
    start_date__lte: '',
    start_date__between_min: '',
    start_date__between_max: '',
    due_date: '',
    due_date__gte: '',
    due_date__lte: '',
    due_date__between_min: '',
    due_date__between_max: '',
    due_date__isnull: '0',
    creator_role: null,
    creator_role__exclude: null,
    assignee_role: null,
    assignee_role__exclude: null,
    version_date: '',
    version_date__gte: '',
    version_date__lte: '',
    version_date__between_min: '',
    version_date__between_max: '',
    version_date__isnull: '0',
    version_status: '',
    version_status__exclude: '',
    project_status: '',
    project_status__exclude: '',
    sub_project: null,
    sub_project__exclude: null,
    sub_project__isnull: '0',
  }

  const form = ref<IssueFilter & Record<string, unknown>>({ ...defaultForm })

  // 4. 활성화된 저장 검색양식 ID
  const activeQueryId = ref<number | null>(null)

  // 5. 필터 파라미터 빌드 로직 (DRF API 쿼리 파라미터 생성)
  const buildFilterPayload = (currentProjectSlug = ''): IssueFilter => {
    const filterData: IssueFilter & Record<string, unknown> = {
      status__closed: '0',
      project_status: '1',
    }

    // 기본 프로젝트 조회 세팅 (전역에서 project 필터 해제 시 sticky 방지)
    if (currentProjectSlug) {
      filterData.project__slug = currentProjectSlug
    }

    // 1. 상태(status) 필터링
    if (enabledFields.value.includes('status')) {
      if (cond.value.status === 'open') {
        filterData.status__closed = '0'
        filterData.status = null
        filterData.status__exclude = null
      } else if (cond.value.status === 'is') {
        filterData.status = form.value.status
        filterData.status__closed = ''
        filterData.status__exclude = null
      } else if (cond.value.status === 'exclude') {
        filterData.status__exclude = form.value.status
        filterData.status = null
        filterData.status__closed = ''
      } else if (cond.value.status === 'closed') {
        filterData.status__closed = '1'
        filterData.status = null
        filterData.status__exclude = null
      } else if (cond.value.status === 'any') {
        filterData.status__closed = ''
        filterData.status = null
        filterData.status__exclude = null
      }
    } else {
      filterData.status__closed = ''
    }

    // 2. 활성화된 필드 매핑
    enabledFields.value.forEach(key => {
      if (key === 'status') return

      const fieldKey = key === 'sub_issue' ? 'parent' : key
      const operator = cond.value[fieldKey]
      const val = form.value[fieldKey]

      if (operator === 'is') {
        if (key === 'project') {
          if (form.value.project === '') {
            filterData.project__my_project = true
            delete filterData.project__slug
          } else if (form.value.project === 'bookmark') {
            filterData.project__bookmark = true
            delete filterData.project__slug
          } else if (form.value.project === 'closed') {
            filterData.project_status = '2'
            delete filterData.project__slug
          } else {
            filterData.project__search = form.value.project
          }
        } else if (key === 'issue') {
          filterData.id = form.value.id
        } else if (key === 'is_private') {
          filterData.is_private = true
        } else {
          filterData[fieldKey] = val
        }
      } else if (operator === 'exclude') {
        if (key === 'project') {
          if (form.value.project === '') {
            filterData.project__my_project = false
            delete filterData.project__slug
          } else if (form.value.project === 'bookmark') {
            filterData.project__bookmark = false
            delete filterData.project__slug
          } else if (form.value.project === 'closed') {
            filterData.project_status__exclude = '2'
            delete filterData.project_status
            delete filterData.project__slug
          } else {
            filterData.project__exclude = form.value.project
            delete filterData.project__slug
          }
        } else if (key === 'is_private') {
          filterData.is_private = false
        } else {
          const exclRaw = form.value[`${fieldKey}__exclude`]
          const exclVal =
            exclRaw !== undefined && exclRaw !== null && exclRaw !== '' ? exclRaw : val
          if (
            key === 'project_status' &&
            exclVal !== undefined &&
            exclVal !== null &&
            exclVal !== ''
          ) {
            delete filterData.project_status
          }
          filterData[`${fieldKey}__exclude`] = exclVal
        }
      } else if (operator === 'none') {
        filterData[`${fieldKey}__isnull`] = '1'
      } else if (operator === 'any') {
        filterData[`${fieldKey}__isnull`] = '0'
      } else if (operator === 'contains') {
        if (fieldKey === 'parent_issue' || fieldKey === 'parent') {
          const containsVal = form.value[`${fieldKey}__contains`] ?? val
          filterData[`${fieldKey}__contains`] =
            containsVal !== null && containsVal !== undefined ? String(containsVal) : undefined
        } else {
          filterData[fieldKey] = val
        }
      } else if (operator === 'gte') {
        if (key === 'issue') filterData.id__gte = form.value.id__gte
        else filterData[`${fieldKey}__gte`] = form.value[`${fieldKey}__gte`]
      } else if (operator === 'lte') {
        if (key === 'issue') filterData.id__lte = form.value.id__lte
        else filterData[`${fieldKey}__lte`] = form.value[`${fieldKey}__lte`]
      } else if (operator === 'between') {
        let min = ''
        let max = ''
        if (key === 'issue') {
          const rawIdMin = form.value.id__between_min as number | string | null | undefined
          const rawIdMax = form.value.id__between_max as number | string | null | undefined
          min =
            rawIdMin !== null && rawIdMin !== undefined && String(rawIdMin) !== ''
              ? String(rawIdMin)
              : ''
          max =
            rawIdMax !== null && rawIdMax !== undefined && String(rawIdMax) !== ''
              ? String(rawIdMax)
              : ''
          if (min || max) filterData.id__between = `${min},${max}`
        } else {
          const rawMin = form.value[`${fieldKey}__between_min`]
          const rawMax = form.value[`${fieldKey}__between_max`]
          min = rawMin !== null && rawMin !== undefined && rawMin !== '' ? String(rawMin) : ''
          max = rawMax !== null && rawMax !== undefined && rawMax !== '' ? String(rawMax) : ''
          if (min || max) filterData[`${fieldKey}__between`] = `${min},${max}`
        }
      }
    })

    return filterData
  }

  // 6. 초기화
  const resetFilter = (currentProjectSlug = '') => {
    activeQueryId.value = null
    searchCond.value = ['status']
    enabledFields.value = ['status']
    cond.value = { ...defaultCond }
    form.value = {
      ...defaultForm,
      project: currentProjectSlug,
    }
    return buildFilterPayload(currentProjectSlug)
  }

  // 7. 저장된 쿼리 복원
  const applySavedQuery = (
    query: SavedIssueQuery | null | undefined,
    currentUserId?: number,
    _defaultUserId?: number,
    currentProjectSlug = '',
  ) => {
    if (!query || !query.filters) {
      activeQueryId.value = null
      return null
    }

    activeQueryId.value = query.pk ?? null

    const f = query.filters
    searchCond.value = ['status']
    enabledFields.value = ['status']
    cond.value = { ...defaultCond }
    form.value = {
      ...defaultForm,
      project: currentProjectSlug,
    }

    if (f.searchCond) {
      searchCond.value = [...f.searchCond]
      enabledFields.value = [...f.searchCond]
    }
    if (f.cond) {
      cond.value = { ...cond.value, ...f.cond }
    }

    const myId: number | string = currentUserId ?? 'me'
    const resolveUser = (v: SavedUserFilterVal | undefined): number | null => {
      const resolved = v === 'me' ? myId : v
      return (resolved ?? null) as number | null
    }

    if (f.form) {
      const formPayload: Record<string, string | number | boolean | null | undefined> = {
        ...f.form,
      }
      if (f.form.watcher === 'me') formPayload.watcher = myId
      if (f.form.author === 'me' || f.form.creator === 'me') formPayload.author = myId
      if (f.form.updater === 'me') formPayload.updater = myId
      if (f.form.assignee === 'me' || f.form.assigned_to === 'me') {
        formPayload.assignee = myId
      }

      form.value = { ...form.value, ...formPayload }

      if (!currentProjectSlug && formPayload.project && !searchCond.value.includes('project')) {
        searchCond.value.push('project')
        if (!enabledFields.value.includes('project')) {
          enabledFields.value.push('project')
        }
      }
      // 워크스페이스 범위 내 적용 시 다른 워크스페이스 조건과 충돌 방지
      if (currentProjectSlug) {
        searchCond.value = searchCond.value.filter(k => k !== 'project')
        enabledFields.value = enabledFields.value.filter(k => k !== 'project')
      }
    } else {
      // 레거시 평면 필터 구조 복원
      if (f.watcher !== undefined) {
        if (!searchCond.value.includes('watcher')) searchCond.value.push('watcher')
        if (!enabledFields.value.includes('watcher')) enabledFields.value.push('watcher')
        cond.value.watcher = 'is'
        form.value.watcher = resolveUser(f.watcher)
      }
      if (f.creator !== undefined || f.author !== undefined) {
        const creatorVal = f.creator ?? f.author
        if (!searchCond.value.includes('author')) searchCond.value.push('author')
        if (!enabledFields.value.includes('author')) enabledFields.value.push('author')
        cond.value.author = 'is'
        form.value.author = resolveUser(creatorVal)
      }
      if (f.updater !== undefined) {
        if (!searchCond.value.includes('updater')) searchCond.value.push('updater')
        if (!enabledFields.value.includes('updater')) enabledFields.value.push('updater')
        cond.value.updater = 'is'
        form.value.updater = resolveUser(f.updater)
      }
      if (f.assigned_to !== undefined || f.assignee !== undefined) {
        const assigneeVal = f.assigned_to ?? f.assignee
        if (!searchCond.value.includes('assignee')) searchCond.value.push('assignee')
        if (!enabledFields.value.includes('assignee')) enabledFields.value.push('assignee')
        cond.value.assignee = 'is'
        form.value.assignee = resolveUser(assigneeVal)
      }
    }

    return buildFilterPayload(currentProjectSlug)
  }

  return {
    activeQueryId,
    searchCond,
    enabledFields,
    cond,
    form,
    buildFilterPayload,
    resetFilter,
    applySavedQuery,
  }
})
