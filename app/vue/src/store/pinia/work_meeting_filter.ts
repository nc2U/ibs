import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MeetingFilter } from '@/store/types/work_meeting.ts'

export interface MeetingFilterForm {
  project: string
  status: string
  is_confirmed: string
  category: number | undefined
  creator: number | null
  attendees: number | null
  meeting_date_after: string
  meeting_date_before: string
  created_after: string
  created_before: string
  title: string
  agenda: string
  content: string
  decisions: string
  [key: string]: any
}

export const useMeetingFilter = defineStore('meetingFilter', () => {
  // 1. 활성화된 검색 조건 태그 및 체크박스
  const searchCond = ref<string[]>(['status'])
  const enabledFields = ref<string[]>(['status'])

  // 2. 연산자 조건
  const defaultCond: Record<string, string> = {
    status: 'any',
    project: 'is',
    is_confirmed: 'is',
    category: 'is',
    creator: 'is',
    attendees: 'is',
    meeting_date: 'between',
    created: 'between',
    title: 'contains',
    agenda: 'contains',
    content: 'contains',
    decisions: 'contains',
  }
  const cond = ref<Record<string, string>>({ ...defaultCond })

  // 3. 폼 입력값
  const defaultForm: MeetingFilterForm = {
    project: '',
    status: '1',
    is_confirmed: '',
    category: undefined,
    creator: null,
    attendees: null,
    meeting_date_after: '',
    meeting_date_before: '',
    created_after: '',
    created_before: '',
    title: '',
    agenda: '',
    content: '',
    decisions: '',
  }
  const form = ref<MeetingFilterForm>({ ...defaultForm })

  // 4. 필터 페이로드 생성 로직
  const buildFilterPayload = (currentProjSlug = ''): MeetingFilter => {
    const payload: MeetingFilter = { page: 1 }

    if (currentProjSlug) {
      payload.project = currentProjSlug
    } else if (enabledFields.value.includes('project')) {
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
        else if (cond.value.project === 'exclude') payload.project = form.value.project
      }
    }

    // 상태 처리
    if (enabledFields.value.includes('status')) {
      if (cond.value.status === 'open') {
        payload.status = '1' // 준비중
      } else if (cond.value.status === 'closed') {
        payload.status = '2' // 종료
      } else if (cond.value.status === 'is') {
        payload.status = form.value.status || '1'
      } else if (cond.value.status === 'exclude') {
        payload.status__exclude = form.value.status || '1'
      } else if (cond.value.status === 'any') {
        delete payload.status
      }
    } else {
      delete payload.status
    }

    // 확정 여부
    if (enabledFields.value.includes('is_confirmed')) {
      const val = form.value.is_confirmed || 'true'
      const isTrue = val === 'true'
      if (cond.value.is_confirmed === 'is') {
        payload.is_confirmed = isTrue
      } else if (cond.value.is_confirmed === 'exclude') {
        payload.is_confirmed = !isTrue
      }
    }

    // 카테고리
    if (enabledFields.value.includes('category') && form.value.category !== undefined) {
      if (cond.value.category === 'is') {
        payload.category = form.value.category
      } else if (cond.value.category === 'exclude') {
        payload.category__exclude = form.value.category
      }
    }

    // 작성자
    if (enabledFields.value.includes('creator') && form.value.creator !== null) {
      if (cond.value.creator === 'is') {
        payload.creator = form.value.creator
      } else if (cond.value.creator === 'exclude') {
        payload.creator__exclude = form.value.creator
      }
    }

    // 참석자
    if (enabledFields.value.includes('attendees') && form.value.attendees !== null) {
      if (cond.value.attendees === 'is') {
        payload.attendees = form.value.attendees
      } else if (cond.value.attendees === 'exclude') {
        payload.attendees__exclude = form.value.attendees
      }
    }

    // 회의 일시 범위
    if (enabledFields.value.includes('meeting_date')) {
      if (cond.value.meeting_date === 'between') {
        if (form.value.meeting_date_after) payload.meeting_date_after = form.value.meeting_date_after
        if (form.value.meeting_date_before) payload.meeting_date_before = form.value.meeting_date_before
      } else if (cond.value.meeting_date === 'gte' && form.value.meeting_date_after) {
        payload.meeting_date_after = form.value.meeting_date_after
      } else if (cond.value.meeting_date === 'lte' && form.value.meeting_date_before) {
        payload.meeting_date_before = form.value.meeting_date_before
      }
    }

    // 등록일 범위
    if (enabledFields.value.includes('created')) {
      if (cond.value.created === 'between') {
        if (form.value.created_after) payload.created_after = form.value.created_after
        if (form.value.created_before) payload.created_before = form.value.created_before
      } else if (cond.value.created === 'gte' && form.value.created_after) {
        payload.created_after = form.value.created_after
      } else if (cond.value.created === 'lte' && form.value.created_before) {
        payload.created_before = form.value.created_before
      }
    }

    // 문자열 검색
    const searchTerms: string[] = []
    if (enabledFields.value.includes('title') && form.value.title) searchTerms.push(form.value.title)
    if (enabledFields.value.includes('agenda') && form.value.agenda) searchTerms.push(form.value.agenda)
    if (enabledFields.value.includes('content') && form.value.content) searchTerms.push(form.value.content)
    if (enabledFields.value.includes('decisions') && form.value.decisions) {
      searchTerms.push(form.value.decisions)
    }

    if (searchTerms.length) {
      payload.search = searchTerms.join(' ')
    }

    return payload
  }

  // 5. 초기화
  const resetFilter = (currentProjSlug = '') => {
    searchCond.value = ['status']
    enabledFields.value = ['status']
    cond.value = { ...defaultCond }
    form.value = {
      ...defaultForm,
      project: currentProjSlug,
    }
    return buildFilterPayload(currentProjSlug)
  }

  // 6. 저장된 쿼리 복원
  const applySavedQuery = (
    query: any,
    currentUserId?: number,
    defaultUserId?: number,
    currentProjSlug = '',
  ) => {
    if (!query || !query.filters) return null

    const f = query.filters
    searchCond.value = ['status']
    enabledFields.value = ['status']
    cond.value = { ...defaultCond }
    form.value = {
      ...defaultForm,
      project: currentProjSlug,
    }

    if (f.searchCond) {
      searchCond.value = [...f.searchCond]
      enabledFields.value = [...f.searchCond]
    }
    if (f.cond) {
      cond.value = { ...cond.value, ...f.cond }
    }

    const myId = currentUserId ?? defaultUserId

    if (f.form) {
      const formPayload = { ...f.form }
      if (formPayload.creator === 'me') formPayload.creator = myId
      if (formPayload.attendees === 'me') formPayload.attendees = myId

      form.value = { ...form.value, ...formPayload }

      if (formPayload.project && !searchCond.value.includes('project')) {
        searchCond.value.push('project')
        if (!enabledFields.value.includes('project')) {
          enabledFields.value.push('project')
        }
      }
    } else {
      if (f.creator !== undefined || f.author !== undefined) {
        const creatorVal = f.creator ?? f.author
        if (!searchCond.value.includes('creator')) searchCond.value.push('creator')
        if (!enabledFields.value.includes('creator')) enabledFields.value.push('creator')
        cond.value.creator = 'is'
        form.value.creator = creatorVal === 'me' ? myId : creatorVal
      }
      if (f.attendees !== undefined) {
        if (!searchCond.value.includes('attendees')) searchCond.value.push('attendees')
        if (!enabledFields.value.includes('attendees')) enabledFields.value.push('attendees')
        cond.value.attendees = 'is'
        form.value.attendees = f.attendees === 'me' ? myId : f.attendees
      }
    }

    return buildFilterPayload(currentProjSlug)
  }

  return {
    searchCond,
    enabledFields,
    cond,
    form,
    buildFilterPayload,
    resetFilter,
    applySavedQuery,
  }
})
