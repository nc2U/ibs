import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCalendarFilter = defineStore('calendarFilter', () => {
  // 1. 이벤트 종류 (업무, 회의) 선택
  const eventTypes = ref<('issue' | 'meeting')[]>(['issue', 'meeting'])

  // 2. 활성화된 검색 조건 태그 및 체크박스 필드
  const searchCond = ref<string[]>(['issue_status'])
  const enabledFields = ref<string[]>(['issue_status'])

  // 3. 연산자 조건
  const defaultCond: Record<string, any> = {
    issue_status: 'open',
    project: 'is',
    tracker: 'is',
    priority: 'is',
    assignee: 'is',
    author: 'is',
    issue_subject: 'contains',
    start_date: 'gte',
    due_date: 'lte',
    meeting_status: 'is',
    meeting_category: 'is',
    meeting_attendees: 'is',
    meeting_creator: 'is',
    meeting_title: 'contains',
    meeting_date: 'between',
  }
  const cond = ref<Record<string, any>>({ ...defaultCond })

  // 4. 폼 값 상태
  const defaultForm: Record<string, any> = {
    project: '',
    issue_status: null,
    issue_status__exclude: null,
    tracker: null,
    tracker__exclude: null,
    priority: null,
    priority__exclude: null,
    assignee: null,
    assignee__exclude: null,
    author: null,
    author__exclude: null,
    issue_subject: '',
    issue_subject__exclude: '',
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
    meeting_status: '1',
    meeting_status__exclude: null,
    meeting_category: null,
    meeting_category__exclude: null,
    meeting_attendees: null,
    meeting_attendees__exclude: null,
    meeting_creator: null,
    meeting_creator__exclude: null,
    meeting_title: '',
    meeting_date: '',
    meeting_date__gte: '',
    meeting_date__lte: '',
    meeting_date__between_min: '',
    meeting_date__between_max: '',
  }
  const form = ref<Record<string, any>>({ ...defaultForm })

  // 5. 날짜 헬퍼
  const _applyDateFilter = (payload: Record<string, any>, key: string, op: string) => {
    if (op === 'is' && form.value[key]) {
      payload[key] = form.value[key]
    } else if (op === 'gte' && form.value[`${key}__gte`]) {
      payload[`${key}__gte`] = form.value[`${key}__gte`]
    } else if (op === 'lte' && form.value[`${key}__lte`]) {
      payload[`${key}__lte`] = form.value[`${key}__lte`]
    } else if (op === 'between') {
      if (form.value[`${key}__between_min`])
        payload[`${key}__gte`] = form.value[`${key}__between_min`]
      if (form.value[`${key}__between_max`])
        payload[`${key}__lte`] = form.value[`${key}__between_max`]
    }
  }

  // 6. 페이로드 빌드 로직
  const buildFilterPayload = (): Record<string, any> => {
    const payload: Record<string, any> = {
      event_type: eventTypes.value.length === 2 ? 'all' : (eventTypes.value[0] ?? 'all'),
    }

    // 프로젝트 (체크 박스 활성화시에만 적용)
    if (enabledFields.value.includes('project')) {
      if (form.value.project === '') {
        if (cond.value.project === 'is') payload.project__my_project = true
        else if (cond.value.project === 'exclude') payload.project__my_project = false
      } else if (form.value.project === 'bookmark') {
        if (cond.value.project === 'is') payload.project__bookmark = true
        else if (cond.value.project === 'exclude') payload.project__bookmark = false
      } else if (form.value.project === 'closed') {
        if (cond.value.project === 'is') payload.project_status = '2'
        else if (cond.value.project === 'exclude') payload.project_status__exclude = '2'
      } else if (form.value.project) {
        if (cond.value.project === 'is') payload.project = form.value.project
        else if (cond.value.project === 'exclude') payload.project__exclude = form.value.project
      }
    }

    // 업무 상태 (체크 박스 활성화시에만 적용)
    if (enabledFields.value.includes('issue_status')) {
      if (cond.value.issue_status === 'open') {
        payload.status__closed = '0'
      } else if (cond.value.issue_status === 'closed') {
        payload.status__closed = '1'
      } else if (cond.value.issue_status === 'any') {
        payload.status__closed = ''
      } else if (cond.value.issue_status === 'is' && form.value.issue_status) {
        payload.status = form.value.issue_status
        payload.status__closed = ''
      } else if (cond.value.issue_status === 'exclude' && form.value.issue_status__exclude) {
        payload.status__exclude = form.value.issue_status__exclude
        payload.status__closed = ''
      }
    }

    // 동적 조건 순회
    enabledFields.value.forEach(key => {
      if (key === 'issue_status' || key === 'project') return

      const op = cond.value[key]

      // 업무 필터
      if (key === 'tracker') {
        if (op === 'is' && form.value.tracker) payload.tracker = form.value.tracker
        else if (op === 'exclude' && form.value.tracker)
          payload.tracker__exclude = form.value.tracker
      } else if (key === 'priority') {
        if (op === 'is' && form.value.priority) payload.priority = form.value.priority
        else if (op === 'exclude' && form.value.priority)
          payload.priority__exclude = form.value.priority
      } else if (key === 'assignee') {
        if (op === 'is' && form.value.assignee) payload.assigned_to = form.value.assignee
        else if (op === 'exclude' && form.value.assignee)
          payload.assigned_to__exclude = form.value.assignee
      } else if (key === 'author') {
        if (op === 'is' && form.value.author) payload.creator = form.value.author
        else if (op === 'exclude' && form.value.author)
          payload.creator__exclude = form.value.author
      } else if (key === 'issue_subject') {
        if (op === 'contains' && form.value.issue_subject)
          payload.subject = form.value.issue_subject
        else if (op === 'exclude' && form.value.issue_subject__exclude)
          payload.subject__exclude = form.value.issue_subject__exclude
      } else if (key === 'start_date') {
        _applyDateFilter(payload, 'start_date', op)
      } else if (key === 'due_date') {
        _applyDateFilter(payload, 'due_date', op)
      } else if (key === 'meeting_status') {
        // 회의 필터
        if (op === 'is' && form.value.meeting_status)
          payload.meeting_status = form.value.meeting_status
        else if (op === 'exclude' && form.value.meeting_status)
          payload.meeting_status__exclude = form.value.meeting_status
      } else if (key === 'meeting_category') {
        if (op === 'is' && form.value.meeting_category)
          payload.meeting_category = form.value.meeting_category
        else if (op === 'exclude' && form.value.meeting_category)
          payload.meeting_category__exclude = form.value.meeting_category
      } else if (key === 'meeting_attendees') {
        if (op === 'is' && form.value.meeting_attendees)
          payload.meeting_attendees = form.value.meeting_attendees
        else if (op === 'exclude' && form.value.meeting_attendees)
          payload.meeting_attendees__exclude = form.value.meeting_attendees
      } else if (key === 'meeting_creator') {
        if (op === 'is' && form.value.meeting_creator)
          payload.meeting_creator = form.value.meeting_creator
        else if (op === 'exclude' && form.value.meeting_creator)
          payload.meeting_creator__exclude = form.value.meeting_creator
      } else if (key === 'meeting_title') {
        if (op === 'contains' && form.value.meeting_title)
          payload.meeting_search = form.value.meeting_title
        else if (op === 'exclude' && form.value.meeting_title__exclude)
          payload.meeting_search__exclude = form.value.meeting_title__exclude
      } else if (key === 'meeting_date') {
        _applyDateFilter(payload, 'meeting_date', op)
      }
    })

    return payload
  }

  // 7. 초기화
  const resetFilter = () => {
    eventTypes.value = ['issue', 'meeting']
    searchCond.value = ['issue_status']
    enabledFields.value = ['issue_status']
    cond.value = { ...defaultCond }
    form.value = { ...defaultForm }
    return buildFilterPayload()
  }

  // 8. 저장된 쿼리 복원
  const applySavedQuery = (query: any, currentUserId?: number, defaultUserId?: number) => {
    if (!query || !query.filters) return null

    const f = query.filters
    searchCond.value = ['issue_status']
    enabledFields.value = ['issue_status']
    cond.value = { ...defaultCond }
    form.value = { ...defaultForm }

    if (f.searchCond) {
      searchCond.value = [...f.searchCond]
      enabledFields.value = [...f.searchCond]
    }
    if (f.cond) cond.value = { ...cond.value, ...f.cond }
    if (f.form) {
      form.value = { ...form.value, ...f.form }
    } else {
      const myId = currentUserId ?? defaultUserId

      if (f.assignee !== undefined || f.assigned_to !== undefined) {
        const val = f.assignee ?? f.assigned_to
        if (!searchCond.value.includes('assignee')) searchCond.value.push('assignee')
        if (!enabledFields.value.includes('assignee')) enabledFields.value.push('assignee')
        cond.value.assignee = 'is'
        form.value.assignee = val === 'me' ? myId : val
      }
      if (f.author !== undefined || f.creator !== undefined) {
        const val = f.author ?? f.creator
        if (!searchCond.value.includes('author')) searchCond.value.push('author')
        if (!enabledFields.value.includes('author')) enabledFields.value.push('author')
        cond.value.author = 'is'
        form.value.author = val === 'me' ? myId : val
      }
      if (f.meeting_attendees !== undefined) {
        if (!searchCond.value.includes('meeting_attendees'))
          searchCond.value.push('meeting_attendees')
        if (!enabledFields.value.includes('meeting_attendees'))
          enabledFields.value.push('meeting_attendees')
        cond.value.meeting_attendees = 'is'
        form.value.meeting_attendees = f.meeting_attendees === 'me' ? myId : f.meeting_attendees
      }
      if (f.meeting_creator !== undefined) {
        if (!searchCond.value.includes('meeting_creator')) searchCond.value.push('meeting_creator')
        if (!enabledFields.value.includes('meeting_creator'))
          enabledFields.value.push('meeting_creator')
        cond.value.meeting_creator = 'is'
        form.value.meeting_creator = f.meeting_creator === 'me' ? myId : f.meeting_creator
      }
    }

    return buildFilterPayload()
  }

  return {
    eventTypes,
    searchCond,
    enabledFields,
    cond,
    form,
    buildFilterPayload,
    resetFilter,
    applySavedQuery,
  }
})
