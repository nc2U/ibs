import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useMeetingFilter } from '../work_meeting_filter'

describe('useMeetingFilter', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('has expected initial filter state and empty default payload', () => {
    const store = useMeetingFilter()
    expect(store.searchCond).toEqual(['status'])
    expect(store.enabledFields).toEqual(['status'])
    expect(store.cond.status).toBe('any')
    expect(store.buildFilterPayload()).toEqual({ page: 1 })
  })

  it('builds project scope filters for my_project, bookmark, closed, and specific slug', () => {
    const store = useMeetingFilter()
    store.enabledFields = ['project']

    store.form.project = ''
    store.cond.project = 'is'
    expect(store.buildFilterPayload()).toMatchObject({ project__my_project: true })

    store.cond.project = 'exclude'
    expect(store.buildFilterPayload()).toMatchObject({ project__my_project: false })

    store.form.project = 'bookmark'
    store.cond.project = 'is'
    expect(store.buildFilterPayload()).toMatchObject({ project__bookmark: true })

    store.form.project = 'closed'
    store.cond.project = 'exclude'
    expect(store.buildFilterPayload()).toMatchObject({ project_status__exclude: '2' })

    store.form.project = 'proj-alpha'
    store.cond.project = 'is'
    expect(store.buildFilterPayload()).toMatchObject({ project: 'proj-alpha' })

    // Explicit currentProjSlug overrides enabled project filter
    expect(store.buildFilterPayload('forced-slug')).toMatchObject({ project: 'forced-slug' })
  })

  it('builds status, boolean, relation, date range, and text search payloads', () => {
    const store = useMeetingFilter()
    store.enabledFields = [
      'status',
      'is_confirmed',
      'category',
      'creator',
      'attendees',
      'meeting_date',
      'created',
      'title',
      'decisions',
    ]

    store.cond.status = 'closed'
    store.cond.is_confirmed = 'exclude'
    store.form.is_confirmed = 'true'
    store.form.category = 3
    store.cond.category = 'exclude'
    store.form.creator = 7
    store.form.attendees = 12
    store.cond.meeting_date = 'between'
    store.form.meeting_date_after = '2026-01-01'
    store.form.meeting_date_before = '2026-01-31'
    store.cond.created = 'gte'
    store.form.created_after = '2026-01-05'
    store.form.title = '주간'
    store.form.decisions = '승인'

    expect(store.buildFilterPayload()).toEqual({
      page: 1,
      status: '2',
      is_confirmed: false,
      category__exclude: 3,
      creator: 7,
      attendees: 12,
      meeting_date_after: '2026-01-01',
      meeting_date_before: '2026-01-31',
      created_after: '2026-01-05',
      search: '주간 승인',
    })
  })

  it('restores saved queries including "me" shorthand and resets cleanly', () => {
    const store = useMeetingFilter()
    const payload = store.applySavedQuery(
      {
        pk: 42,
        filters: {
          searchCond: ['status', 'creator', 'attendees'],
          cond: { status: 'open', creator: 'is', attendees: 'exclude' },
          form: { creator: 'me', attendees: 'me', project: 'dev-site' },
        },
      },
      99,
    )

    expect(store.activeQueryId).toBe(42)
    expect(store.form.creator).toBe(99)
    expect(store.form.attendees).toBe(99)
    expect(store.searchCond).toContain('project')
    expect(payload).toMatchObject({
      status: '1',
      creator: 99,
      attendees__exclude: 99,
      project: 'dev-site',
    })

    const resetPayload = store.resetFilter('reset-proj')
    expect(store.activeQueryId).toBeNull()
    expect(store.searchCond).toEqual(['status'])
    expect(resetPayload).toEqual({ page: 1, project: 'reset-proj' })
  })
})
